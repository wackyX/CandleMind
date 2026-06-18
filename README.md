<div align="center">

<img src="./frontend/public/candlemind-logo.svg" alt="CandleMind" width="72%"/>

# CandleMind

AI candlestick prophecy terminal for China A-shares

English | [中文文档](./README-ZH.md)

</div>

## Overview

**CandleMind** is an open-source research workstation for China A-share daily candlesticks. Enter a stock code and it pulls real K-line data, recent news and announcements, technical indicators, historical analogs and an optional user-provided LLM to generate a single forecast candlestick path after the real chart.

It is built for research, review, product prototyping and open-source experimentation. It is **not investment advice**.

## What It Does

- **A-share stock input**: enter a 6-digit A-share code such as `600519`
- **Real daily K-line chart**: shows recent real candlesticks with stock name, code, exchange and cycle
- **Forecast candlesticks**: appends one explicit prophecy path after the real K-line chart
- **Candlestick animation**: forecast candles render step by step, including upper/lower wicks
- **News and announcement events**: pulls recent Eastmoney news and announcements when enabled
- **Technical analysis**: MA, RSI, ATR, BOLL, support/resistance and turnover mood
- **Historical analogs**: compares current structure with similar historical patterns
- **User-owned LLM**: supports OpenAI-compatible providers such as DeepSeek, OpenAI, Qwen, Ollama and LM Studio
- **Explainability chain**: breaks down the prophecy into technical, analog, event, model and risk layers
- **Credibility radar**: visualizes signal consistency across technicals, events, LLM and risk
- **Single-date backtest**: choose a historical cut-off date and compare the forecast with actual future candles
- **Batch backtest**: sample multiple historical cut-off dates and calculate hit rate and average error
- **Data source health check**: checks market data, realtime data, event data and LLM configuration
- **Data source record**: every report records actual provider, fallback status, latest candle date, event count and LLM status
- **Local archive and cache**: saves local prophecy archives and reuses short-lived identical requests
- **Dual UI themes**: light and dark terminal styles with red/gold/cold-gray market palette

## Prophecy Modes

### Live Prophecy

Generates a forward-looking candlestick path from the latest available A-share daily K-line data.

Typical use:

```json
{
  "symbol": "600519",
  "horizon": 5,
  "days": 180,
  "includeEvents": true,
  "useLlm": true
}
```

### Single-Date Backtest

Uses only data available up to a selected historical date, generates the prophecy from that point, then compares it against actual future candles.

The chart history is capped at the backtest date. Actual future candles are shown only in the prophecy comparison area.

### Batch Backtest

Samples multiple historical cut-off dates and reports:

- direction hit rate
- average hit score
- average absolute error
- average return error
- per-sample predicted return vs actual return

The UI also shows one recent reference backtest chart so users can inspect the K-line-level behavior.

## Explainability

Each prophecy report includes a structured `explanation` object and a frontend "Evidence Chain" panel.

Explanation layers:

- **Technical Structure**: MA alignment, RSI, support/resistance and price position
- **Historical Analog**: similar-pattern sample size, up probability and forward return
- **Event Driver**: recent news/announcement signal and event score
- **Model Judgment**: LLM summary, reasons and confidence when enabled
- **Risk Boundary**: ATR, support/resistance distance and invalidation triggers

Each layer has a score, stance (`support`, `caution`, `oppose`) and concrete evidence points. The report also includes invalidation triggers for when the prophecy should be recalculated.

## Data Sources

CandleMind currently focuses only on the China A-share market.

Market data flow:

1. Eastmoney daily K-line is preferred
2. If Eastmoney daily K-line fails, Sina historical K-line is used as fallback
3. Eastmoney realtime data can be merged when available
4. Demo data remains available for tests and offline UI work

Event data:

- Eastmoney news search
- Eastmoney announcements
- Local transparent keyword-based event scoring

Health check endpoint:

```http
GET /api/config/data-sources/health?symbol=600519
```

Report source record:

```json
{
  "dataSources": {
    "market": {
      "requestedProvider": "eastmoney",
      "actualProvider": "sina+eastmoney_realtime",
      "fallbackUsed": true,
      "latestCandleDate": "2026-06-18"
    },
    "events": {
      "enabled": true,
      "eventCount": 12
    },
    "llm": {
      "enabled": true,
      "status": "ok",
      "model": "deepseek-chat"
    }
  }
}
```

