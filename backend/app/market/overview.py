"""Builds the '시장 상황' payload, scheduler logic and the public (redistributable) snapshot."""
from __future__ import annotations

import asyncio
import logging
import threading
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from .collectors import (
    UST_10Y_SERIES, UST_2Y_SERIES, KST,
    collect_gpu_rent, collect_ust_10y, collect_ust_2y, condition_key,
)
from . import quotes as qt
from .config import Settings
from .store import Store, iso, utcnow

SOURCES = ("ust_10y", "ust_2y", "gpu_rent", "fx", "quotes_us", "quotes_krx")
FRED_COLLECTORS = {
    "ust_10y": collect_ust_10y,
    "ust_2y": collect_ust_2y,
}


def _network() -> dict:
    from ..service import load_network  # late import: service imports this module
    return load_network()

log = logging.getLogger("contagion.market")

STATUS_KO = {
    "ok": "정상",
    "weekend_or_holiday": "최신 발표값 (주말·휴일·발표 시차로 새 값 없음)",
    "missing_value": "최근 관측일 결측 (직전 유효값 표시)",
    "stale": "오래된 데이터",
    "fetch_failed": "갱신 실패 (마지막 정상값 유지)",
    "no_key": "API 키 미설정",
    "auth_error": "인증 오류",
    "rate_limited": "호출 한도 초과",
    "timeout": "응답 시간 초과",
    "network_error": "네트워크 오류",
    "bad_response": "제공처 응답 오류",
    "no_data": "자료 없음",
    "never": "아직 수집 안 함",
}


def _parse(ts: Optional[str]) -> Optional[datetime]:
    return datetime.fromisoformat(ts) if ts else None


def _business_days_between(d0: date, d1: date) -> int:
    """Weekdays strictly after d0 up to and including d1."""
    n, d = 0, d0
    while d < d1:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def _fred_yield_overview(
    store: Store,
    settings: Settings,
    *,
    source_id: str,
    series_id: str,
    name: str,
    plain: str,
    unit: str,
    unit_note: str,
    fred_url: str,
    caution: str,
    license_note: str | None = None,
    as_bp: bool = False,
    today: Optional[date] = None,
    provider_note: str | None = None,
) -> dict:
    today = today or datetime.now(KST).date()
    st = store.get_state(source_id)
    rows = store.observations(series_id, limit=400)  # newest first
    valid = [r for r in rows if r["value"] is not None]
    base = {
        "id": source_id,
        "name": name,
        "plain": plain,
        "unit": unit,
        "unit_note": unit_note,
        "source": {"name": f"FRED ({series_id})", "url": fred_url},
        "freshness_label": "최신 발표값 (실시간 아님 · 일별 종가 기준)",
        "caution": caution,
        "license": license_note,
        "last_attempt_at": st["last_attempt_at"], "last_success_at": st["last_success_at"],
        "last_error": None,
    }
    if not valid:
        code = st["last_status"] or ("no_key" if not settings.fred_api_key else "never")
        return {**base, "status": code if code != "ok" else "no_data", "status_ko": STATUS_KO.get(code, code),
                "latest": None, "detail": st["last_detail"]}
    latest, prev = valid[0], (valid[1] if len(valid) > 1 else None)
    obs_date = date.fromisoformat(latest["obs_date"])
    lag = _business_days_between(obs_date, today)
    if rows[0]["value"] is None:
        status = "missing_value"
    elif lag <= 1:
        status = "ok"
    elif lag <= 3:
        status = "weekend_or_holiday"
    else:
        status = "stale"
    last_error = None
    if st["last_status"] and st["last_status"] != "ok":
        last_error = {"code": st["last_status"], "label": STATUS_KO.get(st["last_status"]), "detail": st["last_detail"]}
        status = "fetch_failed"

    def change_vs(days: int):
        target = obs_date - timedelta(days=days)
        cand = [r for r in valid if date.fromisoformat(r["obs_date"]) <= target]
        if not cand:
            return {"status": "insufficient", "label": "이력 부족"}
        ref = cand[0]
        nd = 2 if as_bp else 3
        return {"status": "ok", "ref_date": ref["obs_date"], "ref_value": ref["value"],
                "change": round(latest["value"] - ref["value"], nd)}

    oldest = valid[-1]["obs_date"]
    nd = 2 if as_bp else 3
    return {
        **base,
        "status": status, "status_ko": STATUS_KO[status], "last_error": last_error,
        "latest": {"value": latest["value"], "obs_date": latest["obs_date"]},
        "previous": {"value": prev["value"], "obs_date": prev["obs_date"]} if prev else None,
        "change_vs_previous": round(latest["value"] - prev["value"], nd) if prev else None,
        "trend": {"d7": change_vs(7), "d30": change_vs(30)},
        "history": {"stored_from": oldest, "stored_to": latest["obs_date"], "stored_count": len(valid),
                    "provider_note": provider_note or "FRED 일별 관측값. 저장되지 않은 과거 값은 만들지 않습니다.",
                    "fred_meta": st["meta"]},
    }


