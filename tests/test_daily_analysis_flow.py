from trader.agent_layer.daily_cache import resolve_daily_analysis
from trader.models import AttributionResult, CritiqueResult, CritiqueView


def test_uncached_analysis_waits_for_explicit_request_then_caches(tmp_path) -> None:
    calls = []

    def generate_analysis():
        calls.append("generate")
        return (
            AttributionResult(
                ticker="SPY", timeframe="1mo", narrative="test attribution"
            ),
            CritiqueResult(
                views=[CritiqueView(name="Test", commentary="test critique")]
            ),
        )

    initial = resolve_daily_analysis(
        "2026-10-02__yahoo finance__SPY__1mo",
        should_generate=False,
        generate=generate_analysis,
        cache_dir=tmp_path,
    )

    assert initial is None
    assert calls == []
    assert list(tmp_path.glob("*.json")) == []

    generated = resolve_daily_analysis(
        "2026-10-02__yahoo finance__SPY__1mo",
        should_generate=True,
        generate=generate_analysis,
        cache_dir=tmp_path,
    )

    assert generated is not None
    assert generated.cache_hit is False
    assert generated.attribution.narrative == "test attribution"
    assert generated.critique.views[0].commentary == "test critique"
    assert calls == ["generate"]
    assert list(tmp_path.glob("*.json"))

    cached = resolve_daily_analysis(
        "2026-10-02__yahoo finance__SPY__1mo",
        should_generate=False,
        generate=generate_analysis,
        cache_dir=tmp_path,
    )

    assert cached is not None
    assert cached.cache_hit is True
    assert cached.attribution.narrative == "test attribution"
    assert calls == ["generate"]
