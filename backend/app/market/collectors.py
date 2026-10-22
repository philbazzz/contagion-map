"""Collectors: FRED HY OAS and Vast.ai GPU rental listings."""
from __future__ import annotations

import hashlib
import json
import statistics
import urllib.parse
from datetime import datetime, timedelta, timezone

from .config import Settings
from .http import FetchError, NoKey, BadResponse, request_json, urllib_transport
from .store import Store, iso, utcnow

KST = timezone(timedelta(hours=9))

HY_SERIES = "BAMLH0A0HYM2"
UST_10Y_SERIES = "DGS10"
UST_2Y_SERIES = "DGS2"
FRED_BASE = "https://api.stlouisfed.org/fred"
VAST_URL = "https://console.vast.ai/api/v0/bundles/"

# source_id → (FRED series_id, store as bp?, state key)
FRED_SERIES = {
    "hy_oas": (HY_SERIES, True),
    "ust_10y": (UST_10Y_SERIES, False),
    "ust_2y": (UST_2Y_SERIES, False),
}


def percent_to_bp(value_pct: float) -> float:
    """FRED reports the spread in percent. 1% = 100bp."""
    return round(value_pct * 100.0, 4)


def _collect_fred_series(
    source_id: str,
    series_id: str,
    as_bp: bool,
    settings: Settings,
    store: Store,
    transport=urllib_transport,
    sleep=None,
    meta_extra: dict | None = None,
) -> dict:
    started = iso(utcnow())
    try:
        if not settings.fred_api_key:
            raise NoKey("FRED_API_KEY가 설정되지 않았습니다")
        kw = dict(timeout=settings.http_timeout, retries=settings.http_retries, transport=transport)
        if sleep:
            kw["sleep"] = sleep
        q = {"series_id": series_id, "api_key": settings.fred_api_key, "file_type": "json"}
        meta = request_json("GET", f"{FRED_BASE}/series?{urllib.parse.urlencode(q)}", **kw)
        info = (meta.get("seriess") or [{}])[0]
        start = (utcnow() - timedelta(days=400)).date().isoformat()
        q2 = dict(q, observation_start=start, sort_order="asc")
        data = request_json("GET", f"{FRED_BASE}/series/observations?{urllib.parse.urlencode(q2)}", **kw)
        obs = data.get("observations")
        if obs is None:
            raise BadResponse("observations 항목 없음")
        rows = []
        for o in obs:
            raw = str(o.get("value", "."))
            try:
                if raw in (".", ""):
                    val = None
                else:
                    pct = float(raw)
                    val = percent_to_bp(pct) if as_bp else round(pct, 4)
            except ValueError:
                val = None
            rows.append((o["date"], val, raw))
        if not rows:
            store.record_attempt(source_id, started, "no_data", "제공처에서 받은 관측값이 없습니다")
            return {"status": "no_data"}
        changed = store.upsert_observations(series_id, rows, iso(utcnow()))
        extra = {
            "fred_last_updated": info.get("last_updated"),
            "fred_observation_start": info.get("observation_start"),
            "fred_observation_end": info.get("observation_end"),
            "units": info.get("units"),
            **(meta_extra or {}),
        }
        store.record_attempt(
            source_id, started, "ok",
            f"관측 {len(rows)}건 확인 · 신규/수정 {changed}건",
            success=True, meta=extra,
        )
        return {"status": "ok", "rows": len(rows), "changed": changed}
    except FetchError as e:
        store.record_attempt(source_id, started, e.code, e.detail)
        return {"status": e.code, "detail": e.detail}


# --------------------------------------------------------------------- FRED
def collect_hy_oas(settings: Settings, store: Store, transport=urllib_transport, sleep=None) -> dict:
    return _collect_fred_series(
        "hy_oas", HY_SERIES, True, settings, store, transport, sleep,
        meta_extra={"notes_restriction": "ICE Data: 내부 이용 한정, 재배포는 ICE 사전 승인 필요"},
    )


def collect_ust_10y(settings: Settings, store: Store, transport=urllib_transport, sleep=None) -> dict:
    return _collect_fred_series("ust_10y", UST_10Y_SERIES, False, settings, store, transport, sleep)


def collect_ust_2y(settings: Settings, store: Store, transport=urllib_transport, sleep=None) -> dict:
    return _collect_fred_series("ust_2y", UST_2Y_SERIES, False, settings, store, transport, sleep)


# --------------------------------------------------------------------- Vast.ai
def condition_key(cond: dict) -> str:
    keep = {k: cond[k] for k in sorted(cond) if k != "limit"}
    return hashlib.sha1(json.dumps(keep, sort_keys=True).encode()).hexdigest()[:12]


