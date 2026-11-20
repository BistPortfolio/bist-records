"""
Ortak yardımcılar: Borsa İstanbul veri hatları (pay_bulten, pay_acigasatis, pay_yabanci).
Ortam: GCP_SA_KEY, SPREADSHEET_ID (repository secrets)
"""
import csv
import io
import json
import os
import re
import zipfile
from collections import Counter
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import gspread
import requests
from gspread.utils import a1_to_rowcol, rowcol_to_a1

TR = ZoneInfo("Europe/Istanbul")
SITE = "https://www.borsaistanbul.com"
UA = {"User-Agent": "Mozilla/5.0 (BistPortfoy veri hatti)"}
DURUM_SEKMESI = "Durum"


def simdi():
    return datetime.now(TR)


def anahtar(metin):
    """Başlık eşleştirme anahtarı: Türkçe harfler ASCII'ye, harf ve rakam dışı atılır."""
    cevir = str.maketrans("ıİşŞğĞüÜöÖçÇ", "iIsSgGuUoOcC")
    return re.sub(r"[^A-Z0-9]", "", str(metin).translate(cevir).upper())


def son_is_gunu_mu_ay(gun):
    """Hafta içi bir gün ayın son iş günü mü? (Resmi tatiller dikkate alınmaz.)"""
    if gun.weekday() >= 5:
        return False
    sonraki = gun + timedelta(days=1)
    while sonraki.weekday() >= 5:
        sonraki += timedelta(days=1)
    return sonraki.month != gun.month


# ------------------------------------------------------------ Google Sheets

def baglan():
    k, t = os.environ.get("GCP_SA_KEY"), os.environ.get("SPREADSHEET_ID")
    if not k or not t:
        raise RuntimeError("GCP_SA_KEY veya SPREADSHEET_ID tanımlı değil.")
    return gspread.service_account_from_dict(json.loads(k)).open_by_key(t)


def sayfa_getir(tablo, ad):
    try:
        return tablo.worksheet(ad)
    except gspread.WorksheetNotFound:
        return tablo.add_worksheet(title=ad, rows=1000, cols=26)


def tablo_yaz(ws, matris, ilk_satir, ilk_sutun=1):
    """Matrisi tek istekte yazar, artan eski satırları temizler, sütunları boyutlandırır."""
    if not matris:
        raise ValueError("Yazılacak veri yok.")
    son_satir = ilk_satir + len(matris) - 1
    sut = max(len(r) for r in matris)
    son_sutun = ilk_sutun + sut - 1
    if son_satir > ws.row_count or son_sutun > ws.col_count:
        ws.resize(rows=max(ws.row_count, son_satir + 50),
                  cols=max(ws.col_count, son_sutun))
    ws.update(values=matris, range_name=rowcol_to_a1(ilk_satir, ilk_sutun),
              value_input_option="RAW")
    if ws.row_count > son_satir:
        ws.batch_clear(["%s:%s" % (rowcol_to_a1(son_satir + 1, ilk_sutun),
                                   rowcol_to_a1(ws.row_count, son_sutun))])
    try:
        ws.columns_auto_resize(ilk_sutun - 1, son_sutun)
    except Exception as e:  # boyutlandırma başarısız olsa da veri yazıldı
        print("Otomatik boyutlandırma yapılamadı:", e)


def durum_yaz(tablo, kaynak, sonuc, kayit=0, basarili=False):
    """Durum sekmesinde yalnızca kendi satırını günceller."""
    ws = sayfa_getir(tablo, DURUM_SEKMESI)
    zaman = simdi().strftime("%Y-%m-%d %H:%M:%S")
    if ws.acell("A1").value != "kaynak":
        ws.update(values=[["kaynak", "son_deneme", "son_basarili", "kayit_sayisi", "sonuc"]],
                  range_name="A1", value_input_option="RAW")
    hucre = ws.find(kaynak, in_column=1)
    onceki = ws.row_values(hucre.row) if hucre else []
    son_basarili = zaman if basarili else (onceki[2] if len(onceki) > 2 else "")
    satir = [kaynak, zaman, son_basarili, kayit, str(sonuc)[:300]]
    if hucre:
        ws.update(values=[satir], range_name="A%d:E%d" % (hucre.row, hucre.row),
                  value_input_option="RAW")
    else:
        ws.append_row(satir, value_input_option="RAW")


# ------------------------------------------------------------ İndirme ve okuma

def indir(adres):
    """Dosyayı indirir. 404 ise None döner."""
    r = requests.get(adres, headers=UA, timeout=90)
    if r.status_code == 404:
        return None
    if r.status_code != 200:
        raise RuntimeError("İndirme hatası: HTTP %d (%s)" % (r.status_code, adres))
    return r.content


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


def _xlsx_satirlar(ham):
    from openpyxl import load_workbook
    ws = load_workbook(io.BytesIO(ham), read_only=True, data_only=True).active
    satirlar = []
    for r in ws.iter_rows(values_only=True):
        r = ["" if c is None else (c if isinstance(c, (int, float)) else str(c)) for c in r]
        if any(str(c).strip() for c in r):
            satirlar.append(r)
    return satirlar


