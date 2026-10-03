from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from trader.models import AttributionResult, CritiqueResult


@dataclass(frozen=True)
class DailyAnalysis:
    attribution: AttributionResult
    critique: CritiqueResult
    generated_at: str
    cache_hit: bool


def build_daily_cache_key(*, provider: str, ticker: str, timeframe: str, day: date | None = None) -> str:
    cache_day = day or date.today()
    safe_parts = [
        cache_day.isoformat(),
        provider.lower().replace("/", "_"),
        ticker.upper().replace("/", "_"),
        timeframe.lower().replace("/", "_"),
    ]
    return "__".join(safe_parts)


def get_daily_cache_path(cache_key: str, cache_dir: Path | None = None) -> Path:
    root = cache_dir or Path(".cache") / "market_lens" / "daily_analysis"
    return root / f"{cache_key}.json"


def load_daily_analysis(cache_key: str, cache_dir: Path | None = None) -> DailyAnalysis | None:
    path = get_daily_cache_path(cache_key, cache_dir)
    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    return DailyAnalysis(
        attribution=AttributionResult.model_validate(payload["attribution"]),
        critique=CritiqueResult.model_validate(payload["critique"]),
        generated_at=payload["generated_at"],
        cache_hit=True,
    )


def save_daily_analysis(
    *,
    cache_key: str,
    attribution: AttributionResult,
    critique: CritiqueResult,
    cache_dir: Path | None = None,
) -> DailyAnalysis:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload: dict[str, Any] = {
        "generated_at": generated_at,
        "attribution": attribution.model_dump(),
        "critique": critique.model_dump(),
    }
    path = get_daily_cache_path(cache_key, cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return DailyAnalysis(
        attribution=attribution,
        critique=critique,
        generated_at=generated_at,
        cache_hit=False,
    )


def resolve_daily_analysis(
    cache_key: str,
    *,
    should_generate: bool,
    generate: Callable[[], tuple[AttributionResult, CritiqueResult]],
    cache_results: bool = True,
    cache_dir: Path | None = None,
) -> DailyAnalysis | None:
    """Load cached analysis, or generate only after an explicit request."""
    if cache_results and not should_generate:
        cached = load_daily_analysis(cache_key, cache_dir=cache_dir)
        if cached:
            return cached

    if not should_generate:
        return None

    attribution, critique = generate()
    if not cache_results:
        return DailyAnalysis(
            attribution=attribution,
            critique=critique,
            generated_at="本次会话",
            cache_hit=False,
        )
    return save_daily_analysis(
        cache_key=cache_key,
        attribution=attribution,
        critique=critique,
        cache_dir=cache_dir,
    )
