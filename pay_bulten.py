"""
Pay Piyasası Bülteni (günlük) -> Borsaİstanbul / PayBülten
Kaynak : /data/thb/YYYY/AA/thbYYYYAAGGS.zip   (S: dosya sıra eki, aşağıda denenir)
Yazma  : A1 = bülten tarihi, veriler 3. satırdan itibaren (1-2. satırlar başlıktır)
Zaman  : Hafta içi her gün 23:00 (Türkiye saati), pay-bulten.yml
"""
import json
import os
import sys
from collections import Counter
from datetime import timedelta

import ortak
from gspread.utils import a1_to_rowcol

KAYNAK = SEKME = "PayBülten"
URL = ortak.SITE + "/data/thb/{yil}/{ay}/thb{yil}{ay}{gun}{s}.zip"
S_ADAYLARI = ["1", "2", "3", "0", ""]   # dosya adındaki son eki: ilk bulunan kullanılır
GERI_GUN = 6                            # bugünün bülteni yoksa en fazla kaç gün geriye bakılır
ILK_SATIR = 3
BASLIK_SONRASI_ATLA = 1                 # Türkçe başlıktan sonra gelen İngilizce satır
KURAL_DOSYASI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kurallar_pay_bulten.json")
GRUP_SUTUNU = a1_to_rowcol("AC1")[1] - 1   # ENSTRUMAN GRUBU: GTS AC sütunu (0 tabanlı indeks)

ESLEME = {
    "ISLEM KODU": "A", "ENSTRUMAN GRUBU": "AC", "BIST 100 ENDEKS": "AD",
    "BIST 30 ENDEKS": "AE", "ONCEKI KAPANIS FIYATI": "B", "ACILIS FIYATI": "C",
    "EN DUSUK FIYAT": "D", "EN YUKSEK FIYAT": "E", "KAPANIS FIYATI": "F",
    "DEGISIM (%)": "G", "BEKLEYEN EN IYI ALIS": "I", "BEKLEYEN EN IYI SATIS": "J",
    "A.O.F": "H", "TOPLAM ISLEM HACMI": "K", "TOPLAM ISLEM ADEDI": "L",
    "TOPLAM SOZLESME SAYISI": "M", "ACILIS SEANSI ISLEM HACMI": "N",
    "ACILIS SEANSI ISLEM MIKTARI": "O", "ACILIS SEANSI SOZLESME SAYISI": "P",
    "KAPANIS SEANSI ISLEM HACMI": "Q", "KAPANIS SEANSI ISLEM MIKTARI": "R",
    "KAPANIS SEANSI SOZLESME SAYISI": "S", "KAPANIS FIYATINDAN ISLEMLER HACMI": "T",
    "KAPANIS FIYATINDAN ISLEMLER ISLEM MIKTARI": "U",
    "KAPANIS FIYATINDAN ISLEMLER SOZLESME SAYISI": "V",
    "EN DUSUK ACIGA SATIS": "W", "EN YUKSEK ACIGA SATIS": "X", "ACIGA SATIS A.O.F": "Y",
    "ACIGA SATIS ISLEM HACMI": "Z", "ACIGA SATIS ISLEM ADEDI": "AA",
    "ACIGA SATIS SOZLESME SAYISI": "AB", "ACIGA SATIS": "AF",
    "BIST KATILIM TUM ENDEKS": "AG",
}


def en_son_bulteni_bul():
    bugun = ortak.simdi().date()
    for geri in range(GERI_GUN + 1):
        t = bugun - timedelta(days=geri)
        if t.weekday() >= 5:
            continue
        for s in S_ADAYLARI:
            adres = URL.format(yil=t.strftime("%Y"), ay=t.strftime("%m"),
                               gun=t.strftime("%d"), s=s)
            ham = ortak.indir(adres)
            if ham is not None and ham[:2] == b"PK":   # PK değilse sitenin "yok" sayfası
                print("Bulundu:", adres)
                return adres, ham
    return None, None


def kurallari_uygula(matris):
    """ENSTRUMAN GRUBU'na göre satırları süzer, A sütunundaki uzantıyı kaldırır ve sıralar."""
    with open(KURAL_DOSYASI, encoding="utf-8") as f:
        gruplar = json.load(f)["gruplar"]
    kural = {g["kod"].upper(): (sira, g.get("uzanti", "")) for sira, g in enumerate(gruplar)}
    secilen, disarida, uzantisiz = [], Counter(), 0
    for satir in matris:
        grup = str(satir[GRUP_SUTUNU]).strip().upper()
        if grup not in kural:
            disarida[grup or "(boş)"] += 1
            continue
        sira, uzanti = kural[grup]
        kod = str(satir[0]).strip()
        if uzanti and kod.upper().endswith(uzanti.upper()):
            kod = kod[:-len(uzanti)]
        elif uzanti:
            uzantisiz += 1
        satir[0] = kod
        secilen.append((sira, kod, satir))
    secilen.sort(key=lambda x: (x[0], x[1]))
    if disarida:
        print("Kural dışı gruplar (yazılmadı):", ", ".join("%s=%d" % kv for kv in sorted(disarida.items())))
    if uzantisiz:
        print("UYARI - beklenen uzantıya sahip olmayan kod sayısı:", uzantisiz)
    return [x[2] for x in secilen]


def hazirla(ham):
    rows = ortak.satirlari_oku(ham)
    hi = ortak.baslik_bul(rows, ESLEME.keys())
    baslik = rows[hi]
    veri = rows[hi + 1 + BASLIK_SONRASI_ATLA:]
    if not veri:
        raise ValueError("Bültende veri satırı yok.")
    tarih = str(veri[0][0]).strip()          # web tablosunun A sütunu: bülten tarihi
    matris, eksik = ortak.matris_olustur(baslik, veri, ESLEME, kod_temizle_uygula=False)
    if eksik:
        print("UYARI - dosyada bulunamayan başlıklar:", ", ".join(eksik))
    if "ISLEM KODU" in eksik:
        print("Dosyanın ilk satırları:")
        ortak.ornek_yaz(rows)
        raise ValueError("ISLEM KODU sütunu bulunamadı.")
    if "ENSTRUMAN GRUBU" in eksik:
        raise ValueError("ENSTRUMAN GRUBU sütunu bulunamadı.")
    matris = kurallari_uygula(matris)
    if not matris:
        raise ValueError("Kurallara uyan satır yok, sekmeye dokunulmadı.")
    return tarih, matris


def main():
    tablo = ortak.baglan()
    try:
        adres, ham = en_son_bulteni_bul()
        if ham is None:
            raise RuntimeError("Son %d günde bülten dosyası bulunamadı." % GERI_GUN)
        tarih, matris = hazirla(ham)
        ws = ortak.sayfa_getir(tablo, SEKME)
        ortak.tablo_yaz(ws, matris, ILK_SATIR)
        ws.update(values=[[tarih]], range_name="A1", value_input_option="RAW")
        ortak.durum_yaz(tablo, KAYNAK, "tamam, bülten tarihi " + tarih, len(matris), True)
        print("%d satır yazıldı. Bülten tarihi: %s" % (len(matris), tarih))
    except Exception as e:
        ortak.durum_yaz(tablo, KAYNAK, "HATA: %s" % e)
        raise


if __name__ == "__main__":
    sys.exit(main())
