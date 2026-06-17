# CandleMind Agent Guide

This file is for coding agents that need to understand, run, deploy, or maintain CandleMind quickly.

## Project

CandleMind, Chinese name `烛机`, is an A-share daily K-line AI prophecy terminal.

Core flow:

1. User enters an A-share stock code.
2. Backend pulls recent K-line data, news, and announcements.
3. Backend computes technical indicators and historical analogs.
4. DeepSeek/OpenAI-compatible LLM makes the final direction judgment.
5. Frontend renders real candles plus one explicit forecast candlestick path.

The app is based on `666ghj/MiroFish`, but the active product surface is CandleMind.

## Repository Shape

- `frontend/`: Vue 3 + Vite app.
- `frontend/src/views/StockProphecyView.vue`: main CandleMind UI.
- `frontend/src/api/stock.js`: stock prophecy API client.
- `frontend/public/candlemind-icon.svg`: app icon.
- `frontend/public/candlemind-logo.svg`: horizontal logo.
- `backend/`: Flask backend.
- `backend/app/api/stock.py`: stock API blueprint.
- `backend/app/services/stock_market_data.py`: Eastmoney/Sina market data.
- `backend/app/services/stock_events.py`: Eastmoney news and announcements.
- `backend/app/services/stock_indicators.py`: indicators and analogs.
- `backend/app/services/stock_prophecy.py`: orchestration, LLM judgment, forecast candles.
- `backend/app/services/stock_archive.py`: short-lived prophecy cache and local JSON audit archive.
- `Dockerfile`: builds frontend and backend into one image.
- `docker-compose.yml`: local/server container deployment.
- `.github/workflows/docker-image.yml`: GHCR image build on tag or manual dispatch.

## Secrets

Never commit `.env` or real API keys.

Required runtime env:

```env
LLM_API_KEY=your_deepseek_or_openai_compatible_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_NAME=deepseek-v4-pro

ZEP_API_KEY=dummy

STOCK_PROPHECY_CACHE_TTL_SECONDS=600
STOCK_PROPHECY_ARCHIVE_DIR=./data/prophecies

FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=False
```

Notes:

- A real `LLM_API_KEY` is required for LLM prophecy.
- `ZEP_API_KEY=dummy` is acceptable for CandleMind. It exists for historical compatibility.
- `.env` is ignored by git.
- Prophecy archives are written under `data/prophecies` by default. `data/` is ignored by git.

## Local Setup

From repo root:

```bash
npm run setup:all
cp .env.example .env
```

Fill `.env`, then run:

```bash
npm run dev
```

Default URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:5001`

Run separately:

```bash
npm run backend
npm run frontend
```

## Verification

Frontend build:

```bash
npm run build
```

Backend lock check:

```bash
cd backend && uv lock --check
```

Backend API smoke test:

```bash
curl -sS http://localhost:5001/api/stock/prophecy \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"600519","horizon":5,"days":120,"includeEvents":true,"useLlm":true}'
```

Expected:

- Response has `success: true`.
- `data.llmProphecy.status` should be `ok` when LLM key is valid.
- `data.forecast.candles` should contain forecast candles.
- `data.archive.id` identifies the local audit archive for this run.
- A repeated request within `STOCK_PROPHECY_CACHE_TTL_SECONDS` should return `data.cache.hit: true`.

Backend tests:

```bash
cd backend && python -m pytest tests
```

## Docker Deployment

On a server with Docker:

```bash
git clone git@github.com:wackyX/CandleMind.git
cd CandleMind
cp .env.example .env
# edit .env with real values
docker compose up -d --build
```

Check:

```bash
docker compose ps
docker compose logs -f
```

Stop:

```bash
docker compose down
```

Container exposes:

- `3000`: frontend Vite preview
- `5001`: Flask backend

## GitHub Container Registry

Workflow: `.github/workflows/docker-image.yml`

Build image by pushing a tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Expected image:

```text
ghcr.io/wackyx/candlemind:latest
```

The repository owner name may be lowercased by GHCR.

## Production Notes

The current Dockerfile starts both services in one container:

```bash
cd /app/backend && uv run python run.py &
cd /app/frontend && npm run preview -- --host 0.0.0.0 --port 3000
```

This is simple and works for a small MVP. For a more robust production deployment, split frontend and backend into separate services and put them behind a reverse proxy.

Recommended reverse proxy routes:

- `/` -> frontend `3000`
- `/api/*` -> backend `5001`

If frontend and backend are deployed on different domains, set:

```env
VITE_API_BASE_URL=https://your-backend-domain
```

Then rebuild the frontend.

## Common Issues

### `LLM_API_KEY 未配置为真实密钥`

The backend process did not read a real key. Restart the backend after editing `.env`.

```bash
docker compose restart
```

or local:

```bash
cd backend && uv run python run.py
```

### LLM JSON parse failure

`stock_prophecy.py` includes JSON extraction and repair. If failures persist, reduce prompt size or increase `max_tokens` in `run_llm_prophecy`.

### Eastmoney data is unavailable

The backend tries Eastmoney first, then falls back to Sina historical K-line and Eastmoney realtime where possible. Do not fake market data.

### Frontend shows old UI

Restart Vite or rebuild:

```bash
npm run frontend
npm run build
```

### Port conflict

Defaults are `3000` and `5001`. Check:

```bash
lsof -nP -iTCP:3000 -sTCP:LISTEN
lsof -nP -iTCP:5001 -sTCP:LISTEN
```

## Safety Rules

- Do not commit `.env`.
- Do not print real API keys in logs or final responses.
- Do not present output as investment advice.
- Do not fake current K-line data.
- Keep forecast as one explicit path, not simultaneous bullish and bearish paths.
- Forecast candles should look like real candles, including upper and lower wicks.
