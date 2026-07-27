"""
Configuration loader for People Chat.
Reads environment variables to determine LLM provider, model, and API keys.
"""

import os
from pathlib import Path
from typing import Optional

DOT_ENV_PATH = Path.home() / ".people-chat" / ".env"


def load_dotenv(path: Optional[Path] = None) -> None:
    """Load .env file if it exists."""
    env_path = path or DOT_ENV_PATH
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                if key not in os.environ:
                    os.environ[key] = value


class ProviderConfig:
    """Holds the active LLM provider configuration."""

    def __init__(self):
        load_dotenv()

        self.provider: str = os.getenv("LLM_PROVIDER", "deepseek").lower()
        self.api_key: Optional[str] = os.getenv("LLM_API_KEY")
        self.model: str = os.getenv("LLM_MODEL", "deepseek-chat")
        self.base_url: Optional[str] = os.getenv("LLM_BASE_URL")
        self.max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))
        self.temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
        self.timeout: int = int(os.getenv("LLM_TIMEOUT", "30"))

    def validate(self) -> list:
        """Return list of missing required config items."""
        missing = []
        if self.provider != "ollama" and not self.api_key:
            missing.append(f"LLM_API_KEY (required for provider '{self.provider}')")
        return missing


# Provider defaults
PROVIDER_DEFAULTS = {
    "openai": {
        "model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
    },
    "anthropic": {
        "model": "claude-3-haiku-20240307",
        "base_url": "https://api.anthropic.com",
    },
    "deepseek": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
    },
    "ollama": {
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
    },
}


def apply_defaults(cfg: ProviderConfig) -> ProviderConfig:
    """Apply provider-specific defaults for any unset fields."""
    defaults = PROVIDER_DEFAULTS.get(cfg.provider, {})
    if not cfg.model or cfg.model == "deepseek-chat" and cfg.provider != "deepseek":
        cfg.model = defaults.get("model", cfg.model)
    if not cfg.base_url:
        cfg.base_url = defaults.get("base_url")
    return cfg
