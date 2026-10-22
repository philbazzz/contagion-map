/**
 * Evidence model for every amount / relationship shown on screen.
 * One function decides what a number is (kind), how sure we are (certainty), whether the
 * deal is current, and where it comes from — summaries, tables, tooltips and the map all
 * read it, so they cannot disagree.
 */
import type { NetEdge } from "../types";
import { AMOUNT_KIND_KO, EXPOSURE_STATUS_KO, RELATIONSHIP_STATUS_KO, eok } from "./labels";

type X = NetEdge & {
  amount_krw_eok?: number | null; amount_type?: string | null; amount_unit?: string | null; amount_as_of?: string | null;
  exposure_status?: string; relationship_status?: string; exposure_kind?: string | null; maturity?: string | null;
  source_url?: string | null; source_title?: string | null; source_date?: string | null; rcept_no?: string | null;
  dart_receipt_number?: string | null; period_basis?: string | null; source_publisher?: string | null;
  contingent_obligation?: boolean; evidence_quote?: string | null; transaction_date?: string | null;
};

export type Certainty = "confirmed" | "estimated" | "inferred" | "assumed" | "unknown";
export type Currentness = "current" | "matured_unconfirmed" | "past" | "superseded" | "role_only";

export const CERTAINTY_KO: Record<Certainty, string> = {
  confirmed: "확인된 금액",
  estimated: "추정 · 확인 필요",
  inferred: "공개자료 추론",
  assumed: "사용자 가정",
  unknown: "금액 미확인",
};
export const CERTAINTY_SHORT: Record<Certainty, string> = {
  confirmed: "확인", estimated: "추정", inferred: "추론", assumed: "가정", unknown: "미확인",
};
export const CURRENT_KO: Record<Currentness, string> = {
  current: "현재 거래",
  matured_unconfirmed: "만기 경과 · 상환 미확인",
  past: "상환·종료(현재 노출 제외)",
  superseded: "최신 공시로 대체됨",
  role_only: "역할만(보유 노출 아님)",
};

const PAST_STATUS = new Set(["HISTORICAL_ONLY", "FULLY_REPAID", "REFINANCED", "TRANSFERRED", "EXPIRED", "SECURITIZED"]);
const PAST_REL = new Set(["repaid", "historical", "terminated", "withdrawn", "expired", "refinanced", "transferred"]);
const PAST_KIND = new Set(["historical_outstanding", "historical_commitment", "outstanding_principal_prior_period"]);
/** Roles that do not mean the institution holds the money. */
export const ROLE_ONLY_TYPES = new Set(["ARRANGER", "FINANCING_ARRANGEMENT", "FINANCIAL_ADVISOR", "TRUST_SERVICES", "ASSET_MANAGER"]);
/** Kinds that are context, not a position (never summed into exposure). */
const CONTEXT_KINDS = new Set(["facility_total_context", "underwrite_commitment", "fee_paid", "ownership_pct", "asset_sale_price"]);

export interface AmountFacts {
  value: number | null;       // in `unit`
  unit: "억원" | "USD m" | null;
  kind: string;               // normalized amount kind code
  kindKo: string;
  certainty: Certainty;
  certaintyReason: string;
  current: Currentness;
  asOf: string | null;
  contingent: boolean;
  /** Eligible to be added into a "confirmed exposure" total. */
  summable: boolean;
  display: string;            // e.g. "280억 원 (추정 · 확인 필요)"
}

export function amountKind(e: NetEdge): string {
  const x = e as X;
  const note = `${e.amount_note || ""} ${x.evidence_quote || ""}`;
  let k = x.amount_type || "";
  if (!k) {
    if (x.exposure_kind === "loan_principal_outstanding") k = "outstanding_principal";
    else if (x.exposure_kind === "purchase_commitment") k = "purchase_commitment";
    else if (x.exposure_kind === "facility_total_context") k = "facility_total_context";
    else if (e.relationship_type === "EQUITY_INVESTMENT") k = "equity_investment";
    else k = "unspecified";
  }
  // The data sometimes labels a book value as "paid-in" — the source text decides.
  if (/^equity_/.test(k) && /장부가/.test(note)) k = "equity_book_value";
  return k;
}

