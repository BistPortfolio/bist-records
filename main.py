import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    # 1. GitHub Secrets kasasından gelen gizli anahtarı ve ID'yi alıyoruz
    sa_key_json = os.environ.get("GCP_SA_KEY")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")

    if not sa_key_json or not spreadsheet_id:
        raise ValueError("GCP_SA_KEY veya SPREADSHEET_ID ortam değişkenleri eksik!")

    # 2. Google Sheets API kimlik doğrulamasını yapıyoruz
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # JSON string verisini Python sözlüğüne çevirip yetkilendiriyoruz
    creds_dict = json.loads(sa_key_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # 3. Google E-Tablomuzu ID ile açıyoruz
    spreadsheet = client.open_by_key(spreadsheet_id)
    print(f"Başarıyla bağlanıldı: {spreadsheet.title}")

    # Örnek test: 'SpotVerileri' dosyasındaki 'GenelBilgiler' sekmesine veri yazma simülasyonu
    # (İleride buraya TradingView veya dış kaynaklardan çektiğimiz veriler gelecek)
    try:
        sheet = spreadsheet.worksheet("GenelBilgiler")
        
        # Mermere kazıdığımız kural: 2. satırdan itibaren yazdırma
        # Örnek veri satırı: [Hisse, Fiyat, Tarih]
        ornek_veri = ["AEFES", "100.50", "2026-11-04"]
        
        # 2. satıra veriyi iliştiriyoruz (append_row otomatik olarak boş olan ilk satıra, yani başlıkların altına yazar)
        sheet.append_row(ornek_veri)
        print("Veri başarıyla 2. satırdan itibaren işlendi Hacı!")

    except Exception as e:
        print(f"Sekme yazma sırasında hata oluştu: {e}")

if __name__ == "__main__":
    main()
