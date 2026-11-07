import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

def debug_scan():
    url = "https://scanner.tradingview.com/turkey/scan"
    
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
        "range": [0, 1]  # Sadece ilk şirketi test için çeker
    }
    
    response = requests.post(url, json=payload, timeout=15)
    data = response.json().get("data", [])
    
    if data:
        item = data[0]
        raw_values = item.get("d", [])
        print(f"İstenen sütun sayısı: {len(columns_74)}")
        print(f"API'den dönen ham veri eleman sayısı: {len(raw_values)}")
        print(f"Şirket adı: {item.get('s')}")
        
        # Hangilerinin None veya boş döndüğünü görelim
        for i, (col, val) in enumerate(zip(columns_74, raw_values)):
            if val is None:
                print(f"[{i}] {col} -> Boş (None döndü)")
    else:
        print("API'den veri dönmedi.")

if __name__ == "__main__":
    debug_scan()
