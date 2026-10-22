import type { Network, SourcesResponse } from "../types";
import { KIND_KO } from "../lib/scenario";
import { GROUP_LABEL, REL_LABEL, STATUS_KO, domainOf, usdM } from "../lib/format";
import { cleanNote } from "../lib/labels";
import { IconLink } from "./Icons";
import { amountFacts, isHomepageUrl, CERTAINTY_SHORT } from "../lib/evidence";
import { SOURCE_STATUS_KO } from "../lib/labels";
import { findDuplicateProjects } from "../lib/dupCheck";

/** Every number the engine uses (section 6 audit). Kept next to the data so the screen and README agree. */
export const MODEL_INPUTS: { name: string; meaning: string; value: string; formula: string; basis: string; status: string }[] = [
  { name: "차환 대상 원금", meaning: "새 금리가 적용될 차입금 잔액", value: "차입금별 10-Q 잔액 (예: 2030 Notes $2.00B)", formula: "추가 이자 = 원금 × 성공비율 × (신규 − 기존)", basis: "10-Q 2026.6.30 Note Debt", status: "VERIFIED" },
  { name: "기존 표면금리 (고정)", meaning: "채권 쿠폰", value: "9.25% · 9.00% · 9.75% · 9.625% · 8.50% · 1.75%", formula: "기존 비교금리 (표면 기준)", basis: "발행 보도자료 · 10-Q", status: "VERIFIED" },
  { name: "가산금리 (변동)", meaning: "SOFR 위 추가 금리", value: "DDTL 3.0 4.00% · 4.0 2.25% · 5.0 4.50% · 5.5 5.50% (VERIFIED) / DDTL 1.0 9.62% · 2.1 4.25% (INFERRED)", formula: "기존 비교금리 = SOFR(하한 적용) + 가산금리", basis: "8-K · 보도자료 / 2차 집계", status: "VERIFIED / INFERRED" },
  { name: "SOFR", meaning: "변동금리 기준금리", value: "3.88% (2026-10-16)", formula: "위 식의 기준금리 · 사용자 수정 가능", basis: "NY Fed 데이터 재게시", status: "VERIFIED (시장 관측)" },
  { name: "유효이자율", meaning: "할인·발행비 상각 포함 금리", value: "차입금별 7~15% (정수 반올림 공시)", formula: "기존 비교금리 (유효 기준 또는 표면 미공시 시)", basis: "10-Q 표", status: "VERIFIED" },
  { name: "상반기 영업현금흐름 · 계약상 이자", meaning: "부담 크기 비교 기준", value: "$3.66B · $1.08B (6개월)", formula: "추가 이자 6개월분 ÷ 해당 실적", basis: "10-Q", status: "VERIFIED" },
  { name: "NVIDIA FY2026 매출", meaning: "GPU 구매 감소(가정)의 상대 크기", value: "$215.9B", formula: "GPU 구매 감소 ÷ NVIDIA 매출", basis: "NVIDIA 8-K 2026.2.25", status: "VERIFIED" },
  { name: "신규 차환금리 · 성공 비율 · 수수료 · 만기 · 시점", meaning: "시나리오 조건", value: "기본 12% · 100% · 0% · 5년 · 만기월", formula: "위 식의 입력", basis: "사용자 입력", status: "ASSUMED" },
  { name: "CAPEX 흡수율 · GPU 비중", meaning: "추가 이자가 투자 축소로 이어지는 정도", value: "기본 미입력 (계산 안 함)", formula: "CAPEX 축소 = 추가 이자 × 흡수율, GPU 감소 = CAPEX 축소 × 비중", basis: "사용자 입력 (공개 근거 없음)", status: "ASSUMED" },
];

export const REMOVED_INPUTS: { name: string; old: string; reason: string }[] = [
  { name: "출발 충격 점수", old: "감소율 × 100 (예: 70점)", reason: "경제적 단위가 없는 임의 척도 → 제거, USD 금액으로 대체" },
  { name: "공급망 · 서비스 의존도 9개", old: "5% ~ 50%", reason: "출처 없는 데모 가정 → 제거, 관계만 표시(D)" },
  { name: "충격 전달계수", old: "0.6 (GPU) · 1.0 (서비스)", reason: "근거 없음, 여러 단계 곱셈 금지 원칙 → 제거" },
  { name: "DEMO 기관 익스포저 · 회수율 · 자본", old: "$250M ~ $1.2B · 20 ~ 40% · 300 등", reason: "가상 기관 → 기관 5개와 연결선 5개 삭제" },
  { name: "연쇄 부도 기준", old: "자본 < 0", reason: "실존 기관의 보유액이 공시되지 않아 계산 대상 없음 → 신용손실 시나리오 제거" },
];

