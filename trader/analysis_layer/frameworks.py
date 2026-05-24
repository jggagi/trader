from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FrameworkItem:
    label: str
    assessment: str
    learning_prompt: str
    simulated_answer: str


@dataclass(frozen=True)
class InvestmentFramework:
    name: str
    subtitle: str
    applicability: str
    applicability_reason: str
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
    asset_profile = classify_asset(snapshot)
    frameworks: list[InvestmentFramework] = []
    if _should_apply_dalio(asset_profile):
        frameworks.append(
            build_dalio_framework(
                snapshot=snapshot,
                metrics=metrics,
                technical=technical,
                risk=risk,
                weather=weather,
                applicability_reason=_dalio_applicability_reason(asset_profile),
            )
        )
    if _should_apply_buffett_munger(asset_profile):
        frameworks.append(
            build_buffett_munger_framework(
                snapshot=snapshot,
                metrics=metrics,
                technical=technical,
                risk=risk,
                applicability_reason=_value_applicability_reason(asset_profile),
            )
        )
    return frameworks


def classify_asset(snapshot: dict) -> dict[str, str | bool]:
    ticker = str(snapshot.get("provider_symbol") or snapshot.get("ticker") or "").upper()
    market = str(snapshot.get("market") or "")
    query = str(snapshot.get("query") or ticker).upper()
    is_known_etf = bool(snapshot.get("selected_preset_symbol")) or _looks_like_etf(ticker, query)
    style = str(snapshot.get("selected_preset_style") or "")
    theme = str(snapshot.get("selected_preset_theme") or "")
    if is_known_etf:
        if style == "大盘核心" or theme == "大盘":
            asset_type = "broad_etf"
        elif style == "低波红利":
            asset_type = "dividend_factor_etf"
        elif style in {"科技成长", "成长"}:
            asset_type = "growth_or_sector_etf"
        else:
            asset_type = "etf"
    else:
        asset_type = "stock"
    return {
        "asset_type": asset_type,
        "ticker": ticker or query,
        "market": market,
        "style": style,
        "theme": theme,
        "is_etf": is_known_etf,
    }


