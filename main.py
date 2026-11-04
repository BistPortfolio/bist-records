import os
import json
import traceback
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    try:
        print("1. Ortam değişkenleri alınıyor...")
        sa_key_json = os.environ.get("GCP_SA_KEY")
        spreadsheet_id = os.environ.get("SPREADSHEET_ID")

        print("2. Google kimlik bilgileri işleniyor...")
        creds_dict = json.loads(sa_key_json)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        print(f"3. E-tabloya bağlanılıyor...")
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        print("4. Mevcut sekmeler kontrol ediliyor...")
        existing_worksheets = [ws.title for ws in spreadsheet.worksheets()]
        print(f"Tablodaki sekmeler: {existing_worksheets}")

        # Sekme var mı yok mu kontrol edelim, yoksa oluşturalım ki hata vermesin
        sheet_name = "GenelBilgiler"
        if sheet_name in existing_worksheets:
            sheet = spreadsheet.worksheet(sheet_name)
            print(f"'{sheet_name}' sekmesi bulundu, bağlanıldı.")
        else:
            print(f"'{sheet_name}' sekmesi bulunamadı, otomatik oluşturuluyor...")
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="10")
            print(f"'{sheet_name}' sekmesi başarıyla oluşturuldu.")

print("5. Veri yazılıyor...")
        ornek_veri = ["AEFES", "100.50", "2026-11-04"]
        sheet.append_row(ornek_veri)
        print("İşlem tamamdır Hacı, veri başarıyla 2. satırdan itibaren işlendi!")

    except Exception as e:
        print("\n❌ KRİTİK HATA YAKALANDI:")
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    main()

if __name__ == "__main__":
main()
