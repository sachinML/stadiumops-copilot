from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

import json
import os

import httpx

Role = Literal["system", "user", "assistant"]


def _degraded_response(*, provider: str, error: Exception) -> str:
    """
    Never let a transient network/API failure crash the app mid-demo.
    Surface a clear, honest message instead of an unhandled traceback.
    """
    kind = type(error).__name__
    if isinstance(error, httpx.TimeoutException):
        reason = "The request timed out."
    elif isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code if error.response is not None else "unknown"
        reason = f"The provider returned an HTTP {status} error (e.g. rate limit or auth issue)."
    elif isinstance(error, httpx.ConnectError):
        reason = "Could not connect to the LLM provider."
    else:
        reason = f"Unexpected error ({kind})."

    return (
        "I couldn't reach the GenAI provider just now, so here's a graceful fallback "
        "instead of an error page.\n\n"
        f"**Provider**: `{provider}`\n"
        f"**Issue**: {reason}\n\n"
        "Please try again in a moment. If this persists, check the provider's API key, "
        "rate limits, and base URL configuration."
    )


@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str


class LLM(Protocol):
    def name(self) -> str: ...

    def is_live(self) -> bool: ...

    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.2) -> str: ...


class OllamaLLM:
    def __init__(self, *, base_url: str, model: str, timeout_s: float = 30.0):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_s = timeout_s
        self._live: bool | None = None

    def name(self) -> str:
        return f"ollama:{self._model}"

    def is_live(self) -> bool:
        if self._live is None:
            self._live = self._check_live()
        return self._live

    def _check_live(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.2) -> str:
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": float(temperature)},
        }
        try:
            with httpx.Client(timeout=self._timeout_s) as client:
                r = client.post(f"{self._base_url}/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
                msg = data.get("message", {}) if isinstance(data, dict) else {}
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
            return ""
        except Exception as exc:
            return _degraded_response(provider=self.name(), error=exc)


class OpenAICompatibleLLM:
    """
    Minimal OpenAI-compatible chat client over HTTP.
    Works with OpenAI, Azure OpenAI (via compatible gateway), or any /v1/chat/completions provider.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_s: float = 45.0,
    ):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_s = timeout_s

    def name(self) -> str:
        return f"openai-compatible:{self._model}"

    def is_live(self) -> bool:
        return True

    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.2) -> str:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": float(temperature),
        }
        try:
            with httpx.Client(timeout=self._timeout_s, headers=headers) as client:
                r = client.post(f"{self._base_url}/chat/completions", json=payload)
                r.raise_for_status()
                data = r.json()
                try:
                    return (
                        data["choices"][0]["message"]["content"].strip()
                        if data["choices"][0]["message"]["content"]
                        else ""
                    )
                except (KeyError, IndexError, TypeError):
                    return json.dumps(data, indent=2)[:2000]
        except Exception as exc:
            return _degraded_response(provider=self.name(), error=exc)


class MockLLM:
    def __init__(self, *, reason: str):
        self._reason = reason

    def name(self) -> str:
        return "mock"

    def is_live(self) -> bool:
        return False

    def chat(self, messages: list[ChatMessage], *, temperature: float = 0.2) -> str:
        user_last = next((m.content for m in reversed(messages) if m.role == "user"), "")
        return (
            "I’m running in **mock mode** (no live LLM available).\n\n"
            f"Reason: {self._reason}\n\n"
            "Here’s a structured answer based on the stadium data and rules I have:\n\n"
            f"{user_last[:1200]}"
        )


def build_llm(settings: Any) -> LLM:
    provider = (getattr(settings, "llm_provider", None) or os.getenv("LLM_PROVIDER", "ollama")).lower()

    if provider == "ollama":
        llm = OllamaLLM(
            base_url=getattr(settings, "ollama_base_url", "http://localhost:11434"),
            model=getattr(settings, "ollama_model", "llama3.1"),
        )
        if llm.is_live():
            return llm
        return MockLLM(reason="Ollama not reachable at OLLAMA_BASE_URL (start `ollama serve`).")

    if provider in {"openai", "openai-compatible"}:
        key = getattr(settings, "openai_api_key", None) or os.getenv("OPENAI_API_KEY")
        if not key:
            return MockLLM(reason="OPENAI_API_KEY not set.")
        return OpenAICompatibleLLM(
            base_url=getattr(settings, "openai_base_url", "https://api.openai.com/v1"),
            api_key=key,
            model=getattr(settings, "openai_model", "gpt-4o-mini"),
        )

    return MockLLM(reason=f"Unknown LLM_PROVIDER={provider!r}. Use 'ollama' or 'openai'.")

