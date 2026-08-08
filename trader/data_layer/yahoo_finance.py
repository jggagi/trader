from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from trader.data_layer.base import BaseMarketDataFetcher
from trader.models import NewsItem, PricePoint


class YahooFinanceFetcher(BaseMarketDataFetcher):
    def get_historical_prices(self, ticker: str, timeframe: str) -> list[PricePoint]:
        history = yf.Ticker(ticker.upper()).history(
            period=timeframe, interval="1d", auto_adjust=False
        )
        if history.empty:
            return []

        points: list[PricePoint] = []
        for index, row in history.reset_index().iterrows():
            raw_date = row.get("Date") or row.iloc[0]
            points.append(
                PricePoint(
                    date=_format_date(raw_date),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=int(row.get("Volume") or 0),
                )
            )
        return points

    def get_recent_news(self, ticker: str) -> list[NewsItem]:
        try:
            raw_news = yf.Ticker(ticker.upper()).news or []
        except Exception:
            raw_news = []
        return [_normalize_news(item) for item in raw_news[:10]]


def _format_date(value: Any) -> str:
    if hasattr(value, "date"):
        return value.date().isoformat()
    return str(value)[:10]


def _normalize_news(item: dict[str, Any]) -> NewsItem:
    content = item.get("content") if isinstance(item.get("content"), dict) else item
    title = content.get("title") or item.get("title") or "Untitled"
    provider = content.get("provider") or {}
    publisher = (
        provider.get("displayName")
        if isinstance(provider, dict)
        else item.get("publisher")
    )
    link = (
        content.get("canonicalUrl")
        or content.get("clickThroughUrl")
        or item.get("link")
    )
    if isinstance(link, dict):
        link = link.get("url")
    published_at = content.get("pubDate") or _timestamp_to_iso(
        item.get("providerPublishTime")
    )
    summary = content.get("summary") or item.get("summary")
    return NewsItem(
        title=title,
        publisher=publisher or "Yahoo Finance",
        link=link,
        published_at=published_at,
        summary=summary,
    )


def _timestamp_to_iso(value: Any) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None
