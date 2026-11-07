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
    
    # Tablonun A'dan BV'ye kadar olan tam 74 sütunluk TradingView API karşılıkları
    columns_74 = [
        "name", "description", "sector", "close", "change", "change_abs", "volume", "Value.Traded", 
        "relative_volume_10d_calc", "market_cap_basic", "price_earnings_ttm", "earnings_per_share_diluted_ttm", 
        "price_sales", "price_book", "price_free_cash_flow_ttm", "enterprise_value_ebitda_ttm", 
        "enterprise_value_to_revenue_ttm", "dividends_yield_current", "dps_common_stock_prim_issue_fy", 
        "perf_1w", "perf_1m", "perf_3m", "perf_6m", "perf_ytd", "perf_1y", "perf_5y", 
        "volatility_week", "volatility_month", "recommendation_mark", "RSI", "Mom", "CCI", 
        "Stoch.K", "Stoch.D", "MACD.macd", "MACD.signal", "AO", "ADX", "Aroon.Up", "Aroon.Down", 
        "BB.upper", "BB.lower", "total_revenue", "gross_profit", "operating_income", "ebitda", 
        "net_income", "total_assets", "current_assets", "cash_and_short_term_investments", 
        "total_liabilities", "total_debt", "net_debt", "total_shareholder_equity", 
        "gross_margin", "operating_margin", "net_profit_margin", "fcf_margin", 
        "return_on_equity", "return_on_assets", "return_on_invested_capital", 
        "current_ratio", "quick_ratio", "debt_to_equity", "cash_to_debt", "net_debt_to_ebitda", 
        "free_cash_flow", "capital_expenditures", "number_of_employees", 
        "earnings_per_share_forecast_next_fq", "revenue_forecast_next_fq", 
        "Basic_EPS_FY", "Total_Revenue_FY", "Market_Cap_Calc"
    ]
    
    payload = {
        "filter": [{"left": "exchange", "operation": "equal", "right": "BIST"}],
        "options": {"lang": "tr"},
        "symbols": {"query": {"types": []}},
        "columns": columns_74,
        "range": [0, 1000]
    }
    
    response = requests.post(url, json=payload, timeout=15)
    data = response.json().get("data", [])
    
    rows_to_write = []
    for item in data:
        rows_to_write.append(item.get("d", []))
        
    if rows_to_write:
        worksheet.update('A3', rows_to_write)
        print(f"Başarıyla güncellendi: {len(rows_to_write)} şirket, 74 sütun.")

if __name__ == "__main__":
    gt_doc = connect_to_sheets()
    update_spot_data(gt_doc)
