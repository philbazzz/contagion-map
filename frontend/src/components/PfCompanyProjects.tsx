/** Group a company's verified PF edges by project for the detail panel. */
import { useState, type ReactNode } from "react";
import type { Network, NetEdge, NetNode } from "../types";
import type { PfProject } from "../pf/types";
import { displayName, projectDisplayName } from "../lib/displayName";
import { EVIDENCE_STATUS_KO, FINANCING_STAGE_KO, REL_LABEL } from "../lib/format";
import { cleanNote } from "../lib/labels";
import { CERTAINTY_KO, CURRENT_KO, amountFacts, fmtSum, sourceRef, statusKo, summarizeExposure, type AmountFacts } from "../lib/evidence";

function Sec({ label, aside, children }: { label: string; aside?: ReactNode; children: ReactNode }) {
  return (
    <section className="rp-sec">
      <h3 className="lbl">{label}{aside ? <span className="lbl-aside">{aside}</span> : null}</h3>
      {children}
    </section>
  );
}

/** Amount + certainty in one string, from the shared evidence model. */
function amtDisplay(e: NetEdge, today: string): string {
  return amountFacts(e, today).display;
}

/** Small certainty chip used next to every amount (same wording everywhere). */
export function CertTag({ f }: { f: AmountFacts }) {
  if (f.value === null) return <span className="cert cert-unknown" data-tip={f.certaintyReason}>미확인</span>;
  return <span className={`cert cert-${f.certainty}`} data-tip={`${CERTAINTY_KO[f.certainty]} · ${f.certaintyReason}`}>{CERTAINTY_KO[f.certainty]}</span>;
}

