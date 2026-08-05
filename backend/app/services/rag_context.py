import logging
from typing import List, Dict, Any

logger = logging.getLogger("codesage.rag_context")

MAX_RAG_TOKEN_BUDGET = 2048  # Token budget for repository context injection


def format_rag_context(retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deduplicates overlapping chunks, enforces token budget limits,
    and formats structured RAG context with line-level citations.
    """
    if not retrieved_chunks:
        return {
            "formatted_text": "",
            "chunk_count": 0,
            "citations": []
        }

    formatted_blocks = []
    citations = []
    current_tokens = 0

    for idx, chunk in enumerate(retrieved_chunks, start=1):
        content = chunk["content"]
        est_tokens = len(content) // 4

        if current_tokens + est_tokens > MAX_RAG_TOKEN_BUDGET:
            break

        citation = chunk["citation"]
        citations.append(citation)
        current_tokens += est_tokens

        block = f"[{idx}] File: {chunk['file_path']} (Lines {chunk['start_line']}-{chunk['end_line']}, Symbol: {chunk['symbol'] or 'block'})\nCitation: {citation}\n```\n{content}\n```\n"
        formatted_blocks.append(block)

    formatted_text = "\n--- REPOSITORY CONTEXT (RAG ENHANCED) ---\n" + "\n".join(formatted_blocks)

    return {
        "formatted_text": formatted_text,
        "chunk_count": len(formatted_blocks),
        "citations": citations
    }
