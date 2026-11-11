import os
import json
import datetime
import requests
import gspread

TARAYICI_URL = "https://scanner.tradingview.com/turkey/scan"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

E_TABLO = "Borsaİstanbul"
SEKME = "SpotVerileri"
ILK_SATIR = 3          # 1-2. satırlar başlık, veri 3. satırdan başlar

SEKTOR = {
    "Finance": "Finans",
    "Health Technology": "Sağlık Teknolojisi",
    "Health Services": "Sağlık Hizmetleri",
    "Consumer Durables": "Dayanıklı Tüketim",
    "Consumer Non-Durables": "Dayanıksız Tüketim",
    "Consumer Services": "Tüketici Hizmetleri",
    "Distribution Services": "Dağıtım Hizmetleri",
    "Electronic Technology": "Elektronik Teknoloji",
    "Energy Minerals": "Enerji/Madencilik",
    "Industrial Services": "Endüstriyel Hizmetler",
    "Miscellaneous": "Diğer",
    "Non-Energy Minerals": "Maden (Enerji Dışı)",
    "Process Industries": "Süreç Endüstrileri",
    "Producer Manufacturing": "Üretici İmalat",
    "Retail Trade": "Perakende Ticaret",
    "Technology Services": "Teknoloji Hizmetleri",
    "Transportation": "Ulaştırma",
    "Utilities": "Kamu Hizmetleri",
    "Commercial Services": "Ticari Hizmetler",
    "Communications": "İletişim",
}


# ---- Dönüşümler: fonksiyon(değer, satırın_tüm_alanları) ----
def sektor(x, v):
    return SEKTOR.get(x, x)


def derece(x, v):
    if x is None:
        return ""
    if x <= -0.5:
        return "Güçlü Sat"
    if x < -0.1:
        return "Sat"
    if x <= 0.1:
        return "Nötr"
    if x < 0.5:
        return "Al"
    return "Güçlü Al"


def _tarih(x):
    return datetime.datetime.fromtimestamp(x, tz=datetime.timezone.utc)


def tarih(x, v):                      # Unix saniye -> gg.aa.yyyy
    return _tarih(x).strftime("%d.%m.%Y") if x else ""


def donem(x, v):                      # dönem sonu tarihinden "2026-Q1"
    if not x:
        return ""
    t = _tarih(x)
    return f"{t.year}-Q{(t.month - 1) // 3 + 1}"


def ev_ebit(x, v):                    # FD/FVÖK ≈ İD ÷ Faaliyet geliri
    ev, ebit = v.get("enterprise_value_current"), v.get("oper_income_ttm")
    return ev / ebit if ev is not None and ebit and ebit > 0 else ""


def nakit_borc(x, v):                 # Eldeki nakit ÷ Toplam borç
    nakit, borc = v.get("cash_n_short_term_invest_fq"), v.get("total_debt_fq")
    return nakit / borc if nakit is not None and borc and borc > 0 else ""


