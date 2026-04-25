# Local-First QQQ Attribution & Master Critique

A modular Streamlit app for local market attribution and skill-based critique.

## Phase 1

- Market data layer behind `BaseMarketDataFetcher`
- Yahoo Finance provider and Google Finance mock provider
- Local portfolio parser placeholder that returns `{}`
- Stateless attribution and critique calls
- Streamlit UI for QQQ price/news context and roundtable output

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
streamlit run app.py
```

LLM calls are optional. Without `OPENAI_API_KEY`, the app returns deterministic local placeholder analysis so the local workflow remains usable.

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4o-mini"
```

## Tests

```bash
pytest
```

