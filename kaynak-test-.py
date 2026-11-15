"""
Kaynak inceleme: verilen adresteki dosyayı (CSV, ZIP içinde CSV, XLSX) indirir,
sütun adlarını ve SON SATIRDAKİ değerleri Borsaİstanbul tablosundaki
"Inceleme" sekmesine yazar. Hangi sütunların gerekli olduğunu seçmek içindir.

Kullanım : python kaynak_test.py <adres>
Ortam    : GCP_SA_KEY, SPREADSHEET_ID  (repository secrets)
"""
import csv
import io
import json
import os
import sys
import zipfile
from collections import Counter
from urllib.parse import urlparse

import requests

BASLIK = {"User-Agent": "Mozilla/5.0 (BistPortfoy kaynak incelemesi)"}
SEKME = "Inceleme"
MAKS_BAYT = 60 * 1024 * 1024


def kodlama_bul(ham):
    if ham.startswith((b"\xff\xfe", b"\xfe\xff")):
        return "utf-16"
    if ham.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    if ham[:400].count(b"\x00") > 50:
        return "utf-16-le"
    try:
        ham.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        return "cp1254"


def csv_coz(ham):
    kod = kodlama_bul(ham)
    satirlar = [s for s in ham.decode(kod).splitlines() if s.strip()]
    ornek = satirlar[:50]
    ayrac = max(";,\t", key=lambda a: sum(s.count(a) for s in ornek))
    sayilar = [s.count(ayrac) for s in satirlar]
    dolu = [c for c in sayilar[:50] if c > 0]
    if not dolu:
        raise ValueError("Tablo yapısı bulunamadı (ayraç tespit edilemedi).")
    ortak = Counter(dolu).most_common(1)[0][0]
    ilk = next(i for i, c in enumerate(sayilar) if c == ortak)
    son = max(i for i, c in enumerate(sayilar) if c == ortak)

    def ayir(satir):
        return next(csv.reader([satir], delimiter=ayrac))

    return {"tur": "CSV", "kodlama": kod, "ayrac": repr(ayrac),
            "baslik": ayir(satirlar[ilk]), "son": ayir(satirlar[son])}


def xlsx_coz(ham):
    from openpyxl import load_workbook
    wb = load_workbook(io.BytesIO(ham), read_only=True, data_only=True)
    ws = wb.active
    satirlar = []
    for r in ws.iter_rows(values_only=True):
        r = ["" if c is None else str(c) for c in r]
        if any(c.strip() for c in r):
            satirlar.append(r)
    if not satirlar:
        raise ValueError("Sayfa boş.")
    en_dolu = max(range(min(20, len(satirlar))),
                  key=lambda i: (sum(1 for c in satirlar[i] if c.strip()), -i))
    return {"tur": "XLSX", "kodlama": "-", "ayrac": "-",
            "baslik": satirlar[en_dolu], "son": satirlar[-1]}


def dosya_coz(ad, ham):
    if ham[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(ham))
        adlar = [n for n in z.namelist() if not n.endswith("/")]
        if "xl/workbook.xml" in adlar:
            return xlsx_coz(ham)
        print("ZIP içeriği:", ", ".join(adlar))
        ic = adlar[0]
        return dosya_coz(ic, z.read(ic))
    if ad.lower().endswith(".xls"):
        raise ValueError("Eski .xls biçimi desteklenmiyor.")
    return csv_coz(ham)


def indir(adres):
    r = requests.get(adres, headers=BASLIK, timeout=60, stream=True)
    print("Durum kodu:", r.status_code, "| Tür:", r.headers.get("Content-Type", "-"))
    if r.status_code != 200:
        if r.status_code in (403, 429):
            print("UYARI: Sunucu bu bağlantıyı engelliyor olabilir.")
        raise SystemExit(1)
    parcalar, toplam = [], 0
    for p in r.iter_content(1024 * 256):
        toplam += len(p)
        if toplam > MAKS_BAYT:
            raise SystemExit("Dosya çok büyük (60 MB üstü).")
        parcalar.append(p)
    return b"".join(parcalar)


def tabloya_yaz(adres, s):
    import gspread
    anahtar = os.environ.get("GCP_SA_KEY")
    tablo_id = os.environ.get("SPREADSHEET_ID")
    if not anahtar or not tablo_id:
        print("GCP_SA_KEY veya SPREADSHEET_ID tanımlı değil, tabloya yazılmadı.")
        return
    tablo = gspread.service_account_from_dict(json.loads(anahtar)).open_by_key(tablo_id)
    try:
        ws = tablo.worksheet(SEKME)
    except gspread.WorksheetNotFound:
        ws = tablo.add_worksheet(title=SEKME, rows=200, cols=6)

    bas, son = s["baslik"], s["son"]
    son = son + [""] * (len(bas) - len(son))
    veri = [["Kaynak", adres], ["Biçim", s["tur"], s["kodlama"], s["ayrac"]], [],
            ["No", "Sütun adı", "Son satır", "Seç"]]
    veri += [[i + 1, ad, son[i], ""] for i, ad in enumerate(bas)]
    if len(veri) > ws.row_count:
        ws.resize(rows=len(veri) + 20)
    ws.clear()
    ws.update(values=veri, range_name="A1", value_input_option="RAW")
    print("'%s' sekmesine %d sütun yazıldı." % (SEKME, len(bas)))


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith("http"):
        print("Kullanım: python kaynak_test.py <http veya https adresi>")
        return 2
    adres = sys.argv[1]
    ham = indir(adres)
    ad = os.path.basename(urlparse(adres).path)
    sonuc = dosya_coz(ad, ham)
    tabloya_yaz(adres, sonuc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
