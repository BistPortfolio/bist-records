"""
Açığa Satış İşlemleri (haftalık) -> Borsaİstanbul / PayAçığaSatış
Kaynak : /datum/acigasat.zip
Yazma  : B1 = bülten hafta bilgisi (birleştirilmiş B1:E1), veriler 3. satırdan itibaren A:E
Zaman  : Her Cuma 23:00 (Türkiye saati), pay-acigasatis.yml
"""
import sys

import ortak

KAYNAK = SEKME = "PayAçığaSatış"
URL = ortak.SITE + "/datum/acigasat.zip"
ILK_SATIR = 3

ESLEME = {
    "İşlem Kodu": "A", "İşlem Hacmi (TL)": "B", "İşlem Miktarı": "C",
    "En Düşük Fiyat": "D", "En Yüksek Fiyat": "E",
}


def hazirla(ham):
    rows = ortak.satirlari_oku(ham)
    hi = ortak.baslik_bul(rows, ESLEME.keys())
    ust, baslik, veri = rows[:hi], rows[hi], rows[hi + 1:]
    donem = ""
    for r in ust:                                  # başlıktan önceki ilk dolu hücre: hafta bilgisi
        dolu = [str(c).strip() for c in r if str(c).strip()]
        if dolu:
            donem = dolu[0]
            break
    matris, eksik = ortak.matris_olustur(baslik, veri, ESLEME)
    if eksik:
        print("UYARI - dosyada bulunamayan başlıklar:", ", ".join(eksik))
    if "İşlem Kodu" in eksik:
        raise ValueError("İşlem Kodu sütunu bulunamadı.")
    return donem, matris


def main():
    tablo = ortak.baglan()
    try:
        ham = ortak.indir(URL)
        if ham is None:
            raise RuntimeError("Dosya bulunamadı (404): " + URL)
        donem, matris = hazirla(ham)
        ws = ortak.sayfa_getir(tablo, SEKME)
        ortak.tablo_yaz(ws, matris, ILK_SATIR)
        ws.update(values=[[donem]], range_name="B1", value_input_option="RAW")
        ortak.durum_yaz(tablo, KAYNAK, "tamam, " + donem, len(matris), True)
        print("%d satır yazıldı. %s" % (len(matris), donem))
    except Exception as e:
        ortak.durum_yaz(tablo, KAYNAK, "HATA: %s" % e)
        raise


if __name__ == "__main__":
    sys.exit(main())
