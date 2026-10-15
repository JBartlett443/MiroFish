from app import api_keys as api_keys_mod
from tests.conftest import seed_user


def test_health_is_public(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json["ok"] is True


def test_missing_key_rejected(client):
    r = client.get("/api/v1/users")
    assert r.status_code == 401


def test_unknown_key_rejected(client):
    r = client.get("/api/v1/users", headers={"X-API-Key": "nope"})
    assert r.status_code == 401


def test_valid_key_allows_and_updates_last_used(client, ctx):
    _id, key = api_keys_mod.generate("ops")
    r = client.get("/api/v1/users", headers={"X-API-Key": key})
    assert r.status_code == 200
    rows = api_keys_mod.list_all()
    assert rows[0]["last_used_at"] is not None


def test_revoked_key_rejected(client, ctx):
    key_id, key = api_keys_mod.generate("ops")
    api_keys_mod.revoke(key_id)
    r = client.get("/api/v1/users", headers={"X-API-Key": key})
    assert r.status_code == 401


def test_scans_filters_by_date(client, ctx):
    from app import db as db_mod
    uid = seed_user("Jane")
    db_mod.execute(
        "INSERT INTO scans (user_id, scanned_at, direction, entry_source, created_by) "
        "VALUES (?, '2026-10-05 09:00:00', 'IN', 'fob', 't')",
        (uid,),
    )
    db_mod.execute(
        "INSERT INTO scans (user_id, scanned_at, direction, entry_source, created_by) "
        "VALUES (?, '2026-09-10 09:00:00', 'IN', 'fob', 't')",
        (uid,),
    )
    _id, key = api_keys_mod.generate("ops")
    r = client.get(
        "/api/v1/scans?from=2026-10-01&to=2026-10-31",
        headers={"X-API-Key": key},
    )
    assert r.status_code == 200
    assert len(r.json["scans"]) == 1
    assert r.json["scans"][0]["scanned_at"].startswith("2026-10-05")
