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

# Google Sheets başlıklarını TradingView API alan adlarıyla eşleyen sözlük
HEADER_MAP = {
    "Sembol": "name",
    "Şirket Adı": "description",
    "Sektör": "sector",
    "Kapanış": "close",
    "Değişim %": "change",
    "Fiyat Değişimi": "change_abs",
    "Hacim": "volume",
    "İşlem Hacmi (TL)": "Value.Traded",
    "Rel Hacim (10D)": "relative_volume_10d_calc",
    "Piyasa Değeri": "market_cap_basic",
    "F/K (TTM)": "price_earnings_ttm",
    "Hisse Başına Kazanç": "earnings_per_share_diluted_ttm",
    "PD/Satış": "price_sales",
    "PD/DD": "price_book",
    "Fiyat/Serbest Nakit Akışı": "price_free_cash_flow_ttm",
    "FD/FAVÖK": "enterprise_value_ebitda_ttm",
    "FD/Satış": "enterprise_value_to_revenue_ttm",
    "Temettü Verimi %": "dividends_yield_current",
    "Hisse Başına Temettü": "dps_common_stock_prim_issue_fy",
    "Haftalık Perf %": "Perf.W",
    "Aylık Perf %": "Perf.1M",
    "3 Aylık Perf %": "Perf.3M",
    "6 Aylık Perf %": "Perf.6M",
    "YTD Perf %": "Perf.YTD",
    "1 Yıllık Perf %": "Perf.Y",
    "5 Yıllık Perf %": "Perf.5Y",
    "Haftalık Volatilite": "volatility_week",
    "Aylık Volatilite": "volatility_month",
    "Al/Sat Tavsiyesi": "recommendation_mark",
    "RSI (14)": "RSI",
    "Momentum": "Mom",
    "CCI": "CCI",
    "Stoch K": "Stoch.K",
    "Stoch D": "Stoch.D",
    "MACD": "MACD.macd",
    "MACD Sinyal": "MACD.signal",
    "Awesome Osc": "AO",
    "ADX": "ADX",
    "Aroon Up": "Aroon.Up",
    "Aroon Down": "Aroon.Down",
    "Bollinger Üst": "BB.upper",
    "Bollinger Alt": "BB.lower",
    "Toplam Gelir": "total_revenue",
    "Brüt Kar": "gross_profit",
    "Faaliyet Karı": "operating_income",
    "FAVÖK (EBITDA)": "ebitda",
    "Net Kar": "net_income",
    "Toplam Varlıklar": "total_assets",
    "Dönen Varlıklar": "current_assets",
    "Nakit ve Nakit Benzerleri": "cash_and_short_term_investments",
    "Toplam Yükümlülükler": "total_liabilities",
    "Toplam Borç": "total_debt",
    "Net Borç": "net_debt",
    "Özkaynaklar": "total_shareholder_equity",
    "Brüt Kar Marjı %": "gross_margin",
    "Faaliyet Kar Marjı %": "operating_margin",
    "Net Kar Marjı %": "net_profit_margin",
    "FCF Marjı %": "fcf_margin",
    "Özkaynak Karlılığı (ROE) %": "return_on_equity",
    "Aktif Karlılığı (ROA) %": "return_on_assets",
    "Yatırılan Sermaye Karlılığı %": "return_on_invested_capital",
    "Cari Oran": "current_ratio",
    "Likit Oran": "quick_ratio",
    "Borç / Özkaynak": "debt_to_equity",
    "Nakit / Borç": "cash_to_debt",
    "Net Borç / FAVÖK": "net_debt_to_ebitda",
    "Serbest Nakit Akışı": "free_cash_flow",
    "Sermaye Harcamaları": "capital_expenditures",
    "Çalışan Sayısı": "number_of_employees",
    "Gelecek Çeyrek HBK Tahmini": "earnings_per_share_forecast_next_fq",
    "Gelecek Çeyrek Gelir Tahmini": "revenue_forecast_next_fq",
    "Yıllık HBK": "Basic_EPS_FY",
    "Yıllık Toplam Gelir": "Total_Revenue_FY",
    "Hesaplanan Piyasa Değeri": "Market_Cap_Calc"
}

def update_spot_data(sheet):
    worksheet = sheet.worksheet("SpotVerileri")
    
    # 1. Satırdaki başlıkları oku
    sheet_headers = worksheet.row_values(1)
    if not sheet_headers:
        print("Hata: Başlıklar boş.")
        return

    # Başlıkları API alan adlarına eşle
    api_columns = []
    for h in sheet_headers:
        cleaned_h = h.strip()
        if cleaned_h in HEADER_MAP:
            api_columns.append(HEADER_MAP[cleaned_h])
        else:
            api_columns.append(cleaned_h)

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
        # Önce sayfayı tamamen temizle
        worksheet.clear()
        
        # Başlıkları tekrar en üste yaz
        worksheet.update('A1', [sheet_headers])
        
        # Verileri Z sınırına takılmadan, doğrudan matris boyutunda A2'den başlatarak bas
        worksheet.update('A2', rows_to_write)
        print(f"Başarılı: {len(rows_to_write)} şirket, {len(api_columns)} sütun eksiksiz yazıldı.")

if __name__ == "__main__":
    gt_doc = connect_to_sheets()
    update_spot_data(gt_doc)
