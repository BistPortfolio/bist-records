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
    
    # 1. Başlıklar (Google Sheets'in 1. satırına yazılacak anlaşılır isimler)
    headers = [
        "Sembol", "Şirket Adı", "Sektör", "Kapanış", "Değişim %", "Fiyat Değişimi", "Hacim", "İşlem Hacmi (TL)", 
        "Rel Hacim (10D)", "Piyasa Değeri", "F/K (TTM)", "Hisse Başına Kazanç", 
        "PD/Satış", "PD/DD", "Fiyat/FAK (TTM)", "FD/FAVÖK (TTM)", 
        "FD/Satışlar (TTM)", "Temettü Verimi %", "Hisse Başına Temettü", 
        "Haftalık Perf %", "Aylık Perf %", "3 Aylık Perf %", "6 Aylık Perf %", "YTD Perf %", "1 Yıllık Perf %", "5 Yıllık Perf %", 
        "Haftalık Volatilite", "Aylık Volatilite", "Al/Sat Tavsiyesi", "RSI (14)", "Momentum", "CCI", 
        "Stoch K", "Stoch D", "MACD", "MACD Sinyal", "Awesome Osc", "ADX", "Aroon Up", "Aroon Down", 
        "Bollinger Üst", "Bollinger Alt", "Toplam Gelir", "Brüt Kar", "Faaliyet Karı", "FAVÖK (EBITDA)", 
        "Net Kar", "Toplam Varlıklar", "Dönen Varlıklar", "Nakit ve Nakit Benzerleri", 
        "Toplam Yükümlülükler", "Toplam Borç", "Net Borç", "Özkaynaklar", 
        "Brüt Kar Marjı %", "Faaliyet Kar Marjı %", "Net Kar Marjı %", "FAK Marjı %", 
        "Özkaynak Karlılığı (ROE) %", "Aktif Karlılığı (ROA) %", "Yatırılan Sermaye Karlılığı (ROIC) %", 
        "Cari Oran", "Likit Oran (Asit-Test)", "Borç / Özkaynak", "Nakit / Borç", "Net Borç / FAVÖK", 
        "Serbest Nakit Akışı (FCF)", "Sermaye Harcamaları (Capex)", "Çalışan Sayısı", 
        "Gelecek Çeyrek HBK Tahmini", "Gelecek Çeyrek Gelir Tahmini", 
        "Yıllık HBK", "Yıllık Toplam Gelir", "Hesaplanan Piyasa Değeri"
    ]

    # 2. TradingView API Karşılıkları
    columns_api = [
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
        "columns": columns_api,
        "range": [0, 1000]
    }
    
    response = requests.post(url, json=payload, timeout=15)
    data = response.json().get("data", [])
    
    # 1. Satıra Türkçe Başlıkları koyuyoruz
    all_rows = [headers]
    
    # 2. Satırdan itibaren şirket verilerini diziyoruz
    for item in data:
        raw_values = item.get("d", [])
        clean_row = [val if val is not None else "" for val in raw_values]
        all_rows.append(clean_row)
        
    if all_rows:
        # Sayfayı sıfırlayıp A1'den itibaren (Başlıklar + Veriler) yazdırıyoruz
        worksheet.clear()
        worksheet.update('A1', all_rows)
        print(f"Sıfır sayfaya başarıyla yazıldı: 1 satır başlık + {len(all_rows)-1} şirket verisi.")

if __name__ == "__main__":
    gt_doc = connect_to_sheets()
    update_spot_data(gt_doc)
