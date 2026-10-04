from datetime import date

from trader.data_layer.status import describe_market_data


def snapshot(provider="Yahoo Finance", observed="2026-10-02"):
    return {"provider": provider, "provider_symbol": "SYNTH", "prices": [{"date": observed}]}


def test_simulation_is_never_labeled_current_real_quote():
    status = describe_market_data(snapshot("Google Finance Mock"), market_today=date(2026, 10, 2))
    assert status.kind == "mock"
    assert "不代表真实行情" in status.message
    marked = snapshot()
    marked["data_mode"] = "simulated"
    assert describe_market_data(marked, market_today=date(2026, 10, 2)).kind == "mock"


def test_empty_current_stale_and_invalid_dates_are_distinct():
    today = date(2026, 10, 2)
    assert describe_market_data({"provider": "Yahoo Finance", "prices": []}, market_today=today).kind == "empty"
    current = describe_market_data(snapshot(), market_today=today)
    assert current.kind == "current"
    assert "日频数据，非实时报价" in current.message
    assert describe_market_data(snapshot(observed="2026-10-01"), market_today=today).kind == "stale"
    assert describe_market_data(snapshot(observed="not-a-date"), market_today=today).kind == "unknown"
    assert describe_market_data(snapshot(observed="2026-10-03"), market_today=today).kind == "unknown"
