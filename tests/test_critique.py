from typing import Any

from trader.agent_layer.attribution.engine import AttributionEngine
from trader.agent_layer.critique.engine import MASTER_SKILLS, MasterCritiqueEngine
from trader.agent_layer.llm import LocalFallbackLLMClient


class FakeLLM:
    def complete(
        self, *, system_prompt: str, user_payload: dict[str, Any]
    ) -> tuple[str, bool]:
        return (
            f"fake response for {user_payload.get('ticker') or user_payload['market_snapshot']['ticker']}",
            False,
        )


def test_master_critique_runs_all_skills() -> None:
    snapshot = {
        "provider": "test",
        "ticker": "SPY",
        "timeframe": "5d",
        "prices": [
            {
                "date": "2026-01-01",
                "open": 1,
                "high": 2,
                "low": 1,
                "close": 1,
                "volume": 10,
            },
            {
                "date": "2026-01-02",
                "open": 2,
                "high": 3,
                "low": 2,
                "close": 2,
                "volume": 20,
            },
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


def test_local_master_critique_references_selected_asset_context() -> None:
    snapshot = {
        "provider": "test",
        "ticker": "QQQ",
        "provider_symbol": "QQQ",
        "market": "US / Global",
        "timeframe": "1mo",
        "selected_preset_style": "科技成长",
        "selected_preset_theme": "科技/成长",
        "prices": [
            {
                "date": "2026-01-01",
                "open": 100,
                "high": 101,
                "low": 99,
                "close": 100,
                "volume": 10,
            },
            {
                "date": "2026-01-02",
                "open": 108,
                "high": 110,
                "low": 107,
                "close": 108,
                "volume": 20,
            },
        ],
        "news": [{"title": "AI stocks rally", "publisher": "test"}],
    }
    attribution = AttributionEngine(LocalFallbackLLMClient()).run(snapshot)
    critique = MasterCritiqueEngine(LocalFallbackLLMClient()).run(
        market_snapshot=snapshot,
        portfolio_state={},
        attribution=attribution,
    )

    combined = "\n".join(view.commentary for view in critique.views)
    assert "QQQ" in combined
    assert "成长/行业 ETF" in combined
    assert "AI stocks rally" in combined
