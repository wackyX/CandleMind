"""
Local audit archive and short-lived cache for stock prophecies.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import threading
import time
from datetime import datetime
from typing import Any

from ..config import Config


_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, dict[str, Any]] = {}


def prophecy_cache_key(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def get_cached_prophecy(cache_key: str, ttl_seconds: int | None = None) -> dict[str, Any] | None:
    ttl = Config.STOCK_PROPHECY_CACHE_TTL_SECONDS if ttl_seconds is None else ttl_seconds
    if ttl <= 0:
        return None
    now = time.time()
    with _CACHE_LOCK:
        item = _CACHE.get(cache_key)
        if not item:
            return None
        if now - item["stored_at"] > ttl:
            _CACHE.pop(cache_key, None)
            return None
        result = copy.deepcopy(item["result"])
    result["cache"] = {
        "hit": True,
        "key": cache_key,
        "storedAt": datetime.fromtimestamp(item["stored_at"]).isoformat(timespec="seconds"),
        "ttlSeconds": ttl,
    }
    return result


def set_cached_prophecy(cache_key: str, result: dict[str, Any]) -> None:
    with _CACHE_LOCK:
        _CACHE[cache_key] = {
            "stored_at": time.time(),
            "result": copy.deepcopy(result),
        }


def archive_prophecy(
    request_payload: dict[str, Any],
    result: dict[str, Any],
    cache_key: str,
    llm_raw_response: str | None = None,
) -> str:
    archive_id = build_archive_id(result.get("symbol") or request_payload.get("symbol") or "unknown")
    archive_dir = Config.STOCK_PROPHECY_ARCHIVE_DIR
    os.makedirs(archive_dir, exist_ok=True)
    archive = {
        "archiveId": archive_id,
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "cacheKey": cache_key,
        "request": request_payload,
        "result": result,
        "llmRawResponse": llm_raw_response,
    }
    path = os.path.join(archive_dir, f"{archive_id}.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(archive, file, ensure_ascii=False, indent=2)
    return archive_id


def list_prophecy_archives(limit: int = 20) -> list[dict[str, Any]]:
    archive_dir = Config.STOCK_PROPHECY_ARCHIVE_DIR
    if not os.path.isdir(archive_dir):
        return []

    rows: list[dict[str, Any]] = []
    for filename in os.listdir(archive_dir):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(archive_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            result = data.get("result") or {}
            forecast = result.get("forecast") or {}
            rows.append(
                {
                    "archiveId": data.get("archiveId") or filename.removesuffix(".json"),
                    "createdAt": data.get("createdAt"),
                    "symbol": result.get("symbol"),
                    "name": result.get("name"),
                    "horizon": result.get("horizon"),
                    "direction": forecast.get("direction"),
                    "probability": forecast.get("probability"),
                    "provider": result.get("provider"),
                    "llmStatus": (result.get("llmProphecy") or {}).get("status"),
                }
            )
        except Exception:
            continue

    rows.sort(key=lambda item: item.get("createdAt") or "", reverse=True)
    return rows[: max(1, min(int(limit or 20), 100))]


def read_prophecy_archive(archive_id: str) -> dict[str, Any] | None:
    safe_id = "".join(ch for ch in archive_id if ch.isalnum() or ch in {"-", "_"})
    if not safe_id:
        return None
    path = os.path.join(Config.STOCK_PROPHECY_ARCHIVE_DIR, f"{safe_id}.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def build_archive_id(symbol: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    digest = hashlib.sha1(f"{symbol}-{timestamp}-{time.time_ns()}".encode("utf-8")).hexdigest()[:8]
    return f"{symbol}-{timestamp}-{digest}"
