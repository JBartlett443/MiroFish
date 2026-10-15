from datetime import datetime

from app import scans, db as db_mod
from tests.conftest import seed_user, seed_fob


def test_unknown_fob_recorded(ctx):
    result = scans.record_fob_scan("ABC123")
    assert result["status"] == "unknown"
    rows = db_mod.query("SELECT * FROM scans")
    assert len(rows) == 1
    assert rows[0]["user_id"] is None
    assert rows[0]["entry_source"] == "fob"


def test_direction_toggles_within_day(ctx):
    uid = seed_user("A")
    seed_fob("F1", uid)
    r1 = scans.record_fob_scan("F1")
    r2 = scans.record_fob_scan("F1")
    r3 = scans.record_fob_scan("F1")
    assert [r1["direction"], r2["direction"], r3["direction"]] == ["IN", "OUT", "IN"]


def test_two_users_dont_cross(ctx):
    a = seed_user("A", "E-A")
    b = seed_user("B", "E-B")
    seed_fob("Fa", a)
    seed_fob("Fb", b)
    assert scans.record_fob_scan("Fa")["direction"] == "IN"
    assert scans.record_fob_scan("Fb")["direction"] == "IN"
    assert scans.record_fob_scan("Fa")["direction"] == "OUT"
    assert scans.record_fob_scan("Fb")["direction"] == "OUT"


def test_manual_entry_flag(ctx):
    uid = seed_user("A")
    scans.manual_add(uid, datetime(2026, 10, 1, 9, 0), "IN", "forgot fob", "admin")
    row = db_mod.query("SELECT * FROM scans", one=True)
    assert row["entry_source"] == "manual"
    assert row["fob_uid"] is None
    assert row["note"] == "forgot fob"
    assert row["created_by"] == "admin"


def test_inactive_user_not_recorded_as_ok(ctx):
    uid = seed_user("A")
    seed_fob("F1", uid)
    db_mod.execute("UPDATE users SET active = 0 WHERE id = ?", (uid,))
    r = scans.record_fob_scan("F1")
    assert r["status"] == "inactive"


def test_revoked_fob_is_unknown(ctx):
    uid = seed_user("A")
    seed_fob("F1", uid)
    db_mod.execute("UPDATE fobs SET revoked_at = datetime('now') WHERE fob_uid = 'F1'")
    r = scans.record_fob_scan("F1")
    assert r["status"] == "unknown"
