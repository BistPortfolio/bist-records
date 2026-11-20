"""
Pay Piyasası Bülteni (günlük) -> Borsaİstanbul / PayBülten
Kaynak : /data/thb/YYYY/AA/thbYYYYAAGGS.zip   (S: dosya sıra eki, aşağıda denenir)
Yazma  : A1 = bülten tarihi, veriler 3. satırdan itibaren (1-2. satırlar başlıktır)
Zaman  : Hafta içi her gün 23:00 (Türkiye saati), pay-bulten.yml
"""
import sys
from datetime import timedelta

import ortak

KAYNAK = SEKME = "PayBülten"
URL = ortak.SITE + "/data/thb/{yil}/{ay}/thb{yil}{ay}{gun}{s}.zip"
S_ADAYLARI = ["1", "2", "3", "0", ""]   # dosya adındaki son eki: ilk bulunan kullanılır
GERI_GUN = 6                            # bugünün bülteni yoksa en fazla kaç gün geriye bakılır
ILK_SATIR = 3
BASLIK_SONRASI_ATLA = 1                 # Türkçe başlıktan sonra gelen İngilizce satır

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


def hazirla(ham):
    rows = ortak.satirlari_oku(ham)
    hi = ortak.baslik_bul(rows)
    baslik = rows[hi]
    veri = rows[hi + 1 + BASLIK_SONRASI_ATLA:]
    if not veri:
        raise ValueError("Bültende veri satırı yok.")
    tarih = str(veri[0][0]).strip()          # web tablosunun A sütunu: bülten tarihi
    matris, eksik = ortak.matris_olustur(baslik, veri, ESLEME)
    if eksik:
        print("UYARI - dosyada bulunamayan başlıklar:", ", ".join(eksik))
    if "ISLEM KODU" in eksik:
        raise ValueError("ISLEM KODU sütunu bulunamadı.")
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
