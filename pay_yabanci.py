"""
Yabancı Yatırımcı İşlemleri (aylık) -> Borsaİstanbul / PayYabancı
Kaynak : /datfile/specialfile?key=pay_yabanci   (zip, ör. yabanci202609.zip)
Yazma  : Dosyadaki tüm satırlar A1'den itibaren, A sütunundaki .E uzantıları kaldırılır
Zaman  : Her ayın son iş günü 23:00 (Türkiye saati), pay-yabanci.yml
Elle çalıştırmada (ZORLA=true) tarih kontrolü yapılmaz.
"""
import os
import re
import sys

import ortak

KAYNAK = SEKME = "PayYabancı"
URL = ortak.SITE + "/datfile/specialfile?key=pay_yabanci"
ILK_SATIR = 1


def hazirla(ham):
    """Tüm satırlar olduğu gibi alınır; sayılar sayıya çevrilir, A sütunundaki
    A1CAP.E gibi kodların uzantısı (.E, .F, .G) her satırda kaldırılır."""
    matris = []
    for r in ortak.satirlari_oku(ham):
        yeni = [ortak.sayi_cevir(c) for c in r]
        if yeni and re.fullmatch(r"[A-Z0-9_]+\.[A-Z]", str(yeni[0]).strip()):
            yeni[0] = ortak.kod_temizle(yeni[0])
        matris.append(yeni)
    return matris


def main():
    zorla = os.environ.get("ZORLA", "").lower() == "true"
    bugun = ortak.simdi().date()
    if not zorla and not ortak.son_is_gunu_mu_ay(bugun):
        print("Bugün ayın son iş günü değil, güncelleme yapılmadı.")
        return 0
    tablo = ortak.baglan()
    try:
        ham = ortak.indir(URL)
        if ham is None:
            raise RuntimeError("Dosya bulunamadı (404): " + URL)
        matris = hazirla(ham)
        ortak.tablo_yaz(ortak.sayfa_getir(tablo, SEKME), matris, ILK_SATIR)
        ortak.durum_yaz(tablo, KAYNAK, "tamam", len(matris), True)
        print("%d satır yazıldı." % len(matris))
    except Exception as e:
        ortak.durum_yaz(tablo, KAYNAK, "HATA: %s" % e)
        raise


if __name__ == "__main__":
    sys.exit(main())
