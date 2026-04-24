import os
from datetime import datetime, timedelta, timezone

import aiosqlite


def _db_path() -> str:
    data_dir = os.environ.get("DATA_DIR", "/app/data")
    return os.path.join(data_dir, "dns.db")


async def init_db() -> None:
    path = _db_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    async with aiosqlite.connect(path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                id            TEXT PRIMARY KEY,
                domain        TEXT NOT NULL,
                subdomain     TEXT,
                ovh_record_id TEXT,
                ip            TEXT,
                created_at    TEXT NOT NULL,
                last_used_at  TEXT,
                expires_at    TEXT NOT NULL
            )
        """)
        await db.commit()


async def create_token(token: str, domain: str, expires_at: datetime) -> None:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            "INSERT INTO tokens (id, domain, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (token, domain, now, expires_at.isoformat()),
        )
        await db.commit()


async def get_token(token: str) -> dict | None:
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(_db_path()) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tokens WHERE id = ? AND expires_at > ?",
            (token, now),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_existing_subdomains(domain: str) -> set:
    async with aiosqlite.connect(_db_path()) as db:
        async with db.execute(
            "SELECT subdomain FROM tokens WHERE domain = ? AND subdomain IS NOT NULL",
            (domain,),
        ) as cursor:
            rows = await cursor.fetchall()
            return {row[0] for row in rows}


async def set_subdomain(
    token: str, subdomain: str, ovh_record_id: str, ip: str, expiry_days: int
) -> None:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=expiry_days)
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            """UPDATE tokens
               SET subdomain = ?, ovh_record_id = ?, ip = ?, last_used_at = ?, expires_at = ?
               WHERE id = ?""",
            (subdomain, ovh_record_id, ip, now.isoformat(), expires_at.isoformat(), token),
        )
        await db.commit()


async def update_ip(token: str, ip: str, expiry_days: int) -> None:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=expiry_days)
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            "UPDATE tokens SET ip = ?, last_used_at = ?, expires_at = ? WHERE id = ?",
            (ip, now.isoformat(), expires_at.isoformat(), token),
        )
        await db.commit()


async def touch_token(token: str, expiry_days: int) -> None:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(days=expiry_days)
    async with aiosqlite.connect(_db_path()) as db:
        await db.execute(
            "UPDATE tokens SET last_used_at = ?, expires_at = ? WHERE id = ?",
            (now.isoformat(), expires_at.isoformat(), token),
        )
        await db.commit()
