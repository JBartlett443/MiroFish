from flask import Blueprint, jsonify, render_template, request

from .. import scans

bp = Blueprint("scan", __name__)


@bp.route("/", methods=["GET"])
def kiosk():
    return render_template("scan.html")


@bp.route("/scan/submit", methods=["POST"])
def submit():
    data = request.get_json(silent=True) or request.form
    fob_uid = (data.get("fob_uid") or "").strip()
    result = scans.record_fob_scan(fob_uid)
    return jsonify(result)
