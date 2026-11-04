import os
import json
import traceback
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    try:
        print("1. Ortam degiskenleri aliniyor...")
        sa_key_json = os.environ.get("GCP_SA_KEY")
        spreadsheet_id = os.environ.get("SPREADSHEET_ID")

        if not sa_key_json or not spreadsheet_id:
            raise ValueError("GCP_SA_KEY veya SPREADSHEET_ID ortam degiskenleri eksik!")

        print("2. Google kimlik bilgileri işleniyor...")
        creds_dict = json.loads(sa_key_json)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        print("3. E-tabloya baglaniyor...")
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        print("4. Mevcut sekmeler kontrol ediliyor...")
        existing_worksheets = [ws.title for ws in spreadsheet.worksheets()]
        print(f"Tablodaki sekmeler: {existing_worksheets}")

        sheet_name = "GenelBilgiler"
        if sheet_name in existing_worksheets:
            sheet = spreadsheet.worksheet(sheet_name)
            print(f"'{sheet_name}' sekmesi bulundu.")
        else:
            print(f"'{sheet_name}' sekmesi bulunamadi, olusturuluyor...")
            sheet = spreadsheet.add_worksheet(title=sheet_name, rows="100", cols="10")
            print(f"'{sheet_name}' sekmesi olusturuldu.")

        print("5. Veri yaziliyor...")
        ornek_veri = ["AEFES", "100.50", "2026-11-04"]
        sheet.append_row(ornek_veri)
        print("İslem basariyla tamamlandi.")

    except Exception as e:
        print("\nKRITIK HATA TESPIT EDILDI:")
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    main()
