import type { NetNode } from "../types";

export const REL_LABEL: Record<string, string> = {
  FINANCING_PARTICIPATION: "차입 계약 참여 (대주 · 주선 · 에이전트)",
  PROJECT_LOAN: "프로젝트 대출 (대주)",
  CREDIT_ENHANCEMENT: "신용보강 · 인수확약 · 보증",
  ARRANGER: "금융 주관 · 주선",
  REFINANCING_UNDERWRITE: "리파이낸싱 · 총액인수",
  EQUITY_SPONSOR: "스폰서 · 출자",
  EQUITY_INVESTMENT: "지분 투자",
  PREFERRED_EQUITY: "우선주 · 중순위 자본",
  EPC_CONTRACT: "시공(EPC) 계약",
  FACILITY_OPERATION: "위탁운영",
  TENANT_LEASE: "임차 · 임대료 현금흐름",
  ASSET_MANAGER: "자산운용",
  STRUCTURING_EQUITY: "구조화 · 에쿼티 주선",
  PARENT_SPV: "모회사 · PFV",
  COLLATERAL_AGENT: "담보 · 예치 관리",
  SUPPLIER: "공급 관계",
  INDIRECT_SUPPLY_CHAIN: "간접 공급망",
  CUSTOMER: "고객 계약",
  LESSOR: "데이터센터 임차",
  CAPACITY_BACKSTOP: "용량 매입 약정",
  STRATEGIC_PARTNERSHIP: "전략적 협력 · 기술 제휴",
  POWER_SUPPLY: "전력 · 전기 인프라",
  ABS_SPONSOR: "유동화 SPC 신용보강·매입약정",
  ABS_HOLDING: "유동화증권 보유",
  LIQUIDITY_COMMITMENT: "유동성·매입 확약",
  COMPLETION_GUARANTEE: "책임준공 확약",
  LOAN_GUARANTEE: "대출 보증",
  LEASE_GUARANTEE: "임대차 보증",
  DEBT_ASSUMPTION: "채무인수 약정",
  PRIORITY_BENEFICIARY: "우선수익권",
  SHARE_PLEDGE: "주식 질권",
  INSURANCE_PLEDGE: "보험금 질권",
  COLLATERAL_PROVIDED: "담보 제공",
  SHAREHOLDER_LOAN: "주주 대여금",
  CORPORATE_LOAN: "기업 대출",
  ACQUISITION_LOAN: "인수 대출",
  ASSET_SALE: "자산 매각",
  TRUST_SERVICES: "신탁 업무 (보유 노출 아님)",
  FINANCIAL_ADVISOR: "금융 자문 (보유 노출 아님)",
  FINANCING_ARRANGEMENT: "금융 주선 (보유 노출 아님)",
  PROJECT_SPV: "사업 SPC",
  PARENT_AFFILIATE: "계열 관계",
  EPC_AFFILIATE: "계열 시공",
  EPC_CANDIDATE: "시공 후보 (미확정)",
  EPC_OR_OPS_MANDATE: "시공·운영 위탁",
  SENIOR_SECURED_NOTES: "선순위 담보부 채권",
  REVOLVER: "리볼빙 한도",
  DEMAND_CHANNEL: "수요 경로 (가정)",
  EQUIPMENT_SUPPLY: "장비 공급",
  SECTOR_SUPPLY: "산업 공급 경로 (가정)",
  SECTOR_DEMAND: "산업 수요 경로 (가정)",
  FUNDING_MARKET: "자금시장 경로 (가정)",
  STRATEGIC_MOU: "전략 MOU",
  GPU_SUPPLY: "GPU 공급",
  HBM_SUPPLY: "HBM 공급",
};

/** Amount type labels — never treat Unknown as zero. */
export const AMOUNT_TYPE_KO: Record<string, string> = {
  institution_commitment: "기관별 약정/참여금액",
  facility_total_context: "시설·신디케이트 총액(맥락)",
  underwrite_commitment: "인수·총액인수 약정",
  credit_support_limit: "신용보강·매입확약 한도",
  guarantee_limit: "보증·채무인수 한도",
  equity_investment: "지분 출자",
  fund_commitment: "펀드·리츠 출자",
  construction_contract_value: "공사 도급액",
  lease_contract_value: "임차·위탁운영 계약액",
  outstanding_balance: "현재 잔액",
  actual_funding: "실인출·집행액",
};

export const FINANCING_STAGE_KO: Record<string, string> = {
  bridge: "브릿지론",
  main_pf: "본PF",
  operating_refinancing: "운영·리파이낸싱",
  securitization: "유동화(ABCP·ABSTB)",
  equity: "에쿼티",
  construction: "시공·책임준공",
  operations: "운영",
};

export const EVIDENCE_STATUS_KO: Record<string, string> = {
  "기사상 참여 확인": "기사상 참여 확인",
  "추진·협의 중": "추진·협의 중",
  "과거 참여": "과거 참여",
  "현재 잔액 미확인": "현재 잔액 미확인",
  "금액 미공개": "금액 미공개",
  "자료 상충": "자료 상충",
};

export const REL_EN: Record<string, string> = {
  FINANCING_PARTICIPATION: "Lender / Arranger", COLLATERAL_AGENT: "Collateral Agent", EQUITY_INVESTMENT: "Shareholder",
  SUPPLIER: "Supplier", INDIRECT_SUPPLY_CHAIN: "Indirect Supplier", CUSTOMER: "Customer", LESSOR: "Data Center Lessor",
  CAPACITY_BACKSTOP: "Capacity Backstop", STRATEGIC_PARTNERSHIP: "Strategic Partnership", POWER_SUPPLY: "Power / Electrical",
};

