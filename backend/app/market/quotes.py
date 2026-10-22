"""Listed-company share prices and KRW conversion (MARKET VIEW).

Providers:
  * yfinance           US-listed tickers (NYSE / Nasdaq) — primary, no API key (batch download).
  * Finnhub            Optional US fallback when FINNHUB_API_KEY is set (or unit-test transports).
  * FinanceDataReader  KOSPI / KOSDAQ daily close — preferred for Korean stocks, no API key.
  * yfinance           Lightweight fallback for Korean codes if FDR fails (no API key).
  * 금융위원회_주식시세정보 Optional legacy KRX path when DATA_GO_KR_SERVICE_KEY is set and FDR/yf fail.
  * 한국수출입은행 환율    KRW FX for US prices (optional key).

Rules
  * A price is only ever a stored provider observation. If a call fails, the last good value stays with
    its own timestamp and the error is shown; no number is invented.
  * KRW value = local price x KRW rate of that currency. Price time and FX date are reported separately.
  * Past KRW prices use the FX rate of each date; a date without a stored rate is left out, never filled.
  * Market quotes are observed prices — never derived from interest-rate shock scenarios.
  * Korean quotes are daily closes — never labelled as realtime.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from .config import Settings
from .http import BadResponse, FetchError, NoKey, request_json, urllib_transport
from .store import Store, iso, utcnow

log = logging.getLogger("contagion.quotes")

KST = timezone(timedelta(hours=9))
FINNHUB_BASE = "https://finnhub.io/api/v1"
KRX_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"
EXIM_URL = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
US_EXCHANGES = ("NYSE", "Nasdaq", "NASDAQ")
# KRX = umbrella label used by PF dataset; treat like KOSPI/KOSDAQ for FDR/yfinance.
KR_EXCHANGES = ("KOSPI", "KOSDAQ", "KRX")
FX_CURRENCIES = ("USD", "JPY", "EUR", "GBP", "CNH", "HKD", "TWD")  # TWD is not published by Eximbank today

SCHEMA = """
CREATE TABLE IF NOT EXISTS quotes (
  symbol TEXT PRIMARY KEY, provider TEXT NOT NULL, currency TEXT, price REAL, change REAL, change_pct REAL,
  prev_close REAL, day_high REAL, day_low REAL, market_cap REAL, market_cap_currency TEXT, price_time TEXT,
  basis TEXT, collected_at TEXT NOT NULL, raw TEXT);
CREATE TABLE IF NOT EXISTS price_history (
  symbol TEXT NOT NULL, obs_date TEXT NOT NULL, close REAL NOT NULL, currency TEXT, provider TEXT,
  collected_at TEXT NOT NULL, PRIMARY KEY (symbol, obs_date));
CREATE TABLE IF NOT EXISTS fx_rates (
  obs_date TEXT NOT NULL, currency TEXT NOT NULL, krw_per_unit REAL NOT NULL, raw TEXT, collected_at TEXT NOT NULL,
  PRIMARY KEY (obs_date, currency));
CREATE TABLE IF NOT EXISTS quote_errors (
  symbol TEXT PRIMARY KEY, provider TEXT, code TEXT, detail TEXT, at TEXT);
