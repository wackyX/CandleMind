<div align="center">

<img src="./frontend/public/candlemind-logo.svg" alt="CandleMind" width="72%"/>

# CandleMind

An AI candlestick prophecy terminal for China A-shares

English | [中文文档](./README-ZH.md)

</div>

## Overview

**CandleMind** is a research-oriented AI terminal for China A-share daily candlesticks. Given a stock code, it pulls recent real K-line data, news and announcements, combines technical indicators, historical analogs and DeepSeek reasoning, then renders a single forecast candlestick path after the real chart.

This project is for research, review and product prototyping only. It is not investment advice.

## Features

- Query A-share daily K-line data, recent news and announcements by stock code
- Calculate MA, RSI, ATR, BOLL, support/resistance and historical analogs
- Use DeepSeek V4 Pro for direction judgment, reasoning and risk boundaries
- Append one explicit forecast candlestick path after the real K-line chart
- Show LLM judgment, agent summaries, event signal and Stock Seed Report
- Prefer Eastmoney data, with Sina historical K-line and Eastmoney realtime fallback

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
LLM_API_KEY=your_deepseek_or_openai_compatible_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_NAME=deepseek-v4-pro

ZEP_API_KEY=dummy

FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=True
```

Notes:

- A real `LLM_API_KEY` is required for DeepSeek-powered prophecy
- `ZEP_API_KEY` is a legacy compatibility startup setting; CandleMind can use `dummy` for now
- `.env` is ignored by git. Do not commit real secrets

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

## Disclaimer

CandleMind output is for research, learning and strategy review only. It may be affected by delayed data, missing events, API failures, model mistakes and unexpected market risks. It is not investment advice and should not be used as a trading basis.

## Acknowledgment

CandleMind is developed based on [666ghj/MiroFish](https://github.com/666ghj/MiroFish).
