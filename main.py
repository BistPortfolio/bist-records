import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tradingview_ta import TA_Handler, Interval
import pandas as pd

def main():
    # 1. Google Sheets Bağlantısı (Environment Secrets üzerinden)
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # GitHub Secrets'tan GCP Service Account JSON verisini alıyoruz
    sa_key_json = os.environ.get("GCP_SA_KEY")
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    
    if not sa_key_json or not spreadsheet_id:
        raise ValueError("GCP_SA_KEY veya SSPREADSHEET_ID ortam değişkenleri eksik!")
        
    creds_dict = json.loads(sa_key_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # E-tabloyu ve SpotVerileri sekmesini açıyoruz
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = spreadsheet.worksheet("SpotVerileri")
    
    # 2. Örnek Veri Çekme ve İşleme (Takip edeceğin sembol listesini buraya ekleyebilirsin)
    # Şimdilik örnek birkaç BIST hissesi ile test yapıyoruz
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
            
            # Verileri sözlük olarak topluyoruz
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

    # Pandas ile veriyi DataFrame'e çevirip Sembol adına göre A-Z alfabetik sıralıyoruz
    df = pd.DataFrame(data_list)
    df = df.sort_values(by="Sembol", ascending=True)
    
    # 3. Google Sheets'e Yazdırma İşlemi
    # Önce mevcut verileri temizleyip başlıklarla beraber tabloya yazıyoruz
    worksheet.clear()
    
    # Başlıklar ve satır değerlerini listeye çeviriyoruz
    header = list(df.columns)
    rows = df.values.tolist()
    
    # Tabloya veri akışını sağlıyoruz (3. satırdan başladığını varsayarak veya direkt tepeye)
    worksheet.update([header] + rows)
    print("Veriler SpotVerileri sekmesine alfabetik olarak başarıyla yazıldı!")

if __name__ == "__main__":
    main()
