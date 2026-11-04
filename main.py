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

        print("3. E-tabloya bağlanılıyor...")
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        print("4. Çalışma sayfası (worksheet) seçiliyor...")
        # İlk sayfayı doğrudan seçerek sekme adı uyuşmazlığı riskini ortadan kaldırıyoruz
        sheet = spreadsheet.sheet1
        print(f"Aktif sayfa adı: {sheet.title}")

        print("5. Sütun yapısına uygun örnek veriler yazılıyor...")
        # A'dan O'ya kadar olan 15 sütunun sırasına göre örnek veri seti:
        # [Sembol, Şirket İsmi, Son, Değişim ( % ), Hacim, Göreceli Hacim, Piyasa Değeri, Piyasa Değeri Performansı ( % ), FAVÖK, FD / FAVÖK, EPS, EPS Seyereltilmiş Büyüme, FKO, FSO, P / B]
        ornek_veri = [
            "AEFES", "Anadolu Efes", "100.50", "+1.25", "1500000", "1.5", 
            "60000000", "+5.2", "12000000", "5.0", "4.5", "12.4", "8.2", "3.1", "2.1"
        ]
        
        sheet.append_row(ornek_veri)
        print("İşlem başarıyla tamamlandı, veriler ilgili sütunlara yerleştirildi.")

    except Exception as e:
        print("\nKRİTİK HATA TESPİT EDİLDİ:")
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    main()
