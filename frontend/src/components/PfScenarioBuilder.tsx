import { useEffect, useMemo, useRef, useState } from "react";
import type { Network, NodeVisual, QuoteItem, QuotesOverview } from "../types";
import type { PfShockForm, PfShockResult, PfProjectsFile } from "../pf/types";
import {
  CAPEX_PRESETS, CW_DISTRESS, GPU_PRESETS,
  PF_AMOUNT_FILTERS, PF_DIRECTNESS_FILTERS, PF_EVIDENCE_FILTERS,
  PF_CLASSES, PF_INSTITUTION_FILTERS, PF_INSTRUMENT_FILTERS, PF_ROLE_FILTERS, PF_STAGE_FILTERS, RATE_PRESETS,
} from "../pf/scenario";
import type { CoreWeaveDistress } from "../pf/types";
import { displayName, projectDisplayName } from "../lib/displayName";
import { buildSearchIndex, searchCompanies, type SearchHit } from "../lib/companySearch";
import { IconChevron, IconReset, IconSearch } from "./Icons";
import { LpResize } from "./LpResize";
import { PfAffectedCompaniesPanel } from "./PfAffectedCompanies";
import { PfShockDigest } from "./PfShockDigest";
import { hasLiveRelation } from "../lib/relationState";
import { refreshLabel } from "../lib/labels";
import type { Mode } from "./TopBar";

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
function isKrEx(ex: string | null | undefined): boolean {
  const u = (ex || "").toUpperCase();
  return u === "KOSPI" || u === "KOSDAQ" || u === "KRX";
}

const STAGE_KO: Record<string, string> = {
  planned: "계획", pre_construction: "착공 전", under_construction: "공사 중", expanding: "증설",
  completed_permit: "준공·허가", stabilized_operating: "안정 운영", operating_collateral: "운영 담보",
};

