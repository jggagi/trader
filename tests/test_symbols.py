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
    assert resolve_symbol("159915").provider_symbol == "159915.SZ"


def test_resolve_beijing_a_share() -> None:
    symbol = resolve_symbol("830799")

    assert symbol.provider_symbol == "830799.BJ"
    assert symbol.market == "China A · Beijing"


def test_preserves_explicit_china_suffix() -> None:
    symbol = resolve_symbol("600519.ss")

    assert symbol.provider_symbol == "600519.SS"
    assert symbol.display_symbol == "600519.SS"
    assert symbol.currency_symbol == "¥"


def test_resolve_shanghai_listed_etf() -> None:
    assert resolve_symbol("510300").provider_symbol == "510300.SS"
    assert resolve_symbol("588000").provider_symbol == "588000.SS"


def test_resolve_hong_kong_suffix_and_prefix() -> None:
    suffix_symbol = resolve_symbol("700.hk")
    prefix_symbol = resolve_symbol("HK:700")

    assert suffix_symbol.provider_symbol == "0700.HK"
    assert suffix_symbol.market == "Hong Kong"
    assert suffix_symbol.currency_symbol == "HK$"
    assert prefix_symbol.provider_symbol == "0700.HK"


def test_resolve_japan_suffix_and_prefix() -> None:
    suffix_symbol = resolve_symbol("7203.t")
    prefix_symbol = resolve_symbol("JP:7203")

    assert suffix_symbol.provider_symbol == "7203.T"
    assert suffix_symbol.market == "Japan"
    assert suffix_symbol.currency_symbol == "¥"
    assert prefix_symbol.provider_symbol == "7203.T"
