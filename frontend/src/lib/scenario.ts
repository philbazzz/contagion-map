/** Scenario inputs, plain-language help and network filter classes. */
import type { Instrument, Network, RateShockParams } from "../types";
import type { CrisisMode, FundingAvail } from "../engine/sectorContagion";

export interface ShockForm {
  shockBp: number;
  benchmark: RateShockParams["benchmark"];
  sofr: number | null;
  /** Contagion scenario family. */
  crisisMode: CrisisMode;
  refiAvailability: FundingAvail;
  projectFinancing: FundingAvail;
  horizonMonths: 12 | 24;
}

export interface RefiForm {
  instrumentId: string;
  newRate: number;            // %
  amount: number | null;      // USD M (null = disclosed 6/30 balance)
  basis: "stated" | "effective";
  refiDate: string | null;    // YYYY-MM (null = instrument maturity)
  success: number;            // 0-1
  fee: number;                // % one-off
  tenor: number;              // years
  sofr: number | null;        // % (null = dataset observation)
  capexAbsorb: number | null; // % of added interest absorbed by capex cut (null = no assumption)
  gpuShare: number | null;    // % of capex cut that is GPU purchase (null = no assumption)
}

export const defaultShockForm = (): ShockForm => ({
  shockBp: 100,
  benchmark: "sofr",
  sofr: null,
  crisisMode: "rate_only",
  refiAvailability: "normal",
  projectFinancing: "normal",
  horizonMonths: 12,
});

export const defaultForm = (net: Network): RefiForm => ({
  instrumentId: net.meta.next_maturity_id || net.financials.instruments[0].id,
  newRate: 12, amount: null, basis: "stated", refiDate: null, success: 1, fee: 0, tenor: 5,
  sofr: null, capexAbsorb: null, gpuShare: null,
});

export interface InputHelp { term: string; oneLine: string; example: string; status: "ASSUMED" | "VERIFIED" | "MARKET" }

export const HELP: Record<string, InputHelp> = {
  shockBp: { term: "금리 충격", oneLine: "현재 조건(+0bp) 대비 추가 충격(bp). +0bp는 절대금리 0%가 아니라 ‘추가 충격 없음’입니다. 결과는 항상 +0bp 기준과 비교되며, 직전 슬라이더 값(+300→+500)과의 증분이 아닙니다.", example: "+500bp를 고르면 +0bp 대비 결과가 표시됩니다 (+300에서 바꾼 경우에도 동일).", status: "ASSUMED" },
  benchmark: { term: "기준금리", oneLine: "충격을 적용할 시장 변수. SOFR와 국채 금리는 서로 다른 변수입니다.", example: "국채 +100bp가 SOFR 차입 이자를 자동으로 +100bp 올리지 않습니다.", status: "ASSUMED" },
  crisisMode: { term: "위기 시나리오", oneLine: "CoreWeave 금리만 / CW 채무불이행 / 섹터 자금경색 / 복합.", example: "복합은 임차 중단과 조달 제한을 동시에 적용합니다.", status: "ASSUMED" },
  refiAvailability: { term: "차환 가능 여부", oneLine: "만기도래 부채를 시장에서 다시 조달할 수 있는지.", example: "unavailable면 단기 만기 원금이 유동성 압박으로 잡힙니다.", status: "ASSUMED" },
  projectFinancing: { term: "신규 프로젝트 금융", oneLine: "신규 데이터센터·GPU 프로젝트 자금 조달 환경.", example: "unavailable면 공시 CAPEX 필요가 자금 갭으로 반영됩니다.", status: "ASSUMED" },
  horizonMonths: { term: "시나리오 시계", oneLine: "자금 갭·이자 증가를 누적하는 기간.", example: "12개월 또는 24개월.", status: "ASSUMED" },
  instrument: { term: "차환 대상 차입금", oneLine: "새 금리로 다시 빌린다고 가정할 차입금 하나. 다른 차입금 금리는 그대로입니다.", example: "기본값은 최종 만기가 가장 먼저 오는 차입금(10-Q 기준).", status: "VERIFIED" },
  newRate: { term: "신규 차환금리", oneLine: "다시 빌릴 때의 연 금리(전부 포함). 사용자 가정입니다.", example: "9% · 12% · 15%는 같은 조건으로 함께 비교됩니다.", status: "ASSUMED" },
  basis: { term: "기존 비교금리", oneLine: "표면금리 = 계약상 금리(고정 쿠폰 또는 SOFR+가산금리). 유효이자율 = 10-Q가 공시한 할인·발행비 상각 포함 금리(정수 % 반올림).", example: "표면금리가 공시되지 않은 차입금은 자동으로 유효이자율을 씁니다.", status: "VERIFIED" },
  amount: { term: "차환 대상 금액", oneLine: "비워 두면 2026.6.30 공시 잔액을 씁니다.", example: "분할상환 차입금은 만기 잔액이 더 작을 수 있습니다.", status: "ASSUMED" },
  refiDate: { term: "차환 시점", oneLine: "새 금리가 적용되기 시작하는 달. 비우면 해당 차입금 만기월.", example: "연도별 표의 첫해는 시작 월부터 일할 계산됩니다.", status: "ASSUMED" },
  success: { term: "차환 성공 비율", oneLine: "새 차입으로 갈아탈 수 있는 비율. 나머지는 자체 자금으로 갚아야 할 금액(자금조달 필요액).", example: "75%면 $2.0B 중 $500M을 자체 상환.", status: "ASSUMED" },
  fee: { term: "추가 조달비용", oneLine: "차환 때 한 번 드는 수수료(금액 대비 %).", example: "1%면 $2.0B 차환 시 $20M.", status: "ASSUMED" },
  tenor: { term: "신규 만기", oneLine: "새 차입금의 만기(년). 일시상환으로 가정해 연도별 원리금을 보여줍니다.", example: "5년이면 마지막 해에 원금 상환.", status: "ASSUMED" },
  sofr: { term: "SOFR", oneLine: "변동금리 차입금의 기준금리. 기본값은 데이터 기준일의 관측값입니다.", example: "고정금리 차입금에는 영향이 없습니다.", status: "MARKET" },
  capexAbsorb: { term: "CAPEX 흡수율", oneLine: "추가 이자 중 설비투자(CAPEX)를 줄여서 메운다고 가정할 비율. 비우면 투자 축소를 계산하지 않습니다.", example: "100%면 추가 이자 $55M만큼 CAPEX가 줄어든다고 가정.", status: "ASSUMED" },
  gpuShare: { term: "GPU 비중", oneLine: "줄어든 CAPEX 중 GPU 구매가 차지한다고 가정할 비율. 비우면 NVIDIA 금액을 계산하지 않습니다.", example: "60%면 CAPEX 축소 $55M 중 $33M을 GPU 구매 감소로 봅니다.", status: "ASSUMED" },
};

