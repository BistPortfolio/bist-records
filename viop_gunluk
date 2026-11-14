import os
import re
import json
import html
import time
import requests
import gspread

# ======================= AYARLAR =======================
URL = "https://bigpara.hurriyet.com.tr/viop-varant/viop-verileri/"
E_TABLO = "Borsaİstanbul"
SEKME = "ViopGünlük"
ILK_SATIR = 2                # 1. satır başlık, veri 2. satırdan başlar
EN_AZ_SATIR = 20             # bundan az satır gelirse sayfaya dokunulmaz
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
      "Accept-Language": "tr-TR,tr;q=0.9"}


def sayi(x):
    """'%-0,73' -> -0.73 ; '1.234,56' -> 1234.56 ; '-' veya boş -> ''"""
    x = x.strip()
    if x in ("", "-"):
        return ""
    try:
        return float(x.replace("%", "").replace(".", "").replace(",", "."))
    except ValueError:
        return x


def yon(yuzde):
    """% değerinden ok türet: artı ▲, eksi ▼, sıfır -"""
    if not isinstance(yuzde, (int, float)):
        return ""
    if yuzde > 0:
        return "▲"
    if yuzde < 0:
        return "▼"
    return "-"


def sayfayi_al():
    for deneme in range(3):
        try:
            r = requests.get(URL, headers=UA, timeout=30)
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.text
        except requests.RequestException as e:
            print(f"İstek hatası ({deneme + 1}/3): {e}")
            time.sleep(5)
    raise RuntimeError("Bigpara sayfasına ulaşılamadı.")


def tablodan_satirlar(sayfa_html):
    satirlar, goruldu = [], set()
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", sayfa_html, re.S | re.I):
        hucreler = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", c))).strip()
                    for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", tr, re.S | re.I)]
        idx = next((i for i, h in enumerate(hucreler) if h.startswith("F_")), -1)
        if idx == -1 or hucreler[idx] in goruldu:
            continue
        goruldu.add(hucreler[idx])

        sonraki = hucreler[idx + 1:]
        while sonraki and re.fullmatch(r"[\s▲▼△▽↑↓]*", sonraki[0]):   # ok simgesi sütununu atla
            sonraki.pop(0)
        sonraki += [""] * 7
        son, dun, yuzde, yuksek, dusuk, lot, tl = [sayi(x) for x in sonraki[:7]]

        # A Sembol | B Son | C Dün | D % | E Yön | F Düşük | G Yüksek | H LOT | I TL
        satirlar.append([hucreler[idx], son, dun, yuzde, yon(yuzde), dusuk, yuksek, lot, tl])
    return satirlar


def sheets_baglan():
    anahtar = os.environ.get("GCP_SA_KEY")                    # GitHub Secret
    if anahtar:
        return gspread.service_account_from_dict(json.loads(anahtar))
    return gspread.service_account(filename="anahtar.json")    # yerel çalıştırma


def yaz(satirlar):
    n = 9                                                      # A ... I
    tablo = sheets_baglan().open(E_TABLO)
    sayfa = tablo.worksheet(SEKME)

    gerekli = ILK_SATIR - 1 + len(satirlar)
    if sayfa.row_count < gerekli:
        sayfa.add_rows(gerekli - sayfa.row_count)
    if sayfa.col_count < n:
        sayfa.add_cols(n - sayfa.col_count)

    # Önce yaz, sonra artakalan eski satırları temizle (sayfa hiç boş kalmasın)
    sayfa.update(values=satirlar, range_name=f"A{ILK_SATIR}")
    ilk_artik = ILK_SATIR + len(satirlar)
    if sayfa.row_count >= ilk_artik:
        sayfa.batch_clear([f"A{ilk_artik}:I{sayfa.row_count}"])

    # Sütunları otomatik boyutlandır
    tablo.batch_update({"requests": [{"autoResizeDimensions": {"dimensions": {
        "sheetId": sayfa.id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": n}}}]})


def main():
    satirlar = tablodan_satirlar(sayfayi_al())
    print(f"{len(satirlar)} kontrat ayrıştırıldı.")
    if satirlar:
        print("İlk satır:", satirlar[0])
    if len(satirlar) < EN_AZ_SATIR:
        raise SystemExit("Beklenenden az satır geldi, sayfaya dokunulmadı.")
    yaz(satirlar)
    print("ViopGünlük güncellendi.")


if __name__ == "__main__":
    main()
