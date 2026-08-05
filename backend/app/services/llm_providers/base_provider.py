from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Unified response object returned by all LLM providers."""
    content: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    latency_ms: int = 0
    raw_response: Optional[Dict[str, Any]] = None


class BaseLLMProvider(ABC):
    """Abstract Base Class for Multi-LLM Providers (Gemini, OpenAI, Claude)."""

    def __init__(self, name: str, default_model: str):
        self.name = name
        self.default_model = default_model

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> LLMResponse:
        """Generates AI completion for a given prompt."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Returns True if provider API credentials and connection are operational."""
        pass

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimates cost in USD based on token counts."""
        return (prompt_tokens * 0.00015 / 1000) + (completion_tokens * 0.00060 / 1000)
