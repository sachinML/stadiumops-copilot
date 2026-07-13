from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_title: str = "StadiumOps Copilot (FIFA World Cup 2026)"

    # LLM selection
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama").lower()

    # Ollama (no API key) - requires local Ollama server
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1")

    # OpenAI-compatible (optional)
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # App behavior
    demo_tournament_name: str = os.getenv("TOURNAMENT_NAME", "FIFA World Cup 2026")
    demo_venue_name: str = os.getenv("VENUE_NAME", "Metropolis Stadium")


def get_settings() -> Settings:
    return Settings()