export function currentness(e: NetEdge, today: string): Currentness {
  const x = e as X;
  const st = (x.exposure_status || "").toUpperCase();
  if (st === "SUPERSEDED_BY_DART_AUDIT") return "superseded";
  if (PAST_STATUS.has(st) || PAST_REL.has((x.relationship_status || "").toLowerCase()) || PAST_KIND.has(x.amount_type || "")) return "past";
  if (ROLE_ONLY_TYPES.has(e.relationship_type)) return "role_only";
  const mat = x.maturity;
  if (mat && /^\d{4}-\d{2}/.test(mat) && mat.slice(0, 10) < today) return "matured_unconfirmed";
  return "current";
}

export function amountFacts(e: NetEdge, today: string): AmountFacts {
  const x = e as X;
  const note = `${e.amount_note || ""}`;
  const krw = x.amount_krw_eok;
  const usd = e.amount_usd_m;
  const value = krw != null && Number.isFinite(krw) ? krw : usd != null && Number.isFinite(usd) ? usd : null;
  const unit: AmountFacts["unit"] = krw != null && Number.isFinite(krw) ? "억원" : usd != null && Number.isFinite(usd) ? "USD m" : null;
  const kind = amountKind(e);
  const kindKo = AMOUNT_KIND_KO[kind] || (kind === "unspecified" ? "금액유형 미기재" : kind);
  let certainty: Certainty;
  let certaintyReason: string;
  if (value === null) { certainty = "unknown"; certaintyReason = "원문에서 금액이 확인되지 않음"; }
  else if (/추정/.test(note)) { certainty = "estimated"; certaintyReason = "원문 금액 또는 단위가 추정으로 기재됨"; }
  else if ((x.exposure_status || "").toUpperCase() === "ACTIVE_AMOUNT_UNKNOWN") { certainty = "estimated"; certaintyReason = "현재 금액 확인이 필요한 거래로 분류됨"; }
  else if (e.source_status === "ASSUMED") { certainty = "assumed"; certaintyReason = "사용자·모형 가정값"; }
  else if (e.source_status === "INFERRED") { certainty = "inferred"; certaintyReason = "2차 자료 또는 구조상 추론"; }
  else if (e.source_status === "VERIFIED") { certainty = "confirmed"; certaintyReason = "공시·회사 발표로 확인"; }
  else { certainty = "unknown"; certaintyReason = "근거 상태 미확인"; }
  const current = currentness(e, today);
  const asOf = x.amount_as_of || x.transaction_date || x.source_date || null;
  const contingent = !!x.contingent_obligation;
  const summable = certainty === "confirmed" && current === "current" && !CONTEXT_KINDS.has(kind) && value !== null;
  const base = value === null ? "금액 미확인" : unit === "억원" ? eok(value) : `$${value.toLocaleString("en-US")}M`;
  const display = value === null ? base : certainty === "confirmed" ? base : `${base} (${CERTAINTY_SHORT[certainty]})`;
  return { value, unit, kind, kindKo, certainty, certaintyReason, current, asOf, contingent, summable, display };
}

// ---------------------------------------------------------------- sources

export interface SourceRef {
  title: string;
  url: string | null;
  date: string | null;
  filing: string | null;
  publisher: string | null;
  status: "linked" | "homepage_only" | "missing";
}

/** A bare domain / homepage is not evidence for a specific claim. */
export function isHomepageUrl(u: string | null | undefined): boolean {
  if (!u) return true;
  try {
    const p = new URL(u);
    return (p.pathname === "" || p.pathname === "/") && !p.search;
  } catch { return true; }
}

export function sourceRef(e: NetEdge): SourceRef {
  const x = e as X;
  const url = x.source_url || null;
  const status: SourceRef["status"] = !url ? "missing" : isHomepageUrl(url) ? "homepage_only" : "linked";
  return {
    title: x.source_title || (status === "missing" ? "원문 연결 미확보" : "출처"),
    url: status === "linked" ? url : null,
    date: x.source_date || null,
    filing: x.rcept_no || x.dart_receipt_number || null,
    publisher: x.source_publisher || null,
    status,
  };
}

