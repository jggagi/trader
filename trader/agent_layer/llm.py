from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

import requests


class StatelessLLMClient(Protocol):
    def complete(self, *, system_prompt: str, user_payload: dict[str, Any]) -> tuple[str, bool]:
        """Return generated text and whether an external LLM was used."""


@dataclass(frozen=True)
class LocalFallbackLLMClient:
    reason: str = "OPENAI_API_KEY is not configured"

    def complete(self, *, system_prompt: str, user_payload: dict[str, Any]) -> tuple[str, bool]:
        ticker = user_payload.get("ticker") or user_payload.get("market_snapshot", {}).get("ticker") or "the asset"
        timeframe = user_payload.get("timeframe") or user_payload.get("market_snapshot", {}).get("timeframe") or "selected period"
        return (
            f"Local placeholder: review {ticker} over {timeframe} using the supplied price and news context. "
            f"No external LLM call was made because {self.reason}.",
            False,
        )


@dataclass(frozen=True)
class OpenAIResponsesClient:
    api_key: str
    model: str = "gpt-4o-mini"
    timeout_seconds: int = 45

    def complete(self, *, system_prompt: str, user_payload: dict[str, Any]) -> tuple[str, bool]:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, ensure_ascii=False, default=str),
                    },
                ],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        return _extract_response_text(body), True


def build_default_llm_client() -> StatelessLLMClient:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return LocalFallbackLLMClient()
    return OpenAIResponsesClient(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )


def _extract_response_text(body: dict[str, Any]) -> str:
    text = body.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    chunks: list[str] = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(str(content["text"]))
    return "\n".join(chunks).strip() or "No model output returned."