def build_vast_query(cond: dict) -> dict:
    q = {
        "limit": int(cond.get("limit", 500)),
        "type": cond.get("rental_type", "ondemand"),
        "rentable": {"eq": True},
        "rented": {"eq": False},
        "gpu_name": {"in": list(cond.get("gpu_name", ["H100 SXM"]))},
        "gpu_ram": {"gte": cond.get("min_gpu_ram_mb", 79000)},
        "num_gpus": {"gte": cond.get("num_gpus_min", 1), "lte": cond.get("num_gpus_max", 8)},
        "allocated_storage": cond.get("allocated_storage_gb", 1),
        "order": [["dph_total", "asc"]],
    }
    if cond.get("verified_only", True):
        q["verified"] = {"eq": True}
    region = cond.get("region", "ALL")
    if region and region != "ALL":
        q["geolocation"] = {"in": region if isinstance(region, list) else [region]}
    return q


def _quantile(sorted_vals: list, p: float) -> float:
    """Linear interpolation between closest ranks (same as numpy 'linear')."""
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * p
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def summarize_offers(offers: list, cond: dict) -> dict:
    """Normalise each offer to USD per GPU per hour and summarise.

    Re-checks the conditions locally so a looser API response can never mix
    products (e.g. PCIe vs SXM) or rental types.
    """
    names = set(cond.get("gpu_name", []))
    want_type = cond.get("rental_type", "ondemand")
    per_gpu, base_per_gpu = [], []
    for o in offers:
        n = o.get("num_gpus") or 0
        if n < cond.get("num_gpus_min", 1) or n > cond.get("num_gpus_max", 8):
            continue
        if names and o.get("gpu_name") not in names:
            continue
        if (o.get("gpu_ram") or 0) < cond.get("min_gpu_ram_mb", 0):
            continue
        if want_type == "bid":
            price = o.get("min_bid")
        else:
            if o.get("is_bid") is True:
                continue
            price = o.get("dph_total")
        if price is None or price <= 0:
            continue
        per_gpu.append(price / n)
        if o.get("dph_base"):
            base_per_gpu.append(o["dph_base"] / n)
    per_gpu.sort()
    base_per_gpu.sort()
    if not per_gpu:
        return {"offer_count": 0, "median": None, "p25": None, "p75": None, "min": None, "max": None,
                "median_dph_base": None}
    return {
        "offer_count": len(per_gpu),
        "median": round(statistics.median(per_gpu), 4),
        "p25": round(_quantile(per_gpu, 0.25), 4),
        "p75": round(_quantile(per_gpu, 0.75), 4),
        "min": round(per_gpu[0], 4),
        "max": round(per_gpu[-1], 4),
        "median_dph_base": round(statistics.median(base_per_gpu), 4) if base_per_gpu else None,
    }


def collect_gpu_rent(settings: Settings, store: Store, transport=urllib_transport, sleep=None, today=None) -> dict:
    started = iso(utcnow())
    cond = settings.gpu_condition
    key = condition_key(cond)
    snap_date = today or datetime.now(KST).date().isoformat()
    try:
        if not settings.vast_api_key:
            raise NoKey("VASTAI_API_KEY가 설정되지 않았습니다")
        if store.has_gpu_snapshot(snap_date, key):
            store.record_attempt("gpu_rent", started, "ok", "오늘 스냅샷이 이미 있어 다시 저장하지 않았습니다",
                                 success=True, meta={"condition_key": key})
            return {"status": "ok", "duplicate": True}
        kw = dict(timeout=settings.http_timeout, retries=settings.http_retries, transport=transport,
                  auth_statuses=(401, 403, 404))  # Vast.ai documents 404 for an invalid key
        if sleep:
            kw["sleep"] = sleep
        data = request_json("POST", VAST_URL, headers={"Authorization": f"Bearer {settings.vast_api_key}"},
                            payload=build_vast_query(cond), **kw)
        offers = data.get("offers") if isinstance(data, dict) else None
        if offers is None:
            raise BadResponse("offers 항목 없음")
        if isinstance(offers, dict):
            offers = [offers]
        summ = summarize_offers(offers, cond)
        if summ["offer_count"] == 0:
            store.record_attempt("gpu_rent", started, "no_data", "조건에 맞는 매물이 없습니다",
                                 meta={"condition_key": key})
            return {"status": "no_data"}
        snap = dict(summ, snap_date=snap_date, condition_key=key, condition=cond, collected_at=iso(utcnow()))
        inserted = store.insert_gpu_snapshot(snap)
        store.record_attempt("gpu_rent", started, "ok", f"매물 {summ['offer_count']}건 요약 저장", success=True,
                             meta={"condition_key": key})
        return {"status": "ok", "inserted": inserted, **summ}
    except FetchError as e:
        store.record_attempt("gpu_rent", started, e.code, e.detail, meta={"condition_key": key})
        return {"status": e.code, "detail": e.detail}
