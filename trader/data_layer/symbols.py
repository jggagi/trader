from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolResolution:
    query: str
    provider_symbol: str
    display_symbol: str
    market: str
    currency_symbol: str
    note: str | None = None


def resolve_symbol(raw_ticker: str) -> SymbolResolution:
    query = (raw_ticker or "").strip().upper()
    if not query:
        query = "SPY"

    if _is_china_a_share_code(query):
        suffix = _china_a_share_suffix(query)
        provider_symbol = f"{query}{suffix}"
        return SymbolResolution(
            query=query,
            provider_symbol=provider_symbol,
            display_symbol=query,
            market=_china_market_name(suffix),
            currency_symbol="¥",
            note=f"已自动映射到 Yahoo Finance 代码 {provider_symbol}",
        )

    if _has_china_suffix(query):
        return SymbolResolution(
            query=query,
            provider_symbol=query,
            display_symbol=query,
            market=_china_market_name(query[-3:]),
            currency_symbol="¥",
        )

    return SymbolResolution(
        query=query,
        provider_symbol=query,
        display_symbol=query,
        market="US / Global",
        currency_symbol="$",
    )


def _is_china_a_share_code(value: str) -> bool:
    return len(value) == 6 and value.isdigit()


def _china_a_share_suffix(value: str) -> str:
    if value.startswith(("5", "6", "9")):
        return ".SS"
    if value.startswith(("0", "1", "2", "3")):
        return ".SZ"
    if value.startswith(("4", "8")):
        return ".BJ"
    return ".SS"


def _has_china_suffix(value: str) -> bool:
    return value.endswith((".SS", ".SZ", ".BJ"))


def _china_market_name(suffix: str) -> str:
    return {
        ".SS": "China A · Shanghai",
        ".SZ": "China A · Shenzhen",
        ".BJ": "China A · Beijing",
    }.get(suffix, "China A")
