/** First-visit guide: who the tool is for, the 4-step flow, and what the data can / cannot support. */
import { useEffect, useRef } from "react";

const KEY = "contagion.guide.v1";

export function guideSeen(): boolean {
  try { return localStorage.getItem(KEY) === "1"; } catch { return false; }
}
function markSeen() {
  try { localStorage.setItem(KEY, "1"); } catch { /* storage blocked — guide just shows again */ }
}

export function GuideCard({ onClose, onStartPf }: { onClose: () => void; onStartPf: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.querySelector<HTMLButtonElement>("button.guide-primary")?.focus();
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") { markSeen(); onClose(); } };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  const close = () => { markSeen(); onClose(); };
  return (
    <div className="guide-scrim" role="presentation" onClick={close}>
      <div className="guide-card" role="dialog" aria-modal="true" aria-labelledby="guide-t" ref={ref} onClick={(e) => e.stopPropagation()}>
        <p className="lbl">처음 사용하는 분께</p>
        <h2 id="guide-t">기업·사업·금융 관계와 충격 전달 경로를 근거와 함께 탐색합니다</h2>
        <p className="guide-who">증권사 IB · 리서치 · 심사 · 리스크관리 담당자가 「어느 기업이 어떤 사업에 어떤 형태로 참여하며, 특정 충격이 어떤 경로로 닿을 수 있는가」를 빠르게 확인하도록 만든 도구입니다.</p>
        <ol className="guide-steps">
          <li><b>기업 검색</b><span>왼쪽 Network Filter 검색창 또는 지도에서 기업을 누릅니다.</span></li>
          <li><b>관련 사업·포지션 확인</b><span>오른쪽 패널에서 대출 잔액·지분·확약을 유형별로, 확실성 표시와 함께 봅니다.</span></li>
          <li><b>충격 선택</b><span>상단 Shock에서 CoreWeave 상태·AI CAPEX·금리를 고릅니다. 결과는 항상 「추가 충격 없음」과 비교합니다.</span></li>
          <li><b>영향 경로와 근거 확인</b><span>결과 상단 3줄(바뀐 것 · 영향 대상 · 근거)과 주요 5개 기업을 확인하고, 원문 링크로 검증합니다.</span></li>
        </ol>
        <div className="guide-cols">
          <div>
            <p className="lbl">지원하는 판단</p>
            <ul>
              <li>공시·보도로 확인된 관계와 금액의 탐색</li>
              <li>충격이 어떤 계약·가정 경로로 닿는지 구분</li>
              <li>공시된 잔액·금리가 있는 범위의 추가 이자·DSCR</li>
            </ul>
          </div>
          <div>
            <p className="lbl">계산하지 않는 범위</p>
            <ul>
              <li>기관별 보유잔액·CFADS가 없으면 금액·DSCR은 「산정 불가」</li>
              <li>부도확률·손실률을 만들지 않으며, 계산 불가는 「영향 없음」이 아님</li>
              <li>시나리오는 예측·투자 의견이 아님</li>
            </ul>
          </div>
        </div>
        <p className="guide-legend">
          금액 표시: <span className="cert cert-confirmed">확인된 금액</span> <span className="cert cert-estimated">추정 · 확인 필요</span> <span className="cert cert-inferred">공개자료 추론</span> <span className="cert cert-assumed">사용자 가정</span> <span className="cert cert-unknown">미확인</span>
        </p>
        <div className="guide-actions">
          <button type="button" className="btn guide-primary" onClick={close}>시작하기</button>
          <button type="button" className="btn-text" onClick={() => { close(); onStartPf(); }}>국내 AI 데이터센터 PF부터 보기</button>
          <span className="fine">상단 「안내」로 다시 열 수 있습니다.</span>
        </div>
      </div>
    </div>
  );
}