def build_dalio_framework(
    *,
    snapshot: dict,
    metrics: dict[str, Any],
    technical: dict[str, Any],
    risk: dict[str, Any],
    weather: dict[str, Any],
    applicability_reason: str = "适合用来理解宏观环境、周期位置和组合分散。",
) -> InvestmentFramework:
    market = snapshot.get("market", "Unknown")
    ticker = snapshot.get("ticker", "该标的")
    risk_label = risk.get("risk_label", "数据不足")
    move_pct = metrics.get("move_pct_raw")
    trend = technical.get("trend_label", "数据不足")
    context = _framework_context(snapshot, metrics)
    current_read = _dalio_current_read(move_pct, risk_label, trend)
    return InvestmentFramework(
        name="Ray Dalio 宏观周期框架",
        subtitle="周期、债务、通胀、政策与分散",
        applicability="适用",
        applicability_reason=applicability_reason,
        philosophy="先判断自己暴露在哪类宏观环境里，再决定是否需要分散、再平衡或降低单一风险。",
        current_read=current_read,
        items=[
            FrameworkItem(
                "周期位置",
                f"{market} · {trend} · {weather['long_term']['label']}",
                "问：这更像流动性扩张、增长修复，还是风险资产退潮？",
                _answer_cycle_position(ticker, context, move_pct, trend, risk_label),
            ),
            FrameworkItem(
                "风险平衡",
                f"{risk_label} · 最大回撤 { _format_optional_pct(risk.get('max_drawdown')) }",
                "问：如果这个标的继续回撤，组合里有没有资产能对冲同一个宏观冲击？",
                _answer_risk_balance(ticker, risk_label, risk.get("max_drawdown")),
            ),
            FrameworkItem(
                "政策敏感度",
                "科技/成长通常更敏感，红利/低波通常更防守。",
                "问：利率、美元、信用和通胀变化会怎样影响估值倍数？",
                _answer_policy_sensitivity(snapshot, context),
            ),
            FrameworkItem(
                "结构性分散",
                "不要让所有仓位押注同一个国家、行业、因子或货币。",
                "问：这笔投资是在增加分散，还是让组合更集中在同一个宏观押注上？",
                _answer_diversification(snapshot, context),
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
    applicability_reason: str = "适合用来检查生意质量、护城河、现金流和安全边际。",
) -> InvestmentFramework:
    ticker = snapshot.get("ticker", "Unknown")
    move_pct = metrics.get("move_pct_raw")
    context = _framework_context(snapshot, metrics)
    current_read = _value_current_read(move_pct, technical.get("trend_label"), risk.get("risk_label"))
    return InvestmentFramework(
        name="Buffett-Munger 价值投资框架",
        subtitle="好生意、护城河、现金流、安全边际与心理纪律",
        applicability="适用",
        applicability_reason=applicability_reason,
        philosophy="先判断是不是值得长期拥有的好生意，再判断价格是否给了足够安全边际。",
        current_read=current_read,
        items=[
            FrameworkItem(
                "能力圈",
                f"{ticker} 是否能用一句话解释赚钱模式？",
                "问：我真的懂它如何赚钱、为什么客户留下、竞争对手为什么难以复制吗？",
                _answer_circle_of_competence(snapshot, context),
            ),
            FrameworkItem(
                "护城河",
                "品牌、网络效应、成本优势、规模优势或监管壁垒。",
                "问：五年后它的竞争地位更强，还是被技术/竞争侵蚀？",
                _answer_moat(snapshot, context),
            ),
            FrameworkItem(
                "现金流质量",
                "长期看自由现金流、资本回报率和再投资空间。",
                "问：增长需要大量烧钱，还是能把利润稳定转成现金？",
                _answer_cash_flow(snapshot, context),
            ),
            FrameworkItem(
                "安全边际",
                f"近期区间涨跌 {metrics.get('move_pct', 'N/A')}，风险状态 {risk.get('risk_label', '数据不足')}",
                "问：现在的价格是否已经透支乐观预期？如果错了，下行空间有多大？",
                _answer_margin_of_safety(ticker, context, move_pct, risk.get("risk_label")),
            ),
            FrameworkItem(
                "反心理误判",
                "防止追涨、锚定、确认偏误和因为大师持仓而外包判断。",
                "问：如果不知道任何大师买了它，我还愿意独立持有吗？",
                _answer_psychology(ticker, context, move_pct, technical.get("trend_label")),
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


def _framework_context(snapshot: dict, metrics: dict[str, Any]) -> str:
    ticker = snapshot.get("ticker", "该标的")
    timeframe = snapshot.get("timeframe", "当前周期")
    move_text = metrics.get("move_pct", "N/A")
    news = snapshot.get("news") or []
    leading_news = "；".join(str(item.get("title", "")) for item in news[:2] if item.get("title"))
    news_text = f"；新闻线索：{leading_news}" if leading_news else "；暂无明确新闻线索"
    return f"{ticker} 在 {timeframe} 内涨跌 {move_text}{news_text}"


def _answer_cycle_position(ticker: str, context: str, move_pct: float | None, trend: str, risk_label: str) -> str:
    if move_pct is None:
        return f"Dalio 式回答：{ticker} 的价格和新闻证据不足，先不要给周期下结论。"
    if risk_label == "波动偏高":
        return f"Dalio 式回答：{context}。这更像风险偏好下降或宏观变量扰动阶段，先看组合脆弱性而不是预测单点方向。"
    if move_pct >= 5 and trend in {"上升趋势", "短线偏强"}:
        return f"Dalio 式回答：{context}。当前像风险资产顺风期，但还要验证是盈利改善、政策宽松，还是单纯估值扩张。"
    if move_pct <= -5:
        return f"Dalio 式回答：{context}。这像风险资产逆风期，要拆成增长、通胀、利率、信用四个驱动分别看。"
    return f"Dalio 式回答：{context}。周期信号不极端，最佳动作通常是观察、再平衡，而不是大幅押注。"


def _answer_risk_balance(ticker: str, risk_label: str, max_drawdown: float | None) -> str:
    drawdown = _format_optional_pct(max_drawdown)
    if risk_label == "波动偏高":
        return f"Dalio 式回答：{ticker} 最大回撤 {drawdown}，说明它可能正在放大组合波动，需要检查是否有现金、债券、红利或其他区域资产对冲。"
    if risk_label == "中等波动":
        return f"Dalio 式回答：{ticker} 最大回撤 {drawdown}，风险还可观察，但不能假设相关性永远分散。"
    return f"Dalio 式回答：{ticker} 最大回撤 {drawdown}，短期风险温和，但真正的风险平衡要看压力情景下的相关性。"


def _answer_policy_sensitivity(snapshot: dict, context: str) -> str:
    style = str(snapshot.get("selected_preset_style") or "")
    theme = str(snapshot.get("selected_preset_theme") or "")
    if style in {"科技成长", "成长"} or "科技" in theme:
        return f"Dalio 式回答：{context}。成长和科技暴露通常对利率与流动性更敏感，折现率上行会压估值，流动性宽松会放大弹性。"
    if style == "低波红利" or "红利" in theme:
        return f"Dalio 式回答：{context}。红利/低波更像防守资产，但仍会受利率替代效应和经济下行盈利压力影响。"
    return f"Dalio 式回答：{context}。先判断它主要暴露于增长、通胀、利率还是货币，再决定需要什么对冲。"


def _answer_diversification(snapshot: dict, context: str) -> str:
    market = str(snapshot.get("market") or "Unknown")
    style = str(snapshot.get("selected_preset_style") or "")
    if style == "大盘核心":
        return f"Dalio 式回答：{context}。这是 {market} 的核心 beta，适合作为组合底仓，但不能替代跨国家、货币和资产类别的分散。"
    if style:
        return f"Dalio 式回答：{context}。这是 {market} 的 {style} 暴露，可能增加风格集中度，要看组合里是否已经有类似因子。"
    return f"Dalio 式回答：{context}。这是 {market} 标的，至少要检查国家、行业、货币和因子是否已经过度集中。"


def _answer_circle_of_competence(snapshot: dict, context: str) -> str:
    ticker = snapshot.get("ticker", "该标的")
    if snapshot.get("selected_preset_style"):
        return f"Buffett-Munger 式回答：{context}。{ticker} 是一篮子资产，能力圈不是理解每家公司，而是理解指数规则、成分集中度和长期驱动。"
    return f"Buffett-Munger 式回答：{context}。如果不能清楚说出 {ticker} 如何赚钱、客户为何选择它、竞争优势来自哪里，就先不要假装懂。"


def _answer_moat(snapshot: dict, context: str) -> str:
    style = str(snapshot.get("selected_preset_style") or "")
    if style:
        return f"Buffett-Munger 式回答：{context}。ETF 没有单一公司的护城河，重点看底层成分是否普遍有护城河，以及指数是否把劣质公司也一起买进来。"
    return f"Buffett-Munger 式回答：{context}。护城河必须能抵抗时间和竞争。只说公司很有名不够，要能解释定价权、转换成本或网络效应。"


def _answer_cash_flow(snapshot: dict, context: str) -> str:
    style = str(snapshot.get("selected_preset_style") or "")
    if style in {"科技成长", "成长"}:
        return f"Buffett-Munger 式回答：{context}。成长 ETF 要看底层公司是否能把增长转成自由现金流，而不只是收入增速和叙事。"
    if style == "低波红利":
        return f"Buffett-Munger 式回答：{context}。红利 ETF 要区分真实现金流支撑的股息，和因为股价下跌显得股息率很高的陷阱。"
    if style:
        return f"Buffett-Munger 式回答：{context}。ETF 的现金流质量来自成分股整体质量，要关注盈利稳定性、资本回报率和行业周期性。"
    return f"Buffett-Munger 式回答：{context}。好生意最终要体现在自由现金流和资本回报率上，否则增长可能只是昂贵的幻觉。"


def _answer_margin_of_safety(ticker: str, context: str, move_pct: float | None, risk_label: str | None) -> str:
    if move_pct is None:
        return f"Buffett-Munger 式回答：{ticker} 没有价格和估值上下文，就谈不上安全边际。"
    if move_pct >= 5:
        return f"Buffett-Munger 式回答：{context}。上涨后更要保守，先问价格是否已经把好消息都算进去了。"
    if move_pct <= -5:
        return f"Buffett-Munger 式回答：{context}。下跌只有在内在价值未受损时才是机会，否则只是价值陷阱更便宜。"
    if risk_label == "波动偏高":
        return f"Buffett-Munger 式回答：{context}。波动高时安全边际必须更厚，否则情绪会替你做决定。"
    return f"Buffett-Munger 式回答：{context}。价格不极端时，不急着行动，先把内在价值区间和机会成本算清楚。"


def _answer_psychology(ticker: str, context: str, move_pct: float | None, trend: str | None) -> str:
    if move_pct is not None and move_pct >= 5 and trend in {"上升趋势", "短线偏强"}:
        return f"Munger 式回答：{context}。最危险的是把 {ticker} 的上涨当成自己聪明。先写下反方理由，再决定是否值得承担追高风险。"
    if move_pct is not None and move_pct <= -5:
        return f"Munger 式回答：{context}。{ticker} 下跌时也别急着装勇敢。先确认不是基本面变坏，再谈逆向。"
    return f"Munger 式回答：{context}。没有强信号时，少动往往是优势。别为了显得勤奋而交易。"


def _looks_like_etf(ticker: str, query: str) -> bool:
    known_etfs = {
        "SPY",
        "VOO",
        "QQQ",
        "QQQM",
        "VGT",
        "XLK",
        "VUG",
        "SCHG",
        "IWF",
        "SMH",
        "USMV",
        "SPLV",
        "SPHD",
        "SCHD",
        "VIG",
        "DGRO",
    }
    return ticker in known_etfs or query in known_etfs


def _should_apply_dalio(asset_profile: dict[str, str | bool]) -> bool:
    return True


def _should_apply_buffett_munger(asset_profile: dict[str, str | bool]) -> bool:
    return asset_profile["asset_type"] in {"stock", "growth_or_sector_etf", "dividend_factor_etf"}


def _dalio_applicability_reason(asset_profile: dict[str, str | bool]) -> str:
    asset_type = asset_profile["asset_type"]
    if asset_type == "stock":
        return "个股也会受到利率、信用、通胀和市场风险偏好的影响；此框架作为宏观背景使用。"
    if asset_type == "broad_etf":
        return "宽基 ETF 本质是资产配置工具，非常适合用宏观周期和风险平衡框架分析。"
    if asset_type == "growth_or_sector_etf":
        return "成长/行业 ETF 对利率、流动性和风险偏好敏感，适合用宏观框架拆解波动。"
    if asset_type == "dividend_factor_etf":
        return "红利/低波 ETF 常被用作防守或现金流暴露，适合放进风险平衡框架。"
    return "ETF 适合先放到宏观和组合配置框架里理解。"


def _value_applicability_reason(asset_profile: dict[str, str | bool]) -> str:
    asset_type = asset_profile["asset_type"]
    if asset_type == "stock":
        return "个股可以直接分析商业模式、护城河、现金流和管理层纪律。"
    if asset_type == "growth_or_sector_etf":
        return "行业/成长 ETF 不能像单一公司那样估值，但可以检查底层行业质量、集中度和长期现金流质量。"
    if asset_type == "dividend_factor_etf":
        return "红利/低波 ETF 可用价值框架检查股息质量、成分股稳定性和是否只是高股息陷阱。"
    return "此品类不适合完整套用单一公司价值投资框架。"
