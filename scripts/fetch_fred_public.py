"""Fetch redistributable FRED series for the static GitHub Pages market.json.

Uses only UST yields (DGS10, DGS2). Does NOT embed HY OAS (ICE redistribution limits)
or equity quotes (Finnhub / Yahoo redistribution not permitted).

    FRED_API_KEY=... python scripts/fetch_fred_public.py --out frontend/public/data/market.json

Requires: urllib (stdlib). No yfinance.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

FRED = "https://api.stlouisfed.org/fred"
SERIES = [
    {
        "id": "ust_10y",
        "series_id": "DGS10",
        "name": "미국 10년물 국채 금리",
        "plain": "장기 시장금리의 대표 벤치마크 (관측값 · 시나리오 가정 아님)",
        "unit": "%",
        "url": "https://fred.stlouisfed.org/series/DGS10",
    },
    {
        "id": "ust_2y",
        "series_id": "DGS2",
        "name": "미국 2년물 국채 금리",
        "plain": "단기·중기 시장금리 벤치마크 (관측값 · 시나리오 가정 아님)",
        "unit": "%",
        "url": "https://fred.stlouisfed.org/series/DGS2",
    },
]


def _get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_series(api_key: str, series_id: str) -> list[tuple[str, float]]:
    q = urllib.parse.urlencode({
        "series_id": series_id, "api_key": api_key, "file_type": "json",
        "sort_order": "desc", "limit": 40,
    })
    data = _get(f"{FRED}/series/observations?{q}")
    out: list[tuple[str, float]] = []
    for o in data.get("observations") or []:
        raw = str(o.get("value", "."))
        if raw in (".", ""):
            continue
        try:
            out.append((o["date"], float(raw)))
        except ValueError:
            continue
    return out  # newest first


def build_indicator(meta: dict, rows: list[tuple[str, float]]) -> dict:
    base = {
        "id": meta["id"], "name": meta["name"], "plain": meta["plain"], "unit": meta["unit"],
        "unit_note": f"FRED {meta['series_id']} · 연율 %",
        "source": {"name": f"FRED ({meta['series_id']})", "url": meta["url"]},
        "freshness_label": "최신 발표값 (실시간 아님 · 일별)",
        "caution": "관측된 시장 금리입니다. 좌측 시나리오의 가상 bp 충격과 혼동하지 마세요.",
        "license": None,
    }
    if not rows:
        return {**base, "status": "no_data", "status_ko": "관측값 없음", "latest": None}
    latest, prev = rows[0], (rows[1] if len(rows) > 1 else None)
    ch = round(latest[1] - prev[1], 3) if prev else None

    def trend(days: int):
        target = date.fromisoformat(latest[0])
        # rows are newest-first; find first obs on or before target-days
        from datetime import timedelta
        cut = (target - timedelta(days=days)).isoformat()
        cand = [r for r in rows if r[0] <= cut]
        if not cand:
            return {"status": "insufficient", "label": "이력 부족"}
        ref = cand[0]
        return {"status": "ok", "ref_date": ref[0], "ref_value": ref[1],
                "change": round(latest[1] - ref[1], 3)}

    return {
        **base,
        "status": "ok", "status_ko": "정상",
        "latest": {"value": latest[1], "obs_date": latest[0]},
        "previous": {"value": prev[1], "obs_date": prev[0]} if prev else None,
        "change_vs_previous": ch,
        "trend": {"d7": trend(7), "d30": trend(30)},
        "history": {
            "stored_from": rows[-1][0], "stored_to": latest[0], "stored_count": len(rows),
            "provider_note": "미국 재무부 일별 국채 금리 · FRED 공개 데이터 (재배포 시 출처 표기)",
        },
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--api-key", default=os.environ.get("FRED_API_KEY", ""))
    args = p.parse_args()
    if not args.api_key:
        print("FRED_API_KEY missing — writing placeholder market.json", file=sys.stderr)
        out = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_at": None, "auto_update": False,
            "usage_note": "FRED_API_KEY가 없어 국채 스냅샷을 갱신하지 못했습니다.",
            "indicators": [
                {**{k: m[k] for k in ("id", "name", "plain", "unit")},
                 "source": {"name": f"FRED ({m['series_id']})", "url": m["url"]},
                 "status": "no_key", "status_ko": "FRED_API_KEY 미설정", "latest": None}
                for m in SERIES
            ] + [{
                "id": "hy_oas", "name": "미국 하이일드 채권 가산금리 (HY OAS)",
                "plain": "하이일드 신용 가산금리", "unit": "bp",
                "source": {"name": "FRED (BAMLH0A0HYM2)", "url": "https://fred.stlouisfed.org/series/BAMLH0A0HYM2"},
                "status": "not_redistributable", "status_ko": "ICE 재배포 제한", "latest": None,
            }],
        }
    else:
        inds = []
        for meta in SERIES:
            rows = fetch_series(args.api_key, meta["series_id"])
            inds.append(build_indicator(meta, rows))
            print(meta["id"], "obs", len(rows), "latest", rows[0] if rows else None)
        inds.append({
            "id": "hy_oas", "name": "미국 하이일드 채권 가산금리 (HY OAS)",
            "plain": "하이일드 신용 가산금리", "unit": "bp",
            "source": {"name": "FRED (BAMLH0A0HYM2)", "url": "https://fred.stlouisfed.org/series/BAMLH0A0HYM2"},
            "status": "not_redistributable", "status_ko": "ICE 재배포 제한으로 공개 배포본 미포함",
            "latest": None, "license": "ICE Data Indices · 제3자 공개 배포는 사전 승인 필요",
        })
        out = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
            "auto_update": True,
            "usage_note": "국채 금리는 FRED 관측값입니다. 주식 수치는 재배포 제한으로 포함하지 않으며, 금리 충격 시나리오와 무관합니다.",
            "indicators": inds,
        }
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
