import { useEffect, useMemo, useState, type ReactNode } from "react";
import type { Api, Assessment, CompanyProfile, Instrument, NetEdge, NetNode, Network, NetworkStats, PathResult, QuoteHistory, QuoteItem, QuotesOverview } from "../types";
import type { RunView, Selection } from "../App";
import type { PfProject, PfShockResult } from "../pf/types";
import { KIND_KO } from "../lib/scenario";
import {
  AMOUNT_TYPE_KO, CATEGORY_CODE, CATEGORY_KO, CHANNEL_LABEL, FINANCING_STAGE_KO,
  GROUP_LABEL, REL_LABEL, RELATION_KIND_KO, STATUS_KO, domainOf, korUsd, usdM,
} from "../lib/format";
import { displayName, projectDisplayName } from "../lib/displayName";
import { STAGES } from "../engine/refinancing";
import { SHOCK_STAGES } from "../engine/rateShock";
import { PF_SHOCK_STAGES } from "../pf/shockEngine";
import { tradingViewQuote } from "../lib/tickers";
import { IconChevron, IconClose, IconLink, IconReset } from "./Icons";
import { TradingViewTicker } from "./TradingViewTicker";
import { PathFlow, PeriodTabs, PriceChart, ShareBar, Timeline, type TimelineRow } from "./Viz";
import { PfCompanyProjectsBlock, PfProjectFinanceRoster } from "./PfCompanyProjects";
import { PfBorrowerPanel } from "./PfBorrowerPanel";
import { PanelErrorBoundary } from "./PanelErrorBoundary";
import { isBorrowerNode, type BorrowerEdgeMode, type InstCategoryId } from "../pf/borrowerSummary";
import { CERTAINTY_KO, CURRENT_KO, amountFacts, isHomepageUrl, sourceRef, statusKo } from "../lib/evidence";
import { relationState, type RelationState } from "../lib/relationState";
import { CertTag } from "./PfCompanyProjects";
import { PfShockDigest, changedInputs } from "./PfShockDigest";
import { AMOUNT_KIND_KO, EXPOSURE_CLASS_KO, CRISIS_MODE_KO, STRESS_LEVEL_KO, TRANSMISSION_CLASS_KO, CW_DISTRESS_KO, ko, multipleChange, refreshLabel, refreshTip, cleanNote } from "../lib/labels";

const dn = (n?: NetNode | null) => (n ? displayName(n) : "—");
const STAGE_KO: Record<string, string> = {
  planned: "계획",
  pre_construction: "착공 전",
  under_construction: "공사 중",
  expanding: "증설",
  completed_permit: "준공·사용승인(허가)",
  stabilized_operating: "안정 운영",
  operating_collateral: "운영·담보자산",
};

interface Props {
  api: Api;
  net: Network;
  origin: string;
  onSetOrigin: (id: string) => void;
  nodeMap: Map<string, NetNode>;
  stats: NetworkStats | null;
  quotes: QuotesOverview | null;
  onRefreshQuotes: () => void;
  quotesLive?: boolean;
  quotesBusy: boolean;
  selection: Selection;
  run: RunView | null;
  mode: "network" | "market" | "shock";
  stage: number;
  entityPath: PathResult | null;
  pathQuery: { a: string; b: string; path: PathResult | null } | null;
  onFindPath: (a: string, b: string) => void;
  onClearPath: () => void;
  onSelectNode: (id: string) => void;
  onSelectEdge: (id: string) => void;
  onSelectContract: (id: string) => void;
  onUseContract: (id: string) => void;
  onClose: () => void;
  onCollapse: () => void;
  pfProjects?: PfProject[];
  pfShockResult?: PfShockResult | null;
  /** Full PF ledger (includes historical edges) for institution dossiers. */
  pfLedgerNet?: Network;
  borrowerEdgeMode?: BorrowerEdgeMode;
  onBorrowerEdgeMode?: (m: BorrowerEdgeMode) => void;
  borrowerCategoryFocus?: InstCategoryId | null;
  onBorrowerCategoryFocus?: (c: InstCategoryId | null) => void;
  hiddenGroups?: string[];
}

const sgn = (x: number) => (x > 0 ? "+" : "");
const money = (x: number | null | undefined, signed = false) => (x === null || x === undefined ? "—" : `${signed ? sgn(x) : ""}${usdM(x)}`);

// ---------------------------------------------------------------- primitives
const Sec = ({ label, aside, children }: { label: string; aside?: ReactNode; children: ReactNode }) => (
  <section className="rp-sec">
    <h4 className="lbl">{label}{aside ? <span className="lbl-aside">{aside}</span> : null}</h4>
    {children}
  </section>
);

const KV = ({ k, v, tone, tip, mono = true, st }: { k: string; v: ReactNode; tone?: string; tip?: string; mono?: boolean; st?: string }) => (
  <div className="kv" data-tip={tip}>
    <dt>{k}</dt>
    <dd className={`${mono ? "num" : ""} ${tone ? `t-${tone}` : ""}`}>{v}{st ? <StTag s={st} /> : null}</dd>
  </div>
);

const ccyLabel = (c?: string) => {
  if (!c) return null;
  const u = c.toUpperCase();
  if (u === "USD") return "Financials · USD";
  if (u === "KRW") return "재무제표 · KRW (원화)";
  if (u === "TWD" || u === "NTD") return "Financials · TWD (reporting) · ADR may quote USD";
  return `Financials · ${u}`;
};

function ProjectDossierBlock({
  project, stress, nodeMap,
}: {
  project: PfProject;
  stress?: PfShockResult["pf"]["projects"][number];
  nodeMap?: Map<string, NetNode>;
}) {
  const card = (k: string, v: ReactNode) => (
    <div className="metric"><dt>{k}</dt><dd className="num">{v ?? "—"}</dd></div>
  );
  const ent = (id: string | null | undefined) => {
    if (!id) return "—";
    const n = nodeMap?.get(id);
    return n ? displayName(n) : id;
  };
  const stage = STAGE_KO[project.construction_stage] || project.construction_stage;
  const title = projectDisplayName(project);
  const finMissing = project.financing_disclosed === false
    || (project.senior_debt_usd_m == null && project.equity_usd_m == null && !project.debt_interest_rate_pct);
  return (
    <div className="dossier">
      <p className="dossier-overview">{title} · {project.location || project.address || "—"}</p>

      <p className="lbl" style={{ marginTop: 8 }}>사업장 개요</p>
      <dl className="metrics-grid">
        {card("사업장명", title)}
        {card("소재지", project.location || project.address || "—")}
        {card("개발 단계", stage)}
        {card("허가일", project.permit_date || "—")}
        {card("착공일", project.construction_start || "—")}
        {card("준공일", project.completion_date || project.target_completion || "—")}
        {card("개발사", ent(project.developer))}
        {card("운영사", ent(project.operator || project.owner))}
      </dl>

      <p className="lbl" style={{ marginTop: 10 }}>사업 규모</p>
      <dl className="metrics-grid">
        {card("연면적", project.gfa_m2 != null ? `${project.gfa_m2.toLocaleString("ko-KR")} ㎡` : "—")}
        {card("수전·IT 용량", project.critical_it_load_mw != null ? `${project.critical_it_load_mw} MW` : (project.capacity_note || "—"))}
        {card("총사업비", project.capex_usd_m != null ? usdM(project.capex_usd_m) : (project.capex_native_krw_b != null ? `${project.capex_native_krw_b}억 원` : "—"))}
        {card("공사 현황", stage)}
      </dl>
      {project.capex_note ? <p className="fine">{project.capex_note}</p> : null}

      <p className="lbl" style={{ marginTop: 10 }}>사업 및 금융 구조</p>
      <dl className="metrics-grid">
        {card("시행·개발", ent(project.developer))}
        {card("PFV/SPV", ent(project.spv))}
        {card("임차·테넌트", ent(project.tenant))}
        {card("시공사", ent(project.construction_company))}
        {card("신탁사", ent(project.trust_company))}
        {card("담보·구조", project.collateral || project.lease_structure || "—")}
      </dl>
      {project.korean_counterparties?.length ? (
        <p className="fine">확인된 한국 거래상대방 ID: {project.korean_counterparties.map((id) => ent(id)).join(", ")}
          {project.korean_link_class ? ` · ${project.korean_link_class}` : ""}</p>
      ) : null}

      <p className="lbl" style={{ marginTop: 10 }}>재무 및 PF 현황</p>
      {finMissing ? (
        <p className="muted-line">공시된 차입·DSCR·금리가 없어 수치를 채우지 않습니다. 건축허가·개발 정보만 확인된 사업장은 금융 연결이 별도 공시로 검증되어야 합니다.</p>
      ) : null}
      <dl className="metrics-grid">
        {card("선순위 차입", project.senior_debt_usd_m != null ? usdM(project.senior_debt_usd_m) : "—")}
        {card("지분", project.equity_usd_m != null ? usdM(project.equity_usd_m) : "—")}
        {card("금리 유형", project.debt_rate_type || "—")}
        {card("금리", project.debt_interest_rate_pct != null ? `${project.debt_interest_rate_pct}%` : "—")}
        {card("만기", project.debt_maturity || "—")}
        {card("변동/고정 잔액", [
          project.floating_debt_usd_m != null ? `변동 ${usdM(project.floating_debt_usd_m)}` : null,
          project.fixed_debt_usd_m != null ? `고정 ${usdM(project.fixed_debt_usd_m)}` : null,
        ].filter(Boolean).join(" · ") || "—")}
        {card("기준 DSCR", project.baseline_dscr ?? project.dscr_status ?? "미공시")}
        {card("책임준공·보증", project.sponsor_guarantees || project.covenants || "—")}
      </dl>

      <p className="lbl" style={{ marginTop: 10 }}>위험 요인</p>
      <ul className="dossier-notes">
        <li>금리 상승 · 임차수요 감소 · 공사 지연 · 차환 · 유동성 — 프로젝트 단계별로 상이</li>
        {project.gpu_rent_note ? <li>{project.gpu_rent_note}</li> : null}
        {project.note ? <li>{project.note}</li> : null}
        {project.missing?.length ? <li>미공시: {project.missing.join(" · ")}</li> : null}
        {project.id === "bundang_hostway_idc" ? (
          <li>안정 운영 코로케이션 자산 — 개발 PF 허브가 아니며 CW/CAPEX 충격의 기본 전달 경로로 쓰지 않음</li>
        ) : null}
      </ul>

      {stress ? (
        <div style={{ marginTop: 10 }}>
          <p className="lbl">시나리오 스트레스 <span className="lbl-aside">{stress.level}</span></p>
          <dl className="metrics-grid">
            {card("스트레스 DSCR", stress.stressed_dscr?.toFixed(2) ?? "—")}
            {card("이자 증분", stress.interest_delta_usd_m != null ? usdM(stress.interest_delta_usd_m) : "—")}
            {card("유동성 갭(모형)", stress.liquidity_gap_usd_m != null ? usdM(stress.liquidity_gap_usd_m) : "—")}
          </dl>
          <ul className="dossier-notes">{stress.reasons.map((t) => <li key={t}>{t}</li>)}</ul>
        </div>
      ) : null}

      <p className="lbl" style={{ marginTop: 10 }}>공시 및 출처</p>
      <ul className="dossier-notes">
        {(project.sources || []).map((s, i) => (
          <li key={i}>
            {s.title || "출처"}{s.filing_id ? ` · ${s.filing_id}` : ""}{s.date ? ` · ${s.date}` : ""}
            {s.url ? <> · <a href={s.url} target="_blank" rel="noreferrer">{domainOf(s.url)} <IconLink size={11} /></a></> : null}
          </li>
        ))}
        {(project.source_ids || []).map((sid) => <li key={sid}>source_id: {sid}</li>)}
        {!project.sources?.length && !project.source_ids?.length ? <li>출처 메타데이터 미기재</li> : null}
        <li>검증일: {project.verification_date || "—"}</li>
      </ul>
    </div>
  );
}

