from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EtfPreset:
    symbol: str
    name: str
    market: str
    style: str
    theme: str
    note: str

    @property
    def label(self) -> str:
        return f"{self.symbol} · {self.name}"


ETF_PRESETS = [
    EtfPreset("SPY", "S&P 500", "美股", "大盘核心", "大盘", "美国大盘核心暴露"),
    EtfPreset("VOO", "Vanguard S&P 500", "美股", "大盘核心", "大盘", "低费率 S&P 500"),
    EtfPreset("QQQ", "Nasdaq 100", "美股", "科技成长", "科技/成长", "大型科技与成长权重高"),
    EtfPreset("QQQM", "Nasdaq 100 低费率版本", "美股", "科技成长", "科技/成长", "QQQ 的低费率版本"),
    EtfPreset("VGT", "Vanguard Information Technology", "美股", "科技成长", "科技", "美国信息技术行业"),
    EtfPreset("XLK", "Technology Select Sector", "美股", "科技成长", "科技", "S&P 500 科技板块"),
    EtfPreset("VUG", "Vanguard Growth", "美股", "成长", "成长", "美国大盘成长"),
    EtfPreset("SCHG", "Schwab U.S. Large-Cap Growth", "美股", "成长", "成长", "美国大盘成长"),
    EtfPreset("IWF", "Russell 1000 Growth", "美股", "成长", "成长", "Russell 1000 成长"),
    EtfPreset("SMH", "VanEck Semiconductor", "美股", "科技成长", "半导体", "全球半导体龙头"),
    EtfPreset("USMV", "MSCI USA Minimum Volatility", "美股", "低波红利", "低波", "美国最小波动因子"),
    EtfPreset("SPLV", "S&P 500 Low Volatility", "美股", "低波红利", "低波", "S&P 500 低波动"),
    EtfPreset("SPHD", "S&P 500 High Dividend Low Volatility", "美股", "低波红利", "红利/低波", "高股息 + 低波动"),
    EtfPreset("SCHD", "Schwab U.S. Dividend Equity", "美股", "低波红利", "红利", "美国股息质量"),
    EtfPreset("VIG", "Vanguard Dividend Appreciation", "美股", "低波红利", "红利成长", "股息增长"),
    EtfPreset("DGRO", "iShares Core Dividend Growth", "美股", "低波红利", "红利成长", "股息增长"),
    EtfPreset("510300", "沪深300ETF", "A股", "大盘核心", "大盘", "A股大盘核心"),
    EtfPreset("510050", "上证50ETF", "A股", "大盘核心", "大盘", "沪市大盘蓝筹"),
    EtfPreset("588000", "科创50ETF", "A股", "科技成长", "科技/成长", "科创板科技成长"),
    EtfPreset("159915", "创业板ETF", "A股", "成长", "成长", "创业板成长风格"),
    EtfPreset("159949", "创业板50ETF", "A股", "成长", "成长", "创业板龙头成长"),
    EtfPreset("512480", "半导体ETF", "A股", "科技成长", "半导体", "A股半导体产业"),
    EtfPreset("515000", "科技ETF", "A股", "科技成长", "科技", "A股科技龙头"),
    EtfPreset("159995", "芯片ETF", "A股", "科技成长", "芯片", "A股芯片产业"),
    EtfPreset("512890", "红利低波ETF", "A股", "低波红利", "红利/低波", "中证红利低波动"),
    EtfPreset("515100", "低波红利ETF", "A股", "低波红利", "红利/低波", "红利低波100"),
    EtfPreset("510880", "红利ETF", "A股", "低波红利", "红利", "上证红利"),
    EtfPreset("515080", "中证红利ETF", "A股", "低波红利", "红利", "中证红利"),
]


def get_markets() -> list[str]:
    return ["全部"] + sorted({item.market for item in ETF_PRESETS})


def get_styles(market: str) -> list[str]:
    items = _filter_items(market=market, style="全部")
    return ["全部"] + sorted({item.style for item in items})


def get_presets(market: str = "全部", style: str = "全部") -> list[EtfPreset]:
    return _filter_items(market=market, style=style)


def _filter_items(market: str, style: str) -> list[EtfPreset]:
    items = ETF_PRESETS
    if market != "全部":
        items = [item for item in items if item.market == market]
    if style != "全部":
        items = [item for item in items if item.style == style]
    return items
