import type { CoreWeaveDistress, PfShockForm } from "./types";

export type { CoreWeaveDistress };

export const defaultPfShockForm = (): PfShockForm => ({
  coreweaveDistress: "normal",
  rateBp: 0,
  krRateBp: 0,
  krRateLinkPct: 0,
  gpuRentPct: 0,
  hyperscalerCapexPct: 0,
  restrictNewFinancing: false,
  horizonMonths: 12,
  gpuOperatorMarginPassThrough: 0.35,
  capexDemandElasticity: 0.5,
  /** Explicit ASSUMED KR funding-market pass-through from CoreWeave distress (0–1). */
  cwKrFundingPassThrough: 0.25,
  showUsKoreaOnly: false,
  showKoreanPfOnly: false,
  includeHistoricalRelationships: false,
  exposureFilter: "confirmed_dc",
});

export const RATE_PRESETS = [0, 100, 200, 300, 500] as const;
export const GPU_PRESETS = [0, -10, -20, -30, -40, -50] as const;
export const CAPEX_PRESETS = [0, -10, -20, -30, -40, -50] as const;

export const CW_DISTRESS: { id: CoreWeaveDistress; label: string }[] = [
  { id: "normal", label: "정상" },
  { id: "moderate", label: "중간 스트레스" },
  { id: "severe_liquidity", label: "심각 유동성" },
  { id: "payment_default", label: "지급불이행(모형)" },
  { id: "insolvency", label: "회생·파산(모형)" },
];

export const PF_CLASSES: { id: string; label: string; groups: string[] }[] = [
  { id: "project_finance", label: "PFV · SPC 법인", groups: ["project_finance"] },
  { id: "ai_infra", label: "US AI 인프라", groups: ["ai_infra"] },
  { id: "customer", label: "하이퍼스케일러", groups: ["customer"] },
  { id: "kr_operator", label: "KR CSP · 운영", groups: ["kr_operator", "datacenter"] },
  { id: "kr_construction", label: "KR 건설 · PM/CM", groups: ["kr_construction"] },
  { id: "kr_trust", label: "KR 부동산신탁", groups: ["kr_trust"] },
  { id: "kr_savings", label: "KR 저축은행", groups: ["kr_savings"] },
  { id: "kr_cooperative", label: "KR 새마을금고 · 공제", groups: ["kr_cooperative"] },
  { id: "kr_bank", label: "KR 은행 · 캐피탈", groups: ["kr_bank", "financial"] },
  { id: "kr_securities", label: "KR 증권", groups: ["kr_securities"] },
  { id: "kr_insurance", label: "KR 보험", groups: ["kr_insurance"] },
  { id: "kr_am", label: "KR 운용사 · 리츠 · 연기금", groups: ["kr_am"] },
  { id: "semiconductor", label: "반도체 (연계)", groups: ["semiconductor"] },
];

/** Institution-type filters for finance-first AI DC PF view. */
export const PF_INSTITUTION_FILTERS: { id: string; label: string; groups: string[] }[] = [
  { id: "all", label: "전체 기관유형", groups: [] },
  { id: "construction", label: "건설", groups: ["kr_construction"] },
  { id: "securities", label: "증권", groups: ["kr_securities"] },
  { id: "insurance", label: "보험", groups: ["kr_insurance"] },
  { id: "bank", label: "은행·캐피탈", groups: ["kr_bank", "financial"] },
  { id: "mutual_aid", label: "공제·협동", groups: ["kr_cooperative"] },
  { id: "pension_am", label: "연기금·운용사·리츠", groups: ["kr_am"] },
  { id: "savings", label: "저축은행", groups: ["kr_savings"] },
  { id: "trust", label: "신탁", groups: ["kr_trust"] },
  { id: "spv", label: "PFV·SPC", groups: ["project_finance"] },
  { id: "operator", label: "운영·임차", groups: ["kr_operator", "datacenter"] },
];

/** Financing-stage filters (edge metadata). */
export const PF_STAGE_FILTERS: { id: string; label: string; stages: string[] }[] = [
  { id: "all", label: "전체 금융단계", stages: [] },
  { id: "bridge", label: "브릿지", stages: ["bridge"] },
  { id: "main_pf", label: "본PF", stages: ["main_pf"] },
  { id: "refi", label: "운영·리파이낸싱", stages: ["operating_refinancing"] },
  { id: "sec", label: "유동화", stages: ["securitization"] },
  { id: "equity", label: "에쿼티", stages: ["equity"] },
];

/** Instrument / path filters (edge metadata). */
export const PF_INSTRUMENT_FILTERS: { id: string; label: string; match: string[] }[] = [
  { id: "all", label: "전체 경로", match: [] },
  { id: "direct_loan", label: "직접 대출", match: ["PROJECT_LOAN"] },
  { id: "fund_equity", label: "펀드·지분", match: ["EQUITY_INVESTMENT", "EQUITY_SPONSOR", "PREFERRED_EQUITY"] },
  { id: "securitization", label: "유동화", match: ["CREDIT_ENHANCEMENT"] },
  { id: "credit_support", label: "신용보강·보증", match: ["CREDIT_ENHANCEMENT", "REFINANCING_UNDERWRITE"] },
  { id: "arranger", label: "주관·인수", match: ["ARRANGER", "REFINANCING_UNDERWRITE"] },
];

/** Role attribute filters (not map nodes). */
export const PF_ROLE_FILTERS: { id: string; label: string; match: string[] }[] = [
  { id: "all", label: "전체 역할", match: [] },
  { id: "csp", label: "CSP", match: ["csp", "cloud"] },
  { id: "developer", label: "개발·시행", match: ["developer", "developer_vehicle", "spv", "borrower"] },
  { id: "operator", label: "운영사", match: ["operator", "colocation", "telecom"] },
  { id: "pm_cm", label: "PM/CM", match: ["pm_cm", "construction_management", "design", "development_management", "property_management"] },
  { id: "contractor", label: "시공사", match: ["contractor", "epc", "engineering", "completion_undertaking"] },
  { id: "trustee", label: "신탁", match: ["trust", "trustee", "re trust"] },
  { id: "lender", label: "대주·금융", match: ["lender", "senior_lender", "mezz_lender", "arranger", "bank", "capital", "insurer"] },
  { id: "securities", label: "증권사", match: ["securities", "underwrite", "credit_support"] },
  { id: "mutual_aid", label: "공제회", match: ["mutual_aid", "cooperative"] },
  { id: "infra", label: "장비·인프라", match: ["power", "cooling", "infrastructure", "equipment"] },
  { id: "am_invest", label: "운용사·투자", match: ["asset_manager", "investment", "pe", "sponsor", "equity_investor", "reit"] },
  { id: "isolated", label: "연결관계 확인 필요", match: ["__connection_pending__"] },
];

/** Evidence status filters for PF network list (not map category nodes). */
export const PF_EVIDENCE_FILTERS: { id: string; label: string }[] = [
  { id: "all", label: "근거 전체" },
  { id: "verified", label: "기사상 참여 확인" },
  { id: "inferred", label: "추론(INFERRED)" },
  { id: "pending", label: "연결관계 확인 필요" },
];

export const PF_AMOUNT_FILTERS: { id: string; label: string }[] = [
  { id: "all", label: "금액 전체" },
  { id: "disclosed", label: "금액 공개" },
  { id: "undisclosed", label: "금액 미공개" },
];

export const PF_DIRECTNESS_FILTERS: { id: string; label: string }[] = [
  { id: "all", label: "직접·간접" },
  { id: "direct", label: "직접 참여" },
  { id: "indirect", label: "간접 참여" },
];
