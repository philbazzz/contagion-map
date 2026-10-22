/**
 * Compact borrower (PFV / SPC) aggregation for progressive disclosure.
 * Does not mutate network data or shock math — display-only selectors.
 */
import type { NetEdge, NetNode, Network } from "../types";
import { displayName } from "../lib/displayName";
import { REL_LABEL } from "../lib/format";
import { amountFacts, CERTAINTY_SHORT } from "../lib/evidence";

/** Data as-of used when deciding past/current (set by buildBorrowerSummary). */
let TODAY = "9999-12-31";

export type BorrowerEdgeMode = "material" | "all" | "by_category";

export type InstCategoryId =
  | "securities"
  | "bank"
  | "insurance"
  | "savings"
  | "am"
  | "trust"
  | "cooperative"
  | "other_fin";

export const INST_CATEGORY_ORDER: InstCategoryId[] = [
  "securities", "bank", "insurance", "savings", "am", "trust", "cooperative", "other_fin",
];

export const INST_CATEGORY_LABEL: Record<InstCategoryId, string> = {
  securities: "증권사",
  bank: "은행",
  insurance: "보험사",
  savings: "저축은행",
  am: "자산운용사",
  trust: "신탁사",
  cooperative: "공제회·연기금",
  other_fin: "기타 금융기관",
};

const PAST = new Set([
  "repaid", "terminated", "historical", "withdrawn", "expired", "refinanced", "transferred",
  "FULLY_REPAID", "REFINANCED", "TRANSFERRED", "EXPIRED", "HISTORICAL_ONLY", "SUPERSEDED_BY_DART_AUDIT",
]);
const ARRANGE = new Set(["ARRANGER", "FINANCING_ARRANGEMENT", "UNDERWRITING_COMMITMENT"]);
const NON_EXPOSURE_AMT = new Set(["facility_total_context", "fee_paid", "underwrite_commitment"]);
const LOAN_REL = new Set([
  "PROJECT_LOAN", "ACQUISITION_LOAN", "CORPORATE_LOAN", "BRIDGE_LOAN", "DIRECT_LOAN",
  "MORTGAGE_LOAN", "PROJECT_FINANCE_LOAN", "FINANCING_PARTICIPATION",
]);
const FIN_REL = new Set([
  ...LOAN_REL,
  "EQUITY_INVESTMENT", "EQUITY_SPONSOR", "PREFERRED_EQUITY", "SHAREHOLDER_LOAN", "SUBORDINATED_INVESTMENT",
  "CREDIT_ENHANCEMENT", "COMPLETION_GUARANTEE", "DEBT_ASSUMPTION", "LOAN_GUARANTEE",
  "FINANCIAL_GUARANTEE", "LIQUIDITY_COMMITMENT", "REFINANCING_UNDERWRITE",
  "COLLATERAL_AGENT", "ASSET_MANAGER", "STRUCTURING_EQUITY",
]);

const FIN_GROUPS = new Set([
  "kr_bank", "kr_securities", "kr_insurance", "kr_savings", "kr_am", "kr_trust",
  "kr_cooperative", "financial", "project_finance",
]);

export type PfEdgeX = NetEdge & {
  exposure_status?: string;
  relationship_status?: string;
  amount_krw_eok?: number | null;
  amount_type?: string;
  project_id?: string;
  project_name?: string;
  financing_stage?: string;
  seniority?: string;
  facility_total_krw_eok?: number | null;
  source_url?: string;
  source_title?: string;
  source_date?: string;
  last_verified_date?: string;
  layer?: string;
  shock_eligible?: boolean;
};

export function isBorrowerNode(n: NetNode | null | undefined): boolean {
  if (!n) return false;
  return n.entity_type === "spv" || n.group === "project_finance";
}

export function institutionCategory(n: NetNode | null | undefined): InstCategoryId | null {
  if (!n) return null;
  switch (n.group) {
    case "kr_securities": return "securities";
    case "kr_bank":
    case "financial": return "bank";
    case "kr_insurance": return "insurance";
    case "kr_savings": return "savings";
    case "kr_am": return "am";
    case "kr_trust": return "trust";
    case "kr_cooperative": return "cooperative";
    default:
      if (FIN_GROUPS.has(n.group) && n.group !== "project_finance") return "other_fin";
      // Non-finance counterparties (EPC, operator) are excluded from lender tallies
      return null;
  }
}

export function isPastEdge(e: NetEdge): boolean {
  const x = e as PfEdgeX;
  const st = x.exposure_status || x.relationship_status || "";
  if (PAST.has(st) || PAST.has(st.toUpperCase())) return true;
  if (x.layer === "historical") return true;
  return false;
}

export function isArrangerOnly(e: NetEdge): boolean {
  return ARRANGE.has(e.relationship_type);
}

