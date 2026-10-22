import type { CSSProperties } from "react";
import type { RunView } from "../App";
import { STAGES } from "../engine/refinancing";
import { SHOCK_STAGES } from "../engine/rateShock";
import { PF_SHOCK_STAGES } from "../pf/shockEngine";
import { korUsd, usdM } from "../lib/format";
import { IconNext, IconPause, IconPlay, IconPrev, IconReset } from "./Icons";

const SPEEDS = [0.5, 1, 1.5, 2, 3];
const sgn = (x: number) => (x > 0 ? "+" : "");
const fx = (x: number, d: number) => `${x > 0 ? "+" : x < 0 ? "−" : ""}${Math.abs(x).toFixed(d)}`;

interface Kpi { k: string; v: string; tone?: string; tip: string; vtip?: string }

export function BottomBar(p: {
  run: RunView | null; stage: number; lastStage: number; playing: boolean; speed: number;
  onPlayPause: () => void; onPrev: () => void; onNext: () => void; onSeek: (s: number) => void; onReset: () => void;
  onSpeed: (s: number) => void;
}) {
  const r = p.run;
  const kpis: Kpi[] = [];
  const stages = r?.kind === "pf_shock" ? PF_SHOCK_STAGES : r?.kind === "rate_shock" ? SHOCK_STAGES : STAGES;

  if (r?.kind === "pf_shock") {
    const pf = r.result.pf;
    const s = r.result.summary;
    kpis.push(
      { k: "CW", v: String(pf.coreweave_distress || "normal"), tip: "Primary shock A — CoreWeave distress ladder (modeled)" },
      { k: "CAPEX", v: `${pf.hyperscaler_capex_pct}%`, tip: "Primary shock B — Big Tech AI CAPEX scenario" },
      { k: "Rates/GPU", v: `+${pf.rate_bp}bp / ${pf.gpu_rent_pct}%`, tip: "Secondary: USD PF rates & GPU rental" },
      { k: "Measurable", v: String(pf.measurable_projects), tip: "Projects with quantified interest or operator stress" },
      { k: "US→KR", v: `${pf.korean_verified_exposure}/${pf.korean_sector_sensitivity}`, tip: "Direct contract paths / sector·funding paths" },
      { k: "Crit", v: String(s.companies_critical ?? 0), tip: "Modeled critical — not confirmed legal default" },
    );
  } else if (r?.kind === "rate_shock") {
    const s = r.result.summary;
    const delta = s.total_incremental_interest_usd_m;
    kpis.push(
      { k: "선택 시나리오", v: `${r.result.benchmark.label_en} ${s.shock_bp > 0 ? "+" : ""}${s.shock_bp}bp`, tip: `${r.result.benchmark.plain} · 현재 기준(+0bp) 대비 절대 충격 (이전 슬라이더 값과 무관)` },
      { k: "현재 대비 Δ이자/년", v: delta === null ? "미산정" : `${sgn(delta)}${usdM(delta)}`, vtip: delta !== null ? korUsd(delta) : undefined,
        tone: delta && delta > 0 ? "warn" : undefined,
        tip: "+0bp(현재 조건) 대비. 원금 × bp / 10,000. +0bp면 변화 0" },
      { k: "Direct", v: String(s.direct_measurable), tip: "연간 이자 변화를 숫자로 계산한 기업 수" },
      { k: "L1/L2/L3+", v: `${s.order1 ?? 0}/${s.order2 ?? 0}/${s.order3_plus ?? 0}`, tip: `전염 order · max ${s.max_contagion_order ?? 0} · quantified ${s.quantified_contagion ?? 0} · pathway ${s.pathway_only ?? 0}` },
      { k: "Sector", v: String(s.sector_stressed ?? 0), tip: `섹터(비-홉) · 심각 ${s.sector_critical ?? 0} · SPV ${s.spv_critical ?? 0}` },
      { k: "Crit", v: String(s.companies_critical ?? 0), tip: "모델상 critical (확정 부도 아님)" },
    );
  } else if (r?.kind === "refinancing") {
    const m = r.result.result;
    kpis.push(
      { k: "Scenario", v: `${r.result.instrument.name} → ${m.new_rate_pct}%`, tip: `차환 대상 ${r.result.instrument.name} ${usdM(m.amount_usd_m)} · 기존 비교금리 ${m.existing_rate_pct}% (${r.result.existing_rate.formula})` },
      { k: "Δ Interest / yr", v: `${sgn(m.annual_interest_delta_usd_m)}${usdM(m.annual_interest_delta_usd_m)}`, vtip: korUsd(m.annual_interest_delta_usd_m), tone: m.annual_interest_delta_usd_m > 0 ? "warn" : undefined,
        tip: "추가 연간 이자비용 = 차환 금액 × 성공 비율 × (신규 금리 − 기존 비교금리). 계산값" },
      { k: "Rate Δ", v: `${fx(m.rate_change_bp, 0)}bp`, tip: "신규 금리 − 기존 비교금리 (bp)" },
      { k: "vs 6M OCF", v: m.delta_6m_vs_ocf_6m_pct === null ? "—" : `${fx(m.delta_6m_vs_ocf_6m_pct, 2)}%`,
        tip: "추가 이자 6개월분 ÷ 2026 상반기 영업현금흐름 (10-Q). 기간을 맞춘 비교" },
      { k: "9 / 12 / 15%", v: r.result.comparison.map((c) => `${sgn(c.annual_interest_delta_usd_m)}${usdM(c.annual_interest_delta_usd_m)}`).join(" · "),
        tip: "같은 차입금·같은 비금리 가정에서 신규 금리 9% · 12% · 15%일 때의 추가 연간 이자비용" },
    );
  }
  kpis.push({ k: "Stage", v: r ? `${p.stage + 1}/${p.lastStage + 1}` : "—", tip: "현재 재생 단계 / 전체 단계. 지도와 패널은 이 단계 기준" });

  return (
    <footer className="bb">
      <div className="bb-transport" role="group" aria-label="재생 제어">
        <button type="button" className="ibtn" onClick={p.onPrev} disabled={!r || p.stage === 0} data-tip="이전 단계 (←)" aria-label="이전 단계"><IconPrev size={14} /></button>
        <button type="button" className="ibtn ibtn-play" onClick={p.onPlayPause} disabled={!r}
          data-tip={p.stage >= p.lastStage && !p.playing ? "처음부터 전파 시퀀스 다시 재생 (현재 시나리오)" : "재생 / 일시정지 (Space)"}
          aria-label={p.playing ? "일시정지" : (p.stage >= p.lastStage ? "다시 재생" : "재생")}>
          {p.playing ? <IconPause size={14} /> : <IconPlay size={14} />}
        </button>
        <button type="button" className="ibtn" onClick={p.onNext} disabled={!r || p.stage >= p.lastStage} data-tip="다음 단계 (→)" aria-label="다음 단계"><IconNext size={14} /></button>
        <select id="speed" className="speed num" value={p.speed} onChange={(e) => p.onSpeed(Number(e.target.value))} aria-label="재생 속도" data-tip="애니메이션 재생 속도 (계산에는 영향 없음)">
          {SPEEDS.map((s) => <option key={s} value={s}>{s.toFixed(1)}×</option>)}
        </select>
        <button type="button" className="ibtn" onClick={p.onReset} disabled={!r} data-tip="충격 초기화 (+100bp SOFR)" aria-label="초기화"><IconReset size={14} /></button>
      </div>

      <div className="bb-timeline">
        <input id="timeline" type="range" min={0} max={Math.max(1, p.lastStage)} step={1} value={r ? p.stage : 0}
          disabled={!r} onChange={(e) => p.onSeek(Number(e.target.value))} aria-label="단계 이동"
          style={{ "--fill": r ? `${(p.stage / Math.max(1, p.lastStage)) * 100}%` : "0%" } as CSSProperties} />
        <div className="ticks">
          {stages.map((s, i) => (
            <button type="button" key={s} disabled={!r} className={`${r && i <= p.stage ? "is-past" : ""} ${r && i === p.stage ? "is-cur" : ""}`} onClick={() => p.onSeek(i)} data-tip={s}>
              S{i + 1}<span className="tk-l"> {s.split(" ")[0]}</span>
            </button>
          ))}
        </div>
      </div>

      <dl className="bb-kpi">
        {kpis.map((k) => (
          <div key={k.k} data-tip={k.tip}><dt>{k.k}</dt><dd className={`num ${k.tone || ""}`} data-tip={k.vtip}>{k.v}</dd></div>
        ))}
      </dl>
    </footer>
  );
}
