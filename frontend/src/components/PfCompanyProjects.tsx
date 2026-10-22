/** Group a company's verified PF edges by project for the detail panel. */
import type { ReactNode } from "react";
import type { Network, NetEdge, NetNode } from "../types";
import type { PfProject } from "../pf/types";
import { displayName, projectDisplayName } from "../lib/displayName";
import { AMOUNT_TYPE_KO, EVIDENCE_STATUS_KO, FINANCING_STAGE_KO, REL_LABEL } from "../lib/format";

function Sec({ label, aside, children }: { label: string; aside?: ReactNode; children: ReactNode }) {
  return (
    <section className="rp-sec">
      <h3 className="lbl">{label}{aside ? <span className="lbl-aside">{aside}</span> : null}</h3>
      {children}
    </section>
  );
}

function amtDisplay(e: NetEdge): string {
  const note = e.amount_note || "";
  const eok = (e as { amount_krw_eok?: number | null }).amount_krw_eok;
  if (eok != null && !Number.isNaN(eok)) {
    return `${eok.toLocaleString("ko-KR")}억 원`;
  }
  if (note.includes("금액 미공개") || note.includes("미공시") || note.includes("미기재")) {
    return "금액 미공개";
  }
  if (e.amount_usd_m != null) return note || `≈ $${e.amount_usd_m}M`;
  return note || "금액 미공개";
}

function edgeMeta(e: NetEdge) {
  const stage = (e as { financing_stage?: string }).financing_stage;
  const amtType = (e as { amount_type?: string }).amount_type;
  const ev = (e as { evidence_status?: string }).evidence_status;
  const path = (e as { participation_path?: string }).participation_path;
  const contingent = (e as { contingent_obligation?: boolean }).contingent_obligation;
  const seniority = (e as { seniority?: string }).seniority;
  const facility = (e as { facility_total_krw_eok?: number | null }).facility_total_krw_eok;
  const status = (e as { relationship_status?: string }).relationship_status;
  return { stage, amtType, ev, path, contingent, seniority, facility, status };
}

