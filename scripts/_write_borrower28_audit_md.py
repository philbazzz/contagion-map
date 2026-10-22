#!/usr/bin/env python3
"""Generate docs/BORROWER28_AUDIT.md from investigation + body + integration JSON."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
inv = json.loads((ROOT / "docs/opendart_borrower28_investigation.json").read_text(encoding="utf-8"))
body = json.loads((ROOT / "docs/opendart_borrower28_body_hits.json").read_text(encoding="utf-8"))
integ = json.loads((ROOT / "docs/opendart_borrower28_integration.json").read_text(encoding="utf-8"))
body_by = {r["id"]: r for r in body["results"]}

lines = []
lines.append("# 국내 DC 차주 28건 DART 조사 보고")
lines.append("")
lines.append(f"- 조사일: **{inv.get('verification_date')}**")
lines.append(f"- 본문 스캔일: **{inv.get('body_scan_date') or body.get('verification_date')}**")
lines.append(f"- 통합일: **{integ.get('verification_date')}**")
lines.append("- OpenDART API: 서버측 `OPEN_DART_API_KEY` 사용 (키 미노출)")
lines.append("- 원칙: 키워드 동시출현만으로 잔액·엣지를 만들지 않음. 주선≠보유. Unknown≠0.")
lines.append("")
lines.append("## 분류 요약")
lines.append("")
for k, v in sorted(inv.get("by_classification", {}).items(), key=lambda x: -x[1]):
    lines.append(f"- {v}건 — {k}")
lines.append("")
lines.append("## 통합 요약")
lines.append("")
lines.append(f"- 추가 노드: {', '.join(integ.get('added_nodes') or []) or '(없음)'}")
lines.append(f"- 메타 갱신 노드: {len(integ.get('updated_nodes') or [])}개")
lines.append(f"- 추가 출처(감사보고서): {len(integ.get('added_sources') or [])}건")
lines.append(f"- 자동 추가 금융 엣지: {len(integ.get('edges_added') or [])}건 (의도적으로 0)")
lines.append("")
lines.append("## 차주별 결과")
lines.append("")
lines.append("| # | 시드명 | 분류 | DART 법인 | 맵 노드 | 감사보고서 | 비고 |")
lines.append("|---|--------|------|-----------|---------|------------|------|")

for r in inv["results"]:
    bid = r["id"]
    br = body_by.get(bid) or {}
    pc = r.get("primary_corp") or {}
    corp = pc.get("corp_name") or br.get("corp_name") or "—"
    code = pc.get("corp_code") or br.get("corp_code") or ""
    corp_cell = f"{corp}" + (f" (`{code}`)" if code else "")
    maps = ", ".join(m["id"] for m in (r.get("map_nodes") or [])) or "—"
    doc = br.get("document") or {}
    audit = "—"
    if doc.get("rcept_no"):
        audit = f"[{doc.get('rcept_dt')}]({doc.get('url')})"
    elif br.get("status") == "no_audit_report":
        audit = "목록에 감사보고서 없음/미수집"
    elif br.get("status") == "no_corp":
        audit = "법인 미확정"
    notes = "; ".join((r.get("notes") or [])[:2]) or "—"
    lines.append(
        f"| {bid} | {r['seed_name']} | {r['classification']} | {corp_cell} | {maps} | {audit} | {notes} |"
    )

lines.append("")
lines.append("## 본문 키워드에서 관측된 기관명 (잔액 미확정)")
lines.append("")
lines.append("아래는 감사보고서 텍스트 키워드 주변에서 **이름이 나타난** 기관입니다. "
             "기관별 대출잔액·보증한도로 확정하지 않았으며, 네트워크 엣지로 자동 반영하지 않았습니다.")
lines.append("")
from collections import Counter
for r in body["results"]:
    lenders = []
    for s in r.get("snippets") or []:
        lenders.extend(s.get("lenders_mentioned") or [])
    if not lenders:
        continue
    top = ", ".join(f"{a}({b})" for a, b in Counter(lenders).most_common(6))
    lines.append(f"- **{r['seed_name']}**: {top}")

lines.append("")
lines.append("## 미확인·제외")
lines.append("")
for s in integ.get("skipped") or []:
    lines.append(f"- {s['id']}: {s['reason']}")
lines.append("")
lines.append("## 남은 작업")
lines.append("")
lines.append("1. 감사보고서 주석의 차입금 명세표를 행 단위로 읽어 기관별 잔액이 명시된 경우만 `PROJECT_LOAN` 엣지 작성")
lines.append("2. 가산디씨에스엘원·디씨아이티와이부천·케이스퀘어장림·파인디씨 등 감사보고서 미수집 건 재수집")
lines.append("3. 더엣지영등포·IBK부산AI·에이아이팩토리포항·케이인더스트리·캄스퀘어용인·하남엣지 법인코드 확정")
lines.append("4. 브라우저 GPU/실기기에서 회전·선택 반복 시 메모리 프로파일 (이 환경에서는 자동화 미실시)")
lines.append("")

out = ROOT / "docs" / "BORROWER28_AUDIT.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote", out)
