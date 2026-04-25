from typing import Any

from trader.agent_layer.attribution.engine import AttributionEngine
from trader.agent_layer.critique.engine import MASTER_SKILLS, MasterCritiqueEngine


class FakeLLM:
    def complete(self, *, system_prompt: str, user_payload: dict[str, Any]) -> tuple[str, bool]:
        return f"fake response for {user_payload.get('ticker') or user_payload['market_snapshot']['ticker']}", False


def test_master_critique_runs_all_skills() -> None:
    snapshot = {
        "provider": "test",
        "ticker": "QQQ",
        "timeframe": "5d",
        "prices": [
            {"date": "2026-01-01", "open": 1, "high": 2, "low": 1, "close": 1, "volume": 10},
            {"date": "2026-01-02", "open": 2, "high": 3, "low": 2, "close": 2, "volume": 20},
        ],
        "news": [{"title": "test news", "publisher": "test"}],
    }
    attribution = AttributionEngine(FakeLLM()).run(snapshot)
    critique = MasterCritiqueEngine(FakeLLM()).run(
        market_snapshot=snapshot,
        portfolio_state={},
        attribution=attribution,
    )

    assert [view.name for view in critique.views] == list(MASTER_SKILLS)
    assert critique.metadata["portfolio_state_present"] is False

