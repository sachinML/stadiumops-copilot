from __future__ import annotations

from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class Settings:
    app_title: str = "StadiumOps Copilot (FIFA World Cup 2026)"

    # LLM selection
    # NOTE: use default_factory (not a bare `os.getenv(...)` default) so each
    # Settings() instantiation reads *current* env vars, rather than caching
    # whatever was set the first time this module was imported.
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "ollama").lower())

    # Ollama (no API key) - requires local Ollama server
    ollama_base_url: str = field(default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3.1"))

    # OpenAI-compatible (optional)
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    # App behavior
    demo_tournament_name: str = field(default_factory=lambda: os.getenv("TOURNAMENT_NAME", "FIFA World Cup 2026"))
    demo_venue_name: str = field(default_factory=lambda: os.getenv("VENUE_NAME", "Metropolis Stadium"))


def get_settings() -> Settings:
    return Settings()

