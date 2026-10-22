import { useEffect, useMemo, useState, type ReactNode } from "react";
import type { Instrument, Network, NodeVisual, QuoteItem, QuotesOverview, RateShockResult } from "../types";
import { CLASSES, GLOSSARY, HELP, KIND_KO, refinanceable, type RefiForm, type ShockForm } from "../lib/scenario";
import { korUsd, usdM } from "../lib/format";
import { existingRate } from "../engine/refinancing";
import { BENCHMARKS, SHOCK_PRESETS, simulateRateShock, type RateBenchmark } from "../engine/rateShock";
import { compareStress, STRESS_LABEL_KO, THRESHOLDS, type OriginStress } from "../engine/stressModel";
import type { CrisisMode, FundingAvail } from "../engine/sectorContagion";
import { IconChevron, IconInfo, IconReset, IconSearch } from "./Icons";
import { LpResize } from "./LpResize";
import { multipleChange } from "../lib/labels";
import { displayName } from "../lib/displayName";
import type { Mode } from "./TopBar";
import { refreshLabel, refreshTip } from "../lib/labels";

interface Props {
  mode: Mode;
  net: Network;
  quotes: QuotesOverview | null;
  quotesBusy: boolean;
  onRefreshQuotes: () => void;
  /** true = button fetches from a quote server; false = re-reads the stored snapshot. */
  quotesLive?: boolean;
  shock: ShockForm;
  onShock: (p: Partial<ShockForm>) => void;
  shockResult: RateShockResult | null;
  form: RefiForm;
  onForm: (p: Partial<RefiForm>) => void;
  summary: string;
  canRunRefi: boolean; blockReason: string | null; busy: boolean; stale: boolean;
  onRunRefi: () => void;
  hiddenGroups: string[]; onToggleGroup: (g: string) => void;
  visuals: Record<string, NodeVisual> | null; selectedId: string | null; onSelect: (id: string) => void;
  onOpenContract: (id: string) => void;
  shockPending?: boolean;
}

const STATUS_DOT: Record<string, string> = {
  shock_origin: "warn", stress_normal: "warn", stress_moderate: "warn", stress_high: "warn", stress_critical: "warn",
  contract_party: "gold-o", assumed: "warn", potential: "muted-o", insufficient: "muted-o",
};
const RATE_PRESETS = [9, 12, 15];
const BM_OPTS: RateBenchmark[] = ["sofr", "ust_2y", "ust_10y"];
/** Always compare selected shock vs current conditions (+0 bp). Never vs prior scenario. */
const BASELINE_BP = 0;
const CRISIS_MODES: { id: CrisisMode; label: string }[] = [
  { id: "rate_only", label: "CW 금리만" },
  { id: "cw_default", label: "A · CW 불이행" },
  { id: "financing", label: "B · 자금경색" },
  { id: "combined", label: "C · 복합" },
];
const FUNDING: FundingAvail[] = ["normal", "restricted", "unavailable"];

function Tip({ text }: { text: string }) {
  return <span className="tip-i" data-tip={text} aria-label={text}><IconInfo size={11} /></span>;
}
const helpTip = (k: string) => `${HELP[k].oneLine} ${HELP[k].example}`;
const StatusTag = ({ s }: { s: string }) => <span className={`st-tag st-${s}`}>{s}</span>;

function NumField({ id, value, onChange, step = 0.25, min, max, allowBlank, suffix, placeholder, width = 72 }: {
  id: string; value: number | null; onChange: (v: number | null) => void; step?: number; min?: number; max?: number;
  allowBlank?: boolean; suffix?: string; placeholder?: string; width?: number;
}) {
  const [txt, setTxt] = useState(value === null ? "" : String(value));
  useEffect(() => { setTxt(value === null ? "" : String(value)); }, [value]);
  const commit = (s: string) => {
    if (s.trim() === "") { if (allowBlank) onChange(null); else setTxt(value === null ? "" : String(value)); return; }
    let v = Number(s);
    if (Number.isNaN(v)) { setTxt(value === null ? "" : String(value)); return; }
    if (min !== undefined) v = Math.max(min, v);
    if (max !== undefined) v = Math.min(max, v);
    onChange(v);
  };
  return (
    <span className="numf" style={{ width }}>
      <input id={id} type="number" inputMode="decimal" step={step} min={min} max={max} value={txt} placeholder={placeholder}
        onChange={(e) => setTxt(e.target.value)} onBlur={(e) => commit(e.target.value)}
        onKeyDown={(e) => { if (e.key === "Enter") commit((e.target as HTMLInputElement).value); }} />
      {suffix ? <i>{suffix}</i> : null}
    </span>
  );
}

