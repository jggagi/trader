from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class MarketDataStatus:
    kind: str
    message: str


def describe_market_data(snapshot: dict, *, market_today: date) -> MarketDataStatus:
    """Describe observed daily data, without implying a live quote or generation."""
    provider = str(snapshot.get("provider", "未知来源"))
    symbol = str(snapshot.get("provider_symbol", snapshot.get("ticker", "标的")))
    prices = snapshot.get("prices") or []
    if not prices:
        return MarketDataStatus("empty", f"空数据 · {provider} 没有返回价格数据，可刷新或切换来源。")
    last_date = str(prices[-1].get("date", ""))
    if provider == "Google Finance Mock" or snapshot.get("data_mode") == "simulated":
        return MarketDataStatus(
            "mock", f"模拟数据 · {provider} · {symbol} · 示例日期 {last_date}；不代表真实行情。"
        )
    try:
        observed_date = date.fromisoformat(last_date)
    except (TypeError, ValueError):
        return MarketDataStatus("unknown", f"时间未知 · {provider} 的行情日期无法核对，请刷新数据。")
    if observed_date > market_today:
        return MarketDataStatus("unknown", f"时间异常 · 行情日期 {last_date} 晚于市场日期 {market_today}。")
    if observed_date == market_today:
        return MarketDataStatus(
            "current", f"真实来源 · {provider} · {symbol} · 当日行情 {last_date}；日频数据，非实时报价。"
        )
    return MarketDataStatus(
        "stale",
        f"过期/非当日数据 · 最新行情日期 {last_date}，不是 {market_today}。"
        "可能是市场休市或数据源尚未更新，可点击“刷新行情与新闻”核对。",
    )
