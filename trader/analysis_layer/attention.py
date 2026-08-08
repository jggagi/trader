from __future__ import annotations

from dataclasses import dataclass

from trader.data_layer.master_holdings import ConsensusHolding
from trader.models import PricePoint


@dataclass(frozen=True)
class AttentionCandidate:
    symbol: str
    name: str
    reason: str
    consensus_score: float
    master_count: int
    move_pct: float | None
    latest_close: float | None
    attention_score: float
    action_hint: str


def build_attention_candidates(
    consensus: list[ConsensusHolding],
    prices_by_symbol: dict[str, list[PricePoint]],
) -> list[AttentionCandidate]:
    candidates: list[AttentionCandidate] = []
    for item in consensus:
        prices = prices_by_symbol.get(item.symbol, [])
        move_pct = _compute_move_pct(prices)
        latest_close = float(prices[-1].close) if prices else None
        move_component = min(abs(move_pct or 0.0) * 4, 45.0)
        score = round(item.score * 0.65 + move_component, 1)
        candidates.append(
            AttentionCandidate(
                symbol=item.symbol,
                name=item.name,
                reason=item.note,
                consensus_score=item.score,
                master_count=item.holder_count,
                move_pct=move_pct,
                latest_close=latest_close,
                attention_score=score,
                action_hint=_build_action_hint(item.holder_count, move_pct),
            )
        )
    return sorted(
        candidates, key=lambda candidate: candidate.attention_score, reverse=True
    )


def _compute_move_pct(prices: list[PricePoint]) -> float | None:
    if len(prices) < 2:
        return None
    first_close = float(prices[0].close)
    last_close = float(prices[-1].close)
    if not first_close:
        return None
    return round(((last_close / first_close) - 1) * 100, 2)


def _build_action_hint(master_count: int, move_pct: float | None) -> str:
    if move_pct is None:
        return "补行情后再判断"
    if move_pct <= -5 and master_count >= 2:
        return "共识标的回撤，适合复查基本面和估值"
    if move_pct >= 5 and master_count >= 2:
        return "共识标的快速走强，适合核对催化和追高风险"
    if abs(move_pct) >= 3:
        return "出现异动，适合加入今日复盘"
    return "长期跟踪，等待更清晰价格或基本面信号"