def ust_10y_overview(store: Store, settings: Settings, today: Optional[date] = None) -> dict:
    return _fred_yield_overview(
        store, settings, today=today,
        source_id="ust_10y", series_id=UST_10Y_SERIES,
        name="미국 10년물 국채 금리",
        plain="장기 시장금리의 대표 벤치마크 (관측값 · 시나리오 가정이 아님)",
        unit="%", unit_note="FRED DGS10 · 연율 %",
        fred_url="https://fred.stlouisfed.org/series/DGS10",
        caution="관측된 시장 금리입니다. 좌측 시나리오의 가상 충격(+bp)과 혼동하지 마세요. SOFR 연동 차입 이자와 자동으로 같지 않습니다.",
        as_bp=False,
    )


def ust_2y_overview(store: Store, settings: Settings, today: Optional[date] = None) -> dict:
    return _fred_yield_overview(
        store, settings, today=today,
        source_id="ust_2y", series_id=UST_2Y_SERIES,
        name="미국 2년물 국채 금리",
        plain="단기·중기 시장금리의 벤치마크 (관측값 · 시나리오 가정이 아님)",
        unit="%", unit_note="FRED DGS2 · 연율 %",
        fred_url="https://fred.stlouisfed.org/series/DGS2",
        caution="관측된 시장 금리입니다. 가상 금리 충격 시나리오와 별개입니다.",
        as_bp=False,
    )


