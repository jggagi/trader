from datetime import date

import pytest

from trader.agent_layer.daily_cache import (
    DailyAnalysisCacheError,
    build_daily_cache_key,
    load_daily_analysis,
    save_daily_analysis,
    resolve_daily_analysis,
)
from trader.models import AttributionResult, CritiqueResult, CritiqueView


def test_daily_cache_key_changes_by_day() -> None:
    today = build_daily_cache_key(provider="yahoo", ticker="AAPL", timeframe="1mo", day=date(2026, 5, 23))
    tomorrow = build_daily_cache_key(provider="yahoo", ticker="AAPL", timeframe="1mo", day=date(2026, 5, 24))

    assert today != tomorrow
    assert "AAPL" in today


def test_daily_analysis_round_trips(tmp_path) -> None:
    cache_key = "2026-05-23__yahoo__AAPL__1mo"
    attribution = AttributionResult(ticker="AAPL", timeframe="1mo", narrative="归因", llm_used=True)
    critique = CritiqueResult(views=[CritiqueView(name="Warren Buffett", commentary="批判", llm_used=True)])

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


def test_corrupt_cache_is_preserved_without_generation_and_can_be_explicitly_rebuilt(tmp_path):
    path = tmp_path / "synthetic.json"
    original = b'{"unfinished":'
    path.write_bytes(original)
    calls = []

    def generate():
        calls.append("explicit")
        return AttributionResult(ticker="SYNTH", timeframe="1mo", narrative="synthetic"), CritiqueResult()

    with pytest.raises(DailyAnalysisCacheError):
        resolve_daily_analysis("synthetic", should_generate=False, generate=generate, cache_dir=tmp_path)
    assert calls == []
    assert path.read_bytes() == original
    result = resolve_daily_analysis("synthetic", should_generate=True, generate=generate, cache_dir=tmp_path)
    assert result and not result.cache_hit
    assert calls == ["explicit"]
    assert path.with_suffix(".json.backup").read_bytes() == original
    assert load_daily_analysis("synthetic", cache_dir=tmp_path).attribution.ticker == "SYNTH"


def test_failed_publish_keeps_existing_cache_and_removes_its_temporary_file(tmp_path, monkeypatch):
    import trader.agent_layer.daily_cache as cache

    original = b'{"original":"synthetic"}'
    path = tmp_path / "synthetic.json"
    path.write_bytes(original)
    replace = cache.os.replace

    def fail_publish(source, target):
        if target == path:
            raise OSError("synthetic publish failure")
        return replace(source, target)

    monkeypatch.setattr(cache.os, "replace", fail_publish)
    with pytest.raises(OSError):
        save_daily_analysis(cache_key="synthetic", attribution=AttributionResult(ticker="SYNTH", timeframe="1mo", narrative="new"), critique=CritiqueResult(), cache_dir=tmp_path)
    assert path.read_bytes() == original
    assert path.with_suffix(".json.backup").read_bytes() == original
    assert list(tmp_path.glob(".analysis-*")) == []
