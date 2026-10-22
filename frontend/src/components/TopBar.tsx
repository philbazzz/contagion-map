import type { ReactNode } from "react";
import type { NetworkStats } from "../types";
import { IconPanel } from "./Icons";

export type View = "map" | "sources";
export type Mode = "network" | "market" | "shock";

/** Header: row 1 = brand · modes · counts · panel toggle; row 2 = ecosystem switch + what the screen is scoped to. */
const MODES: { id: Mode; label: string; tip: string }[] = [
  { id: "network", label: "Network", tip: "NETWORK · 공개자료로 확인된 기업·금융기관 연결 구조" },
  { id: "market", label: "Market", tip: "MARKET · 관측된 주가·국채 (시나리오 가정과 별개)" },
  { id: "shock", label: "Shock", tip: "SHOCK · 사용자가 정한 충격의 전달 경로 (가상 시나리오 · 예측 아님)" },
];

export interface StatDef { key: string; label: string; value: number | undefined; tip: string }

export function TopBar({ view, onView, mode, onMode, children, panelOpen, onTogglePanel, statDefs, brand, brandSub, scope, onGuide }: {
  view: View; onView: (v: View) => void; mode: Mode; onMode: (m: Mode) => void;
  /** Ecosystem selector (row 2). */
  children?: ReactNode;
  panelOpen: boolean; onTogglePanel: () => void;
  /** Counts with ecosystem-specific definitions (so labels and tooltips never describe another ecosystem). */
  statDefs: StatDef[];
  brand: string;
  brandSub: string;
  /** Plain description of what the counts and panels refer to. */
  scope: ReactNode;
  onGuide?: () => void;
}) {
  return (
    <header className="hdr">
      <div className="hdr-row1">
        <div className="hdr-brand">
          <span className="wm">{brand}</span>
          <span className="wm-sub">{brandSub}</span>
        </div>
        <nav className="hdr-nav" aria-label="화면 전환">
          <span className="mode-seg" role="tablist" aria-label="지도 모드">
            {MODES.map((m) => (
              <button key={m.id} type="button" role="tab" aria-selected={view === "map" && mode === m.id} data-tip={m.tip}
                className={`mode-${m.id} ${view === "map" && mode === m.id ? "is-on" : ""}`} onClick={() => { onView("map"); onMode(m.id); }}>{m.label}</button>
            ))}
          </span>
          <button type="button" className={view === "sources" ? "is-on" : ""} aria-pressed={view === "sources"} onClick={() => onView("sources")}>Data &amp; Sources</button>
        </nav>
        <dl className="hdr-stats" aria-label="데이터 집계">
          {statDefs.map((s) => (
            <div key={s.key} data-tip={s.tip} tabIndex={0} aria-label={`${s.label} ${s.value ?? "—"}. ${s.tip}`}><dt>{s.label}</dt><dd className="num">{s.value ?? "—"}</dd></div>
          ))}
        </dl>
        <button type="button" className={`ibtn hdr-panel ${panelOpen ? "is-on" : ""}`} onClick={onTogglePanel} data-tip={panelOpen ? "분석 패널 접기" : "분석 패널 열기"} aria-label="분석 패널" aria-pressed={panelOpen}><IconPanel size={14} /></button>
      </div>
      <div className="hdr-row2">
        {children}
        <p className="hdr-scope">{scope}</p>
        {onGuide ? <button type="button" className="hdr-guide" onClick={onGuide} aria-label="사용 안내 열기">안내</button> : null}
        <span className="hdr-flag" data-tip="충격·차환 값은 사용자 시나리오입니다. 관측 시장 데이터와 구분되며 예측·투자 의견이 아닙니다.">SCENARIO · 예측 아님</span>
      </div>
    </header>
  );
}
