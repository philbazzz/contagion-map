#!/usr/bin/env python3
"""국내 DC v6 데이터 검증 — 금액 정합성·중복 배분·참조 무결성·표시 규칙."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PF = ROOT / "frontend" / "public" / "data" / "pf"

# 공시된 총 약정(억원) — 감사보고서·공시 원문 기준
EXPECTED_COMMIT = {
    ("camsquare_ansan", "main_pf"): 8340,        # Tr.A 7,100 + Tr.B 700 + Tr.C 540 (일반자금 1,360은 equity 단계로 분리)
    ("casequare_gasan", "refinancing"): 3800,
    ("magna_deogi", "refinancing"): 2730,
    ("bucheon_peach_dc", "main_pf"): 5900,
    ("bupyeong_digital_edge", "refinancing"): 8000,
    ("gasan_stt_seoul1", "refinancing"): 2300,
    ("yeongdeungpo_yedc", "main_pf"): 2200,
    ("hanam_mkif_dc", "refinancing"): 4950 + 200,  # 인수금융 4,950 + 신용공여 200
}
EXPECTED_DRAWN = {("camsquare_ansan", "main_pf"): 1351.0, ("casequare_gasan", "refinancing"): 3746,
                  ("magna_deogi", "refinancing"): 908, ("bucheon_peach_dc", "main_pf"): 3047,
                  ("bupyeong_digital_edge", "refinancing"): 5020, ("yeongdeungpo_yedc", "main_pf"): 820}


def main() -> int:
    net = json.load(open(PF / "network.json", encoding="utf-8"))
    pj = json.load(open(PF / "projects.json", encoding="utf-8"))
    ids = {n["id"] for n in net["nodes"]}
    errors, checks = [], []

    def ok(name, cond, detail=""):
        checks.append({"check": name, "pass": bool(cond), "detail": detail})
        if not cond:
            errors.append(f"{name}: {detail}")

    v6 = [e for e in net["edges"] if e.get("added_in") == "v6"]
    # 1. 참조 무결성
    ok("edge endpoints exist", all(e["source"] in ids and e["target"] in ids for e in net["edges"]))
    ok("unique edge ids", len({e["id"] for e in net["edges"]}) == len(net["edges"]))
    ok("unique node ids", len(ids) == len(net["nodes"]))
    src_ids = {s["id"] for s in net["sources"]}
    ok("every v6 relation has a source", all(e["source_ids"] and all(s in src_ids for s in e["source_ids"]) for e in v6))
    ok("every v6 relation has a URL", all(e.get("source_url") for e in v6),
       ", ".join(e["id"] for e in v6 if not e.get("source_url")))
    # 2. 금액: 비공개는 None, 0 금지
    zero = [e["id"] for e in v6 if e.get("amount_krw_eok") == 0]
    ok("no zero placeholder amounts", not zero, ", ".join(zero))
    # 3. 사업별 기관 약정 합계 = 공시 총약정 (현재 대주, 대출성 관계만)
    loanish = {"PROJECT_LOAN", "ACQUISITION_LOAN", "REVOLVER"}
    sums, drawn = defaultdict(float), defaultdict(float)
    for e in v6:
        if e["relationship_type"] in loanish and e.get("amount_type") == "institution_commitment" \
                and e.get("relationship_status") not in ("repaid",):
            k = (e["project_id"], e["financing_stage"])
            sums[k] += e["amount_krw_eok"] or 0
            drawn[k] += e.get("drawn_krw_eok") or 0
    for k, exp in EXPECTED_COMMIT.items():
        ok(f"commitment sum {k}", abs(sums[k] - exp) < 1.0, f"{sums[k]:.1f} vs {exp}")
    for k, exp in EXPECTED_DRAWN.items():
        ok(f"drawn sum {k}", abs(drawn[k] - exp) < 2.0, f"{drawn[k]:.1f} vs {exp}")
    # 4. 총액(facility_total_context)·주선 관계에 금액을 보유액처럼 넣지 않음
    bad_arr = [e["id"] for e in v6 if e["relationship_type"] == "ARRANGER" and e.get("amount_type") not in (None, "facility_total_context", "fee_paid", "institution_commitment")]
    ok("arranger amounts typed as context/fee", not bad_arr, ", ".join(bad_arr))
    # 5. 공동 대주 '총액 복제' 탐지: 같은 사업·같은 금액·대출성·3곳 이상이면 의심
    dup = defaultdict(list)
    for e in v6:
        if e["relationship_type"] in loanish and e.get("amount_krw_eok"):
            dup[(e["project_id"], e["financing_stage"], e["amount_krw_eok"], e.get("amount_type"))].append(e["source"])
    suspicious = {k: v for k, v in dup.items() if len(v) >= 3 and k[2] >= 1000}
    ok("no syndicate total copied to each lender", not suspicious, str(suspicious))
    # 6. 상환된 관계는 현재 잔액으로 표시하지 않음
    bad_hist = [e["id"] for e in v6 if e.get("relationship_status") == "repaid" and e.get("amount_type") in ("outstanding", "institution_commitment")]
    ok("repaid relations use historical amount types", not bad_hist, ", ".join(bad_hist))
    # 7. 도급액 ≠ 미수공사비
    ok("no receivable typed as contract value", not any(e.get("amount_type") == "construction_receivable" for e in v6))
    # 8. 조건부 의무에는 발동 조건 기재
    no_trig = [e["id"] for e in v6 if e.get("contingent_obligation") and e["relationship_type"] in
               ("DEBT_ASSUMPTION", "COMPLETION_GUARANTEE", "LOAN_GUARANTEE", "SHARE_PLEDGE", "LEASE_GUARANTEE") and not e.get("obligation_trigger")]
    ok("contingent obligations have trigger", not no_trig, ", ".join(no_trig))
    # 9. 코어위브↔국내 PF 직접 사실 관계 없음
    region = {n["id"]: n.get("region") for n in net["nodes"]}
    cw_kr = [e["id"] for e in net["edges"] if "coreweave" in (e["source"], e["target"]) and
             region.get(e["target"] if e["source"] == "coreweave" else e["source"]) == "KR" and e.get("layer") != "scenario"]
    ok("no factual CoreWeave–Korea PF edge", not cw_kr, ", ".join(cw_kr))
    # 10. 같은 프로젝트 기업끼리 직접 연결 금지 — v6 관계의 한쪽은 반드시 차주·SPV·펀드
    vehicle = {n["id"] for n in net["nodes"] if n.get("entity_type") in ("spv", "fund", "reit") or n.get("group") == "project_finance"}
    borrowers = {p.get("spv") for p in pj["projects"] if p.get("spv")}
    # 기업 대출·출자의 대상(운영사 차주·사업주체)도 계약 상대방으로 인정
    borrowers |= {e["target"] for e in v6 if e["relationship_type"] in ("CORPORATE_LOAN", "EQUITY_INVESTMENT", "EPC_CONTRACT")
                  and e["relationship_type"] != "EPC_CONTRACT" or e["relationship_type"] == "CORPORATE_LOAN"}
    borrowers |= {"gs_ai_infra"}  # 동해 AIDC 사업주체(자회사 출자 법인)
    peer = [e["id"] for e in v6 if e["source"] not in vehicle | borrowers and e["target"] not in vehicle | borrowers
            and e["relationship_type"] not in ("ASSET_SALE", "PARENT_AFFILIATE")]
    ok("v6 relations attach to vehicle/borrower (no peer-to-peer)", not peer, ", ".join(peer))
    # 11. 별개 사업 병합 금지 (같은 시군구 다른 사업)
    must_differ = [("camsquare_ansan", "keppel_ansan"), ("camsquare_ansan", "koramco_siheung_dc"),
                   ("incheon_wonchang_dc", "incheon_bukhang_idc"), ("bucheon_samjeong_ai", "bucheon_peach_dc"),
                   ("hanam_mkif_dc", "hanam_edge_dc"), ("gasan_stt_seoul1", "gasan_dci_sel1"), ("gasan_stt_seoul1", "casequare_gasan")]
    pids = {p["id"]: p for p in pj["projects"]}
    ok("distinct projects kept separate", all(a in pids and b in pids and pids[a].get("spv") != pids[b].get("spv") for a, b in must_differ))
    # 12. 숨김 노드는 지도 노드에 없음
    ok("hidden nodes not on map", not ({h["id"] for h in net.get("hidden_nodes", [])} & ids))

    report = {"passed": not errors, "errors": errors, "checks": checks,
              "counts": {"nodes": len(net["nodes"]), "edges": len(net["edges"]), "v6_relations": len(v6),
                         "hidden_nodes": len(net.get("hidden_nodes", []))}}
    json.dump(report, open(PF / "_validation_v6.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for c in checks:
        print(("PASS " if c["pass"] else "FAIL ") + c["check"] + (f"  [{c['detail']}]" if c["detail"] and not c["pass"] else ""))
    print("RESULT:", "PASSED" if not errors else f"FAILED ({len(errors)})")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
