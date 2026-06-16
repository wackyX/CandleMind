"""
Stock prophecy orchestration for the A-share MVP.

This module intentionally separates deterministic quantitative baselines from
the future MiroFish multi-agent adapter. The returned report shape is stable so
the UI can evolve while the real simulation backend is wired in.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime

from ..config import Config
from ..utils.llm_client import LLMClient
from .stock_events import load_recent_events
from .stock_indicators import build_indicator_series, historical_analogs, latest_snapshot
from .stock_market_data import Candle, get_symbol_name, load_candles_with_provider, normalize_symbol


@dataclass(frozen=True)
class ProphecyRequest:
    symbol: str
    horizon: int = 5
    days: int = 180
    provider: str = "eastmoney"
    include_events: bool = True
    use_llm: bool = True


def generate_stock_seed_report(
    symbol: str,
    candles: list[Candle],
    indicators: list[dict],
    horizon: int,
    events: dict | None = None,
) -> str:
    snapshot = latest_snapshot(candles, indicators)
    analog = historical_analogs(candles, horizon)
    trend = classify_trend(snapshot)
    risk = classify_risk(snapshot)
    analog_up = f"{analog['upProbability']}%" if analog["upProbability"] is not None else "样本不足"
    analog_return = f"{analog['avgForwardReturn']}%" if analog["avgForwardReturn"] is not None else "样本不足"
    event_signal = events.get("signal") if events else None
    event_lines = []
    if event_signal:
        event_lines.append(f"近期事件：{event_signal['label']}，事件分数 {event_signal['score']}。{event_signal['summary']}")
        for event in (events.get("events") or [])[:5]:
            event_lines.append(f"- [{event['type']}] {event['datetime']} {event['title']}（{event['sentiment']}，重要性 {event['importance']}）")
    else:
        event_lines.append("近期事件：未启用或未获取到。")

    return "\n".join(
        [
            f"股票：{get_symbol_name(symbol)}（{normalize_symbol(symbol)}）",
            "市场：A股，周期：日K",
            f"预测目标：未来 {horizon} 个交易日的方向概率、区间与失效条件",
            f"最新收盘：{snapshot['close']}，当日涨跌幅：{snapshot['changePct']}%",
            f"趋势状态：{trend}",
            f"量能状态：{snapshot['turnoverMood']}",
            f"关键价位：支撑 {snapshot['support']}，压力 {snapshot['resistance']}",
            f"RSI14：{snapshot['rsi14']}，ATR14：{snapshot['atr14']}",
            f"相似形态样本：{analog['sampleSize']}，上涨概率：{analog_up}，平均前瞻收益：{analog_return}",
            f"风险状态：{risk}",
            *event_lines,
            "说明：当前 MVP 使用技术面、历史相似形态、近期新闻公告事件构建种子报告；后续可将该报告交给 MiroFish 多智能体环境做情景推演。",
        ]
    )


def run_prophecy(request: ProphecyRequest) -> dict:
    symbol = normalize_symbol(request.symbol)
    horizon = max(1, min(int(request.horizon or 5), 20))
    candles, actual_provider = load_candles_with_provider(symbol, days=request.days, provider=request.provider)
    indicators = build_indicator_series(candles)
    snapshot = latest_snapshot(candles, indicators)
    analog = historical_analogs(candles, horizon)
    events = _safe_load_events(symbol) if request.include_events else None
    baseline_scores = score_scenarios(snapshot, analog, events)
    baseline_path = project_paths(candles[-1].close, snapshot, horizon, baseline_scores)
    baseline_forecast = build_forecast_candles(candles[-1].close, snapshot, baseline_path, baseline_scores)
    seed_report = generate_stock_seed_report(symbol, candles, indicators, horizon, events)
    llm_prophecy = (
        run_llm_prophecy(symbol, candles, indicators, snapshot, analog, events, baseline_scores, baseline_forecast, seed_report, horizon)
        if request.use_llm
        else {"enabled": False, "status": "disabled", "summary": "本次请求未启用 LLM 裁决。"}
    )
    scores = apply_llm_to_scenarios(baseline_scores, llm_prophecy)
    path = project_paths(candles[-1].close, snapshot, horizon, scores)
    forecast = build_llm_forecast(candles[-1].close, snapshot, horizon, scores, llm_prophecy) or baseline_forecast
    agents = agent_views(snapshot, analog, scores, events, llm_prophecy)

    return {
        "symbol": symbol,
        "name": get_symbol_name(symbol),
        "market": "A股",
        "period": "1d",
        "provider": actual_provider,
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "horizon": horizon,
        "candles": [item.to_dict() for item in candles],
        "indicators": indicators,
        "snapshot": snapshot,
        "analog": analog,
        "events": events,
        "scenarios": scores,
        "paths": path,
        "forecast": forecast,
        "baselineForecast": baseline_forecast,
        "llmProphecy": llm_prophecy,
        "seedReport": seed_report,
        "agents": agents,
        "disclaimer": "本功能仅用于研究与策略复盘，不构成投资建议。",
    }


def classify_trend(snapshot: dict) -> str:
    close = snapshot["close"]
    ma5 = snapshot["ma5"] or close
    ma20 = snapshot["ma20"] or close
    ma60 = snapshot["ma60"] or close
    if close > ma5 > ma20 > ma60:
        return "多头排列"
    if close < ma5 < ma20 < ma60:
        return "空头排列"
    if close > ma20 and ma20 >= ma60:
        return "中期偏强，短线观察"
    if close < ma20 and ma20 <= ma60:
        return "中期偏弱，等待修复"
    return "震荡均衡"


def classify_risk(snapshot: dict) -> str:
    rsi = snapshot["rsi14"] or 50
    change = snapshot["changePct"]
    if rsi > 72:
        return "短线过热，追高风险较高"
    if rsi < 28:
        return "短线超卖，反弹与继续杀跌并存"
    if abs(change) > 5:
        return "单日波动放大，需降低置信度"
    return "常规波动"


def score_scenarios(snapshot: dict, analog: dict, events: dict | None = None) -> list[dict]:
    close = snapshot["close"]
    ma5 = snapshot["ma5"] or close
    ma20 = snapshot["ma20"] or close
    ma60 = snapshot["ma60"] or close
    rsi = snapshot["rsi14"] or 50
    analog_up = analog["upProbability"] if analog["upProbability"] is not None else 50

    bull = 34
    bear = 28
    if close > ma20:
        bull += 8
        bear -= 4
    if ma20 > ma60:
        bull += 6
    if close < ma5:
        bull -= 4
        bear += 4
    if rsi > 65:
        bull -= 4
        bear += 3
    elif rsi < 38:
        bull += 4
        bear -= 2
    bull += (analog_up - 50) * 0.35
    bear += (50 - analog_up) * 0.25
    if snapshot["turnoverMood"] == "放量" and close > ma20:
        bull += 5
    if snapshot["turnoverMood"] == "缩量" and close < ma20:
        bear += 4
    event_score = (events or {}).get("signal", {}).get("score", 0)
    if event_score > 0:
        bull += min(8, event_score * 0.7)
        bear -= min(4, event_score * 0.25)
    elif event_score < 0:
        bear += min(8, abs(event_score) * 0.75)
        bull -= min(5, abs(event_score) * 0.35)

    bull = max(12, min(68, bull))
    bear = max(10, min(60, bear))
    neutral = max(12, 100 - bull - bear)
    total = bull + neutral + bear

    scenarios = [
        {
            "key": "bull",
            "name": "上行情景",
            "probability": round(bull / total * 100, 1),
            "trigger": f"放量站稳 {snapshot['resistance']} 上方",
            "description": "趋势延续，资金承接增强，价格尝试向上扩展波动区间。",
        },
        {
            "key": "neutral",
            "name": "震荡情景",
            "probability": round(neutral / total * 100, 1),
            "trigger": f"围绕 {snapshot['support']} - {snapshot['resistance']} 反复拉锯",
            "description": "方向信号不足，均线与量能需要继续消化。",
        },
        {
            "key": "bear",
            "name": "下行情景",
            "probability": round(bear / total * 100, 1),
            "trigger": f"有效跌破 {snapshot['support']}",
            "description": "支撑失守后风险偏好下降，回撤空间打开。",
        },
    ]
    return scenarios


def project_paths(close: float, snapshot: dict, horizon: int, scenarios: list[dict]) -> list[dict]:
    atr = snapshot["atr14"] or close * 0.025
    steps = list(range(1, horizon + 1))
    weights = {item["key"]: item["probability"] / 100 for item in scenarios}
    return [
        {
            "day": step,
            "bull": round(close + atr * (0.35 * step + 0.14 * step * weights["bull"]), 2),
            "neutral": round(close + atr * 0.08 * ((step % 2) * 2 - 1), 2),
            "bear": round(close - atr * (0.30 * step + 0.12 * step * weights["bear"]), 2),
        }
        for step in steps
    ]


def build_forecast_candles(close: float, snapshot: dict, paths: list[dict], scenarios: list[dict]) -> dict:
    primary = max(scenarios, key=lambda item: item["probability"])
    key = primary["key"]
    atr = snapshot["atr14"] or close * 0.025
    previous_close = close
    candles: list[dict] = []

    for item in paths:
        target_close = item[key]
        direction = 1 if target_close >= previous_close else -1
        body = abs(target_close - previous_close)
        min_wick = max(atr * 0.16, close * 0.0025)
        pattern = (item["day"] - 1) % 4

        if direction >= 0:
            upper_factor = [1.15, 0.55, 1.65, 0.8][pattern]
            lower_factor = [0.45, 0.9, 0.35, 0.75][pattern]
        else:
            upper_factor = [0.45, 0.95, 0.35, 0.75][pattern]
            lower_factor = [1.2, 0.55, 1.7, 0.85][pattern]

        upper_wick = max(min_wick, body * upper_factor)
        lower_wick = max(min_wick, body * lower_factor)
        high = max(previous_close, target_close) + upper_wick
        low = min(previous_close, target_close) - lower_wick

        candles.append(
            {
                "day": item["day"],
                "open": round(previous_close, 2),
                "high": round(high, 2),
                "low": round(max(0.01, low), 2),
                "close": round(target_close, 2),
                "direction": primary["key"],
                "scenario": primary["name"],
                "probability": primary["probability"],
            }
        )
        previous_close = target_close

    return {
        "direction": primary["key"],
        "scenario": primary["name"],
        "probability": primary["probability"],
        "candles": candles,
    }


def run_llm_prophecy(
    symbol: str,
    candles: list[Candle],
    indicators: list[dict],
    snapshot: dict,
    analog: dict,
    events: dict | None,
    scenarios: list[dict],
    baseline_forecast: dict,
    seed_report: str,
    horizon: int,
) -> dict:
    if not Config.LLM_API_KEY or Config.LLM_API_KEY.lower() in {"dummy", "your_api_key", "your_api_key_here"}:
        return {
            "enabled": False,
            "status": "missing_config",
            "summary": "LLM_API_KEY 未配置为真实密钥，本次使用规则基线推演。",
        }

    recent_candles = [item.to_dict() for item in candles[-30:]]
    recent_indicators = indicators[-30:]
    compact_events = []
    for event in (events or {}).get("events", [])[:10]:
        compact_events.append(
            {
                "type": event.get("type"),
                "datetime": event.get("datetime"),
                "title": event.get("title"),
                "summary": event.get("summary"),
                "sentiment": event.get("sentiment"),
                "importance": event.get("importance"),
                "source": event.get("source"),
            }
        )

    payload = {
        "symbol": normalize_symbol(symbol),
        "name": get_symbol_name(symbol),
        "market": "A股",
        "period": "日K",
        "horizon": horizon,
        "snapshot": snapshot,
        "analog": analog,
        "eventSignal": (events or {}).get("signal"),
        "events": compact_events,
        "baselineScenarios": scenarios,
        "baselineForecast": baseline_forecast,
        "recentCandles": recent_candles,
        "recentIndicators": recent_indicators,
        "seedReport": seed_report,
    }

    system_prompt = (
        "你是一个严谨的A股日K研究员。你只能基于用户给出的真实行情、技术指标、相似形态和新闻公告事件做研究推演，"
        "不能编造未提供的事实、内幕消息、实时资金流或确定性结论。你必须给出一个明确主方向，但要保留风险边界。"
        "输出必须是严格JSON对象，不要使用markdown。"
    )
    user_prompt = f"""