"""

DELAY = {
    "yfinance": ("close", "yfinance 일간 종가 · 실시간 시세 아님 · 거래소 공식 통합시세 아님"),
    "finnhub": ("realtime", "제공처 표기 '실시간' 미국 시세 · 앱은 15분마다 조회 (최대 15분 지연) · 거래소 공식 통합시세 아님"),
    "fdr": ("close", "KRX 일간 종가 (FinanceDataReader) · 실시간 시세 아님 · 장 마감 후 확인 가능한 마지막 종가"),
    "krx": ("close", "KRX 일간 종가 · 금융위원회 OpenAPI · 기준일 다음 영업일 13시 이후 공개"),
}

SOURCE_META = {
    "yfinance": {"name": "yfinance (Yahoo Finance 일간 종가)", "url": "https://github.com/ranaroussi/yfinance"},
    "finnhub": {"name": "Finnhub", "url": "https://finnhub.io/docs/api/quote"},
    "fdr": {"name": "FinanceDataReader (KRX 일간 종가)", "url": "https://github.com/FinanceData/FinanceDataReader"},
    "krx": {"name": "금융위원회_주식시세정보 (KRX)", "url": "https://www.data.go.kr/data/15094808/openapi.do"},
}


def ensure_schema(store: Store) -> None:
    with store.conn() as c:
        c.executescript(SCHEMA)


# ------------------------------------------------------------------ coverage
def coverage(entity: dict) -> dict:
    """Which provider (if any) can price this entity, and why not otherwise."""
    if not entity.get("listed"):
        return {"provider": None, "status": "unlisted", "status_ko": "비상장", "symbol": None}
    ex = entity.get("exchange") or ""
    tk = entity.get("ticker")
    if ex in US_EXCHANGES and tk:
        return {"provider": "yfinance", "status": "pending", "status_ko": "조회 전", "symbol": tk}
    if ex in KR_EXCHANGES and tk:
        # Stored rows may come from fdr / yfinance / krx; collection prefers FDR.
        return {"provider": "fdr", "status": "pending", "status_ko": "조회 전", "symbol": str(tk).zfill(6)}
    return {"provider": None, "status": "not_supported", "symbol": tk,
            "status_ko": f"{ex} 상장 — 연동한 무료 제공처 미지원 (미국·한국만)"}


def targets(net: dict) -> Dict[str, List[str]]:
    """Buckets for collectors. ``us`` = NYSE/Nasdaq tickers; ``krx`` = Korean codes."""
    out: Dict[str, List[str]] = {"us": [], "krx": [], "finnhub": []}  # finnhub kept as alias of us for older callers
    for n in net["nodes"]:
        cv = coverage(n)
        if not cv["provider"] or not cv["symbol"]:
            continue
        if cv["provider"] in ("fdr",) or (n.get("exchange") in KR_EXCHANGES):
            bucket = "krx"
        else:
            bucket = "us"
        if cv["symbol"] not in out[bucket]:
            out[bucket].append(cv["symbol"])
    out["finnhub"] = list(out["us"])  # backward-compatible alias
    return out


# ------------------------------------------------------------------ store helpers
def _save_quote(store: Store, q: dict) -> None:
    with store._lock, store.conn() as c:
        c.execute(
            "INSERT INTO quotes(symbol, provider, currency, price, change, change_pct, prev_close, day_high, day_low, "
            "market_cap, market_cap_currency, price_time, basis, collected_at, raw) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(symbol) DO UPDATE SET provider=excluded.provider, currency=excluded.currency, price=excluded.price, "
            "change=excluded.change, change_pct=excluded.change_pct, prev_close=excluded.prev_close, day_high=excluded.day_high, "
            "day_low=excluded.day_low, market_cap=COALESCE(excluded.market_cap, quotes.market_cap), "
            "market_cap_currency=COALESCE(excluded.market_cap_currency, quotes.market_cap_currency), "
            "price_time=excluded.price_time, basis=excluded.basis, collected_at=excluded.collected_at, raw=excluded.raw",
            (q["symbol"], q["provider"], q["currency"], q["price"], q.get("change"), q.get("change_pct"), q.get("prev_close"),
             q.get("day_high"), q.get("day_low"), q.get("market_cap"), q.get("market_cap_currency"), q.get("price_time"),
             q["basis"], q["collected_at"], json.dumps(q.get("raw"), ensure_ascii=False)))
        c.execute("DELETE FROM quote_errors WHERE symbol=?", (q["symbol"],))


def _save_history(store: Store, symbol: str, rows: list, currency: str, provider: str) -> int:
    now = iso(utcnow())
    with store._lock, store.conn() as c:
        before = c.total_changes
        c.executemany("INSERT INTO price_history(symbol, obs_date, close, currency, provider, collected_at) VALUES (?,?,?,?,?,?) "
                      "ON CONFLICT(symbol, obs_date) DO UPDATE SET close=excluded.close, collected_at=excluded.collected_at",
                      [(symbol, d, v, currency, provider, now) for d, v in rows if v is not None and v > 0])
        return c.total_changes - before


def _save_error(store: Store, symbol: str, provider: str, e: FetchError) -> None:
    with store._lock, store.conn() as c:
        c.execute("INSERT INTO quote_errors(symbol, provider, code, detail, at) VALUES (?,?,?,?,?) ON CONFLICT(symbol) DO UPDATE "
                  "SET provider=excluded.provider, code=excluded.code, detail=excluded.detail, at=excluded.at",
                  (symbol, provider, e.code, e.detail, iso(utcnow())))


def get_quote(store: Store, symbol: str) -> Optional[dict]:
    with store.conn() as c:
        r = c.execute("SELECT * FROM quotes WHERE symbol=?", (symbol,)).fetchone()
    return dict(r) if r else None


def get_error(store: Store, symbol: str) -> Optional[dict]:
    with store.conn() as c:
        r = c.execute("SELECT * FROM quote_errors WHERE symbol=?", (symbol,)).fetchone()
    return dict(r) if r else None


def latest_fx(store: Store, currency: str, on_or_before: Optional[str] = None) -> Optional[dict]:
    q = "SELECT obs_date, krw_per_unit FROM fx_rates WHERE currency=?" + (" AND obs_date<=?" if on_or_before else "") + \
        " ORDER BY obs_date DESC LIMIT 1"
    with store.conn() as c:
        r = c.execute(q, (currency, on_or_before) if on_or_before else (currency,)).fetchone()
    return dict(r) if r else None


def fx_on(store: Store, currency: str, d: str) -> Optional[float]:
    with store.conn() as c:
        r = c.execute("SELECT krw_per_unit FROM fx_rates WHERE currency=? AND obs_date=?", (currency, d)).fetchone()
    return r["krw_per_unit"] if r else None


def history(store: Store, symbol: str, since: str) -> list:
    with store.conn() as c:
        return [dict(r) for r in c.execute("SELECT obs_date, close, currency FROM price_history WHERE symbol=? AND obs_date>=? "
                                           "ORDER BY obs_date", (symbol, since))]


# ------------------------------------------------------------------ parsing helpers
def _num(s) -> Optional[float]:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    t = str(s).replace(",", "").strip()
    if t in ("", "-", "."):
        return None
    try:
        return float(t)
    except ValueError:
        return None


try:
    from zoneinfo import ZoneInfo
    _NY = ZoneInfo("America/New_York")
except Exception:  # tzdata missing (some Windows Pythons): fixed EST offset, off by one hour in summer only
    _NY = timezone(timedelta(hours=-5))


def _us_trade_date(ts: Optional[float]) -> Optional[str]:
    """Exchange-local (New York) trading date of a Finnhub quote timestamp."""
    if not ts:
        return None
    return datetime.fromtimestamp(ts, timezone.utc).astimezone(_NY).date().isoformat()


# ------------------------------------------------------------------ collectors
def _bars_to_us_quote(symbol: str, hist: List[Tuple[str, float]], provider: str = "yfinance",
                      highs: Optional[List[float]] = None, lows: Optional[List[float]] = None) -> dict:
    """Build a USD quote row from daily close bars (last = latest close)."""
    if len(hist) < 1:
        raise BadResponse("시세 행 없음")
    hist = [(d, c) for d, c in hist if c is not None and c > 0]
    if not hist:
        raise BadResponse("유효 종가 없음")
    last_d, last_c = hist[-1]
    prev_c = hist[-2][1] if len(hist) >= 2 else None
    change = (last_c - prev_c) if prev_c is not None else None
    change_pct = (change / prev_c * 100.0) if prev_c and change is not None else None
    return {
        "symbol": symbol, "provider": provider, "currency": "USD", "price": last_c,
        "change": change, "change_pct": change_pct, "prev_close": prev_c,
        "day_high": highs[-1] if highs else None, "day_low": lows[-1] if lows else None,
        "market_cap": None, "market_cap_currency": "USD",
        "price_time": last_d, "basis": "close", "collected_at": iso(utcnow()),
        "raw": {"bars": len(hist), "as_of": last_d},
    }


def _fetch_yfinance_us_batch(symbols: List[str], days: int = 10) -> Dict[str, Tuple[dict, List[Tuple[str, float]]]]:
    """Batch-download US daily bars via yfinance. Returns symbol → (quote, history bars)."""
    try:
        import yfinance as yf
    except ImportError as e:
        raise BadResponse(f"yfinance 미설치: {e}") from e
    if not symbols:
        return {}
    period = f"{max(days, 5)}d"
    try:
        raw = yf.download(
            symbols, period=period, group_by="ticker", auto_adjust=True,
            threads=True, progress=False, timeout=30,
        )
    except Exception as e:  # noqa: BLE001
        raise BadResponse(f"yfinance 일괄 조회 실패: {e}") from e
    if raw is None or getattr(raw, "empty", True):
        raise BadResponse("yfinance 빈 응답")

    out: Dict[str, Tuple[dict, List[Tuple[str, float]]]] = {}
    multi = hasattr(raw.columns, "levels") and len(getattr(raw.columns, "levels", [])) >= 2
    for sym in symbols:
        try:
            if multi:
                if sym not in raw.columns.get_level_values(0):
                    continue
                sub = raw[sym].dropna(how="all")
            else:
                sub = raw.dropna(how="all") if len(symbols) == 1 else None
            if sub is None or getattr(sub, "empty", True) or "Close" not in sub.columns:
                continue
            hist: List[Tuple[str, float]] = []
            highs: List[float] = []
            lows: List[float] = []
            for idx, row in sub.iterrows():
                try:
                    d = idx.tz_convert("America/New_York").date().isoformat() if getattr(idx, "tzinfo", None) else (
                        idx.date().isoformat() if hasattr(idx, "date") else str(idx)[:10])
                    close = float(row["Close"])
                    hist.append((d, close))
                    if "High" in sub.columns and row["High"] == row["High"]:
                        highs.append(float(row["High"]))
                    if "Low" in sub.columns and row["Low"] == row["Low"]:
                        lows.append(float(row["Low"]))
                except (TypeError, ValueError, AttributeError):
                    continue
            if hist:
                out[sym] = (_bars_to_us_quote(sym, hist, "yfinance", highs or None, lows or None), hist)
        except Exception as e:  # noqa: BLE001 — one symbol must not abort the batch
            log.info("yfinance US parse %s failed: %s", sym, e)
    return out


def _collect_us_finnhub(settings: Settings, store: Store, symbols: List[str], transport=urllib_transport,
                        sleep=None, with_profile: bool = True) -> dict:
    """Legacy Finnhub path (unit tests with Fake transport, or optional live key fallback)."""
    ensure_schema(store)
    started = iso(utcnow())
    if not settings.finnhub_api_key:
        store.record_attempt("quotes_us", started, "no_key", "FINNHUB_API_KEY가 설정되지 않았습니다")
        return {"status": "no_key", "ok": 0, "failed": {}}
    hdr = {"X-Finnhub-Token": settings.finnhub_api_key}
    kw = dict(timeout=settings.http_timeout, retries=settings.http_retries, transport=transport)
    if sleep:
        kw["sleep"] = sleep
    ok, failed = 0, {}
    for sym in symbols:
        try:
            q = request_json("GET", f"{FINNHUB_BASE}/quote?symbol={sym}", headers=hdr, **kw)
            price = _num(q.get("c")) if isinstance(q, dict) else None
            if not price:
                raise BadResponse("시세 없음 (종목 미지원 또는 거래 정지)")
            mc = mcc = None
            if with_profile:
                try:
                    pr = request_json("GET", f"{FINNHUB_BASE}/stock/profile2?symbol={sym}", headers=hdr, **kw)
                    if isinstance(pr, dict) and _num(pr.get("marketCapitalization")):
                        mc, mcc = _num(pr["marketCapitalization"]), pr.get("marketCapCurrency") or pr.get("currency") or "USD"
                except FetchError:
                    pass
            t = q.get("t")
            rec = {"symbol": sym, "provider": "finnhub", "currency": "USD", "price": price, "change": _num(q.get("d")),
                   "change_pct": _num(q.get("dp")), "prev_close": _num(q.get("pc")), "day_high": _num(q.get("h")),
                   "day_low": _num(q.get("l")), "market_cap": mc, "market_cap_currency": mcc,
                   "price_time": iso(datetime.fromtimestamp(t, timezone.utc)) if t else None,
                   "basis": "realtime", "collected_at": iso(utcnow()), "raw": q}
            _save_quote(store, rec)
            d = _us_trade_date(t)
            if d:
                _save_history(store, sym, [(d, price)], "USD", "finnhub")
            ok += 1
        except FetchError as e:
            _save_error(store, sym, "finnhub", e)
            failed[sym] = e.code
            if e.code in ("auth_error", "rate_limited"):
                break
    status = "ok" if ok and not failed else ("partial" if ok else (next(iter(failed.values())) if failed else "no_data"))
    store.record_attempt("quotes_us", started, status, f"Finnhub 성공 {ok} · 실패 {len(failed)}", success=ok > 0)
    return {"status": status, "ok": ok, "failed": failed}


def collect_us_quotes(settings: Settings, store: Store, symbols: List[str], transport=urllib_transport,
                      sleep=None, with_profile: bool = True) -> dict:
    """US listed closes via yfinance (no API key). Finnhub only when a test transport or live key fallback is needed."""
    ensure_schema(store)
    started = iso(utcnow())
    symbols = [s for s in symbols if s]

    # Unit tests inject a Fake transport and exercise the Finnhub parser.
    if transport is not urllib_transport:
        return _collect_us_finnhub(settings, store, symbols, transport=transport, sleep=sleep, with_profile=with_profile)

    ok, failed = 0, {}
    try:
        batch = _fetch_yfinance_us_batch(symbols, days=30)
    except FetchError as e:
        if settings.finnhub_api_key:
            log.info("yfinance US batch failed (%s); trying Finnhub", e.detail)
            return _collect_us_finnhub(settings, store, symbols, with_profile=with_profile)
        store.record_attempt("quotes_us", started, e.code, e.detail)
        return {"status": e.code, "ok": 0, "failed": {s: e.code for s in symbols}, "detail": e.detail}

    for sym in symbols:
        pair = batch.get(sym)
        if not pair:
            e = BadResponse("yfinance 시세 없음")
            _save_error(store, sym, "yfinance", e)
            failed[sym] = e.code
            continue
        rec, hist = pair
        _save_quote(store, rec)
        _save_history(store, sym, hist, "USD", "yfinance")
        ok += 1

    missing = [s for s in symbols if s in failed]
    if missing and settings.finnhub_api_key:
        r2 = _collect_us_finnhub(settings, store, missing, with_profile=with_profile)
        for s in list(failed):
            if s not in (r2.get("failed") or {}):
                failed.pop(s, None)
                ok += 1

    status = "ok" if ok and not failed else ("partial" if ok else (next(iter(failed.values())) if failed else "no_data"))
    store.record_attempt("quotes_us", started, status,
                         f"yfinance 성공 {ok} · 실패 {len(failed)}", success=ok > 0)
    return {"status": status, "ok": ok, "failed": failed}


def _bars_to_quote(code: str, hist: List[Tuple[str, float]], provider: str, extra: Optional[dict] = None) -> dict:
    """Build a cached quote row from (date, close) bars — last bar is the latest close."""
    if len(hist) < 1:
        raise BadResponse("시세 행 없음")
    hist = [(d, c) for d, c in hist if c is not None and c > 0]
    if not hist:
        raise BadResponse("유효 종가 없음")
    last_d, last_c = hist[-1]
    prev_c = hist[-2][1] if len(hist) >= 2 else None
    change = (last_c - prev_c) if prev_c is not None else None
    change_pct = (change / prev_c * 100.0) if prev_c and change is not None else None
    return {
        "symbol": code, "provider": provider, "currency": "KRW", "price": last_c,
        "change": change, "change_pct": change_pct, "prev_close": prev_c,
        "day_high": None, "day_low": None, "market_cap": None, "market_cap_currency": "KRW",
        "price_time": last_d, "basis": "close", "collected_at": iso(utcnow()),
        "raw": {"bars": len(hist), **(extra or {})},
    }


def _fetch_fdr_history(code: str, days: int = 400) -> List[Tuple[str, float]]:
    """FinanceDataReader daily OHLCV → [(YYYY-MM-DD, close), ...]."""
    try:
        import FinanceDataReader as fdr
    except ImportError as e:
        raise BadResponse(f"FinanceDataReader 미설치: {e}") from e
    end = datetime.now(KST).date()
    start = end - timedelta(days=max(days, 14))
    try:
        df = fdr.DataReader(code, start.isoformat(), end.isoformat())
    except Exception as e:  # noqa: BLE001 — library raises various errors
        raise BadResponse(f"FinanceDataReader 조회 실패: {e}") from e
    if df is None or getattr(df, "empty", True):
        raise BadResponse("FinanceDataReader 빈 응답")
    if "Close" not in df.columns:
        raise BadResponse("Close 열 없음")
    out: List[Tuple[str, float]] = []
    for idx, row in df.iterrows():
        try:
            d = idx.date().isoformat() if hasattr(idx, "date") else str(idx)[:10]
            out.append((d, float(row["Close"])))
        except (TypeError, ValueError):
            continue
    return out


def _fetch_yfinance_history(code: str, days: int = 60) -> List[Tuple[str, float]]:
    """yfinance fallback for KRX (symbol.KS). Verified for 005930 / 000660."""
    try:
        import yfinance as yf
    except ImportError as e:
        raise BadResponse(f"yfinance 미설치: {e}") from e
    sym = f"{code}.KS"
    try:
        df = yf.Ticker(sym).history(period=f"{max(days, 10)}d")
    except Exception as e:  # noqa: BLE001
        raise BadResponse(f"yfinance 조회 실패: {e}") from e
    if df is None or getattr(df, "empty", True):
        raise BadResponse("yfinance 빈 응답")
    out: List[Tuple[str, float]] = []
    for idx, row in df.iterrows():
        try:
            d = idx.tz_convert("Asia/Seoul").date().isoformat() if getattr(idx, "tzinfo", None) else idx.date().isoformat()
            out.append((d, float(row["Close"])))
        except (TypeError, ValueError, AttributeError):
            continue
    return out


def collect_krx(settings: Settings, store: Store, codes: List[str], transport=urllib_transport, sleep=None,
                days: int = 400) -> dict:
    """Korean daily closes: FinanceDataReader → yfinance → optional data.go.kr (if key set).

    When a custom ``transport`` is injected (unit tests), use the legacy OpenAPI path only.
    """
    ensure_schema(store)
    started = iso(utcnow())
    codes = [str(c).zfill(6) for c in codes]

    # Unit tests inject a Fake transport and exercise the legacy OpenAPI parser.
    if transport is not urllib_transport:
        return _collect_krx_datago(settings, store, codes, transport=transport, sleep=sleep, days=days, started=started)

    ok, failed = 0, {}
    for code in codes:
        saved = False
        last_err: Optional[FetchError] = None
        for provider in ("fdr", "yfinance"):
            try:
                hist = (_fetch_fdr_history(code, days) if provider == "fdr"
                        else _fetch_yfinance_history(code, min(days, 90)))
                _save_history(store, code, hist, "KRW", provider)
                _save_quote(store, _bars_to_quote(code, hist, provider))
                ok += 1
                saved = True
                break
            except FetchError as e:
                last_err = e
                log.info("KRX %s via %s failed: %s", code, provider, e.detail)
        if not saved and settings.data_go_kr_key:
            try:
                r = _collect_krx_datago(settings, store, [code], transport=urllib_transport, sleep=sleep,
                                        days=days, started=started)
                if r.get("ok", 0):
                    ok += 1
                    saved = True
                else:
                    failed[code] = (r.get("failed") or {}).get(code) or r.get("status") or "bad_response"
            except FetchError as e:
                last_err = e
        if not saved:
            e = last_err or BadResponse("국내 시세 조회 실패")
            _save_error(store, code, "fdr", e)
            failed[code] = e.code
    status = "ok" if ok and not failed else ("partial" if ok else (next(iter(failed.values())) if failed else "no_data"))
    store.record_attempt("quotes_krx", started, status,
                         f"FDR/yfinance 성공 {ok} · 실패 {len(failed)}", success=ok > 0)
    return {"status": status, "ok": ok, "failed": failed}


def _collect_krx_datago(settings: Settings, store: Store, codes: List[str], transport=urllib_transport, sleep=None,
                        days: int = 400, started: Optional[str] = None) -> dict:
    """Legacy 금융위원회_주식시세정보 OpenAPI (requires DATA_GO_KR_SERVICE_KEY)."""
    ensure_schema(store)
    started = started or iso(utcnow())
    if not settings.data_go_kr_key:
        store.record_attempt("quotes_krx", started, "no_key", "DATA_GO_KR_SERVICE_KEY가 설정되지 않았습니다")
        return {"status": "no_key", "ok": 0, "failed": {}}
    kw = dict(timeout=settings.http_timeout, retries=settings.http_retries, transport=transport)
    if sleep:
        kw["sleep"] = sleep
    begin = (datetime.now(KST).date() - timedelta(days=days)).strftime("%Y%m%d")
    ok, failed = 0, {}
    for code in codes:
        try:
            url = (f"{KRX_URL}?serviceKey={settings.data_go_kr_key}&resultType=json&numOfRows=400&pageNo=1"
                   f"&likeSrtnCd={code}&beginBasDt={begin}")
            data = request_json("GET", url, **kw)
            try:
                items = data["response"]["body"]["items"]["item"]
            except (KeyError, TypeError):
                raise BadResponse("응답 형식 오류 (items 없음)")
            if isinstance(items, dict):
                items = [items]
            rows = [it for it in items if str(it.get("srtnCd", "")).endswith(code)]
            if not rows:
                raise BadResponse("해당 종목 시세 없음")
            rows.sort(key=lambda it: it["basDt"])
            hist = [(f"{it['basDt'][:4]}-{it['basDt'][4:6]}-{it['basDt'][6:]}", _num(it.get("clpr"))) for it in rows]
            _save_history(store, code, hist, "KRW", "krx")
            last = rows[-1]
            bas = last["basDt"]
            rec = {"symbol": code, "provider": "krx", "currency": "KRW", "price": _num(last.get("clpr")),
                   "change": _num(last.get("vs")), "change_pct": _num(last.get("fltRt")), "prev_close": None,
                   "day_high": _num(last.get("hipr")), "day_low": _num(last.get("lopr")),
                   "market_cap": (_num(last.get("mrktTotAmt")) or 0) / 1e6 or None, "market_cap_currency": "KRW",
                   "price_time": f"{bas[:4]}-{bas[4:6]}-{bas[6:]}", "basis": "close", "collected_at": iso(utcnow()), "raw": last}
            if rec["price"] and rec["change"] is not None:
                rec["prev_close"] = rec["price"] - rec["change"]
            _save_quote(store, rec)
            ok += 1
        except FetchError as e:
            _save_error(store, code, "krx", e)
            failed[code] = e.code
    status = "ok" if ok and not failed else ("partial" if ok else (next(iter(failed.values())) if failed else "no_data"))
    store.record_attempt("quotes_krx", started, status, f"data.go.kr 성공 {ok} · 실패 {len(failed)}", success=ok > 0)
    return {"status": status, "ok": ok, "failed": failed}


def parse_exim(items: list) -> Dict[str, float]:
    """[{cur_unit:'USD', deal_bas_r:'1,430.5'}, {cur_unit:'JPY(100)', ...}] -> {'USD': 1430.5, 'JPY': 9.53}"""
    out: Dict[str, float] = {}
    for it in items or []:
        if str(it.get("result", "1")) not in ("1", ""):
            continue
        unit = str(it.get("cur_unit", "")).strip()
        rate = _num(it.get("deal_bas_r"))
        if not unit or not rate:
            continue
        per = 1.0
        if "(" in unit:
            unit, n = unit.split("(", 1)
            per = _num(n.rstrip(")")) or 1.0
        out[unit.strip()] = rate / per
    return out


def collect_fx(settings: Settings, store: Store, transport=urllib_transport, sleep=None, today: Optional[date] = None,
               backfill_dates: Optional[List[str]] = None, max_backfill: int = 40) -> dict:
    """Latest fixing (walks back over weekends/holidays) plus a bounded backfill for dates in the price history."""
    ensure_schema(store)
    started = iso(utcnow())
    if not settings.koreaexim_api_key:
        store.record_attempt("fx", started, "no_key", "KOREAEXIM_API_KEY가 설정되지 않았습니다")
        return {"status": "no_key"}
    kw = dict(timeout=settings.http_timeout, retries=settings.http_retries, transport=transport)
    if sleep:
        kw["sleep"] = sleep

    def fetch(d: date) -> Dict[str, float]:
        url = f"{EXIM_URL}?authkey={settings.koreaexim_api_key}&searchdate={d.strftime('%Y%m%d')}&data=AP01"
        data = request_json("GET", url, **kw)
        if not isinstance(data, list):
            raise BadResponse("응답 형식 오류 (목록 아님)")
        if data and str(data[0].get("result")) in ("2", "3", "4"):
            raise BadResponse(f"제공처 오류 코드 {data[0].get('result')}")
        return parse_exim(data)

    def save(d: date, rates: Dict[str, float]) -> None:
        now = iso(utcnow())
        with store._lock, store.conn() as c:
            c.executemany("INSERT INTO fx_rates(obs_date, currency, krw_per_unit, raw, collected_at) VALUES (?,?,?,?,?) "
                          "ON CONFLICT(obs_date, currency) DO UPDATE SET krw_per_unit=excluded.krw_per_unit, collected_at=excluded.collected_at",
                          [(d.isoformat(), k, v, None, now) for k, v in rates.items()])

    try:
        d0 = today or datetime.now(KST).date()
        got = None
        for back in range(0, 8):  # an empty list means a non-business day or not yet published (before ~11:00 KST)
            d = d0 - timedelta(days=back)
            rates = fetch(d)
            if rates:
                save(d, rates)
                got = d
                break
        if not got:
            store.record_attempt("fx", started, "no_data", "최근 7일 고시 환율 없음")
            return {"status": "no_data"}
        filled = 0
        for ds in (backfill_dates or [])[:max_backfill]:
            if fx_on(store, "USD", ds) is not None:
                continue
            r = fetch(date.fromisoformat(ds))
            if r:
                save(date.fromisoformat(ds), r)
                filled += 1
        store.record_attempt("fx", started, "ok", f"{got.isoformat()} 고시 환율 저장 · 과거 {filled}일 보충", success=True)
        return {"status": "ok", "date": got.isoformat(), "backfilled": filled}
    except FetchError as e:
        store.record_attempt("fx", started, e.code, e.detail)
        return {"status": e.code, "detail": e.detail}


# ------------------------------------------------------------------ read model
STATUS_KO = {"ok": "정상", "stale": "갱신 지연", "no_key": "API 키 미설정", "auth_error": "인증 실패", "rate_limited": "호출 한도 초과",
             "timeout": "응답 시간 초과", "network_error": "네트워크 오류", "bad_response": "응답 오류", "pending": "조회 전"}


def _stale(q: dict, provider: str) -> bool:
    try:
        age = utcnow() - datetime.fromisoformat(q["collected_at"])
    except (KeyError, ValueError, TypeError):
        return True
    # Finnhub intraday snapshots age faster; daily closes (yfinance/fdr/krx) refresh on a longer cadence.
    return age > (timedelta(hours=2) if provider == "finnhub" else timedelta(hours=18))


def entity_quote(store: Store, settings: Settings, entity: dict) -> dict:
    ensure_schema(store)
    cv = coverage(entity)
    out = {"entity": entity["id"], "listed": bool(entity.get("listed")), "ticker": entity.get("ticker"),
           "exchange": entity.get("exchange"), "listing_note": entity.get("listing_note"), **cv}
    if not cv["provider"]:
        return out
    q = get_quote(store, cv["symbol"])
    err = get_error(store, cv["symbol"])
    # Prefer the provider that actually stored the last observation (fdr / yfinance / krx / finnhub).
    prov = q["provider"] if q and q.get("provider") in DELAY else cv["provider"]
    out["provider"] = prov
    out["delay_kind"], out["delay_label"] = DELAY[prov]
    out["source"] = SOURCE_META[prov]
    # yfinance / FDR need no key; Finnhub-only rows still need a key for fresh fetches.
    needs_key = prov == "finnhub" and cv["provider"] == "finnhub"
    key_set = bool(settings.finnhub_api_key) if needs_key else True
    if not q:
        code = err["code"] if err else ("pending" if key_set else "no_key")
        out.update(status=code, status_ko=STATUS_KO.get(code, code), error=err["detail"] if err else None, price=None)
        return out
    out.update(price=q["price"], currency=q["currency"], change=q["change"], change_pct=q["change_pct"], prev_close=q["prev_close"],
               day_high=q["day_high"], day_low=q["day_low"], market_cap=q["market_cap"], market_cap_currency=q["market_cap_currency"],
               market_cap_unit="million", price_time=q["price_time"], collected_at=q["collected_at"], basis=q["basis"])
    status = "stale" if _stale(q, prov) else "ok"
    if err:
        status = err["code"]
        out["error"] = f"최근 조회 실패 — 마지막 정상값 표시 ({err['detail']})"
    out.update(status=status, status_ko=STATUS_KO.get(status, status))
    if q["currency"] == "KRW":
        out["krw"] = {"value": q["price"], "native": True}
    else:
        fx = latest_fx(store, q["currency"])
        out["krw"] = ({"value": round(q["price"] * fx["krw_per_unit"], 0), "fx_rate": fx["krw_per_unit"], "fx_date": fx["obs_date"],
                       "fx_currency": q["currency"], "fx_source": "한국수출입은행 매매기준율",
                       "note": "현지 주가 × 환율 단순 환산 · 한국 거래 가격 아님"} if fx else
                      {"value": None, "note": "환율 미수집 — 원화 환산 불가"})
    return out


def overview(store: Store, settings: Settings, net: dict) -> dict:
    ensure_schema(store)
    items = [entity_quote(store, settings, n) for n in net["nodes"]]
    fx = {c: latest_fx(store, c) for c in FX_CURRENCIES}
    states = {s: store.get_state(s) for s in ("quotes_us", "quotes_krx", "fx")}
    return {
        "generated_at": iso(utcnow()),
        "items": items,
        "fx": {"source": "한국수출입은행 매매기준율 (영업일 1회 고시)", "rates": {k: v for k, v in fx.items() if v}},
        "providers": {k: {"last_success_at": v["last_success_at"], "last_attempt_at": v["last_attempt_at"],
                          "last_status": v["last_status"], "last_status_ko": STATUS_KO.get(v["last_status"] or "", v["last_status"]),
                          "detail": v["last_detail"]} for k, v in states.items()},
        "keys": {"finnhub": bool(settings.finnhub_api_key), "yfinance": True, "krx": True,
                 "fx": bool(settings.koreaexim_api_key), "data_go_kr": bool(settings.data_go_kr_key)},
        "note": "관측된 시장 가격입니다 (미국: yfinance 일간 종가 · 한국: FinanceDataReader). "
                "금리 충격 시나리오·모델 추정 노출과 무관하며, 시뮬레이션이 주가를 바꾸거나 예측하지 않습니다.",
    }


PERIOD_DAYS = {"1M": 31, "3M": 92, "6M": 183, "1Y": 366}


def price_history(store: Store, settings: Settings, entity: dict, period: str) -> dict:
    ensure_schema(store)
    cv = coverage(entity)
    if period == "1D":
        return {"entity": entity["id"], "period": period, "points": [], "status": "not_supported",
                "note": "1일(분 단위) 차트는 무료 제공처가 분봉을 제공하지 않아 지원하지 않습니다."}
    if not cv["provider"]:
        return {"entity": entity["id"], "period": period, "points": [], "status": cv["status"], "note": cv["status_ko"]}
    days = PERIOD_DAYS.get(period, 31)
    since = (datetime.now(KST).date() - timedelta(days=days)).isoformat()
    rows = history(store, cv["symbol"], since)
    pts, missing = [], 0
    for r in rows:
        if r["currency"] == "KRW":
            pts.append({"date": r["obs_date"], "close": r["close"], "krw": r["close"], "fx": None})
        else:
            rate = fx_on(store, r["currency"], r["obs_date"])
            if rate is None:
                missing += 1
            pts.append({"date": r["obs_date"], "close": r["close"], "krw": round(r["close"] * rate, 0) if rate else None, "fx": rate})
    # If US history is empty, pull a yfinance window once (observed closes only — never invent bars).
    if cv["provider"] == "yfinance" and not rows and entity.get("exchange") in US_EXCHANGES:
        try:
            batch = _fetch_yfinance_us_batch([cv["symbol"]], days=min(days + 5, 400))
            pair = batch.get(cv["symbol"])
            if pair:
                _save_history(store, cv["symbol"], pair[1], "USD", "yfinance")
                rows = history(store, cv["symbol"], since)
                pts, missing = [], 0
                for r in rows:
                    rate = fx_on(store, r["currency"], r["obs_date"])
                    if rate is None:
                        missing += 1
                    pts.append({"date": r["obs_date"], "close": r["close"],
                                "krw": round(r["close"] * rate, 0) if rate else None, "fx": rate})
        except FetchError as e:
            log.info("yfinance history backfill %s failed: %s", cv["symbol"], e.detail)

    note = ("KRX 일간 종가 (FinanceDataReader / 폴백)" if entity.get("exchange") in KR_EXCHANGES else
            "yfinance 일간 종가 (관측값 · 시나리오와 무관)")
    if missing:
        note += f" 환율이 없는 {missing}일은 원화 값을 비워 둡니다 (현재 환율로 채우지 않음)."
    return {"entity": entity["id"], "period": period, "symbol": cv["symbol"], "provider": cv["provider"],
            "currency": rows[0]["currency"] if rows else None, "points": pts, "status": "ok" if pts else "insufficient",
            "note": note}
