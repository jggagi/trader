from __future__ import annotations

import html
import os

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from trader.agent_layer.attribution.engine import AttributionEngine
from trader.agent_layer.critique.engine import MasterCritiqueEngine
from trader.agent_layer.llm import build_default_llm_client
from trader.analysis_layer.insights import (
    build_action_checklist,
    build_markdown_report,
    build_risk_snapshot,
    build_scenario_table,
    build_technical_snapshot,
    enrich_price_frame,
)
from trader.data_layer.etf_catalog import get_markets, get_presets, get_styles
from trader.data_layer.factory import DataProvider, create_market_data_fetcher
from trader.data_layer.master_holdings import (
    MASTER_PORTFOLIOS,
    get_consensus_holdings,
    get_master_names,
    get_master_portfolio,
)
from trader.data_layer.symbols import resolve_symbol
from trader.state_layer.parser import LocalDocumentParser


st.set_page_config(page_title="Market Lens", page_icon="📈", layout="wide")



TIMEFRAME_OPTIONS = {
    "5d": "5天",
    "1mo": "1个月",
    "3mo": "3个月",
    "6mo": "6个月",
    "1y": "1年",
}

PROVIDER_HELP = {
    DataProvider.YAHOO.value: "真实行情与新闻",
    DataProvider.GOOGLE_MOCK.value: "离线演示数据",
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #16202a;
            --muted: #65717d;
            --panel: #ffffff;
            --line: #dfe5ea;
            --teal: #087f8c;
            --teal-soft: #e4f5f6;
            --green: #15803d;
            --red: #b42318;
            --amber: #b7791f;
            --violet: #6d5dfc;
            --blue: #2463eb;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(8, 127, 140, 0.10), transparent 30rem),
                radial-gradient(circle at 85% 5%, rgba(36, 99, 235, 0.08), transparent 26rem),
                linear-gradient(180deg, #f7fafb 0%, #edf2f5 100%);
            color: var(--ink);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #101820 0%, #14212a 100%);
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        [data-testid="stSidebar"] * {
            color: #f7fafc;
        }

        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] select,
        [data-testid="stSidebar"] textarea {
            color: var(--ink);
        }

        [data-testid="stSidebar"] [data-baseweb="select"] * {
            color: var(--ink) !important;
        }

        [data-testid="stSidebar"] button[kind="primary"] {
            background: var(--teal);
            border-color: var(--teal);
            border-radius: 8px;
            font-weight: 760;
        }

        [data-testid="stSidebar"] button[kind="primary"]:hover {
            background: #066b75;
            border-color: #066b75;
        }

        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }

        h1, h2, h3 {
            letter-spacing: 0;
        }

        .app-header {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(236,246,247,0.94));
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 1rem 1.25rem;
            box-shadow: 0 18px 40px rgba(16, 24, 32, 0.08);
            margin-bottom: 1.1rem;
        }

        .app-header:before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 6px;
            background: linear-gradient(180deg, var(--teal), var(--blue));
        }

        .header-kicker {
            color: var(--teal);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
        }

        .header-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .app-title {
            font-size: 2rem;
            line-height: 1.05;
            font-weight: 780;
            color: var(--ink);
        }

        .app-meta {
            color: var(--muted);
            font-size: 0.95rem;
            margin-top: 0.25rem;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.45rem 0.7rem;
            background: #17212b;
            color: white;
            border-radius: 999px;
            font-size: 0.82rem;
            white-space: nowrap;
            box-shadow: 0 10px 22px rgba(23, 33, 43, 0.16);
        }

        .dot {
            width: 0.48rem;
            height: 0.48rem;
            border-radius: 999px;
            background: #34d399;
            box-shadow: 0 0 0 4px rgba(52, 211, 153, 0.14);
        }

        .section-card {
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.7rem;
            box-shadow: 0 14px 34px rgba(16, 24, 32, 0.07);
            margin-top: 0.5rem;
        }

        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.65rem;
            margin: 0.8rem 0 0.8rem;
        }

        .decision-panel {
            display: grid;
            grid-template-columns: 1.35fr 0.65fr;
            gap: 0.85rem;
            margin: 0.75rem 0 0.95rem;
        }

        .decision-main, .decision-side {
            background: var(--panel);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            box-shadow: 0 12px 30px rgba(16, 24, 32, 0.07);
        }

        .decision-main {
            border-top: 4px solid var(--teal);
        }

        .decision-label {
            color: var(--teal);
            font-size: 0.76rem;
            font-weight: 740;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .decision-title {
            color: var(--ink);
            font-size: 1.2rem;
            font-weight: 780;
            line-height: 1.28;
            margin-bottom: 0.4rem;
        }

        .decision-copy {
            color: var(--muted);
            font-size: 0.94rem;
            line-height: 1.5;
        }

        .step-list {
            display: grid;
            gap: 0.5rem;
            margin-top: 0.55rem;
        }

        .step-item {
            display: flex;
            gap: 0.5rem;
            align-items: start;
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.38;
        }

        .step-number {
            width: 1.25rem;
            height: 1.25rem;
            flex: 0 0 1.25rem;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: rgba(8, 127, 140, 0.12);
            color: var(--teal);
            font-size: 0.74rem;
            font-weight: 760;
        }

        .mini-news {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.65rem;
            margin-top: 0.65rem;
        }

        .mini-news-item {
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.78rem;
        }

        .mini-news-source {
            color: var(--teal);
            font-size: 0.72rem;
            font-weight: 720;
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }

        .mini-news-title {
            color: var(--ink);
            font-size: 0.9rem;
            font-weight: 660;
            line-height: 1.34;
        }

        .insight-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
            gap: 0.75rem;
            margin: 0.75rem 0 1rem;
        }

        .insight-card {
            background: var(--panel);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.95rem;
            box-shadow: 0 10px 24px rgba(16, 24, 32, 0.06);
            min-height: 8.4rem;
        }

        .insight-label {
            color: var(--muted);
            font-size: 0.74rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }

        .insight-value {
            color: var(--ink);
            font-size: 1.08rem;
            font-weight: 780;
            margin-bottom: 0.45rem;
        }

        .insight-detail {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.45;
        }

        .checklist {
            display: grid;
            gap: 0.55rem;
            margin-top: 0.75rem;
        }

        .check-item {
            background: rgba(255,255,255,0.86);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.78rem 0.85rem;
            color: var(--ink);
            font-size: 0.93rem;
            line-height: 1.45;
        }

        .overview-band {
            display: grid;
            grid-template-columns: minmax(0, 1fr) 18rem;
            gap: 0.8rem;
            align-items: stretch;
        }

        .risk-meter {
            background: var(--panel);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.95rem;
            box-shadow: 0 12px 30px rgba(16, 24, 32, 0.07);
        }

        .risk-track {
            height: 0.6rem;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--green), var(--amber), var(--red));
            margin: 0.75rem 0 0.45rem;
            position: relative;
            overflow: hidden;
        }

        .risk-track:after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, rgba(255,255,255,0.55), transparent);
        }

        .risk-label-row {
            display: flex;
            justify-content: space-between;
            color: var(--muted);
            font-size: 0.74rem;
        }

        .metric-card {
            background: var(--panel);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.78rem 0.85rem;
            box-shadow: 0 12px 30px rgba(16, 24, 32, 0.07);
            min-width: 0;
            position: relative;
            overflow: hidden;
        }

        .metric-card:before {
            content: "";
            position: absolute;
            inset: 0 0 auto 0;
            height: 3px;
            background: linear-gradient(90deg, var(--teal), var(--blue));
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.77rem;
            font-weight: 650;
            margin-bottom: 0.35rem;
        }

        .metric-value {
            color: var(--ink);
            font-size: 1.16rem;
            font-weight: 760;
            line-height: 1.15;
            overflow-wrap: anywhere;
        }

        .etf-card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 0.55rem;
        }

        .master-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 0.75rem;
            margin-bottom: 0.95rem;
        }

        .master-card {
            background: rgba(255,255,255,0.94);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.9rem;
            box-shadow: 0 10px 24px rgba(16, 24, 32, 0.06);
            min-height: 9rem;
        }

        .master-name {
            color: var(--ink);
            font-size: 1.05rem;
            font-weight: 820;
        }

        .master-entity {
            color: var(--muted);
            font-size: 0.82rem;
            margin-top: 0.2rem;
        }

        .source-link {
            display: inline-flex;
            margin-top: 0.65rem;
            color: var(--teal);
            font-size: 0.82rem;
            font-weight: 760;
            text-decoration: none;
        }

        .consensus-hero {
            background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(228,245,246,0.92));
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 1rem 1.1rem;
            box-shadow: 0 18px 40px rgba(16, 24, 32, 0.08);
            margin-bottom: 1rem;
        }

        .consensus-title {
            color: var(--ink);
            font-size: 1.35rem;
            font-weight: 840;
            line-height: 1.15;
        }

        .consensus-subtitle {
            color: var(--muted);
            font-size: 0.92rem;
            margin-top: 0.3rem;
            line-height: 1.45;
        }

        .consensus-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.72rem;
            margin: 0.8rem 0 1rem;
        }

        .consensus-card {
            background: rgba(255,255,255,0.96);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.82rem;
            box-shadow: 0 10px 24px rgba(16, 24, 32, 0.06);
            min-height: 8.25rem;
        }

        .consensus-rank {
            color: var(--teal);
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .consensus-symbol {
            color: var(--ink);
            font-size: 1.22rem;
            font-weight: 840;
            margin-top: 0.18rem;
        }

        .consensus-meta {
            color: var(--muted);
            font-size: 0.78rem;
            line-height: 1.35;
            margin-top: 0.35rem;
        }

        .etf-card {
            background: rgba(255,255,255,0.94);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.72rem;
        }

        .etf-symbol {
            color: var(--ink);
            font-size: 1rem;
            font-weight: 800;
        }

        .etf-name {
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.35;
            margin-top: 0.15rem;
        }

        .tag-row {
            display: flex;
            gap: 0.35rem;
            flex-wrap: wrap;
            margin-top: 0.55rem;
        }

        .tag {
            border-radius: 999px;
            padding: 0.18rem 0.45rem;
            background: var(--teal-soft);
            color: var(--teal);
            font-size: 0.7rem;
            font-weight: 720;
        }

        .news-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 0.85rem;
            margin-top: 0.85rem;
        }

        .news-card, .critique-card {
            background: var(--panel);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.95rem;
            min-height: 9rem;
            box-shadow: 0 10px 24px rgba(16, 24, 32, 0.06);
        }

        .news-card:hover, .etf-card:hover, .insight-card:hover, .master-card:hover, .consensus-card:hover {
            border-color: rgba(8, 127, 140, 0.28);
            box-shadow: 0 14px 30px rgba(16, 24, 32, 0.09);
        }

        .news-source, .critique-name {
            color: var(--teal);
            font-size: 0.76rem;
            font-weight: 720;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.45rem;
        }

        .news-title {
            color: var(--ink);
            font-size: 0.98rem;
            font-weight: 680;
            line-height: 1.3;
        }

        .news-summary, .critique-body {
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.48;
            margin-top: 0.55rem;
        }

        .critique-card {
            min-height: 12rem;
            border-top: 4px solid var(--violet);
        }

        .critique-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 0.9rem;
            margin-top: 0.85rem;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.35rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 6px;
            padding: 0.55rem 0.95rem;
        }

        .stTabs [aria-selected="true"] {
            background: #17212b;
            color: #ffffff;
        }

        @media (max-width: 700px) {
            .app-title {
                font-size: 1.65rem;
            }
            .app-header {
                padding: 1rem;
            }
            .news-card, .critique-card {
                min-height: auto;
            }
            .metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
            .decision-panel {
                grid-template-columns: 1fr;
            }
            .overview-band {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_market_snapshot(provider: str, ticker: str, timeframe: str) -> dict:
    errors: list[str] = []
    symbol = resolve_symbol(ticker)
    try:
        fetcher = create_market_data_fetcher(DataProvider(provider))
        prices = fetcher.get_historical_prices(ticker=symbol.provider_symbol, timeframe=timeframe)
        news = fetcher.get_recent_news(ticker=symbol.provider_symbol)
    except Exception as exc:
        errors.append(f"{provider} 数据拉取失败，已切换到离线演示数据：{exc}")
        fallback = create_market_data_fetcher(DataProvider.GOOGLE_MOCK)
        prices = fallback.get_historical_prices(ticker=symbol.provider_symbol, timeframe=timeframe)
        news = fallback.get_recent_news(ticker=symbol.provider_symbol)
        provider = DataProvider.GOOGLE_MOCK.value
    return {
        "provider": provider,
        "ticker": symbol.display_symbol,
        "query": symbol.query,
        "provider_symbol": symbol.provider_symbol,
        "market": symbol.market,
        "currency_symbol": symbol.currency_symbol,
        "symbol_note": symbol.note,
        "timeframe": timeframe,
        "prices": [point.model_dump() for point in prices],
        "news": [item.model_dump() for item in news],
        "errors": errors,
    }


def build_price_frame(snapshot: dict) -> pd.DataFrame:
    frame = pd.DataFrame(snapshot["prices"])
    if frame.empty:
        return frame
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("date")


def format_optional_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:+.2f}%"


def compute_market_metrics(frame: pd.DataFrame, news_count: int, ticker: str, currency_symbol: str) -> dict:
    if frame.empty:
        return {
            "ticker": ticker,
            "last_close": "N/A",
            "first_close": None,
            "last_close_raw": None,
            "move_pct_raw": None,
            "move_pct": "N/A",
            "range": "N/A",
            "news_count": str(news_count),
        }

    first_close = float(frame.iloc[0]["close"])
    last_close = float(frame.iloc[-1]["close"])
    move_pct = ((last_close / first_close) - 1) * 100 if first_close else 0.0
    high = float(frame["high"].max())
    low = float(frame["low"].min())
    return {
        "ticker": ticker,
        "last_close": f"{currency_symbol}{last_close:,.2f}",
        "first_close": first_close,
        "last_close_raw": last_close,
        "move_pct_raw": move_pct,
        "move_pct": f"{move_pct:+.2f}%",
        "range": f"{currency_symbol}{low:,.2f} - {currency_symbol}{high:,.2f}",
        "news_count": str(news_count),
    }


def build_plain_language_takeaway(metrics: dict, timeframe: str, news: list[dict]) -> dict:
    move_pct = metrics.get("move_pct_raw")
    readable_timeframe = TIMEFRAME_OPTIONS.get(timeframe, timeframe)
    news_count = len(news)

    if move_pct is None:
        return {
            "title": "暂时没有足够行情数据",
            "body": "可以先切换到 Google Finance Mock 验证界面流程，或稍后重新拉取 Yahoo Finance 数据。",
            "tone": "数据不足",
        }

    if move_pct >= 5:
        title = f"过去{readable_timeframe}明显走强，先看是否由少数大科技股和宏观预期共同推动。"
        tone = "偏强"
    elif move_pct >= 1:
        title = f"过去{readable_timeframe}温和上涨，适合重点核对新闻催化和成交量是否配合。"
        tone = "温和偏强"
    elif move_pct <= -5:
        title = f"过去{readable_timeframe}明显回撤，先排查利率、通胀、财报或风险偏好变化。"
        tone = "偏弱"
    elif move_pct <= -1:
        title = f"过去{readable_timeframe}小幅走弱，重点看下跌是否有明确新闻解释。"
        tone = "温和偏弱"
    else:
        title = f"过去{readable_timeframe}波动不大，短期信号不强，适合等待更清晰的催化。"
        tone = "中性"

    body = (
        f"当前已拉取 {news_count} 条新闻。建议先读“总览”，再进入“归因”和“大师批判”："
        "前者解释发生了什么，后者帮助你避免只看价格而忽略商业质量、机会成本和宏观周期。"
    )
    return {"title": title, "body": body, "tone": tone}


def render_price_chart(frame: pd.DataFrame) -> None:
    chart_frame = enrich_price_frame(frame)
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.76, 0.24],
    )
    fig.add_trace(
        go.Candlestick(
            x=chart_frame["date"],
            open=chart_frame["open"],
            high=chart_frame["high"],
            low=chart_frame["low"],
            close=chart_frame["close"],
            name="OHLC",
            increasing_line_color="#15803d",
            increasing_fillcolor="rgba(21, 128, 61, 0.55)",
            decreasing_line_color="#b42318",
            decreasing_fillcolor="rgba(180, 35, 24, 0.5)",
        ),
        row=1,
        col=1,
    )
    if "ma20" in chart_frame:
        fig.add_trace(
            go.Scatter(
                x=chart_frame["date"],
                y=chart_frame["ma20"],
                mode="lines",
                line=dict(color="#b7791f", width=1.5),
                name="20 日均线",
            ),
            row=1,
            col=1,
        )
    if "ma50" in chart_frame:
        fig.add_trace(
            go.Scatter(
                x=chart_frame["date"],
                y=chart_frame["ma50"],
                mode="lines",
                line=dict(color="#6d5dfc", width=1.5),
                name="50 日均线",
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Bar(
            x=chart_frame["date"],
            y=chart_frame["volume"],
            marker_color="rgba(8, 127, 140, 0.35)",
            name="Volume",
        )
        ,
        row=2,
        col=1,
    )
    fig.update_layout(
        height=440,
        margin=dict(l=8, r=8, t=16, b=6),
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,255,255,0.72)",
        font=dict(color="#17212b", family="Inter, system-ui, sans-serif"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(102,112,124,0.16)", zeroline=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_header(snapshot: dict, metrics: dict, llm_available: bool) -> None:
    llm_label = "AI 已连接" if llm_available else "本地占位分析"
    timeframe = TIMEFRAME_OPTIONS.get(snapshot["timeframe"], snapshot["timeframe"])
    st.markdown(
        f"""
        <div class="app-header">
            <div class="header-kicker">本地优先 · 市场归因分析</div>
            <div class="header-row">
                <div>
                    <div class="app-title">{html.escape(snapshot["ticker"])} 投资观察台</div>
                    <div class="app-meta">{html.escape(snapshot["provider"])} · {html.escape(snapshot["market"])} · 数据代码 {html.escape(snapshot["provider_symbol"])} · {html.escape(timeframe)} · {metrics["news_count"]} 条新闻</div>
                </div>
                <div class="status-pill"><span class="dot"></span>{llm_label}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_runtime_notice() -> None:
    if os.getenv("APP_MODE", "local").lower() != "cloud":
        return
    st.info(
        "当前运行在公网部署模式。请不要上传或粘贴券商 PDF、账户截图、身份证明、API key "
        "或任何真实个人组合明细。这个版本只适合展示公开行情分析。"
    )


def configure_streamlit_secrets() -> None:
    try:
        secrets = st.secrets
    except Exception:
        return

    for key in ("OPENAI_API_KEY", "OPENAI_MODEL", "APP_MODE", "DEFAULT_TICKER"):
        value = secrets.get(key)
        if value and not os.getenv(key):
            os.environ[key] = str(value)


def get_default_ticker() -> str:
    return os.getenv("DEFAULT_TICKER", "SPY").strip().upper() or "SPY"


def render_metrics(metrics: dict) -> None:
    metric_items = [
        ("标的", metrics["ticker"]),
        ("最新收盘", metrics["last_close"]),
        ("区间涨跌", metrics["move_pct"]),
        ("区间范围", metrics["range"]),
    ]
    cards = [
        (
            '<div class="metric-card">'
            f'<div class="metric-label">{html.escape(label)}</div>'
            f'<div class="metric-value">{html.escape(value)}</div>'
            "</div>"
        )
        for label, value in metric_items
    ]
    st.markdown(f'<div class="metric-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_takeaway_panel(takeaway: dict) -> None:
    st.markdown(
        f"""
        <div class="decision-panel">
            <div class="decision-main">
                <div class="decision-label">一句话结论 · {html.escape(takeaway["tone"])}</div>
                <div class="decision-title">{html.escape(takeaway["title"])}</div>
                <div class="decision-copy">{html.escape(takeaway["body"])}</div>
            </div>
            <div class="decision-side">
                <div class="decision-label">建议阅读顺序</div>
                <div class="step-list">
                    <div class="step-item"><span class="step-number">1</span><span>先看价格图，确认趋势和成交量。</span></div>
                    <div class="step-item"><span class="step-number">2</span><span>看新闻卡片，找可能的催化事件。</span></div>
                    <div class="step-item"><span class="step-number">3</span><span>再看归因和大师批判，避免单一视角。</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_mini_news(news: list[dict]) -> None:
    if not news:
        return

    cards = []
    for item in news[:3]:
        source = html.escape(item.get("publisher") or "Unknown")
        title = html.escape(item.get("title") or "Untitled")
        cards.append(
            '<div class="mini-news-item">'
            f'<div class="mini-news-source">{source}</div>'
            f'<div class="mini-news-title">{title}</div>'
            "</div>"
        )
    st.markdown(f'<div class="mini-news">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_news_cards(news: list[dict]) -> None:
    if not news:
        st.info("暂时没有拉取到相关新闻。")
        return

    cards = []
    for item in news[:6]:
        source = html.escape(item.get("publisher") or "Unknown")
        title = html.escape(item.get("title") or "Untitled")
        summary = html.escape(item.get("summary") or item.get("published_at") or "")
        link = item.get("link")
        title_markup = f'<a href="{html.escape(link)}" target="_blank">{title}</a>' if link else title
        cards.append(
            '<div class="news-card">'
            f'<div class="news-source">{source}</div>'
            f'<div class="news-title">{title_markup}</div>'
            f'<div class="news-summary">{summary}</div>'
            "</div>"
        )
    st.markdown(f'<div class="news-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_critique_cards(critique) -> None:
    cards = []
    for view in critique.views:
        cards.append(
            '<div class="critique-card">'
            f'<div class="critique-name">{html.escape(view.name)}</div>'
            f'<div class="critique-body">{html.escape(view.commentary)}</div>'
            "</div>"
        )
    st.markdown(f'<div class="critique-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_investment_dashboard(technical: dict, risk: dict, checklist: list[str]) -> None:
    cards = [
        (
            "趋势状态",
            technical["trend_label"],
            technical["trend_detail"],
        ),
        (
            "距 20 日均线",
            format_optional_pct(technical["distance_to_ma20"]),
            "正数代表价格高于短期均线，负数代表跌破短期均线。",
        ),
        (
            "风险状态",
            risk["risk_label"],
            risk["detail"],
        ),
        (
            "最大回撤",
            format_optional_pct(risk["max_drawdown"]),
            f"年化波动率：{format_optional_pct(risk['annualized_volatility'])}",
        ),
    ]
    html_cards = [
        '<div class="insight-card">'
        f'<div class="insight-label">{html.escape(label)}</div>'
        f'<div class="insight-value">{html.escape(value)}</div>'
        f'<div class="insight-detail">{html.escape(detail)}</div>'
        "</div>"
        for label, value, detail in cards
    ]
    st.markdown(f'<div class="insight-grid">{"".join(html_cards)}</div>', unsafe_allow_html=True)

    st.subheader("行动清单")
    checklist_html = "".join(f'<div class="check-item">{html.escape(item)}</div>' for item in checklist)
    st.markdown(f'<div class="checklist">{checklist_html}</div>', unsafe_allow_html=True)


def render_etf_catalog_preview(presets) -> None:
    if not presets:
        st.info("当前筛选下没有 ETF。")
        return
    cards = []
    for item in presets:
        tags = "".join(
            f'<span class="tag">{html.escape(tag)}</span>'
            for tag in (item.market, item.style, item.theme)
        )
        cards.append(
            '<div class="etf-card">'
            f'<div class="etf-symbol">{html.escape(item.symbol)}</div>'
            f'<div class="etf-name">{html.escape(item.name)}</div>'
            f'<div class="tag-row">{tags}</div>'
            f'<div class="insight-detail" style="margin-top:0.55rem;">{html.escape(item.note)}</div>'
            "</div>"
        )
    st.markdown(
        f'<div class="etf-card-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def render_overview_risk_panel(technical: dict, risk: dict) -> None:
    st.markdown(
        f"""
        <div class="risk-meter">
            <div class="decision-label">趋势 / 风险雷达</div>
            <div class="insight-value">{html.escape(technical["trend_label"])}</div>
            <div class="insight-detail">{html.escape(technical["trend_detail"])}</div>
            <div class="risk-track"></div>
            <div class="risk-label-row"><span>温和</span><span>中等</span><span>偏高</span></div>
            <div class="insight-detail" style="margin-top:0.75rem;">
                {html.escape(risk["risk_label"])} · 最大回撤 {html.escape(format_optional_pct(risk["max_drawdown"]))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_master_cards() -> None:
    cards = []
    for portfolio in MASTER_PORTFOLIOS:
        tags = "".join(
            f'<span class="tag">{html.escape(tag)}</span>'
            for tag in (portfolio.style, portfolio.report_period)
        )
        cards.append(
            '<div class="master-card">'
            f'<div class="master-name">{html.escape(portfolio.master)}</div>'
            f'<div class="master-entity">{html.escape(portfolio.entity)}</div>'
            f'<div class="tag-row">{tags}</div>'
            f'<div class="insight-detail" style="margin-top:0.55rem;">{html.escape(portfolio.learn)}</div>'
            f'<a class="source-link" href="{html.escape(portfolio.source_url)}" target="_blank">{html.escape(portfolio.source_label)}</a>'
            "</div>"
        )
    st.markdown(f'<div class="master-grid">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_consensus_holdings() -> None:
    consensus = get_consensus_holdings()
    if not consensus:
        return

    top = consensus[:6]
    st.markdown(
        """
        <div class="consensus-hero">
            <div class="consensus-title">大师共识塔</div>
            <div class="consensus-subtitle">
                从公开披露持仓中提取被多位投资大师共同持有或反复出现的标的。
                这不是买入建议，而是一个更快进入研究状态的候选清单。
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    figure = go.Figure(
        go.Funnel(
            y=[f"{item.symbol} · {item.name}" for item in top],
            x=[item.score for item in top],
            text=[
                f"{item.conviction_label} · {item.holder_count} 位大师 · {', '.join(item.masters)}"
                for item in top
            ],
            textposition="inside",
            marker={
                "color": ["#087f8c", "#2463eb", "#15803d", "#6d5dfc", "#b7791f", "#65717d"][: len(top)],
                "line": {"width": 1, "color": "rgba(255,255,255,0.85)"},
            },
            connector={"line": {"color": "rgba(22,32,42,0.18)", "dash": "solid", "width": 1}},
            hovertemplate="<b>%{y}</b><br>%{text}<br>共识分: %{x}<extra></extra>",
        )
    )
    figure.update_layout(
        height=360,
        margin={"l": 10, "r": 10, "t": 4, "b": 8},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#16202a", "family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif"},
    )
    st.plotly_chart(figure, use_container_width=True)

    cards = []
    for index, item in enumerate(top, start=1):
        tags = "".join(
            f'<span class="tag">{html.escape(tag)}</span>'
            for tag in (item.conviction_label, f"{item.holder_count} 位大师")
        )
        cards.append(
            '<div class="consensus-card">'
            f'<div class="consensus-rank">Consensus #{index}</div>'
            f'<div class="consensus-symbol">{html.escape(item.symbol)} · {html.escape(item.name)}</div>'
            f'<div class="tag-row">{tags}</div>'
            f'<div class="consensus-meta">持有者：{html.escape(", ".join(item.masters))}</div>'
            f'<div class="consensus-meta">研究线索：{html.escape(item.note)}</div>'
            "</div>"
        )
    st.markdown(f'<div class="consensus-grid">{"".join(cards)}</div>', unsafe_allow_html=True)

    consensus_frame = pd.DataFrame(
        [
            {
                "代码": item.symbol,
                "名称": item.name,
                "共识等级": item.conviction_label,
                "大师人数": item.holder_count,
                "大师": ", ".join(item.masters),
                "主题": " / ".join(item.themes),
                "共识分": item.score,
            }
            for item in consensus
        ]
    )
    with st.expander("查看完整共识清单与计算结果", expanded=False):
        st.dataframe(consensus_frame, hide_index=True, use_container_width=True)


def render_master_holdings() -> None:
    st.info(
        "大师持仓来自公开披露，通常有季度滞后，只适合学习风格和研究线索，不适合作为实时跟单依据。"
    )
    render_consensus_holdings()
    render_master_cards()

    selected_master = st.selectbox("查看大师", get_master_names(), index=0)
    portfolio = get_master_portfolio(selected_master)
    st.subheader(f"{portfolio.master} · {portfolio.entity}")

    meta_cols = st.columns(4)
    meta_cols[0].metric("风格", portfolio.style)
    meta_cols[1].metric("报告期", portfolio.report_period)
    meta_cols[2].metric("披露日期", portfolio.filed_date)
    meta_cols[3].metric("组合规模", portfolio.portfolio_value)

    holdings_frame = pd.DataFrame(
        [
            {
                "代码": item.symbol,
                "名称": item.name,
                "权重/位置": item.weight,
                "学习线索": item.note,
            }
            for item in portfolio.holdings
        ]
    )
    st.dataframe(holdings_frame, hide_index=True, use_container_width=True)
    st.warning(portfolio.caveat)
    st.link_button("打开公开来源", portfolio.source_url, use_container_width=True)


def main() -> None:
    inject_styles()
    configure_streamlit_secrets()

    with st.sidebar:
        st.header("导航")
        page = st.radio("页面", ["市场分析", "大师持仓"], horizontal=True)
        st.divider()

        if page == "大师持仓":
            st.caption("独立学习区：查看公开披露持仓，不依赖当前股票或 ETF。")
            st.caption("这些数据有披露滞后，只适合学习，不适合实时跟单。")
        else:
            st.header("分析设置")
            st.caption("输入美股/ETF 代码，或 A 股 6 位代码。例：SPY、AAPL、600519、000001。")
            default_ticker = get_default_ticker()
            market_filter = st.selectbox(
                "ETF 市场",
                get_markets(),
                index=0,
                help="先按市场缩小范围。",
            )
            style_filter = st.selectbox(
                "ETF 风格",
                get_styles(market_filter),
                index=0,
                help="按你的偏好筛选大盘、科技成长、成长、低波红利等风格。",
            )
            filtered_presets = get_presets(market_filter, style_filter)
            selected_preset = st.selectbox(
                "ETF 快捷选择",
                [None, *filtered_presets],
                format_func=lambda item: "自定义输入" if item is None else item.label,
                help="这些只是常见 ETF 快捷入口，不构成投资建议。",
            )
            if selected_preset:
                ticker = selected_preset.symbol
                st.caption(f"{selected_preset.market} · {selected_preset.style} · {selected_preset.theme} · {selected_preset.note}")
            else:
                ticker = st.text_input("标的代码", value=default_ticker).strip().upper() or default_ticker
            with st.expander("查看当前 ETF 列表", expanded=False):
                render_etf_catalog_preview(filtered_presets)
            timeframe = st.selectbox(
                "观察周期",
                list(TIMEFRAME_OPTIONS),
                index=1,
                format_func=lambda value: TIMEFRAME_OPTIONS[value],
            )
            provider = st.selectbox(
                "数据源",
                [DataProvider.YAHOO.value, DataProvider.GOOGLE_MOCK.value],
                index=0,
                format_func=lambda value: f"{value} · {PROVIDER_HELP[value]}",
            )
            st.divider()
            st.subheader("我的情景推演")
            position_value = st.number_input(
                f"{ticker} 持仓市值（本币）",
                min_value=0.0,
                value=0.0,
                step=1000.0,
                help="只在本地用于估算情景影响，不会上传。",
            )
            shock_pct = st.slider("压力/乐观情景幅度", min_value=3, max_value=25, value=10, step=1)
            run_analysis = st.button("刷新分析", type="primary", use_container_width=True)
            st.divider()
            st.caption("组合文件解析仍是本地占位功能，不会上传你的个人文件。")

    if page == "大师持仓":
        render_master_holdings()
        return

    needs_snapshot = "snapshot" not in st.session_state or "provider_symbol" not in st.session_state.get("snapshot", {})
    if needs_snapshot or run_analysis:
        with st.spinner("Loading market context"):
            st.session_state.snapshot = load_market_snapshot(provider, ticker, timeframe)

    snapshot = st.session_state.snapshot
    price_frame = build_price_frame(snapshot)
    portfolio_state = LocalDocumentParser().get_portfolio_state()
    llm_client = build_default_llm_client()
    metrics = compute_market_metrics(
        price_frame,
        len(snapshot["news"]),
        snapshot["ticker"],
        snapshot["currency_symbol"],
    )
    takeaway = build_plain_language_takeaway(metrics, snapshot["timeframe"], snapshot["news"])
    technical = build_technical_snapshot(price_frame)
    risk = build_risk_snapshot(price_frame)
    checklist = build_action_checklist(
        technical=technical,
        risk=risk,
        move_pct=metrics.get("move_pct_raw"),
        position_value=position_value,
        ticker=snapshot["ticker"],
    )
    scenario_table = build_scenario_table(
        price_frame,
        position_value,
        float(shock_pct),
        snapshot["currency_symbol"],
    )
    report_markdown = build_markdown_report(
        ticker=snapshot["ticker"],
        timeframe=TIMEFRAME_OPTIONS.get(snapshot["timeframe"], snapshot["timeframe"]),
        takeaway=takeaway,
        metrics=metrics,
        technical=technical,
        risk=risk,
        checklist=checklist,
    )

    render_header(snapshot, metrics, llm_available=llm_client.__class__.__name__ != "LocalFallbackLLMClient")
    render_runtime_notice()
    for error in snapshot.get("errors", []):
        st.warning(error)
    if snapshot.get("symbol_note"):
        st.caption(snapshot["symbol_note"])
    render_takeaway_panel(takeaway)
    render_metrics(metrics)

    overview_tab, dashboard_tab, news_tab, attribution_tab, critique_tab, data_tab = st.tabs(
        ["总览", "投资仪表盘", "新闻", "归因", "大师批判", "原始数据"]
    )

    with overview_tab:
        if price_frame.empty:
            st.warning("没有拉取到价格数据。可以换一个数据源或稍后重试。")
        else:
            chart_col, risk_col = st.columns([3.4, 1.1])
            with chart_col:
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                render_price_chart(price_frame)
                st.markdown("</div>", unsafe_allow_html=True)
            with risk_col:
                render_overview_risk_panel(technical, risk)
        st.subheader("最近新闻线索")
        render_mini_news(snapshot["news"])

    with dashboard_tab:
        render_investment_dashboard(technical, risk, checklist)
        st.subheader("持仓情景推演")
        st.dataframe(scenario_table, hide_index=True, use_container_width=True)
        st.download_button(
            "下载本地 Markdown 报告",
            data=report_markdown,
            file_name=f"{snapshot['ticker'].lower()}_market_lens_report.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with news_tab:
        render_news_cards(snapshot["news"])

    with attribution_tab:
        with st.spinner("Synthesizing attribution"):
            attribution = AttributionEngine(llm_client).run(snapshot)
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("客观归因")
        st.write(attribution.narrative)
        st.markdown("</div>", unsafe_allow_html=True)
        if attribution.evidence:
            st.subheader("证据")
            st.dataframe(pd.DataFrame([item.model_dump() for item in attribution.evidence]), hide_index=True)

    with critique_tab:
        with st.spinner("Running roundtable"):
            critique = MasterCritiqueEngine(llm_client).run(
                market_snapshot=snapshot,
                portfolio_state=portfolio_state,
                attribution=attribution,
            )
        render_critique_cards(critique)

    with data_tab:
        st.subheader("新闻原始数据")
        st.dataframe(pd.DataFrame(snapshot["news"]), hide_index=True, use_container_width=True)
        st.subheader("价格原始数据")
        st.dataframe(price_frame, hide_index=True, use_container_width=True)
        st.subheader("本地组合状态")
        st.json(portfolio_state)


if __name__ == "__main__":
    main()
