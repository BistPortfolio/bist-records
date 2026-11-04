import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    sa_key_json = os.environ.get("GCP_SA_KEY")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")

    if not sa_key_json or not spreadsheet_id:
        raise ValueError("GCP_SA_KEY veya SPREADSHEET_ID ortam değişkenleri eksik!")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds_dict = json.loads(sa_key_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(spreadsheet_id)
    print(f"Tabloya başarıyla bağlanıldı: {spreadsheet.title}")

    sheet = spreadsheet.worksheet("GenelBilgiler")
    ornek_veri = ["AEFES", "100.50", "2026-11-04"]
    sheet.append_row(ornek_veri)
    print("Veri başarıyla 2. satırdan itibaren işlendi Hacı!")

if __name__ == "__main__":
    main()
