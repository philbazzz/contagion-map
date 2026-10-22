/**
 * Three-line answer at the top of every PF shock result:
 *  ① what changed vs. "no additional shock"  ② who / which projects are affected  ③ why (contract · assumption · path)
 * Quantified results, contract-based qualitative impact, assumption paths and data gaps are counted separately.
 */
import type { PfShockForm, PfShockResult } from "../pf/types";
import { CW_DISTRESS_KO, bp } from "../lib/labels";

export function changedInputs(f: PfShockForm | PfShockResult["pf"]): string[] {
  const g = f as Partial<PfShockForm> & Partial<PfShockResult["pf"]>;
  const distress = (g.coreweaveDistress ?? g.coreweave_distress) || "normal";
  const capex = g.hyperscalerCapexPct ?? g.hyperscaler_capex_pct ?? 0;
  const rate = g.rateBp ?? g.rate_bp ?? 0;
  const kr = g.krRateBp ?? g.kr_rate_bp ?? 0;
  const gpu = g.gpuRentPct ?? g.gpu_rent_pct ?? 0;
  const restrict = g.restrictNewFinancing ?? g.restrict_new_financing ?? false;
  const out: string[] = [];
  if (distress !== "normal") out.push(`CoreWeave ${CW_DISTRESS_KO[distress] || distress}`);
  if (capex) out.push(`빅테크 AI CAPEX ${capex}%`);
  if (rate) out.push(`미국 PF 금리 ${bp(rate)}`);
  if (kr) out.push(`국내 조달금리 ${bp(Math.round(kr))}`);
  if (gpu) out.push(`GPU 임대료 ${gpu}%`);
  if (restrict) out.push("신규 프로젝트 금융 제한");
  return out;
}

export function PfShockDigest({ result, pending }: { result: PfShockResult; pending?: boolean }) {
  const pf = result.pf;
  const b = pf.impact_breakdown;
  const changes = changedInputs(pf);
  const quantProjects = pf.projects.filter((p) => p.quantified && p.level !== "normal");
  const dscrComputable = pf.projects.filter((p) => p.baseline_dscr != null && p.stressed_dscr != null).length;
  const contractKinds = new Map<string, number>();
  for (const c of pf.affected_companies) {
    if (c.basis !== "contract" && c.basis !== "quantified") continue;
    for (const p of c.projects) contractKinds.set(p.exposure_label, (contractKinds.get(p.exposure_label) || 0) + 1);
  }
  const assumptionPaths: string[] = [];
  if (b.assumption) {
    if (pf.hyperscaler_capex_pct < 0) assumptionPaths.push("AI CAPEX 감소 → 국내 시공·장비 수요(가정)");
    if (pf.coreweave_distress && pf.coreweave_distress !== "normal") assumptionPaths.push("CoreWeave 스트레스 → 국내 DC PF 자금시장 심리(가정 전가율)");
    if (pf.restrict_new_financing) assumptionPaths.push("신규 PF 제한 → 대주 여신 여력(정성)");
  }
  return (
    <div className={`shock-digest ${pending ? "is-pending" : ""}`} aria-live="polite">
      {pending ? <p className="digest-pending">입력이 바뀌어 다시 계산 중입니다 — 아래는 직전 입력의 결과입니다.</p> : null}
      <div className="digest-row">
        <span className="digest-k">① 바뀐 것</span>
        <p className="digest-v">{changes.length ? <>추가 충격 없음 대비 <b>{changes.join(" · ")}</b></> : <b>추가 충격 없음 (비교 기준 상태)</b>}</p>
      </div>
      <div className="digest-row">
        <span className="digest-k">② 영향 대상</span>
        <div className="digest-v">
          {changes.length ? (
            <>
              <p>스트레스 단계가 올라간 기업 <b className="num">{b.unique_companies}</b>개 <span className="muted">(중복 제거 · 손실·부도 확인 아님)</span></p>
              <ul className="digest-split">
                <li><span className="cert cert-confirmed">정량 계산</span> <b className="num">{b.quantified}</b></li>
                <li><span className="cert cert-inferred">계약 근거 정성</span> <b className="num">{b.contract}</b></li>
                <li><span className="cert cert-assumed">산업·자금시장 가정</span> <b className="num">{b.assumption}</b></li>
              </ul>
              <p className="fine">정량 산정 불가 <b className="num">{b.data_gap}</b>개 — CFADS·원리금·기관별 보유잔액이 공개되지 않아 금액·DSCR을 계산하지 않았습니다. 계산 불가는 '영향 없음'이 아닙니다.</p>
              <p className="fine">사업장: 정량 계산 {quantProjects.length}개 · DSCR {dscrComputable ? `산정 가능 ${dscrComputable}개 중 악화 ${pf.dscr_deterioration}개` : "산정 불가 (CFADS·원리금 미공시)"}</p>
            </>
          ) : <p>비교 기준 상태라 추가 영향이 없습니다.</p>}
        </div>
      </div>
      {changes.length ? (
        <div className="digest-row">
          <span className="digest-k">③ 근거</span>
          <div className="digest-v">
            {contractKinds.size ? <p>계약: {[...contractKinds.entries()].slice(0, 3).map(([k, n]) => `${k} ${n}건`).join(" · ")}</p> : <p className="muted">계약으로 확인된 직접 경로 없음</p>}
            {assumptionPaths.length ? <p>가정 경로: {assumptionPaths.join(" · ")}</p> : null}
            <p className="fine">미국→국내 직접 계약 {pf.korean_verified_exposure}건 · 산업·자금시장 경로 {pf.korean_sector_sensitivity}건{pf.korean_unclassified_links ? ` · 계약 아닌 공급망·제휴 링크 ${pf.korean_unclassified_links}건(직접 계약에서 제외)` : ""}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
