"""
Technical indicators and lightweight backtesting helpers for A-share candles.
"""

from __future__ import annotations

from statistics import mean, pstdev

from .stock_market_data import Candle


def _round(value: float | None, digits: int = 4) -> float | None:
    if value is None:
        return None
    return round(value, digits)


def simple_moving_average(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < period:
            result.append(None)
        else:
            result.append(mean(values[index + 1 - period : index + 1]))
    return result


def exponential_moving_average(values: list[float], period: int) -> list[float | None]:
    if not values:
        return []
    alpha = 2 / (period + 1)
    ema = values[0]
    result: list[float | None] = []
    for index, value in enumerate(values):
        ema = value if index == 0 else (value * alpha + ema * (1 - alpha))
        result.append(ema if index + 1 >= period else None)
    return result


def relative_strength_index(values: list[float], period: int = 14) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return result

    gains: list[float] = []
    losses: list[float] = []
    for index in range(1, period + 1):
        change = values[index] - values[index - 1]
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))

    avg_gain = mean(gains)
    avg_loss = mean(losses)
    result[period] = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))

    for index in range(period + 1, len(values)):
        change = values[index] - values[index - 1]
        gain = max(change, 0)
        loss = abs(min(change, 0))
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        result[index] = 100 if avg_loss == 0 else 100 - (100 / (1 + avg_gain / avg_loss))

    return result


def average_true_range(candles: list[Candle], period: int = 14) -> list[float | None]:
    true_ranges: list[float] = []
    for index, candle in enumerate(candles):
        prev_close = candles[index - 1].close if index > 0 else candle.close
        true_ranges.append(
            max(
                candle.high - candle.low,
                abs(candle.high - prev_close),
                abs(candle.low - prev_close),
            )
        )
    return simple_moving_average(true_ranges, period)


def macd(values: list[float]) -> tuple[list[float | None], list[float | None], list[float | None]]:
    ema12 = exponential_moving_average(values, 12)
    ema26 = exponential_moving_average(values, 26)
    dif: list[float | None] = []
    for fast, slow in zip(ema12, ema26):
        dif.append(None if fast is None or slow is None else fast - slow)

    signal_values = [item if item is not None else 0 for item in dif]
    dea_raw = exponential_moving_average(signal_values, 9)
    dea: list[float | None] = []
    hist: list[float | None] = []
    for index, value in enumerate(dif):
        if value is None or index < 34:
            dea.append(None)
            hist.append(None)
        else:
            dea_value = dea_raw[index]
            dea.append(dea_value)
            hist.append((value - dea_value) * 2 if dea_value is not None else None)
    return dif, dea, hist


def bollinger(values: list[float], period: int = 20) -> tuple[list[float | None], list[float | None], list[float | None]]:
    mid = simple_moving_average(values, period)
    upper: list[float | None] = []
    lower: list[float | None] = []
    for index, center in enumerate(mid):
        if center is None:
            upper.append(None)
            lower.append(None)
            continue
        window = values[index + 1 - period : index + 1]
        width = pstdev(window) * 2
        upper.append(center + width)
        lower.append(center - width)
    return mid, upper, lower


def build_indicator_series(candles: list[Candle]) -> list[dict]:
    closes = [candle.close for candle in candles]
    volumes = [float(candle.volume) for candle in candles]
    ma5 = simple_moving_average(closes, 5)
    ma20 = simple_moving_average(closes, 20)
    ma60 = simple_moving_average(closes, 60)
    volume_ma5 = simple_moving_average(volumes, 5)
    rsi14 = relative_strength_index(closes, 14)
    atr14 = average_true_range(candles, 14)
    dif, dea, hist = macd(closes)
    bb_mid, bb_upper, bb_lower = bollinger(closes, 20)

    rows: list[dict] = []
    for index, candle in enumerate(candles):
        rows.append(
            {
                "date": candle.date,
                "ma5": _round(ma5[index], 2),
                "ma20": _round(ma20[index], 2),
                "ma60": _round(ma60[index], 2),
                "volumeMa5": _round(volume_ma5[index], 0),
                "rsi14": _round(rsi14[index], 2),
                "atr14": _round(atr14[index], 2),
                "macdDif": _round(dif[index], 4),
                "macdDea": _round(dea[index], 4),
                "macdHist": _round(hist[index], 4),
                "bbMid": _round(bb_mid[index], 2),
                "bbUpper": _round(bb_upper[index], 2),
                "bbLower": _round(bb_lower[index], 2),
            }
        )
    return rows


def latest_snapshot(candles: list[Candle], indicators: list[dict]) -> dict:
    latest = candles[-1]
    previous = candles[-2]
    latest_indicators = indicators[-1]
    closes = [item.close for item in candles]
    recent20 = candles[-20:]
    high20 = max(item.high for item in recent20)
    low20 = min(item.low for item in recent20)
    return {
        "close": latest.close,
        "changePct": round((latest.close / previous.close - 1) * 100, 2),
        "volume": latest.volume,
        "turnoverMood": _volume_mood(candles),
        "ma5": latest_indicators["ma5"],
        "ma20": latest_indicators["ma20"],
        "ma60": latest_indicators["ma60"],
        "rsi14": latest_indicators["rsi14"],
        "atr14": latest_indicators["atr14"],
        "high20": round(high20, 2),
        "low20": round(low20, 2),
        "support": round(max(low20, closes[-1] - (latest_indicators["atr14"] or 0) * 1.4), 2),
        "resistance": round(min(high20, closes[-1] + (latest_indicators["atr14"] or 0) * 1.6), 2),
    }


def _volume_mood(candles: list[Candle]) -> str:
    recent = mean([item.volume for item in candles[-5:]])
    base = mean([item.volume for item in candles[-30:-5]])
    if recent > base * 1.25:
        return "放量"
    if recent < base * 0.78:
        return "缩量"
    return "温和"


def historical_analogs(candles: list[Candle], horizon: int = 5) -> dict:
    if len(candles) < 90:
        return {"sampleSize": 0, "upProbability": None, "avgForwardReturn": None}

    closes = [item.close for item in candles]
    current_return_5 = closes[-1] / closes[-6] - 1
    current_return_20 = closes[-1] / closes[-21] - 1
    current_volatility = _window_volatility(closes[-21:])
    matches: list[float] = []

    for index in range(60, len(candles) - horizon - 1):
        ret5 = closes[index] / closes[index - 5] - 1
        ret20 = closes[index] / closes[index - 20] - 1
        vol = _window_volatility(closes[index - 20 : index + 1])
        distance = abs(ret5 - current_return_5) + abs(ret20 - current_return_20) + abs(vol - current_volatility)
        if distance < 0.08:
            forward = closes[index + horizon] / closes[index] - 1
            matches.append(forward)

    if not matches:
        return {"sampleSize": 0, "upProbability": None, "avgForwardReturn": None}

    up_probability = sum(1 for value in matches if value > 0) / len(matches)
    return {
        "sampleSize": len(matches),
        "upProbability": round(up_probability * 100, 1),
        "avgForwardReturn": round(mean(matches) * 100, 2),
    }


def _window_volatility(values: list[float]) -> float:
    returns = [values[index] / values[index - 1] - 1 for index in range(1, len(values))]
    return pstdev(returns) if len(returns) > 1 else 0
