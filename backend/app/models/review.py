from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ReviewCategory(str, Enum):
    """Categorization for AI code review findings."""
    SECURITY = "security"
    BUG_RISK = "bug_risk"
    CODE_QUALITY = "code_quality"
    PERFORMANCE = "performance"
    BEST_PRACTICE = "best_practice"


class ReviewSeverity(str, Enum):
    """Severity levels for code review findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReviewFinding(BaseModel):
    """Represents an individual issue or suggestion identified by AI code review."""
    title: str = Field(description="Short summary title of the finding")
    category: ReviewCategory = Field(description="Finding category")
    severity: ReviewSeverity = Field(description="Severity level")
    file: Optional[str] = Field(default=None, description="Filename where issue occurs")
    line: Optional[int] = Field(default=None, description="1-indexed line number if applicable")
    description: str = Field(description="Detailed explanation of the issue")
    suggested_fix: Optional[str] = Field(default=None, description="Recommended code fix or patch suggestion")


class StructuredReview(BaseModel):
    """Structured result model for a complete AI code review."""
    summary: str = Field(description="Executive summary of the pull request review")
    overall_rating: int = Field(ge=1, le=10, description="Overall code quality rating from 1 to 10")
    findings: List[ReviewFinding] = Field(default_factory=list, description="List of identified findings")
