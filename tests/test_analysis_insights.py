from __future__ import annotations

import pandas as pd

from trader.analysis_layer.insights import (
    build_action_checklist,
    build_risk_snapshot,
    build_scenario_table,
    build_technical_snapshot,
    build_weather_forecast,
    enrich_price_frame,
)


def _sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=30, freq="D"),
            "open": [100 + i for i in range(30)],
            "high": [102 + i for i in range(30)],
            "low": [99 + i for i in range(30)],
            "close": [100 + i for i in range(30)],
            "volume": [1_000_000 + i for i in range(30)],
        }
    )


def test_enrich_price_frame_adds_indicators() -> None:
    enriched = enrich_price_frame(_sample_frame())

    assert "ma20" in enriched.columns
    assert "drawdown" in enriched.columns
    assert enriched.iloc[-1]["ma20"] > 0


def test_build_technical_snapshot_labels_uptrend() -> None:
    snapshot = build_technical_snapshot(_sample_frame())

    assert snapshot["trend_label"] == "上升趋势"
    assert snapshot["distance_to_ma20"] is not None


def test_build_risk_snapshot_and_scenarios() -> None:
    frame = _sample_frame()
    risk = build_risk_snapshot(frame)
    scenarios = build_scenario_table(
        frame, position_value=10_000, shock_pct=10, currency_symbol="$"
    )

    assert risk["max_drawdown"] == 0
    assert list(scenarios["情景"]) == [
        "压力情景",
        "温和回调",
        "基准不变",
        "温和上涨",
        "乐观情景",
    ]
    assert scenarios.iloc[0]["持仓影响"] == "$-1,000"


def test_action_checklist_uses_position_context() -> None:
    technical = build_technical_snapshot(_sample_frame())
    risk = build_risk_snapshot(_sample_frame())
    checklist = build_action_checklist(
        technical, risk, move_pct=3, position_value=0, ticker="SPY"
    )

    assert len(checklist) == 4
    assert "输入你的 SPY 持仓市值" in checklist[-1]


def test_weather_forecast_translates_trend_and_risk() -> None:
    technical = build_technical_snapshot(_sample_frame())
    risk = build_risk_snapshot(_sample_frame())
    weather = build_weather_forecast(technical, risk)

    assert weather["short_term"]["label"] in {"晴朗", "多云转晴"}
    assert weather["long_term"]["label"] == "晴朗"
    assert weather["risk_weather"]["label"] == "晴朗"
    assert "短期" in weather["summary"]
