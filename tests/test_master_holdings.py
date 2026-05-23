from trader.data_layer.master_holdings import (
    MASTER_PORTFOLIOS,
    get_consensus_holdings,
    get_master_names,
    get_master_portfolio,
)


def test_master_portfolios_include_requested_investors() -> None:
    names = set(get_master_names())

    assert {"Warren Buffett", "Charlie Munger", "Duan Yongping", "Li Lu", "Ray Dalio"} <= names


def test_master_portfolios_have_sources_and_holdings() -> None:
    for portfolio in MASTER_PORTFOLIOS:
        assert portfolio.source_url.startswith("https://")
        assert portfolio.report_period
        assert portfolio.caveat
        assert portfolio.holdings


def test_get_master_portfolio_returns_named_portfolio() -> None:
    portfolio = get_master_portfolio("Li Lu")

    assert portfolio.master == "Li Lu"
    assert any(holding.symbol == "GOOGL" for holding in portfolio.holdings)


def test_consensus_holdings_identify_shared_positions() -> None:
    consensus = get_consensus_holdings()
    symbols = {holding.symbol for holding in consensus}

    assert {"AAPL", "BAC", "BRK.B", "GOOGL", "NVDA", "PDD"} <= symbols
    assert "GOOG" not in symbols


def test_consensus_holdings_are_ranked_by_breadth() -> None:
    consensus = get_consensus_holdings()

    assert consensus
    assert consensus[0].holder_count >= consensus[-1].holder_count
    assert all(holding.conviction_label for holding in consensus)
