import json

from app.config import Config
from app.services.stock_archive import (
    archive_prophecy,
    get_cached_prophecy,
    list_prophecy_archives,
    prophecy_cache_key,
    read_prophecy_archive,
    set_cached_prophecy,
)
from app.services.stock_investor_panel import build_deep_investor_commentary, build_investor_panel
from app.services.stock_market_data import Candle
from app.services.stock_prophecy import (
    build_data_sources_meta,
    build_llm_forecast,
    build_prophecy_explanation,
    build_risk_monitor,
    evaluate_backtest,
    summarize_batch_backtest,
)


def test_prophecy_cache_key_is_stable():
    left = {"symbol": "600519", "horizon": 5, "useLlm": True}
    right = {"useLlm": True, "horizon": 5, "symbol": "600519"}

    assert prophecy_cache_key(left) == prophecy_cache_key(right)


def test_cache_roundtrip_marks_cache_hit():
    cache_key = prophecy_cache_key({"symbol": "600519"})
    result = {"symbol": "600519", "forecast": {"direction": "bull"}}

    set_cached_prophecy(cache_key, result)
    cached = get_cached_prophecy(cache_key, ttl_seconds=60)

    assert cached["symbol"] == "600519"
    assert cached["cache"]["hit"] is True
    assert cached["cache"]["key"] == cache_key


def test_archive_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(Config, "STOCK_PROPHECY_ARCHIVE_DIR", str(tmp_path))
    request_payload = {"symbol": "600519", "horizon": 5}
    result = {
        "symbol": "600519",
        "name": "贵州茅台",
        "horizon": 5,
        "provider": "eastmoney",
        "forecast": {"direction": "bear", "probability": 62},
        "llmProphecy": {"status": "ok"},
    }

    archive_id = archive_prophecy(request_payload, result, "cache-key", llm_raw_response='{"direction":"bear"}')
    archive = read_prophecy_archive(archive_id)
    rows = list_prophecy_archives()

    assert archive["archiveId"] == archive_id
    assert archive["request"] == request_payload
    assert json.loads(archive["llmRawResponse"])["direction"] == "bear"
    assert rows[0]["archiveId"] == archive_id
    assert rows[0]["llmStatus"] == "ok"


def test_llm_forecast_candle_bounds_are_valid():
    snapshot = {"close": 100, "atr14": 2.5}
    scenarios = [{"key": "bull", "probability": 67}]
    llm_prophecy = {
        "status": "ok",
        "direction": "bull",
        "probability": 67,
        "expectedReturnPct": 3.2,
        "maxUpsidePct": 5.4,
        "maxDownsidePct": 2.2,
    }

    forecast = build_llm_forecast(100, snapshot, 5, scenarios, llm_prophecy)

    assert forecast["candles"]
    for candle in forecast["candles"]:
        assert candle["high"] >= max(candle["open"], candle["close"])
        assert candle["low"] <= min(candle["open"], candle["close"])
        assert candle["low"] > 0


def test_backtest_evaluation_compares_forecast_with_actual_candles():
    base = Candle(date="2026-05-01", open=99, high=101, low=98, close=100, volume=1000)
    actual = [
        Candle(date="2026-05-04", open=100, high=104, low=99, close=103, volume=1200),
        Candle(date="2026-05-05", open=103, high=106, low=102, close=105, volume=1300),
    ]
    forecast = {
        "direction": "bull",
        "candles": [
            {"day": 1, "open": 100, "high": 103, "low": 99, "close": 102},
            {"day": 2, "open": 102, "high": 106, "low": 101, "close": 104},
        ],
    }

    result = evaluate_backtest(forecast, base, actual)

    assert result["directionHit"] is True
    assert result["predictedReturnPct"] == 4.0
    assert result["actualReturnPct"] == 5.0
    assert result["rows"][1]["errorPct"] == -0.95


def test_batch_backtest_summary_aggregates_runs():
    runs = [
        {"directionHit": True, "hitScore": 82, "avgAbsErrorPct": 1.2, "returnErrorPct": -0.5},
        {"directionHit": False, "hitScore": 48, "avgAbsErrorPct": 3.0, "returnErrorPct": 2.0},
        {"directionHit": True, "hitScore": 76, "avgAbsErrorPct": 1.8, "returnErrorPct": 0.7},
    ]

    result = summarize_batch_backtest(runs)

    assert result["sampleCount"] == 3
    assert result["directionHits"] == 2
    assert result["directionHitRate"] == 66.67
    assert result["bestRun"]["hitScore"] == 82
    assert result["worstRun"]["hitScore"] == 48