def gpu_overview(store: Store, settings: Settings, today: Optional[date] = None) -> dict:
    today = today or datetime.now(KST).date()
    cond = settings.gpu_condition
    key = condition_key(cond)
    st = store.get_state("gpu_rent")
    snaps = store.gpu_snapshots(key, limit=120)
    base = {
        "id": "gpu_rent",
        "name": "H100 GPU 임대 매물가",
        "plain": "온라인 GPU 임대 플랫폼에 올라온 H100 매물의 1장·1시간 가격",
        "unit": "USD / GPU·시간",
        "source": {"name": "Vast.ai 매물 조회 API (search offers)", "url": "https://docs.vast.ai/api-reference/search/search-offers"},
        "freshness_label": "최근 수집값 (하루 1회 스냅샷 · 실시간 아님)",
        "condition": cond,
        "condition_text": _condition_text(cond),
        "fee_note": "가격은 매물의 시간당 총액(dph_total)을 GPU 수로 나눈 값입니다. 최소 디스크(1GB) 저장비가 포함되며 네트워크 전송비는 제외됩니다.",
        "caution": "한 플랫폼의 매물 호가입니다. CoreWeave 실제 계약단가나 시장 전체 대표 가격이 아니며, 매물 수는 거래량·수요·가동률이 아닙니다. 비교 대상 매물 구성이 날마다 바뀌어 가격이 움직일 수 있습니다.",
        "last_attempt_at": st["last_attempt_at"], "last_success_at": st["last_success_at"], "last_error": None,
        "history_since": snaps[-1]["snap_date"] if snaps else None,
    }
    if not snaps:
        code = st["last_status"] or ("no_key" if not settings.vast_api_key else "never")
        return {**base, "status": code if code != "ok" else "no_data", "status_ko": STATUS_KO.get(code, code),
                "latest": None, "detail": st["last_detail"]}
    latest = snaps[0]
    prev = snaps[1] if len(snaps) > 1 else None
    age = (today - date.fromisoformat(latest["snap_date"])).days
    status = "ok" if age <= 1 else "stale"
    last_error = None
    if st["last_status"] and st["last_status"] != "ok":
        last_error = {"code": st["last_status"], "label": STATUS_KO.get(st["last_status"]), "detail": st["last_detail"]}
        status = "fetch_failed"

    def change_vs(days: int):
        target = date.fromisoformat(latest["snap_date"]) - timedelta(days=days)
        cand = [s for s in snaps if date.fromisoformat(s["snap_date"]) <= target]
        if not cand:
            return {"status": "insufficient", "label": "이력 부족"}
        ref = cand[0]
        return {"status": "ok", "ref_date": ref["snap_date"], "ref_value": ref["median"],
                "change": round(latest["median"] - ref["median"], 4),
                "change_pct": round((latest["median"] / ref["median"] - 1) * 100, 2) if ref["median"] else None}

    pick = lambda s: {k: s[k] for k in ("snap_date", "median", "p25", "p75", "min", "max", "offer_count", "median_dph_base", "collected_at")}  # noqa: E731
    return {
        **base, "status": status, "status_ko": STATUS_KO[status], "last_error": last_error,
        "latest": pick(latest), "previous": pick(prev) if prev else None,
        "change_vs_previous": round(latest["median"] - prev["median"], 4) if prev else None,
        "trend": {"d7": change_vs(7), "d30": change_vs(30)},
        "history": {"stored_count": len(snaps), "stored_from": snaps[-1]["snap_date"], "stored_to": latest["snap_date"],
                    "provider_note": "과거 가격 이력은 제공되지 않아 수집 시작일부터 직접 쌓습니다. 프로그램이 꺼져 있던 날은 비어 있습니다."},
    }


def _condition_text(c: dict) -> str:
    rtype = {"ondemand": "온디맨드(중단 없음)", "bid": "중단 가능(입찰형)", "reserved": "예약형"}.get(c.get("rental_type"), c.get("rental_type"))
    region = "전체 지역" if c.get("region", "ALL") == "ALL" else f"지역 {c.get('region')}"
    return (f"{', '.join(c.get('gpu_name', []))} · 메모리 {round(c.get('min_gpu_ram_mb', 0) / 1000)}GB급 이상 · {rtype} · "
            f"매물당 GPU {c.get('num_gpus_min')}~{c.get('num_gpus_max')}장 (1장 기준 환산) · "
            f"{'인증 호스트만' if c.get('verified_only', True) else '인증 무관'} · {region}")