export function PfCompanyProjectsBlock({
  companyId,
  net,
  projects,
  onSelectNode,
  onSelectEdge,
}: {
  companyId: string;
  net: Network;
  projects?: PfProject[];
  onSelectNode: (id: string) => void;
  onSelectEdge: (id: string) => void;
}) {
  const nodeMap = new Map(net.nodes.map((n) => [n.id, n]));
  const links = net.edges.filter((e) => e.source === companyId || e.target === companyId);
  const byProject = new Map<string, { meta?: PfProject; edges: NetEdge[] }>();

  for (const e of links) {
    const pid = (e as { project_id?: string }).project_id
      || (projects || []).find((pr) => pr.spv === e.source || pr.spv === e.target || pr.id === e.source || pr.id === e.target)?.id
      || "_none";
    if (!byProject.has(pid)) {
      byProject.set(pid, { meta: projects?.find((p) => p.id === pid), edges: [] });
    }
    byProject.get(pid)!.edges.push(e);
  }

  for (const pr of projects || []) {
    const roles: string[] = [];
    if (pr.developer === companyId) roles.push("developer");
    if (pr.operator === companyId) roles.push("operator");
    if (pr.owner === companyId) roles.push("owner");
    if (pr.spv === companyId) roles.push("spv");
    if (!roles.length) continue;
    if (!byProject.has(pr.id)) {
      byProject.set(pr.id, { meta: pr, edges: [] });
    }
    const bucket = byProject.get(pr.id)!;
    (bucket as { participation_roles?: string[]; participation_gap?: string }).participation_roles = roles;
    if (!bucket.edges.length) {
      (bucket as { participation_gap?: string }).participation_gap =
        "사업 참여는 확인되나 회사↔회사 계약 상대가 미확인 — 엣지를 만들지 않음";
    }
  }

  if (!byProject.size) return null;

  const PAST = new Set(["repaid", "terminated", "historical", "withdrawn", "expired", "refinanced", "transferred",
    "FULLY_REPAID", "REFINANCED", "TRANSFERRED", "EXPIRED", "HISTORICAL_ONLY"]);
  const ARRANGE = new Set(["ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT"]);
  const LOAN = new Set(["PROJECT_LOAN", "ACQUISITION_LOAN", "CORPORATE_LOAN", "BRIDGE_LOAN", "DIRECT_LOAN", "MORTGAGE_LOAN", "PROJECT_FINANCE_LOAN"]);
  const EQUITY = new Set(["EQUITY_INVESTMENT", "EQUITY_SPONSOR", "PREFERRED_EQUITY", "SHAREHOLDER_LOAN", "SUBORDINATED_INVESTMENT"]);
  const GUAR = new Set(["CREDIT_ENHANCEMENT", "COMPLETION_GUARANTEE", "DEBT_ASSUMPTION", "LOAN_GUARANTEE", "FINANCIAL_GUARANTEE", "LIQUIDITY_COMMITMENT", "REFINANCING_UNDERWRITE"]);

  function isPast(e: NetEdge) {
    const st = (e as { exposure_status?: string }).exposure_status || (e as { relationship_status?: string }).relationship_status || "";
    return PAST.has(st) || PAST.has(st.toUpperCase());
  }
  function sumVerified(pred: (e: NetEdge) => boolean): { eok: number | null; known: number; unknown: number } {
    let eok = 0; let known = 0; let unknown = 0; let any = false;
    for (const e of links) {
      if (!pred(e) || isPast(e)) continue;
      const amtType = (e as { amount_type?: string }).amount_type;
      if (amtType === "facility_total_context" || amtType === "fee_paid" || amtType === "underwrite_commitment") continue;
      any = true;
      const v = (e as { amount_krw_eok?: number | null }).amount_krw_eok;
      if (v != null) { eok += v; known += 1; }
      else unknown += 1;
    }
    if (!any) return { eok: null, known: 0, unknown: 0 };
    return { eok: known ? eok : null, known, unknown };
  }

  const loan = sumVerified((e) => LOAN.has(e.relationship_type));
  const equity = sumVerified((e) => EQUITY.has(e.relationship_type));
  const guar = sumVerified((e) => GUAR.has(e.relationship_type) || !!(e as { contingent_obligation?: boolean }).contingent_obligation);
  const activeProjects = [...byProject.keys()].filter((k) => k !== "_none" && byProject.get(k)!.edges.some((e) => !isPast(e) && !ARRANGE.has(e.relationship_type)));
  const arrangerProjects = [...byProject.keys()].filter((k) => k !== "_none" && byProject.get(k)!.edges.some((e) => ARRANGE.has(e.relationship_type)));
  const repaid = links.filter((e) => isPast(e)).length;
  const lastVerified = links
    .map((e) => (e as { last_verified_date?: string; source_date?: string }).last_verified_date
      || (e as { source_date?: string }).source_date || "")
    .filter(Boolean)
    .sort()
    .at(-1) || "—";

  const fmtEok = (s: { eok: number | null; known: number; unknown: number }) => {
    if (s.known && s.eok != null) {
      const base = `${Math.round(s.eok).toLocaleString("ko-KR")}억`;
      return s.unknown ? `${base} (미확인 ${s.unknown}건)` : base;
    }
    if (s.unknown) return "미확인";
    return "해당 없음 / 미확인";
  };

  return (
    <>
      <Sec label="현재 확인된 데이터센터 금융 익스포저" aside={`${links.length}건`}>
        <p className="fine">주선·인수 총액은 보유 익스포저에 합산하지 않습니다. 검증된 잔액만 표시하며, Unknown은 0으로 두지 않습니다.</p>
        <dl>
          <div className="kv"><dt>대출잔액</dt><dd className="num">{fmtEok(loan)}</dd></div>
          <div className="kv"><dt>지분투자</dt><dd className="num">{fmtEok(equity)}</dd></div>
          <div className="kv"><dt>보증·확약</dt><dd className="num">{fmtEok(guar)}</dd></div>
          <div className="kv"><dt>참여 사업장</dt><dd className="num">{activeProjects.length}</dd></div>
          <div className="kv"><dt>과거 주선 사업장</dt><dd className="num">{arrangerProjects.length}</dd></div>
          <div className="kv"><dt>상환·종료 거래</dt><dd className="num">{repaid}</dd></div>
          <div className="kv"><dt>최종 확인일</dt><dd className="num">{lastVerified}</dd></div>
        </dl>
        <p className="fine muted">위 항목을 단순 합산한 값을 순위험으로 제시하지 않습니다.</p>
      </Sec>
      <Sec label="사업장별 포지션" aside={`${byProject.size}건`}>
        <div className="pf-pos-table-wrap">
          <table className="pf-pos-table">
            <thead>
              <tr>
                <th>사업장</th>
                <th>참여형태</th>
                <th>현재 잔액</th>
                <th>상태</th>
                <th>출처</th>
              </tr>
            </thead>
            <tbody>
              {[...byProject.entries()].flatMap(([pid, bucket]) => {
                const title = bucket.meta
                  ? projectDisplayName(bucket.meta)
                  : pid === "_none" ? "사업 미기재" : pid;
                if (!bucket.edges.length) {
                  return [(
                    <tr key={`${pid}-gap`}>
                      <td className="wrap">{title}</td>
                      <td>{(bucket as { participation_roles?: string[] }).participation_roles?.join(", ") || "—"}</td>
                      <td>N/A</td>
                      <td>UNVERIFIED</td>
                      <td>—</td>
                    </tr>
                  )];
                }
                return bucket.edges.map((e) => {
                  const m = edgeMeta(e);
                  const past = isPast(e);
                  const arr = ARRANGE.has(e.relationship_type);
                  const amtType = m.amtType || "";
                  const status = past
                    ? ((m.status || "HISTORICAL").toUpperCase())
                    : arr ? "HISTORICAL_ARRANGEMENT"
                      : (e as { exposure_status?: string }).exposure_status
                        || (m.status === "funded" || m.status === "current" || m.status === "committed" ? "ACTIVE_CONFIRMED" : (m.status || "ACTIVE_AMOUNT_UNKNOWN").toUpperCase());
                  const bal = arr || amtType === "facility_total_context"
                    ? "N/A (주선·시설총액)"
                    : past && (m.status === "repaid" || status.includes("REPAID"))
                      ? "0 (상환)"
                      : amtDisplay(e);
                  const src = (e as { source_url?: string }).source_url;
                  const srcTitle = (e as { source_title?: string }).source_title || "출처";
                  return (
                    <tr key={e.id} className={past || arr ? "is-hist" : ""}>
                      <td className="wrap">
                        <button type="button" className="link" onClick={() => onSelectEdge(e.id)}>{title}</button>
                      </td>
                      <td>{REL_LABEL[e.relationship_type] || e.relationship_type}{m.contingent ? " · 조건부" : ""}</td>
                      <td className="num">{bal}</td>
                      <td>{status}</td>
                      <td>{src ? <a href={src} target="_blank" rel="noreferrer">{srcTitle}</a> : (EVIDENCE_STATUS_KO[m.ev || ""] || m.ev || "—")}</td>
                    </tr>
                  );
                });
              })}
            </tbody>
          </table>
        </div>
      </Sec>
      <Sec label="관련 사업 · 자금 경로" aside={`${byProject.size}건`}>
        <p className="fine">프로젝트·주소는 맥락입니다. 맵 노드는 회사·PFV만 표시합니다.</p>
        {[...byProject.entries()].map(([pid, bucket]) => {
          const title = bucket.meta
            ? projectDisplayName(bucket.meta)
            : pid === "_none"
              ? "사업 미기재 관계"
              : pid;
          const loc = bucket.meta?.location;
          const gap = (bucket as { participation_gap?: string }).participation_gap;
          const partRoles = (bucket as { participation_roles?: string[] }).participation_roles;
          return (
            <div key={pid} className="pf-proj-card" style={{ marginBottom: 12, paddingBottom: 8, borderBottom: "1px solid var(--bd)" }}>
              <h4 className="ent-name" style={{ margin: "0 0 4px" }}>{title}</h4>
              {loc ? <p className="fine muted">소재·맥락: {loc}</p> : null}
              {partRoles?.length ? <p className="fine">사업 메타 역할: {partRoles.join(", ")}</p> : null}
              {gap ? <p className="fine warn">{gap}</p> : null}
              {!bucket.edges.length && !gap ? <p className="fine">이 사업에 대한 검증 엣지 없음</p> : null}
              <ul className="ent-list" style={{ marginTop: 6 }}>
                {bucket.edges.map((e) => {
                  const otherId = e.source === companyId ? e.target : e.source;
                  const other = nodeMap.get(otherId) as NetNode | undefined;
                  const m = edgeMeta(e);
                  return (
                    <li key={e.id}>
                      <button type="button" className="link-row" onClick={() => onSelectEdge(e.id)}>
                        <span className="lr-t">
                          <button type="button" className="link" onClick={(ev) => { ev.stopPropagation(); onSelectNode(otherId); }}>
                            {other ? displayName(other) : otherId}
                          </button>
                        </span>
                        <span className="lr-m">
                          {REL_LABEL[e.relationship_type] || e.relationship_type}
                          {m.stage ? ` · ${FINANCING_STAGE_KO[m.stage] || m.stage}` : ""}
                          {m.seniority ? ` · ${m.seniority}` : ""}
                          {m.contingent ? " · 조건부" : ""}
                        </span>
                        <span className="lr-v num">{amtDisplay(e)}</span>
                      </button>
                      {m.amtType ? (
                        <p className="fine">금액유형: {AMOUNT_TYPE_KO[m.amtType] || m.amtType}
                          {m.facility != null ? ` · 시설총액 맥락 ${m.facility.toLocaleString("ko-KR")}억` : ""}
                        </p>
                      ) : null}
                      {m.path ? <p className="fine">자금 경로: {m.path}</p> : null}
                      {e.amount_note ? <p className="fine">{e.amount_note}</p> : null}
                      {m.ev ? <p className="fine">{EVIDENCE_STATUS_KO[m.ev] || m.ev}{m.status && m.status !== "current" ? ` · ${m.status}` : ""}</p> : null}
                      {(e as { source_url?: string }).source_url ? (
                        <p className="fine">근거: <a href={(e as { source_url?: string }).source_url} target="_blank" rel="noreferrer">{(e as { source_title?: string }).source_title || "출처"}</a>
                          {(e as { source_date?: string }).source_date ? ` · ${(e as { source_date?: string }).source_date}` : ""}
                        </p>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </Sec>
    </>
  );
}

/** When a project SPV is selected, list all financial participants by role. */
export function PfProjectFinanceRoster({
  spvId,
  projectId,
  net,
  onSelectNode,
  onSelectEdge,
}: {
  spvId: string;
  projectId?: string | null;
  net: Network;
  onSelectNode: (id: string) => void;
  onSelectEdge: (id: string) => void;
}) {
  const nodeMap = new Map(net.nodes.map((n) => [n.id, n]));
  const edges = net.edges.filter((e) => {
    if (e.source === spvId || e.target === spvId) return true;
    if (projectId && (e as { project_id?: string }).project_id === projectId) return true;
    return false;
  });
  if (!edges.length) return null;

  const buckets: { id: string; label: string; test: (e: NetEdge) => boolean }[] = [
    { id: "bridge", label: "브릿지 대주", test: (e) => (e as { financing_stage?: string }).financing_stage === "bridge" },
    { id: "main", label: "본PF 대주", test: (e) => e.relationship_type === "PROJECT_LOAN" && (e as { financing_stage?: string }).financing_stage !== "bridge" },
    { id: "ins_mutual", label: "보험·공제 투자", test: (e) => {
      const oid = e.source === spvId ? e.target : e.source;
      const g = nodeMap.get(oid)?.group;
      return g === "kr_insurance" || g === "kr_cooperative";
    } },
    { id: "fund", label: "펀드·운용사·리츠", test: (e) => ["ASSET_MANAGER", "EQUITY_INVESTMENT", "EQUITY_SPONSOR", "STRUCTURING_EQUITY"].includes(e.relationship_type) },
    { id: "sec", label: "증권 주관·신용보강", test: (e) => ["ARRANGER", "CREDIT_ENHANCEMENT", "REFINANCING_UNDERWRITE"].includes(e.relationship_type) },
    { id: "epc", label: "시공·책임준공", test: (e) => e.relationship_type === "EPC_CONTRACT" || (e.roles || []).includes("completion_undertaking") || (e.roles || []).includes("guarantor") },
    { id: "ops", label: "운영·임차", test: (e) => ["FACILITY_OPERATION", "TENANT_LEASE", "LEASE_OR_COLOCATION"].includes(e.relationship_type) },
  ];

  const seen = new Set<string>();
  return (
    <Sec label="사업 금융 참여자" aside={`${edges.length}관계`}>
      <p className="fine">같은 사업의 참여자는 사업(차주)을 통해 연결됩니다. 대주↔시공 직접 보증은 기사에 있을 때만 표시합니다.</p>
      {buckets.map((b) => {
        const rows = edges.filter((e) => b.test(e) && !seen.has(e.id));
        rows.forEach((e) => seen.add(e.id));
        if (!rows.length) return null;
        return (
          <div key={b.id} style={{ marginBottom: 10 }}>
            <p className="lbl">{b.label} <span className="lbl-aside">{rows.length}</span></p>
            <ul className="ent-list">
              {rows.map((e) => {
                const oid = e.source === spvId ? e.target : e.target === spvId ? e.source : e.source;
                const other = nodeMap.get(oid);
                const m = edgeMeta(e);
                return (
                  <li key={e.id}>
                    <button type="button" className="link-row" onClick={() => onSelectEdge(e.id)}>
                      <span className="lr-t">
                        <button type="button" className="link" onClick={(ev) => { ev.stopPropagation(); onSelectNode(oid); }}>
                          {other ? displayName(other) : oid}
                        </button>
                      </span>
                      <span className="lr-m">{REL_LABEL[e.relationship_type] || e.relationship_type}{m.contingent ? " · 조건부" : ""}</span>
                      <span className="lr-v num">{amtDisplay(e)}</span>
                    </button>
                    {m.path ? <p className="fine">{m.path}</p> : null}
                    {(e as { source_url?: string }).source_url ? (
                      <p className="fine"><a href={(e as { source_url?: string }).source_url} target="_blank" rel="noreferrer">{(e as { source_title?: string }).source_title || "기사"}</a></p>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
      {edges.filter((e) => !seen.has(e.id)).length ? (
        <div>
          <p className="lbl">기타 <span className="lbl-aside">{edges.filter((e) => !seen.has(e.id)).length}</span></p>
          <ul className="ent-list">
            {edges.filter((e) => !seen.has(e.id)).map((e) => {
              const oid = e.source === spvId ? e.target : e.source;
              return (
                <li key={e.id}>
                  <button type="button" className="link-row" onClick={() => onSelectEdge(e.id)}>
                    <span className="lr-t">{nodeMap.get(oid) ? displayName(nodeMap.get(oid)!) : oid}</span>
                    <span className="lr-m">{REL_LABEL[e.relationship_type] || e.relationship_type}</span>
                    <span className="lr-v num">{amtDisplay(e)}</span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </Sec>
  );
}
