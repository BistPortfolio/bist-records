"""
BistPortföy - Veri akışı: GitHub Actions -> Google Sheets (yönetici tablosu)
 
Kullanım:
    python main.py test      Bağlantıyı ve yazma iznini dener, "Durum" sekmesine yazar.
    python main.py guncelle  KAYNAKLAR listesindeki her kaynağı çeker ve ilgili sekmeye yazar.
 
Gerekli ortam değişkenleri (GitHub > Settings > Secrets and variables > Actions):
    GCP_SA_KEY      Servis hesabı anahtar dosyasının TÜM JSON içeriği
    SPREADSHEET_ID  Yönetici tablosunun (Borsaİstanbul) kimliği
 
Servis hesabının e-postası (anahtardaki client_email) tabloya DÜZENLEYİCİ
olarak eklenmiş olmalıdır.
"""
import json
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
 
import gspread
from gspread.utils import rowcol_to_a1
 
TR = ZoneInfo("Europe/Istanbul")
 
 
def simdi():
    return datetime.now(TR).strftime("%Y-%m-%d %H:%M:%S")
 
 
# ---------------------------------------------------------------- Google Sheets
 
def baglan():
    anahtar = os.environ.get("GCP_SA_KEY")
    tablo_id = os.environ.get("SPREADSHEET_ID")
    if not anahtar or not tablo_id:
        raise RuntimeError("GCP_SA_KEY veya SPREADSHEET_ID tanımlı değil (repository secrets).")
    gc = gspread.service_account_from_dict(json.loads(anahtar))
    return gc.open_by_key(tablo_id)
 
 
def sayfa_getir(tablo, ad):
    """Sekmeyi döndürür, yoksa oluşturur."""
    try:
        return tablo.worksheet(ad)
    except gspread.WorksheetNotFound:
        return tablo.add_worksheet(title=ad, rows=1000, cols=26)
 
 
def tabloyu_yaz(ws, basliklar, satirlar):
    """
    Başlık + satırları tek istekte yazar (API kotasını korur), artan eski
    satırları temizler. Veri, temizlemeden ÖNCE yazıldığı için sekme hiçbir
    anda boş kalmaz. Sayılar float/int olarak gönderilmelidir (RAW yazılır,
    tablonun yerel ayarından etkilenmez).
    """
    veri = [basliklar] + satirlar
    satir_sayisi = len(veri)
    sutun_sayisi = max(len(r) for r in veri)
 
    if satir_sayisi > ws.row_count or sutun_sayisi > ws.col_count:
        ws.resize(rows=max(ws.row_count, satir_sayisi + 100),
                  cols=max(ws.col_count, sutun_sayisi))
 
    ws.update(values=veri, range_name="A1", value_input_option="RAW")
 
    if ws.row_count > satir_sayisi:
        ilk = "A%d" % (satir_sayisi + 1)
        son = rowcol_to_a1(ws.row_count, ws.col_count)
        ws.batch_clear(["%s:%s" % (ilk, son)])
 
 
# ---------------------------------------------------------------- Kaynaklar
# Her kaynak fonksiyonu (basliklar, satirlar) döndürür:
#   basliklar: ["SEMBOL", "SON FİYAT", ...]
#   satirlar : [["THYAO", 312.5, ...], ...]  (sayılar float/int olmalı)
 
def spot_verileri():
    raise NotImplementedError("SpotVerileri kaynağı henüz tanımlanmadı")
 
 
def viop_verileri():
    raise NotImplementedError("ViopVerileri kaynağı henüz tanımlanmadı")
 
 
KAYNAKLAR = [
    ("SpotVerileri", spot_verileri),
    ("ViopVerileri", viop_verileri),
]
 
 
# ---------------------------------------------------------------- Çalıştırma
 
def eski_durum(durum_ws):
    """Önceki 'son başarılı' zamanlarını korumak için Durum sekmesini okur."""
    sonuc = {}
    try:
        for r in durum_ws.get_all_values()[1:]:
            if len(r) >= 3 and r[0]:
                sonuc[r[0]] = r[2]
    except Exception:
        pass
    return sonuc
 
 
def calistir(mod):
    tablo = baglan()
    durum_ws = sayfa_getir(tablo, "Durum")
 
    if mod == "test":
        durum_ws.update(
            values=[["alan", "deger"], ["son_test", simdi()], ["mod", "test"]],
            range_name="A1", value_input_option="RAW")
        print("Bağlantı ve yazma testi başarılı. Tablo:", tablo.title)
        return 0
 
    eski = eski_durum(durum_ws)
    durum = [["kaynak", "son_deneme", "son_basarili", "kayit_sayisi", "sonuc"]]
    basarili = 0
 
    for ad, fonksiyon in KAYNAKLAR:
        try:
            basliklar, satirlar = fonksiyon()
            tabloyu_yaz(sayfa_getir(tablo, ad), basliklar, satirlar)
            durum.append([ad, simdi(), simdi(), len(satirlar), "tamam"])
            basarili += 1
            print("%s: %d kayıt yazıldı" % (ad, len(satirlar)))
        except Exception as e:
            mesaj = "HATA: %s" % str(e)[:200]
            durum.append([ad, simdi(), eski.get(ad, ""), 0, mesaj])
            print("%s: %s" % (ad, mesaj))
 
    durum_ws.clear()
    durum_ws.update(values=durum, range_name="A1", value_input_option="RAW")
    # Hiçbir kaynak yazılamadıysa iş akışı hata verir (GitHub e-posta bildirimi gönderir)
    return 0 if basarili else 1
 
 
if __name__ == "__main__":
    mod = sys.argv[1] if len(sys.argv) > 1 else "guncelle"
    if mod not in ("test", "guncelle"):
        print("Kullanım: python main.py [test|guncelle]")
        sys.exit(2)
    sys.exit(calistir(mod))
