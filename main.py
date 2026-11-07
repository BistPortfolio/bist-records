import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import requests

# 1. Google Sheets Kimlik Doğrulama ve Bağlantı
def connect_to_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    sa_key_json = os.environ.get("GCP_SA_KEY")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    
    if not sa_key_json or not spreadsheet_id:
        raise ValueError("GCP_SA_KEY veya SPREADSHEET_ID ortam değişkenleri eksik!")
        
    creds_dict = json.loads(sa_key_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(spreadsheet_id)
    return sheet

# 2. Spot Verilerini Çekme ve SpotVerileri Sekmesine Yazma
def update_spot_data(sheet):
    print("Spot verileri işleniyor...")
    worksheet = sheet.worksheet("SpotVerileri")
    
    url = "https://scanner.tradingview.com/turkey/scan"
    
    # A'dan BV'ye kadar (74 Sütun) Tam ve Eksiksiz TradingView API Haritası
    payload = {
        "filter": [{"left": "exchange", "operation": "equal", "right": "BIST"}],
        "options": {"lang": "tr"},
        "symbols": {"query": {"types": []}},
        "columns": [
            # Temel Bilgiler / Genel Bakış (A - K)
            "name", "description", "sector", "close", "change", "volume", "relative_volume_10d_calc",
            "price_earnings_ttm", "earnings_per_share_diluted_ttm", "earnings_per_share_diluted_growth_ttm", "dividends_yield_current",
            # Performans ve Volatilite (L - W / Q sütunu dahil)
            "perf_1w", "perf_1m", "perf_3m", "perf_6m", "perf_ytd", "perf_1y", "perf_5y", "perf_10y", "perf_all",
            "volatility_1w", "volatility_1m",
            # Teknik Göstergeler (X - AD)
            "recommendation_mark", "rec_m_ma", "rec_m_rsi", "RSI", "Mom", "CCI", "MACD.macd", "MACD.signal",
            # Değerleme ve Karlılık (AE - AX / AF, AG, AO, AP, AX dahil)
            "price_sales", "price_book", "enterprise_value", "enterprise_value_ebitda_ttm", "fcf_margin", 
            "net_income", "gross_margin", "operating_margin", "pre_tax_margin", "net_profit_margin",
            "return_on_equity", "return_on_assets", "return_on_invested_capital", "research_and_development_ratio",
            # Gelir Tablosu, Bilanço ve Nakit Akışı Detay Kalemleri (AY - BV)
            "total_revenue", "total_revenue_growth", "gross_profit", "operating_income", "ebitda",
            "net_income_growth", "earnings_per_share_growth", "total_assets", "current_assets", 
            "cash_and_short_term_investments", "total_liabilities", "total_debt", "net_debt", 
            "total_shareholder_equity", "current_ratio", "quick_ratio", "debt_to_equity", "cash_to_debt",
            "free_cash_flow", "capital_expenditures", "dividend_payout_ratio_ttm", "book_value_per_share",
            "cash_per_share", "operational_cash_flow", "free_cash_flow_per_share", "goodwill",
            "total_debt_to_total_asset", "long_term_debt_to_equity", "short_term_debt", "long_term_debt"
        ],
        "range": [0, 1000]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        result = response.json()
        data = result.get("data", [])
        
        rows_to_write = []
        for item in data:
            row_data = item.get("d", [])
            rows_to_write.append(row_data)
            
        if rows_to_write:
            worksheet.update('A3', rows_to_write)
            print(f"SpotVerileri başarıyla güncellendi. Toplam {len(rows_to_write)} şirket yazıldı.")
        else:
            print("TradingView'den veri alınamadı.")
            
    except Exception as e:
        print(f"Spot verileri çekilirken hata oluştu: {e}")

# 3. Viop Verilerini Çekme ve ViopVerileri Sekmesine Yazma
def update_viop_data(sheet):
    print("Viop verileri işleniyor...")
    worksheet = sheet.worksheet("ViopVerileri")
    print("ViopVerileri hazırlık aşamasında.")

if __name__ == "__main__":
    print("Borsaİstanbul Portföy Botu Başlatıldı...")
    gt_doc = connect_to_sheets()
    update_spot_data(gt_doc)
    update_viop_data(gt_doc)
    print("Tüm işlemler başarıyla tamamlandı.")