function DossierBlock({ profile, net }: { profile: CompanyProfile; net: Network }) {
  const metrics = profile.metrics || [];
  const snap = metrics.filter((m) => m.status !== "UNKNOWN" || m.display);
  const missing = metrics.filter((m) => m.status === "UNKNOWN" && !m.display);
  const srcIds = [...(profile.source_ids || []), ...metrics.flatMap((m) => m.source_ids || [])];
  return (
    <div className="dossier">
      {profile.overview ? <p className="dossier-overview">{profile.overview}</p> : null}
      <p className="dossier-ccy">{ccyLabel(profile.reporting_currency || profile.currency) || "Currency per metric"}{profile.listing_currency && profile.listing_currency !== (profile.reporting_currency || profile.currency) ? ` · Quotes ${profile.listing_currency}` : ""}</p>
      {snap.length ? (
        <div className="metric-grid">
          {snap.map((m) => (
            <div key={m.id} className="metric-card" data-tip={[m.period, m.note, m.status, m.currency].filter(Boolean).join(" · ") || undefined}>
              <span className="mc-l">{m.label}{m.status === "VERIFIED" || m.status === "INFERRED" ? <StTag s={m.status} /> : null}</span>
              <span className="mc-v num">{m.display || (m.value_usd_m != null ? usdM(m.value_usd_m) : "Not disclosed")}</span>
              {m.period ? <span className="mc-p">{m.period}{m.currency ? ` · ${m.currency}` : ""}</span> : null}
            </div>
          ))}
        </div>
      ) : <p className="muted-line">정량 지표는 출처에 따라 관계·노트에 분산되어 있습니다.</p>}
      {missing.length ? (
        <p className="hint caution">Data unavailable: {missing.map((m) => m.label).join(" · ")}</p>
      ) : null}
      {profile.financing_notes?.length ? (
        <Disclosure label="Financing & debt notes" defaultOpen>
          <ul className="dossier-notes">{profile.financing_notes.map((t) => <li key={t}>{t}</li>)}</ul>
        </Disclosure>
      ) : null}
      {profile.risk_factors?.length ? (
        <Disclosure label="Risk & exposure" defaultOpen>
          <ul className="dossier-notes">{profile.risk_factors.map((t) => <li key={t}>{t}</li>)}</ul>
        </Disclosure>
      ) : null}
      {profile.missing?.length ? <p className="hint caution">미수록: {profile.missing.join(" · ")}</p> : null}
      <Disclosure label="Official filings & sources">
        <SourceList net={net} ids={srcIds} />
      </Disclosure>
    </div>
  );
}

const StTag = ({ s }: { s: string }) => <span className={`st-tag st-${s}`} data-tip={STATUS_KO[s] || s}>{s}</span>;

function Disclosure({ label, children, defaultOpen = false }: { label: string; children: ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className={`disc ${open ? "is-open" : ""}`}>
      <button type="button" className="disclosure" aria-expanded={open} onClick={() => setOpen((o) => !o)}>
        <IconChevron size={11} className="chev" />{label}
      </button>
      {open ? <div className="disc-body">{children}</div> : null}
    </div>
  );
}

function SourceList({ net, ids }: { net: Network; ids: string[] }) {
  const byId = new Map(net.sources.map((s) => [s.id, s]));
  const list = [...new Set(ids)].map((i) => byId.get(i)).filter(Boolean) as Network["sources"];
  if (!list.length) return <p className="muted-line">출처 없음</p>;
  return (
    <ul className="srcs">
      {list.map((s) => (
        <li key={s.id}>
          {s.url && !isHomepageUrl(s.url)
            ? <a href={s.url} target="_blank" rel="noreferrer">{s.title} <IconLink size={10} /></a>
            : <span>{s.title} <span className="muted tiny">· 원문 연결 미확보{s.url ? " (홈페이지 주소만 있음)" : ""}</span></span>}
          <span className="src-m num">{s.date || "날짜 미기재"}{s.url ? ` · ${domainOf(s.url)}` : ""}</span>
        </li>
      ))}
    </ul>
  );
}

const rateText = (x: Instrument) => {
  if (x.rate_type === "fixed" && x.coupon_pct !== null) return `고정 ${x.coupon_pct}%`;
  if (x.rate_type === "floating" && x.spread_pct !== null) return `${x.base_rate || "SOFR"}${x.floor_pct !== null ? `(하한 ${x.floor_pct}%)` : ""} + ${x.spread_pct}%`;
  if (x.rate_type === "floating") return `${x.base_rate || "SOFR"} + 가산금리 미확인`;
  return "표면금리 미공시";
};

const won = (v: number) => `${Math.round(v).toLocaleString("ko-KR")}원`;
/** KRW amount in won → "182조 7,250억 원" style */
const wonBig = (v: number) => {
  const jo = Math.floor(v / 1e12), eok = Math.round((v % 1e12) / 1e8);
  return jo ? `${jo.toLocaleString("ko-KR")}조${eok ? ` ${eok.toLocaleString("ko-KR")}억` : ""} 원` : `${eok.toLocaleString("ko-KR")}억 원`;
};
const sgnPct = (x: number) => `${x > 0 ? "+" : x < 0 ? "−" : ""}${Math.abs(x).toFixed(2)}%`;
const remainText = (end: string | null, today: string) => {
  if (!end) return "종료일 미공시";
  const [y, m] = end.split("-").map(Number);
  const [ty, tm] = today.split("-").map(Number);
  const months = (y - ty) * 12 + ((m || 12) - tm);
  if (months <= 0) return "만기 도래";
  return `${Math.floor(months / 12) ? `${Math.floor(months / 12)}년 ` : ""}${months % 12 ? `${months % 12}개월` : ""} 남음`.trim();
};

export function lendingRows(net: Network, entityId: string): (TimelineRow & { inst: Instrument; roles: string[]; pstatus: string })[] {
  return net.financials.instruments
    .map((x) => ({ x, p: x.participants.find((q) => q.entity === entityId) }))
    .filter((r) => r.p)
    .sort((a, b) => (a.x.maturity || "9999").localeCompare(b.x.maturity || "9999"))
    .map(({ x, p }) => ({
      id: x.id, label: x.name, start: x.signed, end: x.maturity, amount: x.principal_usd_m, tone: "debt" as const,
      amountNote: x.commitment_usd_m !== null ? `약정 ${usdM(x.commitment_usd_m)}` : "잔액 미공시",
      inst: x, roles: p!.roles, pstatus: p!.status,
    }));
}

function commercialRows(net: Network, entityId?: string): TimelineRow[] {
  return net.contracts
    .filter((c) => !entityId || c.counterparty === entityId)
    .sort((a, b) => (a.signed || "0").localeCompare(b.signed || "0"))
    .map((c) => ({
      id: c.id, label: c.title,
      start: c.signed, end: c.term_end, amount: c.value_usd_m, amountNote: c.value_basis || "금액 미공시",
      tone: c.kind === "lease" ? "lease" as const : c.kind === "backstop" ? "backstop" as const : "customer" as const,
    }));
}

/** Research notes can predate the current relationship data — never let an old note contradict it silently. */
function DescNote({ n, rs }: { n: NetNode; rs: RelationState }) {
  if (!n.description) return null;
  const stale = rs.relation.count > 0 && /엣지를 (자동 )?생성하지 않|연결관계 확인 필요|미연결|관계 미확인/.test(n.description);
  return (
    <>
      <p className="dossier-overview">{cleanNote(n.description)}</p>
      {stale ? <p className="fine warn">이 메모는 이전 조사 단계의 기록입니다. 현재 관계 데이터 {rs.relation.count}건(위 상태 표시)이 우선합니다.</p> : null}
    </>
  );
}

function StateStrip({ rs }: { rs: RelationState }) {
  const rows: [string, string, string][] = [
    ["식별", rs.identity.ko, rs.identity.code],
    ["관계", rs.relation.ko, rs.relation.code],
    ["금액", rs.amount.ko, rs.amount.code],
    ["거래", rs.current.ko, rs.current.code],
    ["충격 경로", rs.shockPath.ko, rs.shockPath.code],
    ["정량 계산", rs.quant.ko, rs.quant.code],
  ];
  return (
    <div className="state-strip">
      <p className="state-head">{rs.headline}</p>
      <dl className="state-grid">
        {rows.map(([k, v, c]) => (
          <div key={k} className={`st-${c}`}><dt>{k}</dt><dd>{v}</dd></div>
        ))}
      </dl>
    </div>
  );
}

// ---------------------------------------------------------------- panel
export function DetailPanel(p: Props) {
  let body: ReactNode;
  let title = "Overview";
  if (p.selection?.kind === "node") { body = <NodeView {...p} id={p.selection.id} />; title = "Entity"; }
  else if (p.selection?.kind === "edge") { body = <EdgeView {...p} id={p.selection.id} />; title = "Relationship"; }
  else if (p.selection?.kind === "contract") { body = <ContractView {...p} id={p.selection.id} />; title = "Contract"; }
  else if (p.run && p.mode === "shock") { body = <RunSummary {...p} run={p.run} />; title = "Shock View"; }
  else if (p.mode === "market") { body = <MarketOverviewView {...p} />; title = "Market View"; }
  else body = <Overview {...p} />;
  return (
    <aside className="rp" aria-label="분석 패널">
      <div className="rp-bar">
        <span className="lbl">{title}</span>
        <span className="rp-bar-actions">
          {p.selection ? <button type="button" className="ibtn" onClick={p.onClose} data-tip="선택 해제 (Esc)" aria-label="선택 해제"><IconClose size={13} /></button> : null}
          <button type="button" className="ibtn rp-collapse" onClick={p.onCollapse} data-tip="패널 접기" aria-label="패널 접기"><IconChevron size={13} /></button>
        </span>
      </div>
      <div className="rp-scroll" key={p.selection ? `${p.selection.kind}:${p.selection.id}` : p.run ? "run" : "ov"}>
        <PanelErrorBoundary label="선택 상세">{body}</PanelErrorBoundary>
      </div>
    </aside>
  );
}

