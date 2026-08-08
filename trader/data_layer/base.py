from __future__ import annotations

from abc import ABC, abstractmethod

from trader.models import NewsItem, PricePoint


class BaseMarketDataFetcher(ABC):
    """Interface for market data providers."""

    @abstractmethod
    def get_historical_prices(self, ticker: str, timeframe: str) -> list[PricePoint]:
        raise NotImplementedError

    @abstractmethod
    def get_recent_news(self, ticker: str) -> list[NewsItem]:
        raise NotImplementedError
