import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def main():
    # 1. Parçalı Secrets değişkenlerini alıyoruz
    client_email = os.environ.get("GCP_CLIENT_EMAIL")
    project_id = os.environ.get("GCP_PROJECT_ID")
    private_key = os.environ.get("GCP_PRIVATE_KEY")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")

    if not all([client_email, project_id, private_key, spreadsheet_id]):
        raise ValueError("Gerekli ortam değişkenlerinden biri veya birkaçı eksik!")

    # GitHub Secrets escape karakterlerini (\\n) gerçek alt satıra (\n) dönüştürüyoruz
    formatted_private_key = private_key.replace('\\n', '\n')

    # 2. Servis hesabı sözlüğünü dinamik oluşturuyoruz
    creds_dict = {
        "type": "service_account",
        "project_id": project_id,
        "private_key": formatted_private_key,
        "client_email": client_email,
        "token_uri": "https://oauth2.googleapis.com/token"
    }

    # 3. Google Sheets API yetkilendirmesi
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # 4. Tabloya bağlanma ve 2. satırdan itibaren veri yazma
    spreadsheet = client.open_by_key(spreadsheet_id)
    print(f"Başarıyla bağlanıldı: {spreadsheet.title}")

    try:
        sheet = spreadsheet.worksheet("GenelBilgiler")
        
        # Mermere kazıdığımız kural: 2. satırdan itibaren yazdırma
        ornek_veri = ["AEFES", "100.50", "2026-11-04"]
        sheet.append_row(ornek_veri)
        print("Veri başarıyla 2. satırdan itibaren işlendi Hacı!")

    except Exception as e:
        print(f"Sekme yazma sırasında hata oluştu: {e}")

if __name__ == "__main__":
    main()