def test_data_source_meta_records_provider_without_leaking_key(monkeypatch):
    monkeypatch.setattr(Config, "LLM_API_KEY", "sk-test-secret")
    candles = [
        Candle(date="2026-05-01", open=1, high=2, low=1, close=2, volume=100),
        Candle(date="2026-05-02", open=2, high=3, low=2, close=3, volume=110),
    ]

    result = build_data_sources_meta(
        provider="sina",
        requested_provider="eastmoney",
        candles=candles,
        events={"source": "eastmoney", "events": [{"title": "公告"}], "meta": {"latestNewsAt": "2026-05-02T09:00"}},
        use_llm=True,
    )

    assert result["market"]["fallbackUsed"] is True
    assert result["market"]["latestCandleDate"] == "2026-05-02"
    assert result["events"]["eventCount"] == 1
    assert result["llm"]["status"] == "ok"
    assert "sk-test-secret" not in str(result)


def test_prophecy_explanation_has_structured_layers():
    snapshot = {
        "close": 100,
        "ma5": 102,
        "ma20": 98,
        "ma60": 95,
        "rsi14": 56,
        "atr14": 2,
        "support": 96,
        "resistance": 106,
    }
    analog = {"upProbability": 62, "avgForwardReturn": 1.8, "sampleSize": 24}
    events = {
        "signal": {"score": 2, "summary": "近期事件略偏多。"},
        "events": [{"title": "回购公告"}],
    }
    scenarios = [{"key": "bull", "probability": 64}, {"key": "neutral", "probability": 22}, {"key": "bear", "probability": 14}]
    forecast = {"direction": "bull", "probability": 64}
    llm = {"status": "ok", "probability": 66, "summary": "模型支持偏多。", "reasons": ["均线支撑", "事件偏多"]}

    result = build_prophecy_explanation(snapshot, analog, events, scenarios, forecast, llm)

    assert result["direction"] == "bull"
    assert result["layers"]
    assert {item["key"] for item in result["layers"]} == {"technical", "analog", "events", "model", "risk"}
    assert result["score"] > 0


def test_risk_monitor_detects_high_upper_wick_and_volume_stall():
    candles = [
        Candle(date=f"2026-05-{index + 1:02d}", open=106, high=108, low=105, close=107, volume=1000)
        for index in range(20)
    ]
    candles.append(Candle(date="2026-05-22", open=108, high=112, low=107, close=108, volume=2600))
    indicators = [{"date": item.date, "ma20": 100, "rsi14": 68, "atr14": 3} for item in candles]
    snapshot = {
        "close": 108,
        "changePct": 0.93,
        "support": 103,
        "resistance": 112,
        "high20": 112,
        "ma20": 100,
        "rsi14": 68,
        "atr14": 3,
    }

    result = build_risk_monitor(candles, indicators, snapshot, events=None)
    keys = {item["key"] for item in result["alerts"]}

    assert result["level"] in {"medium", "high"}
    assert "high_upper_wick" in keys
    assert "volume_no_price" in keys


def test_investor_panel_builds_original_uzi_vote():
    report = {
        "symbol": "600519",
        "name": "贵州茅台",
        "snapshot": {
            "close": 1200,
            "changePct": 1.2,
            "ma5": 1190,
            "ma20": 1160,
            "ma60": 1120,
            "rsi14": 58,
        },
        "forecast": {"direction": "bull", "probability": 66},
        "events": {"signal": {"score": 2.5}, "events": [{"title": "回购公告"}]},
        "analog": {"upProbability": 61, "sampleSize": 24},
        "llmProphecy": {"status": "ok", "direction": "bull", "probability": 68},
        "riskMonitor": {
            "level": "medium",
            "score": 42,
            "metrics": {"volumeRatio20": 1.35},
        },
        "dataSources": {"market": {"latestCandleDate": "2026-06-18"}},
    }

    result = build_investor_panel(report)

    assert result["total"] == 65
    assert 0 < result["active"] <= 65
    assert result["skipped"] == result["total"] - result["active"]
    assert len(result["investors"]) == 65
    assert {item["group"] for item in result["groups"]} == set("ABCDEFGHI")
    assert sum(result["signalDistribution"].values()) == result["active"]
    assert result["mode"] == "uzi_original_rule_engine"
    assert all("engine" in item for item in result["investors"])


def test_deep_investor_commentary_handles_missing_llm(monkeypatch):
    monkeypatch.setattr(Config, "LLM_API_KEY", "dummy")
    report = {
        "symbol": "600519",
        "name": "贵州茅台",
        "snapshot": {"close": 1200, "ma5": 1190, "ma20": 1160, "ma60": 1120, "rsi14": 58},
        "forecast": {"direction": "bull", "probability": 66},
        "events": {"signal": {"score": 2.5}, "events": []},
        "analog": {"upProbability": 61},
        "riskMonitor": {"score": 42, "metrics": {"volumeRatio20": 1.35}},
    }
    panel = build_investor_panel(report)

    result = build_deep_investor_commentary(report, panel)

    assert result["status"] == "missing_config"
    assert result["enabled"] is False
