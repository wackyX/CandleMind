"""
A-share K-line prophecy API.
"""

import traceback

from flask import jsonify, request

from . import stock_bp
from ..services.stock_archive import list_prophecy_archives, read_prophecy_archive
from ..services.stock_market_data import search_symbols
from ..services.stock_prophecy import (
    BacktestRequest,
    BatchBacktestRequest,
    ProphecyRequest,
    run_backtest,
    run_batch_backtest,
    run_prophecy,
)
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


@stock_bp.route("/prophecy/backtest", methods=["POST"])
def prophecy_backtest():
    try:
        data = request.get_json() or {}
        symbol = data.get("symbol", "600519")
        as_of_date = data.get("asOfDate", "")
        horizon = int(data.get("horizon", 5))
        days = int(data.get("days", 180))
        provider = data.get("provider", "eastmoney")
        use_llm = bool(data.get("useLlm", False))
        result = run_backtest(
            BacktestRequest(
                symbol=symbol,
                as_of_date=as_of_date,
                horizon=horizon,
                days=days,
                provider=provider,
                use_llm=use_llm,
            )
        )
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        logger.error(f"A股预言回测失败: {exc}")
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


@stock_bp.route("/prophecy/backtest/batch", methods=["POST"])
def prophecy_batch_backtest():
    try:
        data = request.get_json() or {}
        symbol = data.get("symbol", "600519")
        horizon = int(data.get("horizon", 5))
        days = int(data.get("days", 180))
        provider = data.get("provider", "eastmoney")
        samples = int(data.get("samples", 12))
        step = int(data.get("step", 5))
        use_llm = bool(data.get("useLlm", False))
        result = run_batch_backtest(
            BatchBacktestRequest(
                symbol=symbol,
                horizon=horizon,
                days=days,
                provider=provider,
                samples=samples,
                step=step,
                use_llm=use_llm,
            )
        )
        return jsonify({"success": True, "data": result})
    except Exception as exc:
        logger.error(f"A股批量回测失败: {exc}")
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


@stock_bp.route("/prophecies", methods=["GET"])
def prophecy_archives():
    limit = int(request.args.get("limit", 20))
    return jsonify({"success": True, "data": list_prophecy_archives(limit)})


@stock_bp.route("/prophecies/<archive_id>", methods=["GET"])
def prophecy_archive_detail(archive_id: str):
    archive = read_prophecy_archive(archive_id)
    if not archive:
        return jsonify({"success": False, "error": "推演档案不存在"}), 404
    return jsonify({"success": True, "data": archive})