function SrcCell({ e }: { e: NetEdge }) {
  const r = sourceRef(e);
  if (r.status !== "linked") return <span className="muted" data-tip={r.status === "homepage_only" ? "기관 홈페이지 주소는 개별 주장의 근거로 쓰지 않습니다" : undefined}>원문 연결 미확보</span>;
  return <a href={r.url!} target="_blank" rel="noreferrer" data-tip={[r.publisher, r.filing ? `접수번호 ${r.filing}` : null].filter(Boolean).join(" · ") || undefined}>{r.title}</a>;
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
  const [allProj, setAllProj] = useState(false);
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

  const today = net.meta.as_of;
  const ARRANGE = new Set(["ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT"]);
  const isPast = (e: NetEdge) => {
    const c = amountFacts(e, today).current;
    return c === "past" || c === "superseded";
  };
  const sum = summarizeExposure(links, companyId, today);
  const activeProjects = [...byProject.keys()].filter((k) => k !== "_none" && byProject.get(k)!.edges.some((e) => !isPast(e) && !ARRANGE.has(e.relationship_type)));
  const arrangerProjects = [...byProject.keys()].filter((k) => k !== "_none" && byProject.get(k)!.edges.some((e) => ARRANGE.has(e.relationship_type)));
  const lastVerified = links
    .map((e) => (e as { last_verified_date?: string; source_date?: string }).last_verified_date
      || (e as { source_date?: string }).source_date || "")
    .filter(Boolean)
    .sort()
    .at(-1) || "—";

  return (
    <>
      <Sec label="현재 데이터센터 금융 포지션" aside={`관계 ${links.length}건`}>
        <p className="fine">금액은 유형별로 따로 봅니다. <b>확인된 금액</b>만 더하며, 같은 유형·같은 기준일·중복 없는 거래일 때만 합산합니다. 추정 금액과 미확인 건수는 합계에 넣지 않습니다.</p>
        {sum.kinds.length ? (
          <table className="tbl pf-exp-tbl">
            <thead><tr><th>금액 유형</th><th className="r">확인된 금액</th><th className="r">추정 · 미확인</th></tr></thead>
            <tbody>
              {sum.kinds.map((k) => (
                <tr key={k.kind}>
                  <td>{k.kindKo}</td>
                  <td className="r num">
                    {k.confirmed.length ? k.confirmed.map((b) => (
                      <div key={`${b.asOf}-${b.unit}`}>{fmtSum(b.sum, b.unit)} <span className="tiny muted">{b.count}건{b.asOf ? ` · ${b.asOf} 기준` : ""}</span></div>
                    )) : <span className="muted">—</span>}
                    {k.confirmed.length > 1 ? <div className="tiny muted">기준일이 달라 합산하지 않음</div> : null}
                  </td>
                  <td className="r num">
                    {k.estimated.map(({ edgeId, facts }) => (
                      <div key={edgeId} className="t-warn" data-tip={facts.certaintyReason}>{facts.display}</div>
                    ))}
                    {k.unknown ? <div className="muted">금액 미확인 {k.unknown}건</div> : null}
                    {!k.estimated.length && !k.unknown ? <span className="muted">—</span> : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="muted-line">현재 금액이 있는 금융 포지션 없음</p>}
        <dl>
          <div className="kv"><dt>참여 사업장 (현재)</dt><dd className="num">{activeProjects.length}</dd></div>
          {arrangerProjects.length ? <div className="kv"><dt>주선·자문 역할 사업장</dt><dd className="num">{arrangerProjects.length} <span className="tiny muted">보유 노출 아님</span></dd></div> : null}
          {sum.past ? <div className="kv"><dt>상환·종료 거래</dt><dd className="num">{sum.past} <span className="tiny muted">현재 노출 제외</span></dd></div> : null}
          {sum.maturedUnconfirmed ? <div className="kv"><dt>만기 경과 · 상환 미확인</dt><dd className="num">{sum.maturedUnconfirmed} <span className="tiny muted">상환으로 단정하지 않음</span></dd></div> : null}
          {sum.superseded ? <div className="kv"><dt>최신 공시로 대체된 기록</dt><dd className="num">{sum.superseded} <span className="tiny muted">중복 집계 제외</span></dd></div> : null}
          <div className="kv"><dt>최종 확인일</dt><dd className="num">{lastVerified}</dd></div>
        </dl>
        <p className="fine muted">유형이 다른 금액(대출 잔액·지분·확약 한도 등)을 더한 값을 순위험으로 제시하지 않습니다.</p>
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
                  : pid === "_none" ? "사업 미기재" : ((bucket.edges[0] as { project_name?: string } | undefined)?.project_name || "사업명 미기재");
                if (!bucket.edges.length) {
                  return [(
                    <tr key={`${pid}-gap`}>
                      <td className="wrap">{title}</td>
                      <td>{(bucket as { participation_roles?: string[] }).participation_roles?.join(", ") || "—"}</td>
                      <td>해당 없음</td>
                      <td>계약 상대 미확인</td>
                      <td>—</td>
                    </tr>
                  )];
                }
                return bucket.edges.map((e) => {
                  const m = edgeMeta(e);
                  const f = amountFacts(e, today);
                  const arr = ARRANGE.has(e.relationship_type);
                  const hist = f.current === "past" || f.current === "superseded" || arr;
                  const bal = arr || f.kind === "facility_total_context"
                    ? "해당 없음 (주선·시설총액)"
                    : f.current === "past" && (m.status === "repaid" || (e as { exposure_status?: string }).exposure_status === "FULLY_REPAID")
                      ? "상환 완료"
                      : f.display;
                  return (
                    <tr key={e.id} className={hist ? "is-hist" : ""}>
                      <td className="wrap">
                        <button type="button" className="link" onClick={() => onSelectEdge(e.id)}>{title}</button>
                      </td>
                      <td>{REL_LABEL[e.relationship_type] || e.relationship_type}{m.contingent ? " · 조건부" : ""}<div className="tiny muted">{f.kindKo}</div></td>
                      <td className="num">{bal}{!arr && f.value !== null ? <div><CertTag f={f} /></div> : null}{f.asOf && f.value !== null ? <div className="tiny muted">{f.asOf} 기준</div> : null}</td>
                      <td>{arr ? "주선(보유 아님)" : f.current === "current" ? statusKo((e as { exposure_status?: string }).exposure_status) : CURRENT_KO[f.current]}</td>
                      <td><SrcCell e={e} /></td>
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
        {[...byProject.entries()].slice(0, allProj ? undefined : 5).map(([pid, bucket]) => {
          const title = bucket.meta
            ? projectDisplayName(bucket.meta)
            : pid === "_none"
              ? "사업 미기재 관계"
              : ((bucket.edges[0] as { project_name?: string } | undefined)?.project_name || "사업명 미기재");
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
                        <span className="lr-v num">{amtDisplay(e, today)}</span>
                      </button>
                      <p className="fine">금액유형: {amountFacts(e, today).kindKo} · <CertTag f={amountFacts(e, today)} />
                        {m.facility != null ? ` · 시설총액 맥락 ${m.facility.toLocaleString("ko-KR")}억 (기관 보유액 아님)` : ""}
                      </p>
                      {m.path ? <p className="fine">자금 경로: {m.path}</p> : null}
                      {e.amount_note ? <p className="fine">{cleanNote(e.amount_note, (id) => (nodeMap.get(id) ? displayName(nodeMap.get(id)!) : null))}</p> : null}
                      {m.ev ? <p className="fine">{EVIDENCE_STATUS_KO[m.ev] || m.ev}{m.status && m.status !== "current" ? ` · ${statusKo(m.status)}` : ""}</p> : null}
                      <p className="fine">근거: <SrcCell e={e} />{sourceRef(e).date ? ` · 공시·보도일 ${sourceRef(e).date}` : ""}</p>
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
        {byProject.size > 5 ? <button type="button" className="btn-text" onClick={() => setAllProj((v) => !v)}>{allProj ? "주요 5개 사업만" : `나머지 ${byProject.size - 5}개 사업 펼치기`}</button> : null}
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
  const today = net.meta.as_of;
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

  return (
    <RosterBody edges={edges} buckets={buckets} spvId={spvId} nodeMap={nodeMap} today={today} onSelectNode={onSelectNode} onSelectEdge={onSelectEdge} />
  );
}

function RosterBody({ edges, buckets, spvId, nodeMap, today, onSelectNode, onSelectEdge }: {
  edges: NetEdge[]; buckets: { id: string; label: string; test: (e: NetEdge) => boolean }[]; spvId: string;
  nodeMap: Map<string, NetNode>; today: string; onSelectNode: (id: string) => void; onSelectEdge: (id: string) => void;
}) {
  const [open, setOpen] = useState<Set<string>>(() => new Set());
  const seen = new Set<string>(); // rebuilt every render so each relationship lands in exactly one bucket
  const toggle = (id: string) => setOpen((s0) => { const n = new Set(s0); if (n.has(id)) n.delete(id); else n.add(id); return n; });
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
              {(open.has(b.id) ? rows : rows.slice(0, 5)).map((e) => {
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
                      <span className="lr-v num">{amtDisplay(e, today)}</span>
                    </button>
                    {m.path ? <p className="fine">{m.path}</p> : null}
                    <p className="fine"><SrcCell e={e} /></p>
                  </li>
                );
              })}
            </ul>
            {rows.length > 5 ? <button type="button" className="btn-text" onClick={() => toggle(b.id)}>{open.has(b.id) ? "주요 5건만" : `나머지 ${rows.length - 5}건 펼치기`}</button> : null}
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
                    <span className="lr-v num">{amtDisplay(e, today)}</span>
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
