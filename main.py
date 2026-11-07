import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from tradingview_ta import TA_Handler, Interval
import pandas as pd

def main():
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
            print(f"{symbol} hata: {e}")
            
    if not data_list:
        return

    df = pd.DataFrame(data_list)
    df = df.sort_values(by="Sembol", ascending=True)
    
    rows = df.values.tolist()
    worksheet.update("A3", rows)

if __name__ == "__main__":
    main()