## LLM Providers

CandleMind does not require a specific vendor. Any OpenAI-compatible chat completions endpoint can be used. If no real LLM key is configured, CandleMind falls back to a deterministic rule baseline.

DeepSeek:

```env
LLM_API_KEY=your_deepseek_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_NAME=deepseek-chat
LLM_SUPPORTS_JSON_MODE=true
```

OpenAI:

```env
LLM_API_KEY=your_openai_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
LLM_SUPPORTS_JSON_MODE=true
```

Qwen / Alibaba Cloud DashScope:

```env
LLM_API_KEY=your_dashscope_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus
LLM_SUPPORTS_JSON_MODE=true
```

Ollama local model:

```env
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=qwen2.5:14b
LLM_SUPPORTS_JSON_MODE=false
```

LM Studio local model:

```env
LLM_API_KEY=lm-studio
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL_NAME=local-model
LLM_SUPPORTS_JSON_MODE=false
```

Diagnostics:

```http
GET /api/config/llm
POST /api/config/check-llm
```

## Requirements

| Tool | Version |
| --- | --- |
| Node.js | 18+ |
| Python | >=3.11, <3.13 |
| uv | latest |

## Configuration

Copy the example env file:

```bash
cp .env.example .env
```

Example `.env`:

```env
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
LLM_SUPPORTS_JSON_MODE=true

ZEP_API_KEY=dummy

STOCK_PROPHECY_CACHE_TTL_SECONDS=600
STOCK_PROPHECY_ARCHIVE_DIR=./data/prophecies

FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=True

# Optional: use when frontend and backend are on different origins
# VITE_API_BASE_URL=http://localhost:5001
```

Notes:

- A real `LLM_API_KEY` is required for model-powered prophecy
- `ZEP_API_KEY` is a legacy compatibility startup setting; CandleMind can use `dummy`
- `.env` is ignored by git. Do not commit real secrets
- Prophecy archives are stored under `data/prophecies` by default. `data/` is ignored by git
- `VITE_API_BASE_URL` is optional. Leave it empty for Vite proxy/local same-origin development

## Install

```bash
npm run setup:all
```

Or install step by step:

```bash
npm run setup
npm run setup:backend
```

## Start

```bash
npm run dev
```

Services:

- Frontend: http://localhost:3000
- Backend: http://localhost:5001

Start separately:

```bash
npm run backend
npm run frontend
```

## API

Live prophecy:

```http
POST /api/stock/prophecy
```

Single-date backtest:

```http
POST /api/stock/prophecy/backtest
```

Batch backtest:

```http
POST /api/stock/prophecy/backtest/batch
```

Data source health:

```http
GET /api/config/data-sources/health?symbol=600519
```

Recent local prophecy archives:

```http
GET /api/stock/prophecies?limit=20
GET /api/stock/prophecies/{archiveId}
```

Example live request:

```json
{
  "symbol": "600519",
  "horizon": 5,
  "days": 180,
  "provider": "eastmoney",
  "includeEvents": true,
  "useLlm": true
}
```

Example single-date backtest request:

```json
{
  "symbol": "600519",
  "asOfDate": "2026-05-18",
  "horizon": 5,
  "days": 180,
  "provider": "eastmoney",
  "useLlm": false
}
```

Example batch backtest request:

```json
{
  "symbol": "600519",
  "horizon": 5,
  "days": 180,
  "provider": "eastmoney",
  "samples": 12,
  "step": 5,
  "useLlm": false
}
```

Each generated response includes `cache.hit`. Live prophecy responses also include local `archive.id` when archive saving succeeds.

## Privacy

CandleMind is self-hosted. API keys are read from your local `.env` or deployment environment. Stock code, K-line data, indicators, news and announcements are sent only to the LLM provider that you configure. Prophecy archives are saved locally under `data/prophecies` by default. The project itself does not collect telemetry.

## Test

```bash
cd backend && python -m pytest tests
```

Frontend build:

```bash
cd frontend && npm run build
```

## Disclaimer

CandleMind output is for research, learning and strategy review only. It may be affected by delayed data, missing events, API failures, model mistakes and unexpected market risks. It is not investment advice and should not be used as a trading basis.

## Acknowledgment

CandleMind is developed based on [666ghj/MiroFish](https://github.com/666ghj/MiroFish).
