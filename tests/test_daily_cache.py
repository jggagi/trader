from datetime import date

from trader.agent_layer.daily_cache import (
    build_daily_cache_key,
    load_daily_analysis,
    save_daily_analysis,
)
from trader.models import AttributionResult, CritiqueResult, CritiqueView


def test_daily_cache_key_changes_by_day() -> None:
    today = build_daily_cache_key(
        provider="yahoo", ticker="AAPL", timeframe="1mo", day=date(2026, 5, 23)
    )
    tomorrow = build_daily_cache_key(
        provider="yahoo", ticker="AAPL", timeframe="1mo", day=date(2026, 5, 24)
    )

    assert today != tomorrow
    assert "AAPL" in today


def test_daily_analysis_round_trips(tmp_path) -> None:
    cache_key = "2026-05-23__yahoo__AAPL__1mo"
    attribution = AttributionResult(
        ticker="AAPL", timeframe="1mo", narrative="归因", llm_used=True
    )
    critique = CritiqueResult(
        views=[CritiqueView(name="Warren Buffett", commentary="批判", llm_used=True)]
    )

    saved = save_daily_analysis(
        cache_key=cache_key,
        attribution=attribution,
        critique=critique,
        cache_dir=tmp_path,
    )
    loaded = load_daily_analysis(cache_key, cache_dir=tmp_path)

    assert not saved.cache_hit
    assert loaded is not None
    assert loaded.cache_hit
    assert loaded.attribution.narrative == "归因"
    assert loaded.critique.views[0].name == "Warren Buffett"
