"""
Recent A-share news and announcement event provider.

The MVP uses public Eastmoney web endpoints and falls back gracefully when the
network or upstream schema is unavailable. Event scoring is deliberately simple
and transparent so it can later be replaced by an LLM or classifier.
"""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from datetime import datetime
from html import unescape

from .stock_market_data import get_symbol_name, normalize_symbol


REQUEST_TIMEOUT_SECONDS = 8

POSITIVE_KEYWORDS = [
    "增长",
    "增持",
    "回购",
    "中标",
    "盈利",
    "预增",
    "突破",
    "创新高",
    "分红",
    "扩产",
    "签约",
    "订单",
    "获批",
    "推荐",
    "买入",
    "上调",
    "目标价",
    "评级上调",
]

NEGATIVE_KEYWORDS = [
    "减持",
    "亏损",
    "下滑",
    "处罚",
    "立案",
    "问询",
    "风险",
    "诉讼",
    "退市",
    "预减",
    "暴跌",
    "债务",
    "违约",
    "卖出",
    "下调",
    "评级下调",
    "目标价下调",
]

IMPORTANT_KEYWORDS = [
    "公告",
    "业绩",
    "年报",
    "季报",
    "董事会",
    "股东",
    "分红",
    "回购",
    "增持",
    "减持",
    "重组",
    "并购",
    "监管",
]