function Row({ k, label, children, status }: { k: string; label?: string; children: ReactNode; status?: string }) {
  return (
    <div className="kvrow">
      <label className="kvrow-l" htmlFor={`f-${k}`}>{label || HELP[k].term}<Tip text={helpTip(k)} /></label>
      <span className="kvrow-v">{children}{status && status !== "ASSUMED" ? <StatusTag s={status} /> : null}</span>
    </div>
  );
}

function EcosystemSummary({ res, net }: { res: RateShockResult | null; net: Network }) {
  /** Fixed +0 bp baseline from the same snapshot/config as the selected scenario. */
  const vsBaseline = useMemo(() => {
    if (!res) return null;
    try {
      const bm = res.params.benchmark as RateBenchmark;
      const baseline = simulateRateShock(net, {
        shock_bp: BASELINE_BP,
        benchmark: bm,
        sofr_pct: res.params.sofr_pct,
        crisis_mode: (res.summary.crisis_mode || "rate_only") as CrisisMode,
        refi_availability: "normal" as FundingAvail,
        project_financing: "normal" as FundingAvail,
        horizon_months: 12,
      });
      const scenario = res;
      const newlyCrit = Object.keys(scenario.assessments).filter((id) => {
        const bl = scenario.rounds[scenario.rounds.length - 1]?.node_states[id]?.stress;
        const al = baseline.rounds[baseline.rounds.length - 1]?.node_states[id]?.stress;
        return bl === "critical" && al !== "critical";
      });
      const dInt = (scenario.summary.total_incremental_interest_usd_m ?? 0)
        - (baseline.summary.total_incremental_interest_usd_m ?? 0);
      const dBp = scenario.summary.shock_bp - BASELINE_BP;
      const baseCov = baseline.origin_stress?.baseline_coverage ?? null;
      const scenCov = scenario.origin_stress?.stressed_coverage ?? null;
      let covDeltaPp: number | null = null;
      if (baseCov != null && scenCov != null) covDeltaPp = scenCov - baseCov;
      const baseScore = baseline.origin_stress?.score_delta_over_ocf;
      const scenScore = scenario.origin_stress?.score_delta_over_ocf;
      let scoreRelPct: number | null = null;
      if (baseScore != null && scenScore != null) {
        if (Math.abs(baseScore) < 1e-12) scoreRelPct = scenScore === 0 ? 0 : null;
        else scoreRelPct = ((scenScore - baseScore) / Math.abs(baseScore)) * 100;
      }
      return {
        baseline,
        scenario,
        diff: compareStress(
          (baseline.origin_stress ?? null) as OriginStress | null,
          (scenario.origin_stress ?? null) as OriginStress | null,
        ),
        newlyCrit,
        dInt,
        dBp,
        covDeltaPp,
        scoreRelPct,
        critBase: baseline.summary.companies_critical ?? 0,
        critScen: scenario.summary.companies_critical ?? 0,
        sectorBase: baseline.summary.sector_stressed ?? 0,
        sectorScen: scenario.summary.sector_stressed ?? 0,
        zeroChange: dBp === 0 && Math.abs(dInt) < 1e-9,
      };
    } catch { return null; }
  }, [net, res]);

  if (!res) {
    return (
      <div className="eco-sum is-idle">
        <p className="eco-lead">금리 충격을 조절하면 네트워크에서 <b>측정 가능한 노출</b>과 <b>재무 스트레스 상태</b>가 바로 표시됩니다. 모든 시나리오는 <b>현재 기준 (+0bp)</b>과 비교됩니다.</p>
      </div>
    );
  }
  const s = res.summary;
  const st = res.origin_stress;
  const delta = s.total_incremental_interest_usd_m;
  const items: [string, string, string][] = [
    ["네트워크", String(s.network_companies), "데이터에 등록된 기업·기관 수"],
    ["직접 측정", String(s.direct_measurable), "공시 잔액으로 연간 이자 변화를 계산한 기업"],
    ["2차 전염", String(s.secondary_stressed ?? 0), `임차 집중도 기반 · 심각 ${s.secondary_critical ?? 0} · 확정 부도 아님`],
    ["높은·심각 스트레스", String((s.companies_at_or_above_high ?? 0)), "직접+2차 합산 · 분석용 밴드 — 파산 예측 아님"],
    ["잠재 간접", String(s.potential_indirect), "관계는 확인되나 금액 미산정"],
    ["전달 채널", String(s.transmission_channels), "대주·주선 등 — 손실로 보지 않음"],
    ["데이터 부족", String(s.insufficient_data), "잔액·금리 미공시 또는 벤치마크 불일치·정성만"],
  ];
  return (
    <div className="eco-sum">
      <p className="eco-lead">
        {res.benchmark.label_en}{" "}
        <b className="num">{s.baseline_sofr_pct ?? res.params.sofr_pct}%</b>
        {" → "}
        <b className="num">{s.stressed_sofr_pct ?? "—"}%</b>
        {" · 선택 "}
        <b className="num">{s.shock_bp > 0 ? "+" : ""}{s.shock_bp}bp</b>
        {delta !== null ? <> · 현재 대비 추가 연간 이자 <b className="num">{delta > 0 ? "+" : ""}{usdM(delta)}</b></> : " · 계산 가능한 이자 변화 없음"}
      </p>
      {st ? (
        <div className="stress-card">
          <div className={`stress-pill stress-${st.level}`}>{STRESS_LABEL_KO[st.level]}</div>
          {st.level === "critical" ? <p className="fine warn-line">심각한 재무 압박 — 시나리오 추정 (파산·부도 판정 아님)</p> : null}
          <dl className="facts">
            <div><dt>Δ이자 / 연환산 OCF</dt><dd className="num">{st.score_delta_over_ocf != null ? `${(st.score_delta_over_ocf * 100).toFixed(1)}%` : "—"}</dd></div>
            <div><dt>OCF/이자 커버리지</dt><dd className="num">{multipleChange(st.baseline_coverage, st.stressed_coverage) || "—"}</dd></div>
            <div><dt>임계 SOFR (분석용)</dt><dd className="num">{st.critical_sofr_pct != null ? `${st.critical_sofr_pct.toFixed(2)}% (+${st.critical_shock_bp?.toFixed(0)}bp)` : "산정 불가"}</dd></div>
            <div><dt>임계까지</dt><dd className="num">{st.bp_to_critical != null ? `${st.bp_to_critical > 0 ? "+" : ""}${st.bp_to_critical.toFixed(0)}bp` : "—"}</dd></div>
          </dl>
          <p className="fine">{st.metric_trigger || st.critical_trigger || THRESHOLDS.definition}</p>
        </div>
      ) : null}
      <dl className="eco-grid">
        {items.map(([k, v, tip]) => (
          <div key={k} data-tip={tip}><dt>{k}</dt><dd className="num">{v}</dd></div>
        ))}
      </dl>
      <div className="cmp-block">
        <h4 className="lbl" style={{ marginTop: 10 }}>현재 대비 변화 <span className="lbl-aside">vs +0bp</span></h4>
        <p className="fine">이전 슬라이더 값(+300bp 등)이 아니라, 항상 <b>현재 기준 (+0bp)</b>과 <b>선택 시나리오</b>를 같은 데이터·모델로 비교합니다.</p>
        {vsBaseline ? (
          <div className="cmp-body">
            <dl className="facts">
              <div><dt>현재 기준 (+0bp)</dt><dd className="num">{vsBaseline.baseline.summary.baseline_sofr_pct ?? res.params.sofr_pct}% · 추가 이자 {usdM(vsBaseline.baseline.summary.total_incremental_interest_usd_m ?? 0)}</dd></div>
              <div><dt>선택 시나리오</dt><dd className="num">{s.shock_bp > 0 ? "+" : ""}{s.shock_bp}bp · {s.stressed_sofr_pct ?? "—"}%</dd></div>
              <div><dt>현재 대비 변화 (bp)</dt><dd className="num">{vsBaseline.dBp > 0 ? "+" : ""}{vsBaseline.dBp}bp</dd></div>
              <div><dt>현재 대비 추가 이자</dt><dd className="num">{vsBaseline.dInt > 0 ? "+" : ""}{usdM(vsBaseline.dInt)}</dd></div>
              <div><dt>OCF/이자 커버리지</dt><dd className="num">{multipleChange(vsBaseline.baseline.origin_stress?.baseline_coverage, vsBaseline.scenario.origin_stress?.stressed_coverage) || "산정 불가"}</dd></div>
              {vsBaseline.scoreRelPct != null ? <div><dt>Δ이자/OCF 상대변화</dt><dd className="num">{`${vsBaseline.scoreRelPct > 0 ? "+" : ""}${vsBaseline.scoreRelPct.toFixed(1)}%`}</dd></div> : null}
              <div><dt>CoreWeave 스트레스</dt><dd>{STRESS_LABEL_KO[vsBaseline.baseline.origin_stress?.level || "insufficient"]} → {STRESS_LABEL_KO[vsBaseline.scenario.origin_stress?.level || "insufficient"]}</dd></div>
              <div><dt>심각 기업 수</dt><dd className="num">{vsBaseline.critBase} → {vsBaseline.critScen}</dd></div>
              <div><dt>섹터 스트레스</dt><dd className="num">{vsBaseline.sectorBase} → {vsBaseline.sectorScen}</dd></div>
              <div><dt>새로 '심각' 단계 (vs 0bp)</dt><dd>{vsBaseline.newlyCrit.length ? vsBaseline.newlyCrit.slice(0, 6).map((id) => { const x = net.nodes.find((n) => n.id === id); return x ? displayName(x) : id; }).join(", ") : "없음"}</dd></div>
            </dl>
            {vsBaseline.zeroChange ? <p className="fine">+0bp 선택 — 현재 기준 대비 변화는 0입니다.</p> : null}
            <p className="eco-lead">{vsBaseline.diff.summary_ko}</p>
          </div>
        ) : null}
      </div>
      <p className="note">관계는 있어도 재무 손실로 세지 않습니다. 행성 균열은 분석용 스트레스 밴드에만 연동되며 부도 예측이 아닙니다.</p>
    </div>
  );
}

