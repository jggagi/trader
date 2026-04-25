from __future__ import annotations

from trader.agent_layer.llm import StatelessLLMClient
from trader.models import AttributionResult, CritiqueResult, CritiqueView


MASTER_SKILLS = {
    "Warren Buffett": (
        "You are Warren Buffett. Evaluate the data based ONLY on intrinsic value, moats, "
        "and cash-flow generation. Ignore short-term macro noise."
    ),
    "Charlie Munger": (
        "You are Charlie Munger. Evaluate using worldly wisdom. Point out potential "
        "psychological misjudgments, stupidity, or opportunity cost. Be harsh, direct, and witty."
    ),
    "Duan Yongping": (
        "You are Duan Yongping. Focus on 'Right Thing, Do Things Right' (本分). Focus intensely "
        "on the business model, free cash flow, and heavy concentration in top-tier companies."
    ),
    "Ray Dalio": (
        "You are Ray Dalio. Evaluate the data strictly through the lens of macro-economic cycles, "
        "debt cycles, inflation, and structural diversification."
    ),
}


class MasterCritiqueEngine:
    def __init__(self, llm_client: StatelessLLMClient):
        self.llm_client = llm_client

    def run(
        self,
        *,
        market_snapshot: dict,
        portfolio_state: dict,
        attribution: AttributionResult,
    ) -> CritiqueResult:
        views: list[CritiqueView] = []
        for name, system_prompt in MASTER_SKILLS.items():
            commentary, llm_used = self.llm_client.complete(
                system_prompt=system_prompt,
                user_payload={
                    "market_snapshot": {
                        "ticker": market_snapshot["ticker"],
                        "timeframe": market_snapshot["timeframe"],
                        "prices": market_snapshot["prices"][-10:],
                        "news": market_snapshot["news"][:5],
                    },
                    "portfolio_state": portfolio_state,
                    "attribution": attribution.model_dump(),
                },
            )
            views.append(CritiqueView(name=name, commentary=commentary, llm_used=llm_used))

        return CritiqueResult(
            views=views,
            metadata={
                "skills": list(MASTER_SKILLS),
                "portfolio_state_present": bool(portfolio_state),
            },
        )

