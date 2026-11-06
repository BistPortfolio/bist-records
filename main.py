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
    
    # GitHub Secrets'tan gelen JSON anahtarını okuyoruz
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
    
    # TODO: TradingView Scanner API veya veri çekme operasyonu buraya eklenecek
    # Örnek test verisi veya dataframe yapısı:
    # SpotVerileri 3. satırdan başliyor (A sütunundan BV sütununa kadar)
    
    print("SpotVerileri başarıyla güncellendi.")

# 3. Viop Verilerini Çekme ve ViopVerileri Sekmesine Yazma
def update_viop_data(sheet):
    print("Viop verileri işleniyor...")
    worksheet = sheet.worksheet("ViopVerileri")
    
    categories = ["Aktif Sözleşmeler", "Hisse", "Döviz", "Endeks", "Emtia"]
    
    # Belirttiğin sıralamayla A sütununa kategori adı, B sütunundan itibaren veriler 2. satırdan yazılacak
    for cat in categories:
        print(f"Kategori işleniyor: {cat}")
        # Web kazıma / veri çekme mantığı buraya entegre edilecek

    print("ViopVerileri başarıyla güncellendi.")

if __name__ == "__main__":
    print("Borsaİstanbul Portöy Botu Başlatıldı...")
    gt_doc = connect_to_sheets()
    update_spot_data(gt_doc)
    update_viop_data(gt_doc)
    print("Tüm işlemler başarıyla tamamlandı Hacı!")
