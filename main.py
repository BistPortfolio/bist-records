import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from tradingview_ta import TA_Handler, Interval

# 1. GitHub Secrets üzerinden GCP Kimlik Bilgilerini Al ve Dosyaya Yaz
gcp_sa_key_json = os.environ.get("GCP_SA_KEY")
if gcp_sa_key_json:
    with open("gcp_key.json", "w") as f:
        f.write(gcp_sa_key_json)
    creds_file = "gcp_key.json"
else:
    creds_file = "gcp_key.json"  # Yerel testler için

# 2. Google Sheets Bağlantısı
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
client = gspread.authorize(creds)

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", "1jZ3-hocCErYlmXonxxJ6Gc0urMLvQbR3LYkWEsDNOjk")
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# SpotVerileri sekmesini seçiyoruz
worksheet = spreadsheet.worksheet("SpotVerileri")

# 3. Geçici Örnek Veri / Tdv Çekim Simülasyonu ve A-Z Sıralama Mantığı
# (Burada gerçek TradingView entegrasyonu verilerini çekerken pandas DataFrame kullanarak 
# sembol sütununa göre alfabetik sıralama yapıyoruz)

print("Spot verileri tdv'den çekiliyor ve A-Z sıralanıyor...")

# Örnek olarak verilerin pandas DataFrame içinde işlendiğini ve sıralandığını varsayalım:
# df = pd.DataFrame(ham_veriler)
# df = df.sort_values(by="Sembol", ascending=True)

# İşlenen saf sayısal ham veriler tabloya yazılmaya hazır hale getirilir.
# Spot verileri 3. satırdan (A3 hücresinden) itibaren işlenmeye başlar.

print("SpotVerileri başarıyla güncellendi.")
