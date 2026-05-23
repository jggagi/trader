from __future__ import annotations

from math import sqrt
from typing import Any

import pandas as pd


def enrich_price_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame

    enriched = frame.copy()
    enriched["daily_return"] = enriched["close"].pct_change()
    enriched["ma20"] = enriched["close"].rolling(window=20, min_periods=3).mean()
    enriched["ma50"] = enriched["close"].rolling(window=50, min_periods=5).mean()
    enriched["high_watermark"] = enriched["close"].cummax()
    enriched["drawdown"] = (enriched["close"] / enriched["high_watermark"]) - 1
    return enriched


def build_technical_snapshot(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {
            "trend_label": "数据不足",
            "trend_detail": "没有足够价格数据计算趋势。",
            "ma20": None,
            "ma50": None,
            "distance_to_ma20": None,
            "distance_to_ma50": None,
        }

    enriched = enrich_price_frame(frame)
    last = enriched.iloc[-1]
    close = float(last["close"])
    ma20 = _optional_float(last.get("ma20"))
    ma50 = _optional_float(last.get("ma50"))
    distance_to_ma20 = _distance(close, ma20)
    distance_to_ma50 = _distance(close, ma50)

    if ma20 and ma50 and close > ma20 > ma50:
        trend_label = "上升趋势"
        trend_detail = "价格位于 20 日和 50 日均线上方，短中期趋势偏强。"
    elif ma20 and close > ma20:
        trend_label = "短线偏强"
        trend_detail = "价格高于 20 日均线，但中期趋势还需要结合 50 日均线确认。"
    elif ma20 and close < ma20:
        trend_label = "短线转弱"
        trend_detail = "价格低于 20 日均线，说明短期动能需要谨慎观察。"
    else:
        trend_label = "样本较短"
        trend_detail = "当前周期较短，均线信号只能作为参考。"

    return {
        "trend_label": trend_label,
        "trend_detail": trend_detail,
        "ma20": ma20,
        "ma50": ma50,
        "distance_to_ma20": distance_to_ma20,
        "distance_to_ma50": distance_to_ma50,
    }


def build_risk_snapshot(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty or len(frame) < 2:
        return {
            "risk_label": "数据不足",
            "annualized_volatility": None,
            "max_drawdown": None,
            "best_day": None,
            "worst_day": None,
            "detail": "没有足够价格数据计算风险。",
        }

    enriched = enrich_price_frame(frame)
    returns = enriched["daily_return"].dropna()
    annualized_volatility = float(returns.std() * sqrt(252) * 100) if not returns.empty else None
    max_drawdown = float(enriched["drawdown"].min() * 100)
    best_day = float(returns.max() * 100) if not returns.empty else None
    worst_day = float(returns.min() * 100) if not returns.empty else None

    if max_drawdown <= -12 or (annualized_volatility and annualized_volatility >= 28):
        risk_label = "波动偏高"
        detail = "近期波动或回撤较大，适合降低仓位冲动，先设定可承受亏损。"
    elif max_drawdown <= -6:
        risk_label = "中等波动"
        detail = "回撤处于可观察区间，适合检查仓位是否与风险承受力匹配。"
    else:
        risk_label = "波动温和"
        detail = "近期最大回撤不深，但这不代表未来风险低。"

    return {
        "risk_label": risk_label,
        "annualized_volatility": annualized_volatility,
        "max_drawdown": max_drawdown,
        "best_day": best_day,
        "worst_day": worst_day,
        "detail": detail,
    }


def build_scenario_table(frame: pd.DataFrame, position_value: float, shock_pct: float) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["情景", "价格变化", "估算价格", "持仓影响"])

    last_close = float(frame.iloc[-1]["close"])
    scenarios = [
        ("压力情景", -abs(shock_pct)),
        ("温和回调", -abs(shock_pct) / 2),
        ("基准不变", 0.0),
        ("温和上涨", abs(shock_pct) / 2),
        ("乐观情景", abs(shock_pct)),
    ]
    rows = []
    for label, move_pct in scenarios:
        estimated_price = last_close * (1 + move_pct / 100)
        impact = position_value * move_pct / 100
        rows.append(
            {
                "情景": label,
                "价格变化": f"{move_pct:+.1f}%",
                "估算价格": f"${estimated_price:,.2f}",
                "持仓影响": f"${impact:,.0f}",
            }
        )
    return pd.DataFrame(rows)


def build_action_checklist(
    technical: dict[str, Any],
    risk: dict[str, Any],
    move_pct: float | None,
    position_value: float,
    ticker: str,
) -> list[str]:
    checklist = []
    if move_pct is not None and abs(move_pct) >= 5:
        checklist.append("价格已经出现明显变化，先写下你原来的买入/持有理由是否仍成立。")
    else:
        checklist.append("价格信号不极端，避免为了交易而交易。")

    if technical["trend_label"] in {"上升趋势", "短线偏强"}:
        checklist.append("趋势偏强时不要只问能不能追，也要问回撤到哪里会让你后悔。")
    else:
        checklist.append("趋势不强时，优先等待更清楚的催化或更好的风险回报。")

    if risk["risk_label"] == "波动偏高":
        checklist.append("波动偏高，先确认单笔亏损和组合回撤是否在可承受范围内。")
    else:
        checklist.append("即使当前波动温和，也要预设压力情景，不要把温和当成永久。")

    if position_value > 0:
        checklist.append("把下面情景推演里的持仓影响与现金流、睡眠质量和其他资产一起看。")
    else:
        checklist.append(f"输入你的 {ticker} 持仓市值后，可以把价格情景转换成更直观的美元影响。")
    return checklist


def build_markdown_report(
    *,
    ticker: str,
    timeframe: str,
    takeaway: dict[str, Any],
    metrics: dict[str, Any],
    technical: dict[str, Any],
    risk: dict[str, Any],
    checklist: list[str],
) -> str:
    lines = [
        f"# {ticker} 本地投资观察报告",
        "",
        f"- 周期: {timeframe}",
        f"- 最新收盘: {metrics['last_close']}",
        f"- 区间涨跌: {metrics['move_pct']}",
        f"- 一句话结论: {takeaway['title']}",
        "",
        "## 技术状态",
        f"- 趋势: {technical['trend_label']}",
        f"- 说明: {technical['trend_detail']}",
        f"- 距 20 日均线: {_format_optional_pct(technical['distance_to_ma20'])}",
        f"- 距 50 日均线: {_format_optional_pct(technical['distance_to_ma50'])}",
        "",
        "## 风险状态",
        f"- 风险标签: {risk['risk_label']}",
        f"- 年化波动率: {_format_optional_pct(risk['annualized_volatility'])}",
        f"- 最大回撤: {_format_optional_pct(risk['max_drawdown'])}",
        f"- 说明: {risk['detail']}",
        "",
        "## 行动清单",
    ]
    lines.extend(f"- {item}" for item in checklist)
    return "\n".join(lines)


def _distance(close: float, average: float | None) -> float | None:
    if not average:
        return None
    return ((close / average) - 1) * 100


def _optional_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _format_optional_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:+.2f}%"
