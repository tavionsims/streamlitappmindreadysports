# MindReady Sports — Beta Streamlit Demo

This is a lightweight Streamlit prototype with 3 role-based views:
- Athlete: 3-question mental readiness check-in + placeholder tools
- Coach: anonymized, aggregated team trends (counts)
- Clinician: individual history + simple early-flag rules + clinician entry

## Quick start

1) Create a virtual environment (recommended)
- Windows (PowerShell):
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1

- macOS/Linux:
  python -m venv .venv
  source .venv/bin/activate

2) Install dependencies
  pip install -r requirements.txt

3) Run the app
  streamlit run app.py

## Notes
- Responses are stored locally at `data/responses.csv`
- This is a class demo prototype (no diagnosis, privacy-first design)
