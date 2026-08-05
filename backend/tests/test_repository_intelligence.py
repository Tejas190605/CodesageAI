import pytest
from app.services.code_chunker import (
    detect_language,
    is_file_excluded,
    calculate_chunk_hash,
    chunk_source_code,
)
from app.services.repository_indexer import (
    generate_embedding,
    generate_embeddings_batch,
    index_repository_contents,
)
from app.services.semantic_search import (
    cosine_similarity,
    semantic_search,
)
from app.services.rag_context import format_rag_context
from app.services.retrieval_service import extract_search_queries_from_diff, retrieve_context_for_pr


def test_language_detection_and_file_exclusions():
    """Tests language detection from extensions and file path exclusion rules."""
    assert detect_language("app/main.py") == "python"
    assert detect_language("src/index.ts") == "typescript"
    assert detect_language("src/App.tsx") == "tsx"
    assert detect_language("main.go") == "go"
    assert detect_language("Application.java") == "java"

    assert is_file_excluded("node_modules/express/index.js") is True
    assert is_file_excluded(".git/config") is True
    assert is_file_excluded("dist/bundle.min.js") is True
    assert is_file_excluded("app/services/main.py") is False


def test_semantic_code_chunker_python():
    """Tests Python semantic code chunking for functions and classes."""
    code = '''
class UserAuth:
    def validate_token(self, token: str) -> bool:
        return len(token) > 10

def generate_session():
    return "session-12345"
'''
    chunks = chunk_source_code("owner/repo", "app/auth.py", code)
    assert len(chunks) >= 2
    symbols = [c["symbol_name"] for c in chunks]
    assert "UserAuth" in symbols or "generate_session" in symbols


def test_semantic_code_chunker_fallback():
    """Tests fallback chunking for unstructured files."""
    code = "\n".join([f"line_{i} = {i}" for i in range(120)])
    chunks = chunk_source_code("owner/repo", "config.py", code)
    assert len(chunks) >= 2
    assert chunks[0]["start_line"] == 1


def test_vector_similarity_computation():
    """Tests vector cosine similarity math."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]

    assert cosine_similarity(v1, v2) == pytest.approx(1.0)
    assert cosine_similarity(v1, v3) == pytest.approx(0.0)


def test_incremental_repository_indexing_and_search(db_session):
    """Tests repository indexing, chunk persistence, and hybrid semantic search."""
    files = {
        "app/security.py": "def validate_jwt_token(token: str):\n    return True\n",
        "app/database.py": "class DatabaseConnection:\n    def connect(self):\n        pass\n"
    }

    index_rec = index_repository_contents(
        db=db_session,
        repository="test-org/secure-app",
        commit_sha="abc123456789",
        files_dict=files
    )

    assert index_rec.status == "completed"
    assert index_rec.chunk_count >= 2

    # Perform Hybrid Code Search
    search_res = semantic_search(
        db=db_session,
        repository="test-org/secure-app",
        query="validate_jwt_token",
        top_k=5
    )

    assert len(search_res) >= 1
    assert search_res[0]["repository"] == "test-org/secure-app"
    assert "app/security.py" in search_res[0]["file_path"]
    assert "citation" in search_res[0]


def test_tenant_isolation_boundary_enforcement(db_session):
    """Critical Security Test: Verifies chunks from Repo A are NEVER returned when searching Repo B."""
    files_a = {"auth.py": "def secret_auth_repo_a(): pass\n"}
    files_b = {"auth.py": "def secret_auth_repo_b(): pass\n"}

    index_repository_contents(db_session, "tenant-a/repo-a", "sha-a", files_a)
    index_repository_contents(db_session, "tenant-b/repo-b", "sha-b", files_b)

    # Search strictly scoped to Tenant A
    results_a = semantic_search(db_session, "tenant-a/repo-a", "secret_auth")
    for r in results_a:
        assert r["repository"] == "tenant-a/repo-a"
        assert "tenant-b" not in r["repository"]

    # Search strictly scoped to Tenant B
    results_b = semantic_search(db_session, "tenant-b/repo-b", "secret_auth")
    for r in results_b:
        assert r["repository"] == "tenant-b/repo-b"
        assert "tenant-a" not in r["repository"]


def test_rag_context_formatting_and_citations():
    """Tests RAG context builder token budgeting and line-level citation formatting."""
    chunks = [
        {
            "chunk_id": 1,
            "file_path": "app/auth.py",
            "symbol": "login_user",
            "start_line": 10,
            "end_line": 25,
            "content": "def login_user(): pass",
            "citation": "app/auth.py:L10-L25"
        }
    ]

    rag = format_rag_context(chunks)
    assert rag["chunk_count"] == 1
    assert "app/auth.py:L10-L25" in rag["citations"]
    assert "REPOSITORY CONTEXT" in rag["formatted_text"]


def test_repository_intelligence_api_endpoints(client):
    """Tests GET/POST repository indexing & search API endpoints."""
    # Index Status Endpoint
    status_res = client.get("/api/repositories/test-org/api-repo/index/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "unindexed"

    # Trigger Indexing API
    idx_res = client.post(
        "/api/repositories/test-org/api-repo/index",
        json={
            "commit_sha": "sha-9999",
            "branch": "main",
            "files": {"main.py": "def main(): print('hello')\n"}
        }
    )
    assert idx_res.status_code == 200
    assert idx_res.json()["status"] == "completed"

    # Search Code API
    search_res = client.post(
        "/api/search/code",
        json={
            "repository": "test-org/api-repo",
            "query": "main",
            "top_k": 5
        }
    )
    assert search_res.status_code == 200
    assert search_res.json()["total_results"] >= 1
