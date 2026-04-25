from trader.state_layer.parser import LocalDocumentParser


def test_portfolio_parser_phase_one_placeholder() -> None:
    assert LocalDocumentParser().get_portfolio_state() == {}

