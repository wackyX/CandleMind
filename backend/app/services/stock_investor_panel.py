"""
UZI-Skill investor panel integration for CandleMind.

This module vendors and calls the original UZI investor evaluator. CandleMind
only supplies a feature bridge from its prophecy report to the UZI rule engine;
the investor roster, criteria, scoring thresholds, reality checks, and group
metadata come from `app/vendor/uzi/lib`.
"""

from __future__ import annotations

import sys
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import Config
from ..utils.llm_client import LLMClient


VENDOR_UZI_ROOT = Path(__file__).resolve().parents[1] / "vendor" / "uzi"
if str(VENDOR_UZI_ROOT) not in sys.path:
    sys.path.insert(0, str(VENDOR_UZI_ROOT))

from lib.investor_db import INVESTORS as UZI_INVESTORS  # type: ignore  # noqa: E402
from lib.investor_evaluator import evaluate as uzi_evaluate  # type: ignore  # noqa: E402


GROUP_LABELS = {
    "A": "经典价值派",
    "B": "成长投资派",
    "C": "宏观对冲派",
    "D": "技术趋势派",
    "E": "中国价投派",
    "F": "A股游资派",
    "G": "量化系统派",
    "H": "科技领袖派",
    "I": "AI卡位猎手",
}

SIGNAL_MAP = {
    "bullish": "bullish",
    "neutral": "neutral",
    "bearish": "bearish",
    "skip": "skip",
}

INVESTOR_ALIASES = {
    "buffett": "巴非特",
    "graham": "格雷厄木",
    "fisher": "费雪",
    "munger": "芒果",
    "templeton": "邓普盾",
    "klarman": "卡拉慢",
    "lynch": "林琪",
    "oneill": "欧七八",
    "thiel": "蒂尔零",
    "wood": "木头姐",
    "andreessen": "安德森",
    "gurley": "格礼",
    "naval": "纳瓦罗",
    "gerstner": "格斯特那",
    "chamath": "查马特",
    "soros": "索螺丝",
    "dalio": "达理奥",
    "marks": "马克思霍",
    "druck": "德鲁肯",
    "robertson": "罗伯虎",
    "burry": "伯利眼",
    "chanos": "查诺斯",
    "livermore": "利弗摩",
    "minervini": "米内维尼",
    "darvas": "达瓦箱",
    "gann": "江嗯",
    "duan": "段不平",
    "zhangkun": "张困",
    "zhushaoxing": "朱少星",
    "xiezhiyu": "谢治雨",
    "fengliu": "风柳",
    "dengxiaofeng": "邓晓风",
    "zhang_lei": "张雷",
    "zhang_mz": "章萌主",
    "sun_ge": "孙一哥",
    "zhao_lg": "赵二板",
    "fs_wyj": "佛山无影手",
    "yangjia": "炒股养娃",
    "chen_xq": "陈小旗",
    "hu_jl": "胡家楼",
    "fang_xx": "方新甲",
    "zuoshou": "作手新二",
    "xiao_ey": "小鳄鱼",
    "jiao_yy": "交易圆",
    "mao_lb": "毛老版",
    "xiao_xian": "消闲客",
    "lasa": "拉萨天囤",
    "chengdu": "成都邦",
    "sunan": "苏南邦",
    "ningbo_st": "宁波桑田",
    "liuyi_zl": "六一中鹿",
    "liu_sh": "流沙湖",
    "gu_bl": "古北鹿",
    "bj_cj": "北京炒夹",
    "wang_zr": "瑞鹤闲",
    "xin_dd": "鑫多哆",
    "simons": "西朦斯",
    "thorp": "索扑",
    "shaw": "大卫肖",
    "asness": "阿斯内斯",
    "jensen_huang": "黄夹克",
    "musk": "马火星",
    "altman": "奥特慢",
    "saylor": "塞乐",
    "serenity": "瑟仁宁",
}


