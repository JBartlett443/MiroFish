"""Scan recording & direction logic."""
from datetime import datetime, date, time

from . import db


def _next_direction(user_id: int, local_date: str) -> str:
    row = db.query(
        """
        SELECT direction FROM scans
        WHERE user_id = ? AND date(scanned_at) = ?
        ORDER BY scanned_at DESC, id DESC
        LIMIT 1
        """,
        (user_id, local_date),
        one=True,
    )
    if row is None:
        return "IN"
    return "OUT" if row["direction"] == "IN" else "IN"


def record_fob_scan(fob_uid: str) -> dict:
    """Record a scan from the kiosk reader. Returns a dict for the kiosk UI."""
    fob_uid = (fob_uid or "").strip()
    if not fob_uid:
        return {"status": "error", "message": "Empty fob UID"}

    fob = db.query(
        "SELECT fob_uid, user_id FROM fobs WHERE fob_uid = ? AND revoked_at IS NULL",
        (fob_uid,),
        one=True,
    )

    now = datetime.now()
    now_iso = now.strftime("%Y-%m-%d %H:%M:%S")
    time_str = now.strftime("%H:%M")

    if fob is None:
        db.execute(
            """
            INSERT INTO scans (fob_uid, user_id, scanned_at, direction, entry_source, created_by)
            VALUES (?, NULL, ?, 'IN', 'fob', 'reader')
            """,
            (fob_uid, now_iso),
        )
        return {"status": "unknown", "fob_uid": fob_uid, "time": time_str}

    user = db.query(
        "SELECT id, name, active FROM users WHERE id = ?",
        (fob["user_id"],),
        one=True,
    )
    if user is None or not user["active"]:
        return {"status": "inactive", "fob_uid": fob_uid, "time": time_str}

    direction = _next_direction(user["id"], now.strftime("%Y-%m-%d"))
    db.execute(
        """
        INSERT INTO scans (fob_uid, user_id, scanned_at, direction, entry_source, created_by)
        VALUES (?, ?, ?, ?, 'fob', 'reader')
        """,
        (fob_uid, user["id"], now_iso, direction),
    )
    return {
        "status": "ok",
        "name": user["name"],
        "direction": direction,
        "time": time_str,
    }


def manual_add(
    user_id: int,
    local_dt: datetime,
    direction: str,
    note: str | None,
    created_by: str,
) -> int:
    if direction not in ("IN", "OUT"):
        raise ValueError("direction must be IN or OUT")
    return db.execute(
        """
        INSERT INTO scans (fob_uid, user_id, scanned_at, direction, entry_source, note, created_by)
        VALUES (NULL, ?, ?, ?, 'manual', ?, ?)
        """,
        (
            user_id,
            local_dt.strftime("%Y-%m-%d %H:%M:%S"),
            direction,
            (note or None),
            created_by,
        ),
    )
