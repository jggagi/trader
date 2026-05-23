# Deployment

## Recommended: Streamlit Community Cloud

1. Push `main` to GitHub.
2. Open https://share.streamlit.io/.
3. Create a new app.
4. Select repository `jggagi/trader`.
5. Select branch `main`.
6. Set main file path to `app.py`.
7. Add secrets:

```toml
APP_MODE = "cloud"
OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-4o-mini"
```

The app works without `OPENAI_API_KEY`, using deterministic local fallback analysis.

## Alternative: Render

This repository includes `render.yaml`.

Render settings:

- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`
- Environment:
  - `APP_MODE=cloud`
  - `OPENAI_MODEL=gpt-4o-mini`
  - `OPENAI_API_KEY`, optional

Free Render services can sleep when idle, so first load can be slow.

## Production Safety

Cloud mode is for public ticker analysis and demos. It is not for sensitive personal portfolio processing.

Keep private files local:

- Brokerage PDFs
- Account screenshots
- API keys
- Identity documents
- Real portfolio exports

