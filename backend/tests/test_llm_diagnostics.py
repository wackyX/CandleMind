from app.config import Config
from app.services.llm_diagnostics import check_llm_connection, llm_config_summary


def test_llm_config_summary_hides_api_key(monkeypatch):
    monkeypatch.setattr(Config, "LLM_API_KEY", "sk-test-secret")
    monkeypatch.setattr(Config, "LLM_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setattr(Config, "LLM_MODEL_NAME", "example-model")
    monkeypatch.setattr(Config, "LLM_SUPPORTS_JSON_MODE", False)

    summary = llm_config_summary()

    assert summary["configured"] is True
    assert summary["apiKeySet"] is True
    assert "sk-test-secret" not in str(summary)
    assert summary["supportsJsonMode"] is False


def test_llm_check_missing_config_uses_baseline_message(monkeypatch):
    monkeypatch.setattr(Config, "LLM_API_KEY", "dummy")

    result = check_llm_connection()

    assert result["ok"] is False
    assert result["status"] == "missing_config"
    assert "规则基线" in result["message"]
