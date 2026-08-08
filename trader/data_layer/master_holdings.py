from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict


@dataclass(frozen=True)
class MasterHolding:
    symbol: str
    name: str
    weight: str
    note: str


@dataclass(frozen=True)
class MasterPortfolio:
    master: str
    entity: str
    style: str
    report_period: str
    filed_date: str
    portfolio_value: str
    source_label: str
    source_url: str
    caveat: str
    learn: str
    holdings: list[MasterHolding]


@dataclass(frozen=True)
class ConsensusHolding:
    symbol: str
    name: str
    holder_count: int
    masters: list[str]
    themes: list[str]
    conviction_label: str
    score: float
    note: str


MASTER_PORTFOLIOS = [
    MasterPortfolio(
        master="Warren Buffett",
        entity="Berkshire Hathaway",
        style="价值 / 质量 / 集中",
        report_period="2026 Q1",
        filed_date="2026-05-15",
        portfolio_value="约 $263B",
        source_label="Berkshire 13F / Kiplinger 汇总",
        source_url="https://www.kiplinger.com/investing/stocks/warren-buffett-stocks-berkshire-hathaway-portfolio",
        caveat="Berkshire 的 13F 不包含全资子公司、现金/T-bills，也可能有保密持仓。",
        learn="看长期护城河、品牌、金融资产和集中度，不要只看季度买卖。",
        holdings=[
            MasterHolding("AAPL", "Apple", "21.99%", "消费科技与生态系统"),
            MasterHolding("AXP", "American Express", "17.43%", "金融网络与品牌"),
            MasterHolding("KO", "Coca-Cola", "11.56%", "消费品牌与分红"),
            MasterHolding("BAC", "Bank of America", "9.52%", "银行资产"),
            MasterHolding("CVX", "Chevron", "6.64%", "能源暴露"),
        ],
    ),
    MasterPortfolio(
        master="Charlie Munger",
        entity="Daily Journal Corp",
        style="极度集中 / 长期持有",
        report_period="2026 Q1",
        filed_date="2026-04-15",
        portfolio_value="约 $241M",
        source_label="Daily Journal 13F",
        source_url="https://13f.info/manager/0000783412-daily-journal-corp",
        caveat="芒格已于 2023 年去世；这里展示的是 Daily Journal 公开组合，不等于个人实时持仓。",
        learn="学习集中持仓、长期忍耐和反复研究少数标的的方式。",
        holdings=[
            MasterHolding("WFC", "Wells Fargo", "公开前列", "银行长期持仓"),
            MasterHolding("BAC", "Bank of America", "公开前列", "银行长期持仓"),
            MasterHolding("BABA", "Alibaba", "公开前列", "中国互联网"),
            MasterHolding("USB", "U.S. Bancorp", "公开前列", "银行资产"),
        ],
    ),
    MasterPortfolio(
        master="Duan Yongping",
        entity="H&H International Investment",
        style="本分 / 好生意 / 高集中",
        report_period="2026 Q1",
        filed_date="公开 13F 汇总",
        portfolio_value="约 $20B",
        source_label="H&H 13F / HoldingsChannel 汇总",
        source_url="https://www.holdingschannel.com/13f/h-h-international-investment-llc-top-holdings/",
        caveat="13F 只覆盖美国上市证券；段永平的非美股、个人直接持仓和现金无法完整体现。",
        learn="重点看好商业、自由现金流、长期主义和对少数公司深度理解。",
        holdings=[
            MasterHolding("AAPL", "Apple", "最大持仓", "长期核心"),
            MasterHolding("BRK.B", "Berkshire Hathaway", "前列", "价值与资本配置"),
            MasterHolding("NVDA", "Nvidia", "前列", "AI/半导体"),
            MasterHolding("PDD", "PDD Holdings", "前列", "中国电商"),
            MasterHolding("TSLA", "Tesla", "前列", "成长/制造"),
        ],
    ),
    MasterPortfolio(
        master="Li Lu",
        entity="Himalaya Capital Management",
        style="价值 / 中国认知 / 集中",
        report_period="2026 Q1",
        filed_date="公开 13F 汇总",
        portfolio_value="约 $3.2B",
        source_label="Himalaya 13F / ValueSider 汇总",
        source_url="https://www2.valuesider.com/guru/li-lu-himalaya-capital-management/portfolio",
        caveat="13F 不包含港股、A 股、私有投资或现金；李录很多重要投资可能不在 13F 中。",
        learn="学习跨市场认知、深度研究、逆向和长期复利。",
        holdings=[
            MasterHolding("GOOGL", "Alphabet Class A", "22.85%", "互联网基础设施"),
            MasterHolding("GOOG", "Alphabet Class C", "21.97%", "互联网基础设施"),
            MasterHolding("PDD", "PDD Holdings", "14.71%", "中国电商"),
            MasterHolding("BRK.B", "Berkshire Hathaway", "13.44%", "价值与资本配置"),
            MasterHolding("EWBC", "East West Bancorp", "9.26%", "金融资产"),
        ],
    ),
    MasterPortfolio(
        master="Ray Dalio",
        entity="Bridgewater Associates",
        style="宏观 / 分散 / 风险平衡",
        report_period="2026 Q1",
        filed_date="2026-05-15",
        portfolio_value="约 $22.4B",
        source_label="Bridgewater 13F",
        source_url="https://13f.info/manager/0001350694-bridgewater-associates-lp",
        caveat="Bridgewater 是宏观多资产机构，13F 只展示部分美国证券，不能代表完整 All Weather / Pure Alpha 仓位。",
        learn="学习资产配置、风险平衡、分散和宏观周期视角。",
        holdings=[
            MasterHolding("SPY", "SPDR S&P 500 ETF", "12.67%", "美国大盘 beta"),
            MasterHolding("IVV", "iShares Core S&P 500 ETF", "7.81%", "美国大盘 beta"),
            MasterHolding("AMZN", "Amazon", "4.08%", "云/消费/AI 基础设施"),
            MasterHolding("NVDA", "Nvidia", "3.65%", "AI/半导体"),
            MasterHolding("GOOGL", "Alphabet Class A", "2.56%", "互联网基础设施"),
        ],
    ),
]


