import type { MarketIndicator, MarketOverview } from "../types";
import { fmtDateTime } from "../lib/format";
import { IconClose, IconLink, IconReset } from "./Icons";

const GOOD = new Set(["ok", "weekend_or_holiday"]);
const RATE_IDS = new Set(["ust_10y", "ust_2y"]);

function shortName(id: string) {
  if (id === "ust_10y") return "10Y";
  if (id === "ust_2y") return "2Y";
  if (id === "gpu_rent") return "H100/hr";
  return id;
}

function headline(ind: MarketIndicator) {
  if (!ind.latest) return null;
  if (ind.id === "ust_10y" || ind.id === "ust_2y") {
    const v = ind.latest.value ?? 0;
    const ch = ind.change_vs_previous;
    return {
      value: `${v.toFixed(2)}%`,
      change: ch === null || ch === undefined ? "이전 값 없음" : `${ch > 0 ? "+" : ""}${(ch * 100).toFixed(0)}bp`,
      date: ind.latest.obs_date,
    };
  }
  const m = ind.latest.median ?? 0;
  const ch = ind.change_vs_previous;
  return { value: `$${m.toFixed(2)}`, change: ch === null || ch === undefined ? "이전 스냅샷 없음" : `${ch > 0 ? "+" : ""}${ch.toFixed(2)}$`, date: ind.latest.snap_date };
}

export function MarketStrip({ market, isDemo, snapshotOnly, onOpen }: {
  market: MarketOverview | null; isDemo: boolean; snapshotOnly?: boolean; onOpen: () => void;
}) {
  const prefer = ["ust_10y", "ust_2y"];
  const inds = (market?.indicators || []).filter((i) => i.id !== "hy_oas");
  const shown = prefer.map((id) => inds.find((i) => i.id === id)).filter(Boolean) as MarketIndicator[];
  const rest = inds.filter((i) => !prefer.includes(i.id));
  const display = [...shown, ...rest].slice(0, 4);
  const tip = isDemo
    ? "저장된 스냅샷 · 자동 갱신 안 됨. 관측값이며 시나리오 가정이 아닙니다."
    : snapshotOnly
      ? "GitHub Actions FRED 스냅샷 · 실시간 아님. 주식 수치는 재배포하지 않음 (TradingView 상세 패널)."
      : "최근 수집값 · 실시간 아님. 관측값이며 시나리오 가정이 아닙니다.";
  return (
    <button type="button" className="mstrip" onClick={onOpen} aria-label="시장 상황 열기" data-tip={tip}>
      <span className="ms-lbl">Market</span>
      {display.map((ind) => {
        const h = headline(ind);
        return (
          <span key={ind.id} className={`ms-item ${GOOD.has(ind.status) ? "" : "is-warn"}`}>
            <span className="ms-name">{shortName(ind.id)}</span>
            {h ? <><span className="num ms-v">{h.value}</span><span className="num ms-d">{h.change}</span></>
              : <span className="ms-s">{ind.status === "not_redistributable" ? "로컬 전용" : ind.status === "no_key" ? "키 미설정" : ind.status === "no_snapshot" ? "스냅샷 없음" : ind.status_ko}</span>}
          </span>
        );
      })}
      {!market ? <span className="ms-s">데이터 없음</span> : null}
    </button>
  );
}

function Trend({ t, unit }: { t?: { status: string; label?: string; change?: number; change_pct?: number | null; ref_date?: string }; unit: "bp" | "usd" | "pct" }) {
  if (!t || t.status !== "ok") return <span className="muted">이력 부족</span>;
  const ch = t.change ?? 0;
  let txt: string;
  if (unit === "bp") txt = `${ch > 0 ? "+" : ""}${ch.toFixed(0)}bp`;
  else if (unit === "pct") txt = `${ch > 0 ? "+" : ""}${(ch * 100).toFixed(0)}bp (${ch > 0 ? "+" : ""}${ch.toFixed(3)}%pt)`;
  else txt = `${ch > 0 ? "+" : ""}$${ch.toFixed(2)}${t.change_pct !== null && t.change_pct !== undefined ? ` (${t.change_pct > 0 ? "+" : ""}${t.change_pct.toFixed(1)}%)` : ""}`;
  return <span className="num">{txt} <small className="muted">vs {t.ref_date}</small></span>;
}

