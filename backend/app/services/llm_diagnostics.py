"""
Diagnostics for user-provided OpenAI-compatible LLM providers.
"""

from __future__ import annotations

import json
import time
from typing import Any

from ..config import Config
from ..utils.llm_client import LLMClient


PLACEHOLDER_KEYS = {"", "dummy", "your_api_key", "your_api_key_here"}


def llm_config_summary() -> dict[str, Any]:
    api_key = (Config.LLM_API_KEY or "").strip()
    configured = bool(api_key) and api_key.lower() not in PLACEHOLDER_KEYS
    return {
        "configured": configured,
        "baseUrl": Config.LLM_BASE_URL,
        "model": Config.LLM_MODEL_NAME,
        "supportsJsonMode": Config.LLM_SUPPORTS_JSON_MODE,
        "apiKeySet": bool(api_key),
        "apiKeyLooksPlaceholder": bool(api_key) and api_key.lower() in PLACEHOLDER_KEYS,
    }


def check_llm_connection() -> dict[str, Any]:
    summary = llm_config_summary()
    if not summary["configured"]:
        return {
            **summary,
            "ok": False,
            "status": "missing_config",
            "message": "LLM_API_KEY 未配置为真实密钥，股票预言将使用规则基线推演。",
            "latencyMs": None,
            "jsonModeOk": None,
        }

    started = time.perf_counter()
    try:
        client = LLMClient()
        response = client.chat(
            [
                {"role": "system", "content": "你是连接检测器。只回答 OK。"},
                {"role": "user", "content": "请回答 OK"},
            ],
            temperature=0,
            max_tokens=16,
        )
        latency_ms = round((time.perf_counter() - started) * 1000)
        json_result = _check_json_mode(client) if Config.LLM_SUPPORTS_JSON_MODE else None
        return {
            **summary,
            "ok": True,
            "status": "ok",
            "message": "LLM 连接正常。",
            "latencyMs": latency_ms,
            "sample": response[:80],
            "jsonModeOk": json_result,
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - started) * 1000)
        return {
            **summary,
            "ok": False,
            "status": "failed",
            "message": str(exc),
            "latencyMs": latency_ms,
            "jsonModeOk": None,
        }


def _check_json_mode(client: LLMClient) -> bool:
    try:
        response = client.chat(
            [
                {"role": "system", "content": "你是 JSON 检测器，只输出合法 JSON。"},
                {"role": "user", "content": "返回 {\"ok\": true}"},
            ],
            temperature=0,
            max_tokens=64,
            response_format={"type": "json_object"},
        )
        data = json.loads(response)
        return data.get("ok") is True
    except Exception:
        return False
