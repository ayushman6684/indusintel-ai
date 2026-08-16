"""
AIProvider abstraction (Section 5 / Section 9 of the spec).

Defines a common interface so the Extraction, Structuring, Enrichment,
Validation, and Explanation agents (app/services/agents.py) can run against
a swappable LLM backend (Anthropic Claude or Gemini) without any calling
code depending on a specific SDK.

Day 2: wired up for real with the Anthropic and Gemini SDKs. Both providers
expose `complete_json`, which asks the model for strict JSON and repairs
common formatting mistakes (markdown code fences, leading/trailing prose)
before the caller does Pydantic validation. The AI is never trusted to
return arbitrary unstructured output — see agents.py for the validation
step that always follows.
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Optional

from app.config import settings


class AIProviderError(Exception):
    """Raised when the configured AI provider fails or is misconfigured."""


class AIProvider(ABC):
    """Common interface every LLM backend must implement."""

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        """Return a raw text completion for the given prompts."""
        raise NotImplementedError

    def complete_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> dict:
        """Return a completion parsed as JSON.

        Appends a strict JSON-only instruction to the system prompt, then
        strips common formatting artifacts (```json fences, stray prose)
        before parsing. Raises AIProviderError if the result still isn't
        valid JSON after cleanup — callers must not silently swallow this,
        per the "never allow the AI to return arbitrary unstructured
        output" rule.
        """
        strict_system = (
            f"{system_prompt}\n\n"
            "CRITICAL: Respond with ONLY valid JSON. No markdown code fences, "
            "no explanation, no preamble or postamble — the entire response "
            "must be a single parseable JSON object."
        )
        raw = self.complete(strict_system, user_prompt, max_tokens=max_tokens)
        cleaned = _extract_json(raw)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise AIProviderError(f"AI did not return valid JSON: {e}\nRaw: {raw[:500]}")


def _extract_json(text: str) -> str:
    """Strip markdown code fences and surrounding prose from a model response."""
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    # Fall back to grabbing the outermost {...} or [...] block.
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            return text[start : end + 1]
    return text


class AnthropicProvider(AIProvider):
    """Claude backend, via the official Anthropic Python SDK."""

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or self.DEFAULT_MODEL
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise AIProviderError(
                    "ANTHROPIC_API_KEY is not set. Add it to backend/.env."
                )
            try:
                import anthropic
            except ImportError as e:
                raise AIProviderError(
                    "The 'anthropic' package is not installed. Run: "
                    "pip install -r requirements.txt"
                ) from e
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except Exception as e:
            raise AIProviderError(f"Anthropic API call failed: {e}") from e

        text_parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
        return "".join(text_parts)


class GeminiProvider(AIProvider):
    """Gemini backend, via Google's official `google-genai` SDK.

    Uses the `gemini-flash-latest` model alias rather than a pinned model
    ID (e.g. `gemini-2.5-flash`). Google periodically retires specific
    model IDs for new API keys — the `-latest` alias is automatically kept
    pointed at a current, free-tier-eligible Flash model, so this doesn't
    need to be updated every time Google ships a new generation.
    """

    DEFAULT_MODEL = "gemini-flash-latest"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model or self.DEFAULT_MODEL
        self._client = None

    @property
    def client(self):
        if self._client is None:
            if not self.api_key:
                raise AIProviderError("GEMINI_API_KEY is not set. Add it to backend/.env.")
            try:
                from google import genai
            except ImportError as e:
                raise AIProviderError(
                    "The 'google-genai' package is not installed. Run: "
                    "pip install -r requirements.txt"
                ) from e
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def complete(self, system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
        try:
            from google.genai import types

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=max_tokens,
                ),
            )
        except Exception as e:
            raise AIProviderError(f"Gemini API call failed: {e}") from e
        return response.text or ""


def get_ai_provider() -> AIProvider:
    """Factory selecting the configured provider (AI_PROVIDER in .env)."""
    if settings.AI_PROVIDER == "gemini":
        return GeminiProvider()
    return AnthropicProvider()
