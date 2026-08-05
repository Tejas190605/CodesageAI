import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.db import Repository, PullRequest, Review, Finding, WebhookDelivery


@pytest.fixture
def db_session():
    """In-memory SQLite database session for unit tests."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_repository_model_creation(db_session):
    repo = Repository(
        owner="Tejas190605",
        name="codexproj",
        full_name="Tejas190605/codexproj",
        default_branch="main",
        private=False,
        description="AI Developer Assistant"
    )
    db_session.add(repo)
    db_session.commit()

    saved = db_session.query(Repository).filter_by(full_name="Tejas190605/codexproj").first()
    assert saved is not None
    assert saved.id > 0
    assert saved.owner == "Tejas190605"
    assert saved.name == "codexproj"


def test_pull_request_and_review_relationships(db_session):
    repo = Repository(owner="org", name="repo", full_name="org/repo")
    db_session.add(repo)
    db_session.commit()

    pr = PullRequest(
        repository_id=repo.id,
        number=10,
        title="Add authentication",
        state="open",
        author="developer"
    )
    db_session.add(pr)
    db_session.commit()

    review = Review(
        pull_request_id=pr.id,
        summary="Solid PR",
        overall_rating=9,
        markdown="### Code Review\nRating: 9/10"
    )
    db_session.add(review)
    db_session.commit()

    finding = Finding(
        review_id=review.id,
        title="Missing type hint",
        category="quality",
        severity="LOW",
        file="app/main.py",
        line=15,
        description="Add return type annotation",
        suggested_fix="def func() -> None:"
    )
    db_session.add(finding)
    db_session.commit()

    fetched_pr = db_session.query(PullRequest).filter_by(number=10).first()
    assert fetched_pr is not None
    assert len(fetched_pr.reviews) == 1

    fetched_review = fetched_pr.reviews[0]
    assert fetched_review.overall_rating == 9
    assert len(fetched_review.findings) == 1
    assert fetched_review.findings[0].category == "quality"


def test_webhook_delivery_model(db_session):
    delivery = WebhookDelivery(
        delivery_id="deliv-12345",
        status="received",
        processed=True
    )
    db_session.add(delivery)
    db_session.commit()

    saved = db_session.query(WebhookDelivery).filter_by(delivery_id="deliv-12345").first()
    assert saved is not None
    assert saved.processed is True