type Issue = { project_id: string; kind: string; text: string };
type Research = { version: string; date: string; method: string; amount_unit: string; principles: string[]; counts: Record<string, number> };

/** 국내 AI DC 조사 현황 — Claude v6 연구 메타 + 숨김 노드. */
function KrDcResearch({ net, onSelectNode, projects }: { net: Network; onSelectNode: (id: string) => void; projects?: { id: string; name?: string | null; name_ko?: string | null }[] }) {
  const projName = (id: string) => { const pp = projects?.find((x) => x.id === id); return pp ? (pp.name_ko || pp.name || id) : id.startsWith("kr_permit_") ? "인허가 사업장(명칭 미기재)" : id; };
  const meta = (net.meta as { kr_dc_research?: Research }).kr_dc_research;
  if (!meta) return null;
  const hidden = ((net as { hidden_nodes?: { id: string; name_ko?: string; name: string; group: string; research_status?: string; research_note?: string }[] }).hidden_nodes) || [];
  const issues = ((net as { kr_dc_issues?: Issue[] }).kr_dc_issues) || [];
  const kr = net.nodes.filter((n) => (n as { region?: string }).region === "KR") as (Network["nodes"][number] & { research_status?: string; research_note?: string })[];
  const rows = [
    ...kr.map((n) => ({ id: n.id, name: n.name_ko || n.name, group: n.group, status: n.research_status || "미분류", note: n.research_note || "", onMap: true })),
    ...hidden.map((n) => ({ id: n.id, name: n.name_ko || n.name, group: n.group, status: n.research_status || "자료 미발견", note: n.research_note || "", onMap: false })),
  ];
  const byStatus = new Map<string, number>();
  rows.forEach((r) => byStatus.set(r.status, (byStatus.get(r.status) || 0) + 1));
  const relCount = new Map<string, number>();
  for (const e of net.edges) {
    relCount.set(e.source, (relCount.get(e.source) || 0) + 1);
    relCount.set(e.target, (relCount.get(e.target) || 0) + 1);
  }
  return (
    <section className="sv-sec">
      <h3>국내 AI DC 조사 현황 ({meta.version} · {meta.date})</h3>
      <p className="tiny">{cleanNote(meta.method)}. 금액 단위 {meta.amount_unit}.</p>
      <ul className="tiny" style={{ margin: "4px 0 8px", paddingLeft: 16 }}>{meta.principles.map((x) => <li key={x}>{cleanNote(x)}</li>)}</ul>
      <div className="sv-status">
        {[...byStatus.entries()].map(([st, n]) => (
          <div key={st} className="sv-card"><b className="num">{n}</b><p>{st}</p></div>
        ))}
      </div>
      <p className="tiny muted">&apos;자료 미발견&apos;은 지도에서 숨기고 이 표에만 남깁니다. 근거를 찾지 못했다는 뜻이며 관계가 없다는 뜻이 아닙니다.</p>
      <div className="table-wrap">
        <table className="sv-table rs-table">
          <thead><tr><th>기업</th><th>분류</th><th>조사 상태</th><th>관계 수</th><th>지도</th><th>비고</th></tr></thead>
          <tbody>
            {rows.sort((a, b) => a.status.localeCompare(b.status) || a.name.localeCompare(b.name, "ko")).map((r) => (
              <tr key={r.id}>
                <td>{r.onMap ? <button type="button" className="linkish" onClick={() => onSelectNode(r.id)}>{r.name}</button> : r.name}</td>
                <td className="tiny">{GROUP_LABEL[r.group] || r.group}</td>
                <td className="tiny">{r.status}</td>
                <td className="num tiny">{relCount.get(r.id) || 0}</td>
                <td className="tiny">{r.onMap ? "표시" : "숨김"}</td>
                <td className="tiny">{r.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {issues.length ? (
        <>
          <h3 className="sv-h-sub">미확인 · 자료 상충 · 추가 확인 필요 ({issues.length})</h3>
          <div className="table-wrap">
            <table className="sv-table">
              <thead><tr><th>사업</th><th>구분</th><th>내용</th></tr></thead>
              <tbody>{issues.map((i, k) => <tr key={k}><td className="tiny">{projName(i.project_id)}</td><td className="tiny">{i.kind}</td><td className="tiny">{cleanNote(i.text)}</td></tr>)}</tbody>
            </table>
          </div>
        </>
      ) : null}
    </section>
  );
}

export function SourcesView({ net, sources, onSelectNode, onSelectContract, projects }: {
  net: Network; sources: SourcesResponse | null; onSelectNode: (id: string) => void; onSelectContract: (id: string) => void;
  projects?: { id: string; name?: string | null; name_ko?: string | null; address?: string | null }[];
}) {
  const names = new Map(net.nodes.map((n) => [n.id, n.name_ko || n.name]));
  const isPf = (net.meta as { ecosystem?: string }).ecosystem === "datacenter_pf";
  const fallbackCounts: Record<string, number> = {};
  for (const x of [...net.nodes, ...net.edges]) fallbackCounts[x.source_status] = (fallbackCounts[x.source_status] || 0) + 1;
  const counts = sources?.status_counts && Object.keys(sources.status_counts).length ? sources.status_counts : fallbackCounts;
  const today = net.meta.as_of;
  const isScenario = (e: Network["edges"][number]) => (e as { layer?: string }).layer === "scenario" || e.source_status === "ASSUMED";
  const factEdges = net.edges.filter((e) => !isScenario(e));
  const scenEdges = net.edges.filter(isScenario);
  const dups = projects ? findDuplicateProjects(projects) : [];
  const unlinked = (sources?.sources || net.sources).filter((s) => !s.url || isHomepageUrl(s.url)).length;
  return (
    <div className="sources-view">
      <header className="sv-head">
        <h2>Data &amp; Sources</h2>
        <p>기업 {net.nodes.length} · 관계 {net.edges.length} · 금융계약 {net.financials.instruments.length} · 출처 {net.sources.length}.
          {" "}<b>자료 기준일</b>(재무) {net.financials.as_of}{isPf ? "" : " (10-Q)"} · <b>데이터 정리일</b> {net.meta.as_of} · 가격 기준일은 Market 화면에 종목별로 표시합니다.
          {" "}확인되지 않은 값은 미확인으로 두고 숫자를 만들지 않습니다.</p>
      </header>
      <div className="sv-status">
        {(["VERIFIED", "INFERRED", "ASSUMED", "UNKNOWN"] as const).map((s) => (
          <div key={s} className="sv-card">
            <span className={`st-tag st-${s}`}>{s}</span>
            <b className="num">{counts[s] ?? 0}</b>
            <p>{STATUS_KO[s]} · 기업+관계 수</p>
          </div>
        ))}
      </div>

      <KrDcResearch net={net} onSelectNode={onSelectNode} projects={projects} />

      {dups.length ? (
        <section className="sv-sec">
          <h3>중복 의심 사업명 ({dups.length}그룹) · 자동 병합하지 않음</h3>
          <p className="tiny muted">한글명·영문명을 정규화했을 때 같은 이름이 되는 사업입니다. 이름이 같아도 다른 사업일 수 있어 자동으로 합치지 않으며, 원문 주소·허가번호로 개별 확인이 필요합니다.</p>
          <div className="table-wrap">
            <table className="sv-table">
              <thead><tr><th>정규화 이름</th><th>해당 사업 수</th><th>표기</th></tr></thead>
              <tbody>{dups.map((d) => <tr key={d.key}><td className="tiny">{d.key}</td><td className="tiny num" data-tip="개발용 사업 식별자">{d.ids.length}건</td><td className="tiny">{d.names.join(" / ")}</td></tr>)}</tbody>
            </table>
          </div>
        </section>
      ) : null}

      <section className="sv-sec">
        <h3>시나리오 가정 · 계산 입력 (사실 출처와 별도)</h3>
        <div className="table-wrap">
          <table className="sv-table">
            <thead><tr><th>값</th><th>경제적 의미</th><th>현재 값</th><th>적용 식</th><th>근거 · 출처</th><th>구분</th></tr></thead>
            <tbody>
              {MODEL_INPUTS.map((x) => (
                <tr key={x.name}><td>{x.name}</td><td>{x.meaning}</td><td className="num tiny">{x.value}</td><td className="tiny">{x.formula}</td><td className="tiny">{x.basis}</td><td className="tiny">{x.status}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <h3 className="sv-h-sub">v0.3까지 쓰던 근거 없는 계수 — v0.4에서 제거</h3>
        <div className="table-wrap">
          <table className="sv-table">
            <thead><tr><th>계수</th><th>이전 값</th><th>처리</th></tr></thead>
            <tbody>{REMOVED_INPUTS.map((x) => <tr key={x.name}><td>{x.name}</td><td className="num tiny">{x.old}</td><td className="tiny">{x.reason}</td></tr>)}</tbody>
          </table>
        </div>
      </section>

      <section className="sv-sec">
        <h3>Financing Contracts ({net.financials.instruments.length})</h3>
        <div className="table-wrap">
          <table className="sv-table">
            <thead><tr><th>계약</th><th>유형</th><th>잔액 ({net.financials.as_of})</th><th>금리</th><th>유효</th><th>만기</th><th>참여기관</th></tr></thead>
            <tbody>
              {net.financials.instruments.map((x) => (
                <tr key={x.id}>
                  <td><button type="button" className="linkish" onClick={() => onSelectContract(x.id)}>{x.name}</button></td>
                  <td className="tiny">{KIND_KO[x.kind]}</td>
                  <td className="num">{x.principal_usd_m !== null ? usdM(x.principal_usd_m) : "미공시"}</td>
                  <td className="num tiny">{x.coupon_pct !== null ? `${x.coupon_pct}%` : x.spread_pct !== null ? `SOFR+${x.spread_pct}%` : "—"} <span className={`st-tag st-${x.rate_status}`}>{x.rate_status}</span></td>
                  <td className="num">{x.effective_rate_pct !== null ? `${x.effective_rate_pct}%` : "—"}</td>
                  <td className="num">{x.maturity || "—"}</td>
                  <td className="tiny">{x.participants.map((q) => names.get(q.entity)).join(", ") || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="sv-sec">
        <h3>확인·추론된 관계 ({factEdges.length})</h3>
        <div className="table-wrap">
          <table className="sv-table">
            <thead><tr><th>관계</th><th>유형</th><th>역할</th><th>금액</th><th>구분</th></tr></thead>
            <tbody>
              {factEdges.map((e) => {
                const f = amountFacts(e, today);
                return (
                <tr key={e.id}>
                  <td><button type="button" className="linkish" onClick={() => onSelectNode(e.source)}>{names.get(e.source)}</button> — <button type="button" className="linkish" onClick={() => onSelectNode(e.target)}>{names.get(e.target)}</button><div className="tiny muted">{e.label}</div></td>
                  <td className="tiny">{REL_LABEL[e.relationship_type] || e.relationship_type}</td>
                  <td className="tiny">{(e.roles || []).join(", ") || "—"}</td>
                  <td className="num tiny">{f.value === null ? "미확인" : f.unit === "억원" ? `${f.value.toLocaleString("ko-KR")}억` : usdM(f.value)}{f.value !== null && f.certainty !== "confirmed" ? ` (${CERTAINTY_SHORT[f.certainty]})` : ""}<div className="muted">{f.kindKo}</div></td>
                  <td><span className={`st-tag st-${e.source_status}`} data-tip={SOURCE_STATUS_KO[e.source_status]}>{e.source_status}</span></td>
                </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {scenEdges.length ? (
        <section className="sv-sec">
          <h3>시나리오 가정 관계 ({scenEdges.length}) · 사실 근거 아님</h3>
          <div className="table-wrap">
            <table className="sv-table">
              <thead><tr><th>관계</th><th>설명</th></tr></thead>
              <tbody>{scenEdges.map((e) => <tr key={e.id}><td>{names.get(e.source)} — {names.get(e.target)}</td><td className="tiny">{e.explanation || e.label}</td></tr>)}</tbody>
            </table>
          </div>
        </section>
      ) : null}

      <section className="sv-sec">
        <h3>Sources ({net.sources.length}){unlinked ? ` · 원문 연결 미확보 ${unlinked}건` : ""}</h3>
        <div className="table-wrap">
          <table className="sv-table">
            <thead><tr><th>자료</th><th>발행</th><th>일자</th><th>사용 내용</th></tr></thead>
            <tbody>
              {(sources?.sources || net.sources).map((s) => (
                <tr key={s.id}>
                  <td>{s.url && !isHomepageUrl(s.url)
                    ? <a href={s.url} target="_blank" rel="noreferrer">{s.title} <IconLink size={11} /></a>
                    : <>{s.title} <span className="tiny muted">· 원문 연결 미확보{s.url ? " (홈페이지 주소만)" : ""}</span></>}
                    <div className="tiny muted">{s.url ? domainOf(s.url) : "—"}</div></td>
                  <td className="tiny">{s.publisher}</td>
                  <td className="num">{s.date}</td>
                  <td className="tiny">{s.used_for}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
