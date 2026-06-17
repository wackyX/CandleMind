<div align="center">

<img src="./frontend/public/candlemind-logo.svg" alt="CandleMind" width="72%"/>

# CandleMind

An AI candlestick prophecy terminal for China A-shares

English | [中文文档](./README-ZH.md)

</div>

## Overview

**CandleMind** is an open-source research workstation for China A-share daily candlesticks. Given a stock code, it pulls recent real K-line data, news and announcements, combines technical indicators, historical analogs and the user-provided LLM, then renders a single forecast candlestick path after the real chart.

This project is for research, review and product prototyping only. It is not investment advice.

## Features

- Query A-share daily K-line data, recent news and announcements by stock code
- Calculate MA, RSI, ATR, BOLL, support/resistance and historical analogs
- Use your own OpenAI-compatible LLM for direction judgment, reasoning and risk boundaries
- Append one explicit forecast candlestick path after the real K-line chart
- Show LLM judgment, agent summaries, event signal and Stock Seed Report
- Prefer Eastmoney data, with Sina historical K-line and Eastmoney realtime fallback
- Save local prophecy archives and reuse short-lived cached results for repeated requests

## Interaction Flow

1. Open the page and enter a stock code
2. Click “Start prophecy”
3. The loading view shows the current reasoning stage
4. The full terminal is rendered after the request completes

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
```

Notes:

- A real `LLM_API_KEY` is required for model-powered prophecy. Without it, CandleMind falls back to a rule baseline
- `ZEP_API_KEY` is a legacy compatibility startup setting; CandleMind can use `dummy` for now
- `.env` is ignored by git. Do not commit real secrets
- Prophecy archives are stored under `data/prophecies` by default. `data/` is ignored by git

## LLM Providers

CandleMind does not require a specific vendor. Any OpenAI-compatible chat completions endpoint can be used.

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

Check the current provider:

```http
GET /api/config/llm
POST /api/config/check-llm
```

The frontend entry screen also shows the current model and provides a model check button.

## Privacy

CandleMind is self-hosted. API keys are read from your local `.env` or deployment environment. Stock code, K-line data, indicators, news and announcements are sent only to the LLM provider that you configure. Prophecy archives are saved locally under `data/prophecies` by default. The project itself does not collect telemetry.

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

Stock prophecy endpoint:

```http
POST /api/stock/prophecy
```

Example request:

```json
{
  "symbol": "600519",
  "horizon": 5,
  "days": 180,
  "includeEvents": true,
  "useLlm": true
}
```

Recent local prophecy archives:

```http
GET /api/stock/prophecies?limit=20
GET /api/stock/prophecies/{archiveId}
```

Each generated response includes `archive.id` and `cache.hit`. A repeated identical request within `STOCK_PROPHECY_CACHE_TTL_SECONDS` returns from cache.

## Test

```bash
cd backend && python -m pytest tests
```

## Disclaimer

CandleMind output is for research, learning and strategy review only. It may be affected by delayed data, missing events, API failures, model mistakes and unexpected market risks. It is not investment advice and should not be used as a trading basis.

## Acknowledgment

CandleMind is developed based on [666ghj/MiroFish](https://github.com/666ghj/MiroFish).
