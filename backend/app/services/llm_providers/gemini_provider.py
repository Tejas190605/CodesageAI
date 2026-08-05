import time
import logging
from typing import Optional
from app.config import settings
from app.services.llm_providers.base_provider import BaseLLMProvider, LLMResponse
from google import genai

logger = logging.getLogger("codesage.llm.gemini")


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider implementation."""

    def __init__(self):
        super().__init__(name="gemini", default_model=settings.GEMINI_MODEL)
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> LLMResponse:
        start_time = time.time()
        target_model = model or self.default_model

        contents = []
        if system_prompt:
            contents.append(f"System: {system_prompt}\n")
        contents.append(prompt)

        response = self.client.models.generate_content(
            model=target_model,
            contents="".join(contents),
        )

        latency_ms = int((time.time() - start_time) * 1000)
        content_text = response.text if hasattr(response, "text") and response.text else ""

        # Estimate tokens based on payload character heuristics
        prompt_tokens = len("".join(contents)) // 4
        completion_tokens = len(content_text) // 4
        total_tokens = prompt_tokens + completion_tokens
        cost = self.estimate_cost(prompt_tokens, completion_tokens)

        return LLMResponse(
            content=content_text,
            provider=self.name,
            model=target_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=cost,
            latency_ms=latency_ms
        )

    def health_check(self) -> bool:
        return bool(settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("test-"))
