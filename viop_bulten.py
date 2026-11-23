"""
Vadeli İşlem ve Opsiyon Piyasası Günlük Bülteni -> Borsaİstanbul / ViopBülten
Kaynak : /data/vadeli/viop_YYYYAAGG.csv
Yazma  : A1 ve B1 = bülten tarihleri, veriler 3. satırdan itibaren (1-2. satırlar başlıktır)
Zaman  : Hafta içi her gün 23:00 (Türkiye saati), viop-bulten.yml
Kural  : kurallar_viop_bulten.json (PAZAR SEGMENTI süzme ve sıralama)
"""
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, date, timedelta

import ortak
from gspread.utils import a1_to_rowcol

KAYNAK = SEKME = "ViopBülten"
URL = ortak.SITE + "/data/vadeli/viop_{yil}{ay}{gun}.csv"
GERI_GUN = 6                            # bugünün bülteni yoksa en fazla kaç gün geriye bakılır
ILK_SATIR = 3
BASLIK_SONRASI_ATLA = 1                 # Türkçe başlıktan sonra gelen İngilizce satır
KURAL_DOSYASI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kurallar_viop_bulten.json")
SEGMENT_SUTUNU = a1_to_rowcol("T1")[1] - 1     # PAZAR SEGMENTI
DAYANAK_SUTUNU = a1_to_rowcol("U1")[1] - 1     # DAYANAK VARLIK
VADE_SUTUNU = a1_to_rowcol("B1")[1] - 1        # VADE TARIHI

ESLEME = {
    "SOZLESME KODU": "A", "PAZAR SEGMENTI": "T", "DAYANAK VARLIK": "U",
    "VADE TARIHI": "B", "UZLASMA FIYATI": "H", "ONCEKI UZLASMA FIYATI": "I",
    "UZLASMA FIYATI DEGISIMI (%)": "J", "ACILIS FIYATI": "C", "EN DUSUK FIYAT": "D",
    "EN YUKSEK FIYAT": "E", "KAPANIS FIYATI": "F", "AGIRLIKLI ORTALAMA FIYAT": "G",
    "ISLEM HACMI": "K", "ISLEM MIKTARI": "L", "ISLEM SAYISI": "M",
    "ACIK POZISYON": "N", "ACIK POZISYON DEGISIMI": "O", "ACILIS SEANSI FIYATI": "P",
    "ACILIS SEANSI ISLEM ISLEM HACMI": "Q",
    "ACILIS SEANSI ISLEM HACMI": "Q",          # olası yazım farkı: biri bulunursa yeterli
    "ACILIS SEANSI ISLEM MIKTARI": "R", "ACILIS SEANSI ISLEM SAYISI": "S",
}
ALTERNATIF = {"ACILIS SEANSI ISLEM ISLEM HACMI": "ACILIS SEANSI ISLEM HACMI",
              "ACILIS SEANSI ISLEM HACMI": "ACILIS SEANSI ISLEM ISLEM HACMI"}


def en_son_bulteni_bul():
    bugun = ortak.simdi().date()
    for geri in range(GERI_GUN + 1):
        t = bugun - timedelta(days=geri)
        if t.weekday() >= 5:
            continue
        adres = URL.format(yil=t.strftime("%Y"), ay=t.strftime("%m"), gun=t.strftime("%d"))
        ham = ortak.indir(adres)
        if ham is not None and ham.lstrip()[:1] != b"<":   # "<": sitenin "yok" sayfası
            print("Bulundu:", adres)
            return adres, ham
    return None, None


def vade_tarihi(v):
    s = str(v).strip()
    for bicim in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(s, bicim).date()
        except ValueError:
            pass
    return date.max


def dayanak_temizle(v):
    """DAYANAK VARLIK değerlerindeki THYAO.E gibi .E uzantısını kaldırır (başka uzantıya dokunmaz)."""
    return re.sub(r"\.E$", "", str(v).strip())


