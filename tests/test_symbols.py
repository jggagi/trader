from trader.data_layer.symbols import resolve_symbol


def test_resolve_us_symbol() -> None:
    symbol = resolve_symbol("spy")

    assert symbol.provider_symbol == "SPY"
    assert symbol.display_symbol == "SPY"
    assert symbol.market == "US / Global"
    assert symbol.currency_symbol == "$"


def test_resolve_shanghai_a_share() -> None:
    symbol = resolve_symbol("600519")

    assert symbol.provider_symbol == "600519.SS"
    assert symbol.display_symbol == "600519"
    assert symbol.market == "China A · Shanghai"
    assert symbol.currency_symbol == "¥"


def test_resolve_shenzhen_a_share() -> None:
    assert resolve_symbol("000001").provider_symbol == "000001.SZ"
    assert resolve_symbol("300750").provider_symbol == "300750.SZ"


def test_resolve_beijing_a_share() -> None:
    symbol = resolve_symbol("830799")

    assert symbol.provider_symbol == "830799.BJ"
    assert symbol.market == "China A · Beijing"


def test_preserves_explicit_china_suffix() -> None:
    symbol = resolve_symbol("600519.ss")

    assert symbol.provider_symbol == "600519.SS"
    assert symbol.display_symbol == "600519.SS"
    assert symbol.currency_symbol == "¥"
