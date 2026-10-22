/**
 * Compact PFV / SPC borrower panel — progressive disclosure for high-degree borrowers.
 * Does not alter underlying edges or shock calculations.
 */
import { Fragment, useMemo, useState } from "react";
import type { Network, NetNode } from "../types";
import type { PfShockResult } from "../pf/types";
import {
  buildBorrowerSummary,
  INST_CATEGORY_LABEL,
  type BorrowerEdgeMode,
  type InstCategoryId,
  type InstFacilityRow,
} from "../pf/borrowerSummary";
import { FINANCING_STAGE_KO } from "../lib/format";

function fmtLoan(eok: number | null, unknown: number): string {
  if (eok != null) {
    const base = `${Math.round(eok).toLocaleString("ko-KR")}억 원`;
    return unknown ? `${base} (잔액미확인 ${unknown}건 제외)` : base;
  }
  if (unknown) return "미확인";
  return "해당 없음 / 미확인";
}

function FacilityExpand({ row, onSelectEdge, onSelectNode }: {
  row: InstFacilityRow;
  onSelectEdge: (id: string) => void;
  onSelectNode: (id: string) => void;
}) {
  return (
    <div className="pfb-expand">
      <dl className="pfb-dl">
        <div><dt>금융시설</dt><dd>{row.projectName || row.projectId || "—"}</dd></div>
        <div><dt>선순위·트랜치</dt><dd>{row.seniority || "—"}{row.stage ? ` · ${FINANCING_STAGE_KO[row.stage] || row.stage}` : ""}</dd></div>
        <div><dt>확인 원금</dt><dd className="num">{row.balanceLabel}</dd></div>
        {row.facilityTotalEok != null ? (
          <div><dt>시설총액(맥락)</dt><dd className="num">{Math.round(row.facilityTotalEok).toLocaleString("ko-KR")}억 · 보유잔액 아님</dd></div>
        ) : null}
        {row.amountNote ? <div><dt>비고</dt><dd>{row.amountNote}</dd></div> : null}
        <div><dt>확인일</dt><dd className="num">{row.verifiedDate || "—"}</dd></div>
        {row.sourceUrl ? (
          <div>
            <dt>근거 공시</dt>
            <dd>
              <a href={row.sourceUrl} target="_blank" rel="noreferrer">{row.sourceTitle || "DART·기사"}</a>
              {row.sourceDate ? ` · ${row.sourceDate}` : ""}
            </dd>
          </div>
        ) : null}
      </dl>
      <div className="pfb-row-actions">
        <button type="button" className="btn-text" onClick={() => onSelectNode(row.institutionId)}>기관으로 이동</button>
        <button type="button" className="btn-text" onClick={() => onSelectEdge(row.edgeId)}>관계 상세</button>
      </div>
    </div>
  );
}