def load_recent_events(symbol: str, limit: int = 18) -> dict:
    code = normalize_symbol(symbol)
    news = _fetch_eastmoney_news(code, limit=max(limit, 24))
    announcements = _fetch_eastmoney_announcements(code, limit=max(8, limit // 2))
    events = _dedupe_events(news + announcements)
    events.sort(key=lambda item: item.get("datetime") or "", reverse=True)
    events = events[:limit]
    signal = score_event_signal(events)
    meta = {
        "newsCount": len(news),
        "announcementCount": len(announcements),
        "latestNewsAt": _latest_datetime(news),
        "latestAnnouncementAt": _latest_datetime(announcements),
    }
    return {
        "symbol": code,
        "name": get_symbol_name(code),
        "source": "eastmoney",
        "events": events,
        "signal": signal,
        "meta": meta,
    }


def score_event_signal(events: list[dict]) -> dict:
    if not events:
        return {
            "score": 0,
            "label": "无近期事件",
            "summary": "未获取到可用于推演的近期新闻或公告。",
            "positiveCount": 0,
            "negativeCount": 0,
            "importantCount": 0,
        }

    score = 0
    positive_count = 0
    negative_count = 0
    important_count = 0

    for event in events:
        sentiment = event["sentiment"]
        importance = event["importance"]
        if sentiment == "positive":
            score += 1.5 * importance
            positive_count += 1
        elif sentiment == "negative":
            score -= 1.7 * importance
            negative_count += 1
        if importance >= 2:
            important_count += 1
        if event["type"] == "announcement":
            score += 0.2 if sentiment == "positive" else -0.2 if sentiment == "negative" else 0

    score = max(-12, min(12, round(score, 2)))
    if score >= 4:
        label = "事件偏多"
    elif score <= -4:
        label = "事件偏空"
    elif score > 0.8:
        label = "事件略偏多"
    elif score < -0.8:
        label = "事件略偏空"
    else:
        label = "事件中性"

    summary = f"近况事件共 {len(events)} 条，正面 {positive_count} 条，负面 {negative_count} 条，重点事件 {important_count} 条。"
    return {
        "score": score,
        "label": label,
        "summary": summary,
        "positiveCount": positive_count,
        "negativeCount": negative_count,
        "importantCount": important_count,
    }


def _fetch_eastmoney_news(symbol: str, limit: int) -> list[dict]:
    stock_name = get_symbol_name(symbol)
    keyword = stock_name if not stock_name.startswith("A股 ") else symbol
    payload = {
        "uid": "",
        "keyword": keyword,
        "type": ["cmsArticleWebOld"],
        "client": "web",
        "clientType": "web",
        "clientVersion": "curr",
        "param": {
            "cmsArticleWebOld": {
                "searchScope": "default",
                "sort": "default",
                "pageIndex": 1,
                "pageSize": limit,
                "preTag": "",
                "postTag": "",
            }
        },
    }
    url = "https://search-api-web.eastmoney.com/search/jsonp?cb=callback&param=" + urllib.parse.quote(
        json.dumps(payload, ensure_ascii=False)
    )
    data = _get_jsonp(url)
    rows = data.get("result", {}).get("cmsArticleWebOld", []) if isinstance(data, dict) else []
    events: list[dict] = []
    for row in rows:
        title = _clean_text(row.get("title", ""))
        content = _clean_text(row.get("content", ""))
        if not title:
            continue
        if not _is_relevant_news(symbol, stock_name, title, content):
            continue
        events.append(
            _build_event(
                event_type="news",
                title=title,
                content=content,
                occurred_at=row.get("date", ""),
                source=row.get("mediaName", "东方财富"),
                url=row.get("url", ""),
            )
        )
    return events


def _is_relevant_news(symbol: str, stock_name: str, title: str, content: str) -> bool:
    front_content = content[:240]
    if symbol in title or symbol in front_content:
        return True
    if not stock_name.startswith("A股 ") and (stock_name in title or stock_name in front_content):
        return True
    return False


def _fetch_eastmoney_announcements(symbol: str, limit: int) -> list[dict]:
    params = {
        "sr": "-1",
        "page_size": str(limit),
        "page_index": "1",
        "ann_type": "A",
        "client_source": "web",
        "f_node": "0",
        "s_node": "0",
        "stock_list": symbol,
    }
    url = "https://np-anotice-stock.eastmoney.com/api/security/ann?" + urllib.parse.urlencode(params)
    data = _get_json(url)
    rows = data.get("data", {}).get("list", []) if isinstance(data, dict) else []
    events: list[dict] = []
    for row in rows:
        title = _clean_text(row.get("title") or row.get("title_ch") or "")
        columns = "、".join(column.get("column_name", "") for column in row.get("columns", []))
        content = _clean_text(columns)
        if not title:
            continue
        events.append(
            _build_event(
                event_type="announcement",
                title=title,
                content=content,
                occurred_at=row.get("display_time") or row.get("notice_date") or "",
                source="东方财富公告",
                url=f"https://data.eastmoney.com/notices/detail/{symbol}/{row.get('art_code', '')}.html",
            )
        )
    return events


def _build_event(event_type: str, title: str, content: str, occurred_at: str, source: str, url: str) -> dict:
    sentiment = _classify_sentiment(f"{title} {content}")
    importance = _classify_importance(f"{title} {content}", event_type)
    return {
        "type": event_type,
        "title": title,
        "summary": content[:180],
        "datetime": _normalize_datetime(occurred_at),
        "source": source,
        "url": url,
        "sentiment": sentiment,
        "importance": importance,
    }


def _classify_sentiment(text: str) -> str:
    positive = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text)
    negative = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "neutral"


def _classify_importance(text: str, event_type: str) -> int:
    score = sum(1 for keyword in IMPORTANT_KEYWORDS if keyword in text)
    if event_type == "announcement":
        score += 1
    return max(1, min(3, score + 1))


def _dedupe_events(events: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for event in events:
        key = re.sub(r"\s+", "", event["title"])[:36]
        if key in seen:
            continue
        seen.add(key)
        result.append(event)
    return result


def _latest_datetime(events: list[dict]) -> str | None:
    values = [event.get("datetime") for event in events if event.get("datetime")]
    return max(values) if values else None


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8", "ignore"))


def _get_jsonp(url: str) -> dict:
    text = _read_text(url)
    match = re.search(r"^[^(]*\((.*)\)\s*$", text, flags=re.S)
    if not match:
        return {}
    return json.loads(match.group(1))


def _read_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", "ignore")


def _clean_text(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value or "")
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _normalize_datetime(value: str) -> str:
    text = (value or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S:%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S:%f"):
        try:
            return datetime.strptime(text, fmt).isoformat(timespec="minutes")
        except ValueError:
            pass
    if re.match(r"\d{4}-\d{2}-\d{2}", text):
        return text[:10]
    return text