请综合下面的数据，给出未来 {horizon} 个交易日的单一路径预言。

要求：
1. direction 只能是 bull、bear、neutral 三选一。
2. probability 为 1-99 的数字，表示你对主方向的置信度，不要写百分号。
3. expectedReturnPct 是到预测窗口末尾的预期涨跌幅，bull 通常为正，bear 通常为负，neutral 应接近 0。
4. maxUpsidePct 和 maxDownsidePct 是预言窗口内可能出现的上冲和下探幅度，用于生成上下影线。
5. 每条 reasons、risks、invalidations 都必须来自给定数据的可解释推断，不要写空话。
6. agentDebate 给出 4 个智能体视角：TechnicalAnalystAgent、NewsEventAgent、QuantBacktestAgent、RiskAgent。

JSON schema:
{{
  "direction": "bull|bear|neutral",
  "probability": 0,
  "expectedReturnPct": 0,
  "maxUpsidePct": 0,
  "maxDownsidePct": 0,
  "scenarioName": "上行情景|下行情景|震荡情景",
  "summary": "一句话结论",
  "reasons": ["理由1", "理由2", "理由3"],
  "risks": ["风险1", "风险2"],
  "invalidations": ["失效条件1", "失效条件2"],
  "agentDebate": [
    {{"role": "TechnicalAnalystAgent", "stance": "观点", "message": "一句话"}},
    {{"role": "NewsEventAgent", "stance": "观点", "message": "一句话"}},
    {{"role": "QuantBacktestAgent", "stance": "观点", "message": "一句话"}},
    {{"role": "RiskAgent", "stance": "观点", "message": "一句话"}}
  ]
}}

