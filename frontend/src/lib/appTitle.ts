import type { EcosystemId } from "../pf/types";

/** Mode-dependent product title (header + document.title). */
export function appTitle(ecosystem: EcosystemId): { brand: string; sub: string; document: string } {
  if (ecosystem === "datacenter_pf") {
    return {
      brand: "AI DC Contagion Map",
      sub: "한국 AI 데이터센터 PF",
      document: "AI DC Contagion Map",
    };
  }
  return {
    brand: "코어위브 Contagion Map",
    sub: "AI Semiconductor Ecosystem",
    document: "코어위브 Contagion Map",
  };
}
