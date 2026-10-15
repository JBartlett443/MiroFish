"""API key generation, hashing, verification."""
import hashlib
import secrets

from . import db


def _hash(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def generate(label: str) -> tuple[int, str]:
    """Create a new key. Returns (id, plain_key). Plain key is shown once."""
    plain = "ft_" + secrets.token_urlsafe(32)
    key_id = db.execute(
        "INSERT INTO api_keys (label, key_hash) VALUES (?, ?)",
        (label, _hash(plain)),
    )
    return key_id, plain


def revoke(key_id: int) -> None:
    db.execute(
        "UPDATE api_keys SET revoked_at = datetime('now', 'localtime') WHERE id = ?",
        (key_id,),
    )


def list_all() -> list:
    return db.query(
        """
        SELECT id, label, created_at, last_used_at, revoked_at
        FROM api_keys ORDER BY id DESC
        """
    )


def verify(key: str) -> int | None:
    if not key:
        return None
    row = db.query(
        "SELECT id FROM api_keys WHERE key_hash = ? AND revoked_at IS NULL",
        (_hash(key),),
        one=True,
    )
    return row["id"] if row else None
