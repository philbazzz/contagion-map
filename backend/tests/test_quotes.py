"""Share prices, KRW conversion and FX (MARKET VIEW) with a fake transport — no network, no real keys."""
import json
import time
from datetime import date, datetime, timedelta, timezone

from app.market import quotes as qt
from app.market.config import Settings
from app.market.store import Store

FH, KRXK, EXK = "finnhubSECRET111", "datagoSECRET222", "eximSECRET333"


def make(tmp_path, fh=FH, krx=KRXK, ex=EXK):
    st = Settings(db_path=tmp_path / "q.db", scheduler_enabled=False, http_retries=1, manual_refresh_min_interval_sec=0,
                  finnhub_api_key=fh, data_go_kr_key=krx, koreaexim_api_key=ex)
    return st, Store(st.db_path)


class Fake:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers))
        for frag, resp in self.routes.items():
            if frag in url:
                r = resp(url) if callable(resp) else resp
                if isinstance(r, Exception):
                    raise r
                return r[0], {}, json.dumps(r[1]).encode()
        return 404, {}, b"{}"


T = int(datetime(2026, 10, 16, 20, 0, tzinfo=timezone.utc).timestamp())  # 16:00 New York
QUOTE = {"c": 150.0, "d": 3.44, "dp": 2.35, "h": 151, "l": 147, "o": 148, "pc": 146.56, "t": T}
EXIM = [{"result": 1, "cur_unit": "USD", "deal_bas_r": "1,430", "cur_nm": "미국 달러"},
        {"result": 1, "cur_unit": "JPY(100)", "deal_bas_r": "953.21", "cur_nm": "일본 옌"},
        {"result": 1, "cur_unit": "EUR", "deal_bas_r": "1,662.4", "cur_nm": "유로"}]
NET = {"nodes": [
    {"id": "nvidia", "listed": True, "ticker": "NVDA", "exchange": "Nasdaq"},
    {"id": "sk_hynix", "listed": True, "ticker": "000660", "exchange": "KOSPI"},
    {"id": "mufg", "listed": True, "ticker": "8306", "exchange": "TSE"},
    {"id": "openai", "listed": False, "ticker": None, "exchange": None}]}


def test_ticker_mapping_and_unlisted_never_priced():
    assert qt.coverage(NET["nodes"][0])["provider"] == "yfinance"
    assert qt.coverage(NET["nodes"][1])["provider"] == "fdr"
    assert qt.coverage(NET["nodes"][1])["symbol"] == "000660"
    assert qt.coverage(NET["nodes"][2])["status"] == "not_supported"
    assert qt.coverage(NET["nodes"][3])["status"] == "unlisted"
    tg = qt.targets(NET)
    assert tg["us"] == ["NVDA"] and tg["krx"] == ["000660"] and tg["finnhub"] == ["NVDA"]


def test_real_dataset_mapping(network):
    tg = qt.targets(network)
    assert {"CRWV", "NVDA", "MSFT", "META", "TSM"} <= set(tg["us"])
    assert "000660" in tg["krx"] or tg["krx"] == ["000660"]
    for n in network["nodes"]:
        if not n["listed"]:
            assert qt.coverage(n)["provider"] is None


def test_usd_quote_and_krw_conversion(tmp_path):
    st, store = make(tmp_path)
    fake = Fake({"/quote?": (200, QUOTE), "profile2": (200, {"marketCapitalization": 3_600_000, "currency": "USD"}),
                 "exchangeJSON": (200, EXIM)})
    assert qt.collect_us_quotes(st, store, ["NVDA"], transport=fake)["status"] == "ok"
    assert qt.collect_fx(st, store, transport=fake, today=date(2026, 10, 19))["status"] == "ok"
    q = qt.entity_quote(store, st, NET["nodes"][0])
    assert q["price"] == 150.0 and q["change_pct"] == 2.35 and q["currency"] == "USD"
    assert q["krw"]["value"] == 214500 and q["krw"]["fx_rate"] == 1430 and q["krw"]["fx_date"] == "2026-10-19"
    assert q["price_time"].startswith("2026-10-16T20:00") and q["delay_kind"] == "realtime"
    assert q["market_cap"] == 3_600_000 and q["market_cap_unit"] == "million"
    # key travels in a header, never in the URL
    assert all(FH not in url for _, url, _ in fake.calls) and fake.calls[0][2]["X-Finnhub-Token"] == FH


def test_jpy_per_100_and_comma_parsing():
    r = qt.parse_exim(EXIM)
    assert r["USD"] == 1430 and abs(r["JPY"] - 9.5321) < 1e-9 and r["EUR"] == 1662.4


