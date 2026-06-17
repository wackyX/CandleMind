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
from app.services.stock_prophecy import build_llm_forecast


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
