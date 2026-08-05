import math
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.db import CodeChunk
from app.services.repository_indexer import generate_embedding

logger = logging.getLogger("codesage.semantic_search")


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def semantic_search(
    db: Session,
    repository: str,
    query: str,
    top_k: int = 10,
    language: Optional[str] = None,
    file_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Performs Hybrid Semantic + Lexical Code Search using Reciprocal Rank Fusion (RRF):
    - Strict tenant isolation: Filters by `repository` at the database level.
    - Vector Semantic Search via cosine similarity.
    - Lexical Exact Search via symbol name and keyword matching.
    - RRF Fusion: RRF = 1 / (60 + semantic_rank) + 1 / (60 + lexical_rank).
    """
    query_stmt = db.query(CodeChunk).filter(CodeChunk.repository == repository)
    if language:
        query_stmt = query_stmt.filter(CodeChunk.language == language.lower())
    if file_path:
        query_stmt = query_stmt.filter(CodeChunk.file_path.contains(file_path))

    all_chunks = query_stmt.all()
    if not all_chunks:
        return []

    # 1. Semantic Vector Similarity Search
    query_vector = generate_embedding(query)
    semantic_scores = []
    for chunk in all_chunks:
        emb = chunk.embedding or []
        sim = cosine_similarity(query_vector, emb)
        semantic_scores.append((chunk, sim))

    semantic_sorted = sorted(semantic_scores, key=lambda x: x[1], reverse=True)
    semantic_ranks = {chunk.id: rank + 1 for rank, (chunk, _) in enumerate(semantic_sorted)}

    # 2. Lexical / Keyword Match Search
    query_lower = query.lower()
    lexical_scores = []
    for chunk in all_chunks:
        score = 0.0
        if chunk.symbol_name and query_lower in chunk.symbol_name.lower():
            score += 10.0
        if query_lower in chunk.file_path.lower():
            score += 5.0
        if query_lower in chunk.content.lower():
            score += 2.0
        lexical_scores.append((chunk, score))

    lexical_sorted = sorted(lexical_scores, key=lambda x: x[1], reverse=True)
    lexical_ranks = {chunk.id: rank + 1 for rank, (chunk, _) in enumerate(lexical_sorted)}

    # 3. Reciprocal Rank Fusion (RRF)
    k_constant = 60.0
    combined_results = []
    for chunk in all_chunks:
        sem_r = semantic_ranks.get(chunk.id, 999)
        lex_r = lexical_ranks.get(chunk.id, 999)
        rrf_score = (1.0 / (k_constant + sem_r)) + (1.0 / (k_constant + lex_r))

        citation_str = f"{chunk.file_path}:L{chunk.start_line}-L{chunk.end_line}"
        combined_results.append({
            "chunk_id": chunk.id,
            "repository": chunk.repository,
            "file_path": chunk.file_path,
            "symbol": chunk.symbol_name,
            "symbol_type": chunk.symbol_type,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "content": chunk.content,
            "score": round(rrf_score, 5),
            "citation": citation_str
        })

    combined_results.sort(key=lambda x: x["score"], reverse=True)
    return combined_results[:top_k]