def build_investor_panel(report: dict[str, Any]) -> dict[str, Any]:
    if not report:
        raise ValueError("缺少预言报告，无法召集评委")

    features = build_uzi_features(report)
    raw_results = [uzi_evaluate(item["id"], features) for item in _panel_roster()]
    investors = [_normalize_signal(item, raw) for item, raw in zip(_panel_roster(), raw_results)]
    active = [item for item in investors if item["signal"] != "skip"]

    signal_counts = Counter(item["signal"] for item in active)
    verdict_counts = Counter(item["verdict"] for item in active)
    avg_score = round(sum(item["score"] for item in active) / max(len(active), 1), 1)
    avg_confidence = round(sum(item["confidence"] for item in active) / max(len(active), 1), 1)
    bullish_pct = round(signal_counts.get("bullish", 0) / max(len(active), 1) * 100, 1)

    groups = _summarize_groups(investors)
    sorted_active = sorted(active, key=lambda item: item["score"], reverse=True)
    summary = _build_panel_summary(features, signal_counts, bullish_pct, avg_score)

    return {
        "mode": "uzi_original_rule_engine",
        "source": "Vendored UZI-Skill investor_db + investor_criteria + investor_evaluator",
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "symbol": report.get("symbol"),
        "name": report.get("name"),
        "total": len(investors),
        "active": len(active),
        "skipped": len(investors) - len(active),
        "panelConsensus": bullish_pct,
        "avgScore": avg_score,
        "avgConfidence": avg_confidence,
        "signalDistribution": {
            "bullish": signal_counts.get("bullish", 0),
            "neutral": signal_counts.get("neutral", 0),
            "bearish": signal_counts.get("bearish", 0),
        },
        "voteDistribution": dict(verdict_counts),
        "summary": summary,
        "features": _public_features(features),
        "groups": groups,
        "topBulls": sorted_active[:5],
        "topBears": list(reversed(sorted(active, key=lambda item: item["score"])[:5])),
        "investors": investors,
        "disclaimer": "本评委打分调用 UZI 原版规则引擎，但 CandleMind 当前只提供日K、事件、量价、风险与预言特征；缺失的财务估值维度不会伪造。",
    }


def build_deep_investor_commentary(report: dict[str, Any], panel: dict[str, Any] | None = None) -> dict[str, Any]:
    if not report:
        raise ValueError("缺少预言报告，无法生成深度评语")
    if not Config.LLM_API_KEY or Config.LLM_API_KEY.lower() in {"dummy", "your_api_key", "your_api_key_here"}:
        return {
            "enabled": False,
            "status": "missing_config",
            "summary": "LLM_API_KEY 未配置为真实密钥，无法生成深度评语。",
            "groups": [],
            "investors": [],
            "risks": [],
        }

    panel = panel or build_investor_panel(report)
    payload = _deep_commentary_payload(report, panel)
    system_prompt = (
        "你是 CandleMind 的A股研究评委主持人。你只基于用户提供的K线、事件、预言和UZI规则打分结果生成深度评语。"
        "不得改变已有分数、不得新增未提供事实、不得给出确定性投资建议。"
        "语言要像原 investor-panel skill：不同流派有不同口吻，但避免夸张表演。输出必须是严格JSON对象，不要markdown。"
    )
    user_prompt = f"""
请基于下面的规则打分结果，生成深度评语。重点是解释为什么这些评委给出这个方向，以及多空分歧来自哪里。

JSON schema:
{{
  "summary": "2-3句总评，点明方向、分歧和数据缺口",
  "hostVerdict": "主持人式一句话结论",
  "groups": [
    {{"group": "A", "label": "经典价值派", "stance": "偏多|偏空|分歧|未参与", "commentary": "该流派为什么这样看"}}
  ],
  "investors": [
    {{
      "investorId": "buffett",
      "name": "巴非特",
      "signal": "bullish|neutral|bearish",
      "commentary": "第一人称或贴近该人物语言风格的1-2句评语",
      "reasoning": "结合命中/失败规则的具体解释",
      "watch": "接下来最应该观察什么"
    }}
  ],
  "risks": ["风险提醒1", "风险提醒2"],
  "invalidations": ["打分失效条件1", "打分失效条件2"]
}}

要求：
1. investors 只写 payload.focusInvestors 中的人，不要扩展名单。
2. commentary 可以模仿风格，但不要直接长篇引用原话。
3. 对价值派必须明确提醒：CandleMind 当前缺少完整财务估值数据，不能把规则扣分解释成真实财务恶化。
4. 对游资派必须说明 skip/射程逻辑，不要强行让所有人表态。
5. 每条文字短而具体，不写空泛口号。

数据：
{json.dumps(payload, ensure_ascii=False)}
"""
    try:
        client = LLMClient()
        raw_response = client.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.45,
            max_tokens=4200,
            response_format={"type": "json_object"} if Config.LLM_SUPPORTS_JSON_MODE else None,
        )
        data = _parse_deep_commentary_json(raw_response)
        return _normalize_deep_commentary(data, panel, raw_response)
    except Exception as exc:
        return {
            "enabled": True,
            "status": "failed",
            "summary": f"深度评语生成失败：{exc}",
            "groups": [],
            "investors": [],
            "risks": [],
        }


