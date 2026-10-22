import { useEffect, useRef, useState } from "react";

const MIN = 320;
const MAX = 640;
const DEFAULT = 420;
const KEY = "contagion.lpWidth";
const COLLAPSE_KEY = "contagion.lpCollapsed";

/** Drag handle on the right edge of the left rail. Persists width; supports collapse. */
export function LpResize() {
  const dragging = useRef(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    const wasCollapsed = localStorage.getItem(COLLAPSE_KEY) === "1";
    setCollapsed(wasCollapsed);
    if (wasCollapsed) {
      document.documentElement.style.setProperty("--lp", "48px");
      document.documentElement.classList.add("lp-collapsed");
      return;
    }
    const saved = Number(localStorage.getItem(KEY) || "");
    const w = saved >= MIN && saved <= MAX ? saved : DEFAULT;
    document.documentElement.style.setProperty("--lp", `${w}px`);
    document.documentElement.classList.remove("lp-collapsed");
  }, []);

  useEffect(() => {
    const onMove = (ev: PointerEvent) => {
      if (!dragging.current) return;
      const w = Math.min(MAX, Math.max(MIN, ev.clientX));
      document.documentElement.style.setProperty("--lp", `${w}px`);
      document.documentElement.classList.remove("lp-collapsed");
      setCollapsed(false);
      localStorage.setItem(COLLAPSE_KEY, "0");
    };
    const onUp = () => {
      if (!dragging.current) return;
      dragging.current = false;
      document.body.classList.remove("is-resizing-lp");
      const raw = getComputedStyle(document.documentElement).getPropertyValue("--lp").trim();
      const n = parseInt(raw, 10);
      if (n >= MIN && n <= MAX) localStorage.setItem(KEY, String(n));
      // Notify layout listeners (universe canvas) without resetting selection
      window.dispatchEvent(new CustomEvent("contagion:lp-resize"));
    };
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
    };
  }, []);

  const toggleCollapse = () => {
    const next = !collapsed;
    setCollapsed(next);
    localStorage.setItem(COLLAPSE_KEY, next ? "1" : "0");
    if (next) {
      document.documentElement.style.setProperty("--lp", "48px");
      document.documentElement.classList.add("lp-collapsed");
    } else {
      const saved = Number(localStorage.getItem(KEY) || "");
      const w = saved >= MIN && saved <= MAX ? saved : DEFAULT;
      document.documentElement.style.setProperty("--lp", `${w}px`);
      document.documentElement.classList.remove("lp-collapsed");
    }
    window.dispatchEvent(new CustomEvent("contagion:lp-resize"));
  };

  return (
    <>
      <button
        type="button"
        className="lp-collapse-btn"
        aria-label={collapsed ? "왼쪽 패널 펼치기" : "왼쪽 패널 접기"}
        data-tip={collapsed ? "패널 펼치기" : "패널 접기 (네트워크 공간 확보)"}
        onClick={toggleCollapse}
      >
        {collapsed ? "»" : "«"}
      </button>
      <div
        className="lp-resize"
        role="separator"
        aria-orientation="vertical"
        aria-label="왼쪽 패널 너비 조절"
        data-tip={`드래그하여 왼쪽 패널 너비 조절 (${MIN}–${MAX}px)`}
        onPointerDown={(e) => {
          if (collapsed) {
            toggleCollapse();
            return;
          }
          dragging.current = true;
          document.body.classList.add("is-resizing-lp");
          (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
        }}
      />
    </>
  );
}
