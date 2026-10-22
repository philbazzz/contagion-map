/**
 * Six separate states for an entity, computed from the relationship data itself (never from a
 * hand-typed "연결관계 확인 필요" flag), so the header, lists, hover cards and shock views agree.
 *  ① 식별  ② 금융·사업 관계 확인  ③ 금액 확인  ④ 현재 거래  ⑤ 선택한 충격의 전파 경로  ⑥ 정량 계산 가능
 */
import type { NetEdge, NetNode, Network } from "../types";
import type { PfShockResult } from "../pf/types";
import { amountFacts } from "./evidence";

export interface StateItem { code: string; ko: string }
export interface RelationState {
  identity: StateItem;
  relation: StateItem & { count: number; financial: number };
  amount: StateItem;
  current: StateItem;
  shockPath: StateItem;
  quant: StateItem;
  /** One line that never turns "no path for this shock" into "no relationship". */
  headline: string;
}

const FIN_TYPES = /LOAN|EQUITY|GUARANTEE|COMMITMENT|CREDIT|ABS|NOTES|REVOLVER|UNDERWRITE|PLEDGE|BENEFICIARY|FINANCING|COLLATERAL|DEBT/;

type ShockLike =
  | { kind: "pf"; result: PfShockResult }
  | { kind: "rate"; assessments: Record<string, { category?: string; exposure_class?: string }>; activeIds: Set<string> }
  | null;

export function relationState(n: NetNode, edges: NetEdge[], today: string, shock: ShockLike): RelationState {
  const mine = edges.filter((e) => e.source === n.id || e.target === n.id);
  const facts = mine.map((e) => ({ e, f: amountFacts(e, today) }));
  const live = facts.filter(({ f }) => f.current === "current" || f.current === "matured_unconfirmed");
  const evidenced = live.filter(({ e }) => e.source_status === "VERIFIED" || e.source_status === "INFERRED");
  const verified = evidenced.filter(({ e }) => e.source_status === "VERIFIED");
  const fin = evidenced.filter(({ e }) => FIN_TYPES.test(e.relationship_type) || e.impact_channel === "financial" || e.impact_channel === "equity");

  const nameHidden = /명칭 미공개|미상/.test(`${n.name} ${n.name_ko || ""}`);
  const identity = nameHidden
    ? { code: "name_undisclosed", ko: "법인 식별 · 명칭 미공개" }
    : { code: "identified", ko: "기업·사업 식별됨" };

  const relation = evidenced.length
    ? { code: verified.length ? "confirmed" : "inferred", ko: `${fin.length ? "금융" : "사업"}관계 ${verified.length ? "확인" : "추론"} ${evidenced.length}건`, count: evidenced.length, financial: fin.length }
    : mine.length
      ? { code: "past_or_unverified", ko: "현재 확인된 관계 없음 (과거·미검증만)", count: 0, financial: 0 }
      : { code: "none", ko: "관계 데이터 없음", count: 0, financial: 0 };

  const withAmt = live.filter(({ f }) => f.value !== null);
  const conf = withAmt.filter(({ f }) => f.certainty === "confirmed");
  const amount = !live.length
    ? { code: "na", ko: "해당 없음" }
    : conf.length === live.length
      ? { code: "confirmed", ko: "금액 확인" }
      : conf.length
        ? { code: "partial", ko: `금액 일부 확인 (${conf.length}/${live.length}건)` }
        : withAmt.length
          ? { code: "estimated", ko: "금액 추정·확인 필요" }
          : { code: "unknown", ko: "금액 미확인" };

  const pastN = facts.filter(({ f }) => f.current === "past").length;
  const current = live.length
    ? { code: "current", ko: `현재 거래 ${live.length}건${pastN ? ` · 종료 ${pastN}건` : ""}` }
    : pastN ? { code: "past_only", ko: "상환·종료 거래만 있음" } : { code: "none", ko: "거래 정보 없음" };

  let shockPath: StateItem = { code: "no_shock", ko: "충격 미선택" };
  let quant: StateItem = { code: "no_shock", ko: "충격 미선택" };
  if (shock?.kind === "pf") {
    const pf = shock.result.pf;
    const hit = pf.affected_companies.find((c) => c.company_id === n.id);
    const proj = pf.projects.find((p) => p.project_id === n.id);
    const onPath = !!hit || (!!proj && proj.level !== "normal");
    shockPath = onPath ? { code: "on_path", ko: hit?.basis === "assumption" ? "충격 경로 해당 (가정 경로)" : "충격 경로 해당" }
      : { code: "not_on_path", ko: "해당 충격의 전파 경로 미확인" };
    const q = (proj && proj.quantified) || hit?.basis === "quantified";
    quant = q ? { code: "computable", ko: "정량 계산 가능" }
      : onPath ? { code: "not_computable", ko: "정량 산정 불가 (원리금·CFADS·보유잔액 자료 부족)" }
        : { code: "na", ko: "해당 없음" };
  } else if (shock?.kind === "rate") {
    const a = shock.assessments[n.id];
    const onPath = shock.activeIds.has(n.id) || (!!a && a.category !== "unconfirmed");
    shockPath = onPath ? { code: "on_path", ko: "충격 경로 해당" } : { code: "not_on_path", ko: "해당 충격의 전파 경로 미확인" };
    quant = a?.category === "computed" ? { code: "computable", ko: "정량 계산 가능" }
      : onPath ? { code: "not_computable", ko: "정량 산정 불가 (잔액·금리 자료 부족)" } : { code: "na", ko: "해당 없음" };
  }

  const relPart = relation.count ? (relation.financial ? "금융관계 확인" : "사업관계 확인") : relation.ko;
  const headline = shockPath.code === "no_shock" ? relPart : `${relPart} / ${shockPath.ko}`;
  return { identity, relation, amount, current, shockPath, quant, headline };
}

/** Lightweight version for lists and hover cards (no shock). */
export function hasLiveRelation(n: NetNode, net: Network, today: string): boolean {
  return net.edges.some((e) => (e.source === n.id || e.target === n.id)
    && (e.source_status === "VERIFIED" || e.source_status === "INFERRED")
    && ["current", "matured_unconfirmed"].includes(amountFacts(e, today).current));
}
