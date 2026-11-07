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
    
    # TradingView Scanner API üzerinden BIST verilerini çekme isteği
    url = "https://scanner.tradingview.com/turkey/scan"
    
    # İstediğimiz sütunların listesi (Senin hazırladığın A'dan BV'ye olan haritaya denk gelen TradingView alanları)
    columns_to_fetch = [
        "name", "description", "sector", "close", "change", "volume", "relative_volume_10d_calc",
        "price_earnings_ttm", "earnings_per_share_diluted_ttm", "earnings_per_share_diluted_growth_ttm",
        # İhtiyaca göre diğer TradingView alanları buraya eklenecek
    ]
    
    payload = {
        "filter": [{"left": "exchange", "operation": "equal", "right": "BIST"}],
        "options": {"lang": "tr"},
        "symbols": {"query": {"types": []}},
        "columns": [
            "name", "description", "sector", "close", "change", "volume", "relative_volume_10d_calc",
            "P_S", "price_earnings_ttm", "earnings_per_share_diluted_ttm", "earnings_per_share_diluted_growth_ttm",
            "dividends_yield_current", "perf_1w", "perf_1m", "perf_3m", "perf_6m", "perf_ytd", "perf_1y",
            "perf_5y", "perf_10y", "perf_all", "volatility_1w", "volatility_1m", "recommendation_mark",
            "rec_m_ma", "rec_m_rsi", "RSI", "Mom", "CCI", "MACD.macd", "MACD.signal", "P_S_1y", "fcf_margin",
            "net_income", "gross_margin", "operating_margin", "pre_tax_margin", "net_profit_margin",
            "total_assets", "current_assets", "cash_and_short_term_investments", "total_liabilities",
            "total_debt", "net_debt", "total_shareholder_equity", "current_ratio", "quick_ratio",
            "debt_to_equity", "cash_to_debt"
        ],
        "range": [0, 1000] # Tüm BIST hisselerini kapsayacak aralık
    }
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        data = result.get("data", [])
        
        rows_to_write = []
        for item in data:
            row_data = item.get("d", [])
            rows_to_write.append(row_data)
            
        if rows_to_write:
            # SpotVerileri 3. satırdan (A sütunundan) başla
            worksheet.update(rows_to_write, 'A3')
            print(f"SpotVerileri başarıyla güncellendi. Toplam {len(rows_to_write)} şirket yazıldı.")
        else:
            print("TradingView'den veri alınamadı.")
            
    except Exception as e:
        print(f"Spot verileri çekilirken hata oluştu: {e}")

# 3. Viop Verilerini Çekme ve ViopVerileri Sekmesine Yazma
def update_viop_data(sheet):
    print("Viop verileri işleniyor...")
    worksheet = sheet.worksheet("ViopVerileri")
    
    categories = ["Aktif Sözleşmeler", "Hisse", "Döviz", "Endeks", "Emtia"]
    
    all_viop_rows = []
    
    for cat in categories:
        print(f"VİOP Kategorisi işleniyor: {cat}")
        
        # Örnek simülasyon/veri toplama yapısı (Gerçek VİOP veri kaynağı entegrasyonu buraya gelecek)
        # Her satır için A sütununa kategori adı, B sütunundan itibaren ise sözleşme verileri yazılacak
        # Örnek: ["Aktif Sözleşmeler", "F_AEFES1126", 150.5, 1.2, ...]
        
        # Şimdilik test/yapı iskeleti olarak bırakıyoruz, veri kaynağını bağlayacağız.
        pass

    print("ViopVerileri hazırlık aşamasında.")

if __name__ == "__main__":
    print("Borsaİstanbul Portföy Botu Başlatıldı...")
    gt_doc = connect_to_sheets()
    update_spot_data(gt_doc)
    update_viop_data(gt_doc)
    print("Tüm işlemler başarıyla tamamlandı!")
