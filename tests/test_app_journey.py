from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests
import streamlit as st
from streamlit.testing.v1 import AppTest

from trader.agent_layer import daily_cache, llm
from trader.data_layer import factory
from trader.models import NewsItem, PricePoint

FIXED_NOW = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)


def test_real_streamlit_controls_use_synthetic_sources_and_only_generate_explicitly(tmp_path, monkeypatch):
    """Run the actual app, replacing providers/secrets/cache at their boundaries."""
    mode = {"kind": "current"}
    calls = {"prices": 0, "llm": 0, "network": 0}

    class SyntheticFetcher:
        def get_historical_prices(self, ticker, timeframe):
            calls["prices"] += 1
            if mode["kind"] == "empty":
                return []
            today = FIXED_NOW.date() - timedelta(days=30 if mode["kind"] == "stale" else 0)
            return [PricePoint(date=(today-timedelta(days=29-i)).isoformat(), open=100+i, high=102+i, low=99+i, close=101+i, volume=1000) for i in range(30)]

        def get_recent_news(self, ticker):
            return [NewsItem(title="Synthetic fixture news", publisher="M6 synthetic source")]

    class SyntheticLocalAnalysis:
        def complete(self, **kwargs):
            calls["llm"] += 1
            return "Synthetic local analysis", False

    def no_network(*args, **kwargs):
        calls["network"] += 1
        raise AssertionError("No external provider/model requests permitted")

    monkeypatch.setattr(factory, "create_market_data_fetcher", lambda provider: SyntheticFetcher())
    monkeypatch.setattr(llm, "build_default_llm_client", lambda: SyntheticLocalAnalysis())
    monkeypatch.setattr(daily_cache, "get_daily_cache_path", lambda cache_key, cache_dir=None: tmp_path / f"{cache_key}.json")
    monkeypatch.setattr(requests.sessions.Session, "request", no_network)
    monkeypatch.setenv("DEFAULT_TICKER", "SYNTH")
    monkeypatch.setenv("APP_MODE", "local")
    st.cache_data.clear()
    app_path = str(Path("app.py").resolve())
    # run_name prevents automatic main; disabling the secrets loader prevents
    # the test from reading the user's Streamlit configuration or credentials.
    at = AppTest.from_string(
        "from datetime import datetime as _datetime, timezone as _timezone\n"
        "FIXED_NOW = _datetime(2026, 10, 3, 12, tzinfo=_timezone.utc)\n"
        "class SyntheticDateTime(_datetime):\n"
        "    @classmethod\n"
        "    def now(cls, tz=None):\n"
        "        return FIXED_NOW.astimezone(tz) if tz is not None else FIXED_NOW.replace(tzinfo=None)\n"
        f"import runpy\napp = runpy.run_path({app_path!r}, run_name='m6_synthetic')\n"
        "app['main'].__globals__['datetime'] = SyntheticDateTime\n"
        "app['main'].__globals__['configure_streamlit_secrets'] = lambda: None\napp['main']()",
        default_timeout=20,
    ).run()

    def clean():
        assert not at.exception, [entry.message for entry in at.exception]
        assert calls["network"] == 0

    def control(elements, label):
        return next(element for element in elements if element.label == label)

    clean()
    assert calls["llm"] == 0
    assert list(tmp_path.iterdir()) == []
    assert any("日频数据，非实时报价" in entry.value for entry in at.info)
    fetched = calls["prices"]
    control(at.button, "刷新行情与新闻").click().run()
    clean()
    assert calls["prices"] > fetched and calls["llm"] == 0
    control(at.button, "重新生成今日归因/批判").click().run()
    clean()
    assert calls["llm"] == 5
    assert len(list(tmp_path.glob("*.json"))) == 1
    at.run()
    clean()
    assert calls["llm"] == 5
    assert any("复用今日缓存" in entry.value for entry in at.caption)

    control(at.selectbox, "数据源").select(factory.DataProvider.GOOGLE_MOCK.value).run()
    clean()
    assert any("模拟数据" in entry.value for entry in at.info)
    assert calls["llm"] == 5
    control(at.selectbox, "数据源").select(factory.DataProvider.YAHOO.value).run()
    mode["kind"] = "stale"
    control(at.button, "刷新行情与新闻").click().run()
    clean()
    assert any("过期/非当日数据" in entry.value for entry in at.warning)
    mode["kind"] = "empty"
    control(at.button, "刷新行情与新闻").click().run()
    clean()
    assert any("空数据" in entry.value for entry in at.warning)
    assert calls["llm"] == 5

    cached = next(tmp_path.glob("*.json"))
    cached.write_bytes(b'{"unfinished":')
    at.run()
    clean()
    assert any("缓存无法读取" in entry.value for entry in at.warning)
    assert cached.read_bytes() == b'{"unfinished":'
    assert calls["llm"] == 5
    control(at.button, "重新生成今日归因/批判").click().run()
    clean()
    assert calls["llm"] == 10
    assert cached.with_suffix(".json.backup").read_bytes() == b'{"unfinished":'
    st.cache_data.clear()
