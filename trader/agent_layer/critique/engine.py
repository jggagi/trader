from __future__ import annotations

from trader.agent_layer.llm import StatelessLLMClient
from trader.models import AttributionResult, CritiqueResult, CritiqueView


MASTER_SKILLS = {
    "Warren Buffett": (
        "You are Warren Buffett. Evaluate the data based ONLY on intrinsic value, moats, "
        "and cash-flow generation. Ignore short-term macro noise. Reply in concise Chinese. "
        "Do not give generic advice: explicitly reference the provided ticker, timeframe, price move, asset type, and news clues."
    ),
    "Charlie Munger": (
        "You are Charlie Munger. Evaluate using worldly wisdom. Point out potential "
        "psychological misjudgments, stupidity, or opportunity cost. Be harsh, direct, and witty. "
        "Reply in concise Chinese. Do not give generic advice: explicitly reference the provided ticker, timeframe, price move, asset type, and news clues."
    ),
    "Duan Yongping": (
        "You are Duan Yongping. Focus on 'Right Thing, Do Things Right' (本分). Focus intensely "
        "on the business model, free cash flow, and heavy concentration in top-tier companies. "
        "Reply in concise Chinese. Do not give generic advice: explicitly reference the provided ticker, timeframe, price move, asset type, and news clues."
    ),
    "Ray Dalio": (
        "You are Ray Dalio. Evaluate the data strictly through the lens of macro-economic cycles, "
        "debt cycles, inflation, and structural diversification. Reply in concise Chinese. "
        "Do not give generic advice: explicitly reference the provided ticker, timeframe, price move, asset type, and news clues."
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
        prices = market_snapshot.get("prices", [])
        price_move = _price_move(prices)
        for name, system_prompt in MASTER_SKILLS.items():
            commentary, llm_used = self.llm_client.complete(
                system_prompt=system_prompt,
                user_payload={
                    "market_snapshot": {
                        "ticker": market_snapshot["ticker"],
                        "timeframe": market_snapshot["timeframe"],
                        "market": market_snapshot.get("market"),
                        "provider_symbol": market_snapshot.get("provider_symbol"),
                        "asset_type_hint": _asset_type_hint(market_snapshot),
                        "price_move_pct": price_move,
                        "selected_preset_style": market_snapshot.get(
                            "selected_preset_style"
                        ),
                        "selected_preset_theme": market_snapshot.get(
                            "selected_preset_theme"
                        ),
                        "prices": market_snapshot["prices"][-10:],
                        "news": market_snapshot["news"][:5],
                    },
                    "portfolio_state": portfolio_state,
                    "attribution": attribution.model_dump(),
                },
            )
            views.append(
                CritiqueView(name=name, commentary=commentary, llm_used=llm_used)
            )

        return CritiqueResult(
            views=views,
            metadata={
                "skills": list(MASTER_SKILLS),
                "portfolio_state_present": bool(portfolio_state),
            },
        )


def _price_move(prices: list[dict]) -> float | None:
    if len(prices) < 2:
        return None
    start = float(prices[0]["close"])
    end = float(prices[-1]["close"])
    if not start:
        return None
    return round(((end / start) - 1) * 100, 2)


def _asset_type_hint(market_snapshot: dict) -> str:
    style = market_snapshot.get("selected_preset_style")
    if style == "大盘核心":
        return "宽基 ETF"
    if style in {"科技成长", "成长"}:
        return "成长/行业 ETF"
    if style == "低波红利":
        return "红利/低波 ETF"
    return "个股或自定义标的"
