import os
import json
import traceback
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    try:
        print("1. Ortam değişkenleri kontrol ediliyor...")
        sa_key_json = os.environ.get("GCP_SA_KEY")
        spreadsheet_id = os.environ.get("SPREADSHEET_ID")

        if not sa_key_json or not spreadsheet_id:
            raise ValueError("GCP_SA_KEY veya SPREADSHEET_ID ortam değişkenleri eksik!")

        print("2. Google kimlik bilgileri işleniyor...")
        creds_dict = json.loads(sa_key_json)
        
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        print(f"3. E-tabloya bağlanılıyor (ID: {spreadsheet_id})...")
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"Tablo başlığı doğrulandı: {spreadsheet.title}")

        print("4. Tablodaki sekmeler kontrol ediliyor...")
        existing_worksheets = [ws.title for ws in spreadsheet.worksheets()]
        print(f"Tabloda bulunan sekmeler: {existing_worksheets}")

        print("5. 'GenelBilgiler' sekmesine veri yazılmaya çalışılıyor...")
        sheet = spreadsheet.worksheet("GenelBilgiler")
        ornek_veri = ["AEFES", "100.50", "2026-11-04"]
        sheet.append_row(ornek_veri)
        print("İşlem tamamdır Hacı, veri başarıyla işlendi!")

    except Exception as e:
        print("\n❌ SİSTEM HATA YAKALADI:")
        print(str(e))
        print("\nDetaylı Hata İzleme (Traceback):")
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    main()
