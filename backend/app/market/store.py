"""SQLite persistence for market observations, GPU snapshots, fetch state and runs."""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
  series TEXT NOT NULL, obs_date TEXT NOT NULL, value REAL, raw TEXT,
  collected_at TEXT NOT NULL, PRIMARY KEY (series, obs_date));
CREATE TABLE IF NOT EXISTS gpu_snapshots (
  snap_date TEXT NOT NULL, condition_key TEXT NOT NULL, condition_json TEXT NOT NULL,
  offer_count INTEGER NOT NULL, median REAL, p25 REAL, p75 REAL, min REAL, max REAL,
  median_dph_base REAL, collected_at TEXT NOT NULL, PRIMARY KEY (snap_date, condition_key));
CREATE TABLE IF NOT EXISTS source_state (
  source TEXT PRIMARY KEY, last_attempt_at TEXT, last_success_at TEXT, last_status TEXT,
  last_detail TEXT, meta_json TEXT);
CREATE TABLE IF NOT EXISTS fetch_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, started_at TEXT, finished_at TEXT,
  status TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS job_lock (name TEXT PRIMARY KEY, holder TEXT, expires_at TEXT);
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, created_at TEXT NOT NULL, event TEXT NOT NULL, origin TEXT, interest TEXT,
  params_json TEXT, market_json TEXT, summary_json TEXT);