export const CHANNEL_LABEL: Record<string, string> = {
  financial: "금융 계약", equity: "지분", supply_chain: "공급망", customer: "고객 계약", facility: "데이터센터", contract: "기타 약정",
};

export const STATUS_LABEL: Record<string, string> = { VERIFIED: "VERIFIED", INFERRED: "INFERRED", ASSUMED: "ASSUMED", UNKNOWN: "UNKNOWN" };
export const STATUS_KO: Record<string, string> = {
  VERIFIED: "공식 공시 · 회사 발표로 확인", INFERRED: "공개자료 기반 추론 · 2차 출처", ASSUMED: "사용자 가정", UNKNOWN: "공개자료로 확인되지 않음",
};
export const REL_STATUS_KO = STATUS_KO;

export const GROUP_LABEL: Record<string, string> = {
  ai_infra: "AI 인프라", semiconductor: "반도체", server: "서버 · 네트워킹", customer: "클라우드 · 고객",
  financial: "금융기관", datacenter: "데이터센터 · 전력장비", project_finance: "프로젝트 · SPV",
  kr_construction: "KR 건설 · EPC", kr_trust: "KR 부동산신탁", kr_savings: "KR 저축은행",
  kr_cooperative: "KR 새마을금고 · 협동", kr_bank: "KR 은행", kr_securities: "KR 증권",
  kr_am: "KR 운용사 · 기관", kr_insurance: "KR 보험", kr_operator: "KR DC · 운영",
};

export const CATEGORY_KO: Record<string, string> = {
  computed: "계산값", assumed: "가정 기반 계산", relationship_only: "관계만 확인 · 정량 미산정", unconfirmed: "관계 미확인",
};
export const CATEGORY_CODE: Record<string, string> = { computed: "B", assumed: "C", relationship_only: "D", unconfirmed: "E" };

export const SIM_STATUS_KO: Record<string, string> = {
  normal: "이번 시나리오와 정량 경로 없음",
  shock_origin: "직접 노출 · 이자 민감도 계산",
  stress_normal: "정상 · 직접 노출 계산",
  stress_moderate: "중간 재무 스트레스",
  stress_high: "높은 재무 스트레스 · 균열",
  stress_critical: "심각 재무 압박 — 시나리오 추정",
  contract_party: "전달 채널 · 영향 미산정",
  assumed: "가정 기반 계산",
  potential: "잠재 간접 경로 · 미산정",
  insufficient: "데이터 부족 · 금액 미산정",
  secondary_contagion: "2차 전염 · 거래상대방 스트레스",
};

export const RELATION_KIND_KO: Record<string, string> = { origin: "네트워크 초점 기업", direct: "직접 연결 (1-hop)", indirect: "간접 연결", unconfirmed: "관계 미확인" };

/** USD million → "8억 4,000만 달러" */
export function korUsd(mn: number | null | undefined): string {
  if (mn === null || mn === undefined || Number.isNaN(mn)) return "—";
  const neg = mn < 0;
  const man = Math.round(Math.abs(mn) * 100); // 1 million USD = 100 × 10,000 USD
  const eok = Math.floor(man / 10000);
  const rest = man % 10000;
  let s = "";
  if (eok) s += `${eok.toLocaleString("ko-KR")}억`;
  if (rest) s += `${s ? " " : ""}${rest.toLocaleString("ko-KR")}만`;
  if (!s) s = "0";
  return `${neg ? "−" : ""}${s} 달러`;
}

/** kept for compact spots (tables): "$840M" */
export function usd(x: number | null | undefined): string {
  return korUsd(x);
}

export function pct(x: number | null | undefined, digits = 0): string {
  if (x === null || x === undefined) return "—";
  return `${(x * 100).toFixed(digits)}%`;
}

export function pts(x: number | null | undefined): string {
  if (x === null || x === undefined) return "—";
  return `${x.toFixed(2)}점`;
}

export function domainOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

export function nameOf(nodes: Map<string, NetNode>, id: string) {
  const n = nodes.get(id);
  if (!n) return id;
  const ko = (n.name_ko || "").trim();
  if (ko && /[가-힣]/.test(ko)) return ko;
  return n.name ?? id;
}

/** Korean subject particle 가/이 after a name (falls back to 가 for Latin endings). */
export function ga(name: string): string {
  const ch = name.charCodeAt(name.length - 1);
  if (ch >= 0xac00 && ch <= 0xd7a3) return (ch - 0xac00) % 28 ? "이" : "가";
  return "가";
}

export function fmtDateTime(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("ko-KR", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

/** USD million → terminal style "$840M" / "$1.90B" / "−$240M" (hover shows korUsd). */
export function usdM(mn: number | null | undefined): string {
  if (mn === null || mn === undefined || Number.isNaN(mn)) return "—";
  const a = Math.abs(mn);
  const s = a >= 1e6 ? `$${(a / 1e6).toFixed(2)}T` : a >= 1000 ? `$${(a / 1000).toFixed(2)}B` : a >= 1 ? `$${a.toLocaleString("en-US", { maximumFractionDigits: 1 })}M` : a === 0 ? "$0" : `$${(a * 1000).toFixed(0)}K`;
  return mn < 0 ? `−${s}` : s;
}

export const pctStr = (x: number | null | undefined, d = 2) => (x === null || x === undefined ? "—" : `${x.toFixed(d)}%`);
export const signed = (x: number, f: (v: number) => string) => (x > 0 ? "+" : "") + f(x);