数据：
{json.dumps(payload, ensure_ascii=False)}
"""

    try:
        client = LLMClient()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw_response = client.chat(
            messages,
            temperature=0.2,
            max_tokens=3600,
            response_format={"type": "json_object"},
        )
        data = parse_llm_prophecy_json(raw_response)
        if data is None:
            data = repair_llm_prophecy_json(client, raw_response)
        return normalize_llm_prophecy(data, snapshot, horizon)
    except Exception as exc:
        return {
            "enabled": True,
            "status": "failed",
            "summary": f"LLM 裁决失败，本次回退到规则基线：{exc}",
        }


def parse_llm_prophecy_json(raw_response: str) -> dict | None:
    cleaned = (raw_response or "").strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    candidates = [cleaned]
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    if first >= 0 and last > first:
        candidates.append(cleaned[first:last + 1])

    for candidate in candidates:
        try:
            data = json.loads(candidate)
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            continue
    return None


def repair_llm_prophecy_json(client: LLMClient, raw_response: str) -> dict:
    repair_prompt = f"""
下面是一段没有成功解析的JSON。请只返回一个完整、合法、可被 json.loads 解析的JSON对象。
不要添加markdown，不要解释。

必须包含字段：
direction, probability, expectedReturnPct, maxUpsidePct, maxDownsidePct, scenarioName, summary, reasons, risks, invalidations, agentDebate。

