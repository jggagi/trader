from trader.data_layer.base import BaseMarketDataFetcher
from trader.data_layer.factory import DataProvider, create_market_data_fetcher


def test_factory_returns_fetcher_for_google_mock() -> None:
    fetcher = create_market_data_fetcher(DataProvider.GOOGLE_MOCK)
    assert isinstance(fetcher, BaseMarketDataFetcher)


def test_google_mock_produces_structured_data() -> None:
    fetcher = create_market_data_fetcher("Google Finance Mock")
    prices = fetcher.get_historical_prices("SPY", "5d")
    news = fetcher.get_recent_news("SPY")

    assert len(prices) == 5
    assert prices[0].close > 0
    assert news[0].publisher == "Google Finance Mock"
