from trader.data_layer.etf_catalog import ETF_PRESETS, get_presets, get_styles


def test_catalog_includes_low_vol_dividend_styles() -> None:
    symbols = {item.symbol for item in ETF_PRESETS if item.style == "低波红利"}

    assert {"USMV", "SPLV", "SPHD", "SCHD", "512890", "515100", "510880", "515080"} <= symbols


def test_catalog_filters_by_market_and_style() -> None:
    presets = get_presets(market="A股", style="低波红利")

    assert presets
    assert all(item.market == "A股" for item in presets)
    assert all(item.style == "低波红利" for item in presets)


def test_styles_follow_market_filter() -> None:
    styles = get_styles("美股")

    assert "低波红利" in styles
    assert "科技成长" in styles
