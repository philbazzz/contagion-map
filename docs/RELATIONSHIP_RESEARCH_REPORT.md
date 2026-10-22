# Relationship research report — existing-entity density pass

**Research as of:** 2026-10-20  
**Scope:** Verified edges among companies **already registered** in Contagion Map. No new planets.

## C. Network expansion summary

| Metric | Before this pass | After |
| --- | ---: | ---: |
| Registered entities | 69 | **69** (unchanged) |
| Verified + inferred edges | 75 | **91** |
| Newly added edges | — | **+16** |
| Edges upgraded INFERRED→VERIFIED / reinforced | — | **9** |
| CoreWeave-touching edges | 42 | **42** (unchanged) |
| **Non–CoreWeave edges** | 33 | **49** |
| Unique undirected pairs | 69 | **83** |
| Avg degree | ~2.2 | **~2.6** |
| Isolated (degree 0) | 8 | **8** (same KR candidates without named counterparties) |

Non-CW share of edges: **33/75 (44%) → 49/91 (54%)**.

## B. Newly added / upgraded relationships (table)

| Company A | Company B | Type | Explanation (concise) | Amount | Status | Source |
| --- | --- | --- | --- | --- | --- | --- |
| NVIDIA | TSMC | SUPPLIER | FY2026 10-K names TSMC as wafer foundry | Undisclosed | **Upgraded VERIFIED** | [nvda-20260125](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm) |
| NVIDIA | Samsung | SUPPLIER | 10-K: foundry + memory supplier | Undisclosed | **Upgraded VERIFIED** | same |
| Dell | NVIDIA | STRATEGIC_PARTNERSHIP | Dell AI Factory with NVIDIA | Undisclosed | **Upgraded VERIFIED** | [Dell blog](https://www.dell.com/en-us/blog/transform-innovation-into-value-the-dell-ai-factory-with-nvidia/) |
| HPE | NVIDIA | STRATEGIC_PARTNERSHIP | NVIDIA AI Computing by HPE | Undisclosed | **Upgraded VERIFIED** | [HPE](https://www.hpe.com/us/en/newsroom/blog-post/2025/06/hpe-and-nvidia-a-partnership-driving-the-next-generation-of-ai-innovation.html) |
| SMCI | NVIDIA | SUPPLIER | FY2025 10-K: works closely with NVIDIA | Undisclosed | Reinforced VERIFIED | [smci 10-K](https://www.sec.gov/Archives/edgar/data/1375365/000137536525000027/smci-20250630.htm) |
| NVIDIA | Micron | SUPPLIER | 10-K + Micron HBM/SOCAMM for Blackwell | Undisclosed | Reinforced | [Micron IR](https://investors.micron.com/news/press-release/2025/Micron-Innovates-From-the-Data-Center-to-the-Edge-With-NVIDIA-03-18-2025/default.aspx) |
| NVIDIA | Foxconn / Wistron | SUPPLIER | 10-K named CMS | Undisclosed | Reinforced VERIFIED | NVIDIA 10-K |
| Microsoft | Equinix | STRATEGIC_PARTNERSHIP | Azure ExpressRoute | Undisclosed | **NEW VERIFIED** | [MS Learn](https://learn.microsoft.com/en-us/azure/expressroute/metro) |
| Microsoft | Digital Realty | STRATEGIC_PARTNERSHIP | Azure ExpressRoute | Undisclosed | **NEW VERIFIED** | [DLR PR](https://www.digitalrealty.com/about/newsroom/press-releases/123278/digital-realty-expands-global-relationship-with-microsoft-with-the-deployment-of-microsoft-azure-expressroute-cloud-on-ramp-in-dallas-and-the-launch-of-the-new-azure-expressroute-metro-service-in-amsterdam-and-zurich) |
| Amazon | Equinix | STRATEGIC_PARTNERSHIP | AWS Direct Connect partner | Undisclosed | **NEW VERIFIED** | [AWS DX partners](https://aws.amazon.com/directconnect/partners/) |
| Amazon | Digital Realty | STRATEGIC_PARTNERSHIP | AWS Direct Connect | Undisclosed | **NEW VERIFIED** | same + [DLR AWS](https://www.digitalrealty.com/partners/aws) |
| Oracle | Equinix | STRATEGIC_PARTNERSHIP | OCI FastConnect / Equinix Fabric | Undisclosed | **NEW VERIFIED** | [Oracle FC partners](https://www.oracle.com/cloud/networking/fastconnect/regions-by-partner/) |
| Oracle | Digital Realty | STRATEGIC_PARTNERSHIP | OCI FastConnect | Undisclosed | **NEW VERIFIED** | same |
| OpenAI | NVIDIA | STRATEGIC_PARTNERSHIP | ≥10 GW systems LOI | Undisclosed GW | **NEW VERIFIED** | [OpenAI](https://openai.com/index/openai-nvidia-systems-partnership/) |
| NVIDIA | OpenAI | EQUITY_INVESTMENT | Intends up to $100B as GW deployed | Up to $100B intent | **NEW VERIFIED** | same |
| OpenAI | Oracle | STRATEGIC_PARTNERSHIP | Stargate 4.5 GW+ capacity | Multi-year / GW | **NEW VERIFIED** | [OpenAI Stargate](https://openai.com/index/stargate-advances-with-partnership-with-oracle/) |
| Amazon | Anthropic | EQUITY_INVESTMENT | Minority stake ($8B prior + $5B / up to $20B) | Staged | **NEW VERIFIED** | [Amazon](https://www.aboutamazon.com/news/company-news/amazon-invests-additional-5-billion-anthropic-ai) |
| Anthropic | Amazon | CUSTOMER | AWS primary cloud / Trainium; >$100B 10y commit | >$100B commit (announced) | **NEW VERIFIED** | [Anthropic](https://www.anthropic.com/news/anthropic-amazon-compute) |
| Microsoft / Meta / Oracle / Amazon | AMD | CUSTOMER | AMD 2024 AR named deployments / instances | Undisclosed share | **NEW VERIFIED** | [AMD AR 2024](https://ir.amd.com/financial-information/sec-filings/content/0001193125-25-067185/0001193125-25-067185.pdf) |
| SMCI | AMD | STRATEGIC_PARTNERSHIP | 10-K co-development with AMD | Undisclosed | **NEW VERIFIED** | SMCI 10-K |

Prior Arista↔MSFT/Meta and Vertiv↔NVIDIA edges retained.

## Hub degrees after pass (sample)

| Entity | Degree |
| --- | ---: |
| NVIDIA | high (supply + OEM + OpenAI + power partners) |
| Microsoft | +Equinix, +DLR, +AMD, +Arista, +OpenAI, +NVIDIA |
| Amazon | +Equinix, +DLR, +AMD, +Anthropic, +NVIDIA |
| Oracle | +Equinix, +DLR, +AMD, +OpenAI, +NVIDIA |
| Equinix / Digital Realty | now multi-cloud hubs (MSFT/AMZN/ORCL) |
| OpenAI | Microsoft + NVIDIA + Oracle |
| Anthropic | Amazon (equity + cloud) |

## D. Research limitations / excluded candidates

| Candidate | Why excluded / limited |
| --- | --- |
| Alphabet ↔ Equinix/DLR | Common interconnect practice; lacked a clean Google-official doc in this pass comparable to Azure/AWS/OCI partner lists |
| Broadcom ↔ Meta/Google/Microsoft ASICs | Strong secondary reporting; Broadcom 10-K does **not** name those customers → kept **Unverified** |
| AMD ↔ named >10% revenue customers | AMD 10-K: **no** customer ≥10% of revenue in FY24/FY25; AR letter used for **deployment** edges only |
| Meta ↔ Equinix/DLR tenant | ColoMap/secondary lists; no Meta 10-K named lease → **Not Disclosed** |
| LS ELECTRIC / HD Hyundai / Hyosung / Doosan / Isu Petasys / KT / SDS / LGE | Remain degree 0: no **named** counterparty among registered entities |
| Financing edges among banks | Still almost entirely CoreWeave syndicate; no new non-CW borrower instruments added without filings |
| NVIDIA ↔ Arista | 10-K lists Arista among **networking competitors**, not as a customer/partner → no commercial edge |
| OpenAI–NVIDIA $100B | LOI / intent tied to GW deployment — not a closed single check |
| Documents not fully page-scraped | Some PDFs accessed via search snippets + IR HTML; exact exhibit page numbers not always captured |

## Shock vs commercial

New edges are **business / interconnect / equity / strategic**. They do **not** invent floating-rate exposure or secondary loss coefficients. Shock quantification remains CoreWeave SOFR instruments.

## How to refresh static site

```bat
cd frontend
set FETCH_QUOTES=0
npm run prepare:static
npm run build
```
