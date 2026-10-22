/** Compact Korean PF shock summary — details only on expand / company click. */
import { useMemo, useState, type ReactNode } from "react";
import type { PfAffectedCompany, PfImpactCategory, PfShockResult } from "../pf/types";

const CATEGORIES: PfImpactCategory[] = [
  "상환·차환 부담 증가",
  "보증·추가 자금부담 가능",
  "대출·투자금 손실 가능",
  "매출·수주 영향",
  "영향 규모 판단 불가",
];

type ViewMode = "summary" | "all" | "paths" | "detail";

function rankScore(c: PfAffectedCompany): number {
  let s = c.basis === "quantified" ? 60 : c.basis === "contract" ? 30 : 0;
  if (c.directness === "direct") s += 40;
  if (c.impact_category === "대출·투자금 손실 가능") s += 30;
  else if (c.impact_category === "보증·추가 자금부담 가능") s += 25;
  else if (c.impact_category === "상환·차환 부담 증가") s += 20;
  else if (c.impact_category === "매출·수주 영향") s += 10;
  for (const p of c.projects) {
    if (p.amount_krw_eok != null) s += Math.min(25, Math.log10(1 + p.amount_krw_eok) * 8);
    if (!p.contingent) s += 5;
  }
  if (!c.default_assessment.includes("자료 부족")) s += 8;
  return s;
}

function sharedMechanisms(rows: PfAffectedCompany[]): { label: string; count: number; path: string }[] {
  const m = new Map<string, { count: number; path: string }>();
  for (const r of rows) {
    const key = r.impact_category;
    const cur = m.get(key) || { count: 0, path: r.transmission_path.split(" → ").slice(0, 3).join(" → ") };
    cur.count += 1;
    m.set(key, cur);
  }
  return [...m.entries()]
    .map(([label, v]) => ({ label, count: v.count, path: v.path }))
    .sort((a, b) => b.count - a.count);
}

export function PfAffectedCompaniesPanel({
  result,
  selectedId,
  onSelectCompany,
  collapsed,
  onToggleCollapse,
}: {
  result: PfShockResult | null;
  selectedId: string | null;
  onSelectCompany: (companyId: string, edgeIds: string[]) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}) {
  const [view, setView] = useState<ViewMode>("summary");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const rows = result?.pf?.affected_companies || [];
  const ranked = useMemo(() => [...rows].sort((a, b) => rankScore(b) - rankScore(a)), [rows]);
  const top5 = ranked.slice(0, 5);
  const mechanisms = useMemo(() => sharedMechanisms(rows), [rows]);

  const stats = useMemo(() => {
    const projects = new Set(rows.flatMap((r) => r.projects.map((p) => p.project_id)));
    // Count related deals by evidence level — amounts of different kinds/dates are never added here.
    const seen = new Set<string>();
    let amtKnown = 0, amtUnknown = 0;
    for (const r of rows) {
      for (const p of r.projects) {
        if (seen.has(p.edge_id)) continue;
        seen.add(p.edge_id);
        if (p.amount_type === "facility_total_context" || p.amount_type === "underwrite_commitment") continue;
        if (p.amount_krw_eok != null && !/추정/.test(p.amount_note || "")) amtKnown += 1; else amtUnknown += 1;
      }
    }
    const maxPath = ranked[0]?.transmission_path || "—";
    return { projects: projects.size, amtKnown, amtUnknown, maxPath };
  }, [rows, ranked]);

  if (!result) {
    return (
      <section className="lp-sec pf-affected pf-shock-summary">
        <h3 className="lbl">SHOCK IMPACT</h3>
        <p className="fine">시나리오를 적용하면 요약만 표시됩니다. 기업별 설명은 클릭 시에만 펼칩니다.</p>
      </section>
    );
  }

  if (collapsed) {
    return (
      <section className="lp-sec pf-affected pf-shock-summary is-collapsed">
        <button type="button" className="btn-text" onClick={onToggleCollapse}>
          SHOCK IMPACT · 영향 {rows.length}개 · 패널 펼치기
        </button>
      </section>
    );
  }

  if (!rows.length) {
    return (
      <section className="lp-sec pf-affected pf-shock-summary">
        <h3 className="lbl">SHOCK IMPACT <span className="lbl-aside">0</span></h3>
        <p className="note">기준선(추가 충격 없음)이거나 증가된 스트레스 대상이 없습니다.</p>
      </section>
    );
  }

  const listForView = view === "summary" ? top5 : ranked;

  return (
    <section className="lp-sec pf-affected pf-shock-summary">
      <div className="pf-shock-head">
        <h3 className="lbl">SHOCK IMPACT <span className="lbl-aside">{rows.length}</span></h3>
        {onToggleCollapse ? (
          <button type="button" className="btn-text" onClick={onToggleCollapse}>패널 접기</button>
        ) : null}
      </div>

      <dl className="pf-shock-kpis">
        <div data-tip="충격 입력으로 모형상 스트레스 단계가 '정상'보다 올라간 기업 수(중복 제거). 손실·부도 확인이 아닙니다."><dt>스트레스 상승 기업</dt><dd className="num">{rows.length}</dd></div>
        <div data-tip="관련 사업장 수(중복 제거)"><dt>관련 사업장</dt><dd className="num">{stats.projects}</dd></div>
        <div data-tip="공시로 금액이 확인된 관련 거래 수. 유형이 다른 금액은 합산하지 않습니다."><dt>금액 확인 거래</dt><dd className="num">{stats.amtKnown}</dd></div>
        <div data-tip="금액이 공개되지 않았거나 추정인 관련 거래 수 — 0으로 처리하지 않음"><dt>금액 미확인·추정</dt><dd className="num">{stats.amtUnknown}</dd></div>
      </dl>
      <p className="fine pf-shock-path"><b>대표 전달 경로</b> <span className="muted">(근거 수준이 가장 높은 순)</span><br />{stats.maxPath}</p>

      <div className="pf-mech-block">
        <p className="lbl">공통 충격 경로</p>
        <ul className="pf-mech-list">
          {mechanisms.slice(0, 4).map((m) => (
            <li key={m.label}>
              <b>{m.label}</b> · {m.count}개 기관
              <div className="fine muted">{m.path}</div>
            </li>
          ))}
        </ul>
      </div>

      <div className="seg seg-wrap pf-shock-views" role="group" aria-label="결과 보기">
        <button type="button" className={view === "summary" ? "is-on" : ""} onClick={() => setView("summary")}>주요 5개</button>
        <button type="button" className={view === "all" ? "is-on" : ""} onClick={() => setView("all")}>전체 보기</button>
        <button type="button" className={view === "paths" ? "is-on" : ""} onClick={() => setView("paths")}>주요 경로</button>
        <button type="button" className={view === "detail" ? "is-on" : ""} onClick={() => setView("detail")}>기업별 상세</button>
      </div>

      {view === "paths" ? (
        <ul className="pf-mech-list">
          {mechanisms.map((m) => (
            <li key={m.label}>
              <b>{m.label}</b> ({m.count})
              <div className="fine">{m.path}</div>
              <p className="fine muted">기관 목록은 &apos;전체 보기&apos;에서 확인</p>
            </li>
          ))}
        </ul>
      ) : (
        <ul className="ent-list pf-aff-list pf-aff-compact">
          {view === "detail"
            ? CATEGORIES.flatMap((cat) => {
              const list = ranked.filter((r) => r.impact_category === cat);
              if (!list.length) return [] as ReactNode[];
              return [
                <li key={`h-${cat}`} className="pf-aff-cat-h">
                  <span className="lbl">{cat} <span className="lbl-aside">{list.length}</span></span>
                </li>,
                ...list.map((r) => (
                  <CompanyRow
                    key={r.company_id}
                    r={r}
                    selectedId={selectedId}
                    expanded={expandedId === r.company_id || view === "detail"}
                    onToggle={() => setExpandedId(expandedId === r.company_id ? null : r.company_id)}
                    onSelect={onSelectCompany}
                  />
                )),
              ];
            })
            : listForView.map((r) => (
              <CompanyRow
                key={r.company_id}
                r={r}
                selectedId={selectedId}
                expanded={expandedId === r.company_id}
                onToggle={() => setExpandedId(expandedId === r.company_id ? null : r.company_id)}
                onSelect={onSelectCompany}
              />
            ))}
        </ul>
      )}

      {view === "summary" && ranked.length > 5 ? (
        <button type="button" className="btn-text" onClick={() => setView("all")}>
          나머지 {ranked.length - 5}개 기관 보기
        </button>
      ) : null}
      <p className="fine muted">주선·인수만으로는 대출손실을 전파하지 않습니다. 약정 총액 ≠ 보유 익스포저.</p>
    </section>
  );
}

