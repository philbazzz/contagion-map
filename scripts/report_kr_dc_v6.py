#!/usr/bin/env python3
"""국내 AI DC v6 조사 보고서(docs/KR_DC_RESEARCH_V6.md) 생성 — 수치는 빌드 산출물에서 직접 집계."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PF = ROOT / "frontend" / "public" / "data" / "pf"
OUT = ROOT / "docs" / "KR_DC_RESEARCH_V6.md"

LOANS = {"PROJECT_LOAN", "ACQUISITION_LOAN", "REVOLVER"}
PAST = {"repaid", "terminated", "historical", "withdrawn"}


def eok(v):
    return "미공개" if v is None else f"{v:,.0f}억" if float(v).is_integer() else f"{v:,.1f}억"


def main() -> None:
    net = json.load(open(PF / "network.json", encoding="utf-8"))
    pj = json.load(open(PF / "projects.json", encoding="utf-8"))
    log = json.load(open(PF / "kr_dc_changelog.json", encoding="utf-8"))
    val = json.load(open(PF / "_validation_v6.json", encoding="utf-8"))
    names = {n["id"]: n.get("name_ko") or n["name"] for n in net["nodes"] + net.get("hidden_nodes", [])}
    v6 = [e for e in net["edges"] if e.get("added_in") == "v6"]
    projects = [p for p in pj["projects"] if p.get("research_v6")]
    issues = net.get("kr_dc_issues", [])
    L: list[str] = []
    w = L.append

    w("# 국내 AI 데이터센터 개발사업 조사 · 반영 결과 (v6)")
    w("")
    w(f"기준일 {log['as_of']} · 금액 단위 억원 · 이 문서는 `python scripts/report_kr_dc_v6.py`로 빌드 산출물에서 자동 생성됩니다.")
    w("")
    w("## 1. 조사 방법과 범위")
    w("")
    w("- 1차 근거: DART 사업법인(PFV·SPC·시행사) 감사보고서 주석(주주·차입금·약정·담보신탁·특수관계자), 건설사·계열사 공시(채무보증결정·단일판매공급계약·유상증자·담보제공). KIND 거래소 공시 포함.")
    w("- 2차 근거: 신뢰 가능한 언론 보도와 회사 공식 발표. 언론만으로 확인한 관계는 `evidence_kind=언론`으로 구분합니다.")
    w("- 원칙: MOU를 실행으로 바꾸지 않음 · 신디케이트 총액을 각 대주에 배분하지 않음 · 주선사 딜 규모를 익스포저로 쓰지 않음 · 펀드 자금을 운용사 고유자금으로 쓰지 않음 · 과거 금액을 현재 잔액으로 쓰지 않음 · 도급액을 미수금으로 쓰지 않음 · 미공개는 0이 아니라 null.")
    w("- 한계: 유료 기사(더벨 등) 본문은 우회하지 않았습니다. 펀드 수익자·대주단 내부 배분·현재 잔액은 비공개인 경우가 많아 '미공개'로 남겼습니다. '자료 미발견' 70곳은 DART 감사보고서 30여 건의 대주·주주·보증 명부 대조와 이름 검색 결과이며, 기업별 전수 공시 검색을 한 것은 아닙니다.")
    w("")

    w("## 2. 사업별 조사 결과")
    w("")
    w("| 사업 | 차주(SPV) | 단계 | 확인 관계 | 현재 대출 약정(공시 합산) | 실행액 | 근거 |")
    w("|---|---|---|---:|---:|---:|---|")
    by_p = defaultdict(list)
    for e in net["edges"]:
        if e.get("project_id") and e.get("layer") != "scenario":
            by_p[e["project_id"]].append(e)
    for p in sorted(projects, key=lambda x: x["id"]):
        es = by_p.get(p["id"], [])
        cur = [e for e in es if e.get("relationship_status") not in PAST]
        loans = [e for e in cur if e["relationship_type"] in LOANS and e.get("amount_type") == "institution_commitment"]
        known = [e for e in loans if e.get("amount_krw_eok") is not None]
        commit = sum(e["amount_krw_eok"] for e in known)
        unk = len(loans) - len(known)
        drawn_rows = [e for e in loans if e.get("drawn_krw_eok") is not None]
        commit_txt = (f"{eok(commit)} ({len(known)}건{f' · 미공개 {unk}건' if unk else ''})" if known
                      else (f"미공개 ({unk}건)" if unk else "미공개"))
        kinds = Counter(e.get("evidence_kind") or "기존" for e in es)
        w(f"| {p.get('name_ko') or p['name']} | {names.get(p.get('spv'), p.get('spv') or '미확인')} | {p.get('stage_ko') or ''} | {len(es)} | "
          f"{commit_txt} | {eok(sum(e['drawn_krw_eok'] for e in drawn_rows)) if drawn_rows else '미공개'} | "
          f"{', '.join(f'{k} {v}' for k, v in kinds.most_common())} |")
    w("")
    w("현재 대출 약정은 상환되지 않은 대출성 관계(PF·인수금융·신용공여)의 기관별 약정만 더한 값입니다. 보증한도·우선수익권 한도·도급액·주선 규모는 더하지 않습니다.")
    w("")

    w("## 3. 기업별 조사 상태")
    w("")
    rows = [n for n in net["nodes"] if n.get("region") == "KR"] + net.get("hidden_nodes", [])
    st = Counter(n.get("research_status") or "미분류" for n in rows)
    w("| 조사 상태 | 기업 수 | 지도 |")
    w("|---|---:|---|")
    for k, v in st.most_common():
        w(f"| {k} | {v} | {'숨김 (데이터에 유지)' if k == '자료 미발견' else '표시'} |")
    w("")
    w("기업별 전체 목록: `frontend/public/data/pf/kr_dc_entity_status.csv` (앱의 Data & Sources 화면에도 표시).")
    w("'접근 제한'으로 분류한 기업은 없습니다. 유료 기사로만 언급된 사항은 아래 6절 미확인 목록에 사업별로 적었습니다.")
    w("")

    w("## 4. 관계·출처 목록")
    w("")
    ek = Counter(e.get("evidence_kind") for e in v6)
    w(f"- 새로 반영한 관계 {len(v6)}건 (공시 {ek.get('공시', 0)} · 언론 {ek.get('언론', 0)} · 공식발표 {ek.get('공식발표', 0)}). 모든 관계에 출처 URL·일자가 있고, 공시는 접수번호(rcept_no)와 원문 인용을 함께 기록했습니다.")
    w("- 파일: `frontend/public/data/pf/kr_dc_relationships.csv` / `.json` (관계별 금액·금액유형·실행액·순위·금리·만기·상태·조건부 의무·발동 조건·충격 방향·출처).")
    rt = Counter(e["relationship_type"] for e in v6)
    w("- 관계 유형: " + ", ".join(f"{k} {v}" for k, v in rt.most_common()))
    w("")

    w("## 5. 변경 내역")
    w("")
    w(f"- 추가 기업 {len(log['added_nodes'])} · 추가 관계 {len(log['added_edges'])} · 추가 사업 {len(log['projects_added'])} · 갱신 사업 {len(log['projects_updated'])}")
    w(f"- 숨김 처리 {len(log['hidden_nodes'])} (근거 미발견 · 데이터에는 유지)")
    w("")
    w("### 병합 (ID 하나로 통합, 이전 ID는 별칭으로 보존)")
    for m in log["merged"]:
        w(f"- `{m['from']}` → `{m['to']}` ({names.get(m['to'], m['to'])})")
    w("")
    w("### 삭제")
    for d in log["deleted_nodes"]:
        w(f"- `{d['id']}` — {d['reason']}")
    w("")
    w("### 공시 근거로 대체한 기존 관계 (v5 → v6)")
    for r in log["replaced_edges"]:
        w(f"- `{r['id']}` — {r['reason']}")
    w("")
    w("### 상태를 정정한 기존 관계")
    for r in log["patched_edges"]:
        note = r["patch"].get("note_add") or ""
        w(f"- `{r['id']}` → {r['patch'].get('relationship_status') or r['patch'].get('layer') or ''} · {note}")
    w("")
    w("### 사업 메타데이터 정정")
    for r in log.get("project_field_fixes", []):
        extra = f" ({r.get('from')} → {r.get('to')})" if r.get("to") else ""
        w(f"- `{r['project']}` · {r['field']}{extra} — {r['reason']}")
    w("")

    w("## 6. 미확인 · 자료 상충 · 추가 확인 필요")
    w("")
    w("| 사업 | 구분 | 내용 |")
    w("|---|---|---|")
    for i in issues:
        w(f"| {i['project_id']} | {i['kind']} | {i['text'].replace('|', '/')} |")
    w("")

    w("## 7. 데이터 검증 결과")
    w("")
    w(f"`python scripts/validate_kr_dc_v6.py` → **{'PASSED' if val['passed'] else 'FAILED'}** ({sum(c['pass'] for c in val['checks'])}/{len(val['checks'])} 검사 통과)")
    w("")
    for c in val["checks"]:
        w(f"- {'통과' if c['pass'] else '실패'} · {c['check']}")
    w("")
    w("## 8. 실행 방법")
    w("")
    w("```bat")
    w("rem Windows — 기존과 동일")
    w("start.bat            & rem 백엔드(:8000) + 프런트(:5173)")
    w("preview.bat          & rem 서버 없이 정적 미리보기(:4173)")
    w("```")
    w("")
    w("데이터를 다시 만들 때 (원장 수정 후):")
    w("")
    w("```bash")
    w("python scripts/build_kr_dc_v6.py      # v5 기준본(scripts/data/pf_v5_baseline) + 조사 원장 → frontend/public/data/pf/*")
    w("python scripts/validate_kr_dc_v6.py   # 금액 합계·중복 배분·참조 무결성·표시 규칙 검사")
    w("python scripts/validate_pf_finance_v5.py")
    w("python scripts/report_kr_dc_v6.py     # 이 문서 재생성")
    w("```")
    w("")
    w("앱에서 보는 법: 상단 `AI DATA CENTER PF` → 좌측 '확인된 사업'에서 사업 클릭(참여자·금융 이력·미확인 사항), 회사 클릭(참여 사업·역할·조건부 의무·같은 사업의 간접 상대방), 관계선·관계 행 클릭(쉬운 설명·근거·공시 접수번호·원문 인용). 좌측 필터(기관 유형·금융 단계·투자·신용 경로·근거·상태)는 목록과 3D 지도에 함께 적용됩니다. `Data & Sources` 화면에 기업별 조사 상태와 미확인 목록이 있습니다.")
    w("")
    w("OpenDART API 키는 조사 중 조회에만 사용했고 코드·데이터·이 저장소 어디에도 저장하지 않았습니다.")
    w("")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("wrote", OUT, len(L), "lines")


if __name__ == "__main__":
    main()