原始内容：
{raw_response[:4000]}
"""
    repaired = client.chat(
        [
            {"role": "system", "content": "你是JSON修复器，只输出合法JSON对象。"},
            {"role": "user", "content": repair_prompt},
        ],
        temperature=0,
        max_tokens=1800,
        response_format={"type": "json_object"},
    )
    data = parse_llm_prophecy_json(repaired)
    if data is None:
        raise ValueError(f"LLM返回的JSON修复失败: {repaired[:800]}")
    return data


def normalize_llm_prophecy(data: dict, snapshot: dict, horizon: int) -> dict:
    direction = str(data.get("direction", "")).strip().lower()
    if direction not in {"bull", "bear", "neutral"}:
        direction = "neutral"

    probability = clamp_float(data.get("probability"), 1, 99, 50)
    expected_return = clamp_float(data.get("expectedReturnPct"), -18, 18, 0)
    if direction == "bull" and expected_return < 0:
        expected_return = abs(expected_return)
    elif direction == "bear" and expected_return > 0:
        expected_return = -expected_return
    elif direction == "neutral":
        expected_return = clamp_float(expected_return, -4, 4, 0)

    atr_pct = ((snapshot.get("atr14") or 0) / max(snapshot.get("close") or 1, 0.01)) * 100
    default_upside = max(atr_pct * min(horizon, 8) * 0.34, abs(expected_return) * 0.55, 0.6)
    default_downside = max(atr_pct * min(horizon, 8) * 0.34, abs(expected_return) * 0.55, 0.6)

    scenario_name = str(data.get("scenarioName") or direction_name(direction))
    return {
        "enabled": True,
        "status": "ok",
        "direction": direction,
        "probability": round(probability, 1),
        "expectedReturnPct": round(expected_return, 2),
        "maxUpsidePct": round(clamp_float(abs_float(data.get("maxUpsidePct"), default_upside), 0.1, 24, default_upside), 2),
        "maxDownsidePct": round(clamp_float(abs_float(data.get("maxDownsidePct"), default_downside), 0.1, 24, default_downside), 2),
        "scenarioName": scenario_name,
        "summary": clean_text(data.get("summary"), "LLM 已给出主方向裁决。", 140),
        "reasons": clean_list(data.get("reasons"), 4),
        "risks": clean_list(data.get("risks"), 3),
        "invalidations": clean_list(data.get("invalidations"), 3),
        "agentDebate": normalize_agent_debate(data.get("agentDebate")),
    }


def apply_llm_to_scenarios(scenarios: list[dict], llm_prophecy: dict) -> list[dict]:
    if llm_prophecy.get("status") != "ok":
        return scenarios

    direction = llm_prophecy["direction"]
    probability = llm_prophecy["probability"]
    remaining = max(0.0, 100.0 - probability)
    opposite = {"bull": "bear", "bear": "bull", "neutral": "bear"}.get(direction, "bear")
    adjusted = []
    for item in scenarios:
        new_item = dict(item)
        if item["key"] == direction:
            new_item["probability"] = round(probability, 1)
            new_item["description"] = llm_prophecy.get("summary") or item["description"]
            if llm_prophecy.get("invalidations"):
                new_item["trigger"] = llm_prophecy["invalidations"][0]
        elif item["key"] == opposite:
            new_item["probability"] = round(remaining * 0.45, 1)
        else:
            new_item["probability"] = round(remaining * 0.55, 1)
        adjusted.append(new_item)

    total = sum(item["probability"] for item in adjusted) or 100
    for item in adjusted:
        item["probability"] = round(item["probability"] / total * 100, 1)
    return adjusted


def build_llm_forecast(close: float, snapshot: dict, horizon: int, scenarios: list[dict], llm_prophecy: dict) -> dict | None:
    if llm_prophecy.get("status") != "ok":
        return None

    direction = llm_prophecy["direction"]
    probability = llm_prophecy["probability"]
    expected_return = llm_prophecy["expectedReturnPct"] / 100
    target_close = close * (1 + expected_return)
    atr = snapshot["atr14"] or close * 0.025
    max_up = close * llm_prophecy["maxUpsidePct"] / 100
    max_down = close * llm_prophecy["maxDownsidePct"] / 100
    previous_close = close
    candles: list[dict] = []

    for day in range(1, horizon + 1):
        progress = day / horizon
        wave = math.sin(day * 1.37) * atr * 0.12
        target = close + (target_close - close) * (0.55 * progress + 0.45 * progress * progress) + wave
        if day == horizon:
            target = target_close
        body = abs(target - previous_close)
        min_wick = max(atr * 0.14, close * 0.0018)
        pattern = (day - 1) % 5
        upper = max(min_wick, max_up * [0.16, 0.28, 0.42, 0.22, 0.35][pattern])
        lower = max(min_wick, max_down * [0.22, 0.14, 0.36, 0.45, 0.18][pattern])
        if target >= previous_close:
            upper += body * [0.55, 0.25, 0.9, 0.35, 0.6][pattern]
            lower += body * [0.22, 0.58, 0.18, 0.45, 0.3][pattern]
        else:
            upper += body * [0.25, 0.62, 0.2, 0.48, 0.32][pattern]
            lower += body * [0.65, 0.25, 0.95, 0.38, 0.7][pattern]

        high = max(previous_close, target) + upper
        low = min(previous_close, target) - lower
        candles.append(
            {
                "day": day,
                "open": round(previous_close, 2),
                "high": round(high, 2),
                "low": round(max(0.01, low), 2),
                "close": round(target, 2),
                "direction": direction,
                "scenario": direction_name(direction),
                "probability": probability,
            }
        )
        previous_close = target

    return {
        "direction": direction,
        "scenario": direction_name(direction),
        "probability": probability,
        "expectedReturnPct": llm_prophecy["expectedReturnPct"],
        "candles": candles,
    }


def direction_name(direction: str) -> str:
    return {
        "bull": "上行情景",
        "bear": "下行情景",
        "neutral": "震荡情景",
    }.get(direction, "震荡情景")


def clamp_float(value, low: float, high: float, fallback: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = fallback
    if math.isnan(number) or math.isinf(number):
        number = fallback
    return max(low, min(high, number))


def abs_float(value, fallback: float) -> float:
    try:
        number = abs(float(value))
    except (TypeError, ValueError):
        number = fallback
    if math.isnan(number) or math.isinf(number):
        number = fallback
    return number


def clean_text(value, fallback: str, limit: int) -> str:
    text = str(value or "").strip()
    if not text:
        text = fallback
    return text[:limit]


def clean_list(value, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    output = []
    for item in value:
        text = clean_text(item, "", 120)
        if text:
            output.append(text)
        if len(output) >= limit:
            break
    return output


def normalize_agent_debate(value) -> list[dict]:
    if not isinstance(value, list):
        return []
    agents = []
    for item in value[:4]:
        if not isinstance(item, dict):
            continue
        agents.append(
            {
                "role": clean_text(item.get("role"), "LLMResearchAgent", 40),
                "stance": clean_text(item.get("stance"), "综合判断", 60),
                "message": clean_text(item.get("message"), "基于当前数据给出审慎推演。", 180),
            }
        )
    return agents


def agent_views(
    snapshot: dict,
    analog: dict,
    scenarios: list[dict],
    events: dict | None = None,
    llm_prophecy: dict | None = None,
) -> list[dict]:
    if llm_prophecy and llm_prophecy.get("status") == "ok" and llm_prophecy.get("agentDebate"):
        return llm_prophecy["agentDebate"]

    top = max(scenarios, key=lambda item: item["probability"])
    if analog["sampleSize"]:
        analog_message = f"样本数 {analog['sampleSize']}，未来窗口上涨概率 {analog['upProbability']}%，平均收益 {analog['avgForwardReturn']}%。"
    else:
        analog_message = "当前样本库内没有足够接近的历史形态，量化回测权重应降低。"
    event_signal = (events or {}).get("signal")
    if event_signal:
        event_message = f"{event_signal['summary']} 事件标签为“{event_signal['label']}”，已对情景概率做小幅修正。"
        event_stance = event_signal["label"]
    else:
        event_message = "未获取到近期事件，新闻公告因子暂不参与本次推演。"
        event_stance = "事件缺失"
    return [
        {
            "role": "TechnicalAnalystAgent",
            "stance": classify_trend(snapshot),
            "message": f"价格位于 MA20 {'上方' if snapshot['close'] > (snapshot['ma20'] or snapshot['close']) else '下方'}，RSI14 为 {snapshot['rsi14']}，当前更接近“{top['name']}”。",
        },
        {
            "role": "NewsEventAgent",
            "stance": event_stance,
            "message": event_message,
        },
        {
            "role": "QuantBacktestAgent",
            "stance": "历史相似形态",
            "message": analog_message,
        },
        {
            "role": "RiskAgent",
            "stance": classify_risk(snapshot),
            "message": f"核心失效线在 {snapshot['support']}，跌破后应降低多头情景权重；突破 {snapshot['resistance']} 才能提高进攻置信度。",
        },
    ]


def _safe_load_events(symbol: str) -> dict:
    try:
        return load_recent_events(symbol)
    except Exception as exc:
        return {
            "symbol": symbol,
            "name": get_symbol_name(symbol),
            "source": "eastmoney",
            "events": [],
            "signal": {
                "score": 0,
                "label": "事件获取失败",
                "summary": f"近期新闻公告拉取失败：{exc}",
                "positiveCount": 0,
                "negativeCount": 0,
                "importantCount": 0,
            },
        }
