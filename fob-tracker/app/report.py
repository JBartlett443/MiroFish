"""Reporting: dashboard stats, monthly summaries, daily IN/OUT pairs."""
from calendar import monthrange
from collections import defaultdict
from datetime import datetime, date, time, timedelta

from . import db


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")


def pair_day(scans: list) -> list[dict]:
    """
    Given scans for a single user on a single local date, sorted by time,
    return a list of session dicts:
        { in: datetime|None, out: datetime|None, hours: float,
          in_source: str|None, out_source: str|None, source: 'fob'|'manual'|'mixed'|None,
          notes: [str] }
    Unpaired INs or OUTs become their own row with notes.
    """
    sessions = []
    current = None
    for s in scans:
        when = _parse(s["scanned_at"])
        if s["direction"] == "IN":
            if current is not None:
                sessions.append(current)
            current = {
                "in": when,
                "out": None,
                "hours": 0.0,
                "in_source": s["entry_source"],
                "out_source": None,
                "notes": ["missing clock-out"],
            }
        else:
            if current is None:
                sessions.append(
                    {
                        "in": None,
                        "out": when,
                        "hours": 0.0,
                        "in_source": None,
                        "out_source": s["entry_source"],
                        "notes": ["missing clock-in"],
                    }
                )
            else:
                hours = (when - current["in"]).total_seconds() / 3600.0
                current["out"] = when
                current["out_source"] = s["entry_source"]
                current["hours"] = max(0.0, hours)
                current["notes"] = []
                sessions.append(current)
                current = None
    if current is not None:
        sessions.append(current)

    for sess in sessions:
        srcs = {s for s in (sess["in_source"], sess["out_source"]) if s}
        if not srcs:
            sess["source"] = None
        elif len(srcs) == 1:
            sess["source"] = next(iter(srcs))
        else:
            sess["source"] = "mixed"
    return sessions


def _scans_for_month(year: int, month: int) -> list:
    start = f"{year:04d}-{month:02d}-01"
    last_day = monthrange(year, month)[1]
    end = f"{year:04d}-{month:02d}-{last_day:02d}"
    return db.query(
        """
        SELECT s.id, s.user_id, s.scanned_at, s.direction, s.entry_source, s.note,
               u.name AS user_name, u.employee_id
        FROM scans s
        JOIN users u ON u.id = s.user_id
        WHERE s.user_id IS NOT NULL
          AND date(s.scanned_at) BETWEEN ? AND ?
        ORDER BY s.user_id, s.scanned_at, s.id
        """,
        (start, end),
    )


def month_summary(year: int, month: int) -> list[dict]:
    """Per-user totals for the month."""
    scans = _scans_for_month(year, month)
    by_user_day = defaultdict(lambda: defaultdict(list))
    user_meta = {}
    for s in scans:
        user_meta[s["user_id"]] = (s["user_name"], s["employee_id"])
        local_date = s["scanned_at"][:10]
        by_user_day[s["user_id"]][local_date].append(s)

    rows = []
    for user_id, days in by_user_day.items():
        total_hours = 0.0
        days_worked = 0
        manual_count = 0
        for day_scans in days.values():
            sessions = pair_day(day_scans)
            day_hours = sum(sess["hours"] for sess in sessions)
            if day_hours > 0:
                days_worked += 1
            total_hours += day_hours
            manual_count += sum(1 for s in day_scans if s["entry_source"] == "manual")
        name, emp_id = user_meta[user_id]
        rows.append(
            {
                "user_id": user_id,
                "name": name,
                "employee_id": emp_id,
                "days_worked": days_worked,
                "total_hours": round(total_hours, 2),
                "manual_entries": manual_count,
            }
        )
    rows.sort(key=lambda r: r["name"].lower())
    return rows