/** Amount eligible as current, confirmed exposure (never facility total / underwrite / fee / estimate). */
export function exposureEok(e: NetEdge): number | null {
  const x = e as PfEdgeX;
  if (isPastEdge(e) || isArrangerOnly(e)) return null;
  if (NON_EXPOSURE_AMT.has(x.amount_type || "")) return null;
  const f = amountFacts(e, TODAY);
  if (!f.summable || f.unit !== "억원") return null;
  return f.value;
}

const OUTSTANDING_KINDS = new Set(["outstanding_principal", "outstanding_principal_gross", "outstanding", "outstanding_balance"]);

export function exposureStatusLabel(e: NetEdge): string {
  const x = e as PfEdgeX;
  if (isPastEdge(e)) {
    const st = (x.exposure_status || x.relationship_status || "HISTORICAL").toUpperCase();
    if (st.includes("REPAID")) return "전액상환";
    return "과거·종료";
  }
  if (isArrangerOnly(e)) return "주선·인수(비보유)";
  if (NON_EXPOSURE_AMT.has(x.amount_type || "")) return "시설총액·약정 맥락";
  const f = amountFacts(e, TODAY);
  if (f.current === "matured_unconfirmed") return "만기 경과·상환 미확인";
  if (f.value !== null && f.certainty !== "confirmed") return "금액 확인 필요";
  if (x.exposure_status === "ACTIVE_CONFIRMED" || exposureEok(e) != null) return "확인됨";
  if (x.exposure_status === "ACTIVE_AMOUNT_UNKNOWN") return "잔액미확인";
  if (e.source_status === "VERIFIED") return "참여확인·잔액미확인";
  return "미확인";
}

function counterpartyId(borrowerId: string, e: NetEdge): string {
  return e.source === borrowerId ? e.target : e.source;
}

function isFinanceLink(borrowerId: string, e: NetEdge, nodeMap: Map<string, NetNode>): boolean {
  if (e.source !== borrowerId && e.target !== borrowerId) return false;
  if (FIN_REL.has(e.relationship_type) || e.impact_channel === "financial" || e.impact_channel === "equity") {
    const other = nodeMap.get(counterpartyId(borrowerId, e));
    // Finance rel always counts; construction EPC etc. only if financial channel
    if (FIN_REL.has(e.relationship_type)) return true;
    if (other && institutionCategory(other)) return true;
    return e.impact_channel === "financial" || e.impact_channel === "equity";
  }
  const other = nodeMap.get(counterpartyId(borrowerId, e));
  return !!other && institutionCategory(other) != null;
}

export interface InstFacilityRow {
  edgeId: string;
  institutionId: string;
  institutionName: string;
  category: InstCategoryId;
  relType: string;
  relLabel: string;
  balanceLabel: string;
  balanceEok: number | null;
  statusLabel: string;
  past: boolean;
  arranger: boolean;
  projectId?: string;
  projectName?: string;
  stage?: string;
  seniority?: string;
  facilityTotalEok?: number | null;
  sourceUrl?: string;
  sourceTitle?: string;
  sourceDate?: string;
  verifiedDate?: string;
  amountNote?: string;
}

export interface CategoryBucket {
  id: InstCategoryId;
  label: string;
  institutionCount: number;
  institutions: {
    id: string;
    name: string;
    facilities: InstFacilityRow[];
    /** Sum of known exposure eok only — never invents zeros for UNKNOWN. */
    knownEok: number | null;
    unknownFacilities: number;
  }[];
}

export interface BorrowerSummary {
  borrowerId: string;
  borrowerName: string;
  institutionCount: number;
  visibleInstitutionCount: number;
  knownLoanEok: number | null;
  /** As-of date of the summed balances (only same-date amounts are added). */
  knownLoanAsOf: string | null;
  knownLoanCount: number;
  /** Confirmed balances with a different as-of date — shown separately, not added. */
  otherDateLoanCount: number;
  /** Confirmed loan amounts that are commitments/limits rather than outstanding balances. */
  nonOutstandingLoanCount: number;
  unknownLoanFacilities: number;
  categoryCounts: { id: InstCategoryId; label: string; count: number }[];
  categories: CategoryBucket[];
  facilityCount: number;
  activeFacilityCount: number;
  /** Top material edges for map highlight (max 5). */
  materialEdgeIds: string[];
  /** Ranking basis shown in UI when amounts incomplete. */
  materialRankingNote: string;
  allFinanceEdgeIds: string[];
  rows: InstFacilityRow[];
}