def satirlari_oku(ham, ad=""):
    """CSV, XLSX ya da bunları içeren ZIP dosyasını satır listesine çevirir."""
    if ham[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(ham))
        adlar = [n for n in z.namelist() if not n.endswith("/")]
        if "xl/workbook.xml" in adlar:
            return _xlsx_satirlar(ham)
        print("ZIP içeriği:", ", ".join(adlar))
        return satirlari_oku(z.read(adlar[0]), adlar[0])
    if ham.lstrip()[:1] == b"<":
        raise ValueError("Dosya yerine bir web sayfası geldi.")
    metin = ham.decode(kodlama_bul(ham))
    satirlar = [s for s in metin.splitlines() if s.strip()]
    ayrac = ayrac_bul(satirlar)
    return [next(csv.reader([s], delimiter=ayrac)) for s in satirlar]


def ayrac_bul(satirlar):
    """En tutarlı ayracı seçer: her satırda aynı sayıda geçen ayraç (sayılardaki virgüller yanıltmaz)."""
    en_iyi, puan = ";", (0, 0)
    for a in ";\t,":
        sayilar = [x.count(a) for x in satirlar[:50] if x.count(a) > 0]
        if not sayilar:
            continue
        adet, sik = Counter(sayilar).most_common(1)[0][0], Counter(sayilar).most_common(1)[0][1]
        if (sik, adet) > puan:
            en_iyi, puan = a, (sik, adet)
    return en_iyi


def baslik_bul(rows, beklenen=None):
    """
    Başlık satırının indeksi. 'beklenen' (başlık adları) verilirse, beklenen başlıkların
    en çok geçtiği satır seçilir (üstteki başlık ya da dil satırları yanıltmaz).
    Verilmezse sütun sayısı en yaygın değere eşit olan ilk satır alınır.
    """
    if beklenen:
        anahtarlar = {anahtar(k) for k in beklenen}
        en_iyi, skor = None, 0
        for i, r in enumerate(rows[:50]):
            p = sum(1 for c in r if anahtar(str(c).split(" / ")[0]) in anahtarlar)
            if p > skor:
                en_iyi, skor = i, p
        if skor >= 2:
            return en_iyi
    doluluk = [sum(1 for c in r if str(c).strip()) for r in rows]
    adaylar = [d for d in doluluk[:50] if d >= 2]
    if not adaylar:
        raise ValueError("Tablo yapısı bulunamadı.")
    ortak = Counter(adaylar).most_common(1)[0][0]
    return next(i for i, d in enumerate(doluluk) if d == ortak)


def ornek_yaz(rows, satir=5, sutun=10):
    """Hata ayıklama: ilk satırların ilk sütunlarını günlüğe yazar."""
    for i, r in enumerate(rows[:satir]):
        print("  satır %d (%d hücre): %s" % (i, len(r), [str(c)[:24] for c in r[:sutun]]))


def sayi_cevir(v):
    """Sayı gibi görünen metni sayıya çevirir (Sheets'e sayı olarak yazılsın diye)."""
    if not isinstance(v, str):
        return v
    s = v.strip()
    if s == "":
        return ""
    if re.fullmatch(r"-?\d+", s):
        return s if (len(s) > 1 and s.lstrip("-").startswith("0")) or len(s) > 15 else int(s)
    if re.fullmatch(r"-?\d*\.\d+", s):
        return float(s)
    if re.fullmatch(r"-?\d+,\d+", s):
        return float(s.replace(",", "."))
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})+,\d+", s):
        return float(s.replace(".", "").replace(",", "."))
    if re.fullmatch(r"-?\d{1,3}(,\d{3})+(\.\d+)?", s):
        return float(s.replace(",", ""))
    return v


def kod_temizle(v):
    """THYAO.E gibi işlem kodlarının sonundaki .E, .F, .G uzantısını kaldırır."""
    return re.sub(r"\.[A-Z]$", "", str(v).strip())


def matris_olustur(baslik, veri, esleme):
    """
    esleme: {'WEB BASLIGI': 'GTS SUTUN HARFİ'}. Başlıklar anahtar() ile eşleştirilir
    ('Türkçe / English' biçiminde ise Türkçe kısım alınır). 'A' sütunu işlem kodudur:
    uzantısı kaldırılır, boş kodlu satırlar atlanır.
    Dönen: (matris, eksik_basliklar). Matris A sütunundan başlar.
    """
    hedef = {anahtar(k): a1_to_rowcol(h + "1")[1] for k, h in esleme.items()}
    sutun_sayisi = max(hedef.values())
    kaynak_idx = {}
    for j, b in enumerate(baslik):
        a = anahtar(str(b).split(" / ")[0])
        if a in hedef and a not in kaynak_idx:
            kaynak_idx[a] = j
    eksik = [k for k in esleme if anahtar(k) not in kaynak_idx]
    matris = []
    for r in veri:
        satir = [""] * sutun_sayisi
        for a, j in kaynak_idx.items():
            deger = r[j] if j < len(r) else ""
            h = hedef[a]
            satir[h - 1] = kod_temizle(deger) if h == 1 else sayi_cevir(deger)
        if str(satir[0]).strip():
            matris.append(satir)
    return matris, eksik