// ---------------------------------------------------------------- exposure summary

export interface KindSummary {
  kind: string;
  kindKo: string;
  /** Confirmed, current, de-duplicated amounts, split by as-of date (only same-date amounts are added). */
  confirmed: { asOf: string | null; sum: number; count: number; unit: string }[];
  estimated: { edgeId: string; facts: AmountFacts }[];
  unknown: number;
}

export interface ExposureSummary {
  kinds: KindSummary[];
  past: number;
  superseded: number;
  roleOnly: number;
  maturedUnconfirmed: number;
  currentDeals: number;
}

/** Group a company's edges into an exposure summary that never mixes kinds, dates or certainty levels. */
export function summarizeExposure(edges: NetEdge[], companyId: string, today: string): ExposureSummary {
  const kinds = new Map<string, KindSummary>();
  const seen = new Set<string>();
  let past = 0, superseded = 0, roleOnly = 0, matured = 0, currentDeals = 0;
  for (const e of edges) {
    const f = amountFacts(e, today);
    if (f.current === "past") { past += 1; continue; }
    if (f.current === "superseded") { superseded += 1; continue; }
    if (f.current === "role_only") { roleOnly += 1; continue; }
    if (f.current === "matured_unconfirmed") matured += 1;
    currentDeals += 1;
    if (CONTEXT_KINDS.has(f.kind) || f.kind === "unspecified" && f.value === null) {
      if (f.kind === "unspecified") {
        const k = kinds.get("unspecified") || { kind: "unspecified", kindKo: "금액유형 미기재", confirmed: [], estimated: [], unknown: 0 };
        k.unknown += 1; kinds.set("unspecified", k);
      }
      continue;
    }
    const k = kinds.get(f.kind) || { kind: f.kind, kindKo: f.kindKo, confirmed: [], estimated: [], unknown: 0 };
    kinds.set(f.kind, k);
    if (f.value === null) { k.unknown += 1; continue; }
    if (!f.summable) { k.estimated.push({ edgeId: e.id, facts: f }); continue; }
    const other = e.source === companyId ? e.target : e.source;
    const x = e as X;
    const key = [other, f.kind, f.value, f.asOf, x.rcept_no || x.source_url || ""].join("|");
    if (seen.has(key)) continue; // same filing line recorded twice
    seen.add(key);
    let bucket = k.confirmed.find((b) => b.asOf === f.asOf && b.unit === f.unit);
    if (!bucket) { bucket = { asOf: f.asOf, sum: 0, count: 0, unit: f.unit || "" }; k.confirmed.push(bucket); }
    bucket.sum += f.value;
    bucket.count += 1;
  }
  return {
    kinds: [...kinds.values()].sort((a, b) => kindOrder(a.kind) - kindOrder(b.kind)),
    past, superseded, roleOnly, maturedUnconfirmed: matured, currentDeals,
  };
}

const ORDER = [
  "outstanding_principal", "outstanding_principal_gross", "outstanding", "institution_commitment", "undrawn_commitment",
  "equity_paid_in", "equity_book_value", "equity_par_value", "equity_subscription", "equity_investment", "fund_commitment",
  "guarantee_limit", "guarantee_amount", "credit_support_limit", "purchase_commitment", "priority_beneficiary_limit",
  "pledge_limit", "collateral_limit", "construction_contract_value", "lease_contract_value",
];
function kindOrder(k: string) { const i = ORDER.indexOf(k); return i < 0 ? 99 : i; }

export function fmtSum(v: number, unit: string): string {
  return unit === "억원" ? eok(v) : `$${Math.round(v).toLocaleString("en-US")}M`;
}

export const statusKo = (code?: string | null) =>
  !code ? "—" : EXPOSURE_STATUS_KO[code] || EXPOSURE_STATUS_KO[code.toUpperCase()] || RELATIONSHIP_STATUS_KO[code] || code;
