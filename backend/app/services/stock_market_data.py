"""
A-share market data providers for the KLine Prophecy MVP.

The default provider uses Eastmoney public K-line endpoints. The deterministic
demo provider remains available for offline UI work and tests.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import subprocess
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from typing import Iterable


@dataclass(frozen=True)
class Candle:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> dict:
        return asdict(self)


A_SHARE_SYMBOLS = {
    "000001": "平安银行",
    "000002": "万科A",
    "000333": "美的集团",
    "000651": "格力电器",
    "000858": "五粮液",
    "002415": "海康威视",
    "002594": "比亚迪",
    "300059": "东方财富",
    "300750": "宁德时代",
    "600000": "浦发银行",
    "600030": "中信证券",
    "600036": "招商银行",
    "600519": "贵州茅台",
    "600887": "伊利股份",
    "601318": "中国平安",
    "601398": "工商银行",
    "601857": "中国石油",
    "603259": "药明康德",
    "688981": "中芯国际",
}


def normalize_symbol(symbol: str) -> str:
    code = "".join(ch for ch in (symbol or "") if ch.isdigit())
    if len(code) != 6:
        raise ValueError("A股代码需要是 6 位数字，例如 600519")
    return code


def get_symbol_name(symbol: str) -> str:
    return A_SHARE_SYMBOLS.get(normalize_symbol(symbol), f"A股 {normalize_symbol(symbol)}")


def search_symbols(keyword: str = "") -> list[dict]:
    query = (keyword or "").strip().lower()
    rows = [
        {"symbol": symbol, "name": name, "market": _market_for_symbol(symbol)}
        for symbol, name in A_SHARE_SYMBOLS.items()
    ]
    if not query:
        return rows
    return [
        row
        for row in rows
        if query in row["symbol"].lower() or query in row["name"].lower()
    ]


def _market_for_symbol(symbol: str) -> str:
    if symbol.startswith(("60", "68")):
        return "SH"
    return "SZ"


def _eastmoney_market_id(symbol: str) -> int:
    return 1 if _market_for_symbol(symbol) == "SH" else 0


def _eastmoney_secid(symbol: str) -> str:
    return f"{_eastmoney_market_id(symbol)}.{normalize_symbol(symbol)}"


def _trading_days(count: int, end: date | None = None) -> Iterable[date]:
    day = end or date.today()
    days: list[date] = []
    while len(days) < count:
        if day.weekday() < 5:
            days.append(day)
        day -= timedelta(days=1)
    return reversed(days)


def _symbol_seed(symbol: str) -> int:
    digest = hashlib.sha256(symbol.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def generate_demo_candles(symbol: str, days: int = 180) -> list[Candle]:
    """
    Generate deterministic, market-like daily candles.

    This is not real market data. It is intentionally stable for demos,
    UI work, and regression tests until a licensed A-share provider is wired in.
    """
    code = normalize_symbol(symbol)
    days = max(60, min(int(days or 180), 360))
    seed = _symbol_seed(code)
    rng = random.Random(seed)

    base = 8 + (seed % 12000) / 180
    trend = rng.uniform(-0.0009, 0.0015)
    cycle_speed = rng.uniform(0.09, 0.17)
    cycle_width = rng.uniform(0.010, 0.028)
    volatility = rng.uniform(0.012, 0.032)
    close = base
    candles: list[Candle] = []

    for index, day in enumerate(_trading_days(days)):
        cycle = math.sin(index * cycle_speed + (seed % 17)) * cycle_width
        shock = rng.gauss(0, volatility)
        if index % 43 == 0 and index > 0:
            shock += rng.choice([-1, 1]) * rng.uniform(0.015, 0.035)

        prev_close = close
        close = max(1.0, prev_close * (1 + trend + cycle + shock))
        open_price = max(1.0, prev_close * (1 + rng.gauss(0, volatility / 2)))
        high = max(open_price, close) * (1 + abs(rng.gauss(0.006, volatility / 3)))
        low = min(open_price, close) * (1 - abs(rng.gauss(0.006, volatility / 3)))
        volume_base = 1_200_000 + (seed % 9_000_000)
        volume_wave = 1 + abs(shock) * 12 + max(cycle, 0) * 9
        volume = int(volume_base * volume_wave * rng.uniform(0.75, 1.35))

        candles.append(
            Candle(
                date=day.isoformat(),
                open=round(open_price, 2),
                high=round(high, 2),
                low=round(max(0.1, low), 2),
                close=round(close, 2),
                volume=volume,
            )
        )

    return candles


def load_eastmoney_candles(symbol: str, days: int = 180) -> list[Candle]:
    code = normalize_symbol(symbol)
    days = max(60, min(int(days or 180), 500))
    params = {
        "secid": _eastmoney_secid(code),
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "klt": "101",
        "fqt": "1",
        "end": "20500101",
        "lmt": str(days),
    }
    query = urllib.parse.urlencode(params, safe=",")
    hosts = [
        "26.push2his.eastmoney.com",
        "28.push2his.eastmoney.com",
        "7.push2his.eastmoney.com",
        "17.push2his.eastmoney.com",
        "push2his.eastmoney.com",
    ]
    errors: list[str] = []
    for host in hosts:
        url = f"https://{host}/api/qt/stock/kline/get?{query}"
        try:
            payload = _read_eastmoney_json(url, code)
            candles = _parse_eastmoney_klines(payload)
            if candles:
                return candles
        except Exception as exc:
            errors.append(f"{host}: {exc}")
            time.sleep(0.15)
    raise RuntimeError("东方财富K线接口拉取失败：" + " | ".join(errors[-3:]))


def load_eastmoney_realtime_candle(symbol: str) -> Candle | None:
    code = normalize_symbol(symbol)
    params = {
        "secid": _eastmoney_secid(code),
        "fields": "f43,f44,f45,f46,f47,f57,f58,f86",
    }
    query = urllib.parse.urlencode(params, safe=",")
    url = f"https://push2.eastmoney.com/api/qt/stock/get?{query}"
    payload = _read_eastmoney_json(url, code)
    data = payload.get("data") if isinstance(payload, dict) else None
    if not data:
        return None

    def scaled(field: str) -> float:
        value = data.get(field)
        if value in (None, "-", ""):
            raise ValueError(f"东方财富实时字段缺失: {field}")
        return round(float(value) / 100, 2)

    timestamp = data.get("f86")
    day = datetime.fromtimestamp(int(timestamp)).date().isoformat() if timestamp else date.today().isoformat()
    return Candle(
        date=day,
        open=scaled("f46"),
        high=scaled("f44"),
        low=scaled("f45"),
        close=scaled("f43"),
        volume=int(float(data.get("f47") or 0)),
    )


def load_sina_candles(symbol: str, days: int = 180) -> tuple[list[Candle], bool]:
    code = normalize_symbol(symbol)
    days = max(60, min(int(days or 180), 500))
    market = "sh" if _market_for_symbol(code) == "SH" else "sz"
    params = {
        "symbol": f"{market}{code}",
        "scale": "240",
        "ma": "no",
        "datalen": str(days),
    }
    url = "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=10) as response:
        rows = json.loads(response.read().decode("utf-8", "ignore"))
    candles = [
        Candle(
            date=row["day"],
            open=round(float(row["open"]), 2),
            high=round(float(row["high"]), 2),
            low=round(float(row["low"]), 2),
            close=round(float(row["close"]), 2),
            volume=int(float(row["volume"])),
        )
        for row in rows
    ]
    try:
        realtime = load_eastmoney_realtime_candle(code)
    except Exception:
        realtime = None
    if realtime and candles and realtime.date > candles[-1].date:
        candles.append(realtime)
        return candles, True
    elif realtime and candles and realtime.date == candles[-1].date:
        candles[-1] = realtime
        return candles, True
    return candles, False


def _read_eastmoney_json(url: str, symbol: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://quote.eastmoney.com/{'sh' if _market_for_symbol(symbol) == 'SH' else 'sz'}{symbol}.html",
        "Connection": "close",
    }
    try:
        return _read_eastmoney_json_urllib(url, headers)
    except Exception:
        return _read_eastmoney_json_curl(url, headers)


def _read_eastmoney_json_urllib(url: str, headers: dict[str, str]) -> dict:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8", "ignore"))


def _read_eastmoney_json_curl(url: str, headers: dict[str, str]) -> dict:
    command = [
        "curl",
        "-sS",
        "-L",
        "--http1.1",
        "--connect-timeout",
        "5",
        "-m",
        "10",
        "-A",
        headers["User-Agent"],
        "-H",
        f"Accept: {headers['Accept']}",
        "-H",
        f"Referer: {headers['Referer']}",
        url,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=12, check=True)
    body = completed.stdout.strip()
    if not body:
        raise ValueError("curl返回空响应")
    return json.loads(body)


def _parse_eastmoney_klines(payload: dict) -> list[Candle]:
    data = payload.get("data") if isinstance(payload, dict) else None
    rows = data.get("klines") if isinstance(data, dict) else None
    if not rows:
        raise ValueError("东方财富返回空K线")
    candles: list[Candle] = []
    for row in rows:
        parts = row.split(",")
        if len(parts) < 6:
            continue
        candles.append(
            Candle(
                date=parts[0],
                open=round(float(parts[1]), 2),
                close=round(float(parts[2]), 2),
                high=round(float(parts[3]), 2),
                low=round(float(parts[4]), 2),
                volume=int(float(parts[5])),
            )
        )
    return candles


def load_candles_with_provider(symbol: str, days: int = 180, provider: str = "eastmoney") -> tuple[list[Candle], str]:
    if provider == "eastmoney":
        try:
            return load_eastmoney_candles(symbol, days), "eastmoney"
        except Exception:
            candles, has_realtime = load_sina_candles(symbol, days)
            return candles, "sina+eastmoney_realtime" if has_realtime else "sina"
    if provider == "demo":
        return generate_demo_candles(symbol, days), "demo"
    raise ValueError(f"不支持的行情源：{provider}")


def load_candles(symbol: str, days: int = 180, provider: str = "eastmoney") -> list[Candle]:
    candles, _actual_provider = load_candles_with_provider(symbol, days, provider)
    return candles
