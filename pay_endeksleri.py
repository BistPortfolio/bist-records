"""
BIST Pay Endeksleri (TL, USD, EURO) -> Borsaİstanbul / PayEndeksler
Kaynak : /datum/PayEndeksleri.zip
Yazma  : Dosyadaki tüm satırlar (başlık dahil) A1'den itibaren. KUR TURU sütunu TL, USD ve EUR
         satırlarını birbirinden ayırır; hepsi tek sekmede toplanır.
Zaman  : Hafta içi her gün 23:00 (Türkiye saati), pay-endeksleri.yml
"""
import sys

import ortak

KAYNAK = SEKME = "PayEndeksler"
URL = ortak.SITE + "/datum/PayEndeksleri.zip"
ILK_SATIR = 1


def hazirla(ham):
    """Tüm satırlar olduğu gibi alınır; sayılar sayıya çevrilir."""
    rows = ortak.satirlari_oku(ham)
    matris = [[ortak.sayi_cevir(c) for c in r] for r in rows]
    if len(matris) < 2:
        raise ValueError("Dosyada veri satırı yok.")
    return matris


def main():
    tablo = ortak.baglan()
    try:
        ham = ortak.indir(URL)
        if ham is None:
            raise RuntimeError("Dosya bulunamadı (404): " + URL)
        matris = hazirla(ham)
        ortak.tablo_yaz(ortak.sayfa_getir(tablo, SEKME), matris, ILK_SATIR)
        ortak.durum_yaz(tablo, KAYNAK, "tamam", len(matris) - 1, True)
        print("%d veri satırı yazıldı." % (len(matris) - 1))
    except Exception as e:
        ortak.durum_yaz(tablo, KAYNAK, "HATA: %s" % e)
        raise


if __name__ == "__main__":
    sys.exit(main())
