# Market Lens

A modular Streamlit app for market attribution, local investment dashboards, risk snapshots, scenario analysis, and skill-based critique across tickers.

## Features

- Market data layer behind `BaseMarketDataFetcher`
- Yahoo Finance provider and Google Finance mock provider
- Local portfolio parser placeholder that returns `{}`
- Stateless attribution and critique calls
- Chinese Streamlit UI for ticker price/news context and roundtable output
- Technical dashboard with 20/50 day moving averages
- Risk snapshot with volatility and max drawdown
- Position scenario table and Markdown report export
- Filterable ETF catalog for common large-cap, technology, growth, low-volatility, and dividend ETFs in US and China A-share markets
- Master holdings study view for selected public 13F-style portfolios

## Run Locally

```bash
python -m venv .venv
source .venv/bin/activate
make setup
make run
```

LLM calls are optional. Without `OPENAI_API_KEY`, the app returns deterministic local placeholder analysis so the local workflow remains usable.

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4o-mini"
export DEFAULT_TICKER="SPY"
```

For development tests:

```bash
make check
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for the full local to GitHub to cloud workflow.

## Deploy For Free

Recommended path: Streamlit Community Cloud.

1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io/).
3. Create a new app from `jggagi/trader`.
4. Use branch `main` and entrypoint `app.py`.
5. In the app's Secrets panel, add:

```toml
APP_MODE = "cloud"
OPENAI_API_KEY = "your-api-key-if-you-want-ai-output"
OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_TICKER = "SPY"
```

Without `OPENAI_API_KEY`, the app still works with deterministic local fallback analysis.

Alternative path: Render free web service.

- This repo includes `render.yaml`.
- Render free services can spin down when idle, so first load may be slower.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment details.

## Security Notes

The original design is local-first. A public deployment changes the threat model:

- Do not upload or paste brokerage PDFs, account screenshots, API keys, identity documents, or true private portfolio details into a public app.
- The current portfolio parser remains a placeholder and returns `{}`.
- Secrets must live in Streamlit Cloud / Render secrets, never in git.
- Public deployments are suitable for public ticker analysis and product demos, not sensitive personal portfolio processing.

## Tests

```bash
pytest
```
