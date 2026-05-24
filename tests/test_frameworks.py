from trader.analysis_layer.frameworks import build_investment_frameworks


def test_investment_frameworks_include_macro_and_value_lenses() -> None:
    frameworks = build_investment_frameworks(
        snapshot={"ticker": "SPY", "market": "US / Global"},
        metrics={"move_pct_raw": 6.0, "move_pct": "+6.00%"},
        technical={"trend_label": "上升趋势", "distance_to_ma20": 3.0},
        risk={"risk_label": "波动温和", "max_drawdown": -2.0},
        weather={"long_term": {"label": "晴朗"}},
    )

    names = [framework.name for framework in frameworks]

    assert "Ray Dalio 宏观周期框架" in names
    assert "Buffett-Munger 价值投资框架" in names
    assert all(framework.items for framework in frameworks)
    assert all(framework.next_questions for framework in frameworks)


def test_value_framework_warns_about_chasing_strength() -> None:
    frameworks = build_investment_frameworks(
        snapshot={"ticker": "AAPL", "market": "US / Global"},
        metrics={"move_pct_raw": 8.0, "move_pct": "+8.00%"},
        technical={"trend_label": "短线偏强"},
        risk={"risk_label": "波动温和", "max_drawdown": -1.0},
        weather={"long_term": {"label": "晴朗"}},
    )
    value_framework = frameworks[1]

    assert "安全边际" in value_framework.current_read
