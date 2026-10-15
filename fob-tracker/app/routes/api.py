from datetime import datetime

from flask import Blueprint, jsonify, request

from .. import auth, db, report

bp = Blueprint("api", __name__)


@bp.route("/health", methods=["GET"])
def health():
    resp = jsonify({"ok": True, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    resp.headers["X-Fob-Api"] = "1"
    return resp


@bp.route("/users", methods=["GET"])
@auth.require_api_key
def users_api():
    rows = db.query(
        "SELECT id, name, employee_id, active, created_at FROM users ORDER BY name"
    )
    return jsonify({"users": [dict(r) for r in rows]})


@bp.route("/scans", methods=["GET"])
@auth.require_api_key
def scans_api():
    frm = request.args.get("from")
    to = request.args.get("to")
    user_id = request.args.get("user_id", type=int)
    limit = min(int(request.args.get("limit", 500)), 5000)
    offset = int(request.args.get("offset", 0))

    where = []
    params: list = []
    if frm:
        where.append("date(s.scanned_at) >= ?")
        params.append(frm)
    if to:
        where.append("date(s.scanned_at) <= ?")
        params.append(to)
    if user_id:
        where.append("s.user_id = ?")
        params.append(user_id)
    sql = """
        SELECT s.id, s.fob_uid, s.user_id, u.name AS user_name,
               s.scanned_at, s.direction, s.entry_source, s.note
        FROM scans s LEFT JOIN users u ON u.id = s.user_id
    """
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY s.scanned_at DESC, s.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    rows = db.query(sql, tuple(params))
    return jsonify({"scans": [dict(r) for r in rows], "limit": limit, "offset": offset})


@bp.route("/currently-in", methods=["GET"])
@auth.require_api_key
def currently_in_api():
    return jsonify({"currently_in": report.currently_in_users()})


@bp.route("/summary", methods=["GET"])
@auth.require_api_key
def summary_api():
    month = request.args.get("month", "")
    try:
        year_s, mon_s = month.split("-")
        year, mon = int(year_s), int(mon_s)
    except ValueError:
        return jsonify({"error": "month must be YYYY-MM"}), 400
    return jsonify({"month": month, "rows": report.month_summary(year, mon)})


@bp.route("/daily", methods=["GET"])
@auth.require_api_key
def daily_api():
    month = request.args.get("month", "")
    user_id = request.args.get("user_id", type=int)
    try:
        year_s, mon_s = month.split("-")
        year, mon = int(year_s), int(mon_s)
    except ValueError:
        return jsonify({"error": "month must be YYYY-MM"}), 400
    return jsonify(
        {
            "month": month,
            "user_id": user_id,
            "rows": report.daily_pairs(year, mon, user_id),
        }
    )