// ---------------------------------------------------------------- entity
function NodeView(p: Props & { id: string }) {
  const n = p.nodeMap.get(p.id);
  const originName = dn(p.nodeMap.get(p.origin)) || p.origin;
  const [target, setTarget] = useState("");
  const [openBuckets, setOpenBuckets] = useState<Set<string>>(() => new Set());
  const edgeMap = useMemo(() => new Map(p.net.edges.map((e) => [e.id, e])), [p.net]);
  const links = useMemo(() => (n ? p.net.edges.filter((e) => e.source === n.id || e.target === n.id) : []), [p.net.edges, n]);
  const neighbors = useMemo(() => {
    if (!n) return [] as { id: string; edge: NetEdge; dir: "out" | "in" }[];
    return links.map((e) => ({
      id: e.source === n.id ? e.target : e.source,
      edge: e,
      dir: (e.source === n.id ? "out" : "in") as "out" | "in",
    }));
  }, [links, n]);
  if (!n) return null;
  const toOrigin = links.filter((e) => e.source === p.origin || e.target === p.origin);
  const instruments = p.net.financials?.instruments || [];
  const isPfNet = (p.net.meta as { ecosystem?: string }).ecosystem === "datacenter_pf";
  const contracts = instruments.filter((x) => (n.id === "coreweave" && !isPfNet) || x.borrower === n.id || (x.participants || []).some((q) => q.entity === n.id));
  const a: Assessment | undefined = p.mode === "shock" ? p.run?.result.assessments[n.id] : undefined;
  const relKind = n.id === p.origin ? "origin" : p.entityPath ? (p.entityPath.hops === 1 ? "direct" : "indirect") : "unconfirmed";
  const srcIds = [
    ...(n.source_ids || []),
    ...links.flatMap((e) => e.source_ids || []),
    ...(p.net.contracts || []).filter((c) => c.counterparty === n.id).flatMap((c) => c.source_ids || []),
  ];
  const lend = n.id === "coreweave" ? [] : lendingRows(p.net, n.id);
  const com = commercialRows(p.net, n.id);
  const today = p.net.meta.as_of;
  const profile = p.net.profiles?.[n.id];
  const pfProject = p.pfProjects?.find((x) => x.id === n.id);
  const pfStress = p.pfShockResult?.pf.projects.find((x) => x.project_id === n.id);
  const borrower = isBorrowerNode(n);
  const shockCtx = p.mode === "shock" && p.run
    ? p.run.kind === "pf_shock"
      ? { kind: "pf" as const, result: p.run.result }
      : { kind: "rate" as const, assessments: p.run.result.assessments as Record<string, { category?: string }>, activeIds: new Set(Object.keys(p.run.result.rounds[Math.min(p.stage, p.run.result.rounds.length - 1)]?.node_states || {})) }
    : null;
  const rs = relationState(n, (p.pfLedgerNet || p.net).edges, today, shockCtx);
  return (
    <div className="rp-body">
      <header className="ent-head">
        <p className="lbl">{GROUP_LABEL[n.group] || n.group}{n.id === p.origin ? " · FOCUS" : ""}{(n as { region?: string }).region === "KR" ? " · KR" : ""}</p>
        <h2>{dn(n)}</h2>
        <p className="ent-sub num">{n.listed ? `${n.ticker} · ${n.exchange}` : "비상장기업"}{(n as { name_en?: string }).name_en ? ` · ${(n as { name_en?: string }).name_en}` : ""}</p>
        <p className="ent-sector">{[ko(n.sector, ""), ko(n.role, ""), ko(n.entity_type, "")].filter(Boolean).join(" · ")}</p>
        <StateStrip rs={rs} />
        {n.id !== p.origin ? (
          <button type="button" className="btn-text" onClick={() => p.onSetOrigin(n.id)} data-tip="이 회사를 네트워크 분석 중심으로 설정">이 회사를 초점으로</button>
        ) : (
          <p className="fine">현재 네트워크 초점 · 상단 Direct/Indirect는 이 회사 기준</p>
        )}
      </header>

      <MarketBlock p={p} n={n} />

      {borrower && p.onBorrowerEdgeMode ? (
        <PfBorrowerPanel
          borrowerId={n.id}
          net={p.net}
          ledgerNet={p.pfLedgerNet || p.net}
          nodeMap={p.nodeMap}
          hiddenGroups={p.hiddenGroups}
          edgeMode={p.borrowerEdgeMode || "material"}
          onEdgeMode={p.onBorrowerEdgeMode}
          categoryFocus={p.borrowerCategoryFocus ?? null}
          onCategoryFocus={p.onBorrowerCategoryFocus || (() => undefined)}
          shockResult={p.pfShockResult}
          onSelectNode={p.onSelectNode}
          onSelectEdge={p.onSelectEdge}
        />
      ) : null}

      {!borrower && links.some((e) => (e as { project_name?: string }).project_name || (e as { stress_direction?: string }).stress_direction) ? (
        <Sec label="PF 위험 설명" aside="회사 기준">
          <dl>
            <KV k="관련 사업" v={[...new Set(links.map((e) => (e as { project_name?: string }).project_name).filter(Boolean))].join(" · ") || "—"} mono={false} />
            <KV k="금액 확인 상태" v={rs.amount.ko} mono={false} />
            <KV k="위험 전이 경로" v={links.map((e) => (e as { stress_direction?: string }).stress_direction).filter(Boolean).slice(0, 3).join(" · ") || "전이 경로 미기재"} mono={false} />
            <KV k="의무 발생 조건" v={links.map((e) => (e as { obligation_trigger?: string }).obligation_trigger).filter(Boolean).slice(0, 3).join(" · ") || "—"} mono={false} />
            <KV k="근거 공시" v={[...new Set(links.map((e) => (e as { source_title?: string; source_url?: string }).source_title || (e as { source_url?: string }).source_url).filter(Boolean))].slice(0, 3).join(" · ") || "—"} mono={false} />
            <KV k="미확인 사항" v={rs.relation.count === 0
              ? "현재 확인된 관계 없음 — 충격에서 손실을 부여하지 않음"
              : rs.amount.code === "confirmed" ? "금액은 확인됨 · 만기·현재성은 최신 공시로 재확인 권장" : "일부 금액·단위·현재 잔액 확인 필요"} mono={false} />
          </dl>
          <p className="fine">부도확률 수치를 만들지 않습니다. 익스포저 규모를 확정할 수 없으면 미확인으로 둡니다.</p>
        </Sec>
      ) : !borrower && (n as { region?: string }).region === "KR" && rs.relation.count === 0 ? (
        <Sec label="PF 위험 설명">
          <p className="muted-line">현재 확인된 데이터센터 금융·사업 관계가 없습니다. 회사는 지도에 남기되, 충격 분석에서 손실을 부여하지 않습니다.</p>
        </Sec>
      ) : null}

      {!borrower && p.pfProjects ? (
        <PfCompanyProjectsBlock
          companyId={n.id}
          net={p.pfLedgerNet || p.net}
          projects={p.pfProjects}
          onSelectNode={p.onSelectNode}
          onSelectEdge={p.onSelectEdge}
        />
      ) : null}

      {!borrower && (n.entity_type === "spv" || n.group === "project_finance") ? (
        <PfProjectFinanceRoster
          spvId={n.id}
          projectId={p.pfProjects?.find((pr) => pr.spv === n.id)?.id || n.id}
          net={p.pfLedgerNet || p.net}
          onSelectNode={p.onSelectNode}
          onSelectEdge={p.onSelectEdge}
        />
      ) : null}

      {pfProject ? (
        <Sec label="사업장 개요" aside={pfProject.verification_date || pfProject.country}>
          <ProjectDossierBlock project={pfProject} stress={pfStress} nodeMap={p.nodeMap} />
        </Sec>
      ) : null}

      {!borrower && profile ? (
        <Sec label="Company dossier" aside={profile.period_label || profile.as_of}>
          <DossierBlock profile={profile} net={p.net} />
        </Sec>
      ) : !borrower && !pfProject ? (
        <Sec label="기업 개요">
          <p className="muted-line">관계·개요 중심으로 수록된 기업입니다 (차입금 주석 수준의 재무 자료 없음).</p>
          <DescNote n={n} rs={rs} />
        </Sec>
      ) : !borrower ? (
        <Sec label="개요">
          <DescNote n={n} rs={rs} />
        </Sec>
      ) : n.description ? (
        <Sec label="조사 메모">
          <DescNote n={n} rs={rs} />
        </Sec>
      ) : null}

      {!borrower ? (
      <Sec label="Relationships" aside={`${neighbors.length} edges`}>
        {n.id !== p.origin ? (
          p.entityPath ? <PathFlow path={p.entityPath} edges={edgeMap} nodeMap={p.nodeMap} onSelect={p.onSelectNode} onSelectEdge={p.onSelectEdge} />
            : <p className="muted-line">초점 기업({originName})까지의 공개 관계 경로는 확인되지 않습니다{neighbors.length ? ` — 이 기업 자체의 관계는 아래 ${neighbors.length}건` : ""}.</p>
        ) : <p className="muted-line">초점 기업 · 아래는 직접 연결 {neighbors.length}건 · 2·3-hop은 경로 탐색으로 확인</p>}
        <p className="fine">{relKind === "unconfirmed" ? `${originName} 기준 경로 미확인` : RELATION_KIND_KO[relKind]}{toOrigin.length ? ` · ${originName}와 직접 ${toOrigin.length}건` : ""}</p>
        {(["CUSTOMER", "SUPPLIER", "STRATEGIC_PARTNERSHIP", "EQUITY_INVESTMENT", "FINANCING_PARTICIPATION", "LESSOR", "OTHER"] as const).map((bucket) => {
          const rows = neighbors.filter(({ edge }) => {
            const t = edge.relationship_type;
            if (bucket === "OTHER") {
              return !["CUSTOMER", "SUPPLIER", "EQUITY_INVESTMENT", "FINANCING_PARTICIPATION", "LESSOR", "INDIRECT_SUPPLY_CHAIN", "STRATEGIC_PARTNERSHIP", "POWER_SUPPLY"].includes(t);
            }
            if (bucket === "SUPPLIER") return t === "SUPPLIER" || t === "INDIRECT_SUPPLY_CHAIN" || t === "POWER_SUPPLY";
            return t === bucket;
          });
          if (!rows.length) return null;
          const title = bucket === "CUSTOMER" ? "Customers / demand"
            : bucket === "SUPPLIER" ? "Suppliers / supply chain"
              : bucket === "STRATEGIC_PARTNERSHIP" ? "Strategic partners"
              : bucket === "EQUITY_INVESTMENT" ? "Equity / strategic ownership"
                : bucket === "FINANCING_PARTICIPATION" ? "Lenders / financing"
                  : bucket === "LESSOR" ? "Lease / facility"
                    : "Other verified links";
          return (
            <div key={bucket} style={{ marginTop: 8 }}>
              <p className="lbl">{title} <span className="lbl-aside">{rows.length}</span></p>
              <ul className="ent-list">
                {(openBuckets.has(bucket) ? rows : rows.slice(0, 5)).map(({ id, edge, dir }) => {
                  const o = p.nodeMap.get(id);
                  if (!o) return null;
                  return (
                    <li key={edge.id}>
                      <button type="button" className="ent" onClick={() => p.onSelectNode(id)}>
                        <span className={`dot g-${o.group}`} />
                        <span className="ent-name">{dn(o)}</span>
                        <span className="ent-tk num">{dir === "out" ? "→" : "←"} {REL_LABEL[edge.relationship_type] || edge.label}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
              {rows.length > 5 ? (
                <button type="button" className="btn-text" onClick={() => setOpenBuckets((s0) => { const n2 = new Set(s0); if (n2.has(bucket)) n2.delete(bucket); else n2.add(bucket); return n2; })}>
                  {openBuckets.has(bucket) ? "주요 5건만" : `나머지 ${rows.length - 5}건 펼치기`}
                </button>
              ) : null}
            </div>
          );
        })}
        {toOrigin.map((e) => <LinkRow key={`o-${e.id}`} e={e} p={p} />)}
        {n.id === "coreweave" && !isPfNet ? <p className="muted-line">금융계약 {contracts.length}건 — 하단 Lending에서 탐색</p> : null}
        <div className="pathfind">
          <label htmlFor="pf-target" className="f-lbl">최단 관계 경로 (2·3차 연결)</label>
          <select id="pf-target" value={target} onChange={(e) => { setTarget(e.target.value); if (e.target.value) p.onFindPath(n.id, e.target.value); else p.onClearPath(); }}>
            <option value="">대상 기업 선택…</option>
            {p.net.nodes.filter((x) => x.id !== n.id).map((x) => <option key={x.id} value={x.id}>{dn(x)}</option>)}
          </select>
          {p.pathQuery && p.pathQuery.a === n.id ? (
            p.pathQuery.path ? <><PathFlow path={p.pathQuery.path} edges={edgeMap} nodeMap={p.nodeMap} onSelect={p.onSelectNode} onSelectEdge={p.onSelectEdge} /><p className="fine num">{p.pathQuery.path.hops}-hop · 방향 무시 · VERIFIED·INFERRED 관계만</p></>
              : <p className="muted-line">확인된 관계 경로 없음</p>
          ) : null}
        </div>
      </Sec>
      ) : (
        <Sec label="경로 탐색" aside="요청 시">
          <p className="fine">대주 목록은 위 차주 요약에서 유형별로 펼칩니다. 지도에는 기본 주요 연결만 강조됩니다.</p>
          <div className="pathfind">
            <label htmlFor="pf-target-b" className="f-lbl">최단 관계 경로</label>
            <select id="pf-target-b" value={target} onChange={(e) => { setTarget(e.target.value); if (e.target.value) p.onFindPath(n.id, e.target.value); else p.onClearPath(); }}>
              <option value="">대상 기업 선택…</option>
              {p.net.nodes.filter((x) => x.id !== n.id).map((x) => <option key={x.id} value={x.id}>{dn(x)}</option>)}
            </select>
            {p.pathQuery && p.pathQuery.a === n.id ? (
              p.pathQuery.path ? <><PathFlow path={p.pathQuery.path} edges={edgeMap} nodeMap={p.nodeMap} onSelect={p.onSelectNode} onSelectEdge={p.onSelectEdge} /><p className="fine num">{p.pathQuery.path.hops}-hop</p></>
                : <p className="muted-line">확인된 관계 경로 없음</p>
            ) : null}
          </div>
        </Sec>
      )}

      {lend.length ? (
        <Sec label="Lending" aside={`${isPfNet ? "미국 PF 프로젝트 차입 계약" : "CoreWeave 차입 계약"} ${lend.length}건`}>
          <Timeline rows={lend} today={today} onSelect={p.onSelectContract}
            caption={`막대 = 체결 → 최종 만기. 금액은 계약 전체 잔액(${p.net.financials.as_of} 기준)이며 이 기관의 보유액이 아닙니다 (기관별 보유액 미공시).`} />
          <table className="tbl ltbl">
            <thead><tr><th>계약</th><th>역할</th><th className="r">금리</th><th className="r">만기</th></tr></thead>
            <tbody>
              {lend.map((r) => (
                <tr key={r.id} onClick={() => p.onSelectContract(r.id)}>
                  <td>{r.label}<div className="tiny muted num">{r.amount !== null ? `잔액 ${usdM(r.amount)}` : r.amountNote}{r.inst.commitment_usd_m !== null && r.amount !== null ? ` / 약정 ${usdM(r.inst.commitment_usd_m)}` : ""}</div></td>
                  <td className="wrap">{r.roles.join(", ")} <StTag s={r.pstatus} /></td>
                  <td className="r num">{rateText(r.inst)}</td>
                  <td className="r num">{r.inst.maturity ? r.inst.maturity.slice(0, 7) : "—"}<div className="tiny muted">{remainText(r.inst.maturity, today)}</div></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Sec>
      ) : null}

      {com.length ? (
        <Sec label="Contracts" aside={`상업 계약 ${com.length}건`}>
          <Timeline rows={com} today={today} from={2024} to={2034} onSelect={undefined}
            caption="막대 = 체결 → 계약 종료일. 금액은 발표 기준(대부분 '최대' 또는 '약')이며, 계약별 남은 금액은 공시되지 않습니다." />
          {p.net.contracts.filter((c) => c.counterparty === n.id).map((c) => (
            <div key={c.id} className="cc">
              <p className="cc-t">{c.title} <StTag s={c.status} /></p>
              <dl>
                <KV k="체결" v={c.signed || "미공시"} />
                <KV k="계약 금액" v={c.value_usd_m !== null ? usdM(c.value_usd_m) : "미공시"} tip={c.value_usd_m !== null ? korUsd(c.value_usd_m) : undefined} />
                <KV k="금액 기준" v={c.value_basis || "—"} mono={false} />
                <KV k="종료" v={c.term_end || "미공시"} />
                <KV k="남은 기간" v={remainText(c.term_end, today)} mono={false} />
                <KV k="남은 금액" v={c.remaining_note} mono={false} st="UNKNOWN" />
              </dl>
              {c.term_note ? <p className="fine">{c.term_note}</p> : null}
              {c.detail ? <p className="fine">{c.detail}</p> : null}
            </div>
          ))}
        </Sec>
      ) : null}

      {p.mode === "shock" ? (
        <Sec label="Shock" aside={p.run ? `Stage ${p.stage + 1}/${p.run.result.rounds.length}` : undefined}>
          {!p.run || !a ? <p className="muted-line">좌측에서 금리 충격을 조절하면 이 기업의 노출 근거가 표시됩니다</p> : <ShockBlock a={a} stage={p.stage} />}
        </Sec>
      ) : null}

      {(n.key_drivers || []).length ? (
        <Sec label="Key Drivers">
          <ol className="drivers">{(n.key_drivers || []).map((d, i) => <li key={d}><span className="num">{String(i + 1).padStart(2, "0")}</span>{ko(d)}</li>)}</ol>
        </Sec>
      ) : null}

      <Sec label="Sources" aside={<StTag s={n.source_status} />}>
        <p className="prose">{cleanNote(n.description)}</p>
        <SourceList net={p.net} ids={srcIds} />
      </Sec>
    </div>
  );
}

function MarketBlock({ p, n }: { p: Props; n: NetNode }) {
  const q: QuoteItem | undefined = p.quotes?.items.find((i) => i.entity === n.id);
  const tv = tradingViewQuote(n);
  const useTv = !!(tv && tv.embeddable);
  const [period, setPeriod] = useState("1M");
  const [inKrw, setInKrw] = useState(true);
  const [hist, setHist] = useState<QuoteHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const canChart = !!q?.provider;
  useEffect(() => {
    if (!canChart) { setHist(null); return; }
    let live = true;
    setLoading(true);
    p.api.quoteHistory(n.id, period).then((h) => { if (live) setHist(h); }).catch(() => { if (live) setHist(null); }).finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [p.api, n.id, period, canChart, q?.collected_at]);
  const has = q && q.price !== null && q.price !== undefined;
  const foreign = has && q!.currency !== "KRW";
  const up = (q?.change_pct ?? 0) > 0, down = (q?.change_pct ?? 0) < 0;
  const aside = useTv ? "TradingView"
    : q?.delay_kind === "close" ? "일간 종가"
      : q?.delay_kind === "realtime" ? "시세"
        : tv && !tv.embeddable ? "위젯 미지원"
          : undefined;
  const quoteDetail = has ? (
    <>
      <div className="quote">
        {foreign ? (
          q!.krw?.value ? <p className="q-krw num" data-tip={q!.krw.note}>약 {won(q!.krw.value)} <span className="q-tag">원화 환산</span></p>
            : <p className="q-krw muted num">원화 환산 불가 <span className="q-tag">{q!.krw?.note}</span></p>
        ) : <p className="q-krw num">{won(q!.price!)}</p>}
        <p className={`q-loc num ${up ? "is-up" : down ? "is-down" : ""}`}>
          {foreign ? `$${q!.price!.toFixed(2)} · ` : ""}{q!.change_pct !== null && q!.change_pct !== undefined ? sgnPct(q!.change_pct) : "—"}
          {q!.change !== null && q!.change !== undefined ? ` (${q!.change > 0 ? "+" : q!.change < 0 ? "−" : ""}${foreign ? `$${Math.abs(q!.change).toFixed(2)}` : won(Math.abs(q!.change))})` : ""}
        </p>
      </div>
      <dl>
        <KV k="종목" v={`${n.ticker} · ${n.exchange}`} />
        <KV k="가격 기준" v={q!.basis === "close" ? `종가 ${q!.price_time}` : q!.price_time ? `${q!.price_time.replace("T", " ").slice(0, 16)} UTC` : "—"} />
        {foreign && q!.krw?.fx_rate ? <KV k="환율" v={`1 ${q!.krw.fx_currency} = ${q!.krw.fx_rate.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}원`} tip={`${q!.krw.fx_source} · ${q!.krw.fx_date} 고시`} /> : null}
        {foreign && q!.krw?.fx_date ? <KV k="환율 기준일" v={q!.krw.fx_date} /> : null}
        {q!.market_cap ? <KV k="시가총액" v={q!.market_cap_currency === "KRW" ? wonBig(q!.market_cap * 1e6) : usdM(q!.market_cap)} /> : null}
        {q!.prev_close ? <KV k="전일 종가" v={foreign ? `$${q!.prev_close.toFixed(2)}` : won(q!.prev_close)} /> : null}
        <KV k="상태" v={q!.status_ko} mono={false} tone={q!.status === "ok" ? undefined : "warn"} />
        <KV k="조회 시각" v={p.quotes?.retrieved_at ? new Date(p.quotes.retrieved_at).toLocaleString("ko-KR") : "—"} mono={false} />
        <KV k="시세 기준(시장)" v={q!.price_time || q!.collected_at || p.quotes?.generated_at || "—"} mono={false} />
        {p.quotes?.refresh_status === "stale_retained" || p.quotes?.refresh_status === "throttled" ? (
          <KV k="데이터 상태" v={p.quotes.refresh_detail || "이전 조회분 유지"} mono={false} tone="warn" />
        ) : null}
      </dl>
      {q!.error ? <p className="fine warn">{q!.error}</p> : null}
      <p className="fine">{q!.delay_label}. {foreign ? "원화 환산 = 현지 주가 × 환율 단순 환산이며 한국 거래 가격이 아닙니다." : ""} 출처: {q!.source?.name}. 가격 변동이 없어도 장 마감·휴장이면 정상일 수 있습니다.</p>
      <div className="chart-head">
        <PeriodTabs value={period} onChange={setPeriod} />
        {foreign ? (
          <span className="seg seg-xs">
            <button type="button" className={inKrw ? "is-on" : ""} onClick={() => setInKrw(true)}>KRW</button>
            <button type="button" className={!inKrw ? "is-on" : ""} onClick={() => setInKrw(false)}>USD</button>
          </span>
        ) : null}
      </div>
      <PriceChart data={hist} krw={foreign ? inKrw : false} loading={loading} />
      <p className="fine">시장에서 관측된 가격입니다. 차환 시뮬레이션 결과와 무관하며, 시뮬레이션은 주가를 예측하지 않습니다.</p>
    </>
  ) : null;
  return (
    <Sec label="Market" aside={aside}>
      {!n.listed ? (
        <p className="muted-line">비상장기업{n.listing_note ? ` · ${n.listing_note}` : ""}</p>
      ) : useTv ? (
        <TradingViewTicker key={tv!.symbol} symbol={tv!.symbol} currency={tv!.currency} />
      ) : has ? (
        quoteDetail
      ) : (
        <>
          <p className="muted-line">주가 조회 불가{n.ticker ? ` · ${n.ticker}` : ""}{n.exchange ? ` · ${n.exchange}` : ""}</p>
          {tv && !tv.embeddable && (n.exchange === "KOSPI" || n.exchange === "KOSDAQ" || n.exchange === "KRX") ? (
            <p className="fine">국내 종목은 일간 종가(FinanceDataReader/yfinance)를 사용합니다. 위 시세 버튼으로 갱신하세요.</p>
          ) : tv && !tv.embeddable ? (
            <p className="fine">TradingView 무료 위젯이 {tv.exchangeLabel} 시세를 임베드하지 않습니다.</p>
          ) : null}
        </>
      )}
      {n.listed && n.listing_note ? <p className="fine">{n.listing_note}</p> : null}
      {useTv && has ? <Disclosure label="로컬 시세 상세 (API)">{quoteDetail}</Disclosure> : null}
      {n.listed && !p.quotes?.demo ? (
        <button type="button" className="btn-text" onClick={p.onRefreshQuotes} disabled={p.quotesBusy}><IconReset size={11} /> {refreshLabel(!!p.quotesLive, p.quotesBusy)}</button>
      ) : null}
    </Sec>
  );
}

function LinkRow({ e, p }: { e: NetEdge; p: Props }) {
  return (
    <button type="button" className="link-row" onClick={() => p.onSelectEdge(e.id)}>
      <span className="lr-t">{e.label}</span>
      <span className="lr-m">{REL_LABEL[e.relationship_type] || e.relationship_type}{(e.roles || []).length ? ` · ${(e.roles || []).slice(0, 2).join(" · ")}${(e.roles || []).length > 2 ? ` 외 ${(e.roles || []).length - 2}건 (아래 Lending)` : ""}` : ""}</span>
      <span className="lr-v num">{e.amount_usd_m !== null ? usdM(e.amount_usd_m) : ""}<StTag s={e.source_status} /></span>
    </button>
  );
}

function ShockBlock({ a, stage }: { a: Assessment & { exposure_class?: string }; stage: number }) {
  const shown = a.values.filter((v) => v.round <= stage);
  const later = a.values.filter((v) => v.round > stage);
  const expLabel: Record<string, string> = {
    direct_computed: "직접 측정 · 이자 민감도",
    potential_indirect: "잠재 간접 · 경로만",
    transmission_channel: "전달 채널 · 미산정",
    insufficient_data: "데이터 부족",
    qualitative_refi: "정성 · 만기 재발행",
    qualitative_credit: "정성 · 신용 채널",
    no_identified_exposure: "노출 미확인",
  };
  return (
    <>
      <p className={`cat cat-${a.category}`}>
        <b>{CATEGORY_CODE[a.category]}</b>
        {a.exposure_class ? expLabel[a.exposure_class] || a.exposure_class : CATEGORY_KO[a.category]}
      </p>
      {shown.length ? (
        <dl>
          {shown.map((v) => (
            <KV key={v.label} k={v.label}
              v={v.usd_m !== undefined ? money(v.usd_m, true) : v.pct !== null && v.pct !== undefined ? `${v.pct.toFixed(4)}%` : "—"}
              tip={v.usd_m !== undefined ? korUsd(v.usd_m) : undefined} st={v.status === "computed" ? "VERIFIED" : "ASSUMED"} />
          ))}
        </dl>
      ) : null}
      {later.length ? <p className="fine">{later.map((v) => `${v.label}: S${v.round + 1}에서 표시`).join(" · ")}</p> : null}
      <p className="prose">{a.reason}</p>
      {a.needed ? <p className="fine">정량화에 필요한 데이터: {a.needed}</p> : null}
    </>
  );
}

// ---------------------------------------------------------------- relationship
function EdgeView(p: Props & { id: string }) {
  const e = p.net.edges.find((x) => x.id === p.id);
  if (!e) return null;
  const s = p.nodeMap.get(e.source)!;
  const t = p.nodeMap.get(e.target)!;
  const f = amountFacts(e, p.net.meta.as_of);
  const src = sourceRef(e);
  const nameOfId = (id: string) => (p.nodeMap.get(id) ? dn(p.nodeMap.get(id)) : null);
  const tc = (e as { transmission_class?: string }).transmission_class;
  return (
    <div className="rp-body">
      <header className="ent-head">
        <p className="lbl">{CHANNEL_LABEL[e.impact_channel]}</p>
        <h2 className="edge-h"><button type="button" className="link" onClick={() => p.onSelectNode(s.id)}>{dn(s)}</button><span className="arr">—</span><button type="button" className="link" onClick={() => p.onSelectNode(t.id)}>{dn(t)}</button></h2>
        <p className="ent-sector">{e.label}</p>
      </header>
      <Sec label="Relationship" aside={<StTag s={e.source_status} />}>
        <p className="note" style={{ marginBottom: 8 }}>
          <b>{dn(s)}</b>이(가) <b>{dn(t)}</b>에 대해 「{REL_LABEL[e.relationship_type] || e.relationship_type}」
          {e.roles?.length ? ` (${e.roles.slice(0, 3).join(", ")})` : ""} 관계를 가집니다.
          {" "}계약·현금흐름 방향과 충격 전달 방향은 다를 수 있습니다.
        </p>
        <dl>
          <KV k="유형" v={REL_LABEL[e.relationship_type] || e.relationship_type} mono={false} />
          {(e.roles || []).length ? <KV k="역할" v={(e.roles || []).join(", ")} mono={false} /> : null}
          <KV k="관련 사업" v={(e as { project_name?: string }).project_name || "—"} mono={false} />
          <KV k="금융 단계" v={FINANCING_STAGE_KO[(e as { financing_stage?: string }).financing_stage || ""] || (e as { financing_stage?: string }).financing_stage || "—"} mono={false} />
          <KV k="자금 경로" v={(e as { participation_path?: string }).participation_path || "투자 경로 미공개"} mono={false} />
          <KV k="금액 유형" v={f.kindKo} mono={false} />
          <KV k="위험 전이 경로" v={(e as { stress_direction?: string }).stress_direction || "미기재"} mono={false} />
          <KV k="충격 전달 분류" v={tc ? (TRANSMISSION_CLASS_KO[tc] || ko(tc)) : "분류 없음"} mono={false} />
          <KV k="조건부 의무" v={(e as { contingent_obligation?: boolean }).contingent_obligation ? "예 — 확약 조건 충족 시에만" : "아니오(또는 미기재)"} mono={false} />
          <KV k="의무 발생 조건" v={(e as { obligation_trigger?: string }).obligation_trigger || "—"} mono={false} />
          <KV k="근거" v={`${ko(e.source_status)}${(e as { evidence_status?: string }).evidence_status ? ` · ${(e as { evidence_status?: string }).evidence_status}` : ""}`} mono={false} />
          <KV k="현재 거래 상태" v={f.current === "current" ? statusKo((e as { exposure_status?: string }).exposure_status || (e as { relationship_status?: string }).relationship_status) : CURRENT_KO[f.current]} mono={false} />
          <KV k="금액" v={<>{f.value === null ? "금액 미확인" : f.unit === "억원" ? `${f.value.toLocaleString("ko-KR")}억 원` : usdM(f.value)} <CertTag f={f} /></>}
            tip={`${CERTAINTY_KO[f.certainty]} · ${f.certaintyReason}`} />
          {f.asOf ? <KV k="금액 기준일" v={f.asOf} /> : null}
        </dl>
        {e.amount_note ? <p className="fine">{cleanNote(e.amount_note, nameOfId)}</p> : null}
        {(e as { facility_total_krw_eok?: number | null }).facility_total_krw_eok != null ? (
          <p className="fine">시설·신디케이트 총액 맥락: {Number((e as { facility_total_krw_eok?: number }).facility_total_krw_eok).toLocaleString("ko-KR")}억 — 이 금액을 기관 단독 보유로 보지 않음</p>
        ) : null}
        <p className="fine">근거 원문: {src.status === "linked"
          ? <><a href={src.url!} target="_blank" rel="noreferrer">{src.title} <IconLink size={10} /></a>{src.date ? ` · ${src.date}` : ""}{src.filing ? ` · 접수번호 ${src.filing}` : ""}</>
          : <span className="muted">원문 연결 미확보{src.status === "homepage_only" ? " (기관 홈페이지만 있음 — 근거로 쓰지 않음)" : ""}</span>}</p>
        <p className="fine">미확인 사항: {cleanNote((e as { verification_gap?: string }).verification_gap, nameOfId) || (e.source_status === "VERIFIED" ? "없음(추가 원문 대조는 권장)" : "근거 보강 필요")}</p>
        <p className="prose">{cleanNote(e.explanation, nameOfId)}</p>
      </Sec>
      {(e.contract_ids || []).length ? (
        <Sec label="Contracts">
          {e.contract_ids.map((c) => {
            const x = p.net.financials.instruments.find((i) => i.id === c);
            return x ? <button type="button" key={c} className="ctr-row" onClick={() => p.onSelectContract(c)}><span>{x.name}</span><span className="num">{money(x.principal_usd_m)}</span></button> : null;
          })}
        </Sec>
      ) : null}
      <Sec label="Sources"><SourceList net={p.net} ids={e.source_ids} /></Sec>
    </div>
  );
}

// ---------------------------------------------------------------- contract
function ContractView(p: Props & { id: string }) {
  const x = p.net.financials.instruments.find((i) => i.id === p.id);
  if (!x) return null;
  return (
    <div className="rp-body">
      <header className="ent-head">
        <p className="lbl">{KIND_KO[x.kind]}</p>
        <h2>{x.name}</h2>
        <p className="ent-sector">차입자 {x.borrower || "공시 미확인"} <StTag s={x.borrower_status} /></p>
      </header>
      <Sec label="Terms" aside={`기준 ${x.principal_as_of}`}>
        <dl>
          <KV k="잔액" v={x.principal_usd_m !== null ? usdM(x.principal_usd_m) : "미공시"} tip={x.principal_usd_m !== null ? korUsd(x.principal_usd_m) : x.principal_note} st={x.principal_usd_m !== null ? "VERIFIED" : "UNKNOWN"} />
          {x.commitment_usd_m !== null ? <KV k="약정금액" v={usdM(x.commitment_usd_m)} tip={korUsd(x.commitment_usd_m)} /> : null}
          <KV k="금리" v={rateText(x)} st={x.rate_status} />
          <KV k="유효이자율 (10-Q)" v={x.effective_rate_pct !== null ? `${x.effective_rate_pct}%` : "—"} st={x.effective_rate_status} tip="할인·발행비 상각 포함, 10-Q가 정수 %로 반올림해 공시" />
          <KV k="만기" v={x.maturity || "미공시"} st={x.maturity_status} />
          <KV k="소구 여부" v={x.recourse === null ? "—" : x.recourse ? "소구 (Recourse)" : "비소구 (Non-recourse)"} mono={false} />
          {x.signed ? <KV k="체결" v={x.signed} /> : null}
          {x.customer ? <KV k="연계 고객 계약" v={p.nodeMap.get(x.customer)?.name || x.customer} mono={false} /> : null}
        </dl>
        {x.principal_note ? <p className="fine">{x.principal_note}</p> : null}
        {x.rate_note ? <p className="fine">{x.rate_note}</p> : null}
        {x.amortization ? <p className="fine">상환: {x.amortization}</p> : null}
        {x.collateral ? <p className="fine">담보·보증: {x.collateral}</p> : null}
      </Sec>
      <Sec label="Participants" aside={`${x.participants.length}곳`}>
        {x.participants.length ? (
          <table className="tbl ptbl">
            <thead><tr><th>기관</th><th>역할</th><th className="r">근거</th></tr></thead>
            <tbody>
              {x.participants.map((q) => (
                <tr key={q.entity} onClick={() => p.onSelectNode(q.entity)}>
                  <td>{dn(p.nodeMap.get(q.entity))}</td><td className="wrap">{q.roles.join(", ")}</td><td className="r"><StTag s={q.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="muted-line">참여 금융기관이 공시되지 않음 (채권은 다수 투자자 보유)</p>}
        <p className="fine">Arranger · Bookrunner는 대출을 구조화·판매하는 역할이며 대출 전체를 보유한다는 뜻이 아닙니다. 기관별 보유액은 공시되지 않습니다.</p>
      </Sec>
      <Sec label="Scenario">
        <button type="button" className="btn-text" onClick={() => p.onUseContract(x.id)} disabled={x.principal_usd_m === null && x.effective_rate_pct === null && x.coupon_pct === null && x.spread_pct === null}>이 차입금으로 차환 시나리오 설정 →</button>
      </Sec>
      <Sec label="Sources"><SourceList net={p.net} ids={x.source_ids} /></Sec>
    </div>
  );
}

function RateShockSummary(p: Props & { run: Extract<RunView, { kind: "rate_shock" }> }) {
  const r = p.run.result;
  const s = r.summary;
  const rnd = r.rounds[Math.min(p.stage, r.rounds.length - 1)];
  const byClass: Record<string, string[]> = {};
  for (const [id, a] of Object.entries(r.assessments)) {
    const c = (a as { exposure_class?: string }).exposure_class || a.category;
    (byClass[c] ||= []).push(id);
  }
  const delta = s.total_incremental_interest_usd_m;
  const labels = EXPOSURE_CLASS_KO;
  const qual = (s.potential_indirect || 0) + (s.transmission_channels || 0);
  return (
    <div className="rp-body">
      <header className="ent-head">
        <p className="lbl">Interest Rate Shock · 가상 시나리오</p>
        <h2>{r.benchmark.label_en} <span className="arr">{s.shock_bp > 0 ? "+" : ""}{s.shock_bp}bp</span></h2>
        <p className="ent-sector">{r.benchmark.plain} · 비교 기준: 추가 충격 없음(+0bp) · 재생 {rnd.stage}/{r.rounds.length}단계</p>
      </header>
      <section className="rp-sec">
        <div className="shock-digest">
          <div className="digest-row"><span className="digest-k">① 바뀐 것</span>
            <p className="digest-v">{s.shock_bp ? <>{r.benchmark.label_en} <b className="num">{s.baseline_sofr_pct ?? r.params.sofr_pct}% → {s.stressed_sofr_pct ?? "—"}%</b> ({s.shock_bp > 0 ? "+" : ""}{s.shock_bp}bp){s.crisis_mode && s.crisis_mode !== "rate_only" ? ` · 위기 가정: ${CRISIS_MODE_KO[s.crisis_mode] || ko(s.crisis_mode)}` : ""}</> : <b>추가 충격 없음 (비교 기준 상태)</b>}</p></div>
          <div className="digest-row"><span className="digest-k">② 영향 대상</span>
            <div className="digest-v">
              <ul className="digest-split">
                <li><span className="cert cert-confirmed">정량 계산</span> <b className="num">{s.direct_measurable}</b></li>
                <li><span className="cert cert-inferred">관계만 확인(금액 미산정)</span> <b className="num">{qual}</b></li>
                <li><span className="cert cert-unknown">자료 부족</span> <b className="num">{s.insufficient_data}</b></li>
              </ul>
              <p className="fine">추가 연간 이자(정량분 합계) {delta === null ? "산정 불가" : money(delta, true)} · 분석용 높은·심각 단계 {s.companies_at_or_above_high ?? 0}개 (부도 판정 아님)</p>
            </div></div>
          <div className="digest-row"><span className="digest-k">③ 근거</span>
            <p className="digest-v">공시된 SOFR 연동 잔액 {usdM(s.floating_sofr_principal_usd_m)} × 금리 변화. 고정금리 차입은 이자 불변. 대주·주선 관계는 손실로 계산하지 않습니다.</p></div>
        </div>
      </section>
      <Sec label="Ecosystem Impact" aside="vs +0bp">
        <dl>
          <KV k="현재 기준 (+0bp)" v={`${s.baseline_sofr_pct ?? r.params.sofr_pct}%`} tip="추가 충격 없음 — 절대금리 0%가 아님" />
          <KV k="선택 시나리오" v={`${s.stressed_sofr_pct ?? "—"}% (${s.shock_bp > 0 ? "+" : ""}${s.shock_bp}bp)`} />
          <KV k="현재 대비 변화" v={`${s.shock_bp > 0 ? "+" : ""}${s.shock_bp}bp`} tip="이전 시나리오(+300 등)와의 증분이 아니라 +0bp 대비" />
          <KV k="기준 → 스트레스 금리" v={`${s.baseline_sofr_pct ?? r.params.sofr_pct}% → ${s.stressed_sofr_pct ?? "—"}%`} />
          <KV k="네트워크 기업" v={String(s.network_companies)} />
          <KV k="직접 측정 가능" v={String(s.direct_measurable)} tip="공시 잔액으로 연간 이자 변화를 계산한 기업" />
          <KV k="높은·심각 스트레스" v={String(s.companies_at_or_above_high ?? 0)} tip="직접+2차 합산 · 분석용 밴드 — 파산 예측 아님" />
          <KV k="전염 1차 / 2차 / 3차 이상" v={`${s.order1 ?? 0} / ${s.order2 ?? 0} / ${s.order3_plus ?? 0}`} tip={`최대 ${s.max_contagion_order ?? 0}차 · 정량 ${s.quantified_contagion ?? 0} · 정성 ${s.qualitative_contagion ?? 0} · 경로만 ${s.pathway_only ?? 0}`} />
          <KV k="섹터·SPV" v={String(s.sector_stressed ?? 0)} tip={`심각 ${s.sector_critical ?? 0} · SPV ${s.spv_critical ?? 0} · 모회사 자동 파산 아님`} />
          <KV k="위기 가정" v={CRISIS_MODE_KO[s.crisis_mode ?? "rate_only"] || ko(s.crisis_mode)} mono={false} tip="금리만 / CoreWeave 부도 가정 / 자금조달 경색 / 복합" />
          <KV k="잠재 간접" v={String(s.potential_indirect)} tip="관계는 확인되나 금액 미산정" />
          <KV k="전달 채널" v={String(s.transmission_channels)} tip="대주·주선 — 손실로 자동 해석하지 않음" />
          <KV k="데이터 부족·정성" v={String(s.insufficient_data)} />
          <KV k="추가 연간 이자(합산)" v={delta === null ? "미산정" : money(delta, true)} tip={delta !== null ? korUsd(delta) : undefined} tone={delta && delta > 0 ? "warn" : undefined} />
          <KV k="SOFR 연동 공시 잔액" v={usdM(s.floating_sofr_principal_usd_m)} tip={korUsd(s.floating_sofr_principal_usd_m)} />
        </dl>
        {r.origin_stress ? (
          <dl style={{ marginTop: 8 }}>
            <KV k="재무 스트레스 (분석용)" v={STRESS_LEVEL_KO[r.origin_stress.level] || r.origin_stress.level} mono={false} tip={r.origin_stress.metric_trigger || undefined} tone={r.origin_stress.level === "critical" || r.origin_stress.level === "high" ? "warn" : undefined} />
            <KV k="Δ이자/연환산 OCF" v={r.origin_stress.score_delta_over_ocf != null ? `${(r.origin_stress.score_delta_over_ocf * 100).toFixed(1)}%` : "—"} />
            <KV k="OCF/이자 커버리지" v={multipleChange(r.origin_stress.baseline_coverage, r.origin_stress.stressed_coverage) || "—"} mono={false} />
            <KV k="임계 SOFR (분석용 · 약정 아님)" v={r.origin_stress.critical_sofr_pct != null ? `${r.origin_stress.critical_sofr_pct.toFixed(2)}%` : "공시 자료로 산정 불가"} tip={r.origin_stress.critical_trigger || undefined} />
          </dl>
        ) : null}
        <p className="fine">관계가 있다고 해서 재무 영향을 받은 것으로 세지 않습니다. 행성 파괴는 시나리오 추정이며 부도 판정이 아닙니다.</p>
      </Sec>
      <section className="rp-sec">
        <Disclosure label="계산식">
          <ul className="log">{r.formulas.map((t, i) => <li key={i}>{t}</li>)}</ul>
        </Disclosure>
        <Disclosure label={`재생 단계 로그 · ${rnd.stage}단계 ${rnd.title_ko || ""}`}>
          <ul className="log">{rnd.lines.map((t, i) => <li key={i}>{t}</li>)}</ul>
        </Disclosure>
      </section>
      <Sec label="Exposure Classes">
        {Object.entries(labels).map(([k, lab]) => (
          <div key={k} className="catrow">
            <span className="cat">{lab}</span>
            <span className="num">{(byClass[k] || []).length}</span>
          </div>
        ))}
      </Sec>
      <Sec label="Instruments" aside="CoreWeave 차입금">
        <table className="tbl">
          <thead><tr><th>차입금</th><th>유형</th><th className="r">이자 Δ</th></tr></thead>
          <tbody>
            {r.instruments.filter((i) => i.exposure_class !== "not_applicable").slice(0, 12).map((i) => (
              <tr key={i.id} data-tip={i.reason}>
                <td>{i.name}</td>
                <td className="wrap">{EXPOSURE_CLASS_KO[i.exposure_class] || ko(i.exposure_class)}</td>
                <td className="r num">{i.annual_interest_delta_usd_m === null ? "—" : money(i.annual_interest_delta_usd_m, true)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Sec>
      <section className="rp-sec">
        <Disclosure label="해석 한계 · 주의">
          <ul className="log">{r.notes.map((t, i) => <li key={i}>{t}</li>)}</ul>
          {r.warnings.length ? <p className="fine warn">{r.warnings.slice(0, 3).join(" · ")}</p> : null}
        </Disclosure>
      </section>
    </div>
  );
}

function PfShockSummary(p: Props & { run: Extract<RunView, { kind: "pf_shock" }> }) {
  const r = p.run.result;
  const pf = r.pf;
  const rnd = r.rounds[Math.min(p.stage, r.rounds.length - 1)];
  const [allCo, setAllCo] = useState(false);
  const order = { quantified: 0, contract: 1, assumption: 2 } as const;
  const ranked = [...pf.affected_companies].sort((a, b) => order[a.basis] - order[b.basis] || a.company_name.localeCompare(b.company_name, "ko"));
  const shown = allCo ? ranked : ranked.slice(0, 5);
  const nm = (id: string) => dn(p.nodeMap.get(id)) || id;
  const intDelta = (pr: PfShockResult["pf"]["projects"][number]) => pr.interest_delta_usd_m == null
    ? <span className="muted" data-tip="잔액·금리 공시가 없어 계산할 수 없음">산정 불가</span>
    : pr.interest_delta_usd_m === 0 && !pf.rate_bp && !pf.kr_rate_bp ? <span className="muted">0 (금리 충격 없음)</span>
      : money(pr.interest_delta_usd_m, true);
  const dscrTxt = (pr: PfShockResult["pf"]["projects"][number]) => pr.baseline_dscr == null || pr.stressed_dscr == null
    ? <span className="muted" data-tip="CFADS·원리금 일정 미공시">산정 불가</span>
    : `${pr.baseline_dscr.toFixed(2)}배 → ${pr.stressed_dscr.toFixed(2)}배`;
  return (
    <div className="rp-body">
      <header className="ent-head">
        <p className="lbl">AI Data Center PF Shock · 가상 시나리오</p>
        <h2>{changedInputs(pf).join(" · ") || "추가 충격 없음"}</h2>
        <p className="ent-sector">비교 기준: 추가 충격 없음 · 재생 {rnd.stage + 1}/{r.rounds.length}단계</p>
      </header>
      <section className="rp-sec"><PfShockDigest result={r} /></section>
      <Sec label="주요 영향" aside={`${ranked.length}개 중 ${shown.length}개`}>
        {ranked.length ? (
          <ul className="ent-list">
            {shown.map((c) => (
              <li key={c.company_id}>
                <button type="button" className="ent" onClick={() => p.onSelectNode(c.company_id)}>
                  <span className="ent-name">{c.company_name}</span>
                  <span className={`cert cert-${c.basis === "quantified" ? "confirmed" : c.basis === "contract" ? "inferred" : "assumed"}`}>{c.basis === "quantified" ? "정량" : c.basis === "contract" ? "계약 근거" : "가정 경로"}</span>
                </button>
                <p className="fine">{c.impact_category} · {c.transmission_path}</p>
              </li>
            ))}
          </ul>
        ) : <p className="muted-line">스트레스가 올라간 기업 없음</p>}
        {ranked.length > 5 ? <button type="button" className="btn-text" onClick={() => setAllCo((v) => !v)}>{allCo ? "주요 5개만 보기" : `전체 ${ranked.length}개 보기`}</button> : null}
      </Sec>
      <Sec label="사업장" aside="기준 대비 · 계산 가능분만 수치">
        <table className="tbl">
          <thead><tr><th>사업장</th><th>모형 단계</th><th className="r">DSCR</th><th className="r">추가 이자</th></tr></thead>
          <tbody>
            {pf.projects.filter((pr) => pr.level !== "normal" || pr.quantified).map((pr) => (
              <tr key={pr.project_id}>
                <td><button type="button" className="btn-text" onClick={() => p.onSelectNode(pr.project_id)}>{projectDisplayName({ id: pr.project_id, name: pr.name })}</button></td>
                <td>{STRESS_LEVEL_KO[pr.level] || pr.level}</td>
                <td className="r num">{dscrTxt(pr)}</td>
                <td className="r num">{intDelta(pr)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="fine">모형 단계는 분석용 구분이며 실제 재무약정 위반·법적 부도 기준이 아닙니다. DSCR 1.0 미만은 모형상 상환여력 부족 신호입니다.</p>
      </Sec>
      <Sec label="미국 → 국내 연결" aside="직접 계약과 가정 경로 구분">
        <ul className="log">
          {pf.us_korea_paths.filter((x) => x.transmission_class !== "unclassified").slice(0, 12).map((x) => (
            <li key={x.edge_id}>
              <button type="button" className="btn-text" onClick={() => p.onSelectNode(x.from)}>{nm(x.from)}</button>
              {" → "}
              <button type="button" className="btn-text" onClick={() => p.onSelectNode(x.to)}>{nm(x.to)}</button>
              {" · "}{TRANSMISSION_CLASS_KO[x.transmission_class] || ko(x.transmission_class)}
            </li>
          ))}
        </ul>
        {pf.korean_unclassified_links ? <p className="fine">반도체 공급·제휴 등 분류 없는 링크 {pf.korean_unclassified_links}건은 직접 계약으로 세지 않습니다.</p> : null}
      </Sec>
      <section className="rp-sec">
        <Disclosure label={`재생 단계 로그 · ${rnd.stage + 1}단계 ${rnd.title_ko || ""}`}>
          <ul className="log">{rnd.lines.map((t, i) => <li key={i}>{t}</li>)}</ul>
        </Disclosure>
        <Disclosure label="사용자 가정">
          <ul className="log">{pf.assumptions.map((t, i) => <li key={i}>{t}</li>)}</ul>
        </Disclosure>
        <Disclosure label="계산 한계 · 해석 주의">
          <ul className="log">{pf.limitations.map((t, i) => <li key={i}>{t}</li>)}</ul>
          {r.warnings.length ? <ul className="log">{r.warnings.map((t, i) => <li key={`w${i}`}>{t}</li>)}</ul> : null}
        </Disclosure>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------- run summary (Shock View)
function RunSummary(p: Props & { run: RunView }) {
  if (p.run.kind === "pf_shock") return <PfShockSummary {...p} run={p.run} />;
  if (p.run.kind === "rate_shock") return <RateShockSummary {...p} run={p.run} />;
  const r = p.run.result;
  const m = r.result;
  const rnd = r.rounds[Math.min(p.stage, r.rounds.length - 1)];
  const cats: Record<string, string[]> = {};
  for (const [id, a] of Object.entries(r.assessments)) (cats[a.category] ||= []).push(id);
  const ac = r.assumption_chain;
  const prev = p.run.prev;
  return (
    <div className="rp-body">
      <header className="ent-head">
        <p className="lbl">Refinancing · 상세 차환 분석</p>
        <h2>{r.instrument.name} <span className="arr">→</span> {m.new_rate_pct}%</h2>
        <p className="ent-sector">기준 {r.reference.as_of} 10-Q · Stage {rnd.stage}/{r.rounds.length} {STAGES[rnd.round]}</p>
      </header>

      <Sec label="Funding Cost" aside="계산값">
        <dl>
          <KV k="차환 금액" v={usdM(m.refinanced_usd_m)} tip={korUsd(m.refinanced_usd_m)} />
          <KV k="기존 비교금리" v={`${m.existing_rate_pct}%`} tip={r.existing_rate.formula} st={r.existing_rate.status} />
          <KV k="신규 금리" v={`${m.new_rate_pct}%`} st="ASSUMED" />
          <KV k="기존 연간 이자" v={usdM(m.annual_interest_existing_usd_m)} tip={korUsd(m.annual_interest_existing_usd_m)} />
          <KV k="차환 후 연간 이자" v={usdM(m.annual_interest_new_usd_m)} tip={korUsd(m.annual_interest_new_usd_m)} />
          <KV k="추가 연간 이자" v={money(m.annual_interest_delta_usd_m, true)} tone={m.annual_interest_delta_usd_m > 0 ? "warn" : undefined} tip={korUsd(m.annual_interest_delta_usd_m)} />
          <KV k="6개월 환산 / 상반기 OCF" v={m.delta_6m_vs_ocf_6m_pct === null ? "—" : `${money(m.delta_6m_usd_m, true)} · ${m.delta_6m_vs_ocf_6m_pct > 0 ? "+" : m.delta_6m_vs_ocf_6m_pct < 0 ? "−" : ""}${Math.abs(m.delta_6m_vs_ocf_6m_pct).toFixed(2)}%`} tip={`2026 상반기 영업현금흐름 ${usdM(r.reference.ocf_6m_usd_m)} (10-Q)`} />
          {m.one_off_fee_usd_m ? <KV k="일회성 조달비용" v={usdM(m.one_off_fee_usd_m)} /> : null}
          {m.funding_need_usd_m ? <KV k="자금조달 필요액" v={usdM(m.funding_need_usd_m)} tone="warn" tip="차환되지 않아 자체 자금으로 상환해야 하는 금액" /> : null}
        </dl>
        <p className="fine">추가 연간 이자 = 차환 금액 × (신규 금리 − 기존 비교금리). 이 차입금에만 적용 · 다른 차입금 금리는 그대로.</p>
      </Sec>

      <Sec label="Compare" aside="같은 차입금 · 같은 비금리 가정">
        <table className="tbl cmp">
          <thead><tr><th>시나리오</th><th className="r">신규 금리</th><th className="r">연간 이자</th><th className="r">추가 이자</th></tr></thead>
          <tbody>
            {r.comparison.map((c) => (
              <tr key={c.label} className={c.new_rate_pct === m.new_rate_pct ? "cur" : ""}>
                <td>{c.label}</td><td className="r num">{c.new_rate_pct}%</td><td className="r num">{usdM(c.annual_interest_new_usd_m)}</td>
                <td className={`r num ${c.annual_interest_delta_usd_m > 0 ? "t-warn" : ""}`} data-tip={korUsd(c.annual_interest_delta_usd_m)}>{money(c.annual_interest_delta_usd_m, true)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {prev && prev.summary ? <p className="fine">이전 실행({String(prev.created_at || "").slice(0, 16).replace("T", " ")}): {String(prev.summary.new_rate_pct)}% → 추가 이자 {money(Number(prev.summary.annual_interest_delta_usd_m), true)}</p> : null}
      </Sec>

      <Sec label={`Stage ${rnd.stage} · ${STAGES[rnd.round]}`}>
        <ul className="log">{rnd.lines.map((t, i) => <li key={i}>{t}</li>)}</ul>
      </Sec>

      <Sec label="Investment Capacity" aside="사용자 가정">
        <dl>
          <KV k="CAPEX 흡수율" v={ac.capex_absorption_pct === null ? "미입력" : `${ac.capex_absorption_pct}%`} st="ASSUMED" />
          <KV k="CAPEX 축소" v={ac.capex_cut_usd_m === null ? "미산정" : money(-ac.capex_cut_usd_m, true)} />
          <KV k="GPU 비중" v={ac.gpu_share_pct === null ? "미입력" : `${ac.gpu_share_pct}%`} st="ASSUMED" />
          <KV k="GPU 구매 감소" v={ac.gpu_purchase_cut_usd_m === null ? "미산정" : money(-ac.gpu_purchase_cut_usd_m, true)} />
          <KV k="NVIDIA FY26 매출 대비" v={ac.gpu_cut_vs_nvidia_revenue_pct === null ? "미산정" : `${ac.gpu_cut_vs_nvidia_revenue_pct.toFixed(4)}%`} tip={`NVIDIA FY2026 매출 ${usdM(r.reference.nvidia_revenue_fy2026_usd_m)} (8-K)`} />
        </dl>
        <p className="fine">추가 이자가 투자 축소로 이어진다는 보장은 없습니다. 비워 두면 계산하지 않고 잠재 경로로만 표시합니다.</p>
      </Sec>

      <Sec label="Network Impact" aside="B 계산 · C 가정 · D 관계만 · E 미확인">
        {(["computed", "assumed", "relationship_only", "unconfirmed"] as const).map((c) => (
          <div key={c} className="catrow">
            <span className={`cat cat-${c}`}><b>{CATEGORY_CODE[c]}</b>{CATEGORY_KO[c]}</span>
            <span className="num">{(cats[c] || []).length}</span>
          </div>
        ))}
        <p className="fine">D: 관계는 확인되지만 영향 규모를 계산할 공개 데이터가 없어 금액·점수를 만들지 않습니다. 기업을 누르면 필요한 데이터가 표시됩니다.</p>
      </Sec>

      <Sec label="Schedule" aside="신규 차입 일시상환 가정">
        <Disclosure label={`연도별 이자 · 원리금 (${r.schedule.length}개 연도)`}>
          <table className="tbl sched">
            <thead><tr><th>연도</th><th className="r">개월</th><th className="r">기존 이자</th><th className="r">신규 이자</th><th className="r">원리금</th></tr></thead>
            <tbody>
              {r.schedule.map((s) => (
                <tr key={s.year}><td className="num">{s.year}</td><td className="r num">{s.months}</td><td className="r num">{usdM(s.interest_existing_usd_m)}</td><td className="r num">{usdM(s.interest_new_usd_m)}</td><td className="r num">{usdM(s.debt_service_new_usd_m)}</td></tr>
              ))}
            </tbody>
          </table>
        </Disclosure>
      </Sec>

      {r.warnings.length ? <Sec label="Warnings"><ul className="assm warn">{r.warnings.map((w) => <li key={w}>{w}</li>)}</ul></Sec> : null}

      <section className="rp-sec">
        <Disclosure label="계산 기준 · 해석 한계">
          <ul className="assm">{r.notes.map((n) => <li key={n}>{n}</li>)}</ul>
        </Disclosure>
      </section>

      <Sec label="Sources"><SourceList net={p.net} ids={[...r.instrument.source_ids, ...r.reference.source_ids, r.reference.nvidia_source_id, p.net.financials.market_inputs.sofr_source_id]} /></Sec>
    </div>
  );
}

// ---------------------------------------------------------------- market overview (Market View, nothing selected)
function MarketOverviewView(p: Props) {
  const items = (p.quotes?.items || []).filter((q) => q.listed);
  const priced = items.filter((q) => q.price !== null && q.price !== undefined);
  const ranked = useMemo(() => {
    const withPct = priced.filter((q) => q.change_pct !== null && q.change_pct !== undefined);
    const without = priced.filter((q) => q.change_pct === null || q.change_pct === undefined);
    const unpriced = items.filter((q) => q.price === null || q.price === undefined);
    withPct.sort((a, b) => (b.change_pct as number) - (a.change_pct as number));
    return [...withPct, ...without, ...unpriced];
  }, [items, priced]);
  const fx = p.quotes?.fx.rates || {};
  let rank = 0;
  return (
    <div className="rp-body">
      <header className="ent-head">
        <p className="lbl">Market View · 관측 시세</p>
        <h2>상장 {items.length}개 · 시세 {priced.length}개</h2>
        <p className="ent-sector">{p.quotes?.note}</p>
        <p className="fine">가격은 일간 종가(실시간 아님) · {p.quotesLive ? "시세 서버 연결됨" : "저장된 스냅샷"}{p.quotes?.retrieved_at ? ` · 마지막 조회 ${new Date(p.quotes.retrieved_at).toLocaleString("ko-KR")}` : p.quotes?.generated_at ? ` · 스냅샷 생성 ${String(p.quotes.generated_at).replace("T", " ").slice(0, 16)}` : ""}</p>
      </header>
      <Sec label="구분">
        <p className="fine">아래 표는 <b>실제 관측 주가</b>입니다. Shock 탭의 금리 충격·차환 가정과 무관하며, 충격 bp를 바꿔도 이 숫자는 바뀌지 않습니다.</p>
      </Sec>
      <Sec label="Performance" aside={<button type="button" className="btn-text" onClick={p.onRefreshQuotes} disabled={p.quotesBusy} data-tip={refreshTip(!!p.quotesLive)}><IconReset size={11} /> {refreshLabel(!!p.quotesLive, p.quotesBusy)}</button>}>
        <table className="tbl qtbl">
          <thead><tr><th>#</th><th>기업</th><th className="r">가격</th><th className="r">등락</th><th className="r">변동</th><th className="r">기준</th></tr></thead>
          <tbody>
            {ranked.map((q) => {
              const n = p.nodeMap.get(q.entity);
              if (!n) return null;
              const has = q.price !== null && q.price !== undefined;
              const up = (q.change_pct ?? 0) > 0, down = (q.change_pct ?? 0) < 0;
              if (has && q.change_pct !== null && q.change_pct !== undefined) rank += 1;
              const rnk = has && q.change_pct !== null && q.change_pct !== undefined ? rank : "—";
              const priceTxt = !has ? null : q.currency === "KRW" ? won(q.price!) : `$${q.price!.toFixed(2)}`;
              const absTxt = !has || q.change === null || q.change === undefined ? "—"
                : q.currency === "KRW" ? `${q.change > 0 ? "+" : q.change < 0 ? "−" : ""}${Math.abs(Math.round(q.change)).toLocaleString("ko-KR")}`
                : `${q.change > 0 ? "+" : q.change < 0 ? "−" : ""}${Math.abs(q.change).toFixed(2)}`;
              const asOf = (q.price_time || q.collected_at || "").replace("T", " ").slice(0, 16) || "—";
              const src = q.source?.name || q.provider || "";
              return (
                <tr key={q.entity} onClick={() => p.onSelectNode(q.entity)} className={up ? "row-up" : down ? "row-down" : ""}>
                  <td className="num muted">{rnk}</td>
                  <td>{dn(n)}<div className="tiny muted num">{q.ticker} · {q.exchange}{q.currency ? ` · ${q.currency}` : ""}{src ? ` · ${src}` : ""}</div></td>
                  {has ? (
                    <>
                      <td className="r num"><b>{priceTxt}</b></td>
                      <td className={`r num ${up ? "is-up" : down ? "is-down" : ""}`}>{q.change_pct !== null && q.change_pct !== undefined ? sgnPct(q.change_pct) : "—"}</td>
                      <td className={`r num ${up ? "is-up" : down ? "is-down" : ""}`}>{absTxt}</td>
                      <td className="r num tiny muted">{asOf}</td>
                    </>
                  ) : <td colSpan={4} className="r wrap muted tiny">{q.status_ko}{q.error ? ` — ${q.error}` : ""}</td>}
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="fine">순위 = 일간 등락률(높은 순). 미국 yfinance 일간 종가 · 한국 FinanceDataReader. 결측은 비우며 가짜 숫자를 넣지 않습니다. 지도 색도 같은 관측값입니다.</p>
      </Sec>
      <Sec label="FX" aside={p.quotes?.fx.source}>
        {Object.keys(fx).length ? (
          <dl>{Object.entries(fx).map(([c, r]) => <KV key={c} k={`1 ${c}`} v={`${r.krw_per_unit.toLocaleString("ko-KR", { maximumFractionDigits: 2 })}원`} tip={`${r.obs_date} 고시`} />)}</dl>
        ) : <p className="muted-line">환율 미수집 — 현지 통화 가격은 표시됩니다. (환율은 한국수출입은행 API 키가 설정된 경우에만 수집)</p>}
      </Sec>
      {p.quotes?.providers && Object.keys(p.quotes.providers).length ? (
        <Sec label="Providers">
          <dl>
            {Object.entries(p.quotes.providers).map(([k, v]) => (
              <KV key={k} k={{ quotes_us: "yfinance (미국 일간 종가)", quotes_krx: "FinanceDataReader (KRX)", fx: "한국수출입은행 (환율)" }[k] || k}
                v={v.last_status_ko || "아직 조회 안 함"} mono={false} tip={v.last_success_at ? `마지막 성공 ${v.last_success_at}` : v.detail || undefined} tone={v.last_status && v.last_status !== "ok" ? "warn" : undefined} />
            ))}
          </dl>
        </Sec>
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------- lenders & commercial (Overview)
function LendersSec({ p }: { p: Props }) {
  const rows = useMemo(() => {
    const m = new Map<string, { id: string; n: number; names: string[]; first: string | null; last: string | null; roles: Set<string> }>();
    for (const x of p.net.financials.instruments) {
      for (const q of x.participants) {
        const r = m.get(q.entity) || { id: q.entity, n: 0, names: [], first: null, last: null, roles: new Set<string>() };
        r.n += 1;
        r.names.push(x.name);
        if (x.maturity) { r.first = !r.first || x.maturity < r.first ? x.maturity : r.first; r.last = !r.last || x.maturity > r.last ? x.maturity : r.last; }
        q.roles.forEach((ro) => r.roles.add(ro.replace(/ \(.*\)$/, "")));
        m.set(q.entity, r);
      }
    }
    return [...m.values()].sort((a, b) => b.n - a.n || dn(p.nodeMap.get(a.id)).localeCompare(dn(p.nodeMap.get(b.id)), "ko"));
  }, [p.net, p.nodeMap]);
  const [all, setAll] = useState(false);
  const shown = all ? rows : rows.slice(0, 10);
  return (
    <Sec label="Lenders" aside={`${rows.length}개 기관`}>
      <table className="tbl lend">
        <thead><tr><th>기관 · 참여 계약</th><th className="r">계약 수</th><th className="r">만기</th></tr></thead>
        <tbody>
          {shown.map((r) => (
            <tr key={r.id} onClick={() => p.onSelectNode(r.id)}>
              <td>{dn(p.nodeMap.get(r.id))}<div className="tiny muted">{[...r.roles].slice(0, 2).map((x) => ko(x)).join(", ")}</div>
                <div className="tiny muted wrap">{r.names.slice(0, 2).join(" · ")}{r.names.length > 2 ? ` 외 ${r.names.length - 2}건` : ""}</div></td>
              <td className="r num">{r.n}건</td>
              <td className="r num">{r.first ? (r.first.slice(0, 4) === r.last?.slice(0, 4) ? r.first.slice(0, 4) : `${r.first.slice(0, 4)}~${r.last?.slice(2, 4)}`) : "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 10 ? <button type="button" className="btn-text" onClick={() => setAll((a) => !a)}>{all ? "접기" : `전체 ${rows.length}개 기관 보기`}</button> : null}
      <p className="fine">공시는 계약 단위 금액과 참여기관 명단만 제공합니다. 기관별 보유액은 공시되지 않으며, 같은 계약 총액을 참여기관마다 더하면 중복 집계가 되므로 기관별 금액 합계를 표시하지 않습니다. 계약 금액은 기관을 눌러 계약별로 확인하세요.</p>
    </Sec>
  );
}

function CommercialSec({ p }: { p: Props }) {
  const c = p.net.financials.commercial;
  return (
    <Sec label="Commercial" aside={`수주잔고 · ${c.rpo_as_of}`}>
      <p className="big-num num" data-tip={korUsd(c.rpo_usd_m)}>RPO {usdM(c.rpo_usd_m)}</p>
      <ShareBar parts={c.rpo_buckets} total={c.rpo_usd_m} />
      <p className="fine">{c.post_q2_note}. 계약별 남은 금액은 공시되지 않습니다.</p>
      <Timeline rows={commercialRows(p.net)} today={p.net.meta.as_of} from={2024} to={2034}
        caption="공시·발표된 고객·약정·임차 계약. 금액은 발표 기준이며 임차 2건은 임대인 측 예상 매출입니다." />
      <dl>
        {c.concentration.map((x) => <KV key={x.customer} k={`${x.customer} 매출 비중`} v={`${x.q2_3m_pct}% (2분기)${x.h1_6m_pct !== null ? ` · ${x.h1_6m_pct}% (상반기)` : ""}`} tip={c.concentration_note} />)}
        <KV k="미개시 임차 약정" v={usdM(c.lease_not_commenced_usd_m)} tip={c.lease_note} />
        <KV k="운영리스 미할인 지급액" v={usdM(c.lease_operating_undiscounted_usd_m)} />
        <KV k="계약 전력 / 가동 전력" v={`${c.contracted_power_gw}GW / ${c.active_power_gw}GW`} tip={c.power_note} />
      </dl>
      <p className="fine">{c.concentration_note}</p>
    </Sec>
  );
}

// ---------------------------------------------------------------- overview (Network View, nothing selected)
function Overview(p: Props) {
  if ((p.net.meta as { ecosystem?: string }).ecosystem === "datacenter_pf") return <PfOverview {...p} />;
  const f = p.net.financials;
  const vendor = f.instruments.filter((x) => x.kind === "vendor_financing").length;
  const netSum = (f.totals.recourse_net_usd_m || 0) + (f.totals.nonrecourse_net_usd_m || 0);
  const max = Math.max(...f.maturities.map((x) => x.usd_m));
  const metric = (id: string) => f.metrics.find((x) => x.id === id);
  return (
    <div className="rp-body">
      <header className="ent-head">
        <p className="lbl">CoreWeave · Debt Structure</p>
        <h2>총 차입 원금 {usdM(f.totals.principal_usd_m)}</h2>
        <p className="ent-sector">대상: CoreWeave 자체 차입 · 10-Q 기준일 {f.as_of} · 소구 {usdM(f.totals.recourse_net_usd_m)} · 비소구 {usdM(f.totals.nonrecourse_net_usd_m)} (순액)</p>
        {Math.abs(netSum - f.totals.principal_usd_m) > 1 ? (
          <p className="fine">원금 합계({usdM(f.totals.principal_usd_m)})와 순액 합계({usdM(netSum)})의 차이 {usdM(f.totals.principal_usd_m - netSum)}는 할인·발행비용 차감 등 회계상 순액 처리에서 생깁니다(10-Q 표시 기준).</p>
        ) : null}
      </header>
      <Sec label="Maturities" aside="원금 상환 예정">
        <ul className="mat">
          {f.maturities.map((x) => (
            <li key={x.period}><span>{x.period}</span><i style={{ width: `${(x.usd_m / max) * 100}%` }} /><b className="num" data-tip={korUsd(x.usd_m)}>{usdM(x.usd_m)}</b></li>
          ))}
        </ul>
      </Sec>
      <LendersSec p={p} />

      <Sec label="Debt Timeline" aside="체결 → 최종 만기">
        <Timeline rows={f.instruments.filter((x) => x.maturity).sort((a, b) => (a.maturity || "").localeCompare(b.maturity || "")).map((x) => ({
          id: x.id, label: x.name, start: x.signed, end: x.maturity, amount: x.principal_usd_m, amountNote: x.commitment_usd_m !== null ? `약정 ${usdM(x.commitment_usd_m)}` : "잔액 미공시", tone: "debt" as const,
        }))} today={p.net.meta.as_of} onSelect={p.onSelectContract}
          caption="잔액 2026.6.30 (10-Q). 분할상환 차입금은 만기 전에 잔액이 줄어듭니다. OEM 금융은 만기 미공시로 제외." />
      </Sec>

      <CommercialSec p={p} />

      <Sec label="Cash Flow" aside="2026 상반기 · 10-Q">
        <dl>
          {["contractual_interest_6m", "cash_interest_6m", "ocf_6m", "capex_6m", "cash", "rpo"].map((id) => {
            const m = metric(id);
            return m ? <KV key={id} k={m.label} v={usdM(m.value_usd_m)} tip={`${korUsd(m.value_usd_m)} · ${m.period}`} /> : null;
          })}
        </dl>
      </Sec>
      <Sec label="Contracts" aside={`${f.instruments.length}건${vendor ? ` (공급사 금융 ${vendor}건 포함)` : ""}`}>
        {vendor ? <p className="fine">상단 Contracts 수({f.instruments.length - vendor}건)는 대출·채권·전환사채·리볼버만 셉니다. 아래 목록은 공급사 금융 {vendor}건을 포함한 전체 차입금입니다.</p> : null}
        {f.instruments.map((x) => (
          <button type="button" key={x.id} className="ctr-row" onClick={() => p.onSelectContract(x.id)}>
            <span>{x.name}</span><span className="num">{money(x.principal_usd_m)}</span><em>{x.maturity || "만기 미공시"} · {x.participants.length ? `${x.participants.length}개 기관` : "참여기관 미공시"}</em>
          </button>
        ))}
      </Sec>
      <section className="rp-sec">
        <Disclosure label="이 화면의 숫자 구분">
          <ul className="assm">
            <li>VERIFIED: 10-Q · 8-K · 회사 발표로 확인</li>
            <li>INFERRED: 2차 출처 또는 구조상 추론 (점선)</li>
            <li>ASSUMED: 사용자가 시나리오에 입력한 값</li>
            <li>UNKNOWN: 공개자료로 확인되지 않음 — 숫자를 만들지 않음</li>
            <li>{p.stats?.note}</li>
          </ul>
        </Disclosure>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------- AI DC PF overview (nothing selected)
function PfOverview(p: Props) {
  const f = p.net.financials;
  const insts = f.instruments;
  const byBorrower = new Map<string, Instrument[]>();
  for (const x of insts) {
    const k = x.borrower || "차주 미공시";
    if (!byBorrower.has(k)) byBorrower.set(k, []);
    byBorrower.get(k)!.push(x);
  }
  const nameOf = (id: string) => (p.nodeMap.get(id) ? dn(p.nodeMap.get(id)) : id);
  const today = p.net.meta.as_of;
  const kr = p.net.nodes.filter((n) => (n as { region?: string }).region === "KR");
  const spv = kr.filter((n) => n.entity_type === "spv" || n.group === "project_finance").length;
  const krIds = new Set(kr.map((n) => n.id));
  const krLoans = p.net.edges.filter((e) => (krIds.has(e.source) || krIds.has(e.target)) && e.relationship_type === "PROJECT_LOAN");
  const krLoanCurrent = krLoans.filter((e) => amountFacts(e, today).current === "current");
  const krLoanConfirmed = krLoanCurrent.filter((e) => amountFacts(e, today).certainty === "confirmed");
  return (
    <div className="rp-body">
      <header className="ent-head">
        <p className="lbl">AI Data Center PF · 개요</p>
        <h2>미국 DC 프로젝트 금융계약 {insts.length}건</h2>
        <p className="ent-sector">대상: {[...byBorrower.keys()].map(nameOf).join(" · ")} (프로젝트 SPC 차주) · 기준 {f.as_of}</p>
        <p className="fine">이 금액은 각 프로젝트 SPC의 차입이며 <b>CoreWeave 자체 차입금이 아닙니다</b>. CoreWeave는 임차인(고객)으로 연결됩니다. CoreWeave 자체 차입은 AI 반도체 생태계 화면에서 봅니다.</p>
      </header>
      <Sec label="차주별 계약" aside="차주 내 계약 잔액 · 비소구">
        <table className="tbl">
          <thead><tr><th>차주</th><th className="r">계약</th><th className="r">잔액 합계</th></tr></thead>
          <tbody>
            {[...byBorrower.entries()].map(([b, xs]) => {
              const known = xs.filter((x) => x.principal_usd_m !== null);
              const sum = known.reduce((s, x) => s + (x.principal_usd_m || 0), 0);
              return (
                <tr key={b} onClick={() => p.nodeMap.has(b) && p.onSelectNode(b)}>
                  <td>{nameOf(b)}</td>
                  <td className="r num">{xs.length}</td>
                  <td className="r num" data-tip={korUsd(sum)}>{known.length ? usdM(sum) : "미공시"}{known.length < xs.length ? <div className="tiny muted">미공시 {xs.length - known.length}건 제외</div> : null}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="fine">합계는 서로 다른 차주의 독립된 계약을 더한 값({usdM(f.totals.principal_usd_m)})이며, 기준일이 계약마다 다를 수 있습니다. 상단 「US PF 계약」 수와 같은 범위입니다.</p>
      </Sec>
      <Sec label="계약 일정" aside="체결 → 최종 만기">
        <Timeline rows={insts.filter((x) => x.maturity).sort((a, b) => (a.maturity || "").localeCompare(b.maturity || "")).map((x) => ({
          id: x.id, label: `${nameOf(x.borrower || "")} · ${x.name}`, start: x.signed, end: x.maturity, amount: x.principal_usd_m, amountNote: x.commitment_usd_m !== null ? `약정 ${usdM(x.commitment_usd_m)}` : "잔액 미공시", tone: "debt" as const,
        }))} today={today} onSelect={p.onSelectContract}
          caption="각 계약의 잔액 기준일은 계약 상세에서 확인하세요. 분할상환 계약은 만기 전에 잔액이 줄어듭니다." />
      </Sec>
      <LendersSec p={p} />
      <Sec label="국내 PF 관계 요약" aside={`기준 ${today}`}>
        <dl>
          <KV k="국내 회사·SPC" v={`${kr.length}개 (SPC·PFV ${spv}개)`} mono={false} />
          <KV k="국내 PF 대출 관계" v={`현재 ${krLoanCurrent.length}건 · 그중 금액 확인 ${krLoanConfirmed.length}건`} mono={false} />
        </dl>
        <p className="fine">국내 대출 금액은 차주(SPC)·대주별 관계에서 확인합니다. 서로 다른 사업·기준일의 금액은 이 화면에서 합산하지 않습니다.</p>
      </Sec>
      <section className="rp-sec">
        <Disclosure label="이 화면의 숫자 구분">
          <ul className="assm">
            <li>확인된 금액: 공시·회사 발표로 확인</li>
            <li>추정·확인 필요: 원문 단위나 현재 잔액이 확인되지 않음 — 합계에 넣지 않음</li>
            <li>공개자료 추론: 2차 자료 또는 구조상 추론</li>
            <li>금액 미확인: 숫자를 만들지 않음 (0으로 처리하지 않음)</li>
          </ul>
        </Disclosure>
      </section>
    </div>
  );
}
