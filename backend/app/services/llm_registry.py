import logging
from typing import Any, Dict, List, Optional
from app.services.llm_providers.base_provider import BaseLLMProvider, LLMResponse
from app.services.llm_providers.gemini_provider import GeminiProvider
from app.services.llm_providers.openai_provider import OpenAIProvider
from app.services.llm_providers.claude_provider import ClaudeProvider
from app.utils.circuit_breaker import gemini_ai_circuit_breaker

logger = logging.getLogger("codesage.llm_registry")


class LLMRegistry:
    """
    LLM Provider Registry supporting priority routing, health-aware fallback,
    and Circuit Breaker integration across Gemini, OpenAI, and Claude.
    """
    def __init__(self):
        self._providers: Dict[str, BaseLLMProvider] = {}
        self._priority_order: List[str] = ["gemini", "openai", "claude"]
        self._register_default_providers()

    def _register_default_providers(self):
        self._providers["gemini"] = GeminiProvider()
        self._providers["openai"] = OpenAIProvider()
        self._providers["claude"] = ClaudeProvider()

    def get_provider(self, name: str) -> Optional[BaseLLMProvider]:
        return self._providers.get(name.lower())

    def list_providers(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": name,
                "default_model": provider.default_model,
                "healthy": provider.health_check(),
                "priority": self._priority_order.index(name) + 1 if name in self._priority_order else 99
            }
            for name, provider in self._providers.items()
        ]

    def generate_with_fallback(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        preferred_provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> LLMResponse:
        """
        Attempts execution using preferred_provider first, falling back through priority list
        if the primary provider fails or is circuit broken.
        """
        order = list(self._priority_order)
        if preferred_provider and preferred_provider in order:
            order.remove(preferred_provider)
            order.insert(0, preferred_provider)

        last_error = None
        for provider_name in order:
            provider = self._providers.get(provider_name)
            if not provider:
                continue

            try:
                logger.info(f"Attempting LLM completion using provider: '{provider_name}'...")
                if provider_name == "gemini":
                    # Execute Gemini through circuit breaker
                    return gemini_ai_circuit_breaker.call(
                        provider.generate,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                else:
                    return provider.generate(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
            except Exception as e:
                logger.warning(f"LLM Provider '{provider_name}' failed: {e}. Trying fallback...")
                last_error = e

        raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")


# Singleton Registry Instance
llm_registry = LLMRegistry()