def build_uzi_features(report: dict[str, Any]) -> dict[str, Any]:
    snapshot = report.get("snapshot") or {}
    forecast = report.get("forecast") or {}
    events = report.get("events") or {}
    analog = report.get("analog") or {}
    llm = report.get("llmProphecy") or {}
    risk = report.get("riskMonitor") or {}
    metrics = risk.get("metrics") or {}
    candles = report.get("candles") or []

    close = _num(snapshot.get("close"))
    ma5 = _num(snapshot.get("ma5"), close)
    ma20 = _num(snapshot.get("ma20"), close)
    ma60 = _num(snapshot.get("ma60"), close)
    rsi = _num(snapshot.get("rsi14"), 50)
    atr = _num(snapshot.get("atr14"))
    change_pct = _num(snapshot.get("changePct"))
    volume_ratio = _num(metrics.get("volumeRatio20"), 1)
    event_signal = events.get("signal") or {}
    event_score = _num(event_signal.get("score"))
    event_count = len(events.get("events") or [])
    up_probability = _num(analog.get("upProbability"), 50)
    avg_forward_return = _num(analog.get("avgForwardReturn"))
    forecast_direction = forecast.get("direction") or "neutral"
    forecast_probability = _num(forecast.get("probability"), 50)
    llm_direction = llm.get("direction") or forecast_direction
    llm_probability = _num(llm.get("probability"), forecast_probability)
    risk_score = _num(risk.get("score"), 45)

    high_60 = max((_num(item.get("high")) for item in candles[-60:]), default=close)
    high_20 = _num(snapshot.get("high20"), high_60)
    low_20 = _num(snapshot.get("low20"), close)
    pct_from_60d_high = (close / high_60 - 1) * 100 if high_60 else 0
    pct_from_year_high = pct_from_60d_high
    ma_bull_aligned = bool(close >= ma20 and ma5 >= ma20 and ma20 >= ma60)
    stage_num = 2 if ma_bull_aligned and close >= ma60 else 4 if close < ma20 and ma5 < ma20 else 1
    vol_amplified = volume_ratio >= 1.25
    rsi_overbought = rsi >= 72
    technical_bull = _technical_bull_score(close, ma5, ma20, ma60, rsi, change_pct, volume_ratio)
    forecast_bull = _direction_to_bull_score(forecast_direction, forecast_probability)
    llm_bull = _direction_to_bull_score(llm_direction, llm_probability)

    # CandleMind does not yet collect full financial statements. Keep these
    # conservative instead of inventing fundamentals.
    features: dict[str, Any] = {
        "ticker": report.get("symbol") or "",
        "name": report.get("name") or "",
        "market": "A",
        "country": "CN",
        "industry": _infer_industry(report),
        "rev": 0,
        "revenue_b": 0,
        "revenue_growth_latest": max(0, event_score * 2),
        "revenue_growth_3y_cagr": max(0, avg_forward_return * 4),
        "rev_growth_yoy": max(0, event_score * 2),
        "rev_growth_3y": max(0, avg_forward_return * 4),
        "rev_growth_3y_pct": max(0, avg_forward_return * 4),
        "net_profit_growth_latest": max(0, event_score * 2),
        "net_profit_growth_3y": max(0, avg_forward_return * 4),
        "roe": 0,
        "roe_latest": 0,
        "roe_5y_above_15": 0,
        "roe_5y_min": 0,
        "roic": 0,
        "net_margin": 0,
        "gross_margin": 0,
        "debt_ratio": 100,
        "current_ratio": 0,
        "fcf_positive": False,
        "fcf_margin": 0,
        "ocf_to_net_income_ratio": 0,
        "cash_to_marketcap_ratio": 0,
        "pe": 999,
        "pe_ttm": 999,
        "pb": 999,
        "ps": 999,
        "peg": 999,
        "ev_to_revenue": 999,
        "pe_x_pb": 999,
        "pe_quantile_5y": 100,
        "vs_peer_avg_pe": 0,
        "safety_margin": 0,
        "upside_to_target": max(0, forecast_bull - 50),
        "dividend_yield": 0,
        "consecutive_dividend_years": 0,
        "consecutive_profit_years": 0,
        "market_cap": 0,
        "market_cap_yi": 0,
        "moat_total": _clamp((event_score + max(0, avg_forward_return)) * 1.6, 0, 20),
        "moat_network": 0,
        "moat_scale": 0,
        "moat_intangible": 0,
        "governance_score": 50,
        "no_violations": True,
        "audit_qualified": False,
        "has_pledge_issue": False,
        "insider_selling_recent": False,
        "founder_active": False,
        "founder_ownership_pct": 0,
        "rd_intensity": 0,
        "industry_growth": event_score,
        "industry_growth_pct": max(0, event_score * 2),
        "industry_is_growing": event_score > 1 or forecast_bull > 58,
        "industry_in_decline": event_score < -1 or forecast_bull < 42,
        "industry_lifecycle": "事件驱动修复" if event_score > 0 else "震荡观察",
        "industry_rank": 50,
        "research_coverage": event_count,
        "buy_rating_pct": _clamp(50 + event_score * 4),
        "fund_manager_count": 0,
        "policy_supportive": event_score > 1,
        "macro_rate_easing": False,
        "has_positive_catalyst": event_score > 0 or forecast_bull > 58,
        "recent_events_count": event_count,
        "sentiment_heat": _clamp(50 + event_score * 4 + max(0, volume_ratio - 1) * 18),
        "retail_holding_pct": 0,
        "is_safe": risk_score < 68,
        "ceo_promotional_score": 0,
        "off_balance_debt_ratio": 0,
        "ai_chain_hit": _has_ai_event(events),
        "ai_chokepoint_score": 0,
        "ai_irreplaceable": False,
        "ai_smallcap": False,
        "tam_usd_bn": 0,
        "network_effect_score": 0,
        "vertical_integration_score": 0,
        "consensus_growth_to_2026": max(0, event_score * 2),
        "btc_holdings_b": 0,
        "capex_growth_yoy": 0,
        "ytd_return": _price_return(candles, 120),
        "max_drawdown_1y": _max_drawdown(candles[-250:]),
        "volatility_1y": _volatility(candles[-120:]),
        "price_above_ma200": close >= ma60,
        "pct_from_60d_high": pct_from_60d_high,
        "pct_from_year_high": pct_from_year_high,
        "ma_bull_aligned": ma_bull_aligned,
        "stage_num": stage_num,
        "rsi": rsi,
        "rsi_overbought": rsi_overbought,
        "vol_amplified": vol_amplified,
        "lhb_30d_count": 0,
        "matched_youzi": [],
        "has_limit_up_recent": _has_limit_like_move(candles),
        "is_sector_leader": event_score > 2 and volume_ratio > 1.1,
        "is_hottest_in_sector": event_score > 3 and volume_ratio > 1.3,
        "is_hot_theme": event_score > 1.5,
        "is_ai_theme": _has_ai_event(events),
        "is_first_or_second_board": False,
        "is_first_board": False,
        "is_continuous_limit_up": False,
        "is_accelerating": change_pct > 3 and volume_ratio > 1.5,
        "is_oversold": rsi < 32,
        "trend": "up" if technical_bull >= 58 else "down" if technical_bull < 42 else "flat",
        "sentiment_cycle": event_score > 0 and volume_ratio > 1.1,
        "short_term_only": True,
        "min_fundamental_score": 0,
        "min_turnover": 0,
        "max_institution_pct": 100,
        "technical_bull": technical_bull,
        "forecast_bull": forecast_bull,
        "llm_bull": llm_bull,
        "analog_bull": up_probability,
        "risk_score": risk_score,
        "risk_safety": 100 - risk_score,
        "volume_ratio_20": volume_ratio,
        "atr_pct": atr / close * 100 if close else 0,
        "support": _num(snapshot.get("support"), low_20),
        "resistance": _num(snapshot.get("resistance"), high_20),
    }
    return features