function IndicatorBlock({ ind }: { ind: MarketIndicator }) {
  const h = headline(ind);
  if (ind.id === "hy_oas") return null;
  const isYield = ind.id === "ust_10y" || ind.id === "ust_2y";
  const isRate = RATE_IDS.has(ind.id);
  const trendUnit = isYield ? "pct" : "usd";
  return (
    <section className={`mk-ind ${GOOD.has(ind.status) ? "" : "mk-warn"}`}>
      <header>
        <h3>{ind.name}</h3>
        <p>{ind.plain}</p>
      </header>
      <div className="mk-main">
        {h ? (
          <>
            <b className="num">{h.value}</b>
            <span>{ind.unit}{isRate ? "" : " · 중앙값"}</span>
          </>
        ) : <b className="mk-none">{ind.status_ko}</b>}
        {h ? <span className="obs-tag">시장 관측값</span> : null}
      </div>
      <dl className="mk-kv">
        {!isRate && ind.latest ? (<><dt>25~75% 구간</dt><dd className="num">${ind.latest.p25?.toFixed(2)} ~ ${ind.latest.p75?.toFixed(2)}</dd><dt>매물 수</dt><dd className="num">{ind.latest.offer_count}건 <small className="muted">(거래량 · 수요 아님)</small></dd></>) : null}
        <dt>이전 관측값 대비</dt><dd>{h ? h.change : "—"}</dd>
        <dt>7일 추세</dt><dd><Trend t={ind.trend?.d7} unit={trendUnit} /></dd>
        <dt>30일 추세</dt><dd><Trend t={ind.trend?.d30} unit={trendUnit} /></dd>
        <dt>관측 기준일</dt><dd className="num">{h?.date || "—"}</dd>
        <dt>마지막 수집 시각</dt><dd>{fmtDateTime(ind.last_success_at)}</dd>
        <dt>데이터 상태</dt><dd className={GOOD.has(ind.status) ? "" : "amber"}>{ind.status_ko}{ind.last_error ? ` — ${ind.last_error.label}: ${ind.last_error.detail}` : ind.detail ? ` — ${ind.detail}` : ""}</dd>
        <dt>표시 기준</dt><dd>{ind.freshness_label || "—"}</dd>
        <dt>출처</dt><dd><a href={ind.source.url} target="_blank" rel="noreferrer">{ind.source.name} <IconLink size={11} /></a></dd>
      </dl>
      {ind.unit_note ? <p className="hint">{ind.unit_note}</p> : null}
      {ind.condition_text ? <p className="hint"><b>비교 조건</b> · {ind.condition_text}</p> : null}
      {ind.fee_note ? <p className="hint">{ind.fee_note}</p> : null}
      {ind.history?.provider_note ? <p className="hint">{ind.history.provider_note}{ind.history.stored_from ? ` 보유 이력: ${ind.history.stored_from} ~ ${ind.history.stored_to} (${ind.history.stored_count}건)` : ""}</p> : null}
      <p className="hint caution">{ind.caution}</p>
      {ind.license ? <p className="hint">{ind.license}</p> : null}
    </section>
  );
}

export function MarketPanel(p: {
  market: MarketOverview | null; isDemo: boolean; snapshotOnly?: boolean;
  onClose: () => void; onRefresh: () => void; refreshing: boolean;
}) {
  return (
    <div className="modal-back" role="dialog" aria-modal="true" aria-label="시장 상황" onClick={(e) => { if (e.target === e.currentTarget) p.onClose(); }}>
      <div className="modal">
        <button type="button" className="ibtn modal-x" onClick={p.onClose} aria-label="닫기"><IconClose size={14} /></button>
        <header className="modal-h">
          <p className="lbl">Market Observations</p><h2>시장 상황</h2>
          <p>{p.isDemo
            ? `이 화면은 공개 데모입니다. 저장된 스냅샷(${p.market?.snapshot_at ? fmtDateTime(p.market.snapshot_at) : "없음"})을 보여 주며 자동으로 갱신되지 않습니다.`
            : p.snapshotOnly
              ? `GitHub Pages 정적 스냅샷입니다. 국채(FRED DGS10·DGS2)는 Actions가 갱신합니다(${p.market?.snapshot_at ? fmtDateTime(p.market.snapshot_at) : "미수집"}). 주식 수치 시세는 재배포 제한으로 포함하지 않으며, 종목별 시세는 상세 패널 TradingView를 사용하세요.`
              : p.market?.scheduler?.note || "관측된 시장 데이터입니다. 좌측 금리 충격 시나리오와 혼동하지 마세요."}</p>
          {!p.isDemo ? (
            <button type="button" className="btn-text" onClick={p.onRefresh} disabled={p.refreshing}>
              <IconReset size={12} /> {p.refreshing ? "불러오는 중…" : p.snapshotOnly ? "스냅샷 다시 불러오기" : "지금 다시 수집"}
            </button>
          ) : null}
        </header>
        <div className="mk-grid">
          {(p.market?.indicators || []).map((ind) => <IndicatorBlock key={ind.id} ind={ind} />)}
          {!p.market ? <p className="muted">시장 데이터가 없습니다.</p> : null}
        </div>

        <section className="mk-scn">
          <p className="lbl">구분</p>
          <p className="hint">
            <b>관측값</b> = FRED·거래소에서 수집한 실제 시장 수치.{" "}
            <b>시나리오 가정</b> = 좌측 슬라이더의 가상 bp 충격.{" "}
            {p.market?.usage_note || "관측값을 시뮬레이션 가정에 자동 대입하지 않습니다."}
            {" "}HY OAS·국채 금리는 CoreWeave 개별 차환금리가 아닙니다.
          </p>
        </section>
      </div>
    </div>
  );
}
