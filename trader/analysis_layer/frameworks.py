from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FrameworkItem:
    label: str
    assessment: str
    learning_prompt: str


@dataclass(frozen=True)
class InvestmentFramework:
    name: str
    subtitle: str
    philosophy: str
    current_read: str
    items: list[FrameworkItem]
    next_questions: list[str]


def build_investment_frameworks(
    *,
    snapshot: dict,
    metrics: dict[str, Any],
    technical: dict[str, Any],
    risk: dict[str, Any],
    weather: dict[str, Any],
) -> list[InvestmentFramework]:
    return [
        build_dalio_framework(snapshot=snapshot, metrics=metrics, technical=technical, risk=risk, weather=weather),
        build_buffett_munger_framework(snapshot=snapshot, metrics=metrics, technical=technical, risk=risk),
    ]


def build_dalio_framework(
    *,
    snapshot: dict,
    metrics: dict[str, Any],
    technical: dict[str, Any],
    risk: dict[str, Any],
    weather: dict[str, Any],
) -> InvestmentFramework:
    market = snapshot.get("market", "Unknown")
    risk_label = risk.get("risk_label", "数据不足")
    move_pct = metrics.get("move_pct_raw")
    trend = technical.get("trend_label", "数据不足")
    current_read = _dalio_current_read(move_pct, risk_label, trend)
    return InvestmentFramework(
        name="Ray Dalio 宏观周期框架",
        subtitle="周期、债务、通胀、政策与分散",
        philosophy="先判断自己暴露在哪类宏观环境里，再决定是否需要分散、再平衡或降低单一风险。",
        current_read=current_read,
        items=[
            FrameworkItem(
                "周期位置",
                f"{market} · {trend} · {weather['long_term']['label']}",
                "问：这更像流动性扩张、增长修复，还是风险资产退潮？",
            ),
            FrameworkItem(
                "风险平衡",
                f"{risk_label} · 最大回撤 { _format_optional_pct(risk.get('max_drawdown')) }",
                "问：如果这个标的继续回撤，组合里有没有资产能对冲同一个宏观冲击？",
            ),
            FrameworkItem(
                "政策敏感度",
                "科技/成长通常更敏感，红利/低波通常更防守。",
                "问：利率、美元、信用和通胀变化会怎样影响估值倍数？",
            ),
            FrameworkItem(
                "结构性分散",
                "不要让所有仓位押注同一个国家、行业、因子或货币。",
                "问：这笔投资是在增加分散，还是让组合更集中在同一个宏观押注上？",
            ),
        ],
        next_questions=[
            "当前价格变化是基本面改善，还是折现率/流动性变化？",
            "如果未来 6-12 个月增长放缓或利率上行，这个标的会怎样表现？",
            "组合是否同时覆盖增长、现金、防守、海外和不同货币暴露？",
        ],
    )


def build_buffett_munger_framework(
    *,
    snapshot: dict,
    metrics: dict[str, Any],
    technical: dict[str, Any],
    risk: dict[str, Any],
) -> InvestmentFramework:
    ticker = snapshot.get("ticker", "Unknown")
    move_pct = metrics.get("move_pct_raw")
    current_read = _value_current_read(move_pct, technical.get("trend_label"), risk.get("risk_label"))
    return InvestmentFramework(
        name="Buffett-Munger 价值投资框架",
        subtitle="好生意、护城河、现金流、安全边际与心理纪律",
        philosophy="先判断是不是值得长期拥有的好生意，再判断价格是否给了足够安全边际。",
        current_read=current_read,
        items=[
            FrameworkItem(
                "能力圈",
                f"{ticker} 是否能用一句话解释赚钱模式？",
                "问：我真的懂它如何赚钱、为什么客户留下、竞争对手为什么难以复制吗？",
            ),
            FrameworkItem(
                "护城河",
                "品牌、网络效应、成本优势、规模优势或监管壁垒。",
                "问：五年后它的竞争地位更强，还是被技术/竞争侵蚀？",
            ),
            FrameworkItem(
                "现金流质量",
                "长期看自由现金流、资本回报率和再投资空间。",
                "问：增长需要大量烧钱，还是能把利润稳定转成现金？",
            ),
            FrameworkItem(
                "安全边际",
                f"近期区间涨跌 {metrics.get('move_pct', 'N/A')}，风险状态 {risk.get('risk_label', '数据不足')}",
                "问：现在的价格是否已经透支乐观预期？如果错了，下行空间有多大？",
            ),
            FrameworkItem(
                "反心理误判",
                "防止追涨、锚定、确认偏误和因为大师持仓而外包判断。",
                "问：如果不知道任何大师买了它，我还愿意独立持有吗？",
            ),
        ],
        next_questions=[
            "这家公司或 ETF 的长期持有理由，能否写成 3 条不依赖股价的判断？",
            "如果价格下跌 30%，我是更想买，还是才发现自己不懂？",
            "有没有一个更简单、更确定、机会成本更低的替代选择？",
        ],
    )


def _dalio_current_read(move_pct: float | None, risk_label: str, trend: str) -> str:
    if move_pct is None:
        return "宏观读数不足，先补齐价格和新闻，再判断周期环境。"
    if risk_label == "波动偏高":
        return "风险环境偏紧，优先检查组合是否过度集中在同一类风险资产。"
    if move_pct >= 5 and trend in {"上升趋势", "短线偏强"}:
        return "风险资产处于较顺风阶段，但要区分基本面改善和流动性推升。"
    if move_pct <= -5:
        return "价格承压，适合从增长、利率、信用和政策四个角度拆解原因。"
    return "宏观信号温和，适合观察而不是频繁动作。"


def _value_current_read(move_pct: float | None, trend: str | None, risk_label: str | None) -> str:
    if move_pct is None:
        return "价值判断不能只靠行情，先回到商业模式、现金流和估值。"
    if move_pct <= -5:
        return "下跌可能带来机会，也可能暴露基本面问题；先判断护城河是否受损。"
    if move_pct >= 5 and trend in {"上升趋势", "短线偏强"}:
        return "价格走强时更要检查安全边际，避免用好公司为高价格辩护。"
    if risk_label == "波动偏高":
        return "波动较大时，先确认自己是否真的愿意长期持有。"
    return "价格信号不极端，适合把重点放在生意质量和机会成本上。"


def _format_optional_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:+.2f}%"
