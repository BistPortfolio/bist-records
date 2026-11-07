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

def update_spot_data(sheet):
    worksheet = sheet.worksheet("SpotVerileri")
    url = "https://scanner.tradingview.com/turkey/scan"
    
    # İstediğimiz ham metrikler listesi
    columns_to_fetch = [
        "name", "description", "sector", "close", "change", "volume", "relative_volume_10d_calc",
        "price_earnings_ttm", "earnings_per_share_diluted_ttm", "dividends_yield_current",
        "perf_1w", "perf_1m", "perf_3m", "perf_6m", "perf_ytd", "perf_1y", "perf_5y",
        "recommendation_mark", "RSI", "Mom", "CCI", "MACD.macd", "MACD.signal",
        "price_sales", "price_book", "fcf_margin", "net_income", "gross_margin", 
        "operating_margin", "net_profit_margin", "return_on_equity", "return_on_assets",
        "total_revenue", "gross_profit", "operating_income", "ebitda", 
        "total_assets", "current_assets", "cash_and_short_term_investments", 
        "total_liabilities", "total_debt", "net_debt", "total_shareholder_equity", 
        "current_ratio", "quick_ratio", "debt_to_equity", "cash_to_debt",
        "free_cash_flow", "capital_expenditures"
    ]
    
    payload = {
        "filter": [{"left": "exchange", "operation": "equal", "right": "BIST"}],
        "options": {"lang": "tr"},
        "symbols": {"query": {"types": []}},
        "columns": columns_to_fetch,
        "range": [0, 1000]
    }
    
    response = requests.post(url, json=payload, timeout=15)
    result_data = response.json().get("data", [])
    
    rows_to_write = []
    for item in result_data:
        raw_values = item.get("d", [])
        
        # Tablonun A'dan BV'ye kadar olan 74 sütunluk tam şablonunu oluşturuyoruz.
        # Gelen verileri sırayla yerleştiriyoruz, eksik/boş kalan yerler "" olarak kalıyor.
        mapped_row = [""] * 74
        for i, val in enumerate(raw_values):
            if i < 74:
                mapped_row[i] = val
                
        rows_to_write.append(mapped_row)
        
    if rows_to_write:
        # A3 hücresinden itibaren tam şablona göre yazdırıyoruz
        worksheet.update('A3', rows_to_write)
        print(f"Güncellendi: {len(rows_to_write)} şirket.")

if __name__ == "__main__":
    gt_doc = connect_to_sheets()
    update_spot_data(gt_doc)
