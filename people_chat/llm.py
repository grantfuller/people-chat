"""
LLM provider abstraction layer.
Supports OpenAI-compatible APIs (OpenAI, DeepSeek, Groq), Anthropic, and Ollama.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Optional

from . import config as cfg


class LLMResponse:
    """Structured response from any LLM provider."""

    def __init__(self, content: str, model: str, provider: str, raw: Optional[dict] = None):
        self.content = content
        self.model = model
        self.provider = provider
        self.raw = raw or {}

    def __repr__(self):
        preview = self.content[:80].replace(chr(10), " ")
        return f"<LLMResponse {self.provider}/{self.model}: '{preview}...'>"


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, config: cfg.ProviderConfig):
        self.config = cfg.apply_defaults(config)
        self._client = None

    @abstractmethod
    def _build_client(self):
        """Initialize the API client."""
        ...

    @abstractmethod
    def send_prompt(self, prompt: str, system: Optional[str] = None, **kwargs) -> LLMResponse:
        """
        Send a prompt to the LLM and return the response.

        Args:
            prompt: The user/assistant prompt text
            system: Optional system message
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with content, model, and provider metadata
        """
        ...


class OpenAICompatibleProvider(LLMProvider):
    """
    Provider for OpenAI-compatible APIs.
    Works with: OpenAI, DeepSeek, Groq, Together AI, etc.
    """

    def _build_client(self):
        from openai import OpenAI
        return OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )

    @property
    def client(self):
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def send_prompt(self, prompt: str, system: Optional[str] = None, **kwargs) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.config.model),
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
        )

        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            model=response.model,
            provider=self.config.provider,
            raw=response.model_dump() if hasattr(response, 'model_dump') else {},
        )


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic Claude API."""

    def _build_client(self):
        import anthropic
        return anthropic.Anthropic(
            api_key=self.config.api_key,
            timeout=self.config.timeout,
        )

    @property
    def client(self):
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def send_prompt(self, prompt: str, system: Optional[str] = None, **kwargs) -> LLMResponse:
        message = self.client.messages.create(
            model=kwargs.get("model", self.config.model),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )

        content = message.content[0].text if message.content else ""
        return LLMResponse(
            content=content,
            model=message.model,
            provider=self.config.provider,
            raw={},
        )


class OllamaProvider(LLMProvider):
    """Provider for local Ollama inference. Free, runs on any machine."""

    def _build_client(self):
        from openai import OpenAI
        return OpenAI(
            api_key="ollama",  # Ollama doesn't need a real key
            base_url=self.config.base_url or "http://localhost:11434/v1",
            timeout=self.config.timeout,
        )

    @property
    def client(self):
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def send_prompt(self, prompt: str, system: Optional[str] = None, **kwargs) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=kwargs.get("model", self.config.model),
            messages=messages,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            stream=False,
        )

        content = response.choices[0].message.content or ""
        return LLMResponse(
            content=content,
            model=response.model,
            provider="ollama",
            raw={},
        )


# ─── Provider Factory ────────────────────────────────────

PROVIDER_REGISTRY = {
    "openai": OpenAICompatibleProvider,
    "deepseek": OpenAICompatibleProvider,
    "groq": OpenAICompatibleProvider,
    "together": OpenAICompatibleProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


def get_provider(config: Optional[cfg.ProviderConfig] = None) -> LLMProvider:
    """
    Factory function — returns the right provider based on config.

    Usage:
        provider = get_provider()
        response = provider.send_prompt("Hello!", system="You are helpful")
        print(response.content)
    """
    if config is None:
        config = cfg.ProviderConfig()

    provider_class = PROVIDER_REGISTRY.get(config.provider)
    if provider_class is None:
        supported = ", ".join(PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"Unknown provider '{config.provider}'. Supported: {supported}"
        )

    return provider_class(config)


def test_provider(provider: LLMProvider) -> LLMResponse:
    """Quick test — send a simple prompt to verify the provider works."""
    return provider.send_prompt(
        "Respond with exactly: OK. No other text.",
        system="You are a test assistant. Be concise."
    )
