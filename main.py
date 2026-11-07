import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

def connect_to_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.environ.get("GCP_SA_KEY"))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(os.environ.get("SPREADSHEET_ID"))

# Hazırladığın görseldeki tablo düzenine ve sütun sırasına %100 sadık kalan harita (A - BV)
SPOT_MAPPING = [
    # GENEL BAKIŞ (A - L)
    ("Sembol", "name"),
    ("Şirket İsmi", "description"),
    ("Sektör", "sector"),
    ("Fiyat", "close"),
    ("Değ %", "change"),
    ("Hacim", "volume"),
    ("Göreceli Hacim", "relative_volume_10d_calc"),
    ("Pys Değ", "market_cap_basic"),
    ("FKO", "price_earnings_ttm"),
    ("EPS Seyreltilmiş", "earnings_per_share_diluted_ttm"),
    ("EPS Seyreltilmiş Büyüme", "earnings_per_share_diluted_yoy_growth_ttm"),
    ("Tmt Getirisi %", "dividends_yield_current"),

    # PERFORMANS (M - W)
    ("Perf % 1H", "Perf.W"),
    ("Perf % 1A", "Perf.1M"),
    ("Perf % 3A", "Perf.3M"),
    ("Perf % 6A", "Perf.6M"),
    ("Perf % YP", "Perf.YTD"),
    ("Son 1 Yıl %", "Perf.Y"),
    ("Son 5 Yıl %", "Perf.5Y"),
    ("Son 10 Yıl %", "Perf.10Y"),
    ("Tüm Zamanlar", "Perf.All"),
    ("Volatilite 1H", "volatility_week"),
    ("Volatilite 1A", "volatility_month"),

    # TEKNİKLER (X - AE)
    ("Teknik Derecelendirme", "recommendation_mark"),
    ("HO Derecelendirmesi", "recommendation_ma_mark"),
    ("Osilatör Derecelendirmesi", "recommendation_osc_mark"),
    ("RSI, 14", "RSI"),
    ("MOM,10", "Mom"),
    ("CCI, 20", "CCI"),
    ("MACD 12, 26 Level", "MACD.macd"),
    ("MACD 12, 26 Signal", "MACD.signal"),

    # DEĞERLEME (AF - AP)
    ("Pys Değ Perf % 1Y", "market_cap_change_1y"),
    ("FKY", "price_earnings_forecast_next_fy"),
    ("FSO", "price_sales"),
    ("P/B", "price_book"),
    ("P/CF", "price_cash_flow_recent"),
    ("P/FCF", "price_free_cash_flow_ttm"),
    ("Fiyat/nakit", "price_to_cash_f_fy"),
    ("ID", "enterprise_value"),
    ("FD/Gelir", "enterprise_value_to_revenue_ttm"),
    ("FD/Fvök", "enterprise_value_ebitda_ttm"),
    ("İD/FAVÖK", "enterprise_value_ebitda_ttm"),

    # KARLILIK (AQ - AX)
    ("Brüt marj", "gross_margin"),
    ("Faaliyet Marjı %", "operating_margin"),
    ("Vergi Öncesi Marj", "pre_tax_margin"),
    ("Net Marj %", "net_profit_margin"),
    ("FCF Marjı %", "fcf_margin"),
    ("MVG", "return_on_equity"),
    ("ÖGO", "return_on_assets"),
    ("YSG", "return_on_invested_capital"),

    # GELİR TABLOSU (AY - BF)
    ("Mali dönem", "fiscal_period"),
    ("Mali dönem sonu", "fiscal_year"),
    ("Gelir", "total_revenue"),
    ("Gelir artışı", "total_revenue_yoy_growth_ttm"),
    ("Brüt Kar", "gross_profit"),
    ("Faaliyet Geliri", "operating_income"),
    ("Net Gelir", "net_income"),
    ("FAVÖK", "ebitda"),

    # BİLANÇO (BG - BQ)
    ("Toplam Aktifler", "total_assets"),
    ("Cari Varlıklar", "current_assets"),
    ("Eldeki nakit", "cash_and_short_term_investments"),
    ("Toplam Mesuliyetler", "total_liabilities"),
    ("Toplam Borç", "total_debt"),
    ("Net borç", "net_debt"),
    ("Toplam Sermaye", "total_shareholder_equity"),
    ("Cari oran", "current_ratio"),
    ("Hızlı oran", "quick_ratio"),
    ("Borç/özkaynak", "debt_to_equity"),
    ("Nakit/borç", "cash_to_debt"),

    # NAKİT AKIŞI (BR - BV)
    ("İşletme CF", "cash_flow_from_operating_activities"),
    ("Yatırım CF", "cash_flow_from_investing_activities"),
    ("Finansman CF", "cash_flow_from_financing_activities"),
    ("FCF", "free_cash_flow"),
    ("Sermaye Harcamaları", "capital_expenditures")
]

def update_spot_data(sheet):
    worksheet = sheet.worksheet("SpotVerileri")
    
    headers = [item[0] for item in SPOT_MAPPING]
    api_columns = [item[1] for item in SPOT_MAPPING]
    
    url = "https://scanner.tradingview.com/turkey/scan"
    payload = {
        "filter": [{"left": "exchange", "operation": "equal", "right": "BIST"}],
        "options": {"lang": "tr"},
        "symbols": {"query": {"types": []}},
        "columns": api_columns,
        "range": [0, 1000]
    }
    
    response = requests.post(url, json=payload, timeout=15)
    data = response.json().get("data", [])
    
    rows_to_write = []
    for item in data:
        raw_values = item.get("d", [])
        clean_row = [val if val is not None else "" for val in raw_values]
        rows_to_write.append(clean_row)
        
    if rows_to_write:
        worksheet.clear()
        worksheet.update('A1', [headers])
        worksheet.update('A2', rows_to_write)
        print(f"SpotVerileri başarıyla güncellendi: {len(rows_to_write)} şirket, {len(headers)} sütun.")

if __name__ == "__main__":
    gt_doc = connect_to_sheets()
    update_spot_data(gt_doc)
