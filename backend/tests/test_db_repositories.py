import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.db_repositories.repository_repo import (
    upsert_repository,
    get_repository_by_full_name,
    get_repository_by_owner_repo,
    list_all_repositories,
)
from app.db_repositories.pr_repo import (
    upsert_pull_request,
    get_pull_request_by_number,
    list_pull_requests_for_repo,
)
from app.db_repositories.review_repo import (
    create_review_with_findings,
    get_latest_review_for_pr,
    list_reviews_for_pr,
)
from app.db_repositories.delivery_repo import (
    record_delivery_in_db,
    is_delivery_processed,
)
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


def test_repository_repo_crud(db_session):
    repo = upsert_repository(db_session, owner="Tejas190605", name="codexproj", description="Initial")
    assert repo.id is not None
    assert repo.full_name == "Tejas190605/codexproj"

    updated = upsert_repository(db_session, owner="Tejas190605", name="codexproj", description="Updated desc")
    assert updated.id == repo.id
    assert updated.description == "Updated desc"

    fetched = get_repository_by_owner_repo(db_session, "Tejas190605", "codexproj")
    assert fetched is not None
    assert len(list_all_repositories(db_session)) == 1


def test_pr_repo_crud(db_session):
    repo = upsert_repository(db_session, owner="owner", name="repo")
    pr1 = upsert_pull_request(db_session, repo.id, number=1, title="PR 1", state="open")
    pr2 = upsert_pull_request(db_session, repo.id, number=2, title="PR 2", state="closed")

    assert pr1.id is not None
    assert pr2.id is not None

    fetched_pr1 = get_pull_request_by_number(db_session, repo.id, 1)
    assert fetched_pr1.title == "PR 1"

    open_prs = list_pull_requests_for_repo(db_session, repo.id, state="open")
    assert len(open_prs) == 1
    assert open_prs[0].number == 1

    all_prs = list_pull_requests_for_repo(db_session, repo.id, state="all")
    assert len(all_prs) == 2


def test_review_repo_crud(db_session):
    repo = upsert_repository(db_session, owner="owner", name="repo")
    pr = upsert_pull_request(db_session, repo.id, number=5, title="Feature PR")

    structured = StructuredReview(
        summary="Well structured feature",
        overall_rating=8,
        findings=[
            ReviewFinding(
                title="Unchecked input",
                category=ReviewCategory.SECURITY,
                severity=ReviewSeverity.MEDIUM,
                file="app.py",
                line=10,
                description="Validate params",
                suggested_fix="add check"
            )
        ]
    )

    review = create_review_with_findings(
        db_session,
        pull_request_id=pr.id,
        summary=structured.summary,
        overall_rating=structured.overall_rating,
        markdown="### Review",
        structured_review=structured
    )

    assert review.id is not None
    assert review.overall_rating == 8

    latest = get_latest_review_for_pr(db_session, pr.id)
    assert latest is not None
    assert latest.id == review.id
    assert len(latest.findings) == 1
    assert latest.findings[0].category == "security"
    assert latest.findings[0].severity == "medium"


def test_delivery_repo_crud(db_session):
    assert not is_delivery_processed(db_session, "deliv-999")
    delivery = record_delivery_in_db(db_session, "deliv-999")
    assert delivery is not None
    assert is_delivery_processed(db_session, "deliv-999")
