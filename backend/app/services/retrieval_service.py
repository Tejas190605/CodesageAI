import re
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.services.semantic_search import semantic_search

logger = logging.getLogger("codesage.retrieval_service")


def extract_search_queries_from_diff(changed_files: List[Dict[str, Any]]) -> List[str]:
    """
    Extracts high-signal search queries (imported symbols, class names, function names)
    from Pull Request diffs.
    """
    queries = set()
    symbol_pattern = re.compile(r"\b(def|class|function|interface|import|from)\s+([a-zA-Z0-9_]+)")

    for f in changed_files:
        filename = f.get("filename", "")
        if filename:
            queries.add(filename)

        patch = f.get("patch", "")
        if patch:
            for match in symbol_pattern.finditer(patch):
                symbol = match.group(2)
                if len(symbol) > 3 and symbol not in ("def", "class", "function", "import", "from"):
                    queries.add(symbol)

    return list(queries)[:5]  # Cap to top 5 queries


def retrieve_context_for_pr(
    db: Session,
    repository: str,
    changed_files: List[Dict[str, Any]],
    top_k_per_query: int = 3
) -> List[Dict[str, Any]]:
    """Retrieves surrounding repository context chunks for a Pull Request."""
    queries = extract_search_queries_from_diff(changed_files)
    if not queries:
        return []

    retrieved_chunks: List[Dict[str, Any]] = []
    seen_ids = set()

    for q in queries:
        results = semantic_search(db=db, repository=repository, query=q, top_k=top_k_per_query)
        for r in results:
            if r["chunk_id"] not in seen_ids:
                seen_ids.add(r["chunk_id"])
                retrieved_chunks.append(r)

    return retrieved_chunks[:10]  # Cap total RAG context chunks to 10
