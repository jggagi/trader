from __future__ import annotations

from datetime import date, timedelta

from trader.data_layer.base import BaseMarketDataFetcher
from trader.models import NewsItem, PricePoint


class GoogleFinanceFetcher(BaseMarketDataFetcher):
    """Interface-compatible mock for future Google Finance integration."""

    def get_historical_prices(self, ticker: str, timeframe: str) -> list[PricePoint]:
        days = _timeframe_to_days(timeframe)
        today = date.today()
        base = 430.0
        points: list[PricePoint] = []
        for offset in range(days):
            current = today - timedelta(days=days - offset - 1)
            drift = offset * 0.55
            wave = 2.8 if offset % 5 in (1, 2) else -1.4
            close = base + drift + wave
            points.append(
                PricePoint(
                    date=current.isoformat(),
                    open=round(close - 0.8, 2),
                    high=round(close + 1.9, 2),
                    low=round(close - 2.1, 2),
                    close=round(close, 2),
                    volume=45_000_000 + offset * 100_000,
                )
            )
        return points

    def get_recent_news(self, ticker: str) -> list[NewsItem]:
        symbol = ticker.upper()
        return [
            NewsItem(
                title=f"{symbol} mock: megacap technology earnings support index sentiment",
                publisher="Google Finance Mock",
                summary="Mock item for proving the provider interface.",
            ),
            NewsItem(
                title=f"{symbol} mock: rate expectations remain the dominant macro driver",
                publisher="Google Finance Mock",
                summary="Mock item for local testing without network dependency.",
            ),
        ]


def _timeframe_to_days(timeframe: str) -> int:
    return {
        "5d": 5,
        "1mo": 22,
        "3mo": 66,
        "6mo": 132,
        "1y": 252,
    }.get(timeframe, 22)

