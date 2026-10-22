/**
 * Single place that turns internal data / engine codes into user-facing Korean.
 * Codes stay in the data and in dev diagnostics; screens call ko()/koOf() so the same
 * code always reads the same way everywhere.
 */

/** Amount kinds — what a number actually is. Never mix kinds in one total. */
export const AMOUNT_KIND_KO: Record<string, string> = {
  outstanding_principal: "대출 실행잔액",
  outstanding_principal_gross: "대출 실행잔액(총액)",
  outstanding_principal_prior_period: "대출 잔액(전기말)",
  outstanding: "대출 잔액",
  outstanding_balance: "대출 잔액",
  historical_outstanding: "과거 잔액",
  historical_commitment: "과거 약정",
  institution_commitment: "기관별 약정액",
  undrawn_commitment: "미사용 약정",
  facility_limit: "한도 약정",
  facility_total_context: "시설·대주단 총액(맥락)",
  underwrite_commitment: "인수·총액인수 약정",
  credit_support_limit: "신용보강 한도",
  guarantee_limit: "보증 한도",
  guarantee_amount: "보증 금액",
  purchase_commitment: "매입확약",
  priority_beneficiary_limit: "우선수익권 한도",
  pledge_limit: "질권 설정 한도",
  collateral_limit: "담보 설정 한도",
  equity_paid_in: "지분 납입금액",
  equity_book_value: "지분 장부가액",
  equity_carrying: "지분 장부가액",
  equity_par_value: "지분 액면금액",
  equity_subscription: "지분 청약·인수금액",
  equity_investment: "지분 출자",
  ownership_pct: "지분율",
  fund_commitment: "펀드·리츠 출자약정",
  construction_contract_value: "공사 도급액",
  construction_billing_period: "기간 공사대금",
  lease_contract_value: "임차·운영 계약액",
  asset_sale_price: "자산 매각가",
  fee_paid: "수수료",
  actual_funding: "실인출·집행액",
};

/** Current-ness of a relationship / exposure (data field exposure_status / relationship_status). */
export const EXPOSURE_STATUS_KO: Record<string, string> = {
  ACTIVE_CONFIRMED: "현재 거래 · 금액 확인",
  ACTIVE_AMOUNT_UNKNOWN: "현재 거래 · 금액 확인 필요",
  HISTORICAL_ONLY: "과거 거래",
  FULLY_REPAID: "상환 완료",
  REFINANCED: "차환 완료",
  TRANSFERRED: "양도 완료",
  EXPIRED: "종료",
  SECURITIZED: "유동화 이전",
  UNVERIFIED: "미검증",
  SUPERSEDED_BY_DART_AUDIT: "감사보고서 수치로 대체됨",
  HISTORICAL_ARRANGEMENT: "과거 주선(보유 아님)",
  UNVERIFIED_PARTICIPATION: "참여 미검증",
};

export const RELATIONSHIP_STATUS_KO: Record<string, string> = {
  current: "현재", funded: "집행됨", committed: "약정(미집행 가능)", operating: "운영 중", proposed: "추진 중",
  review: "검토 중", repaid: "상환", historical: "과거", terminated: "종료", unknown: "상태 미확인",
  assumption: "가정", unverified_current: "현재 여부 미확인",
};

export const TRANSMISSION_CLASS_KO: Record<string, string> = {
  direct_contract: "직접 계약",
  direct: "직접 계약",
  indirect_vehicle: "SPC·펀드 경유",
  sector_demand: "산업 수요 경로(가정)",
  funding_market: "자금시장 경로(가정)",
  unverified: "미검증",
  unclassified: "분류 없음(계약 아님)",
};

export const CW_DISTRESS_KO: Record<string, string> = {
  normal: "정상(추가 충격 없음)",
  moderate: "중간 스트레스",
  severe_liquidity: "심각한 유동성 압박",
  payment_default: "지급불이행(모형)",
  insolvency: "회생·파산(모형)",
};

export const STRESS_LEVEL_KO: Record<string, string> = {
  normal: "정상",
  moderate: "중간",
  elevated: "상승",
  high: "높음",
  critical: "심각(시나리오 추정)",
  insufficient: "산정 불가",
  unknown: "미확인",
};