function ShockImpactBlock({
  result, selectedId, onSelect,
}: {
  result: PfShockResult | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const [collapsed, setCollapsed] = useState(false);
  return (
    <PfAffectedCompaniesPanel
      result={result}
      selectedId={selectedId}
      onSelectCompany={(id) => onSelect(id)}
      collapsed={collapsed}
      onToggleCollapse={() => setCollapsed((c) => !c)}
    />
  );
}

interface Props {
  mode: Mode;
  net: Network;
  projects: PfProjectsFile;
  pfShock: PfShockForm;
  onPfShock: (p: Partial<PfShockForm>) => void;
  shockResult: PfShockResult | null;
  quotes: QuotesOverview | null;
  quotesBusy: boolean;
  onRefreshQuotes: () => void;
  quotesLive?: boolean;
  hiddenGroups: string[];
  onToggleGroup: (g: string) => void;
  visuals: Record<string, NodeVisual> | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
  /** Search result → select + camera locate + pin visibility. */
  onLocate?: (id: string) => void;
  onClearSearchPins?: () => void;
  onClearSelection?: () => void;
  /** Inputs changed and the result shown is from the previous inputs. */
  shockPending?: boolean;
}

const STATUS_DOT: Record<string, string> = {
  elevated: "warn", high: "warn", critical: "warn", unknown: "muted-o", normal: "muted-o",
};

export function PfScenarioBuilder(p: Props) {
  const [q, setQ] = useState("");
  const [guide, setGuide] = useState(false);
  const [filterRole, setFilterRole] = useState<string>("all");
  const [filterEvidence, setFilterEvidence] = useState<string>("all");
  const [filterInstitution, setFilterInstitution] = useState<string>("all");
  const [filterStage, setFilterStage] = useState<string>("all");
  const [filterInstrument, setFilterInstrument] = useState<string>("all");
  const [filterAmount, setFilterAmount] = useState<string>("all");
  const [filterDirectness, setFilterDirectness] = useState<string>("all");
  const [hopDepth, setHopDepth] = useState<1 | 2>(1);
  const [openClass, setOpenClass] = useState<string | null>(null);
  const [activeHit, setActiveHit] = useState(0);
  const composingRef = useRef(false);
  const searchListRef = useRef<HTMLUListElement>(null);

  const searchIndex = useMemo(() => buildSearchIndex(p.net.nodes), [p.net.nodes]);
  const searchHits: SearchHit[] = useMemo(
    () => (q.trim() ? searchCompanies(searchIndex, q, 48) : []),
    [searchIndex, q],
  );
  const searching = q.trim().length > 0;

  useEffect(() => { setActiveHit(0); }, [q]);

  const locate = (id: string) => {
    (p.onLocate || p.onSelect)(id);
  };

  const clearSearch = () => {
    setQ("");
    setActiveHit(0);
    p.onClearSearchPins?.();
  };

  const onSearchKeyDown = (ev: { key: string; preventDefault: () => void; nativeEvent: { isComposing?: boolean } }) => {
    if (ev.nativeEvent.isComposing || composingRef.current) return;
    if (!searchHits.length) {
      if (ev.key === "Escape") clearSearch();
      return;
    }
    if (ev.key === "ArrowDown") {
      ev.preventDefault();
      setActiveHit((i) => Math.min(i + 1, searchHits.length - 1));
    } else if (ev.key === "ArrowUp") {
      ev.preventDefault();
      setActiveHit((i) => Math.max(i - 1, 0));
    } else if (ev.key === "Enter") {
      ev.preventDefault();
      // Ambiguous: only auto-nav when exact unique or single hit
      if (searchHits.length === 1 || (searchHits.filter((h) => h.rank === 0).length === 1 && searchHits[0].rank === 0)) {
        locate(searchHits.find((h) => h.rank === 0)?.id || searchHits[0].id);
      } else if (searchHits[activeHit]) {
        locate(searchHits[activeHit].id);
      }
    } else if (ev.key === "Escape") {
      ev.preventDefault();
      clearSearch();
    }
  };

  const term = q.trim().toLowerCase();
  const match = (n: Network["nodes"][number]) => {
    if (!term) return true;
    // Sidebar list filtering uses the same index ranks (full dataset search is in searchHits).
    return searchHits.some((h) => h.id === n.id);
  };

  const nodeLinks = (n: Network["nodes"][number]) =>
    p.net.edges.filter((e) => e.source === n.id || e.target === n.id);

  const roleMatch = (n: Network["nodes"][number]) => {
    if (filterRole === "all") return true;
    const f = PF_ROLE_FILTERS.find((x) => x.id === filterRole);
    if (!f || !f.match.length) return true;
    if (f.match.includes("__connection_pending__")) {
      return !hasLiveRelation(n, p.net, p.net.meta.as_of);
    }
    const roles = ((n as { roles?: string[] }).roles || []).map((r) => r.toLowerCase());
    const blob = [n.role, n.entity_type, n.group, ...roles].join(" ").toLowerCase();
    return f.match.some((m) => roles.includes(m) || blob.includes(m));
  };

  const institutionMatch = (n: Network["nodes"][number]) => {
    if (filterInstitution === "all") return true;
    const f = PF_INSTITUTION_FILTERS.find((x) => x.id === filterInstitution);
    if (!f || !f.groups.length) return true;
    return f.groups.includes(n.group);
  };

  const edgeFinanceMatch = (n: Network["nodes"][number]) => {
    const links = nodeLinks(n);
    if (filterStage === "all" && filterInstrument === "all" && filterAmount === "all" && filterDirectness === "all") {
      return true;
    }
    if (!links.length) return false;
    const stageF = PF_STAGE_FILTERS.find((x) => x.id === filterStage);
    const instF = PF_INSTRUMENT_FILTERS.find((x) => x.id === filterInstrument);
    return links.some((e) => {
      if (stageF && stageF.stages.length) {
        const st = (e as { financing_stage?: string }).financing_stage || "";
        if (!stageF.stages.includes(st)) return false;
      }
      if (instF && instF.match.length) {
        if (!instF.match.includes(e.relationship_type)) return false;
      }
      if (filterAmount === "disclosed") {
        const eok = (e as { amount_krw_eok?: number | null }).amount_krw_eok;
        if (eok == null && !(e.amount_note || "").match(/\d/)) return false;
        if ((e.amount_note || "").includes("금액 미공개") && eok == null) return false;
      }
      if (filterAmount === "undisclosed") {
        const eok = (e as { amount_krw_eok?: number | null }).amount_krw_eok;
        if (eok != null) return false;
        if (!(e.amount_note || "").includes("미공개") && !(e.amount_note || "").includes("미공시")) return false;
      }
      if (filterDirectness !== "all") {
        const path = (e as { participation_path?: string }).participation_path || "";
        const directness = (e as { participation_directness?: string }).participation_directness
          || (path.includes("간접") || (path.match(/→/g) || []).length >= 2 ? "indirect" : "direct");
        if (directness !== filterDirectness) return false;
      }
      return true;
    });
  };

  const evidenceMatch = (n: Network["nodes"][number]) => {
    if (filterEvidence === "all") return true;
    if (filterEvidence === "pending") {
      return !hasLiveRelation(n, p.net, p.net.meta.as_of);
    }
    const links = nodeLinks(n);
    if (filterEvidence === "verified") {
      return links.some((e) => e.source_status === "VERIFIED"
        || (e as { evidence_status?: string }).evidence_status === "기사상 참여 확인");
    }
    if (filterEvidence === "inferred") {
      return links.some((e) => e.source_status === "INFERRED");
    }
    return true;
  };

  const confirmedProjects = useMemo(() => {
    const ids = new Set(
      p.net.edges.map((e) => (e as { project_id?: string }).project_id).filter(Boolean) as string[],
    );
    return p.projects.projects.filter((pr) => ids.has(pr.id) || (pr as { financing_disclosed?: boolean }).financing_disclosed);
  }, [p.net.edges, p.projects.projects]);

  const pf = p.shockResult?.pf;
  const region = useMemo(() => new Map(p.net.nodes.map((n) => [n.id, (n as { region?: string }).region || "US"])), [p.net]);

  const isCompanyNode = (n: Network["nodes"][number]) => {
    if ((n as { is_company?: boolean }).is_company === false) return false;
    if (n.entity_type === "project" || n.entity_type === "operating_asset" || n.entity_type === "market_aggregate") return false;
    return true;
  };

  const passesFilters = (n: Network["nodes"][number]) =>
    isCompanyNode(n) && match(n) && roleMatch(n) && institutionMatch(n) && evidenceMatch(n) && edgeFinanceMatch(n);

  const companyCount = useMemo(
    () => p.net.nodes.filter((n) => passesFilters(n)).length,
    // eslint-disable-next-line react-hooks/exhaustive-deps -- filters close over state
    [p.net, term, filterRole, filterEvidence, filterInstitution, filterStage, filterInstrument, filterAmount, filterDirectness, p.pfShock.exposureFilter, p.pfShock.showKoreanPfOnly, p.pfShock.showUsKoreaOnly],
  );

  const selectedCompanyProjects = useMemo(() => {
    if (!p.selectedId) return [];
    const id = p.selectedId;
    const fromEdges = new Set<string>();
    for (const e of p.net.edges) {
      if (e.source !== id && e.target !== id) continue;
      const pid = (e as { project_id?: string }).project_id;
      if (pid) fromEdges.add(pid);
    }
    return p.projects.projects.filter((pr) =>
      fromEdges.has(pr.id)
      || pr.developer === id
      || pr.operator === id
      || pr.owner === id
      || pr.spv === id);
  }, [p.selectedId, p.net.edges, p.projects.projects]);

  const entityRows = (groups: string[] | null) =>
    p.net.nodes
      .filter((n) => (!groups || groups.includes(n.group)) && passesFilters(n))
      .filter((n) => {
        if (!isCompanyNode(n)) return false;
        // While searching, show full ranked matches — do not collapse to 1-hop neighborhood.
        if (searching) return true;
        if (p.selectedId && hopDepth >= 1) {
          // When a company is selected, optionally limit list to 1–2 hop neighborhood
          const id = p.selectedId;
          if (n.id === id) return true;
          const one = new Set<string>();
          for (const e of p.net.edges) {
            if (e.source === id) one.add(e.target);
            if (e.target === id) one.add(e.source);
          }
          if (hopDepth === 1) return one.has(n.id);
          const two = new Set(one);
          for (const e of p.net.edges) {
            if (one.has(e.source)) two.add(e.target);
            if (one.has(e.target)) two.add(e.source);
          }
          return two.has(n.id);
        }
        // Search bypasses exposure/region list filters so every network entity is locatable.
        if (searching) return true;
        if (p.pfShock.showKoreanPfOnly && region.get(n.id) !== "KR") return false;
        if (p.pfShock.exposureFilter === "confirmed_dc") {
          const exp = (n as { pf_exposure_class?: string }).pf_exposure_class;
          return exp === "confirmed_aidc_project" || exp === "confirmed_dc_finance" || n.entity_type === "spv" || region.get(n.id) === "US";
        }
        if (p.pfShock.exposureFilter === "general_pf") {
          return (n as { pf_exposure_class?: string }).pf_exposure_class === "general_pf" || region.get(n.id) === "US";
        }
        if (p.pfShock.exposureFilter === "sector_only") {
          const exp = (n as { pf_exposure_class?: string }).pf_exposure_class;
          return exp === "sector_sensitivity" || exp === "research_candidate" || region.get(n.id) === "US";
        }
        if (!p.pfShock.showUsKoreaOnly) return true;
        if (region.get(n.id) === "KR") return true;
        return p.net.edges.some((e) => {
          const a = region.get(e.source); const b = region.get(e.target);
          return (e.source === n.id || e.target === n.id) && ((a === "US" && b === "KR") || (a === "KR" && b === "US"));
        });
      })
      .map((n) => {
        const st = p.visuals?.[n.id]?.status;
        return (
          <li key={n.id}>
            <button type="button" className={`ent ${p.selectedId === n.id ? "is-on" : ""}`} onClick={() => p.onSelect(n.id)}>
              <span className={`dot g-${n.group}`} />
              <span className="ent-name">{displayName(n)}</span>
              <span className="ent-tk num">
                {!hasLiveRelation(n, p.net, p.net.meta.as_of) ? "현재 관계 없음" : ((n as { region?: string }).region === "KR" ? "KR" : (n.ticker || n.entity_type))}
              </span>
              {st && st !== "normal" && p.mode === "shock" ? <span className={`sdot s-${STATUS_DOT[st] || "muted-o"}`} /> : <span className="sdot" />}
            </button>
          </li>
        );
      });

  if (p.mode === "market") {
    const byId = new Map((p.quotes?.items || []).map((i) => [i.entity, i]));
    const listed = p.net.nodes.filter((n) => n.listed);
    const unlisted = p.net.nodes.filter((n) => !n.listed);
    const priced = listed.filter((n) => byId.get(n.id)?.price != null).length;
    const krRows = listed.filter((n) => isKrEx(n.exchange));
    const usRows = listed.filter((n) => !isKrEx(n.exchange));
    const row = (n: Network["nodes"][number]) => {
      const qq = byId.get(n.id);
      const up = (qq?.change_pct ?? 0) > 0;
      const down = (qq?.change_pct ?? 0) < 0;
      const has = qq?.price != null;
      const delay = qq?.delay_label || (qq?.delay_kind === "close" ? "일간 종가" : qq?.delay_kind === "realtime" ? "실시간/지연" : "");
      const short = !n.listed
        ? "비상장"
        : qq?.status === "not_supported" ? "미지원"
        : qq?.status === "no_key" ? "키 없음"
        : qq?.status === "pending" ? "대기"
        : "미수집";
      return (
        <li key={n.id}>
          <button type="button" className={`q-row ${has ? "" : "is-empty"} ${p.selectedId === n.id ? "is-on" : ""} ${up ? "is-up" : down ? "is-down" : ""}`}
            onClick={() => p.onSelect(n.id)}>
            <span className="q-name">
              <span>{displayName(n)}</span>
              <span className="q-meta num">{qq?.ticker || n.ticker || "—"} · {n.exchange || "—"}{delay ? ` · ${delay}` : ""}</span>
            </span>
            {has ? (
              <>
                <span className="q-px num">{fmtPx(qq!)}</span>
                <span className={`q-ch num ${up ? "is-up" : down ? "is-down" : ""}`}>{fmtChg(qq!)}</span>
              </>
            ) : (
              <span className="q-na">{short}</span>
            )}
          </button>
        </li>
      );
    };
    return (
      <aside className="lp" aria-label="PF Market">
        <LpResize />
        <section className="lp-sec">
          <h3 className="lbl">PF Market <span className="lbl-aside">관측 시세</span></h3>
          <p className="note">한국 AI 데이터센터 PF 생태계 상장사의 <b>실제 관측 주가</b>입니다. Shock 시나리오와 무관하며, 결측을 0이나 모회사 시세로 대체하지 않습니다.</p>
          <p className="fine">
            조회 시각: {p.quotes?.retrieved_at ? new Date(p.quotes.retrieved_at).toLocaleString("ko-KR") : "—"}
            {" · "}시세 기준: {p.quotes?.generated_at ? new Date(p.quotes.generated_at).toLocaleString("ko-KR") : "—"}
            {p.quotes?.refresh_status ? ` · ${p.quotes.refresh_status}` : ""}
          </p>
          {p.quotes?.refresh_detail ? <p className="fine">{p.quotes.refresh_detail}</p> : null}
          <button type="button" className="btn-text" onClick={p.onRefreshQuotes} disabled={p.quotesBusy} style={{ marginBottom: 8 }}>
            <IconReset size={11} /> {refreshLabel(!!p.quotesLive, p.quotesBusy)}
          </button>
          <p className="fine num">{priced}/{listed.length} 상장 시세 · 비상장 {unlisted.length} · {p.quotes?.generated_at ? p.quotes.generated_at.replace("T", " ").slice(0, 16) : "스냅샷 없음"}</p>
          <button type="button" className="btn-text" onClick={p.onRefreshQuotes} disabled={p.quotesBusy}>
            <IconReset size={11} /> {refreshLabel(!!p.quotesLive, p.quotesBusy)}
          </button>
          {p.quotes?.note ? <p className="hint">{p.quotes.note}</p> : null}
        </section>
        <section className="lp-sec lp-quotes">
          <h3 className="lbl">한국 상장 <span className="lbl-aside">{krRows.length}</span></h3>
          <ul className="q-rail">{krRows.map(row)}</ul>
        </section>
        <section className="lp-sec lp-quotes">
          <h3 className="lbl">해외 상장 <span className="lbl-aside">{usRows.length}</span></h3>
          <ul className="q-rail">{usRows.map(row)}</ul>
        </section>
        <section className="lp-sec">
          <h3 className="lbl">비상장 · 프로젝트 <span className="lbl-aside">{unlisted.length}</span></h3>
          <p className="fine">비상장 법인은 시세를 표시하지 않습니다 (모회사 주가 대치 없음).</p>
          <ul className="ent-list">
            {p.projects.projects.slice(0, 40).map((pr) => (
              <li key={pr.id}>
                <button type="button" className={`ent ${p.selectedId === pr.id ? "is-on" : ""}`} onClick={() => p.onSelect(pr.id)}>
                  <span className="dot g-project_finance" />
                  <span className="ent-name">{projectDisplayName(pr)}</span>
                  <span className="ent-tk num">{pr.country}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      </aside>
    );
  }

  return (
    <aside className="lp" aria-label={p.mode === "shock" ? "PF Shock" : "PF Network"}>
      <LpResize />
      {p.mode === "shock" ? (
        <section className="lp-sec">
          <h3 className="lbl">PF Stress <span className="lbl-aside">US → Korea</span></h3>
          <p className="note">1차 충격은 CoreWeave 재무 압박과 빅테크 AI CAPEX입니다. 금리·GPU 임대료는 2차 변수입니다. 국내 기관의 부도를 자동으로 가정하지 않으며, 모든 결과는 「추가 충격 없음」과 비교합니다.</p>

          <div className="f-row">
            <span className="f-lbl">1차 A · CoreWeave 재무 스트레스</span>
            <div className="seg seg-wrap" role="group">
              {CW_DISTRESS.map((m) => (
                <button key={m.id} type="button" className={p.pfShock.coreweaveDistress === m.id ? "is-on" : ""}
                  onClick={() => p.onPfShock({ coreweaveDistress: m.id as CoreWeaveDistress })}>{m.label}</button>
              ))}
            </div>
            <span className="f-lbl" style={{ marginTop: 6 }}>CoreWeave→국내 자금시장 전가 (가정)
              <span className="shock-val num">{Math.round((p.pfShock.cwKrFundingPassThrough || 0) * 100)}%</span>
            </span>
            <input className="shock-slider" type="range" min={0} max={100} step={5}
              value={Math.round((p.pfShock.cwKrFundingPassThrough || 0) * 100)}
              onChange={(e) => p.onPfShock({ cwKrFundingPassThrough: Number(e.target.value) / 100 })} />
            <p className="fine">검증된 CoreWeave–한국은행 여신이 없으므로 전가는 명시적 가정입니다.</p>
          </div>

          <div className="f-row">
            <span className="f-lbl">1차 B · 빅테크 AI CAPEX
              <span className="shock-val num">{p.pfShock.hyperscalerCapexPct}%</span>
            </span>
            <input className="shock-slider" type="range" min={-50} max={0} step={5}
              value={p.pfShock.hyperscalerCapexPct} onChange={(e) => p.onPfShock({ hyperscalerCapexPct: Number(e.target.value) })} />
            <div className="seg seg-wrap">
              {CAPEX_PRESETS.map((v) => (
                <button key={v} type="button" className={p.pfShock.hyperscalerCapexPct === v ? "is-on" : ""}
                  onClick={() => p.onPfShock({ hyperscalerCapexPct: v })}>{v}%</button>
              ))}
            </div>
            <span className="f-lbl" style={{ marginTop: 6 }}>수요 탄성 (가정)
              <span className="shock-val num">{Math.round(p.pfShock.capexDemandElasticity * 100)}%</span>
            </span>
            <input className="shock-slider" type="range" min={0} max={100} step={5}
              value={Math.round(p.pfShock.capexDemandElasticity * 100)}
              onChange={(e) => p.onPfShock({ capexDemandElasticity: Number(e.target.value) / 100 })} />
            <label className="chk" style={{ display: "flex", gap: 8, alignItems: "center", marginTop: 8, fontSize: 12 }}>
              <input type="checkbox" checked={p.pfShock.restrictNewFinancing}
                onChange={(e) => p.onPfShock({ restrictNewFinancing: e.target.checked })} />
              신규 프로젝트 금융 제한
            </label>
          </div>

          <button type="button" className="disclosure" aria-expanded={true} onClick={() => undefined}>
            <IconChevron size={11} className="chev" /> 2차 변수 · 금리 · GPU
          </button>
          <div className="f-row">
            <span className="f-lbl">금리 (USD PF)
              <span className="shock-val num">{p.pfShock.rateBp > 0 ? "+" : ""}{p.pfShock.rateBp}bp</span>
            </span>
            <input className="shock-slider" type="range" min={0} max={500} step={25}
              value={p.pfShock.rateBp} onChange={(e) => p.onPfShock({ rateBp: Number(e.target.value) })} />
            <div className="seg seg-wrap">
              {RATE_PRESETS.map((bp) => (
                <button key={bp} type="button" className={p.pfShock.rateBp === bp ? "is-on" : ""}
                  onClick={() => p.onPfShock({ rateBp: bp })}>{bp > 0 ? "+" : ""}{bp}</button>
              ))}
            </div>
            <span className="f-lbl" style={{ marginTop: 6 }}>한국 조달금리
              <span className="shock-val num">+{p.pfShock.krRateBp}bp</span>
            </span>
            <input className="shock-slider" type="range" min={0} max={500} step={25}
              value={p.pfShock.krRateBp} onChange={(e) => p.onPfShock({ krRateBp: Number(e.target.value) })} />
            <span className="f-lbl" style={{ marginTop: 6 }}>GPU 임대료
              <span className="shock-val num">{p.pfShock.gpuRentPct}%</span>
            </span>
            <input className="shock-slider" type="range" min={-50} max={0} step={5}
              value={p.pfShock.gpuRentPct} onChange={(e) => p.onPfShock({ gpuRentPct: Number(e.target.value) })} />
            <div className="seg seg-wrap">
              {GPU_PRESETS.map((v) => (
                <button key={v} type="button" className={p.pfShock.gpuRentPct === v ? "is-on" : ""}
                  onClick={() => p.onPfShock({ gpuRentPct: v })}>{v}%</button>
              ))}
            </div>
            <div className="seg" style={{ marginTop: 8 }}>
              {([12, 24, 36] as const).map((h) => (
                <button key={h} type="button" className={p.pfShock.horizonMonths === h ? "is-on" : ""}
                  onClick={() => p.onPfShock({ horizonMonths: h })}>{h}개월</button>
              ))}
            </div>
          </div>

          {p.shockResult ? <PfShockDigest result={p.shockResult} pending={p.shockPending} /> : null}
          <ShockImpactBlock
            result={p.shockResult}
            selectedId={p.selectedId}
            onSelect={(id) => p.onSelect(id)}
          />
        </section>
      ) : null}

      {p.mode !== "shock" ? (
      <section className="lp-sec">
        <h3 className="lbl">Network Filter <span className="lbl-aside" data-tip="화면 표시만 바뀌며 계산에는 영향이 없습니다">표시만</span></h3>
        <label className="search" htmlFor="pf-search">
          <IconSearch size={13} />
          <input
            id="pf-search"
            type="search"
            placeholder="회사 · PFV · 기관 · 티커"
            value={q}
            autoComplete="off"
            onChange={(e) => setQ(e.target.value)}
            onCompositionStart={() => { composingRef.current = true; }}
            onCompositionEnd={() => { composingRef.current = false; }}
            onKeyDown={onSearchKeyDown}
            aria-autocomplete="list"
            aria-controls="pf-search-results"
            aria-expanded={searching}
          />
        </label>
        {searching ? (
          <div className="pf-search-panel" role="region" aria-label="검색 결과">
            {!searchHits.length ? (
              <p className="muted-line">일치하는 회사 없음 · 다른 키워드를 입력하세요</p>
            ) : (
              <>
                <ul className="pf-search-results" id="pf-search-results" ref={searchListRef} role="listbox">
                  {searchHits.map((h, i) => (
                    <li key={h.id} role="option" aria-selected={i === activeHit || p.selectedId === h.id}>
                      <button
                        type="button"
                        className={`pf-search-hit ${i === activeHit ? "is-active" : ""} ${p.selectedId === h.id ? "is-on" : ""}`}
                        onMouseEnter={() => setActiveHit(i)}
                        onClick={() => locate(h.id)}
                      >
                        <span className={`dot g-${h.group}`} />
                        <span className="pf-search-hit-t">
                          <span className="ent-name">{h.label}</span>
                          <span className="fine">{h.meta}</span>
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
                <button type="button" className="btn-text" onClick={clearSearch}>검색 지우기</button>
              </>
            )}
          </div>
        ) : (
          <ul className="cls-list">
            {PF_CLASSES.map((c) => {
              const members = p.net.nodes.filter((n) => c.groups.includes(n.group) && isCompanyNode(n));
              const hidden = c.groups.every((g) => p.hiddenGroups.includes(g));
              return (
                <li key={c.id}>
                  <div className={`cls ${openClass === c.id ? "is-open" : ""}`}>
                    <input type="checkbox" checked={!hidden} onChange={() => c.groups.forEach((g) => p.onToggleGroup(g))} aria-label={`${c.label} 표시`} />
                    <button type="button" className="cls-b" onClick={() => setOpenClass((x) => (x === c.id ? null : c.id))} aria-expanded={openClass === c.id}>
                      <span className={`dot g-${c.groups[0]}`} /><span>{c.label}</span><span className="num cnt">{members.length}</span><IconChevron size={11} className="chev" />
                    </button>
                  </div>
                  {openClass === c.id ? (
                    <ul className="ent-list">
                      {members.map((n) => (
                        <li key={n.id}>
                          <button type="button" className={`ent ${p.selectedId === n.id ? "is-on" : ""}`} onClick={() => locate(n.id)}>
                            <span className={`dot g-${n.group}`} />
                            <span className="ent-name">{displayName(n)}</span>
                            <span className="ent-tk num">{n.ticker || ((n as { region?: string }).region === "KR" ? "KR" : "비상장")}</span>
                            <span className="sdot" />
                          </button>
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
        {p.selectedId ? (
          <button type="button" className="btn-text" style={{ marginTop: 8 }} onClick={() => p.onClearSelection?.()}>
            ← 전체 네트워크로
          </button>
        ) : null}
      </section>
      ) : null}

      {p.mode === "shock" ? (
      <section className="lp-sec">
        <h3 className="lbl">회사 (Shock) <span className="lbl-aside">{searching ? `${searchHits.length}건 일치` : companyCount}</span></h3>
        <label className="search" htmlFor="pf-search-shock">
          <IconSearch size={13} />
          <input
            id="pf-search-shock"
            type="search"
            placeholder="회사 · PFV · 기관 검색"
            value={q}
            autoComplete="off"
            onChange={(e) => setQ(e.target.value)}
            onCompositionStart={() => { composingRef.current = true; }}
            onCompositionEnd={() => { composingRef.current = false; }}
            onKeyDown={onSearchKeyDown}
          />
        </label>
        {searching ? (
          <div className="pf-search-panel">
            {!searchHits.length ? (
              <p className="muted-line">일치하는 회사 없음</p>
            ) : (
              <ul className="pf-search-results">
                {searchHits.slice(0, 24).map((h, i) => (
                  <li key={h.id}>
                    <button type="button" className={`pf-search-hit ${i === activeHit ? "is-active" : ""}`} onClick={() => locate(h.id)}>
                      <span className={`dot g-${h.group}`} />
                      <span className="pf-search-hit-t">
                        <span className="ent-name">{h.label}</span>
                        <span className="fine">{h.meta}</span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}
        <label className="f-lbl" style={{ display: "block", marginTop: 6 }}>역할
          <select className="shock-slider" style={{ width: "100%", height: 28, marginTop: 4 }} value={filterRole} onChange={(e) => setFilterRole(e.target.value)}>
            {PF_ROLE_FILTERS.map((r) => <option key={r.id} value={r.id}>{r.label}</option>)}
          </select>
        </label>
        <ul className="ent-list" style={{ marginTop: 8 }}>{entityRows(null)}</ul>
      </section>
      ) : null}

      <section className="lp-sec">
        <button type="button" className="disclosure" aria-expanded={guide} onClick={() => setGuide((g) => !g)}>
          <IconChevron size={11} className="chev" /> 전달 경로 등급
        </button>
        {guide ? (
          <div className="guide">
            <dl>
              <div><dt>A · Direct contract</dt><dd>공시·발표로 확인된 계약·여신</dd></div>
              <div><dt>B · Sector demand</dt><dd>업종 수요 민감도 (특정 SPV 계약 아님)</dd></div>
              <div><dt>C · Funding market</dt><dd>자금시장 경색 시나리오</dd></div>
              <div><dt>D · Unverified</dt><dd>미확인 — 금액화하지 않음</dd></div>
            </dl>
          </div>
        ) : null}
      </section>
    </aside>
  );
}
