import type { ReactNode } from "react";
import type { NetworkStats } from "../types";
import { IconPanel } from "./Icons";

export type View = "map" | "sources";
export type Mode = "network" | "market" | "shock";

/** Header: brand, view switch, dataset counts (computed from the data, never typed in), market strip. */
const MODES: { id: Mode; label: string; tip: string }[] = [
  { id: "network", label: "Network", tip: "NETWORK VIEW · 공개자료로 확인된 기업·금융기관 연결 구조" },
  { id: "market", label: "Market", tip: "MARKET VIEW · 관측된 주가·국채·신용스프레드 (시나리오 가정과 별개)" },
  { id: "shock", label: "Shock", tip: "SHOCK VIEW · 금리 충격 시 직접 노출·잠재 전달 경로 (가상 시나리오 · 예측 아님)" },
];

export function TopBar({ view, onView, mode, onMode, children, panelOpen, onTogglePanel, stats, brand, brandSub }: {
  view: View; onView: (v: View) => void; mode: Mode; onMode: (m: Mode) => void; children?: ReactNode;
  panelOpen: boolean; onTogglePanel: () => void; stats: NetworkStats | null;
  /** Mode-dependent product name (e.g. 코어위브 Contagion Map / AI DC Contagion Map). */
  brand: string;
  brandSub: string;
}) {
  const items: [string, number | undefined, string][] = [
    ["Entities", stats?.entities, "공개자료로 확인되어 데이터에 등록된 기업·기관 수 (CoreWeave 포함). 생태계 전체 규모가 아닙니다."],
    ["Direct", stats?.direct, "CoreWeave와 직접 연결된(1-hop) 기업·기관 수"],
    ["Indirect", stats?.indirect, "다른 기업을 거쳐 연결된(2-hop 이상) 기업·기관 수"],
    ["Contracts", stats?.financing_contracts, "공시로 확인된 CoreWeave 금융계약(대출·채권·전환사채·리볼버) 수. 공급사 금융은 제외"],
    ["Industrial", stats?.industrial_relationships, "확인된 산업 관계(공급·고객·데이터센터·약정) 수"],
  ];
  return (
    <header className="hdr">
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
        <button type="button" className={view === "sources" ? "is-on" : ""} onClick={() => onView("sources")}>Data &amp; Sources</button>
      </nav>
      <dl className="hdr-stats" aria-label="데이터 집계">
        {items.map(([k, v, t]) => (
          <div key={k} data-tip={t}><dt>{k}</dt><dd className="num">{v ?? "—"}</dd></div>
        ))}
      </dl>
      <div className="hdr-mid">{children}</div>
      <span className="hdr-flag" data-tip="금리 충격·차환 가정은 사용자 시나리오입니다. 관측 시장 데이터와 구분되며 예측·투자 의견이 아닙니다.">SCENARIO · 예측 아님</span>
      <button type="button" className={`ibtn ${panelOpen ? "is-on" : ""}`} onClick={onTogglePanel} data-tip={panelOpen ? "분석 패널 접기" : "분석 패널 열기"} aria-label="분석 패널"><IconPanel size={14} /></button>
    </header>
  );
}
