from datetime import datetime, date

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from .. import api_keys as api_keys_mod
from .. import auth, db, report, scans

bp = Blueprint("admin", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login_view():
    error = None
    if request.method == "POST":
        if auth.login(request.form.get("username", ""), request.form.get("password", "")):
            nxt = request.args.get("next") or url_for("admin.dashboard")
            return redirect(nxt)
        error = "Invalid credentials."
    return render_template("login.html", error=error)


@bp.route("/logout")
def logout_view():
    auth.logout()
    return redirect(url_for("admin.login_view"))


@bp.route("/", methods=["GET"])
@auth.require_admin
def dashboard():
    return render_template("dashboard.html", stats=report.dashboard_stats())


@bp.route("/stats.json", methods=["GET"])
@auth.require_admin
def dashboard_stats_json():
    return jsonify(report.dashboard_stats())


# ---- Users ----------------------------------------------------------------
@bp.route("/users", methods=["GET", "POST"])
@auth.require_admin
def users_view():
    if request.method == "POST":
        action = request.form.get("action", "add")
        if action == "add":
            name = request.form.get("name", "").strip()
            emp_id = request.form.get("employee_id", "").strip() or None
            if name:
                db.execute(
                    "INSERT INTO users (name, employee_id) VALUES (?, ?)",
                    (name, emp_id),
                )
                flash(f"Added user {name}.", "ok")
        elif action == "toggle":
            uid = int(request.form["user_id"])
            db.execute("UPDATE users SET active = 1 - active WHERE id = ?", (uid,))
        elif action == "edit":
            uid = int(request.form["user_id"])
            name = request.form.get("name", "").strip()
            emp_id = request.form.get("employee_id", "").strip() or None
            db.execute(
                "UPDATE users SET name = ?, employee_id = ? WHERE id = ?",
                (name, emp_id, uid),
            )
        return redirect(url_for("admin.users_view"))

    rows = db.query(
        "SELECT id, name, employee_id, active, created_at FROM users ORDER BY name"
    )
    return render_template("users.html", users=rows)


# ---- Fobs -----------------------------------------------------------------
@bp.route("/fobs", methods=["GET", "POST"])
@auth.require_admin
def fobs_view():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "revoke":
            fob_uid = request.form["fob_uid"]
            db.execute(
                "UPDATE fobs SET revoked_at = datetime('now', 'localtime') WHERE fob_uid = ?",
                (fob_uid,),
            )
            flash(f"Revoked fob {fob_uid}.", "ok")
        return redirect(url_for("admin.fobs_view"))

    assigned = db.query(
        """
        SELECT f.fob_uid, f.assigned_at, u.id AS user_id, u.name
        FROM fobs f JOIN users u ON u.id = f.user_id
        WHERE f.revoked_at IS NULL
        ORDER BY u.name
        """
    )
    seen_unassigned = db.query(
        """
        SELECT s.fob_uid, MAX(s.scanned_at) AS last_seen, COUNT(*) AS cnt
        FROM scans s
        LEFT JOIN fobs f ON f.fob_uid = s.fob_uid AND f.revoked_at IS NULL
        WHERE s.fob_uid IS NOT NULL AND f.fob_uid IS NULL
        GROUP BY s.fob_uid
        ORDER BY last_seen DESC
        """
    )
    return render_template("fobs.html", assigned=assigned, unassigned=seen_unassigned)


@bp.route("/fobs/assign", methods=["GET", "POST"])
@auth.require_admin
def fob_assign_view():
    prefill = request.args.get("fob_uid", "").strip()

    if request.method == "POST":
        fob_uid = request.form.get("fob_uid", "").strip()
        user_id = request.form.get("user_id", "").strip()
        if not fob_uid or not user_id:
            flash("Both fob and user are required.", "err")
            return redirect(url_for("admin.fob_assign_view"))

        existing = db.query(
            "SELECT user_id FROM fobs WHERE fob_uid = ? AND revoked_at IS NULL",
            (fob_uid,),
            one=True,
        )
        if existing:
            flash(f"Fob {fob_uid} is already assigned.", "err")
            return redirect(url_for("admin.fobs_view"))

        # Clear any previous revoked assignment so PK insert works.
        db.execute("DELETE FROM fobs WHERE fob_uid = ?", (fob_uid,))
        db.execute(
            "INSERT INTO fobs (fob_uid, user_id) VALUES (?, ?)",
            (fob_uid, int(user_id)),
        )
        flash(f"Linked fob {fob_uid}.", "ok")
        return redirect(url_for("admin.fob_assign_view"))

    users = db.query(
        "SELECT id, name, employee_id FROM users WHERE active = 1 ORDER BY name"
    )
    return render_template("fob_assign.html", users=users, prefill=prefill)


# ---- Manual scan ----------------------------------------------------------
@bp.route("/manual-scan", methods=["GET", "POST"])
@auth.require_admin
def manual_scan_view():
    users = db.query(
        "SELECT id, name FROM users WHERE active = 1 ORDER BY name"
    )
    if request.method == "POST":
        try:
            user_id = int(request.form["user_id"])
            d = request.form["date"]
            t = request.form["time"]
            direction = request.form["direction"]
            note = request.form.get("note", "").strip() or None
            dt = datetime.strptime(f"{d} {t}", "%Y-%m-%d %H:%M")
            scans.manual_add(user_id, dt, direction, note, auth.current_admin() or "admin")
            flash("Manual scan recorded.", "ok")
            return redirect(url_for("admin.manual_scan_view"))
        except (KeyError, ValueError) as exc:
            flash(f"Could not record scan: {exc}", "err")

    return render_template(
        "manual_scan.html",
        users=users,
        today=date.today().strftime("%Y-%m-%d"),
        now=datetime.now().strftime("%H:%M"),
    )


# ---- API keys -------------------------------------------------------------
@bp.route("/api-keys", methods=["GET", "POST"])
@auth.require_admin
def api_keys_view():
    new_plain = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create":
            label = request.form.get("label", "").strip() or "unnamed"
            _, new_plain = api_keys_mod.generate(label)
        elif action == "revoke":
            api_keys_mod.revoke(int(request.form["key_id"]))
            flash("Key revoked.", "ok")
            return redirect(url_for("admin.api_keys_view"))
    keys = api_keys_mod.list_all()
    return render_template("api_keys.html", keys=keys, new_plain=new_plain)
