from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    func
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now() -> datetime:
    """Returns current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class User(Base):
    """Database model for CodeSage AI users authenticated via GitHub OAuth."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True)
    name = Column(String(200), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    role = Column(String(50), default="member")  # admin, member, viewer
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    memberships = relationship("OrgMembership", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Organization(Base):
    """Database model for GitHub organizations onboarded to CodeSage AI."""
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    login = Column(String(100), unique=True, index=True, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    memberships = relationship("OrgMembership", back_populates="organization", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, login='{self.login}')>"


class OrgMembership(Base):
    """Join table linking Users to Organizations with role-based attributes."""
    __tablename__ = "org_memberships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="member")  # admin, member
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")


class Installation(Base):
    """Database model for GitHub App installations across user accounts and organizations."""
    __tablename__ = "installations"

    id = Column(Integer, primary_key=True, index=True)
    installation_id = Column(Integer, unique=True, index=True, nullable=False)
    account_login = Column(String(100), index=True, nullable=False)
    account_id = Column(Integer, index=True, nullable=False)
    account_type = Column(String(50), default="User")  # User or Organization
    target_type = Column(String(50), default="User")
    repository_selection = Column(String(50), default="all")  # all or selected
    status = Column(String(50), default="active")  # active, suspended, deleted
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    repositories = relationship("Repository", back_populates="installation")

    def __repr__(self) -> str:
        return f"<Installation(id={self.id}, installation_id={self.installation_id}, account='{self.account_login}')>"


class Repository(Base):
    """Database model for GitHub repositories monitored by CodeSage AI."""
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(100), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    full_name = Column(String(200), nullable=False, unique=True, index=True)
    default_branch = Column(String(100), default="main")
    private = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    installation_id = Column(Integer, ForeignKey("installations.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    installation = relationship("Installation", back_populates="repositories")
    pull_requests = relationship("PullRequest", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Repository(id={self.id}, full_name='{self.full_name}')>"


class PullRequest(Base):
    """Database model for GitHub Pull Requests analyzed by CodeSage AI."""
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    github_pr_id = Column(Integer, nullable=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    number = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    state = Column(String(50), default="open", index=True)
    author = Column(String(100), nullable=True)
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    changed_files = Column(Integer, default=0)
    commits = Column(Integer, default=0)
    html_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    repository = relationship("Repository", back_populates="pull_requests")
    reviews = relationship("Review", back_populates="pull_request", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<PullRequest(id={self.id}, number={self.number}, title='{self.title}')>"


class Review(Base):
    """Database model for AI reviews generated by CodeSage AI."""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    pull_request_id = Column(Integer, ForeignKey("pull_requests.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=True)
    overall_rating = Column(Integer, nullable=True)
    markdown = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())

    pull_request = relationship("PullRequest", back_populates="reviews")
    findings = relationship("Finding", back_populates="review", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Review(id={self.id}, rating={self.overall_rating})>"


class Finding(Base):
    """Database model for granular code review findings (bugs, security, style)."""
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True, index=True)
    severity = Column(String(50), nullable=True, index=True)
    file = Column(String(500), nullable=True)
    line = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    suggested_fix = Column(Text, nullable=True)

    review = relationship("Review", back_populates="findings")

    def __repr__(self) -> str:
        return f"<Finding(id={self.id}, severity='{self.severity}', title='{self.title}')>"


class WebhookDelivery(Base):
    """Database model for tracking GitHub Webhook delivery IDs and preventing duplicates."""
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(String(100), unique=True, index=True, nullable=False)
    received_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    processed = Column(Boolean, default=True)
    status = Column(String(50), default="received")

    def __repr__(self) -> str:
        return f"<WebhookDelivery(delivery_id='{self.delivery_id}', status='{self.status}')>"


class ReviewJob(Base):
    """Database model for tracking background AI review jobs, attempts, status, and worker metadata."""
    __tablename__ = "review_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True, nullable=False)
    repository = Column(String(200), nullable=False, index=True)
    pr_number = Column(Integer, nullable=False, index=True)
    pr_title = Column(String(255), nullable=True)
    delivery_id = Column(String(100), nullable=True, index=True)
    status = Column(String(50), default="queued", index=True)  # queued, running, completed, failed, retry, dead_letter
    priority = Column(Integer, default=0)
    attempts = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    failure_reason = Column(Text, nullable=True)
    worker_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<ReviewJob(job_id='{self.job_id}', repo='{self.repository}', pr=#{self.pr_number}, status='{self.status}')>"


class AIProvider(Base):
    """Database model for registered LLM providers (Gemini, OpenAI, Claude)."""
    __tablename__ = "ai_providers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)
    cost_per_1k_input = Column(String(20), default="0.00015")
    cost_per_1k_output = Column(String(20), default="0.00060")
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())


class PromptTemplate(Base):
    """Database model for central prompt registry and versioning."""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    version = Column(String(20), nullable=False)
    template_text = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())


class AIUsage(Base):
    """Database model for AI token analytics and cost tracking."""
    __tablename__ = "ai_usage"

    id = Column(Integer, primary_key=True, index=True)
    repository = Column(String(200), index=True, nullable=True)
    provider = Column(String(50), index=True, nullable=False)
    model = Column(String(100), nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    estimated_cost = Column(String(30), default="0.0000")
    latency_ms = Column(Integer, default=0)
    status = Column(String(50), default="success")  # success, error, retry
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())


class EvaluationRun(Base):
    """Database model for AI evaluation benchmark runs."""
    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    status = Column(String(50), default="completed")  # running, completed, failed
    quality_score = Column(Integer, default=95)
    total_tests = Column(Integer, default=10)
    passed_tests = Column(Integer, default=10)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())

    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    """Granular test result for an AI evaluation run."""
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False)
    test_case_name = Column(String(150), nullable=False)
    passed = Column(Boolean, default=True)
    score = Column(Integer, default=100)
    details = Column(Text, nullable=True)

    run = relationship("EvaluationRun", back_populates="results")


class ModelConfiguration(Base):
    """Per-repository/organization AI model parameters."""
    __tablename__ = "model_configurations"

    id = Column(Integer, primary_key=True, index=True)
    owner_repo = Column(String(200), unique=True, index=True, nullable=False)
    provider = Column(String(50), default="gemini")
    model = Column(String(100), default="gemini-2.5-flash")
    temperature = Column(String(10), default="0.2")
    max_tokens = Column(Integer, default=4096)
    review_depth = Column(String(50), default="thorough")
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class RepositoryIndex(Base):
    """Database model tracking repository indexing state, commit sha, and chunk counts."""
    __tablename__ = "repository_indexes"

    id = Column(Integer, primary_key=True, index=True)
    repository = Column(String(200), unique=True, index=True, nullable=False)
    commit_sha = Column(String(40), nullable=False)
    branch = Column(String(100), default="main")
    status = Column(String(50), default="pending", index=True)  # pending, indexing, completed, partial, failed
    index_version = Column(String(20), default="1.0.0")
    embedding_provider = Column(String(50), default="gemini")
    embedding_model = Column(String(100), default="text-embedding-004")
    chunk_count = Column(Integer, default=0)
    indexed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    chunks = relationship("CodeChunk", back_populates="repository_index", cascade="all, delete-orphan")


class CodeChunk(Base):
    """Database model storing semantic code chunks, AST metadata, content hashes, and vector embeddings."""
    __tablename__ = "code_chunks"

    id = Column(Integer, primary_key=True, index=True)
    repository = Column(String(200), index=True, nullable=False)
    repository_index_id = Column(Integer, ForeignKey("repository_indexes.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(500), index=True, nullable=False)
    language = Column(String(50), index=True, nullable=False)
    symbol_name = Column(String(200), index=True, nullable=True)
    symbol_type = Column(String(50), index=True, nullable=True)  # function, class, method, interface, struct, module
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), index=True, nullable=False)
    embedding = Column(JSON, nullable=True)  # Stores vector embedding list float data
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    repository_index = relationship("RepositoryIndex", back_populates="chunks")


class ReviewPolicy(Base):
    """Database model for system, organization, or repository-level review policies."""
    __tablename__ = "review_policies"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    version = Column(String(20), default="1.0.0")
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    rules = relationship("ReviewRule", back_populates="policy", cascade="all, delete-orphan")


class ReviewRule(Base):
    """Database model for individual policy rules (security, quality, secrets, dependencies, etc.)."""
    __tablename__ = "review_rules"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("review_policies.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_key = Column(String(100), index=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="security", index=True)
    severity = Column(String(20), default="high", index=True)
    enabled = Column(Boolean, default=True)
    configuration = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    policy = relationship("ReviewPolicy", back_populates="rules")


class PolicyEvaluation(Base):
    """Snapshot log of policy evaluations for a code review run."""
    __tablename__ = "policy_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=True, index=True)
    policy_id = Column(Integer, ForeignKey("review_policies.id", ondelete="SET NULL"), nullable=True, index=True)
    passed = Column(Boolean, default=True)
    warning_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    blocking_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())

    rule_evaluations = relationship("RuleEvaluation", back_populates="policy_evaluation", cascade="all, delete-orphan")


class RuleEvaluation(Base):
    """Granular rule execution result within a policy evaluation."""
    __tablename__ = "rule_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    policy_evaluation_id = Column(Integer, ForeignKey("policy_evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(Integer, ForeignKey("review_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    rule_key = Column(String(100), nullable=False)
    status = Column(String(20), default="pass")  # pass, warning, fail, skipped
    message = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=True)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now())

    policy_evaluation = relationship("PolicyEvaluation", back_populates="rule_evaluations")


class AuditEvent(Base):
    """Database model for tracking application audit events, lifecycle hooks, and security activity."""
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    event_type = Column(String(100), index=True, nullable=False)
    actor = Column(String(150), default="system", index=True, nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)

    description = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now(), index=True)




