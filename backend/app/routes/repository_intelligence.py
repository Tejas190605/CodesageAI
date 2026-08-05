import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.db import RepositoryIndex, CodeChunk
from app.services.semantic_search import semantic_search
from app.services.repository_indexer import index_repository_contents

logger = logging.getLogger("codesage.routes.repo_intelligence")

router = APIRouter(tags=["Repository Intelligence & Semantic Search"])


class CodeSearchRequest(BaseModel):
    repository: str
    query: str
    top_k: int = 10
    language: Optional[str] = None
    file_path: Optional[str] = None


class IndexingRequest(BaseModel):
    commit_sha: str = "main"
    branch: str = "main"
    files: Optional[Dict[str, str]] = None


@router.get("/api/repositories/{owner}/{repo}/index/status")
def get_index_status(owner: str, repo: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves current indexing status, commit SHA, chunk count, and metrics for a repository."""
    repository = f"{owner}/{repo}"
    index_rec = db.query(RepositoryIndex).filter(RepositoryIndex.repository == repository).first()
    if not index_rec:
        return {
            "repository": repository,
            "status": "unindexed",
            "chunk_count": 0,
            "indexed_files": 0,
            "failed_files": 0,
            "commit_sha": None,
            "updated_at": None
        }

    return {
        "id": index_rec.id,
        "repository": index_rec.repository,
        "status": index_rec.status,
        "commit_sha": index_rec.commit_sha,
        "branch": index_rec.branch,
        "chunk_count": index_rec.chunk_count,
        "indexed_files": index_rec.indexed_files,
        "failed_files": index_rec.failed_files,
        "embedding_provider": index_rec.embedding_provider,
        "embedding_model": index_rec.embedding_model,
        "updated_at": index_rec.updated_at.isoformat() if index_rec.updated_at else None
    }


@router.post("/api/repositories/{owner}/{repo}/index")
def trigger_repository_indexing(
    owner: str,
    repo: str,
    payload: IndexingRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Triggers or executes repository indexing for a given repository."""
    repository = f"{owner}/{repo}"
    files_to_index = payload.files or {}

    # Execute indexing synchronously or fallback to provided file set
    index_rec = index_repository_contents(
        db=db,
        repository=repository,
        commit_sha=payload.commit_sha,
        files_dict=files_to_index,
        branch=payload.branch
    )

    return {
        "message": f"Successfully indexed repository '{repository}'.",
        "repository": repository,
        "status": index_rec.status,
        "chunk_count": index_rec.chunk_count,
        "indexed_files": index_rec.indexed_files
    }


@router.delete("/api/repositories/{owner}/{repo}/index")
def delete_repository_index(owner: str, repo: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Deletes repository index and purges all code chunks for a repository."""
    repository = f"{owner}/{repo}"
    index_rec = db.query(RepositoryIndex).filter(RepositoryIndex.repository == repository).first()
    if not index_rec:
        raise HTTPException(status_code=404, detail=f"Index for repository '{repository}' not found.")

    db.delete(index_rec)
    db.commit()
    return {"message": f"Successfully deleted index and chunks for '{repository}'."}


@router.post("/api/search/code")
def search_code(payload: CodeSearchRequest, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Performs hybrid vector semantic and exact lexical search across an indexed repository.
    Enforces strict multi-tenant isolation by filtering by repository.
    """
    results = semantic_search(
        db=db,
        repository=payload.repository,
        query=payload.query,
        top_k=payload.top_k,
        language=payload.language,
        file_path=payload.file_path
    )

    return {
        "repository": payload.repository,
        "query": payload.query,
        "total_results": len(results),
        "results": results
    }
