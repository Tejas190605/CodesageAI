import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.db import ReviewPolicy, ReviewRule, PolicyEvaluation, RuleEvaluation, Review
from app.services.policy_config import get_effective_policy
from app.services.policy_engine import evaluate_policy_for_pr

logger = logging.getLogger("codesage.routes.policies")

router = APIRouter(tags=["Policy Engine & Review Rules"])


class PolicyUpdateRequest(BaseModel):
    rules: Optional[Dict[str, Dict[str, Any]]] = None
    ignore_paths: Optional[List[str]] = None
    ignore_rules: Optional[List[str]] = None


@router.get("/api/policies")
def list_policies(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Lists all configured policies in the system."""
    policies = db.query(ReviewPolicy).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "enabled": p.enabled,
            "version": p.version,
            "rule_count": len(p.rules) if p.rules else 0,
            "created_at": p.created_at.isoformat() if p.created_at else None
        }
        for p in policies
    ]


@router.get("/api/policies/effective/{owner}/{repo}")
def get_effective_repo_policy(owner: str, repo: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves resolved effective review policy hierarchy for a repository."""
    repository = f"{owner}/{repo}"
    effective = get_effective_policy()
    return {
        "repository": repository,
        "effective_policy": effective
    }


@router.put("/api/policies/repositories/{owner}/{repo}")
def update_repo_policy(
    owner: str,
    repo: str,
    payload: PolicyUpdateRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Updates custom policy rules for a repository."""
    repository = f"{owner}/{repo}"
    policy_rec = db.query(ReviewPolicy).filter(ReviewPolicy.name == f"repo:{repository}").first()
    if not policy_rec:
        policy_rec = ReviewPolicy(
            name=f"repo:{repository}",
            description=f"Custom policy rules for {repository}",
            enabled=True
        )
        db.add(policy_rec)
        db.commit()
        db.refresh(policy_rec)

    if payload.rules:
        for r_key, r_cfg in payload.rules.items():
            rule_rec = db.query(ReviewRule).filter(
                ReviewRule.policy_id == policy_rec.id,
                ReviewRule.rule_key == r_key
            ).first()
            if not rule_rec:
                rule_rec = ReviewRule(
                    policy_id=policy_rec.id,
                    rule_key=r_key,
                    name=r_key.title().replace("-", " "),
                    category=r_cfg.get("category", "security"),
                    severity=r_cfg.get("severity", "high"),
                    enabled=r_cfg.get("enabled", True),
                    configuration=r_cfg
                )
                db.add(rule_rec)
            else:
                rule_rec.enabled = r_cfg.get("enabled", rule_rec.enabled)
                rule_rec.severity = r_cfg.get("severity", rule_rec.severity)
                rule_rec.configuration = r_cfg

    db.commit()
    return {
        "message": f"Successfully updated review policy for '{repository}'.",
        "policy_id": policy_rec.id
    }


@router.get("/api/reviews/{review_id}/policy")
def get_review_policy_evaluation(review_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves PolicyEvaluation audit snapshot and rule execution results for a review."""
    eval_rec = db.query(PolicyEvaluation).filter(PolicyEvaluation.review_id == review_id).first()
    if not eval_rec:
        return {
            "review_id": review_id,
            "status": "unevaluated",
            "passed": True,
            "rule_evaluations": []
        }

    return {
        "id": eval_rec.id,
        "review_id": eval_rec.review_id,
        "passed": eval_rec.passed,
        "warning_count": eval_rec.warning_count,
        "failure_count": eval_rec.failure_count,
        "blocking_count": eval_rec.blocking_count,
        "created_at": eval_rec.created_at.isoformat() if eval_rec.created_at else None,
        "rule_evaluations": [
            {
                "id": re.id,
                "rule_key": re.rule_key,
                "status": re.status,
                "message": re.message,
                "file_path": re.file_path,
                "start_line": re.start_line,
                "end_line": re.end_line,
                "metadata": re.metadata_json
            }
            for re in eval_rec.rule_evaluations
        ]
    }
