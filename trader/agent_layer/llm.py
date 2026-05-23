from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

import requests


class StatelessLLMClient(Protocol):
    def complete(self, *, system_prompt: str, user_payload: dict[str, Any]) -> tuple[str, bool]:
        """Return generated text and whether an external LLM was used."""


@dataclass(frozen=True)
class LocalFallbackLLMClient:
    reason: str = "OPENAI_API_KEY is not configured"

    def complete(self, *, system_prompt: str, user_payload: dict[str, Any]) -> tuple[str, bool]:
        if "market_snapshot" in user_payload:
            return _local_critique(system_prompt, user_payload), False
        return _local_attribution(user_payload), False


@dataclass(frozen=True)
class OpenAIResponsesClient:
    api_key: str
    model: str = "gpt-4o-mini"
    timeout_seconds: int = 45

    def complete(self, *, system_prompt: str, user_payload: dict[str, Any]) -> tuple[str, bool]:
        response = requests.post(
            "https://api.openai.com/v1/responses",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": [
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": json.dumps(user_payload, ensure_ascii=False, default=str),
                    },
                ],
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        return _extract_response_text(body), True


def build_default_llm_client() -> StatelessLLMClient:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return LocalFallbackLLMClient()
    return OpenAIResponsesClient(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    )


def _extract_response_text(body: dict[str, Any]) -> str:
    text = body.get("output_text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    chunks: list[str] = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(str(content["text"]))
    return "\n".join(chunks).strip() or "No model output returned."


def _local_attribution(user_payload: dict[str, Any]) -> str:
    ticker = user_payload.get("ticker") or "标的"
    timeframe = user_payload.get("timeframe") or "当前周期"
    prices = user_payload.get("prices") or []
    news = user_payload.get("news") or []
    move = _price_move(prices)

    if move is None:
        return "本地分析：暂时没有足够价格数据，无法做可靠归因。建议换一个周期或数据源后重新刷新。"

    direction = "上涨" if move >= 0 else "下跌"
    leading_news = "；".join(item.get("title", "未命名新闻") for item in news[:3]) or "没有相关新闻"
    return (
        f"本地分析：{ticker} 在 {timeframe} 内{direction} {move:+.2f}%。"
        "当前只能把价格变化与已拉取新闻做弱关联，不能证明因果。"
        f"优先核对这些线索：{leading_news}。"
        "如果要获得更完整的宏观和财报解释，请配置 OPENAI_API_KEY 后重新运行。"
    )


def _local_critique(system_prompt: str, user_payload: dict[str, Any]) -> str:
    snapshot = user_payload.get("market_snapshot", {})
    ticker = snapshot.get("ticker") or "标的"
    prices = snapshot.get("prices") or []
    move = _price_move(prices)
    move_text = "数据不足" if move is None else f"{move:+.2f}%"

    if "Warren Buffett" in system_prompt:
        return (
            f"本地视角：{ticker} 短期涨跌 {move_text} 不是核心。"
            "真正要问的是这个标的背后资产的护城河、资本回报率和自由现金流是否仍然优秀。"
            "如果只是因为价格涨了才想追，需要先冷静。"
        )
    if "Charlie Munger" in system_prompt:
        return (
            f"本地视角：{ticker} 的短期表现是 {move_text}。"
            "最容易犯的错是把近期走势当作必然趋势，或者用新闻给已经想做的交易找借口。"
            "先排除冲动，再谈判断。"
        )
    if "Duan Yongping" in system_prompt:
        return (
            f"本地视角：看 {ticker} 要回到本分：是否买的是好商业、好现金流、好管理层。"
            "如果你的持仓逻辑是长期分享顶级公司的价值创造，短期噪音权重应降低；"
            "如果逻辑只是短线猜方向，仓位就要克制。"
        )
    if "Ray Dalio" in system_prompt:
        return (
            f"本地视角：{ticker} 的短期变化 {move_text} 要放在利率、通胀、流动性和风险偏好里看。"
            "不同资产对久期、增长预期、信用条件和流动性的敏感度不同，宏观环境转向时波动可能被放大。"
            "不要让单一资产承担全部周期风险。"
        )
    return f"本地视角：{ticker} 当前变化为 {move_text}，建议结合价格、新闻和仓位约束一起判断。"


def _price_move(prices: list[dict[str, Any]]) -> float | None:
    if len(prices) < 2:
        return None
    start_close = _as_float(prices[0].get("close"))
    end_close = _as_float(prices[-1].get("close"))
    if not start_close or end_close is None:
        return None
    return ((end_close / start_close) - 1) * 100


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
