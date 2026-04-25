from __future__ import annotations

from trader.agent_layer.llm import StatelessLLMClient
from trader.models import AttributionEvidence, AttributionResult


ATTRIBUTION_SYSTEM_PROMPT = """You are an objective market attribution analyst.
Correlate price action with supplied news only. Distinguish observed facts from inference.
Do not invent events. Return a concise narrative suitable for a local trading journal."""


class AttributionEngine:
    def __init__(self, llm_client: StatelessLLMClient):
        self.llm_client = llm_client

    def run(self, market_snapshot: dict) -> AttributionResult:
        payload = {
            "ticker": market_snapshot["ticker"],
            "timeframe": market_snapshot["timeframe"],
            "prices": market_snapshot["prices"][-30:],
            "news": market_snapshot["news"][:10],
        }
        narrative, llm_used = self.llm_client.complete(
            system_prompt=ATTRIBUTION_SYSTEM_PROMPT,
            user_payload=payload,
        )
        return AttributionResult(
            ticker=market_snapshot["ticker"],
            timeframe=market_snapshot["timeframe"],
            narrative=narrative,
            evidence=_build_evidence(market_snapshot),
            llm_used=llm_used,
        )


def _build_evidence(market_snapshot: dict) -> list[AttributionEvidence]:
    prices = market_snapshot.get("prices") or []
    news = market_snapshot.get("news") or []
    evidence: list[AttributionEvidence] = []

    if len(prices) >= 2:
        start = prices[0]
        end = prices[-1]
        start_close = float(start["close"])
        end_close = float(end["close"])
        move_pct = ((end_close / start_close) - 1) * 100 if start_close else 0.0
        evidence.append(
            AttributionEvidence(
                label="Price move",
                detail=f"{start['date']} close {start_close:.2f} to {end['date']} close {end_close:.2f}: {move_pct:+.2f}%",
                source=market_snapshot.get("provider"),
            )
        )

    for item in news[:3]:
        evidence.append(
            AttributionEvidence(
                label="News context",
                detail=item.get("title", "Untitled"),
                source=item.get("publisher"),
            )
        )
    return evidence