export function PfBorrowerPanel({
  borrowerId,
  net,
  ledgerNet,
  nodeMap,
  hiddenGroups,
  edgeMode,
  onEdgeMode,
  categoryFocus,
  onCategoryFocus,
  shockResult,
  onSelectNode,
  onSelectEdge,
}: {
  borrowerId: string;
  net: Network;
  /** Full ledger for accurate exposure counts (may include historical). */
  ledgerNet?: Network;
  nodeMap: Map<string, NetNode>;
  hiddenGroups?: string[];
  edgeMode: BorrowerEdgeMode;
  onEdgeMode: (m: BorrowerEdgeMode) => void;
  categoryFocus: InstCategoryId | null;
  onCategoryFocus: (c: InstCategoryId | null) => void;
  shockResult?: PfShockResult | null;
  onSelectNode: (id: string) => void;
  onSelectEdge: (id: string) => void;
}) {
  const [detailOpen, setDetailOpen] = useState(false);
  const [openCats, setOpenCats] = useState<Set<InstCategoryId>>(() => new Set());
  const [openRows, setOpenRows] = useState<Set<string>>(() => new Set());
  const [q, setQ] = useState("");
  const [filterCat, setFilterCat] = useState<InstCategoryId | "all">("all");
  const [filterStatus, setFilterStatus] = useState<"active" | "all" | "past">("active");
  const [pathsOpen, setPathsOpen] = useState(false);

  const preferEdges = useMemo(() => {
    const co = shockResult?.pf?.affected_companies?.find((c) => c.company_id === borrowerId);
    return co?.projects?.map((p) => p.edge_id).filter(Boolean) as string[] | undefined;
  }, [shockResult, borrowerId]);

  const summary = useMemo(
    () => buildBorrowerSummary(borrowerId, ledgerNet || net, {
      hiddenGroups,
      preferEdgeIds: preferEdges,
    }),
    [borrowerId, ledgerNet, net, hiddenGroups, preferEdges],
  );

  const shockCo = shockResult?.pf?.affected_companies?.find((c) => c.company_id === borrowerId);
  const borrowerNode = nodeMap.get(borrowerId);

  if (!summary) return null;

  const toggleCat = (id: InstCategoryId) => {
    setOpenCats((prev) => {
      const n = new Set(prev);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });
    onCategoryFocus(id);
    if (edgeMode !== "by_category") onEdgeMode("by_category");
  };

  const filteredRows = useMemo(() => {
    const qq = q.trim().toLowerCase();
    return summary.rows.filter((r) => {
      if (filterCat !== "all" && r.category !== filterCat) return false;
      if (filterStatus === "active" && (r.past || r.arranger)) return false;
      if (filterStatus === "past" && !r.past) return false;
      if (qq && !r.institutionName.toLowerCase().includes(qq) && !r.relLabel.toLowerCase().includes(qq)) return false;
      return true;
    });
  }, [summary.rows, q, filterCat, filterStatus]);

  return (
    <section className="rp-sec pfb">
      <h4 className="lbl">차주 요약 <span className="lbl-aside">PFV · SPC</span></h4>

      {shockCo ? (
        <div className="pfb-shock">
          <p className="pfb-shock-k">쇼크 영향</p>
          <dl className="pfb-metrics">
            <div><dt>위험 상태</dt><dd>{shockCo.impact_category || shockCo.default_assessment || "—"}</dd></div>
            <div><dt>영향 사업</dt><dd className="num">{shockCo.projects?.length ?? 0}</dd></div>
            <div><dt>관련 금융기관</dt><dd className="num">{summary.institutionCount}</dd></div>
          </dl>
          <p className="fine">{summary.materialRankingNote}</p>
          {!pathsOpen ? (
            <button type="button" className="btn-text" onClick={() => setPathsOpen(true)}>전이 경로 상세 열기</button>
          ) : (
            <ul className="pfb-paths">
              {(shockCo.projects || []).slice(0, 8).map((pr) => (
                <li key={pr.edge_id || pr.project_id}>
                  <button type="button" className="link" onClick={() => pr.edge_id && onSelectEdge(pr.edge_id)}>
                    {pr.project_name || pr.project_id || pr.edge_id}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}

      <dl className="pfb-metrics">
        <div><dt>차주명</dt><dd>{summary.borrowerName}</dd></div>
        <div>
          <dt>연결 금융기관</dt>
          <dd className="num">
            {summary.institutionCount}개
            {hiddenGroups?.length && summary.visibleInstitutionCount !== summary.institutionCount
              ? <span className="fine"> · 지도 표시 {summary.visibleInstitutionCount}개</span>
              : null}
          </dd>
        </div>
        <div>
          <dt>확인된 대출잔액</dt>
          <dd className="num">{fmtLoan(summary.knownLoanEok, summary.unknownLoanFacilities)}</dd>
        </div>
        <div>
          <dt>대출약정·트랜치</dt>
          <dd className="num">활성 {summary.activeFacilityCount} · 전체 {summary.facilityCount}</dd>
        </div>
      </dl>
      <p className="fine">주선·인수·시설총액은 잔액에 합산하지 않습니다. Unknown은 0으로 두지 않습니다.</p>

      <p className="lbl" style={{ marginTop: 6 }}>금융기관 유형별 현황</p>
      <ul className="pfb-cats">
        {summary.categoryCounts.map((c) => (
          <li key={c.id}>
            <button
              type="button"
              className={`pfb-cat ${openCats.has(c.id) ? "is-open" : ""} ${categoryFocus === c.id ? "is-focus" : ""}`}
              onClick={() => toggleCat(c.id)}
            >
              {c.label} <span className="num">{c.count}</span>
            </button>
            {openCats.has(c.id) ? (
              <ul className="pfb-inst">
                {(summary.categories.find((x) => x.id === c.id)?.institutions || []).map((inst, i, arr) => {
                  if (i >= 4 && arr.length > 5) {
                    if (i === 4) {
                      return <li key="more" className="fine">기타 {arr.length - 4}개 · 상세에서 전체 확인</li>;
                    }
                    return null;
                  }
                  return (
                    <li key={inst.id}>
                      <button type="button" className="link" onClick={() => onSelectNode(inst.id)}>{inst.name}</button>
                      {inst.knownEok != null
                        ? <span className="num fine"> · {Math.round(inst.knownEok).toLocaleString("ko-KR")}억</span>
                        : inst.unknownFacilities
                          ? <span className="fine"> · 잔액미확인</span>
                          : null}
                    </li>
                  );
                })}
              </ul>
            ) : null}
          </li>
        ))}
      </ul>

      <div className="pfb-modes" role="group" aria-label="지도 연결 표시">
        <button type="button" className={edgeMode === "material" ? "is-on" : ""} onClick={() => onEdgeMode("material")}>주요 연결만 보기</button>
        <button type="button" className={edgeMode === "all" ? "is-on" : ""} onClick={() => onEdgeMode("all")}>전체 연결 강조</button>
        <button type="button" className={edgeMode === "by_category" ? "is-on" : ""} onClick={() => onEdgeMode("by_category")}>금융기관별 보기</button>
      </div>
      <p className="fine">{summary.materialRankingNote} · 기본 강조 {summary.materialEdgeIds.length}건</p>

      {!detailOpen ? (
        <button type="button" className="pfb-more" onClick={() => setDetailOpen(true)}>
          금융기관 상세 펼치기
        </button>
      ) : (
        <div className="pfb-detail">
          <div className="pfb-detail-bar">
            <p className="lbl">금융기관 상세</p>
            <button type="button" className="btn-text" onClick={() => setDetailOpen(false)}>접기</button>
          </div>
          <div className="pfb-filters">
            <input
              type="search"
              placeholder="기관 검색…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              aria-label="연결 기관 검색"
            />
            <select value={filterCat} onChange={(e) => setFilterCat(e.target.value as InstCategoryId | "all")} aria-label="기관 유형">
              <option value="all">유형 전체</option>
              {summary.categoryCounts.map((c) => (
                <option key={c.id} value={c.id}>{c.label}</option>
              ))}
            </select>
            <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value as "active" | "all" | "past")} aria-label="익스포저 상태">
              <option value="active">활성만</option>
              <option value="all">전체</option>
              <option value="past">과거·상환</option>
            </select>
          </div>
          <div className="pfb-table-wrap">
            <table className="pfb-table">
              <thead>
                <tr>
                  <th>금융기관</th>
                  <th>관계</th>
                  <th>확인 잔액</th>
                  <th>상태</th>
                </tr>
              </thead>
              <tbody>
                {filteredRows.map((r) => {
                  const open = openRows.has(r.edgeId);
                  return (
                    <Fragment key={r.edgeId}>
                      <tr
                        className={`${r.past || r.arranger ? "is-hist" : ""} ${open ? "is-open" : ""}`}
                        onClick={() => setOpenRows((prev) => {
                          const n = new Set(prev);
                          if (n.has(r.edgeId)) n.delete(r.edgeId);
                          else n.add(r.edgeId);
                          return n;
                        })}
                      >
                        <td className="wrap">
                          <span className="fine">{INST_CATEGORY_LABEL[r.category]}</span>
                          <br />{r.institutionName}
                        </td>
                        <td>{r.relLabel}</td>
                        <td className="num">{r.balanceLabel}</td>
                        <td>{r.statusLabel}</td>
                      </tr>
                      {open ? (
                        <tr className="pfb-detail-row">
                          <td colSpan={4}>
                            <FacilityExpand row={r} onSelectEdge={onSelectEdge} onSelectNode={onSelectNode} />
                          </td>
                        </tr>
                      ) : null}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
            {!filteredRows.length ? <p className="muted-line">조건에 맞는 관계가 없습니다.</p> : null}
          </div>
          {borrowerNode ? (
            <p className="fine">지도에서 숨긴 기관 유형은 시각화에서만 제외되며, 위 집계·쇼크 계산에는 영향을 주지 않습니다.</p>
          ) : null}
        </div>
      )}
    </section>
  );
}
