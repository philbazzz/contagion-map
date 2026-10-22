#!/usr/bin/env python3
"""Map 당기말 borrowings for casequare / peach / camsquare from note tables.

Column rule verified in source text: 당기말 then 전기말.
Rows with 당기말 '-' are prior-only — not mapped as current.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "frontend" / "public" / "data" / "pf" / "network.json"

# (edge_id, lender_node, lender_name, outstanding_krw, rate, maturity, tranche)
CASEQUARE = [  # 단위 천원 → *1000 ; rcept 20260409001042 note 12
    ("dart_loan_kyobo_life_gen_casequare", "kyobo_life", "교보생명보험(일반계정)", 49_200_000_000, "5.50%", None, "Tranche A"),
    ("dart_loan_kyobo_life_spec_casequare", "kyobo_life", "교보생명보험(특별계정)", 49_200_000_000, "5.50%", None, "Tranche A"),
    ("dart_loan_hana_casequare", "hana_bank", "하나은행", 29_600_000_000, "5.50%", None, "Tranche A"),
    ("dart_loan_samsung_fire_casequare", "samsung_fire", "삼성화재해상보험", 83_600_000_000, "5.50%", None, "Tranche A"),
    ("dart_loan_hanwha_life_casequare", "hanwha_life", "한화생명보험", 98_300_000_000, "5.50%", None, "Tranche A"),
    ("dart_loan_thek_savings_casequare", "thek_savings", "더케이저축은행", 9_900_000_000, "5.50%", None, "Tranche A"),
    ("dart_loan_shinhan_capital_casequare", "shinhan_capital", "신한캐피탈", 19_800_000_000, "5.50%", None, "Tranche A"),
    ("dart_loan_bluecorner_casequare", "bluecorner_capital", "블루코너캐피탈", 5_000_000_000, "7.00%", None, "Tranche B"),
    ("dart_loan_kw_tg4_casequare", "kw_tg4_spc", "케이더블유투금제사차", 30_000_000_000, "7.00%", None, "Tranche B"),
]

PEACH = [  # 단위 천원 ; rcept 20260401001191 note 5 ; 당기말 first
    ("dart_loan_ibk_peach_a", "ibk_bank", "중소기업은행", 25_830_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_hyundai_capital_peach_a", "hyundai_capital", "현대캐피탈", 15_500_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_hana_capital_peach_a", "hana_capital", "하나캐피탈", 2_580_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_db_ins_peach_a", "db_ins", "디비손해보험", 20_660_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_heungkuk_fire_peach_a", "heungkuk_fire", "흥국화재해상보험", 12_910_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_kdb_peach_a", "kdb", "한국산업은행", 25_830_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_kb_capital_peach_a", "kb_capital", "케이비캐피탈", 5_170_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_bccard_peach_a", "bccard", "비씨카드", 5_170_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_kyobo_life_gen_peach_a", "kyobo_life", "교보생명보험(일반계정)", 38_740_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_kyobo_life_spec_peach_a", "kyobo_life", "교보생명보험(특별계정)", 38_740_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_saemaul_peach_a", "saemaul_federation", "새마을금고중앙회", 80_070_000_000, "7.40%", "2026-10-20", "PF A 선순위"),
    ("dart_loan_hyundai_capital_peach_b", "hyundai_capital", "현대캐피탈", 7_730_000_000, "9.50%", "2026-10-20", "PF B 후순위"),
    ("dart_loan_hana_capital_peach_b", "hana_capital", "하나캐피탈", 2_580_000_000, "9.50%", "2026-10-20", "PF B 후순위"),
    ("dart_loan_kb_capital_peach_b", "kb_capital", "케이비캐피탈", 2_580_000_000, "9.50%", "2026-10-20", "PF B 후순위"),
    ("dart_loan_bccard_peach_b", "bccard", "비씨카드", 7_730_000_000, "9.50%", "2026-10-20", "PF B 후순위"),
    ("dart_loan_shinhan_capital_peach_b", "shinhan_capital", "신한캐피탈", 2_580_000_000, "9.50%", "2026-10-20", "PF B 후순위"),
    ("dart_loan_jb_woori_capital_peach_b", "jb_woori_capital", "제이비우리캐피탈", 5_150_000_000, "9.50%", "2026-10-20", "PF B 후순위"),
    ("dart_loan_shinhan_sec_peach_b", "shinhan_sec", "신한투자증권", 5_150_000_000, "9.50%", "2026-10-20", "PF B 후순위"),
]

CAMSQUARE = [  # 단위 원 ; rcept 20260413002070 ; 당기 first
    ("dart_loan_camsquare1_camsquare", "camsquare_first_spc", "캄스퀘어제일차", 20_080_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_hyundai_capital_camsquare", "hyundai_capital", "현대캐피탈", 16_200_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_kb_ins_camsquare", "kb_ins", "KB손해보험", 11_340_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_military_mutual_camsquare", "military_mutual", "군인공제회", 11_340_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_db_life_camsquare", "db_life", "DB생명보험", 8_100_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_yk_ansan_camsquare", "yk_ansan_d1", "와이케이안산디원", 3_730_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_kb_capital_camsquare", "kb_capital", "KB캐피탈", 4_860_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_woori_fin_capital_camsquare", "woori_finance_capital", "우리금융캐피탈", 4_860_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_hyundai_commercial_camsquare", "hyundai_commercial", "현대커머셜", 4_860_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_hana_capital_camsquare", "hana_capital", "하나캐피탈", 3_240_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_welcome_savings_camsquare", "welcome_savings", "웰컴저축은행", 1_950_000_000, "6.37%", "2028-06-24", "Tr.A"),
    ("dart_loan_shinhan_capital_camsquare", "shinhan_capital", "신한캐피탈", 1_620_000_000, "6.37%", "2028-06-24", "Tr.A"),
]


def eok(krw: int) -> float:
    return round(krw / 1e8, 4)


def promote(net, nid, name):
    if any(n["id"] == nid for n in net["nodes"]):
        return
    for i, n in enumerate(net.get("hidden_nodes") or []):
        if n.get("id") == nid:
            p = deepcopy(n)
            p.pop("map_hidden", None)
            for k in ("roles", "key_drivers", "source_ids"):
                if not isinstance(p.get(k), list):
                    p[k] = []
            net["nodes"].append(p)
            net["hidden_nodes"].pop(i)
            return
    net["nodes"].append({
        "id": nid, "name": name, "name_ko": name, "group": "financial",
        "entity_type": "lender", "region": "KR", "listed": False, "display_size": 1,
        "source_status": "VERIFIED", "roles": ["lender"], "key_drivers": [], "source_ids": [],
        "connection_status": "관계 확인", "is_company": True, "pf_exposure_class": "confirmed_dc_finance",
    })


def mk(target, rcept, title, as_of, eid, src, name, krw, rate, maturity, tranche):
    return {
        "id": eid, "source": src, "target": target, "relationship_type": "PROJECT_LOAN",
        "roles": ["lender"], "source_ids": [f"dart_audit_{target}_{rcept}"],
        "contract_ids": [], "commercial_ids": [], "amount_usd_m": None,
        "amount_krw_eok": eok(krw), "amount_type": "outstanding_principal", "amount_unit": "억원",
        "amount_note": f"감사보고서 차입금 주석 당기말 {name} {krw:,}원 ({tranche})",
        "amount_as_of": as_of, "impact_channel": "financial", "source_status": "VERIFIED",
        "label": f"{name} → {target} · {eok(krw):g}억",
        "impact_label": f"{name} 당기말 {eok(krw):g}억",
        "explanation": f"당기말 잔액 (전기말 비교열 제외). {tranche} {rate}",
        "transmission_class": "direct", "exposure_status": "ACTIVE_CONFIRMED",
        "relationship_status": "current", "shock_eligible": True, "layer": "fact",
        "evidence_kind": "dart_audit_note", "evidence_status": "DART 감사보고서 차입금 주석 당기말",
        "evidence_level": "company_filing", "participation_path": "직접 대출",
        "participation_directness": "direct", "contingent_obligation": False,
        "source_url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}",
        "source_title": title, "source_date": f"{rcept[:4]}-{rcept[4:6]}-{rcept[6:8]}",
        "dart_receipt_number": rcept, "verification_date": "2026-10-22",
        "maturity": maturity, "interest_rate": rate, "financing_stage": "main_pf",
        "tranche": tranche, "period_basis": "current_period_당기말",
        "stress_direction": "차주 부실 → 대주 신용 익스포저",
        "exposure_kind": "loan_principal_outstanding",
    }


def upsert(net, edge):
    edges = net["edges"]
    for i, e in enumerate(edges):
        if e.get("id") == edge["id"]:
            edges[i] = edge
            return "replaced"
    edges.append(edge)
    return "added"


def main() -> None:
    net = json.loads(NET.read_text(encoding="utf-8"))
    stats = {"added": 0, "replaced": 0}
    batches = [
        ("casequare_pfv", "20260409001042", "케이스퀘어데이터센터피에프브이 감사보고서 (2025.12)", "2025-12-31", CASEQUARE),
        ("peach_pfv", "20260401001191", "퍼시픽피치피에프브이 감사보고서 (2025.12)", "2025-12-31", PEACH),
        ("camsquare_pfv", "20260413002070", "캄스퀘어안산데이터센터피에프브이 감사보고서 (2025.12)", "2025-12-31", CAMSQUARE),
    ]
    for target, rcept, title, as_of, rows in batches:
        src_id = f"dart_audit_{target}_{rcept}"
        if not any(s.get("id") == src_id for s in net.get("sources") or []):
            net.setdefault("sources", []).append({
                "id": src_id, "title": title, "publisher": "DART",
                "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept}",
                "kind": "filing", "dart_receipt_number": rcept, "used_for": "차입금 주석 당기말",
            })
        for eid, src, name, krw, rate, maturity, tranche in rows:
            promote(net, src, name)
            e = mk(target, rcept, title, as_of, eid, src, name, krw, rate, maturity, tranche)
            stats[upsert(net, e)] += 1
        for n in net["nodes"]:
            if n["id"] == target:
                n["connection_status"] = "관계 확인"
                n["dart_last_audit_rcept"] = rcept
                n["amount_as_of"] = as_of
                n["dart_borrowings_note"] = f"주석 당기말 대주 {len(rows)}건 매핑 (rcept {rcept})"

    NET.write_text(json.dumps(net, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(stats)


if __name__ == "__main__":
    main()