function CompanyRow({
  r, selectedId, expanded, onToggle, onSelect,
}: {
  r: PfAffectedCompany;
  selectedId: string | null;
  expanded: boolean;
  onToggle: () => void;
  onSelect: (id: string, edgeIds: string[]) => void;
}) {
  const uncertain = r.default_assessment.includes("자료 부족");
  return (
    <li>
      <div className="pf-aff-row-wrap">
        <button
          type="button"
          className={`ent pf-aff-row ${selectedId === r.company_id ? "is-on" : ""} ${uncertain ? "is-uncertain" : ""}`}
          onClick={() => onSelect(r.company_id, r.projects.map((p) => p.edge_id))}
        >
          <span className={`dot ${r.directness === "direct" ? "dot-direct" : "dot-indirect"}`} />
          <span className="ent-name wrap">{r.company_name}</span>
          <span className={`cert cert-${r.basis === "quantified" ? "confirmed" : r.basis === "contract" ? "inferred" : "assumed"}`}>{r.basis === "quantified" ? "정량" : r.basis === "contract" ? "계약 근거" : "가정 경로"}</span>
        </button>
        <button type="button" className="btn-text pf-aff-expand" onClick={onToggle} aria-expanded={expanded}>
          {expanded ? "접기" : "상세"}
        </button>
      </div>
      {expanded ? (
        <div className="pf-aff-detail">
          <p className="fine"><b>범주</b> {r.impact_category} · {r.directness === "direct" ? "직접 관계" : "간접 경로"}</p>
          <p className="fine"><b>경로</b> {r.transmission_path}</p>
          {r.projects.length ? (
            <ul className="pf-aff-proj">
              {r.projects.slice(0, 6).map((p) => (
                <li key={p.edge_id}>
                  <span className="wrap">{p.project_name}</span>
                  <span className="muted"> · {p.exposure_label}</span>
                  <span className="num"> · {p.amount_krw_eok != null ? `${p.amount_krw_eok.toLocaleString("ko-KR")}억${/추정/.test(p.amount_note || "") ? " (추정)" : ""}` : "금액 미확인"}</span>
                  {p.contingent ? <span className="warn"> · 조건부</span> : null}
                </li>
              ))}
            </ul>
          ) : null}
          <p className="fine warn">{r.default_assessment}</p>
          <p className="fine wrap">{r.explanation_ko}</p>
        </div>
      ) : null}
    </li>
  );
}
