"""
Health checks for A-share data sources used by CandleMind.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Callable

from .llm_diagnostics import llm_config_summary
from .stock_events import load_recent_events
from .stock_market_data import (
    load_candles_with_provider,
    load_eastmoney_candles,
    load_eastmoney_realtime_candle,
    normalize_symbol,
)


def check_stock_data_sources(symbol: str = "600519") -> dict:
    code = normalize_symbol(symbol or "600519")
    checks = [
        _timed_check("market_kline", "东方财富日K", lambda: _check_market_kline(code)),
        _timed_check("market_realtime", "东方财富实时行情", lambda: _check_market_realtime(code)),
        _timed_check("events", "东方财富新闻公告", lambda: _check_events(code)),
        _timed_check("llm", "LLM 推演配置", _check_llm),
    ]
    hard_checks = [item for item in checks if item["key"] not in {"llm", "market_realtime"}]
    if any(item["status"] == "error" for item in hard_checks):
        overall = "error"
    elif any(item["status"] in {"warning", "error"} for item in checks):
        overall = "warning"
    else:
        overall = "ok"
    return {
        "symbol": code,
        "status": overall,
        "checkedAt": datetime.now().isoformat(timespec="seconds"),
        "checks": checks,
    }


def _timed_check(key: str, name: str, fn: Callable[[], dict]) -> dict:
    started_at = time.perf_counter()
    try:
        result = fn()
        status = result.pop("status", "ok")
        message = result.pop("message", "数据源正常")
        return {
            "key": key,
            "name": name,
            "status": status,
            "message": message,
            "latencyMs": round((time.perf_counter() - started_at) * 1000),
            **result,
        }
    except Exception as exc:
        return {
            "key": key,
            "name": name,
            "status": "error",
            "message": str(exc),
            "latencyMs": round((time.perf_counter() - started_at) * 1000),
        }


def _check_market_kline(symbol: str) -> dict:
    try:
        candles = load_eastmoney_candles(symbol, days=80)
    except Exception as primary_exc:
        candles, provider = load_candles_with_provider(symbol, days=80, provider="eastmoney")
        latest = candles[-1] if candles else None
        if not latest:
            raise RuntimeError(f"东方财富日K异常，兜底源也没有返回数据：{primary_exc}") from primary_exc
        return {
            "status": "warning",
            "message": f"东方财富日K异常，已降级到 {provider}，最新交易日 {latest.date}",
            "latestAt": latest.date,
            "count": len(candles),
            "provider": provider,
        }
    latest = candles[-1] if candles else None
    if not latest:
        return {"status": "error", "message": "东方财富没有返回日K数据"}
    return {
        "status": "ok",
        "message": f"日K可用，最新交易日 {latest.date}",
        "latestAt": latest.date,
        "count": len(candles),
    }


def _check_market_realtime(symbol: str) -> dict:
    try:
        candle = load_eastmoney_realtime_candle(symbol)
    except Exception as exc:
        return {
            "status": "warning",
            "message": f"实时行情暂不可用，将使用日K收盘数据：{exc}",
        }
    if not candle:
        return {"status": "warning", "message": "实时行情暂未返回，将使用日K收盘数据"}
    return {
        "status": "ok",
        "message": f"实时行情可用，快照日期 {candle.date}",
        "latestAt": candle.date,
    }


def _check_events(symbol: str) -> dict:
    events = load_recent_events(symbol, limit=8)
    meta = events.get("meta") or {}
    event_count = len(events.get("events") or [])
    if event_count == 0:
        return {
            "status": "warning",
            "message": "新闻公告接口可访问，但没有匹配到近期事件",
            "count": 0,
            "latestAt": meta.get("latestNewsAt") or meta.get("latestAnnouncementAt"),
        }
    return {
        "status": "ok",
        "message": f"新闻公告可用，匹配 {event_count} 条事件",
        "count": event_count,
        "latestAt": meta.get("latestNewsAt") or meta.get("latestAnnouncementAt"),
    }


def _check_llm() -> dict:
    summary = llm_config_summary()
    if not summary["configured"]:
        return {
            "status": "warning",
            "message": "LLM 未配置，将回退到规则基线",
            "model": summary["model"],
            "baseUrl": summary["baseUrl"],
        }
    return {
        "status": "ok",
        "message": f"LLM 已配置：{summary['model']}",
        "model": summary["model"],
        "baseUrl": summary["baseUrl"],
    }
