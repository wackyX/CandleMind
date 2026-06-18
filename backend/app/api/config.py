"""
Runtime configuration and diagnostics API.
"""

from flask import jsonify, request

from . import config_bp
from ..services.stock_data_health import check_stock_data_sources
from ..services.llm_diagnostics import check_llm_connection, llm_config_summary


@config_bp.route("/llm", methods=["GET"])
def llm_config():
    return jsonify({"success": True, "data": llm_config_summary()})


@config_bp.route("/check-llm", methods=["POST"])
def check_llm():
    return jsonify({"success": True, "data": check_llm_connection()})


@config_bp.route("/data-sources/health", methods=["GET"])
def data_sources_health():
    symbol = request.args.get("symbol", "600519")
    return jsonify({"success": True, "data": check_stock_data_sources(symbol)})