class MarketService:
    def __init__(self, settings: Optional[Settings] = None, store: Optional[Store] = None, transport=None):
        self.settings = settings or Settings.load()
        self.store = store or Store(self.settings.db_path)
        self.transport = transport
        self._cache: Optional[tuple] = None
        self._run_lock = threading.Lock()
        self._last_manual: dict = {}

    # ----- read -----
    def overview(self, use_cache: bool = True) -> dict:
        now = time.time()
        if use_cache and self._cache and now - self._cache[0] < 60:
            return self._cache[1]
        data = {
            "generated_at": iso(utcnow()),
            "scheduler": {"enabled": self.settings.scheduler_enabled,
                          "note": "로컬 백엔드가 켜져 있는 동안에만 자동 수집됩니다. 꺼져 있던 기간은 수집되지 않습니다."},
            "indicators": [
                ust_10y_overview(self.store, self.settings),
                ust_2y_overview(self.store, self.settings),
                gpu_overview(self.store, self.settings),
            ],
            "usage_note": "시장 관측값(국채·주가)과 좌측 시나리오의 가상 금리 충격은 별개입니다. 관측값을 충격 bp에 자동 대입하지 않습니다.",
        }
        self._cache = (now, data)
        return data

    def public_snapshot(self) -> dict:
        """What may be embedded in the public HTML demo."""
        ov = self.overview(use_cache=False)
        return {"snapshot_at": ov["generated_at"], "auto_update": False, "indicators": ov["indicators"],
                "usage_note": ov["usage_note"]}

    def quotes(self) -> dict:
        # Pull US (yfinance) and Korean (FDR) closes into the SQLite cache when due — no API key required.
        for src in ("quotes_us", "quotes_krx"):
            try:
                if self.due(src):
                    self.collect(src)
            except Exception:  # noqa: BLE001 — never block the panel on a collect failure
                log.exception("%s collect on read failed", src)
        return qt.overview(self.store, self.settings, _network())

    def quote_history(self, entity_id: str, period: str) -> Optional[dict]:
        ent = next((n for n in _network()["nodes"] if n["id"] == entity_id), None)
        return qt.price_history(self.store, self.settings, ent, period) if ent else None

    def refresh_quotes(self) -> dict:
        """Manual refresh of FX and both quote sources (same 5-minute throttle as the indicators)."""
        res = self.manual_refresh_sources(("fx", "quotes_us", "quotes_krx"))
        quotes = self.quotes()
        return {"results": res, "quotes": self._annotate_quotes(quotes, res, ecosystem="semiconductor")}

    def refresh_pf_quotes(self) -> dict:
        """Collect observed quotes for the Korean AI DC PF company network and persist pf/quotes.json."""
        import json
        from pathlib import Path

        root = Path(__file__).resolve().parents[3]  # repo root (backend/app/market → ../../..)
        pf_net_path = root / "frontend" / "public" / "data" / "pf" / "network.json"
        out_path = root / "frontend" / "public" / "data" / "pf" / "quotes.json"
        if not pf_net_path.is_file():
            return {
                "results": {"pf_network": {"status": "missing", "detail": str(pf_net_path)}},
                "quotes": {
                    "generated_at": iso(utcnow()),
                    "retrieved_at": iso(utcnow()),
                    "ecosystem": "datacenter_pf",
                    "items": [],
                    "fx": {"source": "", "rates": {}},
                    "providers": {},
                    "keys": {},
                    "note": "PF network.json 없음",
                    "refresh_status": "error",
                    "refresh_detail": "frontend/public/data/pf/network.json 을 찾을 수 없습니다",
                },
            }

        net = json.loads(pf_net_path.read_text(encoding="utf-8"))
        tg = qt.targets(net)
        res: dict = {}
        # Separate throttle so PF refresh does not block semiconductor (and vice versa).
        prefix = "pf:"
        for src, run in (
            ("fx", lambda: self.collect("fx")),
            ("quotes_us", lambda: qt.collect_us_quotes(self.settings, self.store, tg.get("us") or [])),
            ("quotes_krx", lambda: qt.collect_krx(self.settings, self.store, tg.get("krx") or [])),
        ):
            key = f"{prefix}{src}"
            if time.time() - self._last_manual.get(key, 0) < self.settings.manual_refresh_min_interval_sec:
                res[src] = {"status": "throttled", "detail": "수동 갱신은 5분에 한 번만 가능합니다"}
                continue
            self._last_manual[key] = time.time()
            try:
                res[src] = run()
            except Exception as e:  # noqa: BLE001
                log.exception("PF %s collect failed", src)
                res[src] = {"status": "error", "detail": str(e)}
        # Always rebuild overview from PF nodes (even if collect was throttled — surfaces last store).
        quotes = qt.overview(self.store, self.settings, net)
        quotes["ecosystem"] = "datacenter_pf"
        quotes["static"] = False
        quotes["demo"] = False
        priced = sum(1 for i in quotes.get("items") or [] if i.get("price") is not None)
        listed = sum(1 for i in quotes.get("items") or [] if i.get("listed"))
        quotes["note"] = (
            f"AI Data Center PF 관측 시세 ({priced}/{listed} 상장사 가격). "
            "미국: yfinance 일간 종가 · 한국: FinanceDataReader/yfinance (KRX). "
            "결측은 비워 두며 0이나 모회사 시세로 대체하지 않습니다."
        )
        quotes = self._annotate_quotes(quotes, res, ecosystem="datacenter_pf")
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(quotes, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:  # noqa: BLE001
            quotes["refresh_detail"] = (quotes.get("refresh_detail") or "") + f" · 파일 저장 실패: {e}"
        return {"results": res, "quotes": quotes}

    @staticmethod
    def _annotate_quotes(quotes: dict, res: dict, *, ecosystem: str) -> dict:
        """Attach retrieval metadata so the UI can distinguish fetch time vs quote market time."""
        quotes = dict(quotes)
        quotes["ecosystem"] = ecosystem
        quotes["retrieved_at"] = iso(utcnow())
        statuses = [v.get("status") for v in (res or {}).values() if isinstance(v, dict)]
        if statuses and all(s == "throttled" for s in statuses):
            quotes["refresh_status"] = "throttled"
            quotes["refresh_detail"] = "수동 갱신 간격 제한 — 직전 수집 시세를 유지합니다. 가격 변동이 없어도 실패가 아닙니다."
        elif statuses and any(s in ("ok", "partial", "success") for s in statuses):
            failed = [k for k, v in (res or {}).items() if isinstance(v, dict) and v.get("status") not in ("ok", "partial", "success", "throttled", "skip")]
            if failed:
                quotes["refresh_status"] = "partial"
                quotes["refresh_detail"] = f"일부 소스 실패: {', '.join(failed)}. 성공한 종목만 갱신됐을 수 있습니다."
            else:
                quotes["refresh_status"] = "ok"
                quotes["refresh_detail"] = "조회 완료. 장 마감·휴장이면 종가가 이전과 같을 수 있습니다."
        elif statuses and any(s == "throttled" for s in statuses):
            quotes["refresh_status"] = "partial"
            quotes["refresh_detail"] = "일부 소스는 갱신, 일부는 간격 제한으로 직전 값을 유지합니다."
        else:
            quotes["refresh_status"] = "error" if statuses else "ok"
            quotes["refresh_detail"] = "수집 결과를 확인하세요." if statuses else "캐시된 시세를 반환했습니다."
        quotes["refresh_results"] = res
        return quotes

    def manual_refresh_sources(self, sources, throttle_key: str | None = None) -> dict:
        res = {}
        prefix = f"{throttle_key}:" if throttle_key else ""
        for s in sources:
            key = f"{prefix}{s}"
            if time.time() - self._last_manual.get(key, 0) < self.settings.manual_refresh_min_interval_sec:
                res[s] = {"status": "throttled", "detail": "수동 갱신은 5분에 한 번만 가능합니다"}
                continue
            self._last_manual[key] = time.time()
            res[s] = self.collect(s)
        return res

    def _fx_gaps(self, us_symbols: list) -> list:
        """Dates in the stored US price history that have no KRW rate yet (newest first)."""
        qt.ensure_schema(self.store)
        with self.store.conn() as c:
            rows = c.execute("SELECT DISTINCT obs_date FROM price_history WHERE currency!='KRW' AND obs_date NOT IN "
                             "(SELECT obs_date FROM fx_rates WHERE currency='USD') ORDER BY obs_date DESC LIMIT 60").fetchall()
        return [r["obs_date"] for r in rows]

    # ----- collection -----
    def due(self, source: str) -> bool:
        st = self.store.get_state(source)
        now = utcnow()
        hours = {"ust_10y": self.settings.hy_refresh_hours,
                 "ust_2y": self.settings.hy_refresh_hours, "gpu_rent": self.settings.gpu_refresh_hours,
                 "fx": self.settings.fx_refresh_hours, "quotes_krx": self.settings.krx_refresh_hours,
                 "quotes_us": self.settings.us_quote_refresh_min / 60.0}[source]
        last_ok = _parse(st["last_success_at"])
        last_try = _parse(st["last_attempt_at"])
        if last_try and st["last_status"] != "ok" and now - last_try < timedelta(minutes=self.settings.retry_after_failure_min):
            return False
        if source == "gpu_rent":
            today = datetime.now(KST).date().isoformat()
            if self.store.has_gpu_snapshot(today, condition_key(self.settings.gpu_condition)):
                return False
        return last_ok is None or now - last_ok >= timedelta(hours=hours)

    def collect(self, source: str) -> dict:
        kw = {"transport": self.transport} if self.transport else {}
        holder = self.store.acquire(f"collect:{source}", ttl_sec=120)
        if not holder:
            return {"status": "busy", "detail": "다른 수집 작업이 실행 중입니다"}
        try:
            if source in FRED_COLLECTORS:
                res = FRED_COLLECTORS[source](self.settings, self.store, **kw)
            elif source == "gpu_rent":
                res = collect_gpu_rent(self.settings, self.store, **kw)
            else:
                tg = qt.targets(_network())
                if source == "quotes_us":
                    res = qt.collect_us_quotes(self.settings, self.store, tg.get("us") or tg.get("finnhub") or [], **kw)
                elif source == "quotes_krx":
                    res = qt.collect_krx(self.settings, self.store, tg["krx"], **kw)
                else:
                    res = qt.collect_fx(self.settings, self.store, backfill_dates=self._fx_gaps(tg.get("us") or tg.get("finnhub") or []), **kw)
        finally:
            self.store.release(f"collect:{source}", holder)
        self._cache = None
        log.info("market collect %s -> %s", source, res.get("status"))
        return res

    def run_due(self) -> dict:
        if not self._run_lock.acquire(blocking=False):
            return {"skipped": "already running"}
        try:
            return {s: self.collect(s) for s in SOURCES if self.due(s)}
        finally:
            self._run_lock.release()

    def manual_refresh(self, source: Optional[str] = None) -> dict:
        res = {}
        for s in ([source] if source else list(SOURCES)):
            last = self._last_manual.get(s, 0)
            if time.time() - last < self.settings.manual_refresh_min_interval_sec:
                res[s] = {"status": "throttled", "detail": "수동 갱신은 5분에 한 번만 가능합니다"}
                continue
            self._last_manual[s] = time.time()
            res[s] = self.collect(s)
        return {"results": res, "overview": self.overview(use_cache=False)}

    # ----- schedulers -----
    async def run_forever(self) -> None:
        """Async loop for FastAPI: checks on startup, then every check_interval_sec."""
        while True:
            try:
                await asyncio.to_thread(self.run_due)
            except Exception:  # never let the loop die
                log.exception("market scheduler error")
            await asyncio.sleep(self.settings.check_interval_sec)

    def start_thread(self) -> threading.Thread:
        """Thread loop for the stdlib fallback server."""
        def loop():
            while True:
                try:
                    self.run_due()
                except Exception:
                    log.exception("market scheduler error")
                time.sleep(self.settings.check_interval_sec)
        t = threading.Thread(target=loop, daemon=True, name="market-scheduler")
        t.start()
        return t
