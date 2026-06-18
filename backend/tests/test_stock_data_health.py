from app.config import Config
from app.services import stock_data_health
from app.services.stock_market_data import Candle


def test_stock_data_health_aggregates_warning_without_leaking_key(monkeypatch):
    monkeypatch.setattr(
        stock_data_health,
        "load_eastmoney_candles",
        lambda symbol, days: [
            Candle(date="2026-05-18", open=1, high=2, low=1, close=2, volume=100)
        ],
        raising=False,
    )
    monkeypatch.setattr(stock_data_health, "load_eastmoney_realtime_candle", lambda symbol: None)
    monkeypatch.setattr(
        stock_data_health,
        "load_recent_events",
        lambda symbol, limit: {"events": [], "meta": {"latestNewsAt": None, "latestAnnouncementAt": None}},
    )
    monkeypatch.setattr(Config, "LLM_API_KEY", "sk-test-secret")
    monkeypatch.setattr(Config, "LLM_MODEL_NAME", "test-model")

    result = stock_data_health.check_stock_data_sources("600519")

    assert result["status"] == "warning"
    assert result["checks"][0]["status"] == "ok"
    assert "sk-test-secret" not in str(result)
