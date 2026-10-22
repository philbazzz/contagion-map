# Ecosystem expansion — validation snapshot

Research date for this pass: **2026-10-20** (updated same day: KR + Arista/Vertiv + dossier layout).

## Counts

| Metric | Value |
| --- | --- |
| Entities (companies / institutions) | **69** (was 58 before KR/Arista pass) |
| Newly added Korean listed | **11** (Hanmi, Isu Petasys, LS ELECTRIC, HD Hyundai Electric, Hyosung Heavy, Doosan Enerbility, SKT, NAVER, Samsung SDS, KT, LG Electronics) |
| Verified relationships (edges) | **75** (was 65) |
| Newly added relationships (this pass) | **+10** (Arista↔MSFT/Meta, Vertiv/Eaton/Schneider↔NVIDIA 800VDC, Hanmi↔SK hynix/Micron, SKT/NAVER↔NVIDIA, SKT↔SMCI) |
| Detailed financial dossiers (`profiles.json`) | **16** |
| Source catalog entries | **86** |
| Debt instruments (CoreWeave-centric Shock model) | **19** |
| Commercial contracts | **12** |
| Zero-degree nodes (intentional — no invented edges) | **8** Korean candidates without named counterparty disclosure |

## Industry / group breakdown

| Group | Count |
| --- | --- |
| financial | 26 |
| customer (hyperscalers / AI buyers) | 10 |
| semiconductor | 8 |
| datacenter | 7 |
| server | 6 |
| ai_infra | 1 (CoreWeave) |

## Relationship-type breakdown

| Type | Count |
| --- | --- |
| FINANCING_PARTICIPATION | 25 |
| SUPPLIER | 20 |
| CUSTOMER | 8 |
| EQUITY_INVESTMENT | 5 |
| INDIRECT_SUPPLY_CHAIN | 3 |
| LESSOR | 2 |
| COLLATERAL_AGENT | 1 |
| CAPACITY_BACKSTOP | 1 |

## Companies with detailed financial profiles

NVIDIA, Microsoft, Amazon, Oracle, TSMC, SK hynix, Samsung Electronics, Meta, Equinix, CoreWeave.

## Companies with overview / relationship data only (examples)

AMD, Broadcom, ASML, Micron, Dell, HPE, SMCI, Arista, Digital Realty, Vertiv, Eaton, Schneider, Alphabet, OpenAI, Anthropic, and most lenders — present as verified nodes/edges; full comparable 10-K dossier not yet mirrored.

## Focal-company smoke checks

| Focal | Direct | Indirect | Profile |
| --- | --- | --- | --- |
| CoreWeave | 37 | 14 | yes |
| NVIDIA | 15 | 36 | yes |
| Microsoft | 3 | 48 | yes |
| Oracle | 1 | 50 | yes |
| TSMC | 5 | 46 | yes |
| SK hynix | 1 | 50 | yes |
| Samsung | 1 | 50 | yes |

Sample paths: Microsoft→NVIDIA (1), Amazon→TSMC (2 via NVIDIA), NVIDIA→ASML (2 via TSMC), OpenAI→Microsoft (1).

## Primary sources used in enrich pass

- NVIDIA FY2026 results / SEC exhibit (`q4fy26pr.htm`)
- Microsoft FY2025 IR statements / 10-K
- TSMC 4Q25 management report / 6-K board approval
- Oracle FY2025 results release
- Amazon FY2025 results exhibit
- SK hynix FY25 newsroom results
- Samsung Electronics FY2025 IR / SOI PDF
- Meta FY2025 results
- Equinix FY2025 results SEC exhibit
- Existing CoreWeave 10-Q (`S_10Q2`) and prior relationship sources

## Known limitations

1. **Shock amounts remain CoreWeave-quantified** for floating SOFR debt. Other companies show pathway / qualitative exposure; no invented secondary loss coefficients.
2. **CW-touching edges still dominate** financing edges (42 of 65). Multi-center industrial edges are 23 and growing only with evidence.
3. **Many majors lack instrument-level debt tables** comparable to CoreWeave Note 10 — marked `UNKNOWN` / `missing` in dossiers.
4. **Customer names** (e.g. SK hynix “Customer A”, TSMC top-10) are often undisclosed; concentration is noted without fabricating identities.
5. **Target 50–80 entities**: 58 entities with evidence; not padded to quota.
6. **GitHub Pages**: data ships via `npm run prepare:static` → `public/data/network.json` (includes profiles). No runtime Python for end users.

## How to refresh static deploy data

```bash
cd frontend
set FETCH_QUOTES=0
npm run prepare:static
npm run build
```