def get_master_names() -> list[str]:
    return [portfolio.master for portfolio in MASTER_PORTFOLIOS]


def get_master_portfolio(name: str) -> MasterPortfolio:
    for portfolio in MASTER_PORTFOLIOS:
        if portfolio.master == name:
            return portfolio
    return MASTER_PORTFOLIOS[0]


CANONICAL_SYMBOLS = {
    "GOOG": "GOOGL",
}


def _canonical_symbol(symbol: str) -> str:
    return CANONICAL_SYMBOLS.get(symbol, symbol)


def _weight_score(weight: str) -> float:
    if "%" in weight:
        try:
            return min(float(weight.replace("%", "").strip()), 25.0) / 25.0
        except ValueError:
            return 0.45
    if "最大" in weight:
        return 1.0
    if "前列" in weight or "前" in weight:
        return 0.72
    return 0.5


def get_consensus_holdings(min_holders: int = 2) -> list[ConsensusHolding]:
    grouped: dict[str, list[tuple[MasterPortfolio, MasterHolding]]] = defaultdict(list)
    for portfolio in MASTER_PORTFOLIOS:
        for holding in portfolio.holdings:
            grouped[_canonical_symbol(holding.symbol)].append((portfolio, holding))

    consensus: list[ConsensusHolding] = []
    for symbol, entries in grouped.items():
        masters = sorted({portfolio.master for portfolio, _ in entries})
        if len(masters) < min_holders:
            continue

        first_holding = entries[0][1]
        names = [holding.name for _, holding in entries if holding.symbol == symbol]
        name = names[0] if names else first_holding.name
        themes = sorted({holding.note for _, holding in entries})
        average_weight_score = sum(
            _weight_score(holding.weight) for _, holding in entries
        ) / len(entries)
        score = round(len(masters) * 20 + average_weight_score * 40, 1)
        if len(masters) >= 3:
            conviction_label = "高共识"
        elif average_weight_score >= 0.75:
            conviction_label = "强线索"
        else:
            conviction_label = "交叉验证"
        consensus.append(
            ConsensusHolding(
                symbol=symbol,
                name=name,
                holder_count=len(masters),
                masters=masters,
                themes=themes,
                conviction_label=conviction_label,
                score=score,
                note=" / ".join(themes[:2]),
            )
        )

    return sorted(
        consensus,
        key=lambda item: (item.holder_count, item.score, item.symbol),
        reverse=True,
    )