function balanceLabel(e: NetEdge): string {
  const f = amountFacts(e, TODAY);
  if (isPastEdge(e)) {
    const st = ((e as PfEdgeX).exposure_status || "").toUpperCase();
    if (st.includes("REPAID")) return "상환 완료";
    if (st.includes("SUPERSEDED")) return "최신 공시로 대체";
    return "과거·종료";
  }
  if (isArrangerOnly(e) || NON_EXPOSURE_AMT.has((e as PfEdgeX).amount_type || "")) {
    return "해당 없음 (주선·시설총액)";
  }
  if (f.value !== null && f.unit === "억원") {
    const base = `${Math.round(f.value * 100) / 100 >= 100 ? Math.round(f.value).toLocaleString("ko-KR") : (Math.round(f.value * 100) / 100).toLocaleString("ko-KR")}억 원`;
    return f.certainty === "confirmed" ? `${base} · ${f.kindKo}` : `${base} (${CERTAINTY_SHORT[f.certainty]}) · ${f.kindKo}`;
  }
  const note = e.amount_note || "";
  if (note.includes("미공개") || note.includes("미공시") || note.includes("미기재")) return "미확인";
  if (e.amount_usd_m != null) return e.amount_note || `≈ $${e.amount_usd_m}M`;
  return "미확인";
}

function toRow(borrowerId: string, e: NetEdge, nodeMap: Map<string, NetNode>): InstFacilityRow | null {
  const iid = counterpartyId(borrowerId, e);
  const inst = nodeMap.get(iid);
  const cat = institutionCategory(inst);
  if (!cat) return null;
  const x = e as PfEdgeX;
  return {
    edgeId: e.id,
    institutionId: iid,
    institutionName: inst ? displayName(inst) : iid,
    category: cat,
    relType: e.relationship_type,
    relLabel: REL_LABEL[e.relationship_type] || e.label || e.relationship_type,
    balanceLabel: balanceLabel(e),
    balanceEok: exposureEok(e),
    statusLabel: exposureStatusLabel(e),
    past: isPastEdge(e),
    arranger: isArrangerOnly(e),
    projectId: x.project_id,
    projectName: x.project_name,
    stage: x.financing_stage,
    seniority: x.seniority,
    facilityTotalEok: x.facility_total_krw_eok ?? null,
    sourceUrl: x.source_url,
    sourceTitle: x.source_title,
    sourceDate: x.source_date,
    verifiedDate: x.last_verified_date || x.source_date,
    amountNote: e.amount_note,
  };
}

/** Prefer verified exposure amounts; never invent ranking when all unknown. */
export function pickMaterialEdges(
  rows: InstFacilityRow[],
  preferEdgeIds?: string[],
  limit = 5,
): { ids: string[]; note: string } {
  const active = rows.filter((r) => !r.past && !r.arranger);
  if (preferEdgeIds?.length) {
    const prefer = preferEdgeIds.filter((id) => active.some((r) => r.edgeId === id));
    if (prefer.length) {
      return {
        ids: prefer.slice(0, limit),
        note: "쇼크 영향 시설 우선 · 상위 연결만 강조",
      };
    }
  }
  const withAmt = active.filter((r) => r.balanceEok != null).sort((a, b) => (b.balanceEok || 0) - (a.balanceEok || 0));
  if (withAmt.length >= 1) {
    return {
      ids: withAmt.slice(0, limit).map((r) => r.edgeId),
      note: "확인된 잔액 기준 상위 연결",
    };
  }
  // Alternative ordering — clearly labeled, no manufactured amounts
  const verified = active.filter((r) => r.statusLabel.includes("확인"));
  const pool = (verified.length ? verified : active).slice().sort((a, b) => {
    const loanA = LOAN_REL.has(a.relType) ? 0 : 1;
    const loanB = LOAN_REL.has(b.relType) ? 0 : 1;
    if (loanA !== loanB) return loanA - loanB;
    return a.institutionName.localeCompare(b.institutionName, "ko");
  });
  return {
    ids: pool.slice(0, limit).map((r) => r.edgeId),
    note: verified.length
      ? "잔액 미확인 · 대출관계·기관명 순 (금액 순위 아님)"
      : "잔액 미확인 · 관계유형·기관명 순 (금액 순위 아님)",
  };
}