def _panel_roster() -> list[dict[str, Any]]:
    # UZI v3.9 has a 66th optional newcomer `ghzw`; keep it vendored but
    # disabled until CandleMind has a separate place for experimental judges.
    return [item for item in UZI_INVESTORS if item.get("id") != "ghzw"]


def _deep_commentary_payload(report: dict[str, Any], panel: dict[str, Any]) -> dict[str, Any]:
    forecast = report.get("forecast") or {}
    snapshot = report.get("snapshot") or {}
    events = report.get("events") or {}
    risk = report.get("riskMonitor") or {}
    llm = report.get("llmProphecy") or {}
    top_bulls = panel.get("topBulls") or []
    top_bears = panel.get("topBears") or []
    focus = _unique_investors([*top_bulls[:4], *top_bears[:4], *_notable_neutrals(panel)])
    return {
        "symbol": report.get("symbol"),
        "name": report.get("name"),
        "market": report.get("market") or "A股",
        "forecast": {
            "direction": forecast.get("direction"),
            "probability": forecast.get("probability"),
            "summary": forecast.get("summary"),
            "horizon": report.get("horizon"),
        },
        "snapshot": {
            "close": snapshot.get("close"),
            "changePct": snapshot.get("changePct"),
            "ma5": snapshot.get("ma5"),
            "ma20": snapshot.get("ma20"),
            "ma60": snapshot.get("ma60"),
            "rsi14": snapshot.get("rsi14"),
            "support": snapshot.get("support"),
            "resistance": snapshot.get("resistance"),
        },
        "events": {
            "signal": events.get("signal"),
            "items": [
                {
                    "datetime": item.get("datetime"),
                    "title": item.get("title"),
                    "sentiment": item.get("sentiment"),
                    "importance": item.get("importance"),
                }
                for item in (events.get("events") or [])[:6]
            ],
        },
        "risk": {
            "label": risk.get("label"),
            "score": risk.get("score"),
            "summary": risk.get("summary"),
            "alerts": [
                {
                    "name": item.get("name"),
                    "severity": item.get("severity"),
                    "evidence": item.get("evidence"),
                }
                for item in (risk.get("alerts") or [])[:4]
            ],
        },
        "llmProphecy": {
            "status": llm.get("status"),
            "direction": llm.get("direction"),
            "probability": llm.get("probability"),
            "summary": llm.get("summary"),
            "reasons": (llm.get("reasons") or [])[:3],
            "risks": (llm.get("risks") or [])[:2],
            "invalidations": (llm.get("invalidations") or [])[:2],
        },
        "panel": {
            "mode": panel.get("mode"),
            "total": panel.get("total"),
            "active": panel.get("active"),
            "skipped": panel.get("skipped"),
            "panelConsensus": panel.get("panelConsensus"),
            "avgScore": panel.get("avgScore"),
            "signalDistribution": panel.get("signalDistribution"),
            "summary": panel.get("summary"),
            "groups": panel.get("groups"),
        },
        "focusInvestors": [
            {
                "investorId": item.get("investorId"),
                "name": item.get("name"),
                "group": item.get("group"),
                "groupLabel": item.get("groupLabel"),
                "signal": item.get("signal"),
                "score": item.get("score"),
                "confidence": item.get("confidence"),
                "verdict": item.get("verdict"),
                "pass": (item.get("pass") or [])[:3],
                "fail": (item.get("fail") or [])[:3],
                "engine": item.get("engine"),
            }
            for item in focus[:8]
        ],
        "styleGuide": {
            "buffett": "化名巴非特：朴素、企业主思维、安全边际",
            "munger": "化名芒果：反过来想、毒舌、心理偏误",
            "soros": "化名索螺丝：反身性、不确定性、及时认错",
            "duan": "化名段不平：生意、人、价格、本分和平常心",
            "zhao_lg": "化名赵二板：题材、龙头、二板、短线故事",
            "zhang_mz": "化名章萌主：趋势、主流、龙头、格局和纪律",
            "chen_xq": "化名陈小旗：情绪、主线、反核、一线天",
            "simons": "化名西朦斯：模型、统计、不要人工覆盖",
        },
    }