# ---- Sütunlar: (başlık, TradingView alanı, dönüşüm) -> sırayla A, B, C ... ----
SUTUNLAR = [
    ("Sembol", "name", None),                                                  # A
    ("Şirket Adı", "description", None),                                       # B
    ("Sektör", "sector", sektor),                                              # C
    ("Fiyat", "close", None),                                                  # D
    ("Değ %", "change", None),                                                 # E
    ("Hacim", "volume", None),                                                 # F
    ("Göreceli hacim", "relative_volume_10d_calc", None),                      # G
    ("Pys değ", "market_cap_basic", None),                                     # H
    ("FKO", "price_earnings_ttm", None),                                       # I
    ("EPS Seyreltilmiş TTM", "earnings_per_share_diluted_ttm", None),          # J
    ("EPS Büyüme TTM YY", "earnings_per_share_diluted_yoy_growth_ttm", None),  # K
    ("Tmt getirisi % TTM", "dividends_yield_current", None),                   # L
    ("Perf % 1H", "Perf.W", None),                                             # M
    ("Perf % 1A", "Perf.1M", None),                                            # N
    ("Perf % 3A", "Perf.3M", None),                                            # O
    ("Perf % 6A", "Perf.6M", None),                                            # P
    ("Perf % YP", "Perf.YTD", None),                                           # Q
    ("Perf % 1Y", "Perf.Y", None),                                             # R
    ("Perf % 5Y", "Perf.5Y", None),                                            # S
    ("Perf % 10Y", "Perf.10Y", None),                                          # T
    ("Perf % Tüm Zamanlar", "Perf.All", None),                                 # U
    ("Volatilite 1H", "Volatility.W", None),                                   # V
    ("Volatilite 1A", "Volatility.M", None),                                   # W
    ("Teknik derecelendirme", "Recommend.All", derece),                        # X
    ("HO derecelendirmesi", "Recommend.MA", derece),                           # Y
    ("Osilatör derecelendirmesi", "Recommend.Other", derece),                  # Z
    ("RSI, 14", "RSI", None),                                                  # AA
    ("Mom, 10", "Mom", None),                                                  # AB
    ("CCI, 20", "CCI20", None),                                                # AC
    ("MACD Level", "MACD.macd", None),                                         # AD
    ("MACD Signal", "MACD.signal", None),                                      # AE
    ("Pys değ perf % 1Y", "Perf.1Y.MarketCap", None),                          # AF (tahmin)
    ("FKY", "price_earnings_growth_ttm", None),                                # AG
    ("FSO", "price_sales_current", None),                                      # AH
    ("P/B", "price_book_fq", None),                                            # AI
    ("P/CF", "price_to_cash_f_operating_activities_ttm", None),                # AJ
    ("P/FCF", "price_free_cash_flow_ttm", None),                               # AK
    ("Fiyat/nakit", "price_sales_current", None),                              # AL
    ("İD", "enterprise_value_current", None),                                  # AM
    ("FD/gelir TTM", "enterprise_value_to_revenue_ttm", None),                 # AN
    ("FD/FVÖK TTM", None, ev_ebit),                                            # AO (hesap)
    ("İD/FAVÖK TTM", "enterprise_value_ebitda_ttm", None),                     # AP
    ("Brüt marj TTM", "gross_margin_ttm", None),                               # AQ
    ("Faaliyet marjı % TTM", "operating_margin_ttm", None),                    # AR
    ("Vergi Öncesi Marj TTM", "pre_tax_margin_ttm", None),                     # AS
    ("Net Marj % TTM", "net_margin_ttm", None),                                # AT
    ("FCF marjı TTM", "free_cash_flow_margin_ttm", None),                      # AU
    ("MVG TTM", "return_on_assets", None),                                     # AV
    ("ÖGO TTM", "return_on_equity", None),                                     # AW
    ("YSG TTM", "return_on_invested_capital", None),                           # AX
    ("Mali dönem Mevcut", "fiscal_period_end_current", donem),                 # AY
    ("Mali dönem sonu Mevcut", "fiscal_period_end_current", tarih),            # AZ
    ("Gelir TTM", "total_revenue_ttm", None),                                  # BA
    ("Gelir artışı TTM YY", "total_revenue_yoy_growth_ttm", None),             # BB
    ("Brüt Kar TTM", "gross_profit_ttm", None),                                # BC
    ("Faaliyet geliri TTM", "oper_income_ttm", None),                          # BD
    ("Net gelir TTM", "net_income_ttm", None),                                 # BE
    ("FAVÖK", "ebitda_ttm", None),                                             # BF
    ("Toplam Aktifler FQ", "total_assets_fq", None),                           # BG
    ("Cari Varlıklar FQ", "total_current_assets_fq", None),                    # BH
    ("Eldeki nakit FQ", "cash_n_short_term_invest_fq", None),                  # BI
    ("Toplam Mesuliyetler FQ", "total_liabilities_fq", None),                  # BJ
    ("Toplam Borç FQ", "total_debt_fq", None),                                 # BK
    ("Net borç FQ", "net_debt_fq", None),                                      # BL
    ("Toplam Sermaye FQ", "total_equity_fq", None),                            # BM
    ("Cari oran FQ", "current_ratio_fq", None),                                # BN
    ("Hızlı oran FQ", "quick_ratio_fq", None),                                 # BO
    ("Borç/özkaynak FQ", "debt_to_equity_fq", None),                           # BP
    ("Nakit/borç FQ", None, nakit_borc),                                       # BQ (hesap)
    ("İşletme CF TTM", "cash_f_operating_activities_ttm", None),               # BR
    ("Yatırım CF TTM", "cash_f_investing_activities_ttm", None),               # BS
    ("Finansman CF TTM", "cash_f_financing_activities_ttm", None),             # BT
    ("FCF TTM", "free_cash_flow_ttm", None),                                   # BU
    ("Sermaye Harcamaları TTM", "capital_expenditures_ttm", None),             # BV
]


def harf(i):                          # 0 -> A, 26 -> AA
    s, i = "", i + 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def sheets_baglan():
    anahtar = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")   # GitHub Secret
    if anahtar:
        return gspread.service_account_from_dict(json.loads(anahtar))
    return gspread.service_account(filename="anahtar.json")    # yerel çalıştırma


def veri_cek(alanlar):
    govde = {"columns": alanlar, "range": [0, 1000],
             "sort": {"sortBy": "name", "sortOrder": "asc"}}
    r = requests.post(TARAYICI_URL, json=govde, headers=UA, timeout=60)
    r.raise_for_status()
    return r.json()["data"]


def satir_olustur(d, alanlar):
    v = dict(zip(alanlar, d))
    satir = []
    for _, alan, donusum in SUTUNLAR:
        deger = v.get(alan) if alan else None
        if donusum:
            deger = donusum(deger, v)
        satir.append("" if deger is None else deger)
    return satir


def main():
    alanlar = []
    for _, alan, _ in SUTUNLAR:
        if alan and alan not in alanlar:
            alanlar.append(alan)

    veri = veri_cek(alanlar)
    satirlar = [satir_olustur(k["d"], alanlar) for k in veri]
    if not satirlar:
        raise SystemExit("Veri gelmedi, sayfaya dokunulmadı.")

    # Tamamen boş gelen sütunları bildir (yanlış alan adı tespiti için)
    bos = [f"{harf(i)} ({SUTUNLAR[i][0]})" for i in range(len(SUTUNLAR))
           if all(s[i] == "" for s in satirlar)]
    if bos:
        print("UYARI - tamamen boş gelen sütunlar:", ", ".join(bos))

    n = len(SUTUNLAR)
    sayfa = sheets_baglan().open(E_TABLO).worksheet(SEKME)
    if sayfa.row_count < ILK_SATIR + len(satirlar):
        sayfa.add_rows(ILK_SATIR + len(satirlar) - sayfa.row_count)
    if sayfa.col_count < n:
        sayfa.add_cols(n - sayfa.col_count)

    sayfa.batch_clear([f"A{ILK_SATIR}:{harf(n - 1)}{sayfa.row_count}"])
    sayfa.update(values=satirlar, range_name=f"A{ILK_SATIR}")
    print(f"{len(satirlar)} satır, {n} sütun yazıldı.")


if __name__ == "__main__":
    main()
