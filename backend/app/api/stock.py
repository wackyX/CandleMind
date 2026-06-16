"""
A-share K-line prophecy API.
"""

import traceback

from flask import jsonify, request

from . import stock_bp
from ..services.stock_market_data import search_symbols
from ..services.stock_prophecy import ProphecyRequest, run_prophecy
from ..utils.logger import get_logger

logger = get_logger("mirofish.api.stock")


@stock_bp.route("/symbols", methods=["GET"])
def symbols():
    keyword = request.args.get("q", "")
    return jsonify({"success": True, "data": search_symbols(keyword)})


@stock_bp.route("/prophecy", methods=["POST"])
def prophecy():
    try:
        data = request.get_json() or {}
        symbol = data.get("symbol", "600519")
        horizon = int(data.get("horizon", 5))
        days = int(data.get("days", 180))
        provider = data.get("provider", "eastmoney")
        include_events = bool(data.get("includeEvents", True))
        use_llm = bool(data.get("useLlm", True))
        result = run_prophecy(
            ProphecyRequest(
                symbol=symbol,
                horizon=horizon,
                days=days,
                provider=provider,
                include_events=include_events,
                use_llm=use_llm,
            )
        )
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        logger.error(f"A股预言生成失败: {exc}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                }
            ),
            500,
        )