/** Semiconductor rate-shock exposure classes. */
export const EXPOSURE_CLASS_KO: Record<string, string> = {
  direct_computed: "직접 계산",
  secondary_contagion: "2차 전염",
  potential_indirect: "잠재 간접(금액 미산정)",
  transmission_channel: "전달 채널(손실 아님)",
  insufficient_data: "자료 부족",
  qualitative_refi: "정성 · 만기 재발행",
  qualitative_credit: "정성 · 신용 채널",
  no_identified_exposure: "노출 미확인",
  floating_sensitive: "변동금리 · 이자 민감",
  fixed_coupon: "고정금리 · 이자 불변",
  not_applicable: "해당 없음",
};

export const CRISIS_MODE_KO: Record<string, string> = {
  rate_only: "금리만",
  cw_default: "CoreWeave 부도 가정",
  financing: "자금조달 경색",
  combined: "복합",
};

export const SOURCE_STATUS_KO: Record<string, string> = {
  VERIFIED: "공시·발표 확인",
  INFERRED: "공개자료 기반 추론",
  ASSUMED: "사용자 가정",
  UNKNOWN: "미확인",
};

export const GPU_IMPACT_KO: Record<string, string> = {
  none: "없음", assumed_operator: "운영사 마진 전가(가정)", lease_protected: "임대차로 보호", insufficient: "자료 부족",
};
export const CAPEX_IMPACT_KO: Record<string, string> = {
  none: "없음", future_phases: "향후 증설 단계", construction_funding: "공사 자금조달", qualitative: "정성",
};

export const PROVIDER_KO: Record<string, string> = {
  quotes_us: "미국 주가 (yfinance 일간 종가)",
  quotes_krx: "한국 주가 (FinanceDataReader)",
  fx: "환율 (한국수출입은행)",
};

export const ENTITY_TYPE_KO: Record<string, string> = {
  company: "기업", spv: "SPC·PFV", lender: "대주", bank: "은행", fund: "펀드", savings_bank: "저축은행", asset_manager: "자산운용사",
  securities: "증권사", nbFI: "비은행 금융기관", insurer: "보험사", trust_company: "신탁사", financial: "금융기관", cooperative: "상호금융",
  cooperative_federation: "상호금융 중앙회", mutual_aid: "공제회", reit: "리츠", operator: "운영사", holding: "지주사", project_ref: "사업 참조",
  developer: "시행사", sponsor: "스폰서", project: "사업", operating_asset: "운영 자산",
};
/** PF exposure classes kept in key_drivers / pf_exposure_class. */
export const PF_CLASS_KO: Record<string, string> = {
  confirmed_aidc_project: "AI 데이터센터 사업 참여 확인",
  confirmed_dc_finance: "데이터센터 금융 참여 확인",
  general_pf: "일반 PF 참여 (DC 연계 미확인)",
  sector_sensitivity: "산업 민감도 (직접 관계 미확인)",
  research_candidate: "조사 후보",
  borrower_spv: "차주 SPC",
};
export const SECTOR_KO: Record<string, string> = { datacenter_pf: "AI 데이터센터 PF", stress_direction: "충격 전달 방향", initial_purchaser: "최초 인수인" };

/** Short mechanism labels the PF engine attaches to stressed nodes. */
export const MECHANISM_KO: Record<string, string> = {
  sector_kr: "산업 수요 경로(가정)",
  funding_market: "자금시장 경로(가정)",
  sector_lending_capacity: "여신 여력 압력(정성)",
  lending_capacity: "여신 여력 압력(정성)",
  kr_epc_verified: "확인된 시공 계약 경로",
  hbm_demand: "HBM 수요 경로(정성)",
  gpu_rent: "GPU 임대료 경로(가정)",
  cw_lease_credit: "CoreWeave 임차 신용 경로",
  cw_distress: "CoreWeave 스트레스(가정)",
  sponsor: "시행·스폰서 경로",
  normal: "정상",
};

const TABLES = [MECHANISM_KO, ENTITY_TYPE_KO, SECTOR_KO, PF_CLASS_KO, 
  AMOUNT_KIND_KO, EXPOSURE_STATUS_KO, RELATIONSHIP_STATUS_KO, TRANSMISSION_CLASS_KO, CW_DISTRESS_KO,
  STRESS_LEVEL_KO, EXPOSURE_CLASS_KO, CRISIS_MODE_KO, SOURCE_STATUS_KO,
];

