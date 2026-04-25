from __future__ import annotations

import html

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from trader.agent_layer.attribution.engine import AttributionEngine
from trader.agent_layer.critique.engine import MasterCritiqueEngine
from trader.agent_layer.llm import build_default_llm_client
from trader.data_layer.factory import DataProvider, create_market_data_fetcher
from trader.state_layer.parser import LocalDocumentParser


st.set_page_config(page_title="QQQ Attribution", page_icon="QQQ", layout="wide")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #17212b;
            --muted: #66707c;
            --panel: #ffffff;
            --line: #dfe5ea;
            --teal: #087f8c;
            --green: #15803d;
            --red: #b42318;
            --amber: #b7791f;
            --violet: #6d5dfc;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(8, 127, 140, 0.11), transparent 32rem),
                linear-gradient(180deg, #f7f9fb 0%, #eef3f5 100%);
            color: var(--ink);
        }

        [data-testid="stSidebar"] {
            background: #101820;
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
        }

        [data-testid="stSidebar"] button[kind="primary"]:hover {
            background: #066b75;
            border-color: #066b75;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1240px;
        }

        h1, h2, h3 {
            letter-spacing: 0;
        }

        .app-header {
            background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(236,246,247,0.94));
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-left: 6px solid var(--teal);
            border-radius: 8px;
            padding: 1rem 1.25rem;
            box-shadow: 0 18px 40px rgba(16, 24, 32, 0.08);
            margin-bottom: 1.1rem;
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
            align-items: end;
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

        .metric-card {
            background: var(--panel);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 8px;
            padding: 0.78rem 0.85rem;
            box-shadow: 0 12px 30px rgba(16, 24, 32, 0.07);
            min-width: 0;
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.77rem;
            font-weight: 650;
            margin-bottom: 0.35rem;
        }

        .metric-value {
            color: var(--ink);
            font-size: 1.12rem;
            font-weight: 760;
            line-height: 1.15;
            overflow-wrap: anywhere;
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
            background: rgba(255,255,255,0.68);
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
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=900, show_spinner=False)
def load_market_snapshot(provider: str, ticker: str, timeframe: str) -> dict:
    fetcher = create_market_data_fetcher(DataProvider(provider))
    prices = fetcher.get_historical_prices(ticker=ticker, timeframe=timeframe)
    news = fetcher.get_recent_news(ticker=ticker)
    return {
        "provider": provider,
        "ticker": ticker.upper(),
        "timeframe": timeframe,
        "prices": [point.model_dump() for point in prices],
        "news": [item.model_dump() for item in news],
    }


def build_price_frame(snapshot: dict) -> pd.DataFrame:
    frame = pd.DataFrame(snapshot["prices"])
    if frame.empty:
        return frame
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("date")


def compute_market_metrics(frame: pd.DataFrame, news_count: int, ticker: str) -> dict:
    if frame.empty:
        return {
            "ticker": ticker,
            "last_close": "N/A",
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
        "last_close": f"${last_close:,.2f}",
        "move_pct": f"{move_pct:+.2f}%",
        "range": f"${low:,.2f} - ${high:,.2f}",
        "news_count": str(news_count),
    }


def render_price_chart(frame: pd.DataFrame) -> None:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.76, 0.24],
    )
    fig.add_trace(
        go.Candlestick(
            x=frame["date"],
            open=frame["open"],
            high=frame["high"],
            low=frame["low"],
            close=frame["close"],
            name="OHLC",
            increasing_line_color="#15803d",
            increasing_fillcolor="rgba(21, 128, 61, 0.55)",
            decreasing_line_color="#b42318",
            decreasing_fillcolor="rgba(180, 35, 24, 0.5)",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=frame["date"],
            y=frame["volume"],
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
        showlegend=False,
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(102,112,124,0.16)", zeroline=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_header(snapshot: dict, metrics: dict, llm_available: bool) -> None:
    llm_label = "LLM ready" if llm_available else "Local fallback"
    st.markdown(
        f"""
        <div class="app-header">
            <div class="header-kicker">Local-First Market Attribution</div>
            <div class="header-row">
                <div>
                    <div class="app-title">{html.escape(snapshot["ticker"])} command center</div>
                    <div class="app-meta">{html.escape(snapshot["provider"])} · {html.escape(snapshot["timeframe"])} · {metrics["news_count"]} news items</div>
                </div>
                <div class="status-pill"><span class="dot"></span>{llm_label}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(metrics: dict) -> None:
    metric_items = [
        ("Ticker", metrics["ticker"]),
        ("Last Close", metrics["last_close"]),
        ("Move", metrics["move_pct"]),
        ("Range", metrics["range"]),
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


def render_news_cards(news: list[dict]) -> None:
    if not news:
        st.info("No recent news returned.")
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


def main() -> None:
    inject_styles()

    with st.sidebar:
        st.header("Controls")
        ticker = st.text_input("Ticker", value="QQQ").strip().upper() or "QQQ"
        timeframe = st.selectbox("Timeframe", ["5d", "1mo", "3mo", "6mo", "1y"], index=1)
        provider = st.selectbox(
            "Provider",
            [DataProvider.YAHOO.value, DataProvider.GOOGLE_MOCK.value],
            index=0,
        )
        run_analysis = st.button("Run", type="primary", use_container_width=True)
        st.divider()
        st.caption("Portfolio parser is local-only in Phase 1.")

    if "snapshot" not in st.session_state or run_analysis:
        with st.spinner("Loading market context"):
            st.session_state.snapshot = load_market_snapshot(provider, ticker, timeframe)

    snapshot = st.session_state.snapshot
    price_frame = build_price_frame(snapshot)
    portfolio_state = LocalDocumentParser().get_portfolio_state()
    llm_client = build_default_llm_client()
    metrics = compute_market_metrics(price_frame, len(snapshot["news"]), snapshot["ticker"])

    render_header(snapshot, metrics, llm_available=llm_client.__class__.__name__ != "LocalFallbackLLMClient")
    render_metrics(metrics)

    chart_tab, news_tab, attribution_tab, critique_tab, data_tab = st.tabs(
        ["Price", "News", "Attribution", "Master Critique", "Data"]
    )

    with chart_tab:
        if price_frame.empty:
            st.warning("No price data returned.")
        else:
            with st.container():
                st.markdown('<div class="section-card">', unsafe_allow_html=True)
                render_price_chart(price_frame)
                st.markdown("</div>", unsafe_allow_html=True)

    with news_tab:
        render_news_cards(snapshot["news"])

    with attribution_tab:
        with st.spinner("Synthesizing attribution"):
            attribution = AttributionEngine(llm_client).run(snapshot)
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.subheader("Objective Narrative")
        st.write(attribution.narrative)
        st.markdown("</div>", unsafe_allow_html=True)
        if attribution.evidence:
            st.subheader("Evidence")
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
        st.subheader("Recent News")
        st.dataframe(pd.DataFrame(snapshot["news"]), hide_index=True, use_container_width=True)
        st.subheader("OHLCV")
        st.dataframe(price_frame, hide_index=True, use_container_width=True)
        st.subheader("Portfolio State")
        st.json(portfolio_state)


if __name__ == "__main__":
    main()
