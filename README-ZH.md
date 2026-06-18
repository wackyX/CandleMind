<div align="center">

<img src="./frontend/public/candlemind-logo.svg" alt="烛机 CandleMind" width="72%"/>

# 烛机 CandleMind

A 股 K 线 AI 预言终端

[English](./README.md) | 中文文档

</div>

## 项目简介

**烛机 CandleMind** 是一个面向 A 股日 K 的开源研究工作台。输入股票代码后，它会拉取真实 K 线、近期新闻公告、技术指标、历史相似形态，并可接入用户自己的 LLM，最终在真实 K 线后方生成一条明确的未来预言 K 线路径。

本项目用于研究、复盘、产品原型和开源实验，不构成任何投资建议。

## 完整功能

- **A 股代码输入**：输入 `600519` 这类 6 位 A 股代码即可推演
- **真实日 K 图表**：展示股票名称、代码、交易所、周期和真实 K 线
- **预言 K 线**：在真实 K 线后方补出单一路径预言 K 线
- **K 线动画**：预言区按交易日逐根渲染，支持上下影线、冲高回落和下探反弹效果
- **新闻公告事件**：可拉取东方财富近期新闻和公告
- **技术指标**：计算 MA、RSI、ATR、BOLL、支撑/压力和量能状态
- **历史相似形态**：用相似历史结构辅助判断方向概率
- **用户自带 LLM**：支持 DeepSeek、OpenAI、通义千问、Ollama、LM Studio 等 OpenAI-compatible 模型
- **推演证据链**：从技术结构、历史相似、事件驱动、模型裁决、风险边界五层解释预言结果
- **可信度雷达图**：展示技术、事件、模型、风险四类信号一致性
- **单点历史回测**：选择某个历史日期，只使用该日期之前的数据生成预言，并与之后真实 K 线对比
- **批量历史回测**：自动抽取多个历史切点，统计方向命中率、平均误差和样本表现
- **数据源健康检查**：检测行情、实时行情、新闻公告和 LLM 配置是否可用
- **数据源记录入报告**：每份报告记录实际行情源、是否兜底、最新 K 线日期、事件数量和 LLM 状态
- **本地档案和缓存**：保存本地推演档案，并对短时间内相同请求复用缓存
- **双主题 UI**：提供白昼和暗黑两种终端风格，整体避免大面积绿色元素

## 推演模式

### 实时预言

基于最新可用 A 股日 K 数据，生成未来若干交易日的单一路径预言 K 线。

典型请求：

```json
{
  "symbol": "600519",
  "horizon": 5,
  "days": 180,
  "includeEvents": true,
  "useLlm": true
}
```

### 单点历史回测

选择一个历史日期作为切点。系统只使用该日期之前可见的数据生成预言，再拿之后真实 K 线做对比。

回测模式下，主图历史 K 线会截止到回测日期，之后的真实 K 线只会作为对照显示在预言区。

### 批量历史回测

自动抽取多个历史切点并批量验证，输出：

- 方向命中率
- 平均命中分
- 平均绝对误差
- 平均收益误差
- 每个切点的预言收益与真实收益

前端会展示一个最近切点的参考 K 线图，方便观察具体预言形态。

## 可解释性

每份推演报告都会返回结构化 `explanation` 字段，并在前端展示“推演证据链”。

证据链包含五层：

- **技术结构**：均线排列、RSI、支撑压力、价格位置
- **历史相似**：相似样本数量、上涨概率、前瞻收益
- **事件驱动**：新闻公告事件分、事件数量和偏多/偏空影响
- **模型裁决**：LLM 输出的方向、概率、摘要和核心理由
- **风险边界**：ATR 波动、支撑压力距离、失效条件

每层都有分数、立场（支持 / 谨慎 / 反对）和具体依据点。报告也会给出“重新推演触发器”，例如跌破支撑、突破压力或模型给出的失效条件。

## 数据源

烛机当前只考虑 A 股市场。

行情数据流程：

1. 优先使用东方财富日 K
2. 东方财富日 K 不可用时，降级使用新浪历史 K 线
3. 东方财富实时行情可用时会合并最新交易日数据
4. Demo 数据保留给测试和离线 UI 场景

事件数据：

- 东方财富新闻搜索
- 东方财富公告
- 本地透明关键词事件打分

健康检查接口：

```http
GET /api/config/data-sources/health?symbol=600519
```

报告中的数据源记录示例：

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

## LLM Provider 配置

烛机不绑定特定模型厂商。只要支持 OpenAI-compatible chat completions 接口，就可以接入。未配置真实 LLM 时，会回退到规则基线推演。

DeepSeek：

```env
LLM_API_KEY=your_deepseek_key
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL_NAME=deepseek-chat
LLM_SUPPORTS_JSON_MODE=true
```

OpenAI：

```env
LLM_API_KEY=your_openai_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
LLM_SUPPORTS_JSON_MODE=true
```

通义千问 / 阿里百炼：

```env
LLM_API_KEY=your_dashscope_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus
LLM_SUPPORTS_JSON_MODE=true
```

Ollama 本地模型：

```env
LLM_API_KEY=ollama
LLM_BASE_URL=http://localhost:11434/v1
LLM_MODEL_NAME=qwen2.5:14b
LLM_SUPPORTS_JSON_MODE=false
```

LM Studio 本地模型：

```env
LLM_API_KEY=lm-studio
LLM_BASE_URL=http://localhost:1234/v1
LLM_MODEL_NAME=local-model
LLM_SUPPORTS_JSON_MODE=false
```

模型诊断接口：

```http
GET /api/config/llm
POST /api/config/check-llm
```

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

# 可选：当前端和后端部署在不同地址时使用
# VITE_API_BASE_URL=http://localhost:5001
```

说明：

- 需要真实 `LLM_API_KEY` 才能启用模型裁决
- `ZEP_API_KEY` 是历史兼容启动项，当前烛机功能可以先填 `dummy`
- `.env` 已被 `.gitignore` 忽略，不要提交真实密钥
- 推演档案默认保存在 `data/prophecies`，`data/` 已被 git 忽略
- `VITE_API_BASE_URL` 是可选项。本地 Vite 代理开发时可以留空

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

实时预言：

```http
POST /api/stock/prophecy
```

单点历史回测：

```http
POST /api/stock/prophecy/backtest
```

批量历史回测：

```http
POST /api/stock/prophecy/backtest/batch
```

数据源健康检查：

```http
GET /api/config/data-sources/health?symbol=600519
```

本地推演档案：

```http
GET /api/stock/prophecies?limit=20
GET /api/stock/prophecies/{archiveId}
```

实时预言请求示例：

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

单点回测请求示例：

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

批量回测请求示例：

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

生成结果会包含 `cache.hit`。实时预言在档案保存成功时还会包含本地 `archive.id`。

## 隐私说明

烛机是自托管开源项目。API Key 只从本地 `.env` 或部署环境变量读取。股票代码、K 线、指标、新闻和公告只会发送给你自己配置的 LLM Provider。推演档案默认保存在本地 `data/prophecies`。项目本身不采集遥测数据。

## 测试

```bash
cd backend && python -m pytest tests
```

前端构建：

```bash
cd frontend && npm run build
```

## 免责声明

烛机 CandleMind 输出内容仅用于研究、学习和策略复盘。模型推演可能受到数据延迟、接口失败、新闻缺失、模型误判和市场突发风险影响，不构成投资建议，也不应作为买卖依据。

## 致谢

烛机 CandleMind 基于 [666ghj/MiroFish](https://github.com/666ghj/MiroFish) 开发。
