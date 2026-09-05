# RecoverOS v0.5

AI Revenue Recovery platform for Razorpay Buildathon Track 03.

## Current capabilities
- Synthetic revenue-risk dataset and ML baseline
- Recovery economics / expected recovery value
- Deterministic policy guard
- Multi-LLM routing: fast / standard / premium
- Provider fallback
- Local soft quota manager
- Mock benchmark lab (no API keys required)
- Live benchmark mode (API keys required)
- FastAPI + Swagger API

## Run backend
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
python -m uvicorn app.main:app --reload --port 8000
```

Swagger: http://127.0.0.1:8000/docs

## Benchmark without API keys
- GET `/api/ai/benchmark?limit=100&live=false`
- GET `/api/ai/quota`
- GET `/api/ai/status`

Mock mode is deterministic and does not call any provider.

## Live benchmark
Set provider keys in `.env`, verify model IDs available to your accounts, then use `/api/ai/benchmark?limit=100&live=true`.
Never commit `.env` or API keys.
