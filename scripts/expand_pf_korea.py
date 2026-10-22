#!/usr/bin/env python3
"""
Expand AI Data Center PF network with 100+ distinct Korean legal entities
and verified Korean DC PF project relationships (Casequare Gasan, Camsquare Ansan, etc.).

Exposure classes (stored on nodes as pf_exposure_class):
  1 confirmed_aidc_project — verified AI/DC project participation
  2 confirmed_dc_finance — verified general DC development/financing
  3 general_pf — general PF participant, no identified DC deal
  4 sector_sensitivity — industry sensitivity only
  5 research_candidate — identified legal entity, no verified relevant exposure
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PF = ROOT / "frontend" / "public" / "data" / "pf"

# (id, name_en, name_ko, group, entity_type, role, listed, ticker, exposure_class, activities, source)
# exposure_class: 1..5 as above
ENTITIES: list[tuple] = [
    # ===== A. Construction / EPC / Developers (20+) =====
    ("samsung_cnt", "Samsung C&T", "삼성물산", "kr_construction", "company", "EPC / developer", True, "028260", 4, "Construction; domestic AI DC EPC candidate", "KRX"),
    ("hyundai_enc", "Hyundai E&C", "현대건설", "kr_construction", "company", "EPC · completion guarantee", True, "000720", 1, "EPC + completion guarantee on Casequare Gasan & Camsquare Ansan DC PF", "DealSite/IBTomato"),
    ("gs_enc", "GS E&C", "GS건설", "kr_construction", "company", "EPC", True, "006360", 4, "Major Korean contractor; DC-specific awards not attached here", "KRX"),
    ("dl_enc", "DL E&C", "DL이앤씨", "kr_construction", "company", "EPC", True, "375500", 4, "Major contractor", "KRX"),
    ("daewoo_enc", "Daewoo E&C", "대우건설", "kr_construction", "company", "EPC", True, "047040", 4, "Major contractor", "KRX"),
    ("posco_enc", "POSCO E&C", "포스코이앤씨", "kr_construction", "company", "EPC", False, None, 4, "Industrial / plant EPC", "Company IR"),
    ("hdc_dev", "HDC Hyundai Development", "HDC현대산업개발", "kr_construction", "company", "Developer", True, "294870", 4, "Property developer", "KRX"),
    ("lotte_enc", "Lotte E&C", "롯데건설", "kr_construction", "company", "EPC", False, None, 4, "Construction affiliate of Lotte", "Company"),
    ("sk_ecoplant", "SK ecoplant", "SK에코플랜트", "kr_construction", "company", "EPC / infra", False, None, 4, "SK Group infra; AIDC discussions", "Company"),
    ("hanwha_eng", "Hanwha Engineering & Construction", "한화건설", "kr_construction", "company", "EPC", False, None, 4, "Hanwha construction unit", "Company"),
    ("kolon_global", "Kolon Global", "코오롱글로벌", "kr_construction", "company", "EPC", True, "003070", 4, "Construction", "KRX"),
    ("kcc_enc", "KCC Engineering & Construction", "KCC건설", "kr_construction", "company", "EPC", False, None, 5, "Construction", "Company"),
    ("sgc_enc", "SGC E&C", "SGC이앤씨", "kr_construction", "company", "EPC", True, "005390", 5, "Construction", "KRX"),
    ("isdongseo", "IS Dongseo", "일성동서", "kr_construction", "company", "Developer", True, "010780", 5, "Construction / development", "KRX"),
    ("taeyoung_eng", "Taeyoung Engineering & Construction", "태영건설", "kr_construction", "company", "EPC", True, "009410", 3, "Active in PF construction market", "KRX"),
    ("doosan_enc", "Doosan Engineering & Construction", "두산건설", "kr_construction", "company", "EPC", True, "011160", 5, "Construction", "KRX"),
    ("kumho_enc", "Kumho Engineering & Construction", "금호건설", "kr_construction", "company", "EPC", True, "002990", 5, "Construction", "KRX"),
    ("hyundai_eng", "Hyundai Engineering", "현대엔지니어링", "kr_construction", "company", "EPC", False, None, 4, "Plant / infra engineering", "Company"),
    ("samsung_eng", "Samsung Engineering", "삼성엔지니어링", "kr_construction", "company", "EPC", True, "028050", 4, "Plant EPC", "KRX"),
    ("lotte_dev", "Lotte Property & Development", "롯데물산", "kr_construction", "company", "Developer", False, None, 5, "Property development", "Company"),
    ("ajooc_enc", "Ajou Construction", "아주건설", "kr_construction", "company", "EPC", False, None, 5, "Construction", "Company"),
    ("sambu_enc", "Sambu Construction", "삼부토건", "kr_construction", "company", "EPC", True, "001470", 5, "Construction", "KRX"),

    # ===== B. Real estate trust companies (10+) =====
    ("korea_asset_trust", "Korea Asset Trust", "한국자산신탁", "kr_trust", "trust_company", "RE trust", True, "123890", 3, "Licensed RE trust; general PF trust roles", "KRX/FSS"),
    ("kreit", "Korea Real Estate Investment & Trust", "한국토지신탁", "kr_trust", "trust_company", "RE trust", True, "034830", 3, "Licensed RE trust", "KRX"),
    ("koramco_trust", "Koramco Asset Trust", "코람코자산신탁", "kr_trust", "trust_company", "RE trust / Casequare equity", True, "357610", 1, "Casequare Gasan DC PFV shareholder (~5.5%)", "DealSite"),
    ("hana_asset_trust", "Hana Asset Trust", "하나자산신탁", "kr_trust", "trust_company", "RE trust", False, None, 3, "Hana Financial Group trust affiliate", "FSS"),
    ("kb_re_trust", "KB Real Estate Trust", "KB부동산신탁", "kr_trust", "trust_company", "RE trust", False, None, 3, "KB Group trust affiliate", "FSS"),
    ("shinhan_re_trust", "Shinhan Asset Trust", "신한자산신탁", "kr_trust", "trust_company", "RE trust", False, None, 3, "Shinhan Group trust affiliate", "FSS"),
    ("woori_asset_trust", "Woori Asset Trust", "우리자산신탁", "kr_trust", "trust_company", "RE trust", False, None, 3, "Woori Group trust affiliate", "FSS"),
    ("daehan_re_trust", "Daehan Real Estate Trust", "대한토지신탁", "kr_trust", "trust_company", "RE trust", False, None, 3, "Licensed RE trust", "FSS"),
    ("kyobo_asset_trust", "Kyobo Asset Trust", "교보자산신탁", "kr_trust", "trust_company", "RE trust", False, None, 3, "Kyobo affiliate trust", "FSS"),
    ("korea_land_trust", "Korea Land and Housing Trust", "한국토지주택신탁", "kr_trust", "trust_company", "RE trust", False, None, 5, "Land trust activities", "FSS"),
    ("mirae_asset_trust", "Mirae Asset Trust", "미래에셋신탁", "kr_trust", "trust_company", "RE trust", False, None, 3, "Mirae Asset Group trust", "FSS"),
    ("nh_re_trust", "NH Real Estate Trust", "농협부동산신탁", "kr_trust", "trust_company", "RE trust", False, None, 3, "NongHyup trust affiliate", "FSS"),

    # ===== C. Savings banks (15+) =====
    ("sbi_savings", "SBI Savings Bank", "SBI저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Large savings bank; general PF/real-estate lending", "FSS"),
    ("ok_savings", "OK Savings Bank", "OK저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Large savings bank", "FSS"),
    ("welcome_savings", "Welcome Savings Bank", "웰컴저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Savings bank", "FSS"),
    ("kis_savings", "Korea Investment Savings Bank", "한국투자저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Korea Investment Group affiliate", "FSS"),
    ("acuon_savings", "Acuon Savings Bank", "애큐온저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Savings bank", "FSS"),
    ("kb_savings", "KB Savings Bank", "KB저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "KB Group savings bank", "FSS"),
    ("shinhan_savings", "Shinhan Savings Bank", "신한저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Shinhan Group savings bank", "FSS"),
    ("hana_savings", "Hana Savings Bank", "하나저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Hana Group savings bank", "FSS"),
    ("woori_fin_savings", "Woori Financial Savings Bank", "우리금융저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Woori Financial Group savings bank", "FSS"),
    ("ibk_savings", "IBK Savings Bank", "IBK저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "IBK affiliate savings bank", "FSS"),
    ("thek_savings", "The-K Savings Bank", "더케이저축은행", "kr_savings", "savings_bank", "Casequare senior lender", False, None, 1, "Senior tranche lender KRW 10bn Casequare Gasan PF (reported)", "DealSite"),
    ("jt_savings", "JT Savings Bank", "JT저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Savings bank", "FSS"),
    ("hk_savings", "HK Savings Bank", "HK저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Savings bank", "FSS"),
    ("pepper_savings", "Pepper Savings Bank", "페퍼저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Savings bank", "FSS"),
    ("smart_savings", "Smart Savings Bank", "스마트저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 5, "Regional savings bank", "FSS"),
    ("imoa_savings", "IMOA Savings Bank", "모아저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 5, "Regional savings bank", "FSS"),
    ("daol_savings", "Daol Savings Bank", "다올저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 3, "Savings bank", "FSS"),
    ("osung_savings", "Osung Savings Bank", "오성저축은행", "kr_savings", "savings_bank", "Savings bank", False, None, 5, "Regional savings bank", "FSS"),

    # ===== D. MG cooperatives (federation + identifiable) =====
    ("mg_federation", "MG Community Credit Cooperatives Federation", "새마을금고중앙회", "kr_cooperative", "cooperative_federation", "Federation", False, None, 3, "Federation-level; aggregate cooperative finance — not individual DC loan book", "MG/FSS"),
    ("mg_seoul", "Seoul MG Community Credit Cooperative", "서울특별시새마을금고", "kr_cooperative", "cooperative", "Local MG", False, None, 5, "Local cooperative; no verified DC PF edge", "MG"),
    ("mg_busan", "Busan MG Community Credit Cooperative", "부산광역시새마을금고", "kr_cooperative", "cooperative", "Local MG", False, None, 5, "Local cooperative", "MG"),
    ("mg_incheon", "Incheon MG Community Credit Cooperative", "인천광역시새마을금고", "kr_cooperative", "cooperative", "Local MG", False, None, 5, "Local cooperative", "MG"),
    ("mg_daegu", "Daegu MG Community Credit Cooperative", "대구광역시새마을금고", "kr_cooperative", "cooperative", "Local MG", False, None, 5, "Local cooperative", "MG"),
    ("mg_gwangju", "Gwangju MG Community Credit Cooperative", "광주광역시새마을금고", "kr_cooperative", "cooperative", "Local MG", False, None, 5, "Local cooperative", "MG"),
    ("mg_daejeon", "Daejeon MG Community Credit Cooperative", "대전광역시새마을금고", "kr_cooperative", "cooperative", "Local MG", False, None, 5, "Local cooperative", "MG"),
    ("mg_ulsan", "Ulsan MG Community Credit Cooperative", "울산광역시새마을금고", "kr_cooperative", "cooperative", "Local MG", False, None, 5, "Local cooperative", "MG"),
    ("mg_gyeonggi", "Gyeonggi MG Community Credit Cooperative", "경기도새마을금고", "kr_cooperative", "cooperative", "Local MG", False, None, 5, "Provincial cooperative identity", "MG"),
    ("shinhyup_federation", "National Credit Union Federation of Korea", "신협중앙회", "kr_cooperative", "cooperative_federation", "Credit union federation", False, None, 3, "Shinhyup system; general cooperative finance", "FSS"),
    ("suhyup_bank", "Suhyup Bank", "수협은행", "kr_bank", "bank", "Fisheries cooperative bank", False, None, 3, "Specialized bank", "FSS"),

    # ===== E. Commercial / regional / policy banks (15+) =====
    ("kb_bank", "KB Kookmin Bank", "KB국민은행", "kr_bank", "bank", "Commercial bank", False, None, 3, "Major commercial bank; general PF", "FSS"),
    ("shinhan_bank", "Shinhan Bank", "신한은행", "kr_bank", "bank", "Commercial bank", False, None, 3, "Major commercial bank", "FSS"),
    ("hana_bank", "Hana Bank", "하나은행", "kr_bank", "bank", "Commercial bank", False, None, 3, "Major commercial bank", "FSS"),
    ("woori_bank", "Woori Bank", "우리은행", "kr_bank", "bank", "Commercial bank", False, None, 3, "Major commercial bank", "FSS"),
    ("nh_bank", "NH NongHyup Bank", "NH농협은행", "kr_bank", "bank", "Commercial / cooperative bank", False, None, 1, "Casequare Gasan senior lender KRW 40bn (reported)", "DealSite"),
    ("ibk_bank", "IBK Industrial Bank of Korea", "기업은행", "kr_bank", "bank", "Policy / commercial bank", True, "024110", 3, "SME / corporate lender", "KRX"),
    ("kdb", "Korea Development Bank", "한국산업은행", "kr_bank", "bank", "Policy bank", False, None, 3, "Policy / project finance", "KDB"),
    ("eximbank_kr", "Export-Import Bank of Korea", "한국수출입은행", "kr_bank", "bank", "Policy bank", False, None, 4, "Export / overseas infra financing", "KEXIM"),
    ("bnk_busan", "BNK Busan Bank", "BNK부산은행", "kr_bank", "bank", "Regional bank", False, None, 3, "Regional bank", "FSS"),
    ("bnk_kyongnam", "BNK Kyongnam Bank", "BNK경남은행", "kr_bank", "bank", "Regional bank", False, None, 3, "Regional bank", "FSS"),
    ("im_bank", "iM Bank", "iM뱅크", "kr_bank", "bank", "Regional bank (ex-DGB)", False, None, 3, "Daegu regional bank rebranded", "FSS"),
    ("jeonbuk_bank", "Jeonbuk Bank", "전북은행", "kr_bank", "bank", "Regional bank", False, None, 3, "JB Financial Group", "FSS"),
    ("gwangju_bank", "Gwangju Bank", "광주은행", "kr_bank", "bank", "Regional bank", False, None, 3, "JB Financial Group", "FSS"),
    ("jeju_bank", "Jeju Bank", "제주은행", "kr_bank", "bank", "Regional bank", True, "006220", 5, "Regional bank", "KRX"),
    ("kfcc", "KFCC / Nonghyup Financial", "농협금융지주", "kr_bank", "holding", "Financial holding", True, "138930", 4, "Holding — not auto-inherit NH Bank DC loan", "KRX"),
    ("kb_fg", "KB Financial Group", "KB금융지주", "kr_bank", "holding", "Financial holding", True, "105560", 4, "Holding company", "KRX"),
    ("shinhan_fg", "Shinhan Financial Group", "신한지주", "kr_bank", "holding", "Financial holding", True, "055550", 4, "Holding company", "KRX"),
    ("hana_fg", "Hana Financial Group", "하나금융지주", "kr_bank", "holding", "Financial holding", True, "086790", 4, "Holding company", "KRX"),
    ("woori_fg", "Woori Financial Group", "우리금융지주", "kr_bank", "holding", "Financial holding", True, "316140", 4, "Holding company", "KRX"),

    # ===== F. Securities (15+) =====
    ("mirae_asset_sec", "Mirae Asset Securities", "미래에셋증권", "kr_securities", "securities", "Broker / arranger", True, "006800", 3, "Major securities; PF arranging capability", "KRX"),
    ("korea_inv_sec", "Korea Investment & Securities", "한국투자증권", "kr_securities", "securities", "Casequare arranger / junior lender", True, "071050", 1, "Arranged Casequare Gasan PF; junior tranche KRW 70bn (reported)", "DealSite"),
    ("nh_inv_sec", "NH Investment & Securities", "NH투자증권", "kr_securities", "securities", "Broker / arranger", True, "005940", 3, "Major securities", "KRX"),
    ("samsung_sec", "Samsung Securities", "삼성증권", "kr_securities", "securities", "Camsquare Ansan arranger", True, "016360", 1, "Arranged Camsquare Ansan KRW 834bn PF (reported)", "IBTomato"),
    ("kb_sec", "KB Securities", "KB증권", "kr_securities", "securities", "Broker", True, None, 3, "KB Group securities", "FSS"),
    ("shinhan_sec", "Shinhan Securities", "신한투자증권", "kr_securities", "securities", "Broker", False, None, 3, "Shinhan Group securities", "FSS"),
    ("hana_sec", "Hana Securities", "하나증권", "kr_securities", "securities", "Broker", False, None, 3, "Hana Group securities", "FSS"),
    ("woori_inv_sec", "Woori Investment & Securities", "우리투자증권", "kr_securities", "securities", "Broker", False, None, 3, "Woori securities", "FSS"),
    ("meritz_sec", "Meritz Securities", "메리츠증권", "kr_securities", "securities", "Broker / PF", True, "008560", 3, "Active PF market participant", "KRX"),
    ("daishin_sec", "Daishin Securities", "대신증권", "kr_securities", "securities", "Broker", True, "003540", 3, "Securities", "KRX"),
    ("kiwoom_sec", "Kiwoom Securities", "키움증권", "kr_securities", "securities", "Casequare refinancing underwriter", True, "039490", 1, "Total underwrite Casequare refinancing ~KRW 380bn (2025 press)", "Sedaily"),
    ("sk_sec", "SK Securities", "SK증권", "kr_securities", "securities", "Broker", True, "001510", 5, "Securities", "KRX"),
    ("hyundai_motor_sec", "Hyundai Motor Securities", "현대차증권", "kr_securities", "securities", "Broker", True, "001500", 5, "Securities", "KRX"),
    ("yuanta_sec", "Yuanta Securities", "유안타증권", "kr_securities", "securities", "Credit enhancement / underwrite", True, "003470", 1, "Private bond underwrite commitment for Mountain Rich ABS (Casequare-related)", "DealSite"),
    ("db_sec", "DB Securities", "DB증권", "kr_securities", "securities", "Broker", True, "016610", 5, "Securities", "KRX"),
    ("eugene_inv_sec", "Eugene Investment & Securities", "유진투자증권", "kr_securities", "securities", "Camsquare structuring", True, "001200", 1, "Structuring / equity in Camsquare Ansan PFV (reported)", "IBTomato"),
    ("bookook_sec", "Bookook Securities", "부국증권", "kr_securities", "securities", "Broker", True, "001270", 5, "Securities", "KRX"),
    ("shinyeong_sec", "Shinyoung Securities", "신영증권", "kr_securities", "securities", "Broker", True, "001720", 5, "Securities", "KRX"),

    # ===== G. Asset managers / insurers / infra investors =====
    ("koramco_am", "Koramco Asset Management", "코람코자산운용", "kr_am", "asset_manager", "Casequare sponsor AM", False, None, 1, "Established Casequare Data Center PFV with LF", "DealSite"),
    ("igis_am", "IGIS Asset Management", "이지스자산운용", "kr_am", "asset_manager", "RE / DC REIT AM", False, None, 2, "Manages Bundang Hostway IDC via REIT vehicles", "IGIS REIT"),
    ("hana_alt_am", "Hana Alternative Asset Management", "하나대체투자자산운용", "kr_am", "asset_manager", "Seller of Bundang IDC", False, None, 2, "Sold Sejong Telecom Bundang IDC (2025)", "Econovill"),
    ("fine_partners_am", "Fine & Partners Asset Management", "파인앤파트너스자산운용", "kr_am", "asset_manager", "Bundang IDC buyer", False, None, 2, "Acquired Bundang IDC 2025", "Econovill"),
    ("korea_alt_am", "Korea Alternative Investment Asset Management", "한국대체투자자산운용", "kr_am", "asset_manager", "Camsquare structuring", False, None, 1, "Structuring Camsquare Ansan with Eugene", "IBTomato"),
    ("mirae_asset_am", "Mirae Asset Global Investments", "미래에셋자산운용", "kr_am", "asset_manager", "Asset manager", False, None, 3, "Large AM; AUM ≠ balance-sheet exposure", "Company"),
    ("samsung_am", "Samsung Asset Management", "삼성자산운용", "kr_am", "asset_manager", "Asset manager", False, None, 3, "Large AM", "Company"),
    ("kb_am", "KB Asset Management", "KB자산운용", "kr_am", "asset_manager", "Asset manager", False, None, 3, "KB AM", "Company"),
    ("shinhan_bnpp_am", "Shinhan Asset Management", "신한자산운용", "kr_am", "asset_manager", "Asset manager", False, None, 3, "Shinhan AM", "Company"),
    ("samsung_life", "Samsung Life Insurance", "삼성생명", "kr_insurance", "insurer", "Life insurer", True, "032830", 3, "Institutional investor; general infra", "KRX"),
    ("samsung_fire", "Samsung Fire & Marine", "삼성화재", "kr_insurance", "insurer", "P&C insurer", True, "000810", 3, "Institutional investor", "KRX"),
    ("db_ins", "DB Insurance", "DB손해보험", "kr_insurance", "insurer", "Casequare equity", True, "005830", 1, "Casequare PFV shareholder (~7.6%)", "DealSite"),
    ("tongyang_life", "Tongyang Life Insurance", "동양생명", "kr_insurance", "insurer", "Casequare senior lender", True, "082640", 1, "Senior tranche KRW 70bn Casequare Gasan (reported)", "DealSite"),
    ("hanwha_life", "Hanwha Life Insurance", "한화생명", "kr_insurance", "insurer", "Life insurer", True, "088350", 3, "Institutional investor", "KRX"),
    ("kyobo_life", "Kyobo Life Insurance", "교보생명", "kr_insurance", "insurer", "Life insurer", False, None, 3, "Institutional investor", "Company"),
    ("orange_life", "Orange Life / Shinhan Life", "신한라이프", "kr_insurance", "insurer", "Life insurer", False, None, 3, "Shinhan Group life", "Company"),
    ("admin_mutual", "Korea Local Government Officials' Mutual Aid Association", "대한지방행정공제회", "kr_am", "mutual_aid", "Camsquare investor", False, None, 1, "KRW 130bn investment in Ansan DC (reported)", "IBTomato"),
    ("nps_korea", "National Pension Service", "국민연금공단", "kr_am", "pension", "Pension", False, None, 4, "Largest KR institutional investor; no deal-specific DC edge here", "NPS"),

    # ===== H. Operators / suppliers / other =====
    ("lf_corp", "LF Corporation", "LF", "kr_operator", "company", "Casequare sponsor", True, "093050", 1, "Majority Casequare PFV shareholder (~66.9%); pledged shares as collateral", "DealSite"),
    ("kakao", "Kakao", "카카오", "kr_operator", "company", "Internet / cloud parent", True, "035720", 4, "Holding — do not auto-inherit Enterprise lease", "KRX"),
    ("kakao_enterprise", "Kakao Enterprise", "카카오엔터프라이즈", "kr_operator", "company", "Camsquare pre-lease tenant", False, None, 1, "Reported ~40% pre-lease on Camsquare Ansan", "IBTomato"),
    ("sejong_telecom", "Sejong Telecom", "세종텔레콤", "kr_operator", "company", "Bundang IDC operator/tenant", True, "036630", 2, "Operates Bundang IDC (colocation)", "KRX"),
    ("hostway_kr", "Hostway IDC Korea", "호스트웨이아이디씨", "kr_operator", "company", "Bundang long-term tenant", False, None, 2, "Long-term lease to 2034 on Bundang Hostway IDC", "IGIS REIT"),
    ("lg_cns", "LG CNS", "LG CNS", "kr_operator", "company", "IT services / DC", False, None, 4, "IT services; DC operations capability", "Company"),
    ("kakao_cloud", "Kakao Cloud", "카카오클라우드", "kr_operator", "company", "Cloud brand", False, None, 4, "Cloud brand under Kakao ecosystem", "Company"),
    ("kt_cloud", "KT Cloud", "KT클라우드", "kr_operator", "company", "Cloud / AI DC", False, None, 2, "LS ELECTRIC MOU for AI DC power", "LS ELECTRIC"),
    # Capitals / specialty lenders from Casequare syndicate
    ("hyundai_capital", "Hyundai Capital", "현대캐피탈", "kr_bank", "nbFI", "Casequare senior lender", False, None, 1, "Senior KRW 30bn Casequare (reported)", "DealSite"),
    ("woori_fin_capital", "Woori Financial Capital", "우리금융캐피탈", "kr_bank", "nbFI", "Casequare senior lender", True, "033530", 1, "Senior KRW 20bn Casequare (reported)", "DealSite"),
    ("shinhan_capital", "Shinhan Capital", "신한캐피탈", "kr_bank", "nbFI", "Casequare senior lender", False, None, 1, "Senior KRW 10bn Casequare (reported)", "DealSite"),
    ("kb_capital", "KB Capital", "KB캐피탈", "kr_bank", "nbFI", "Casequare senior lender", False, None, 1, "Senior KRW 30bn Casequare (reported)", "DealSite"),
    ("hyundai_commercial", "Hyundai Commercial", "현대커머셜", "kr_bank", "nbFI", "Casequare senior lender", False, None, 1, "Senior KRW 20bn Casequare (reported)", "DealSite"),
    ("woori_ib", "Woori Investment Bank / Comprehensive Finance", "우리종합금융", "kr_securities", "nbFI", "Casequare senior lender", True, "010050", 1, "Senior KRW 20bn Casequare (reported)", "DealSite"),
    ("mountain_rich", "Mountain Rich 1st Co., Ltd.", "마운틴리치제일차", "project_finance", "spv", "Casequare ABS vehicle", False, None, 1, "ABS SPV raising KRW 25bn for Casequare senior", "DealSite"),
]


def node_from(row: tuple) -> dict:
    id_, name, name_ko, group, etype, role, listed, ticker, exp, activities, src = row
    classes = {
        1: "confirmed_aidc_project",
        2: "confirmed_dc_finance",
        3: "general_pf",
        4: "sector_sensitivity",
        5: "research_candidate",
    }
    return {
        "id": id_,
        "name": name,
        "name_ko": name_ko,
        "group": group,
        "sector": {
            "kr_construction": "Construction / EPC",
            "kr_trust": "Real Estate Trust",
            "kr_savings": "Savings Bank",
            "kr_cooperative": "Cooperative Finance",
            "kr_bank": "Banking",
            "kr_securities": "Securities",
            "kr_am": "Asset Management / Institutional",
            "kr_insurance": "Insurance",
            "kr_operator": "DC Operator / Developer",
            "project_finance": "Project Finance Vehicle",
        }.get(group, "Korean Financial / Industrial"),
        "entity_type": etype,
        "role": role,
        "description": f"{activities}. Exposure class: {classes[exp]} ({exp}). Source hint: {src}. Not a fabricated bilateral US SPV counterparty unless edges say so.",
        "listed": listed,
        "ticker": ticker,
        "exchange": "KRX" if listed and ticker else None,
        "quote_currency": "KRW" if listed else None,
        "listing_note": None,
        "display_size": 1.05 if exp <= 2 else (0.85 if exp >= 5 else 0.95),
        "source_status": "VERIFIED" if exp <= 2 else ("INFERRED" if exp == 3 else "UNKNOWN"),
        "source_ids": [],
        "key_drivers": [classes[exp]],
        "region": "KR",
        "country": "KR",
        "pf_exposure_class": classes[exp],
        "pf_exposure_class_num": exp,
        "is_demo": False,
    }


def edge(id_, src, tgt, rel, channel, label, impact, expl, *, status="VERIFIED", amount=None, note="", tclass="direct_contract", sources=None):
    return {
        "id": id_,
        "source": src,
        "target": tgt,
        "relationship_type": rel,
        "impact_channel": channel,
        "label": label,
        "impact_label": impact,
        "source_status": status,
        "source_ids": sources or [],
        "contract_ids": [],
        "commercial_ids": [],
        "amount_usd_m": amount,
        "amount_note": note,
        "roles": [],
        "explanation": expl,
        "transmission_class": tclass,
    }


def main() -> None:
    net_path = PF / "network.json"
    proj_path = PF / "projects.json"
    net = json.loads(net_path.read_text(encoding="utf-8"))
    proj = json.loads(proj_path.read_text(encoding="utf-8"))

    # Sources
    new_sources = [
        {
            "id": "S_CASEQUARE",
            "title": "LF Gasan Casequare Data Center PF financing",
            "publisher": "DealSite / company disclosures via press",
            "date": "2024-05",
            "url": "https://dealsite.co.kr/articles/121975",
            "used_for": "CasequareDataCenterPFV lenders, equity, Hyundai E&C completion guarantee, KRW 3450bn PF",
            "kind": "press",
        },
        {
            "id": "S_KIWOOM_REFIN",
            "title": "Kiwoom Securities Casequare refinancing underwrite",
            "publisher": "Sedaily",
            "date": "2025-02-24",
            "url": "https://www.sedaily.com/article/14031532",
            "used_for": "Kiwoom total underwrite ~KRW 3800bn refinancing",
            "kind": "press",
        },
        {
            "id": "S_CAMSQUARE",
            "title": "Camsquare Ansan Data Center PF",
            "publisher": "IBTomato",
            "date": "2025-01",
            "url": "https://96.newstomato.com/ReadNews.aspx?no=1249683",
            "used_for": "KRW 8340bn PF; Samsung Securities arranger; Hyundai E&C EPC; Kakao Enterprise pre-lease; Admin Mutual KRW 130bn",
            "kind": "press",
        },
        {
            "id": "S_BUNDANG_IDC",
            "title": "Sejong Telecom Bundang IDC sale / Hostway lease",
            "publisher": "Econovill / IGIS REIT",
            "date": "2025-07",
            "url": "https://www.econovill.com/news/articleView.html?idxno=702962",
            "used_for": "Bundang IDC ownership transfer; Hostway long-term lease",
            "kind": "press",
        },
    ]
    existing_src = {s["id"] for s in net["sources"]}
    for s in new_sources:
        if s["id"] not in existing_src:
            net["sources"].append(s)

    by_id = {n["id"]: n for n in net["nodes"]}
    added = 0
    for row in ENTITIES:
        n = node_from(row)
        if n["id"] in by_id:
            # Upgrade existing node metadata without wiping US-linked fields
            old = by_id[n["id"]]
            for k in ("group", "name_ko", "sector", "entity_type", "role", "region", "country",
                      "pf_exposure_class", "pf_exposure_class_num", "description", "display_size", "source_status"):
                if k in n:
                    old[k] = n[k]
            if n.get("ticker") and not old.get("ticker"):
                old["ticker"] = n["ticker"]
                old["listed"] = n["listed"]
                old["exchange"] = n["exchange"]
                old["quote_currency"] = n["quote_currency"]
        else:
            net["nodes"].append(n)
            by_id[n["id"]] = n
            added += 1

    # Ensure existing KR operators keep region
    for nid in ("samsung_sds", "sk_telecom", "kt", "naver", "ls_electric", "hd_hyundai_electric",
                "hyosung_heavy", "doosan_enerbility", "lg_electronics", "samsung", "sk_hynix",
                "sds_gumi_aidc", "skt_ulsan_aidc"):
        if nid in by_id:
            by_id[nid]["region"] = "KR"
            by_id[nid]["country"] = "KR"

    # Reclassify operators already present
    if "samsung_sds" in by_id:
        by_id["samsung_sds"]["group"] = "kr_operator"
        by_id["samsung_sds"]["pf_exposure_class"] = "confirmed_aidc_project"
        by_id["samsung_sds"]["pf_exposure_class_num"] = 1
    if "sk_telecom" in by_id:
        by_id["sk_telecom"]["group"] = "kr_operator"
        by_id["sk_telecom"]["pf_exposure_class"] = "confirmed_aidc_project"
        by_id["sk_telecom"]["pf_exposure_class_num"] = 1
    if "kt" in by_id:
        by_id["kt"]["group"] = "kr_operator"
        by_id["kt"]["pf_exposure_class"] = "confirmed_dc_finance"
        by_id["kt"]["pf_exposure_class_num"] = 2
    if "ls_electric" in by_id:
        by_id["ls_electric"]["group"] = "kr_operator"
        by_id["ls_electric"]["pf_exposure_class"] = "confirmed_dc_finance"
        by_id["ls_electric"]["pf_exposure_class_num"] = 2

    # ---- New project nodes ----
    projects_nodes = [
        {
            "id": "casequare_gasan",
            "name": "Casequare Gasan Data Center",
            "name_ko": "케이스퀘어 가산 데이터센터",
            "group": "project_finance",
            "sector": "Korean Data Center Project",
            "entity_type": "project",
            "role": "Domestic DC PF project",
            "description": "Seoul Geumcheon-gu Gasan DC. CasequareDataCenterPFV. Target completion ~2025. Hyundai E&C EPC with completion guarantee. KRW 3.45tn PF (2024) then refinancing.",
            "listed": False, "ticker": None, "exchange": None, "quote_currency": None, "listing_note": None,
            "display_size": 1.35, "source_status": "VERIFIED", "source_ids": ["S_CASEQUARE", "S_KIWOOM_REFIN"],
            "key_drivers": ["confirmed_aidc_project"], "region": "KR", "country": "KR",
            "pf_exposure_class": "confirmed_aidc_project", "pf_exposure_class_num": 1, "is_demo": False,
        },
        {
            "id": "casequare_pfv",
            "name": "Casequare Data Center PFV",
            "name_ko": "케이스퀘어데이터센터PFV",
            "group": "project_finance",
            "sector": "Korean Data Center PFV",
            "entity_type": "spv",
            "role": "Project borrower / PFV",
            "description": "SPC established Jun 2021 by Koramco AM for Gasan DC. Equity: LF ~66.9%, DB Ins ~7.6%, Koramco Trust ~5.5%, others. Borrower under KRW PF loans.",
            "listed": False, "ticker": None, "exchange": None, "quote_currency": None, "listing_note": None,
            "display_size": 1.2, "source_status": "VERIFIED", "source_ids": ["S_CASEQUARE"],
            "key_drivers": ["confirmed_aidc_project"], "region": "KR", "country": "KR",
            "pf_exposure_class": "confirmed_aidc_project", "pf_exposure_class_num": 1, "is_demo": False,
        },
        {
            "id": "camsquare_ansan",
            "name": "Camsquare Ansan Data Center",
            "name_ko": "캄스퀘어 안산 데이터센터",
            "group": "project_finance",
            "sector": "Korean Data Center Project",
            "entity_type": "project",
            "role": "Domestic DC PF project",
            "description": "Ansan Seonggok-dong DC in Sihwa industrial complex. CamsquareAnsanDataCenterPFV. Hyundai E&C EPC KRW 573.5bn contract; KRW 8340bn senior PF; Kakao Enterprise ~40% pre-lease (reported).",
            "listed": False, "ticker": None, "exchange": None, "quote_currency": None, "listing_note": None,
            "display_size": 1.35, "source_status": "VERIFIED", "source_ids": ["S_CAMSQUARE"],
            "key_drivers": ["confirmed_aidc_project"], "region": "KR", "country": "KR",
            "pf_exposure_class": "confirmed_aidc_project", "pf_exposure_class_num": 1, "is_demo": False,
        },
        {
            "id": "camsquare_pfv",
            "name": "Camsquare Ansan Data Center PFV",
            "name_ko": "캄스퀘어안산데이터센터PFV",
            "group": "project_finance",
            "sector": "Korean Data Center PFV",
            "entity_type": "spv",
            "role": "Project borrower / PFV",
            "description": "PFV borrower for Ansan DC. Hyundai E&C holds ~13.2% equity (book KRW 5bn). Samsung Securities arranged PF.",
            "listed": False, "ticker": None, "exchange": None, "quote_currency": None, "listing_note": None,
            "display_size": 1.2, "source_status": "VERIFIED", "source_ids": ["S_CAMSQUARE"],
            "key_drivers": ["confirmed_aidc_project"], "region": "KR", "country": "KR",
            "pf_exposure_class": "confirmed_aidc_project", "pf_exposure_class_num": 1, "is_demo": False,
        },
        {
            "id": "bundang_hostway_idc",
            "name": "Bundang Hostway IDC",
            "name_ko": "분당 호스트웨이 IDC",
            "group": "project_finance",
            "sector": "Korean Data Center Asset",
            "entity_type": "project",
            "role": "Stabilized DC asset",
            "description": "Seongnam Bundang Yatap IDC, ~12.5MW. Hostway long-term lease to 2034. Ownership via REIT/AM structures (IGIS / Fine & Partners transaction history).",
            "listed": False, "ticker": None, "exchange": None, "quote_currency": None, "listing_note": None,
            "display_size": 1.15, "source_status": "VERIFIED", "source_ids": ["S_BUNDANG_IDC"],
            "key_drivers": ["confirmed_dc_finance"], "region": "KR", "country": "KR",
            "pf_exposure_class": "confirmed_dc_finance", "pf_exposure_class_num": 2, "is_demo": False,
        },
    ]
    for n in projects_nodes:
        if n["id"] not in by_id:
            net["nodes"].append(n)
            by_id[n["id"]] = n
            added += 1

    # ---- Verified edges (Casequare / Camsquare / Bundang) ----
    # Amounts stored as USD m approximate only when helpful; prefer note with KRW
    new_edges = [
        edge("pf_lf_casequare", "lf_corp", "casequare_pfv", "EQUITY_SPONSOR", "equity",
             "LF majority equity ~66.9%", "Sponsor equity",
             "LF is majority shareholder of CasequareDataCenterPFV; pledged shares as loan collateral.",
             sources=["S_CASEQUARE"], note="~66.9% equity; collateral pledge KRW 97bn reported"),
        edge("pf_casequare_proj", "casequare_pfv", "casequare_gasan", "PROJECT_SPV", "facility",
             "PFV ↔ Gasan project", "Project vehicle",
             "Casequare PFV develops/owns Gasan data center project.",
             sources=["S_CASEQUARE"]),
        edge("pf_hyundai_casequare_epc", "hyundai_enc", "casequare_gasan", "EPC_CONTRACT", "contract",
             "Hyundai E&C EPC + completion guarantee", "Construction / 책임준공",
             "Hyundai E&C is EPC contractor with completion guarantee (책임준공 확약). Contract progress recognized in filings context.",
             sources=["S_CASEQUARE"], note="Contract amount context KRW 117.3bn recognized progress — full award larger"),
        edge("pf_koramco_am_casequare", "koramco_am", "casequare_pfv", "ASSET_MANAGER", "equity",
             "Koramco AM sponsor/structuring", "Asset manager",
             "Koramco Asset Management established Casequare PFV with LF and investors.",
             sources=["S_CASEQUARE"]),
        edge("pf_koramco_trust_eq", "koramco_trust", "casequare_pfv", "EQUITY_INVESTMENT", "equity",
             "Koramco Trust equity ~5.52%", "Equity",
             "Koramco Asset Trust holds equity in Casequare PFV (reported ~5.52%). Trust equity ≠ borrower liability.",
             sources=["S_CASEQUARE"]),
        edge("pf_db_ins_eq", "db_ins", "casequare_pfv", "EQUITY_INVESTMENT", "equity",
             "DB Insurance equity ~7.59%", "Equity",
             "DB Insurance shareholder in Casequare PFV.",
             sources=["S_CASEQUARE"]),
        # Senior lenders (tranche A) — amounts in KRW bn via note; amount_usd_m approx @1300
        edge("pf_nh_casequare", "nh_bank", "casequare_pfv", "PROJECT_LOAN", "financial",
             "NH Bank senior KRW 40bn", "Senior loan",
             "Reported senior tranche A lender. Arranger role distinct from full loss — exposure is loan principal share.",
             sources=["S_CASEQUARE"], amount=31, note="KRW 40bn reported"),
        edge("pf_tongyang_casequare", "tongyang_life", "casequare_pfv", "PROJECT_LOAN", "financial",
             "Tongyang Life senior KRW 70bn", "Senior loan",
             "Reported senior tranche A lender KRW 70bn.",
             sources=["S_CASEQUARE"], amount=54, note="KRW 70bn reported"),
        edge("pf_hyundai_cap_casequare", "hyundai_capital", "casequare_pfv", "PROJECT_LOAN", "financial",
             "Hyundai Capital senior KRW 30bn", "Senior loan",
             "Reported senior lender KRW 30bn.", sources=["S_CASEQUARE"], amount=23, note="KRW 30bn"),
        edge("pf_woori_cap_casequare", "woori_fin_capital", "casequare_pfv", "PROJECT_LOAN", "financial",
             "Woori Financial Capital senior KRW 20bn", "Senior loan",
             "Reported senior lender KRW 20bn.", sources=["S_CASEQUARE"], amount=15, note="KRW 20bn"),
        edge("pf_shinhan_cap_casequare", "shinhan_capital", "casequare_pfv", "PROJECT_LOAN", "financial",
             "Shinhan Capital senior KRW 10bn", "Senior loan",
             "Reported senior lender KRW 10bn.", sources=["S_CASEQUARE"], amount=8, note="KRW 10bn"),
        edge("pf_kb_cap_casequare", "kb_capital", "casequare_pfv", "PROJECT_LOAN", "financial",
             "KB Capital senior KRW 30bn", "Senior loan",
             "Reported senior lender KRW 30bn.", sources=["S_CASEQUARE"], amount=23, note="KRW 30bn"),
        edge("pf_hyundai_com_casequare", "hyundai_commercial", "casequare_pfv", "PROJECT_LOAN", "financial",
             "Hyundai Commercial senior KRW 20bn", "Senior loan",
             "Reported senior lender KRW 20bn.", sources=["S_CASEQUARE"], amount=15, note="KRW 20bn"),
        edge("pf_woori_ib_casequare", "woori_ib", "casequare_pfv", "PROJECT_LOAN", "financial",
             "Woori Comprehensive Finance senior KRW 20bn", "Senior loan",
             "Reported senior lender KRW 20bn.", sources=["S_CASEQUARE"], amount=15, note="KRW 20bn"),
        edge("pf_thek_casequare", "thek_savings", "casequare_pfv", "PROJECT_LOAN", "financial",
             "The-K Savings Bank senior KRW 10bn", "Senior loan",
             "Reported senior lender KRW 10bn — savings bank DC PF exposure.",
             sources=["S_CASEQUARE"], amount=8, note="KRW 10bn"),
        edge("pf_kis_junior_casequare", "korea_inv_sec", "casequare_pfv", "PROJECT_LOAN", "financial",
             "Korea Investment Securities junior KRW 70bn", "Junior / arranger",
             "Junior tranche B KRW 70bn; also arranged the 2024 PF. Arranged amount ≠ retained economic exposure after sell-down.",
             sources=["S_CASEQUARE"], amount=54, note="KRW 70bn junior reported"),
        edge("pf_mountain_casequare", "mountain_rich", "casequare_pfv", "PROJECT_LOAN", "financial",
             "Mountain Rich ABS KRW 25bn", "Securitized senior",
             "ABS SPV funded KRW 25bn of senior; Yuanta underwrote private bond with purchase commitment.",
             sources=["S_CASEQUARE"], amount=19, note="KRW 25bn"),
        edge("pf_yuanta_mountain", "yuanta_sec", "mountain_rich", "CREDIT_ENHANCEMENT", "financial",
             "Yuanta purchase commitment / underwrite", "Liquidity / credit support",
             "Reported private-bond underwrite/purchase commitment for Mountain Rich ABS. Guarantor ≠ full principal automatic loss.",
             sources=["S_CASEQUARE"], tclass="direct_contract"),
        edge("pf_kiwoom_refin", "kiwoom_sec", "casequare_pfv", "REFINANCING_UNDERWRITE", "financial",
             "Kiwoom refinancing total underwrite ~KRW 3800bn", "Underwriter / takeout",
             "2025 press: Kiwoom total-underwrote refinancing. Underwrite commitment is contingent liquidity — model as enhancement, not automatic loan loss.",
             sources=["S_KIWOOM_REFIN"], amount=292, note="KRW 3800bn refinancing context"),

        # Camsquare Ansan
        edge("pf_camsquare_proj", "camsquare_pfv", "camsquare_ansan", "PROJECT_SPV", "facility",
             "PFV ↔ Ansan project", "Project vehicle",
             "Camsquare Ansan PFV owns/develops Ansan DC.", sources=["S_CAMSQUARE"]),
        edge("pf_hyundai_camsquare_epc", "hyundai_enc", "camsquare_ansan", "EPC_CONTRACT", "contract",
             "Hyundai E&C EPC KRW 573.5bn + equity 13.2%", "EPC + sponsor equity",
             "Hyundai E&C EPC award KRW 573.5bn; also ~13.2% PFV equity (book KRW 5bn). Completion guarantee reported.",
             sources=["S_CAMSQUARE"], amount=441, note="EPC KRW 573.5bn"),
        edge("pf_hyundai_camsquare_eq", "hyundai_enc", "camsquare_pfv", "EQUITY_INVESTMENT", "equity",
             "Hyundai E&C PFV equity ~13.2%", "Equity",
             "Equity stake separate from EPC receivables.", sources=["S_CAMSQUARE"], amount=4, note="Book KRW 5bn"),
        edge("pf_samsung_sec_camsquare", "samsung_sec", "camsquare_pfv", "ARRANGER", "financial",
             "Samsung Securities PF arranger KRW 8340bn", "Arranger",
             "Arranged KRW 8340bn PF. Arranger ≠ automatic full principal exposure.",
             sources=["S_CAMSQUARE"], amount=642, note="Facility KRW 8340bn — arranged size"),
        edge("pf_eugene_camsquare", "eugene_inv_sec", "camsquare_pfv", "STRUCTURING_EQUITY", "equity",
             "Eugene Inv. structuring / equity", "Structuring",
             "Reported structuring partner with Korea Alternative AM; equity in PFV.",
             sources=["S_CAMSQUARE"]),
        edge("pf_korea_alt_camsquare", "korea_alt_am", "camsquare_pfv", "ASSET_MANAGER", "equity",
             "Korea Alternative AM structuring", "Asset manager",
             "Structuring / capital raise support for Camsquare Ansan.", sources=["S_CAMSQUARE"]),
        edge("pf_admin_camsquare", "admin_mutual", "camsquare_ansan", "EQUITY_INVESTMENT", "equity",
             "Admin Mutual Aid KRW 130bn", "Institutional equity",
             "Reported KRW 130bn investment — first DC investment by the mutual aid association.",
             sources=["S_CAMSQUARE"], amount=100, note="KRW 130bn"),
        edge("pf_kakao_ent_lease", "kakao_enterprise", "camsquare_ansan", "TENANT_LEASE", "customer",
             "Kakao Enterprise ~40% pre-lease", "Pre-lease / offtake",
             "Reported senior lease covering ~40% of facility — reduces vacancy risk; not CoreWeave.",
             sources=["S_CAMSQUARE"]),
        edge("pf_kakao_parent", "kakao", "kakao_enterprise", "PARENT_AFFILIATE", "equity",
             "Kakao → Kakao Enterprise", "Affiliate",
             "Parent/affiliate link. Holding company does not automatically inherit lease obligations.",
             sources=["S_CAMSQUARE"], status="INFERRED"),

        # Bundang
        edge("pf_hostway_bundang", "hostway_kr", "bundang_hostway_idc", "TENANT_LEASE", "customer",
             "Hostway lease to 2034", "Long-term lease",
             "Whole-building long-term lease supporting stabilized DC cash flows.",
             sources=["S_BUNDANG_IDC"]),
        edge("pf_sejong_bundang", "sejong_telecom", "bundang_hostway_idc", "OPERATOR", "facility",
             "Sejong Telecom operations / prior structure", "Operator",
             "Sejong Telecom associated with Bundang IDC operations/colocation history.",
             sources=["S_BUNDANG_IDC"], status="INFERRED"),
        edge("pf_igis_bundang", "igis_am", "bundang_hostway_idc", "ASSET_MANAGER", "equity",
             "IGIS AM / REIT DC investment", "Asset manager",
             "IGIS Value Plus REIT materials describe Bundang Hostway IDC investment.",
             sources=["S_BUNDANG_IDC"]),
        edge("pf_fine_bundang", "fine_partners_am", "bundang_hostway_idc", "EQUITY_INVESTMENT", "equity",
             "Fine & Partners acquired Bundang IDC (2025)", "Ownership",
             "2025 acquisition from Hana Alternative AM (reported).",
             sources=["S_BUNDANG_IDC"]),
        edge("pf_hana_alt_bundang", "hana_alt_am", "bundang_hostway_idc", "PRIOR_OWNER", "equity",
             "Hana Alternative prior owner / seller", "Prior ownership",
             "Seller in 2025 Bundang IDC transaction.",
             sources=["S_BUNDANG_IDC"]),

        # Sector transmission hubs (qualitative) — US shock → KR funding market
        edge("pf_cw_kr_funding", "coreweave", "mg_federation", "FUNDING_MARKET", "financial",
             "US AI infra stress → KR cooperative funding sentiment", "Path A qualitative",
             "No verified CoreWeave–MG loan. Edge represents conditional funding-market sentiment only (class C).",
             status="ASSUMED", tclass="funding_market"),
        edge("pf_capex_kr_const", "microsoft", "hyundai_enc", "SECTOR_DEMAND", "supply_chain",
             "Hyperscaler CAPEX → KR EPC demand", "Path B sector",
             "Sector demand for DC construction. Hyundai has verified domestic DC EPCs; US CAPEX cut is not automatic cancellation of those contracts.",
             status="INFERRED", tclass="sector_demand", sources=["S_CAPEX_CNBC"]),
        edge("pf_capex_kr_equip", "amazon", "ls_electric", "SECTOR_DEMAND", "supply_chain",
             "Hyperscaler CAPEX → KR power equipment orders", "Path B sector",
             "LS ELECTRIC discloses NA hyperscale DC wins — sector sensitivity, not Helios bilateral.",
             status="INFERRED", tclass="sector_demand"),
    ]

    existing_e = {e["id"] for e in net["edges"]}
    e_added = 0
    for e in new_edges:
        if e["id"] not in existing_e:
            # Only add if both endpoints exist
            if e["source"] in by_id and e["target"] in by_id:
                net["edges"].append(e)
                e_added += 1

    # Project dossiers
    new_projects = [
        {
            "id": "casequare_gasan",
            "name": "Casequare Gasan Data Center",
            "location": "Gasan-dong, Geumcheon-gu, Seoul, Korea",
            "country": "KR",
            "developer": "lf_corp",
            "owner": "casequare_pfv",
            "spv": "casequare_pfv",
            "tenant": None,
            "construction_stage": "under_construction",
            "target_completion": "2025-05 (press target)",
            "critical_it_load_mw": None,
            "capacity_note": "B3–11F, GFA ~43,200㎡ on ~6,141㎡ site",
            "lease_structure": "Not fully disclosed in cited press",
            "capex_native_krw_b": None,
            "senior_debt_usd_m": None,
            "senior_debt_krw_b": 3450,
            "debt_rate_type": "unknown",
            "debt_rate_note": "2024 PF KRW 3450bn; 2025 refinancing ~KRW 3800bn (Kiwoom) — coupon not fully public here",
            "baseline_dscr": None,
            "dscr_status": "UNKNOWN",
            "gpu_rent_exposure": "none_direct",
            "hyperscaler_capex_exposure": "domestic_demand_and_refi",
            "floating_debt_usd_m": None,
            "fixed_debt_usd_m": None,
            "region": "KR",
            "korean_counterparties": [
                "lf_corp", "hyundai_enc", "koramco_am", "koramco_trust", "db_ins", "nh_bank",
                "tongyang_life", "korea_inv_sec", "kiwoom_sec", "thek_savings", "yuanta_sec",
            ],
            "korean_link_class": "direct_contract",
            "source_ids": ["S_CASEQUARE", "S_KIWOOM_REFIN"],
            "verification_date": "2026-10-21",
            "missing": ["CFADS", "DSCR covenant", "exact all-in rate", "tenant schedule"],
            "completion_guarantee": "Hyundai E&C 책임준공",
        },
        {
            "id": "camsquare_ansan",
            "name": "Camsquare Ansan Data Center",
            "location": "Seonggok-dong, Danwon-gu, Ansan, Korea",
            "country": "KR",
            "developer": "camsquare_pfv",
            "owner": "camsquare_pfv",
            "spv": "camsquare_pfv",
            "tenant": "kakao_enterprise",
            "construction_stage": "under_construction",
            "target_completion": "2027-12 phase1 / 2028-12 phase2 (reported)",
            "critical_it_load_mw": None,
            "capacity_note": "GFA ~76,459㎡; B5–7F",
            "lease_structure": "Kakao Enterprise pre-lease ~40% (reported)",
            "senior_debt_krw_b": 8340,
            "debt_rate_type": "unknown",
            "epc_krw_b": 573.5,
            "baseline_dscr": None,
            "dscr_status": "UNKNOWN",
            "gpu_rent_exposure": "none_direct",
            "hyperscaler_capex_exposure": "domestic_cloud_demand",
            "region": "KR",
            "korean_counterparties": [
                "hyundai_enc", "samsung_sec", "eugene_inv_sec", "korea_alt_am",
                "admin_mutual", "kakao_enterprise",
            ],
            "korean_link_class": "direct_contract",
            "source_ids": ["S_CAMSQUARE"],
            "verification_date": "2026-10-21",
            "missing": ["full lender list by tranche", "CFADS", "coupon"],
            "completion_guarantee": "Hyundai E&C 책임준공 (reported)",
        },
        {
            "id": "bundang_hostway_idc",
            "name": "Bundang Hostway IDC",
            "location": "Yatap-dong, Bundang-gu, Seongnam, Korea",
            "country": "KR",
            "developer": None,
            "owner": "fine_partners_am",
            "spv": None,
            "tenant": "hostway_kr",
            "construction_stage": "stabilized_operating",
            "target_completion": None,
            "critical_it_load_mw": 12.5,
            "lease_structure": "Hostway whole-building lease to Jun 2034",
            "baseline_dscr": None,
            "dscr_status": "UNKNOWN",
            "gpu_rent_exposure": "none_direct",
            "region": "KR",
            "korean_counterparties": ["hostway_kr", "sejong_telecom", "igis_am", "fine_partners_am", "hana_alt_am"],
            "source_ids": ["S_BUNDANG_IDC"],
            "verification_date": "2026-10-21",
            "missing": ["purchase price", "debt on asset"],
        },
    ]
    existing_p = {p["id"] for p in proj["projects"]}
    for p in new_projects:
        if p["id"] not in existing_p:
            proj["projects"].append(p)

    # Hub node for Korean PF market (sector aggregation — not a legal borrower)
    if "kr_pf_market" not in by_id:
        net["nodes"].append({
            "id": "kr_pf_market",
            "name": "Korean Data Center PF Market (aggregate)",
            "name_ko": "한국 DC PF 시장(집계)",
            "group": "kr_bank",
            "sector": "PF Market Aggregate",
            "entity_type": "market_aggregate",
            "role": "Funding-market sentiment hub",
            "description": "Analytical hub for Path A/C funding-market transmission. Not a legal entity and not a loan counterparty.",
            "listed": False, "ticker": None, "exchange": None, "quote_currency": None, "listing_note": None,
            "display_size": 1.1, "source_status": "ASSUMED", "source_ids": [],
            "key_drivers": ["funding_market"], "region": "KR", "country": "KR",
            "pf_exposure_class": "sector_sensitivity", "pf_exposure_class_num": 4, "is_demo": False,
        })
        added += 1
        by_id["kr_pf_market"] = net["nodes"][-1]

    for e in [
        edge("pf_cw_kr_market", "coreweave", "kr_pf_market", "FUNDING_MARKET", "financial",
             "CoreWeave distress → KR DC PF sentiment", "Path A",
             "Explicit ASSUMED funding-market pass-through hub. No bilateral loan.",
             status="ASSUMED", tclass="funding_market"),
        edge("pf_kr_market_casequare", "kr_pf_market", "casequare_pfv", "FUNDING_MARKET", "financial",
             "Refinancing / credit conditions", "Path C",
             "Sentiment may affect refinancing terms — not automatic default.",
             status="ASSUMED", tclass="funding_market"),
        edge("pf_kr_market_camsquare", "kr_pf_market", "camsquare_pfv", "FUNDING_MARKET", "financial",
             "Refinancing / credit conditions", "Path C",
             "Sentiment channel for under-construction KR DC PF.",
             status="ASSUMED", tclass="funding_market"),
        edge("pf_kr_market_sds", "kr_pf_market", "sds_gumi_aidc", "FUNDING_MARKET", "financial",
             "Domestic AIDC financing conditions", "Path C",
             "Gumi project financing terms may tighten under risk-off — debt terms still undisclosed.",
             status="ASSUMED", tclass="funding_market"),
    ]:
        if e["id"] not in existing_e and e["source"] in by_id and e["target"] in by_id:
            net["edges"].append(e)
            e_added += 1

    net["meta"]["name"] = "CONTAGION — AI Data Center PF (US → Korea)"
    net["meta"]["as_of"] = "2026-10-21"
    net["meta"]["disclaimer"] = (
        "Primary question: CoreWeave distress or Big Tech AI CAPEX cuts → Korean DC development & PF. "
        "pf_exposure_class 1–2 only may be verified DC relationships. Classes 3–5 are not confirmed AI DC counterparties. "
        "Arranger ≠ full loss. Trust ≠ borrower debt. Holding ≠ subsidiary loan."
    )

    net_path.write_text(json.dumps(net, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    proj_path.write_text(json.dumps(proj, ensure_ascii=False, indent=2), encoding="utf-8")

    kr = [n for n in net["nodes"] if n.get("region") == "KR" or n.get("country") == "KR"]
    from collections import Counter
    print(f"nodes={len(net['nodes'])} edges={len(net['edges'])} added_nodes={added} added_edges={e_added}")
    print(f"KR entities={len(kr)} by group={dict(Counter(n.get('group') for n in kr))}")
    print(f"by exposure={dict(Counter(n.get('pf_exposure_class','?') for n in kr))}")
    print(f"projects={len(proj['projects'])}")


if __name__ == "__main__":
    main()
