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
    
    # A'dan BV'ye kadar 74 sütunluk tam eşleme (Boş/Özel sütunlar için yer tutucularla)
    payload = {
        "filter": [{"left": "exchange", "operation": "equal", "right": "BIST"}],
        "options": {"lang": "tr"},
        "symbols": {"query": {"types": []}},
        "columns": [
            "name", "description", "sector", "close", "change", "volume", "relative_volume_10d_calc",
            "price_earnings_ttm", "earnings_per_share_diluted_ttm", "earnings_per_share_diluted_growth_ttm", "dividends_yield_current",
            "perf_1w", "perf_1m", "perf_3m", "perf_6m", "perf_ytd", "perf_1y", "perf_5y", "perf_10y", "perf_all",
            "volatility_1w", "volatility_1m",
            "recommendation_mark", "rec_m_ma", "rec_m_rsi", "RSI", "Mom", "CCI", "MACD.macd", "MACD.signal",
            "price_sales", "enterprise_value_ebitda_ttm", "price_book", "price_free_cash_flow_ttm", 
            "fcf_margin", "net_income", "gross_margin", "operating_margin", "pre_tax_margin", "net_profit_margin",
            "return_on_equity", "return_on_assets", "return_on_invested_capital", "research_and_development_ratio",
            "total_revenue", "total_revenue_growth_fq", "gross_profit", "operating_income", "ebitda",
            "net_income_growth_fq", "earnings_per_share_growth_fq", "total_assets", "current_assets", 
            "cash_and_short_term_investments", "total_liabilities", "total_debt", "net_debt", 
            "total_shareholder_equity", "current_ratio", "quick_ratio", "debt_to_equity", "cash_to_debt",
            "free_cash_flow", "capital_expenditures", "dividend_payout_ratio_ttm", "book_value_per_share_fq",
            "cash_per_share_fq", "operational_cash_flow", "free_cash_flow_per_share", "goodwill",
            "total_debt_to_total_asset", "long_term_debt_to_equity", "short_term_debt", "long_term_debt"
        ],
        "range": [0, 1000]
    }
    
    response = requests.post(url, json=payload, timeout=15)
    data = response.json().get("data", [])
    
    rows_to_write = []
    for item in data:
        rows_to_write.append(item.get("d", []))
        
    if rows_to_write:
        # Komple temizleme yok, sadece A3'ten itibaren güncel veriyi basıyoruz
        worksheet.update('A3', rows_to_write)
        print(f"Güncellendi: {len(rows_to_write)} şirket.")

if __name__ == "__main__":
    gt_doc = connect_to_sheets()
    update_spot_data(gt_doc)