"""


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self.conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def conn(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally:
            c.close()

    # ---------------- observations (HY OAS) ----------------
    def upsert_observations(self, series: str, rows: list, collected_at: str) -> int:
        """rows: [(obs_date, value_or_None, raw)]. Revised values replace old ones; no duplicates."""
        with self._lock, self.conn() as c:
            before = c.total_changes
            c.executemany(
                "INSERT INTO observations(series, obs_date, value, raw, collected_at) VALUES (?,?,?,?,?) "
                "ON CONFLICT(series, obs_date) DO UPDATE SET value=excluded.value, raw=excluded.raw, "
                "collected_at=excluded.collected_at WHERE observations.raw IS NOT excluded.raw",
                [(series, d, v, r, collected_at) for d, v, r in rows])
            return c.total_changes - before

    def observations(self, series: str, limit: int = 400) -> list:
        with self.conn() as c:
            return [dict(r) for r in c.execute(
                "SELECT obs_date, value, raw, collected_at FROM observations WHERE series=? "
                "ORDER BY obs_date DESC LIMIT ?", (series, limit))]

    # ---------------- GPU snapshots ----------------
    def insert_gpu_snapshot(self, snap: dict) -> bool:
        """One snapshot per (date, condition). Returns False if today's already exists."""
        with self._lock, self.conn() as c:
            cur = c.execute(
                "INSERT OR IGNORE INTO gpu_snapshots(snap_date, condition_key, condition_json, offer_count, "
                "median, p25, p75, min, max, median_dph_base, collected_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (snap["snap_date"], snap["condition_key"], json.dumps(snap["condition"], ensure_ascii=False, sort_keys=True),
                 snap["offer_count"], snap["median"], snap["p25"], snap["p75"], snap["min"], snap["max"],
                 snap.get("median_dph_base"), snap["collected_at"]))
            return cur.rowcount == 1

    def gpu_snapshots(self, condition_key: str, limit: int = 120) -> list:
        with self.conn() as c:
            rows = [dict(r) for r in c.execute(
                "SELECT * FROM gpu_snapshots WHERE condition_key=? ORDER BY snap_date DESC LIMIT ?",
                (condition_key, limit))]
        for r in rows:
            r["condition"] = json.loads(r.pop("condition_json"))
        return rows

    def has_gpu_snapshot(self, snap_date: str, condition_key: str) -> bool:
        with self.conn() as c:
            return c.execute("SELECT 1 FROM gpu_snapshots WHERE snap_date=? AND condition_key=?",
                             (snap_date, condition_key)).fetchone() is not None

    # ---------------- fetch state ----------------
    def get_state(self, source: str) -> dict:
        with self.conn() as c:
            r = c.execute("SELECT * FROM source_state WHERE source=?", (source,)).fetchone()
        if not r:
            return {"source": source, "last_attempt_at": None, "last_success_at": None,
                    "last_status": None, "last_detail": None, "meta": {}}
        d = dict(r)
        d["meta"] = json.loads(d.pop("meta_json") or "{}")
        return d

    def record_attempt(self, source: str, started: str, status: str, detail: str = "",
                       success: bool = False, meta: Optional[dict] = None) -> None:
        now = iso(utcnow())
        with self._lock, self.conn() as c:
            prev = c.execute("SELECT meta_json, last_success_at FROM source_state WHERE source=?", (source,)).fetchone()
            prev_meta = json.loads(prev["meta_json"]) if prev and prev["meta_json"] else {}
            if meta:
                prev_meta.update(meta)
            last_success = now if success else (prev["last_success_at"] if prev else None)
            c.execute(
                "INSERT INTO source_state(source, last_attempt_at, last_success_at, last_status, last_detail, meta_json) "
                "VALUES (?,?,?,?,?,?) ON CONFLICT(source) DO UPDATE SET last_attempt_at=excluded.last_attempt_at, "
                "last_success_at=excluded.last_success_at, last_status=excluded.last_status, "
                "last_detail=excluded.last_detail, meta_json=excluded.meta_json",
                (source, now, last_success, status, detail, json.dumps(prev_meta, ensure_ascii=False)))
            c.execute("INSERT INTO fetch_log(source, started_at, finished_at, status, detail) VALUES (?,?,?,?,?)",
                      (source, started, now, status, detail))

    # ---------------- cross-process job lock ----------------
    def acquire(self, name: str, ttl_sec: int = 300) -> Optional[str]:
        holder = uuid.uuid4().hex
        now = utcnow()
        with self._lock, self.conn() as c:
            c.execute("BEGIN IMMEDIATE")
            r = c.execute("SELECT holder, expires_at FROM job_lock WHERE name=?", (name,)).fetchone()
            if r and r["expires_at"] and datetime.fromisoformat(r["expires_at"]) > now:
                return None
            c.execute("INSERT INTO job_lock(name, holder, expires_at) VALUES (?,?,?) ON CONFLICT(name) DO UPDATE "
                      "SET holder=excluded.holder, expires_at=excluded.expires_at",
                      (name, holder, iso(now + timedelta(seconds=ttl_sec))))
            return holder

    def release(self, name: str, holder: str) -> None:
        with self._lock, self.conn() as c:
            c.execute("DELETE FROM job_lock WHERE name=? AND holder=?", (name, holder))

    # ---------------- runs ----------------
    def save_run(self, run: dict) -> dict:
        rid = run.get("id") or uuid.uuid4().hex[:12]
        created = run.get("created_at") or iso(utcnow())
        with self._lock, self.conn() as c:
            c.execute("INSERT OR REPLACE INTO runs(id, created_at, event, origin, interest, params_json, market_json, summary_json) "
                      "VALUES (?,?,?,?,?,?,?,?)",
                      (rid, created, run["event"], run.get("origin"), run.get("interest"),
                       json.dumps(run.get("params") or {}, ensure_ascii=False),
                       json.dumps(run.get("market") or {}, ensure_ascii=False),
                       json.dumps(run.get("summary") or {}, ensure_ascii=False)))
        return {**run, "id": rid, "created_at": created}

    def list_runs(self, limit: int = 20) -> list:
        with self.conn() as c:
            rows = [dict(r) for r in c.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,))]
        out = []
        for r in rows:
            out.append({"id": r["id"], "created_at": r["created_at"], "event": r["event"], "origin": r["origin"],
                        "interest": r["interest"], "params": json.loads(r["params_json"] or "{}"),
                        "market": json.loads(r["market_json"] or "{}"), "summary": json.loads(r["summary_json"] or "{}")})
        return out
