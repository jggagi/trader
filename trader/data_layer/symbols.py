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

    prefixed_symbol = _resolve_prefixed_symbol(query)
    if prefixed_symbol:
        return prefixed_symbol

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

    if _has_hong_kong_suffix(query):
        return SymbolResolution(
            query=query,
            provider_symbol=_normalize_hong_kong_symbol(query),
            display_symbol=_normalize_hong_kong_symbol(query),
            market="Hong Kong",
            currency_symbol="HK$",
        )

    if _has_japan_suffix(query):
        return SymbolResolution(
            query=query,
            provider_symbol=query,
            display_symbol=query,
            market="Japan",
            currency_symbol="¥",
        )

    return SymbolResolution(
        query=query,
        provider_symbol=query,
        display_symbol=query,
        market="US / Global",
        currency_symbol="$",
    )


def _resolve_prefixed_symbol(query: str) -> SymbolResolution | None:
    if ":" not in query:
        return None

    prefix, raw_symbol = query.split(":", 1)
    symbol = raw_symbol.strip()
    if prefix in {"HK", "HKG", "香港"} and symbol:
        padded = symbol.zfill(4)
        provider_symbol = f"{padded}.HK"
        return SymbolResolution(
            query=query,
            provider_symbol=provider_symbol,
            display_symbol=provider_symbol,
            market="Hong Kong",
            currency_symbol="HK$",
            note=f"已自动映射到 Yahoo Finance 港股代码 {provider_symbol}",
        )

    if prefix in {"JP", "JPN", "TYO", "日本"} and symbol:
        provider_symbol = f"{symbol}.T" if not symbol.endswith(".T") else symbol
        return SymbolResolution(
            query=query,
            provider_symbol=provider_symbol,
            display_symbol=provider_symbol,
            market="Japan",
            currency_symbol="¥",
            note=f"已自动映射到 Yahoo Finance 日股代码 {provider_symbol}",
        )

    return None


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


def _has_hong_kong_suffix(value: str) -> bool:
    return value.endswith(".HK")


def _normalize_hong_kong_symbol(value: str) -> str:
    code = value.removesuffix(".HK")
    return f"{code.zfill(4)}.HK" if code.isdigit() else value


def _has_japan_suffix(value: str) -> bool:
    return value.endswith(".T")


def _china_market_name(suffix: str) -> str:
    return {
        ".SS": "China A · Shanghai",
        ".SZ": "China A · Shenzhen",
        ".BJ": "China A · Beijing",
    }.get(suffix, "China A")