def _unique_investors(investors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    rows = []
    for item in investors:
        investor_id = item.get("investorId")
        if not investor_id or investor_id in seen:
            continue
        seen.add(investor_id)
        rows.append(item)
    return rows


def _notable_neutrals(panel: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [item for item in (panel.get("investors") or []) if item.get("signal") == "neutral"],
        key=lambda item: item.get("confidence") or 0,
        reverse=True,
    )[:2]


def _parse_deep_commentary_json(raw_response: str) -> dict[str, Any]:
    cleaned = (raw_response or "").strip()
    cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    first = cleaned.find("{")
    last = cleaned.rfind("}")
    candidates = [cleaned]
    if first >= 0 and last > first:
        candidates.append(cleaned[first:last + 1])
    for candidate in candidates:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    raise ValueError(f"LLM返回的JSON格式无效: {cleaned[:800]}")


def _normalize_deep_commentary(data: dict[str, Any], panel: dict[str, Any], raw_response: str) -> dict[str, Any]:
    groups_by_id = {item.get("group"): item for item in (panel.get("groups") or [])}
    investors_by_id = {item.get("investorId"): item for item in (panel.get("investors") or [])}
    groups = []
    for item in data.get("groups") or []:
        group = str(item.get("group") or "")
        if group not in groups_by_id:
            continue
        base = groups_by_id[group]
        groups.append(
            {
                "group": group,
                "label": item.get("label") or base.get("label"),
                "stance": item.get("stance") or base.get("stance"),
                "commentary": _clean_alias_text(str(item.get("commentary") or ""))[:360],
            }
        )

    investors = []
    for item in data.get("investors") or []:
        investor_id = item.get("investorId") or item.get("investor_id")
        if investor_id not in investors_by_id:
            continue
        base = investors_by_id[investor_id]
        investors.append(
            {
                "investorId": investor_id,
                "name": _clean_alias_text(item.get("name") or base.get("name"), investor_id),
                "groupLabel": base.get("groupLabel"),
                "signal": base.get("signal"),
                "score": base.get("score"),
                "verdict": base.get("verdict"),
                "commentary": _clean_alias_text(str(item.get("commentary") or ""), investor_id)[:360],
                "reasoning": _clean_alias_text(str(item.get("reasoning") or ""), investor_id)[:420],
                "watch": _clean_alias_text(str(item.get("watch") or ""), investor_id)[:220],
            }
        )

    return {
        "enabled": True,
        "status": "ok",
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "model": Config.LLM_MODEL_NAME,
        "summary": _clean_alias_text(str(data.get("summary") or "深度评语已生成。"))[:700],
        "hostVerdict": _clean_alias_text(str(data.get("hostVerdict") or ""))[:240],
        "groups": groups[:9],
        "investors": investors[:8],
        "risks": [_clean_alias_text(str(item))[:240] for item in (data.get("risks") or [])[:4]],
        "invalidations": [_clean_alias_text(str(item))[:240] for item in (data.get("invalidations") or [])[:4]],
        "_rawResponse": raw_response,
    }



def _normalize_signal(investor: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    signal = SIGNAL_MAP.get(raw.get("signal"), "neutral")
    score = raw.get("score")
    if score is None or score < 0:
        score = 50
    verdict = _verdict_from_raw(signal, score, raw)
    pass_rules = [item.get("msg") or item.get("name") for item in (raw.get("pass_rules") or [])[:4]]
    fail_rules = [item.get("msg") or item.get("name") for item in (raw.get("fail_rules") or [])[:4]]
    return {
        "investorId": investor.get("id"),
        "name": _investor_alias(investor),
        "group": investor.get("group"),
        "groupLabel": GROUP_LABELS.get(investor.get("group"), investor.get("group")),
        "avatar": f"avatars/{investor.get('id')}.svg",
        "signal": signal,
        "confidence": raw.get("confidence", 0),
        "score": round(float(score), 1),
        "verdict": verdict,
        "reasoning": _clean_alias_text(raw.get("rationale") or raw.get("headline") or "原版规则引擎未给出详细理由。", investor.get("id")),
        "comment": _clean_alias_text(raw.get("headline") or "原版规则引擎给出中性观察。", investor.get("id")),
        "pass": [item for item in pass_rules if item],
        "fail": [item for item in fail_rules if item],
        "idealPrice": None,
        "period": raw.get("time_horizon") or _period_for(investor.get("group")),
        "positionSizing": raw.get("position_sizing"),
        "whatWouldChangeMind": raw.get("what_would_change_my_mind"),
        "engine": {
            "weightPass": raw.get("weight_pass", 0),
            "weightTotal": raw.get("weight_total", 0),
            "passCount": raw.get("pass_count", 0),
            "failCount": raw.get("fail_count", 0),
            "skipReason": raw.get("skip_reason"),
        },
    }


def _investor_alias(investor: dict[str, Any]) -> str:
    investor_id = investor.get("id")
    return INVESTOR_ALIASES.get(investor_id, investor.get("name") or investor_id or "匿名评委")


def _clean_alias_text(text: Any, investor_id: str | None = None) -> str:
    value = str(text or "")
    if investor_id and investor_id in INVESTOR_ALIASES:
        source = next((item.get("name") for item in UZI_INVESTORS if item.get("id") == investor_id), None)
        if source:
            value = value.replace(str(source), INVESTOR_ALIASES[investor_id])
    for item in UZI_INVESTORS:
        source = item.get("name")
        alias = INVESTOR_ALIASES.get(item.get("id"))
        if source and alias:
            value = value.replace(str(source), alias)
    return value


def _summarize_groups(investors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in investors:
        by_group[item["group"]].append(item)
    groups = []
    for group, rows in sorted(by_group.items()):
        active = [item for item in rows if item["signal"] != "skip"]
        counts = Counter(item["signal"] for item in active)
        groups.append(
            {
                "group": group,
                "label": GROUP_LABELS.get(group, group),
                "total": len(rows),
                "active": len(active),
                "bullish": counts.get("bullish", 0),
                "neutral": counts.get("neutral", 0),
                "bearish": counts.get("bearish", 0),
                "avgScore": round(sum(item["score"] for item in active) / max(len(active), 1), 1),
                "stance": _group_stance(counts, len(active)),
            }
        )
    return groups


def _build_panel_summary(features: dict[str, Any], counts: Counter, bullish_pct: float, avg_score: float) -> str:
    leader = "多头占优" if bullish_pct >= 50 else "空头占优" if counts.get("bearish", 0) > counts.get("bullish", 0) else "分歧明显"
    return (
        f"UZI 原版规则引擎会审显示 {leader}，多头占比 {bullish_pct:.1f}%，平均分 {avg_score:.1f}。"
        f"本次输入包含日K、量价、事件、风险与预言特征；财务估值维度缺失时按原版规则自然扣分。"
    )


def _public_features(features: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "ticker",
        "name",
        "market",
        "industry",
        "stage_num",
        "trend",
        "rsi",
        "ma_bull_aligned",
        "vol_amplified",
        "volume_ratio_20",
        "pct_from_60d_high",
        "has_positive_catalyst",
        "sentiment_heat",
        "is_safe",
        "technical_bull",
        "forecast_bull",
        "llm_bull",
        "analog_bull",
        "risk_safety",
    ]
    return {key: features.get(key) for key in keys}


def _group_stance(counts: Counter, total: int) -> str:
    if not total:
        return "未参与"
    if counts.get("bullish", 0) / total >= 0.5:
        return "偏多"
    if counts.get("bearish", 0) / total >= 0.5:
        return "偏空"
    return "分歧"


def _verdict_from_raw(signal: str, score: float, raw: dict[str, Any]) -> str:
    if signal == "skip":
        return "不适合"
    if signal == "bullish":
        return "强烈买入" if score >= 78 else "买入" if score >= 64 else "关注"
    if signal == "bearish":
        return "回避" if score < 30 else "不达标"
    return "观望" if raw.get("weight_total", 0) else "信息不足"


def _infer_industry(report: dict[str, Any]) -> str:
    text = " ".join(
        [
            str(report.get("name") or ""),
            str(report.get("seedReport") or ""),
            " ".join(str(item.get("title") or "") for item in ((report.get("events") or {}).get("events") or [])[:8]),
        ]
    )
    if any(word in text for word in ("白酒", "茅台", "五粮液", "消费")):
        return "消费 白酒 食品饮料"
    if any(word in text for word in ("AI", "人工智能", "算力", "芯片", "半导体")):
        return "AI 半导体 科技"
    if any(word in text for word in ("银行", "保险", "证券", "金融")):
        return "金融"
    if any(word in text for word in ("新能源", "锂电", "储能", "光伏", "汽车")):
        return "新能源 制造"
    return "A股日K事件驱动"


def _has_ai_event(events: dict[str, Any]) -> bool:
    text = " ".join(str(item.get("title") or "") + " " + str(item.get("summary") or "") for item in (events.get("events") or [])[:20])
    return any(word in text for word in ("AI", "人工智能", "算力", "芯片", "半导体", "光模块"))


def _technical_bull_score(close: float, ma5: float, ma20: float, ma60: float, rsi: float, change_pct: float, volume_ratio: float) -> float:
    score = 50
    score += 12 if close >= ma20 else -10
    score += 9 if ma5 >= ma20 else -6
    score += 8 if ma20 >= ma60 else -5
    score += 6 if 42 <= rsi <= 68 else -8 if rsi > 75 else -4 if rsi < 30 else 0
    score += max(-6, min(6, change_pct * 1.5))
    score += max(-4, min(8, (volume_ratio - 1) * 8))
    return _clamp(score)


def _direction_to_bull_score(direction: str, probability: float) -> float:
    probability = _clamp(probability, 0, 100)
    if direction == "bull":
        return 50 + probability * 0.48
    if direction == "bear":
        return 50 - probability * 0.48
    return 50


def _price_return(candles: list[dict[str, Any]], lookback: int) -> float:
    if len(candles) < 2:
        return 0
    start = candles[-min(len(candles), lookback)].get("close") or candles[0].get("close") or 0
    end = candles[-1].get("close") or 0
    return round((end / start - 1) * 100, 2) if start else 0


def _max_drawdown(candles: list[dict[str, Any]]) -> float:
    peak = 0.0
    max_dd = 0.0
    for item in candles:
        close = _num(item.get("close"))
        peak = max(peak, close)
        if peak:
            max_dd = min(max_dd, close / peak - 1)
    return round(abs(max_dd) * 100, 2)


def _volatility(candles: list[dict[str, Any]]) -> float:
    closes = [_num(item.get("close")) for item in candles if item.get("close")]
    if len(closes) < 3:
        return 0
    returns = [(closes[index] / closes[index - 1] - 1) * 100 for index in range(1, len(closes)) if closes[index - 1]]
    if not returns:
        return 0
    mean = sum(returns) / len(returns)
    variance = sum((item - mean) ** 2 for item in returns) / len(returns)
    return round(variance ** 0.5, 2)


def _has_limit_like_move(candles: list[dict[str, Any]]) -> bool:
    if len(candles) < 2:
        return False
    for index in range(max(1, len(candles) - 10), len(candles)):
        prev = _num(candles[index - 1].get("close"))
        close = _num(candles[index].get("close"))
        if prev and (close / prev - 1) * 100 >= 9.5:
            return True
    return False


def _period_for(group: str | None) -> str:
    return {
        "A": "3-5年",
        "B": "6-18个月",
        "C": "1-6个月",
        "D": "5-20个交易日",
        "E": "1-3年",
        "F": "1-5个交易日",
        "G": "20-60个交易日",
        "H": "1-3年",
        "I": "3-12个月",
    }.get(group or "", "--")


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, float(value)))