function fmtPx(q: QuoteItem): string {
  if (q.price === null || q.price === undefined) return "—";
  if (q.currency === "KRW") return `${Math.round(q.price).toLocaleString("ko-KR")}원`;
  return `$${q.price.toFixed(2)}`;
}
function fmtChg(q: QuoteItem): string {
  if (q.change_pct === null || q.change_pct === undefined) return "—";
  const s = q.change_pct > 0 ? "+" : q.change_pct < 0 ? "−" : "";
  return `${s}${Math.abs(q.change_pct).toFixed(2)}%`;
}

/** Short rail labels — full status_ko stays in the detail panel. */
function shortQuoteStatus(q: QuoteItem | undefined, listed: boolean): string {
  if (!listed) return "비상장";
  const st = q?.status;
  if (st === "ok" || st === "stale" || st === "partial") return "시세 있음";
  if (st === "unlisted") return "비상장";
  if (st === "not_supported") return "미지원";
  if (st === "no_key") return "키 없음";
  if (st === "pending") return "대기";
  return "미수집";
}

function MarketRail({ p }: { p: Props }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<"pct" | "name" | "abs">("pct");
  const [exFilter, setExFilter] = useState<"all" | "US" | "KR">("all");
  const term = q.trim().toLowerCase();
  const byId = useMemo(() => new Map((p.quotes?.items || []).map((i) => [i.entity, i])), [p.quotes]);
  const rows = useMemo(() => {
    const listed = p.net.nodes.filter((n) => n.listed);
    const filtered = listed.filter((n) => {
      const qq = byId.get(n.id);
      if (exFilter === "US" && !(n.exchange === "NYSE" || n.exchange === "Nasdaq" || n.exchange === "NASDAQ")) return false;
      if (exFilter === "KR" && !(n.exchange === "KOSPI" || n.exchange === "KOSDAQ" || n.exchange === "KRX")) return false;
      if (!term) return true;
      return n.name.toLowerCase().includes(term) || (n.name_ko || "").includes(term) || (n.ticker || "").toLowerCase().includes(term);
    });
    filtered.sort((a, b) => {
      const qa = byId.get(a.id), qb = byId.get(b.id);
      if (sort === "name") return a.name.localeCompare(b.name);
      const pa = qa?.change_pct, pb = qb?.change_pct;
      if (sort === "abs") {
        const ca = qa?.change, cb = qb?.change;
        if (ca == null && cb == null) return a.name.localeCompare(b.name);
        if (ca == null) return 1;
        if (cb == null) return -1;
        return Math.abs(cb) - Math.abs(ca);
      }
      if (pa == null && pb == null) return a.name.localeCompare(b.name);
      if (pa == null) return 1;
      if (pb == null) return -1;
      return pb - pa;
    });
    return filtered;
  }, [p.net.nodes, byId, term, sort, exFilter]);
  const priced = rows.filter((n) => byId.get(n.id)?.price != null).length;
  return (
    <>
      <section className="lp-sec">
        <h3 className="lbl">Market Performance <span className="lbl-aside">관측 시세</span></h3>
        <p className="note">AI 인프라 생태계 상장사의 <b>실제 주가</b>입니다. 금리 충격·차환 시나리오와 무관합니다.</p>
        <p className="fine num">{priced}/{rows.length} 시세 · {p.quotes?.generated_at ? p.quotes.generated_at.replace("T", " ").slice(0, 16) : "—"}</p>
        <button type="button" className="btn-text" onClick={p.onRefreshQuotes} disabled={p.quotesBusy} data-tip={refreshTip(!!p.quotesLive)}>
          <IconReset size={11} /> {refreshLabel(!!p.quotesLive, p.quotesBusy)}
        </button>
        <div className="seg seg-wrap" role="group" aria-label="거래소">
          {([["all", "전체"], ["US", "US"], ["KR", "KR"]] as const).map(([id, lab]) => (
            <button key={id} type="button" className={exFilter === id ? "is-on" : ""} onClick={() => setExFilter(id)}>{lab}</button>
          ))}
        </div>
        <div className="seg seg-wrap" role="group" aria-label="정렬">
          {([["pct", "등락률"], ["abs", "변동폭"], ["name", "이름"]] as const).map(([id, lab]) => (
            <button key={id} type="button" className={sort === id ? "is-on" : ""} onClick={() => setSort(id)}>{lab}</button>
          ))}
        </div>
        <label className="search">
          <IconSearch size={13} />
          <input type="search" placeholder="기업 · 티커" value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
      </section>
      <section className="lp-sec lp-quotes">
        <ul className="q-rail">
          {rows.map((n) => {
            const qq = byId.get(n.id);
            const up = (qq?.change_pct ?? 0) > 0, down = (qq?.change_pct ?? 0) < 0;
            const has = qq?.price != null;
            return (
              <li key={n.id}>
                <button type="button" className={`q-row ${has ? "" : "is-empty"} ${p.selectedId === n.id ? "is-on" : ""} ${up ? "is-up" : down ? "is-down" : ""}`}
                  onClick={() => p.onSelect(n.id)}>
                  <span className="q-name">
                    <span>{n.name}</span>
                    <span className="q-meta num">{qq?.ticker || n.ticker || "—"} · {n.exchange || "—"}</span>
                  </span>
                  {has ? (
                    <>
                      <span className="q-px num">{fmtPx(qq!)}</span>
                      <span className={`q-ch num ${up ? "is-up" : down ? "is-down" : ""}`}>{fmtChg(qq!)}</span>
                    </>
                  ) : <span className="q-na">{shortQuoteStatus(qq, !!n.listed)}</span>}
                </button>
              </li>
            );
          })}
        </ul>
        {p.quotes?.note ? <p className="hint">{p.quotes.note}</p> : null}
      </section>
    </>
  );
}

