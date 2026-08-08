from trader.analysis_layer.attention import build_attention_candidates
from trader.data_layer.master_holdings import ConsensusHolding
from trader.models import PricePoint


def _price(date: str, close: float) -> PricePoint:
    return PricePoint(
        date=date, open=close, high=close, low=close, close=close, volume=100
    )


def test_attention_candidates_combine_consensus_and_move() -> None:
    consensus = [
        ConsensusHolding(
            "AAPL", "Apple", 2, ["A", "B"], ["生态"], "强线索", 77.0, "生态"
        ),
        ConsensusHolding(
            "NVDA", "Nvidia", 2, ["A", "C"], ["AI"], "交叉验证", 55.0, "AI"
        ),
    ]
    prices = {
        "AAPL": [_price("2026-05-18", 100), _price("2026-05-23", 101)],
        "NVDA": [_price("2026-05-18", 100), _price("2026-05-23", 112)],
    }

    candidates = build_attention_candidates(consensus, prices)

    assert candidates[0].symbol == "NVDA"
    assert candidates[0].move_pct == 12
    assert "走强" in candidates[0].action_hint


def test_attention_candidate_handles_missing_prices() -> None:
    consensus = [
        ConsensusHolding(
            "PDD", "PDD Holdings", 2, ["A", "B"], ["电商"], "交叉验证", 66.0, "电商"
        )
    ]

    candidates = build_attention_candidates(consensus, {})

    assert candidates[0].move_pct is None
    assert candidates[0].latest_close is None
    assert candidates[0].action_hint == "补行情后再判断"