def kurallari_uygula(matris):
    """PAZAR SEGMENTI'ne göre satırları süzer ve sıralar."""
    with open(KURAL_DOSYASI, encoding="utf-8") as f:
        kural = json.load(f)
    sira = {g.upper(): i for i, g in enumerate(kural["gruplar"])}
    alfabetik = kural.get("grup_ici_siralama") == "alfabetik"
    secilen, disarida = [], Counter()
    for satir in matris:
        seg = str(satir[SEGMENT_SUTUNU]).strip().upper()
        if seg not in sira:
            disarida[seg or "(boş)"] += 1
            continue
        satir[DAYANAK_SUTUNU] = dayanak_temizle(satir[DAYANAK_SUTUNU])
        kod = str(satir[0])
        anahtar = ((sira[seg], kod) if alfabetik else
                   (sira[seg], str(satir[DAYANAK_SUTUNU]), vade_tarihi(satir[VADE_SUTUNU]), kod))
        secilen.append((anahtar, satir))
    secilen.sort(key=lambda x: x[0])
    if disarida:
        print("Kural dışı segmentler (yazılmadı):", ", ".join("%s=%d" % kv for kv in sorted(disarida.items())))
    return [x[1] for x in secilen]


def hazirla(ham):
    rows = ortak.satirlari_oku(ham)
    hi = ortak.baslik_bul(rows, ESLEME.keys())
    baslik = rows[hi]
    veri = rows[hi + 1 + BASLIK_SONRASI_ATLA:]
    if not veri:
        raise ValueError("Bültende veri satırı yok.")

    # Tarih sütunları: başlığında TARIH geçen (VADE TARIHI hariç); 1. -> A1, 2. -> B1
    tarih_sutunlari = [j for j, b in enumerate(baslik)
                       if "TARIH" in ortak.anahtar(str(b).split(" / ")[0])
                       and ortak.anahtar(str(b).split(" / ")[0]) != "VADETARIHI"]
    if not tarih_sutunlari:
        tarih_sutunlari = [0]
    tarihler = [str(veri[0][j]).strip() for j in tarih_sutunlari[:2]]
    print("Tarih sütunları:", [str(baslik[j]) for j in tarih_sutunlari[:2]], "->", tarihler)

    matris, eksik = ortak.matris_olustur(baslik, veri, ESLEME, kod_temizle_uygula=False)
    eksik = [k for k in eksik if ALTERNATIF.get(k) in eksik or ALTERNATIF.get(k) is None]
    if eksik:
        print("UYARI - dosyada bulunamayan başlıklar:", ", ".join(eksik))
    for zorunlu in ("SOZLESME KODU", "PAZAR SEGMENTI"):
        if zorunlu in eksik:
            print("Dosyanın ilk satırları:")
            ortak.ornek_yaz(rows)
            raise ValueError(zorunlu + " sütunu bulunamadı.")
    matris = kurallari_uygula(matris)
    if not matris:
        raise ValueError("Kurallara uyan satır yok, sekmeye dokunulmadı.")
    return tarihler, matris


def main():
    tablo = ortak.baglan()
    try:
        adres, ham = en_son_bulteni_bul()
        if ham is None:
            raise RuntimeError("Son %d günde bülten dosyası bulunamadı." % GERI_GUN)
        tarihler, matris = hazirla(ham)
        ws = ortak.sayfa_getir(tablo, SEKME)
        ortak.tablo_yaz(ws, matris, ILK_SATIR)
        ws.update(values=[[tarihler[0]]], range_name="A1", value_input_option="RAW")
        if len(tarihler) > 1:
            ws.update(values=[[tarihler[1]]], range_name="B1", value_input_option="RAW")
        ortak.durum_yaz(tablo, KAYNAK, "tamam, bülten tarihi " + tarihler[0], len(matris), True)
        print("%d satır yazıldı. Bülten tarihi: %s" % (len(matris), tarihler[0]))
    except Exception as e:
        ortak.durum_yaz(tablo, KAYNAK, "HATA: %s" % e)
        raise


if __name__ == "__main__":
    sys.exit(main())