/** Look a code up in one table, falling back to a readable form (never shows a raw snake_case code). */
export function koOf(table: Record<string, string>, code: string | null | undefined, fallback = "—"): string {
  if (code === null || code === undefined || code === "") return fallback;
  return table[code] ?? table[code.toLowerCase()] ?? table[code.toUpperCase()] ?? humanize(code);
}

/** Any known code → Korean. Unknown codes are de-snake-cased rather than shown raw. */
export function ko(code: string | null | undefined, fallback = "—"): string {
  if (code === null || code === undefined || code === "") return fallback;
  for (const t of TABLES) {
    const v = t[code] ?? t[code.toLowerCase()] ?? t[code.toUpperCase()];
    if (v) return v;
  }
  return humanize(code);
}

function humanize(code: string): string {
  // Already natural text (contains Hangul or spaces) → leave as is.
  if (/[가-힣]/.test(code) || /\s/.test(code)) return code;
  return code.replace(/_/g, " ").toLowerCase();
}

// ---------------------------------------------------------------- units

const n2 = (x: number) => x.toFixed(2);

/** Multiple (배) change: 3.72배 → 2.76배 (0.96배 감소). Never "pp". */
export function multipleChange(base: number | null | undefined, next: number | null | undefined): string | null {
  if (base == null || next == null || !Number.isFinite(base) || !Number.isFinite(next)) return null;
  const d = next - base;
  const tail = Math.abs(d) < 0.005 ? "변화 없음" : `${n2(Math.abs(d))}배 ${d < 0 ? "감소" : "증가"}`;
  return `${n2(base)}배 → ${n2(next)}배 (${tail})`;
}

/** Rate change in bp, e.g. +100bp. */
export function bp(x: number): string {
  return `${x > 0 ? "+" : x < 0 ? "−" : ""}${Math.abs(Math.round(x))}bp`;
}

/** Difference between two rates expressed in %p (percentage points of a rate). */
export function pctPoint(x: number, digits = 2): string {
  return `${x > 0 ? "+" : x < 0 ? "−" : ""}${Math.abs(x).toFixed(digits)}%p`;
}

/** Relative change in %. Returns null when the base is 0 (cannot express a ratio). */
export function relChangePct(base: number, next: number, digits = 1): string | null {
  if (!Number.isFinite(base) || !Number.isFinite(next) || Math.abs(base) < 1e-12) return null;
  const r = ((next - base) / Math.abs(base)) * 100;
  return `${r > 0 ? "+" : r < 0 ? "−" : ""}${Math.abs(r).toFixed(digits)}%`;
}

/** KRW 억원 with grouping. */
export function eok(x: number): string {
  const v = Math.abs(x) >= 100 ? Math.round(x) : Math.round(x * 100) / 100;
  return `${v.toLocaleString("ko-KR")}억 원`;
}

/** The quote button says what it really does: a server fetch, or re-reading the stored snapshot. */
export function refreshLabel(live: boolean, busy: boolean): string {
  if (busy) return live ? "시세 조회 중…" : "불러오는 중…";
  return live ? "시세 새로 조회 (일간 종가)" : "저장된 시세 다시 불러오기";
}
export function refreshTip(live: boolean): string {
  return live
    ? "시세 서버에서 최신 일간 종가를 다시 수집합니다. 실시간 체결가가 아니며, 같은 종목은 5분에 한 번만 새로 수집됩니다."
    : "배포 시 저장한 시세 스냅샷을 다시 읽습니다. 새 시세를 가져오지 않습니다.";
}

/**
 * Free-text notes from the research pipeline sometimes carry internal record ids
 * ("[superseded by dart_loan_* 당기말]"). Show them as plain words; names replace node ids.
 */
export function cleanNote(text: string | null | undefined, nameOf?: (id: string) => string | null): string {
  if (!text) return "";
  return text
    .replace(/\[superseded by [^\]]*\]/gi, "[최신 감사보고서 수치로 대체됨]")
    .replace(/\b[a-z][a-z0-9]*(?:_[a-z0-9*]+){1,}\*?(?:_[a-z0-9*]+)*/g, (tok) => {
      const n = nameOf?.(tok);
      if (n) return n;
      if (tok.includes("*") || /^(dart|v6|pf|kr|edge|rel)_/.test(tok)) return "관련 관계 기록";
      return ko(tok);
    });
}
