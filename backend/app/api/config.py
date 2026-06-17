"""
Runtime configuration and diagnostics API.
"""

from flask import jsonify

from . import config_bp
from ..services.llm_diagnostics import check_llm_connection, llm_config_summary


@config_bp.route("/llm", methods=["GET"])
def llm_config():
    return jsonify({"success": True, "data": llm_config_summary()})


@config_bp.route("/check-llm", methods=["POST"])
def check_llm():
    return jsonify({"success": True, "data": check_llm_connection()})