def daily_pairs(year: int, month: int, user_id: int | None = None) -> list[dict]:
    """One row per IN/OUT pair across the month, sorted by date then name."""
    scans = _scans_for_month(year, month)
    if user_id is not None:
        scans = [s for s in scans if s["user_id"] == user_id]
    by_user_day = defaultdict(lambda: defaultdict(list))
    user_name = {}
    for s in scans:
        user_name[s["user_id"]] = s["user_name"]
        by_user_day[s["user_id"]][s["scanned_at"][:10]].append(s)

    out = []
    for uid, days in by_user_day.items():
        for day, day_scans in days.items():
            for sess in pair_day(day_scans):
                out.append(
                    {
                        "date": day,
                        "user_id": uid,
                        "name": user_name[uid],
                        "clock_in": sess["in"].strftime("%H:%M") if sess["in"] else None,
                        "clock_out": sess["out"].strftime("%H:%M") if sess["out"] else None,
                        "hours": round(sess["hours"], 2),
                        "source": sess["source"] or "",
                        "notes": "; ".join(sess["notes"]),
                    }
                )
    out.sort(key=lambda r: (r["date"], r["name"].lower(), r["clock_in"] or ""))
    return out


def dashboard_stats() -> dict:
    today = date.today().strftime("%Y-%m-%d")
    now = datetime.now()
    week_start = (date.today() - timedelta(days=date.today().weekday())).strftime("%Y-%m-%d")

    today_scans = db.query(
        """
        SELECT s.id, s.user_id, s.scanned_at, s.direction, s.entry_source,
               u.name AS user_name
        FROM scans s
        LEFT JOIN users u ON u.id = s.user_id
        WHERE date(s.scanned_at) = ?
        ORDER BY s.user_id, s.scanned_at, s.id
        """,
        (today,),
    )

    by_user = defaultdict(list)
    for s in today_scans:
        if s["user_id"] is not None:
            by_user[s["user_id"]].append(s)

    currently_in = []
    for uid, items in by_user.items():
        last = items[-1]
        if last["direction"] == "IN":
            start_dt = _parse(last["scanned_at"])
            elapsed = (now - start_dt).total_seconds() / 60.0
            hours = int(elapsed // 60)
            mins = int(elapsed % 60)
            currently_in.append(
                {
                    "user_id": uid,
                    "name": last["user_name"],
                    "since": start_dt.strftime("%H:%M"),
                    "elapsed": f"{hours}h {mins:02d}m",
                }
            )
    currently_in.sort(key=lambda r: r["since"])

    unique_people = len({s["user_id"] for s in today_scans if s["user_id"]})
    hour_ago = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    last_hour = db.query(
        "SELECT COUNT(*) AS c FROM scans WHERE scanned_at >= ?", (hour_ago,), one=True
    )["c"]

    week_scans = db.query(
        """
        SELECT user_id, scanned_at, direction, entry_source
        FROM scans
        WHERE user_id IS NOT NULL AND date(scanned_at) BETWEEN ? AND ?
        ORDER BY user_id, scanned_at, id
        """,
        (week_start, today),
    )
    per_day_hours: dict[str, float] = defaultdict(float)
    by_user_day = defaultdict(lambda: defaultdict(list))
    for s in week_scans:
        by_user_day[s["user_id"]][s["scanned_at"][:10]].append(dict(s))
    for uid, days in by_user_day.items():
        for day, scans in days.items():
            for sess in pair_day(scans):
                per_day_hours[day] += sess["hours"]
    week_total = round(sum(per_day_hours.values()), 2)
    week_days = []
    for i in range(7):
        d = (date.today() - timedelta(days=date.today().weekday()) + timedelta(days=i)).strftime(
            "%Y-%m-%d"
        )
        week_days.append({"date": d, "hours": round(per_day_hours.get(d, 0.0), 2)})

    recent = db.query(
        """
        SELECT s.id, s.scanned_at, s.direction, s.entry_source, s.user_id, s.fob_uid,
               u.name AS user_name
        FROM scans s
        LEFT JOIN users u ON u.id = s.user_id
        ORDER BY s.scanned_at DESC, s.id DESC
        LIMIT 20
        """
    )
    recent_rows = []
    for r in recent:
        recent_rows.append(
            {
                "id": r["id"],
                "name": r["user_name"] or f"Unknown ({r['fob_uid']})",
                "direction": r["direction"],
                "time": r["scanned_at"][11:16],
                "date": r["scanned_at"][:10],
                "manual": r["entry_source"] == "manual",
            }
        )

    return {
        "now": now.strftime("%H:%M"),
        "today": today,
        "currently_in": currently_in,
        "scans_today": len(today_scans),
        "people_today": unique_people,
        "scans_last_hour": last_hour,
        "week_total_hours": week_total,
        "week_days": week_days,
        "recent": recent_rows,
    }


def currently_in_users() -> list[dict]:
    return dashboard_stats()["currently_in"]
