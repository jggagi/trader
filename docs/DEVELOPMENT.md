# Development Workflow

Use GitHub as the source of truth, local development for iteration, and Streamlit Cloud or Render only as deployment targets.

## Daily Start

```bash
cd /Users/guoq/opc/qqq-trader
make pull
make setup
make run
```

Open http://localhost:8502.

## Local Secrets

Local secrets stay in `.env` or your shell:

```bash
cp .env.example .env
```

Do not commit `.env`, `.streamlit/secrets.toml`, brokerage PDFs, screenshots, or private portfolio files.

Cloud secrets belong in the hosting provider's secrets panel:

```toml
APP_MODE = "cloud"
OPENAI_API_KEY = ""
OPENAI_MODEL = "gpt-4o-mini"
```

## Small Changes

For small edits on `main`:

```bash
make pull
make check
git status -sb
git add <files>
git commit -m "Short description"
git push origin main
```

Streamlit Cloud should redeploy from GitHub after the push.

## Larger Features

Use a branch when a change is large, risky, or may take more than one session:

```bash
make pull
git checkout -b feature/short-name
make check
git add <files>
git commit -m "Short description"
git push -u origin feature/short-name
```

Open a pull request on GitHub. Merge to `main` only after checks pass.

## Quality Gate

Run this before every push:

```bash
make check
```

This runs:

- `python -m compileall app.py trader tests`
- `pytest`

GitHub Actions also runs tests on push and pull requests.

## Deployment Model

```text
Local machine
  Develop, test, run with private local files

GitHub
  Source of truth for code and history

Streamlit Cloud / Render
  Pull code from GitHub and run public/demo app
```

Public deployments are not a safe place for personal brokerage documents or private portfolio data.

## Recovery

If the cloud app looks stale:

1. Confirm the latest commit is on GitHub.
2. Check the Streamlit Cloud app logs.
3. Reboot or redeploy from the Streamlit Cloud dashboard.
4. Confirm the app is using branch `main` and entrypoint `app.py`.

