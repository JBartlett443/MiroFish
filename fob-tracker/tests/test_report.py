from datetime import datetime, timedelta, date

from app import report, scans
from tests.conftest import seed_user, seed_scan


def test_full_day_pairs(ctx):
    uid = seed_user("Jane")
    seed_scan(uid, "2026-10-01 09:00:00", "IN")
    seed_scan(uid, "2026-10-01 17:30:00", "OUT")
    rows = report.daily_pairs(2026, 10)
    assert len(rows) == 1
    assert rows[0]["hours"] == 8.5
    assert rows[0]["clock_in"] == "09:00"
    assert rows[0]["clock_out"] == "17:30"
    assert rows[0]["source"] == "fob"
    assert rows[0]["notes"] == ""


def test_unpaired_in_flagged(ctx):
    uid = seed_user("Jane")
    seed_scan(uid, "2026-10-01 09:00:00", "IN")
    rows = report.daily_pairs(2026, 10)
    assert len(rows) == 1
    assert rows[0]["hours"] == 0.0
    assert rows[0]["clock_out"] is None
    assert "missing clock-out" in rows[0]["notes"]


def test_multiple_sessions_summed(ctx):
    uid = seed_user("Jane")
    for t_in, t_out in [("09:00", "12:00"), ("13:00", "17:00")]:
        seed_scan(uid, f"2026-10-02 {t_in}:00", "IN")
        seed_scan(uid, f"2026-10-02 {t_out}:00", "OUT")
    s = report.month_summary(2026, 10)
    assert len(s) == 1
    assert s[0]["total_hours"] == 7.0
    assert s[0]["days_worked"] == 1


def test_manual_mixed_pair_marked(ctx):
    uid = seed_user("Jane")
    seed_scan(uid, "2026-10-03 09:00:00", "IN", source="fob")
    seed_scan(uid, "2026-10-03 17:00:00", "OUT", source="manual")
    rows = report.daily_pairs(2026, 10)
    assert rows[0]["source"] == "mixed"


def test_dashboard_currently_in(ctx):
    uid = seed_user("Jane")
    today = date.today().strftime("%Y-%m-%d")
    seed_scan(uid, f"{today} 09:00:00", "IN")
    stats = report.dashboard_stats()
    assert any(p["name"] == "Jane" for p in stats["currently_in"])


def test_dashboard_not_in_after_out(ctx):
    uid = seed_user("Jane")
    today = date.today().strftime("%Y-%m-%d")
    seed_scan(uid, f"{today} 09:00:00", "IN")
    seed_scan(uid, f"{today} 10:00:00", "OUT")
    stats = report.dashboard_stats()
    assert stats["currently_in"] == []
