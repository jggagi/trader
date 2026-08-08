from trader.analysis_layer.frameworks import build_investment_frameworks


def test_stock_frameworks_include_macro_context_and_value_lens() -> None:
    frameworks = build_investment_frameworks(
        snapshot={
            "ticker": "AAPL",
            "provider_symbol": "AAPL",
            "market": "US / Global",
            "timeframe": "1mo",
            "news": [{"title": "Apple reports services growth"}],
        },
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
    assert all(
        item.simulated_answer for framework in frameworks for item in framework.items
    )
    assert any(
        "AAPL" in item.simulated_answer
        for framework in frameworks
        for item in framework.items
    )
    assert any(
        "Apple reports services growth" in item.simulated_answer
        for framework in frameworks
        for item in framework.items
    )


def test_value_framework_warns_about_chasing_strength() -> None:
    frameworks = build_investment_frameworks(
        snapshot={"ticker": "AAPL", "provider_symbol": "AAPL", "market": "US / Global"},
        metrics={"move_pct_raw": 8.0, "move_pct": "+8.00%"},
        technical={"trend_label": "短线偏强"},
        risk={"risk_label": "波动温和", "max_drawdown": -1.0},
        weather={"long_term": {"label": "晴朗"}},
    )
    value_framework = frameworks[1]

    assert "安全边际" in value_framework.current_read
    assert any(
        "上涨后更要保守" in item.simulated_answer for item in value_framework.items
    )


def test_broad_etf_skips_single_company_value_framework() -> None:
    frameworks = build_investment_frameworks(
        snapshot={
            "ticker": "SPY",
            "provider_symbol": "SPY",
            "market": "US / Global",
            "selected_preset_style": "大盘核心",
            "selected_preset_theme": "大盘",
        },
        metrics={"move_pct_raw": 2.0, "move_pct": "+2.00%"},
        technical={"trend_label": "上升趋势"},
        risk={"risk_label": "波动温和", "max_drawdown": -1.0},
        weather={"long_term": {"label": "晴朗"}},
    )

    assert [framework.name for framework in frameworks] == ["Ray Dalio 宏观周期框架"]


def test_sector_etf_gets_adapted_value_framework() -> None:
    frameworks = build_investment_frameworks(
        snapshot={
            "ticker": "QQQ",
            "provider_symbol": "QQQ",
            "market": "US / Global",
            "selected_preset_style": "科技成长",
            "selected_preset_theme": "科技/成长",
        },
        metrics={"move_pct_raw": 4.0, "move_pct": "+4.00%"},
        technical={"trend_label": "短线偏强"},
        risk={"risk_label": "中等波动", "max_drawdown": -3.0},
        weather={"long_term": {"label": "云间有光"}},
    )

    assert [framework.name for framework in frameworks] == [
        "Ray Dalio 宏观周期框架",
        "Buffett-Munger 价值投资框架",
    ]
    assert "底层行业质量" in frameworks[1].applicability_reason
    assert any("ETF" in item.simulated_answer for item in frameworks[1].items)
