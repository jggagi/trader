from __future__ import annotations

from enum import StrEnum

from trader.data_layer.base import BaseMarketDataFetcher
from trader.data_layer.google_finance import GoogleFinanceFetcher
from trader.data_layer.yahoo_finance import YahooFinanceFetcher


class DataProvider(StrEnum):
    YAHOO = "Yahoo Finance"
    GOOGLE_MOCK = "Google Finance Mock"


def create_market_data_fetcher(provider: DataProvider | str) -> BaseMarketDataFetcher:
    normalized = DataProvider(provider)
    if normalized == DataProvider.YAHOO:
        return YahooFinanceFetcher()
    if normalized == DataProvider.GOOGLE_MOCK:
        return GoogleFinanceFetcher()
    raise ValueError(f"Unsupported data provider: {provider}")