export const GLOSSARY: { term: string; plain: string }[] = [
  { term: "직접 노출", plain: "공시된 변동금리 잔액에 금리 충격을 곱해 연간 이자 변화를 계산할 수 있는 경우" },
  { term: "잠재 간접", plain: "관계는 확인되나 전달 규모를 계산할 데이터가 없어 경로만 표시" },
  { term: "전달 채널", plain: "대주·주선 등 금융 연결. 금리 상승이 곧 해당 기관의 손실은 아님" },
  { term: "데이터 부족", plain: "관계나 차입은 있으나 잔액·금리 유형이 미공시라 금액을 만들지 않음" },
  { term: "bp (베이시스 포인트)", plain: "금리 0.01%포인트. 100bp = 1%포인트" },
  { term: "SOFR", plain: "달러 단기 기준금리. CoreWeave 변동금리 차입금이 연동" },
  { term: "VERIFIED", plain: "공식 공시 또는 회사 발표로 확인된 정보" },
  { term: "INFERRED", plain: "공개자료를 바탕으로 추론했거나 2차 출처에서만 확인된 정보" },
  { term: "ASSUMED", plain: "사용자가 시나리오에서 정한 값" },
  { term: "UNKNOWN", plain: "공개자료로 확인되지 않은 정보 — 숫자를 만들지 않습니다" },
  { term: "계산값", plain: "공시 수치와 사용자 금리로 직접 계산한 값 (CoreWeave 이자비용)" },
  { term: "관계만 확인", plain: "연결은 확인되지만 영향 규모를 계산할 공개 데이터가 없는 경우. 금액·점수를 만들지 않습니다" },
  { term: "Arranger / Bookrunner", plain: "대출을 구조화·판매하는 역할. 대출 전체를 보유한다는 뜻이 아닙니다" },
];

export const CLASSES: { id: string; label: string; groups: string[] }[] = [
  { id: "financial", label: "금융기관", groups: ["financial"] },
  { id: "customer", label: "클라우드 · 고객", groups: ["customer"] },
  { id: "semiconductor", label: "반도체", groups: ["semiconductor"] },
  { id: "supply", label: "서버 · 네트워킹", groups: ["server", "ai_infra"] },
  { id: "datacenter", label: "데이터센터 · 장비", groups: ["datacenter"] },
  { id: "project_finance", label: "프로젝트 금융 SPV", groups: ["project_finance"] },
];

export const KIND_KO: Record<Instrument["kind"], string> = {
  term_loan: "담보부 대출(DDTL)", revolver: "리볼빙 한도", senior_notes: "선순위 무담보채", convertible: "전환사채",
  vendor_financing: "공급사 금융", other_loan: "기타 대출",
};

/** Instruments a user can refinance: has a disclosed balance or can take a typed amount and has some rate basis. */
export function refinanceable(i: Instrument) {
  return i.effective_rate_pct !== null || i.coupon_pct !== null || i.spread_pct !== null;
}
