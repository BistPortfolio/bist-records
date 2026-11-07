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
    
    # Tüm sütunların Türkçe başlıkları ve TradingView API'sindeki kesin karşılıkları
    mapping = [
        ("Sembol", "name"),
        ("Şirket Adı", "description"),
        ("Sektör", "sector"),
        ("Kapanış", "close"),
        ("Değişim %", "change"),
        ("Fiyat Değişimi", "change_abs"),
        ("Hacim", "volume"),
        ("İşlem Hacmi (TL)", "Value.Traded"),
        ("Rel Hacim (10D)", "relative_volume_10d_calc"),
        ("Piyasa Değeri", "market_cap_basic"),
        ("F/K (TTM)", "price_earnings_ttm"),
        ("Hisse Başına Kazanç", "earnings_per_share_diluted_ttm"),
        ("PD/Satış", "price_sales"),
        ("PD/DD", "price_book"),
        ("Fiyat/Serbest Nakit Akışı", "price_free_cash_flow_ttm"),
        ("FD/FAVÖK", "enterprise_value_ebitda_ttm"),
        ("FD/Satış", "enterprise_value_to_revenue_ttm"),
        ("Temettü Verimi %", "dividends_yield_current"),
        ("Hisse Başına Temettü", "dps_common_stock_prim_issue_fy"),
        
        # Performans Sekmesi (Doğru API Key'leri)
        ("Haftalık Perf %", "Perf.W"),
        ("Aylık Perf %", "Perf.1M"),
        ("3 Aylık Perf %", "Perf.3M"),
        ("6 Aylık Perf %", "Perf.6M"),
        ("YTD Perf %", "Perf.YTD"),
        ("1 Yıllık Perf %", "Perf.Y"),
        ("5 Yıllık Perf %", "Perf.5Y"),
        
        ("Haftalık Volatilite", "volatility_week"),
        ("Aylık Volatilite", "volatility_month"),
        ("Al/Sat Tavsiyesi", "recommendation_mark"),
        ("RSI (14)", "RSI"),
        ("Momentum", "Mom"),
        ("CCI", "CCI"),
        ("Stoch K", "Stoch.K"),
        ("Stoch D", "Stoch.D"),
        ("MACD", "MACD.macd"),
        ("MACD Sinyal", "MACD.signal"),
        ("Awesome Osc", "AO"),
        ("ADX", "ADX"),
        ("Aroon Up", "Aroon.Up"),
        ("Aroon Down", "Aroon.Down"),
        ("Bollinger Üst", "BB.upper"),
        ("Bollinger Alt", "BB.lower"),
        
        # Bilanço ve Gelir Tablosu Kalemleri
        ("Toplam Gelir", "total_revenue"),
        ("Brüt Kar", "gross_profit"),
        ("Faaliyet Karı", "operating_income"),
        ("FAVÖK (EBITDA)", "ebitda"),
        ("Net Kar", "net_income"),
        ("Toplam Varlıklar", "total_assets"),
        ("Dönen Varlıklar", "current_assets"),
        ("Nakit ve Nakit Benzerleri", "cash_and_short_term_investments"),
        ("Toplam Yükümlülükler", "total_liabilities"),
        ("Toplam Borç", "total_debt"),
        ("Net Borç", "net_debt"),
        ("Özkaynaklar", "total_shareholder_equity"),
        
        # Marjlar ve Oranlar
        ("Brüt Kar Marjı %", "gross_margin"),
        ("Faaliyet Kar Marjı %", "operating_margin"),
        ("Net Kar Marjı %", "net_profit_margin"),
        ("FCF Marjı %", "fcf_margin"),
        ("Özkaynak Karlılığı (ROE) %", "return_on_equity"),
        ("Aktif Karlılığı (ROA) %", "return_on_assets"),
        ("Yatırılan Sermaye Karlılığı %", "return_on_invested_capital"),
        ("Cari Oran", "current_ratio"),
        ("Likit Oran", "quick_ratio"),
        ("Borç / Özkaynak", "debt_to_equity"),
        ("Nakit / Borç", "cash_to_debt"),
        ("Net Borç / FAVÖK", "net_debt_to_ebitda"),
        
        # Nakit Akışı ve Diğer
        ("Serbest Nakit Akışı", "free_cash_flow"),
        ("Sermaye Harcamaları", "capital_expenditures"),
        ("Çalışan Sayısı", "number_of_employees"),
        ("Gelecek Çeyrek HBK Tahmini", "earnings_per_share_forecast_next_fq"),
        ("Gelecek Çeyrek Gelir Tahmini", "revenue_forecast_next_fq"),
        ("Yıllık HBK", "Basic_EPS_FY"),
        ("Yıllık Toplam Gelir", "Total_Revenue_FY"),
        ("Hesaplanan Piyasa Değeri", "Market_Cap_Calc")
    ]

    headers = [item[0] for item in mapping]
    columns_api = [item[1] for item in mapping]
    
    payload = {
        "filter": [{"left": "exchange", "operation": "equal", "right": "BIST"}],
        "options": {"lang": "tr"},
        "symbols": {"query": {"types": []}},
        "columns": columns_api,
        "range": [0, 1000]
    }
    
    response = requests.post(url, json=payload, timeout=15)
    data = response.json().get("data", [])
    
    all_rows = [headers]
    for item in data:
        raw_values = item.get("d", [])
        clean_row = [val if val is not None else "" for val in raw_values]
        all_rows.append(clean_row)
        
    if all_rows:
        worksheet.clear()
        worksheet.update('A1', all_rows)
        print(f"Tam liste başarıyla güncellendi: {len(headers)} sütun, {len(data)} şirket.")

if __name__ == "__main__":
    gt_doc = connect_to_sheets()
    update_spot_data(gt_doc)
