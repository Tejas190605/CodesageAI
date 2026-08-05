from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.db import Review, Finding
from app.models.review import StructuredReview


def create_review_with_findings(
    db: Session,
    pull_request_id: int,
    summary: Optional[str],
    overall_rating: Optional[int],
    markdown: Optional[str],
    structured_review: Optional[StructuredReview] = None,
    raw_findings: Optional[List[Dict[str, Any]]] = None
) -> Review:
    """Persists a new AI code review along with its associated granular findings."""
    review = Review(
        pull_request_id=pull_request_id,
        summary=summary,
        overall_rating=overall_rating,
        markdown=markdown
    )
    db.add(review)
    db.flush()  # assign review.id

    # 1. Process StructuredReview Pydantic model if provided
    if structured_review and structured_review.findings:
        for f in structured_review.findings:
            category_val = f.category.value if hasattr(f.category, "value") else str(f.category)
            severity_val = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            finding_obj = Finding(
                review_id=review.id,
                title=f.title,
                category=category_val,
                severity=severity_val,
                file=f.file,
                line=f.line,
                description=f.description,
                suggested_fix=f.suggested_fix
            )
            db.add(finding_obj)

    # 2. Process dict list if raw_findings passed
    elif raw_findings:
        for fdict in raw_findings:
            finding_obj = Finding(
                review_id=review.id,
                title=fdict.get("title", "Review Finding"),
                category=fdict.get("category"),
                severity=fdict.get("severity"),
                file=fdict.get("file"),
                line=fdict.get("line"),
                description=fdict.get("description"),
                suggested_fix=fdict.get("suggested_fix")
            )
            db.add(finding_obj)

    db.commit()
    db.refresh(review)
    return review


def get_latest_review_for_pr(db: Session, pull_request_id: int) -> Optional[Review]:
    """Fetches the most recent Review for a given Pull Request."""
    return db.query(Review).filter(
        Review.pull_request_id == pull_request_id
    ).order_by(Review.created_at.desc(), Review.id.desc()).first()


def list_reviews_for_pr(db: Session, pull_request_id: int) -> List[Review]:
    """Lists all historical Reviews for a Pull Request ordered chronologically."""
    return db.query(Review).filter(
        Review.pull_request_id == pull_request_id
    ).order_by(Review.created_at.asc(), Review.id.asc()).all()


def list_findings_for_review(db: Session, review_id: int) -> List[Finding]:
    """Lists all findings associated with a specific review."""
    return db.query(Finding).filter(Finding.review_id == review_id).all()
