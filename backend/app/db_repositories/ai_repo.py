from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.db import (
    AIProvider,
    PromptTemplate,
    AIUsage,
    EvaluationRun,
    EvaluationResult,
    ModelConfiguration
)


def get_active_providers(db: Session) -> List[AIProvider]:
    return db.query(AIProvider).filter(AIProvider.is_active == True).order_by(AIProvider.priority).all()


def list_prompt_templates(db: Session) -> List[PromptTemplate]:
    return db.query(PromptTemplate).order_by(PromptTemplate.created_at.desc()).all()


def log_ai_usage(
    db: Session,
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    estimated_cost: float,
    latency_ms: int,
    repository: Optional[str] = None
) -> AIUsage:
    usage = AIUsage(
        repository=repository,
        provider=provider,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        estimated_cost=f"{estimated_cost:.6f}",
        latency_ms=latency_ms
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage


def get_ai_usage_analytics(db: Session, limit: int = 50) -> List[AIUsage]:
    return db.query(AIUsage).order_by(AIUsage.created_at.desc()).limit(limit).all()


def get_evaluation_runs(db: Session, limit: int = 20) -> List[EvaluationRun]:
    return db.query(EvaluationRun).order_by(EvaluationRun.created_at.desc()).limit(limit).all()


def get_model_config(db: Session, owner_repo: str) -> Optional[ModelConfiguration]:
    return db.query(ModelConfiguration).filter(ModelConfiguration.owner_repo == owner_repo).first()


def upsert_model_config(
    db: Session,
    owner_repo: str,
    provider: str = "gemini",
    model: str = "gemini-2.5-flash",
    temperature: str = "0.2",
    max_tokens: int = 4096,
    review_depth: str = "thorough"
) -> ModelConfiguration:
    config = get_model_config(db, owner_repo)
    if not config:
        config = ModelConfiguration(
            owner_repo=owner_repo,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            review_depth=review_depth
        )
        db.add(config)
    else:
        config.provider = provider
        config.model = model
        config.temperature = temperature
        config.max_tokens = max_tokens
        config.review_depth = review_depth

    db.commit()
    db.refresh(config)
    return config