export function ScenarioBuilder(p: Props) {
  const [q, setQ] = useState("");
  const [openClass, setOpenClass] = useState<string | null>(null);
  const [adv, setAdv] = useState(false);
  const [refiOpen, setRefiOpen] = useState(false);
  const [guide, setGuide] = useState(false);
  const fin = p.net.financials;
  const insts = fin.instruments;
  const inst = insts.find((x) => x.id === p.form.instrumentId) as Instrument;
  const sofr = p.form.sofr ?? fin.market_inputs.sofr_pct;
  const ex = useMemo(() => { try { return existingRate(inst, p.form.basis, sofr); } catch { return null; } }, [inst, p.form.basis, sofr]);
  const term = q.trim().toLowerCase();
  const match = (n: Network["nodes"][number]) => !term || n.name.toLowerCase().includes(term) || (n.name_ko || "").includes(term) || (n.ticker || "").toLowerCase().includes(term);
  const bm = BENCHMARKS[p.shock.benchmark];

  const groupsByKind = useMemo(() => {
    const m = new Map<string, Instrument[]>();
    for (const x of insts) { if (!m.has(x.kind)) m.set(x.kind, []); m.get(x.kind)!.push(x); }
    return [...m.entries()];
  }, [insts]);

  const floatingPrin = useMemo(() => insts
    .filter((i) => i.rate_type === "floating" && (i.base_rate || "").toUpperCase() === "SOFR" && (i.principal_usd_m || 0) > 0)
    .reduce((s, i) => s + (i.principal_usd_m || 0), 0), [insts]);

  const entityRows = (groups: string[] | null) => p.net.nodes.filter((n) => (!groups || groups.includes(n.group)) && match(n)).map((n) => {
    const st = p.visuals?.[n.id]?.status;
    return (
      <li key={n.id}>
        <button type="button" className={`ent ${p.selectedId === n.id ? "is-on" : ""}`} onClick={() => p.onSelect(n.id)}>
          <span className={`dot g-${n.group}`} />
          <span className="ent-name">{n.name}</span>
          <span className="ent-tk num">{n.ticker || "비상장"}</span>
          {st && st !== "normal" && p.mode === "shock" ? <span className={`sdot s-${STATUS_DOT[st] || "muted-o"}`} /> : <span className="sdot" />}
        </button>
      </li>
    );
  });

  if (p.mode === "market") {
    return (
      <aside className="lp" aria-label="Market 시세">
        <LpResize />
        <MarketRail p={p} />
      </aside>
    );
  }

  return (
    <aside className="lp" aria-label={p.mode === "shock" ? "금리 충격 시나리오" : "네트워크 필터"}>
      <LpResize />
      {p.mode === "shock" ? (
      <section className="lp-sec">
        <h3 className="lbl">Interest Rate Shock <span className="lbl-aside">생태계 전염</span></h3>
        <p className="note">CoreWeave 금리·채무불이행과 섹터 자금경색을 분리·결합해 봅니다. 행성은 모델상 스트레스이며 확정 부도가 아닙니다.</p>

        <div className="f-row">
          <span className="f-lbl">{HELP.crisisMode.term} <Tip text={helpTip("crisisMode")} /></span>
          <div className="seg seg-wrap" role="group" aria-label="위기 시나리오">
            {CRISIS_MODES.map((m) => (
              <button key={m.id} type="button" className={p.shock.crisisMode === m.id ? "is-on" : ""}
                onClick={() => p.onShock({ crisisMode: m.id })}>{m.label}</button>
            ))}
          </div>
        </div>

        {(p.shock.crisisMode === "financing" || p.shock.crisisMode === "combined") ? (
          <div className="f-row">
            <span className="f-lbl">{HELP.refiAvailability.term}</span>
            <div className="seg" role="group">
              {FUNDING.map((f) => (
                <button key={f} type="button" className={p.shock.refiAvailability === f ? "is-on" : ""}
                  onClick={() => p.onShock({ refiAvailability: f })}>{f}</button>
              ))}
            </div>
            <span className="f-lbl" style={{ marginTop: 6 }}>{HELP.projectFinancing.term}</span>
            <div className="seg" role="group">
              {FUNDING.map((f) => (
                <button key={`p-${f}`} type="button" className={p.shock.projectFinancing === f ? "is-on" : ""}
                  onClick={() => p.onShock({ projectFinancing: f })}>{f}</button>
              ))}
            </div>
            <div className="seg" role="group" style={{ marginTop: 6 }} aria-label="시계">
              {([12, 24] as const).map((h) => (
                <button key={h} type="button" className={p.shock.horizonMonths === h ? "is-on" : ""}
                  onClick={() => p.onShock({ horizonMonths: h })}>{h}개월</button>
              ))}
            </div>
          </div>
        ) : null}

        <div className="f-row">
          <label htmlFor="f-benchmark" className="f-lbl">{HELP.benchmark.term} <Tip text={helpTip("benchmark")} /></label>
          <select id="f-benchmark" value={p.shock.benchmark} onChange={(e) => p.onShock({ benchmark: e.target.value as RateBenchmark })}>
            {BM_OPTS.map((id) => <option key={id} value={id}>{BENCHMARKS[id].label}</option>)}
          </select>
          <p className="fine">{bm.plain}</p>
        </div>

        <div className="f-row">
          <span className="f-lbl">{HELP.shockBp.term} <Tip text={helpTip("shockBp")} />
            <span className="shock-val num">{p.shock.shockBp > 0 ? "+" : ""}{p.shock.shockBp}bp</span>
          </span>
          <input id="f-shockBp" className="shock-slider" type="range" min={-300} max={700} step={25}
            value={p.shock.shockBp} onChange={(e) => p.onShock({ shockBp: Number(e.target.value) })}
            aria-valuetext={`${p.shock.shockBp} basis points`} />
          <div className="seg seg-wrap" role="group" aria-label="금리 충격 빠른 선택">
            {SHOCK_PRESETS.map((bp) => (
              <button key={bp} type="button" className={p.shock.shockBp === bp ? "is-on" : ""}
                onClick={() => p.onShock({ shockBp: bp })}>{bp > 0 ? "+" : ""}{bp}</button>
            ))}
          </div>
          <div className="kvlist" style={{ marginTop: 4 }}>
            <Row k="shockBp" label="직접 입력">
              <NumField id="f-shockBpNum" value={p.shock.shockBp} onChange={(v) => p.onShock({ shockBp: v ?? 0 })}
                min={-700} max={700} step={25} suffix="bp" width={88} />
            </Row>
          </div>
        </div>

        <dl className="facts">
          <div><dt>SOFR 연동 공시 잔액</dt><dd className="num" data-tip={korUsd(floatingPrin)}>{usdM(floatingPrin)}</dd></div>
          <div><dt>SOFR 관측</dt><dd className="num">{fin.market_inputs.sofr_pct}% · {fin.market_inputs.sofr_date}</dd></div>
          <div><dt>적용 방식</dt><dd>{bm.applies_to === "sofr_floating" ? "변동금리 이자 민감도" : "국채 — SOFR 이자 자동 미적용"}</dd></div>
          <div><dt>스트레스 기준금리</dt><dd className="num">{(p.shockResult?.summary.baseline_sofr_pct ?? fin.market_inputs.sofr_pct)}% → {p.shockResult?.summary.stressed_sofr_pct ?? "—"}%</dd></div>
        </dl>

        {p.shockPending ? <p className="digest-pending">입력이 바뀌어 다시 계산 중입니다 — 아래는 직전 입력의 결과입니다.</p> : null}
        <div className={p.shockPending ? "is-pending" : ""}><EcosystemSummary res={p.shockResult} net={p.net} /></div>
      </section>
      ) : (
        <section className="lp-sec">
          <h3 className="lbl">Network View <span className="lbl-aside">다중심 생태계</span></h3>
          <p className="note">공개자료로 확인된 연결만 표시합니다. 기업을 선택한 뒤 우측에서 <b>이 회사를 초점으로</b>를 누르면 Direct/Indirect 집계와 경로 탐색 기준이 바뀝니다. 주가는 Market, 금리 금액 충격은 Shock(CoreWeave 공시 변동금리)입니다.</p>
        </section>
      )}

      {p.mode === "shock" ? (
      <section className="lp-sec">
        <button type="button" className="disclosure" aria-expanded={refiOpen} onClick={() => setRefiOpen((o) => !o)}>
          <IconChevron size={11} className="chev" /> 상세 · 개별 차입금 차환 분석
        </button>
        {refiOpen ? (
          <div className="refi-block">
            <p className="note">특정 CoreWeave 차입금 하나를 새 금리로 갈아탄다고 가정할 때의 상세 계산입니다. 위 생태계 충격과는 별개입니다.</p>
            <div className="f-row">
              <label htmlFor="f-instrument" className="f-lbl">{HELP.instrument.term} <Tip text={helpTip("instrument")} /></label>
              <select id="f-instrument" value={p.form.instrumentId} onChange={(e) => p.onForm({ instrumentId: e.target.value, amount: null, refiDate: null })}>
                {groupsByKind.map(([kind, list]) => (
                  <optgroup key={kind} label={KIND_KO[kind as Instrument["kind"]]}>
                    {list.filter(refinanceable).map((x) => (
                      <option key={x.id} value={x.id}>{x.name} · {x.principal_usd_m !== null ? usdM(x.principal_usd_m) : "잔액 미공시"}{x.maturity ? ` · ${x.maturity.slice(0, 7)}` : ""}</option>
                    ))}
                  </optgroup>
                ))}
              </select>
              <button type="button" className="btn-text" onClick={() => p.onOpenContract(inst.id)}>계약 정보 보기 →</button>
            </div>
            <dl className="facts">
              <div><dt>잔액 (6.30)</dt><dd className="num" data-tip={inst.principal_usd_m !== null ? korUsd(inst.principal_usd_m) : inst.principal_note}>{usdM(inst.principal_usd_m)}</dd></div>
              <div><dt>만기</dt><dd className="num">{inst.maturity ? inst.maturity.slice(0, 7) : "미공시"}</dd></div>
              <div><dt>기존 금리</dt><dd className="num" data-tip={ex ? `${ex.formula} · ${ex.status}` : "확인 불가"}>{ex ? `${ex.rate_pct}%` : "—"}</dd></div>
            </dl>
            <div className="f-row">
              <span className="f-lbl">{HELP.newRate.term} <Tip text={helpTip("newRate")} /></span>
              <div className="rate-pick">
                <div className="seg" role="radiogroup" aria-label="금리 빠른 선택">
                  {RATE_PRESETS.map((r) => (
                    <button key={r} type="button" role="radio" aria-checked={p.form.newRate === r} className={p.form.newRate === r ? "is-on" : ""} onClick={() => p.onForm({ newRate: r })}>{r}%</button>
                  ))}
                </div>
                <NumField id="f-newRate" value={p.form.newRate} onChange={(v) => p.onForm({ newRate: v ?? 12 })} min={0} max={40} suffix="%" />
              </div>
            </div>
            <div className="kvlist">
              <Row k="basis" status={ex?.status}>
                <span className="seg seg-sm">
                  <button type="button" className={p.form.basis === "stated" ? "is-on" : ""} onClick={() => p.onForm({ basis: "stated" })}>표면</button>
                  <button type="button" className={p.form.basis === "effective" ? "is-on" : ""} onClick={() => p.onForm({ basis: "effective" })}>유효</button>
                </span>
              </Row>
              <Row k="success" status="ASSUMED"><NumField id="f-success" value={Math.round(p.form.success * 100)} onChange={(v) => p.onForm({ success: (v ?? 100) / 100 })} min={0} max={100} step={5} suffix="%" /></Row>
            </div>
            <button type="button" className="disclosure" aria-expanded={adv} onClick={() => setAdv((a) => !a)}>
              <IconChevron size={11} className="chev" /> 고급 변수 · 투자 영향 가정
            </button>
            {adv ? (
              <div className="kvlist adv">
                <Row k="amount" status="ASSUMED"><NumField id="f-amount" value={p.form.amount} onChange={(v) => p.onForm({ amount: v })} min={1} step={50} allowBlank placeholder={inst.principal_usd_m !== null ? String(inst.principal_usd_m) : "입력"} suffix="$M" width={92} /></Row>
                <Row k="fee" status="ASSUMED"><NumField id="f-fee" value={p.form.fee} onChange={(v) => p.onForm({ fee: v ?? 0 })} min={0} max={10} step={0.25} suffix="%" /></Row>
                <Row k="tenor" status="ASSUMED"><NumField id="f-tenor" value={p.form.tenor} onChange={(v) => p.onForm({ tenor: Math.round(v ?? 5) })} min={1} max={15} step={1} suffix="년" /></Row>
                <Row k="sofr" label={`SOFR (${fin.market_inputs.sofr_date})`} status={p.form.sofr === null ? "VERIFIED" : "ASSUMED"}><NumField id="f-sofr" value={p.form.sofr} onChange={(v) => p.onForm({ sofr: v })} min={0} max={20} step={0.05} allowBlank placeholder={String(fin.market_inputs.sofr_pct)} suffix="%" /></Row>
                <Row k="capexAbsorb" status="ASSUMED"><NumField id="f-capexAbsorb" value={p.form.capexAbsorb} onChange={(v) => p.onForm({ capexAbsorb: v })} min={0} max={100} step={5} allowBlank placeholder="미입력" suffix="%" /></Row>
                <Row k="gpuShare" status="ASSUMED"><NumField id="f-gpuShare" value={p.form.gpuShare} onChange={(v) => p.onForm({ gpuShare: v })} min={0} max={100} step={5} allowBlank placeholder="미입력" suffix="%" /></Row>
              </div>
            ) : null}
            <p className="summary">{p.summary}</p>
            {p.blockReason ? <p className="note crit">{p.blockReason}</p> : null}
            <button type="button" className="btn-primary" onClick={p.onRunRefi} disabled={!p.canRunRefi || p.busy}>
              {p.busy ? "Running…" : "Run Refinancing"}<span>개별 차입금 상세</span>
            </button>
            {p.stale ? <p className="note warn">입력이 바뀌었습니다. 결과는 이전 실행 기준입니다.</p> : null}
          </div>
        ) : null}
      </section>
      ) : null}

      <section className="lp-sec">
        <h3 className="lbl">Network Filter <span className="lbl-aside" data-tip="화면 표시만 바뀌며 계산에는 영향이 없습니다">표시만</span></h3>
        <label className="search">
          <IconSearch size={13} />
          <input id="entity-search" type="search" placeholder="기업 · 금융기관 · 티커" value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
        {term ? <ul className="ent-list">{entityRows(null)}</ul> : (
          <ul className="cls-list">
            {CLASSES.map((c) => {
              const cnt = p.net.nodes.filter((n) => c.groups.includes(n.group)).length;
              const hidden = c.groups.every((g) => p.hiddenGroups.includes(g));
              return (
                <li key={c.id}>
                  <div className={`cls ${openClass === c.id ? "is-open" : ""}`}>
                    <input type="checkbox" checked={!hidden} onChange={() => c.groups.forEach((g) => p.onToggleGroup(g))} aria-label={`${c.label} 표시`} />
                    <button type="button" className="cls-b" onClick={() => setOpenClass((x) => (x === c.id ? null : c.id))} aria-expanded={openClass === c.id}>
                      <span className={`dot g-${c.groups[0]}`} /><span>{c.label}</span><span className="num cnt">{cnt}</span><IconChevron size={11} className="chev" />
                    </button>
                  </div>
                  {openClass === c.id ? <ul className="ent-list">{entityRows(c.groups)}</ul> : null}
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="lp-sec">
        <button type="button" className="disclosure" aria-expanded={guide} onClick={() => setGuide((g) => !g)}>
          <IconChevron size={11} className="chev" /> 용어 · 데이터 구분
        </button>
        {guide ? (
          <div className="guide">
            <dl>{GLOSSARY.map((x) => (<div key={x.term}><dt>{x.term}</dt><dd>{x.plain}</dd></div>))}</dl>
          </div>
        ) : null}
      </section>
    </aside>
  );
}
