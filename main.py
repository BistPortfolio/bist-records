import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tradingview_ta import TA_Handler, Interval
import pandas as pd

def main():
    # 1. Google Sheets Bağlantısı
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    sa_key_json = os.environ.get("GCP_SA_KEY")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    
    if not sa_key_json or not spreadsheet_id:
        raise ValueError("GCP_SA_KEY veya SPREADSHEET_ID ortam değişkenleri eksik!")
        
    creds_dict = json.loads(sa_key_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.worksheet("SpotVerileri")
    
    # 2. Veri Çekme
    symbols = ["THYAO", "GARAN", "AKBNK", "EREGL", "KCHOL"]
    data_list = []
    
    for symbol in symbols:
        try:
            handler = TA_Handler(
                symbol=symbol,
                screener="turkey",
                exchange="BIST",
                interval=Interval.INTERVAL_1_DAY
            )
            analysis = handler.get_analysis()
            
            data_list.append({
                "Sembol": symbol,
                "Fiyat": analysis.indicators.get("close", 0),
                "Hacim": analysis.indicators.get("volume", 0)
            })
        except Exception as e:
            print(f"{symbol} çekilirken hata oluştu: {e}")
            
    if not data_list:
        print("İşlenecek veri bulunamadı.")
        return

    # Pandas ile A-Z Alfabetik Sıralama
    df = pd.DataFrame(data_list)
    df = df.sort_values(by="Sembol", ascending=True)
    
    # 3. Google Sheets'e Yazdırma (Tablo başlıklarını uçurmadan, 3. satırdan başlatarak)
    # Önce 3. satırdan sonraki eski verileri temizleyelim (A3 hücresinden itibaren)
    # Veya doğrudan 3. satırdan itibaren verileri güncelliyoruz:
    rows = df.values.tolist()
    
    # A3 hücresinden başlayarak verileri yazdırıyoruz (Başlıklara dokunmuyoruz!)
    worksheet.update(values=rows, range_name=f"A3:C{2 + len(rows)}")
    print("Veriler SpotVerileri sekmesine 3. satırdan itibaren alfabetik olarak yazıldı!")

if __name__ == "__main__":
    main()