export function buildBorrowerSummary(
  borrowerId: string,
  net: Network,
  opts?: {
    hiddenGroups?: Set<string> | string[];
    preferEdgeIds?: string[];
  },
): BorrowerSummary | null {
  TODAY = net.meta?.as_of || TODAY;
  const node = net.nodes.find((n) => n.id === borrowerId);
  if (!node || !isBorrowerNode(node)) return null;

  const nodeMap = new Map(net.nodes.map((n) => [n.id, n]));
  const hidden = opts?.hiddenGroups
    ? (opts.hiddenGroups instanceof Set ? opts.hiddenGroups : new Set(opts.hiddenGroups))
    : new Set<string>();

  const financeEdges = net.edges.filter((e) => isFinanceLink(borrowerId, e, nodeMap));
  const rows: InstFacilityRow[] = [];
  for (const e of financeEdges) {
    const row = toRow(borrowerId, e, nodeMap);
    if (row) rows.push(row);
  }

  // Unique institutions (never double-count across tranches)
  const byInst = new Map<string, InstFacilityRow[]>();
  for (const r of rows) {
    if (!byInst.has(r.institutionId)) byInst.set(r.institutionId, []);
    byInst.get(r.institutionId)!.push(r);
  }

  const categories: CategoryBucket[] = [];
  for (const cid of INST_CATEGORY_ORDER) {
    const instIds = [...byInst.keys()].filter((id) => {
      const first = byInst.get(id)![0];
      return first.category === cid;
    });
    if (!instIds.length) continue;
    const institutions = instIds
      .map((id) => {
        const facilities = byInst.get(id)!;
        let known = 0;
        let knownAny = false;
        let unknown = 0;
        for (const f of facilities) {
          if (f.past || f.arranger) continue;
          if (f.balanceEok != null) { known += f.balanceEok; knownAny = true; }
          else if (!f.arranger) unknown += 1;
        }
        return {
          id,
          name: facilities[0].institutionName,
          facilities,
          knownEok: knownAny ? known : null,
          unknownFacilities: unknown,
        };
      })
      .sort((a, b) => a.name.localeCompare(b.name, "ko"));
    categories.push({
      id: cid,
      label: INST_CATEGORY_LABEL[cid],
      institutionCount: institutions.length,
      institutions,
    });
  }

  // Current outstanding loan balance — confirmed amounts of the same kind and the same as-of date only.
  // Commitments, estimates, facility totals, arranger roles and repaid/superseded records are kept out.
  const byAsOf = new Map<string, { sum: number; n: number }>();
  let loanUnknown = 0;
  let loanOther = 0;
  for (const r of rows) {
    if (r.past || r.arranger) continue;
    if (!LOAN_REL.has(r.relType)) continue;
    const e = net.edges.find((x) => x.id === r.edgeId)!;
    const f = amountFacts(e, TODAY);
    if (r.balanceEok == null) { loanUnknown += 1; continue; }
    if (!OUTSTANDING_KINDS.has(f.kind)) { loanOther += 1; continue; }
    const k = f.asOf || "기준일 미기재";
    const cur = byAsOf.get(k) || { sum: 0, n: 0 };
    cur.sum += r.balanceEok; cur.n += 1;
    byAsOf.set(k, cur);
  }
  const groups = [...byAsOf.entries()].sort((a, b) => b[1].n - a[1].n || b[0].localeCompare(a[0]));
  const main = groups[0];
  const loanKnown = main ? main[1].n : 0;
  const loanEok = main ? main[1].sum : 0;

  const material = pickMaterialEdges(rows, opts?.preferEdgeIds, 5);
  const activeRows = rows.filter((r) => !r.past && !r.arranger);
  const visibleInst = [...byInst.keys()].filter((id) => {
    const g = nodeMap.get(id)?.group;
    return g ? !hidden.has(g) : true;
  }).length;

  return {
    borrowerId,
    borrowerName: displayName(node),
    institutionCount: byInst.size,
    visibleInstitutionCount: visibleInst,
    knownLoanEok: loanKnown ? loanEok : null,
    knownLoanAsOf: main ? main[0] : null,
    knownLoanCount: loanKnown,
    otherDateLoanCount: groups.slice(1).reduce((s2, g) => s2 + g[1].n, 0),
    nonOutstandingLoanCount: loanOther,
    unknownLoanFacilities: loanUnknown,
    categoryCounts: categories.map((c) => ({ id: c.id, label: c.label, count: c.institutionCount })),
    categories,
    facilityCount: rows.length,
    activeFacilityCount: activeRows.length,
    materialEdgeIds: material.ids,
    materialRankingNote: material.note,
    allFinanceEdgeIds: rows.map((r) => r.edgeId),
    rows,
  };
}

/** Map highlight payload for a borrower given edge mode. */
export function borrowerHighlight(
  summary: BorrowerSummary,
  mode: BorrowerEdgeMode,
  categoryId?: InstCategoryId | null,
): { nodes: string[]; edges: string[] } {
  let edgeIds: string[];
  if (mode === "all") {
    edgeIds = summary.rows.filter((r) => !r.past).map((r) => r.edgeId);
  } else if (mode === "by_category" && categoryId) {
    edgeIds = summary.rows.filter((r) => r.category === categoryId && !r.past).map((r) => r.edgeId);
  } else {
    edgeIds = summary.materialEdgeIds;
  }
  const nodes = new Set<string>([summary.borrowerId]);
  for (const r of summary.rows) {
    if (edgeIds.includes(r.edgeId)) nodes.add(r.institutionId);
  }
  // Keep other counterparties on graph but not in highlight path → Universe dims them
  return { nodes: [...nodes], edges: edgeIds };
}
