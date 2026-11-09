"""
Signed-in users for the listing assistant (Supabase Auth).

The frontend signs people in with Supabase and sends their access token as
`Authorization: Bearer <token>`. We check the token with Supabase itself
(GET /auth/v1/user), which works whichever JWT signing keys the project uses and
also rejects signed-out sessions.

Per-user daily limits live in Postgres (table assistant_usage), so they hold across
restarts and server workers. Days roll over at midnight Ithaca time.

Needs SUPABASE_URL and SUPABASE_ANON_KEY in the environment (backend/.env works).
Without those, sign-in is off and every caller shares the local account.
"""

import hashlib
import logging
import os
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import Header, HTTPException
from sqlalchemy import Column, Date, DateTime, Integer, String, Text, JSON, func, text
from sqlalchemy.orm import Session

from db import Base, engine

ITHACA_TZ = ZoneInfo("America/New_York")

ASSISTANT_PER_USER_PER_DAY = int(os.getenv("ASSISTANT_PER_USER_PER_DAY", "3"))
PREFERENCES_PER_USER_PER_DAY = int(os.getenv("PREFERENCES_PER_USER_PER_DAY", "3"))


# ---------- Tables ----------

class AssistantUsage(Base):
    """How many times a user used something (kind) on a given Ithaca-time day"""
    __tablename__ = "assistant_usage"

    user_id = Column(String, primary_key=True)
    day = Column(Date, primary_key=True)
    kind = Column(String, primary_key=True)  # "recommend" or "preferences"
    count = Column(Integer, nullable=False, default=0)


class UserPreference(Base):
    """What a user told us they're looking for, plus the compact version the assistant reads"""
    __tablename__ = "user_preferences"

    user_id = Column(String, primary_key=True)
    raw_text = Column(Text, nullable=False)
    schematic = Column(Text, nullable=False)  # e.g. "beds=3 | area=Collegetown | rent<=$1200/person"
    data = Column(JSON)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


def create_tables() -> None:
    tables = [AssistantUsage.__table__, UserPreference.__table__]
    Base.metadata.create_all(bind=engine, tables=tables)
    if engine.dialect.name == "postgresql":
        # Supabase exposes the public schema through its REST API to anyone holding the anon key.
        # RLS with no policies locks these tables to the backend's own database role.
        with engine.begin() as conn:
            for t in tables:
                conn.execute(text(f'ALTER TABLE "{t.name}" ENABLE ROW LEVEL SECURITY'))


# ---------- Who is calling ----------

_token_cache: dict = {}  # sha256(token) -> (expires_at, user)
_token_lock = threading.Lock()
TOKEN_CACHE_SECONDS = 60


# Shared account when Supabase auth isn't configured, so the assistant still works locally.
LOCAL_USER = {"id": "local", "email": None}


def auth_configured() -> bool:
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"))


def current_user(authorization: str = Header(default="")) -> dict:
    """FastAPI dependency: the signed-in Supabase user, or the local account when sign-in is off"""
    if not auth_configured():
        return LOCAL_USER
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Sign in to use the assistant.")

    key = hashlib.sha256(token.encode()).hexdigest()
    now = time.time()
    with _token_lock:
        hit = _token_cache.get(key)
        if hit and hit[0] > now:
            return hit[1]

    try:
        res = httpx.get(
            f"{os.environ['SUPABASE_URL'].rstrip('/')}/auth/v1/user",
            headers={"Authorization": f"Bearer {token}", "apikey": os.environ["SUPABASE_ANON_KEY"]},
            timeout=10,
        )
    except httpx.HTTPError:
        logging.exception("Accounts: couldn't reach Supabase Auth")
        raise HTTPException(status_code=502, detail="Couldn't check your sign-in. Try again.")
    if res.status_code != 200:
        raise HTTPException(status_code=401, detail="Your sign-in expired. Sign in again.")

    body = res.json()
    user = {"id": body["id"], "email": body.get("email")}
    with _token_lock:
        _token_cache[key] = (now + TOKEN_CACHE_SECONDS, user)
        if len(_token_cache) > 5_000:
            for k in [k for k, v in _token_cache.items() if v[0] <= now]:
                del _token_cache[k]
    return user


# ---------- Daily limits ----------

def today():
    return datetime.now(ITHACA_TZ).date()


def used_today(db: Session, user_id: str, kind: str) -> int:
    row = db.get(AssistantUsage, (user_id, today(), kind))
    return row.count if row else 0


def reserve(db: Session, user_id: str, kind: str, limit: int, message: str) -> int:
    """Atomically takes one of today's uses; returns how many are left, or raises 429"""
    row = db.execute(
        text(
            """
            INSERT INTO assistant_usage (user_id, day, kind, count) VALUES (:u, :d, :k, 1)
            ON CONFLICT (user_id, day, kind) DO UPDATE SET count = assistant_usage.count + 1
            WHERE assistant_usage.count < :limit
            RETURNING count
            """
        ),
        {"u": user_id, "d": today(), "k": kind, "limit": limit},
    ).fetchone()
    db.commit()
    if row is None:
        raise HTTPException(status_code=429, detail=message)
    return max(limit - row[0], 0)


def refund(db: Session, user_id: str, kind: str) -> None:
    """Gives a use back when the request failed before producing anything"""
    try:
        db.rollback()
        db.execute(
            text(
                "UPDATE assistant_usage SET count = count - 1 "
                "WHERE user_id = :u AND day = :d AND kind = :k AND count > 0"
            ),
            {"u": user_id, "d": today(), "k": kind},
        )
        db.commit()
    except Exception:
        logging.exception("Accounts: couldn't refund a %s use for %s", kind, user_id)


def get_preferences(db: Session, user_id: str):
    return db.get(UserPreference, user_id)
