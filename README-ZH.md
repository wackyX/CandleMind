<div align="center">

<img src="./frontend/public/candlemind-logo.svg" alt="烛机 CandleMind" width="72%"/>

# 烛机 CandleMind

A股K线AI预言终端

[English](./README.md) | 中文文档

</div>

## 项目简介

**烛机 CandleMind** 是一个面向 A 股日 K 的研究型 AI 预言终端。输入股票代码后，它会拉取近期真实 K 线、新闻和公告事件，结合技术指标、相似形态回测与 DeepSeek 裁决，生成未来若干交易日的单一路径预言 K 线。

当前项目仅用于研究、复盘和产品原型验证，不构成任何投资建议。

## 核心能力

- 输入 A 股代码，拉取真实日 K、近期新闻和公告事件
- 计算 MA、RSI、ATR、BOLL、支撑/压力与相似形态
- 使用 DeepSeek V4 Pro 参与主方向裁决、理由生成和风险边界判断
- 在真实 K 线后方补出单一路径预言 K 线，包括上下影线
- 展示 LLM 裁决层、Agent 摘要、事件信号和 Stock Seed Report
- 东方财富优先，必要时使用新浪历史行情和东方财富实时行情兜底
- 保存本地推演档案，并对短时间内的重复请求复用缓存结果

## 交互流程

1. 打开页面后先输入股票代码
2. 点击“开始预言”
3. 页面展示推演步骤：拉取行情、计算指标、抓取事件、请求 DeepSeek、生成预言 K 线
4. 请求完成后一次性渲染完整结果页

## 环境要求

| 工具 | 版本 |
| --- | --- |
| Node.js | 18+ |
| Python | >=3.11, <3.13 |
| uv | 最新版 |

## 配置

复制示例配置：

```bash
cp .env.example .env
```

`.env` 示例：

```env
LLM_API_KEY=你的DeepSeek或OpenAI兼容API Key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_NAME=deepseek-v4-pro

ZEP_API_KEY=dummy

STOCK_PROPHECY_CACHE_TTL_SECONDS=600
STOCK_PROPHECY_ARCHIVE_DIR=./data/prophecies

FLASK_HOST=0.0.0.0
FLASK_PORT=5001
FLASK_DEBUG=True
```

说明：

- 股票预言功能需要真实 `LLM_API_KEY` 才能启用 DeepSeek 裁决
- `ZEP_API_KEY` 是历史兼容启动项，当前烛机功能可以先填 `dummy`
- `.env` 已被 `.gitignore` 忽略，不要提交真实密钥
- 推演档案默认保存在 `data/prophecies`，`data/` 已被 git 忽略

## 安装

```bash
npm run setup:all
```

也可以分步安装：

```bash
npm run setup
npm run setup:backend
```

## 启动

```bash
npm run dev
```

服务地址：

- 前端：http://localhost:3000
- 后端：http://localhost:5001

单独启动：

```bash
npm run backend
npm run frontend
```

## API

股票预言接口：

```http
POST /api/stock/prophecy
```

请求示例：

```json
{
  "symbol": "600519",
  "horizon": 5,
  "days": 180,
  "includeEvents": true,
  "useLlm": true
}
```

本地推演档案接口：

```http
GET /api/stock/prophecies?limit=20
GET /api/stock/prophecies/{archiveId}
```

每次生成结果会带回 `archive.id` 和 `cache.hit`。相同请求在 `STOCK_PROPHECY_CACHE_TTL_SECONDS` 时间内会直接命中缓存。

## 测试

```bash
cd backend && python -m pytest tests
```

## 免责声明

烛机 CandleMind 输出内容仅用于研究、学习和策略复盘。模型推演可能存在数据延迟、接口失败、新闻缺失、模型误判和市场突发风险，不构成投资建议，也不应作为买卖依据。

## 致谢

烛机 CandleMind 基于 [666ghj/MiroFish](https://github.com/666ghj/MiroFish) 开发。
