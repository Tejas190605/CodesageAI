import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.db_repositories.repository_repo import upsert_repository
from app.db_repositories.pr_repo import upsert_pull_request
from app.db_repositories.review_repo import create_review_with_findings
from app.models.review import StructuredReview, ReviewFinding, ReviewCategory, ReviewSeverity


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_api_dashboard_reads_from_db(client, db_session):
    repo = upsert_repository(db_session, owner="Tejas190605", name="codexproj")
    pr = upsert_pull_request(db_session, repo.id, number=1, title="Test PR", state="open")

    structured = StructuredReview(
        summary="Good test PR",
        overall_rating=9,
        findings=[
            ReviewFinding(
                title="Tip",
                category=ReviewCategory.CODE_QUALITY,
                severity=ReviewSeverity.LOW,
                file="test.py",
                line=1,
                description="Desc",
                suggested_fix="Fix"
            )
        ]
    )
    create_review_with_findings(db_session, pr.id, summary=structured.summary, overall_rating=structured.overall_rating, markdown="Markdown", structured_review=structured)

    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["repositories_count"] == 1
    assert data["open_pull_requests"] == 1
    assert data["reviewed_pull_requests"] == 1
    assert data["average_score"] == 9.0
    assert len(data["recent_pull_requests"]) == 1
    assert data["recent_pull_requests"][0]["number"] == 1


def test_api_repositories_reads_from_db(client, db_session):
    upsert_repository(db_session, owner="Tejas190605", name="codexproj", description="CodeSage Repo")
    res = client.get("/api/repositories")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["owner"] == "Tejas190605"
    assert data[0]["name"] == "codexproj"


def test_api_pull_request_review_status_from_db(client, db_session):
    repo = upsert_repository(db_session, owner="Tejas190605", name="codexproj")
    pr = upsert_pull_request(db_session, repo.id, number=1, title="PR 1")
    create_review_with_findings(db_session, pr.id, summary="Reviewed", overall_rating=8, markdown="Markdown Review")

    res = client.get("/api/pulls/Tejas190605/codexproj/1/review")
    assert res.status_code == 200
    data = res.json()
    assert data["reviewed"] is True
    assert data["review_count"] == 1
    assert data["latest_review"]["overall_rating"] == 8
    assert data["latest_review"]["markdown"] == "Markdown Review"