def test_krw_listing_stays_in_krw(tmp_path):
    st, store = make(tmp_path)
    items = [{"basDt": "20261015", "srtnCd": "000660", "clpr": "251000", "vs": "-3000", "fltRt": "-1.18", "hipr": "255000",
              "lopr": "249000", "mrktTotAmt": "182725000000000"},
             {"basDt": "20261016", "srtnCd": "000660", "clpr": "254500", "vs": "3500", "fltRt": "1.39", "hipr": "256000",
              "lopr": "250000", "mrktTotAmt": "185273000000000"}]
    fake = Fake({"getStockPriceInfo": (200, {"response": {"body": {"items": {"item": items}}}})})
    assert qt.collect_krx(st, store, ["000660"], transport=fake)["status"] == "ok"
    q = qt.entity_quote(store, st, NET["nodes"][1])
    assert q["currency"] == "KRW" and q["price"] == 254500 and q["krw"] == {"value": 254500, "native": True}
    assert q["price_time"] == "2026-10-16" and q["delay_kind"] == "close" and q["prev_close"] == 251000
    h = qt.price_history(store, st, NET["nodes"][1], "1Y")
    assert [p["close"] for p in h["points"]][-2:] == [251000, 254500]


def test_finnhub_no_key_and_errors_never_invent_a_price(tmp_path):
    """Finnhub path still requires a key; yfinance is the no-key primary (tested live separately)."""
    st, store = make(tmp_path, fh="", krx="", ex="")
    assert qt._collect_us_finnhub(st, store, ["NVDA"])["status"] == "no_key"
    q = qt.entity_quote(store, st, NET["nodes"][0])
    assert q["price"] is None
    st2, store2 = make(tmp_path / "b")
    qt.collect_us_quotes(st2, store2, ["NVDA"], transport=Fake({"/quote?": (200, {"c": 0, "d": None, "dp": None, "pc": 0, "t": 0})}))
    q = qt.entity_quote(store2, st2, NET["nodes"][0])
    assert q["price"] is None and q["status"] == "bad_response"


def test_failure_keeps_last_good_value_with_its_time(tmp_path):
    st, store = make(tmp_path)
    qt.collect_us_quotes(st, store, ["NVDA"], transport=Fake({"/quote?": (200, QUOTE), "profile2": (200, {})}))
    r = qt.collect_us_quotes(st, store, ["NVDA"], transport=Fake({"/quote?": (500, {})}), sleep=lambda s: None)
    assert r["status"] == "bad_response"
    q = qt.entity_quote(store, st, NET["nodes"][0])
    assert q["price"] == 150.0 and q["status"] == "bad_response" and "마지막 정상값" in q["error"]


def test_auth_error_stops_batch_and_hides_key(tmp_path):
    st, store = make(tmp_path)
    fake = Fake({"/quote?": (401, {"error": "Invalid API key"})})
    r = qt.collect_us_quotes(st, store, ["NVDA", "MSFT", "META"], transport=fake)
    assert r["status"] == "auth_error" and len(fake.calls) == 1
    ov = json.dumps(qt.overview(store, st, NET), ensure_ascii=False)
    assert FH not in ov and KRXK not in ov and EXK not in ov


def test_fx_walks_back_over_weekend_and_history_uses_rate_of_each_date(tmp_path):
    st, store = make(tmp_path)
    by_day = {"20261018": [], "20261017": [], "20261016": EXIM}  # Sun, Sat empty -> Friday fixing
    fake = Fake({"exchangeJSON": lambda u: (200, by_day.get(u.split("searchdate=")[1][:8], []))})
    assert qt.collect_fx(st, store, transport=fake, today=date(2026, 10, 18))["date"] == "2026-10-16"
    # a stored close on a date without FX keeps an empty KRW value instead of using today's rate
    qt._save_history(store, "NVDA", [("2026-10-16", 150.0), ("2026-10-09", 140.0)], "USD", "finnhub")
    qt._save_quote(store, {"symbol": "NVDA", "provider": "finnhub", "currency": "USD", "price": 150.0, "basis": "realtime",
                           "collected_at": datetime.now(timezone.utc).isoformat()})
    import app.market.quotes as mod
    real = mod.datetime

    class Fixed(real):  # pin "today" so the 1M window contains both dates
        @classmethod
        def now(cls, tz=None):
            return real(2026, 10, 19, 12, tzinfo=tz)
    mod.datetime = Fixed
    try:
        h = qt.price_history(store, st, NET["nodes"][0], "1M")
    finally:
        mod.datetime = real
    pts = {p["date"]: p for p in h["points"]}
    assert pts["2026-10-16"]["krw"] == 214500 and pts["2026-10-09"]["krw"] is None and "현재 환율로 채우지 않음" in h["note"]


def test_1d_chart_is_declared_unsupported(tmp_path):
    st, store = make(tmp_path)
    h = qt.price_history(store, st, NET["nodes"][0], "1D")
    assert h["status"] == "not_supported" and h["points"] == []
