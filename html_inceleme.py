"""
HTML/ZIP inceleme aracı: ZIP içindeki HTML (ya da metin) dosyalarının yapısını
Borsaİstanbul tablosundaki "InceleHTML" sekmesine döker. Hangi dosyada hangi
tablo/başlık/değer olduğunu görmek içindir; veriyi işlemez.

Kullanım : python html_inceleme.py <adres> [filtre]
  adres : bir .zip adresi, ya da bir dizin adresi (dizinse en yeni klasörün en yeni zip'i alınır)
  filtre: isteğe bağlı, dizin seçiminde dosya adında geçmesi gereken metin (örn. TAKASEOD)
Ortam    : GCP_SA_KEY, SPREADSHEET_ID
"""
import io
import re
import sys
import zipfile
from html.parser import HTMLParser

import requests

import ortak

SEKME = "InceleHTML"
UA = {"User-Agent": "Mozilla/5.0 (BistPortfoy inceleme)"}
MAKS_BAYT = 80 * 1024 * 1024
MAKS_UYE = 10            # zip içinden en fazla kaç dosya incelenir
MAKS_TABLO_SATIR = 40    # her tablodan saklanan satır
OZET_TABLO = 80          # tablo özetinde listelenen en fazla tablo
DETAY_TABLO = 4          # ayrıntısı gösterilen ilk tablo sayısı
DETAY_SATIR = 12
DETAY_SUTUN = 12


# ------------------------------------------------------------ Kodlama

def metin_coz(ham):
    """(metin, açıklama) döndürür; çift kodlanmış (karma karışık) metni onarmaya çalışır."""
    if ham.startswith((b"\xff\xfe", b"\xfe\xff")):
        return ham.decode("utf-16"), "utf-16 (BOM)"
    if ham.startswith(b"\xef\xbb\xbf"):
        m, kod = ham.decode("utf-8-sig"), "utf-8 (BOM)"
    else:
        try:
            m, kod = ham.decode("utf-8"), "utf-8"
        except UnicodeDecodeError:
            return ham.decode("cp1254", errors="replace"), "cp1254 (utf-8 değil)"
    # UTF-8 metin yanlışlıkla tekrar çözülmüşse "Ã¼", "Ä±" gibi diziler görülür
    if len(re.findall(r"[ÃÄÅ]", m)) > 20:
        for ara in ("cp1252", "latin-1"):
            try:
                onarilmis = m.encode(ara).decode("utf-8")
                return onarilmis, kod + " + çift kodlama onarıldı (" + ara + ")"
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass
        return m, kod + " (çift kodlama belirtisi var, onarılamadı)"
    return m, kod


# ------------------------------------------------------------ HTML çözümleme

class Cozucu(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.baslik = ""
        self.tablolar = []
        self.metin = []
        self.pre_sayisi = 0
        self._baslikta = False
        self._yigin = []
        self._satir = None
        self._hucre = None
        self._pre = 0
        self._pre_tampon = []

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self._baslikta = True
        elif tag == "table":
            self.tablolar.append({"satir_sayisi": 0, "sutun_max": 0, "satirlar": []})
            self._yigin.append(len(self.tablolar) - 1)
        elif tag == "tr" and self._yigin:
            self._satir = []
        elif tag in ("td", "th") and self._yigin and self._satir is not None:
            self._hucre = []
        elif tag == "pre":
            self._pre += 1
            self.pre_sayisi += 1
        elif tag == "br" and self._hucre is not None:
            self._hucre.append(" ")

    def handle_endtag(self, tag):
        if tag == "title":
            self._baslikta = False
        elif tag in ("td", "th") and self._hucre is not None and self._satir is not None:
            self._satir.append(" ".join("".join(self._hucre).split()))
            self._hucre = None
        elif tag == "tr" and self._satir is not None and self._yigin:
            t = self.tablolar[self._yigin[-1]]
            t["satir_sayisi"] += 1
            t["sutun_max"] = max(t["sutun_max"], len(self._satir))
            if len(t["satirlar"]) < MAKS_TABLO_SATIR:
                t["satirlar"].append(self._satir)
            self._satir = None
        elif tag == "table" and self._yigin:
            self._yigin.pop()
        elif tag == "pre" and self._pre:
            self._pre -= 1
            satirlar = [s.rstrip() for s in "".join(self._pre_tampon).splitlines() if s.strip()]
            self._pre_tampon = []
            if len(self.metin) < 300:
                self.metin.extend(satirlar[:200])

    def handle_data(self, data):
        if self._baslikta:
            self.baslik += data
        elif self._hucre is not None:
            self._hucre.append(data)
        elif self._pre:
            self._pre_tampon.append(data)
        else:
            s = " ".join(data.split())
            if s and len(self.metin) < 300:
                self.metin.append(s)


def kes(x, n=180):
    x = str(x)
    return x if len(x) <= n else x[:n] + "…"


def uye_incele(ad, ham):
    """Bir dosyanın inceleme satırlarını döndürür."""
    satirlar = []
    metin, kod = metin_coz(ham)
    meta = re.search(r"charset\s*=\s*[\"']?([\w\-]+)", metin[:3000], re.I)
    html_mi = ad.lower().endswith((".htm", ".html")) or "<html" in metin[:2000].lower() \
        or "<table" in metin[:20000].lower()
    satirlar.append(["DOSYA", ad, "boyut (bayt)", len(ham), "çözülen kodlama", kod,
                     "meta charset", meta.group(1) if meta else "-"])
    if not html_mi:
        satirlar.append(["Metin dosyası, ilk satırlar:"])
        for s in [x for x in metin.splitlines() if x.strip()][:60]:
            satirlar.append(["", kes(s)])
        return satirlar

    c = Cozucu()
    c.feed(metin)
    c.close()
    satirlar.append(["Başlık (title)", kes(" ".join(c.baslik.split())), "tablo sayısı", len(c.tablolar),
                     "pre bloğu", c.pre_sayisi, "metin parçası", len(c.metin)])
    if c.tablolar:
        satirlar.append([])
        satirlar.append(["TABLO ÖZETİ", "No", "Satır", "Sütun", "İlk satırın ilk hücreleri"])
        for i, t in enumerate(c.tablolar[:OZET_TABLO], 1):
            ilk = t["satirlar"][0][:6] if t["satirlar"] else []
            satirlar.append(["", i, t["satir_sayisi"], t["sutun_max"]] + [kes(x, 60) for x in ilk])
        if len(c.tablolar) > OZET_TABLO:
            satirlar.append(["", "… ve %d tablo daha" % (len(c.tablolar) - OZET_TABLO)])
        # ayrıntı: satır sayısı en çok olan ve ilk tablolar
        secili = list(range(min(DETAY_TABLO, len(c.tablolar))))
        en_buyuk = max(range(len(c.tablolar)), key=lambda i: c.tablolar[i]["satir_sayisi"])
        if en_buyuk not in secili:
            secili.append(en_buyuk)
        for i in secili:
            t = c.tablolar[i]
            satirlar.append([])
            satirlar.append(["TABLO %d" % (i + 1), "toplam satır", t["satir_sayisi"], "sütun", t["sutun_max"]])
            for r in t["satirlar"][:DETAY_SATIR]:
                satirlar.append([""] + [kes(x, 80) for x in r[:DETAY_SUTUN]])
    if c.metin and (len(c.tablolar) < 2 or c.pre_sayisi):
        satirlar.append([])
        satirlar.append(["METİN ÖRNEĞİ (ilk satırlar)"])
        for s in c.metin[:80]:
            satirlar.append(["", kes(s, 200)])
    return satirlar


# ------------------------------------------------------------ İndirme

def liste_baglantilari(url, metin):
    adresler = re.findall(r'href\s*=\s*["\']([^"\']+)["\']', metin, re.I)   # IIS listeleri HREF büyük harfle yazar
    sonuc = []
    for a in adresler:
        tam = requests.compat.urljoin(url, a)
        if tam.startswith(url) and tam != url:
            sonuc.append(tam)
    return sonuc


def zip_adresi_bul(url, filtre="", derinlik=0):
    """Dizin adresiyse en yeni klasöre inip en yeni zip'i bulur."""
    if url.lower().endswith(".zip") or not url.endswith("/"):
        return url
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    baglantilar = sorted(set(liste_baglantilari(url, r.content.decode("utf-8", "replace"))))
    print("Dizin:", url, "| bulunan bağlantı:", len(baglantilar))
    zipler = [b for b in baglantilar if b.lower().endswith(".zip") and filtre.lower() in b.lower()]
    if zipler:
        return zipler[-1]
    klasorler = [b for b in baglantilar if b.endswith("/")]
    if klasorler and derinlik < 2:
        return zip_adresi_bul(klasorler[-1], filtre, derinlik + 1)
    raise RuntimeError("Dizinde uygun zip bulunamadı: " + url)


def main():
    if len(sys.argv) < 2 or not sys.argv[1].startswith("http"):
        print("Kullanım: python html_inceleme.py <adres> [filtre]")
        return 2
    adres = sys.argv[1]
    filtre = sys.argv[2] if len(sys.argv) > 2 else ""
    zip_url = zip_adresi_bul(adres, filtre)
    print("İncelenen dosya:", zip_url)
    r = requests.get(zip_url, headers=UA, timeout=180)
    print("Durum kodu:", r.status_code)
    if r.status_code != 200:
        raise SystemExit(1)
    if len(r.content) > MAKS_BAYT:
        raise SystemExit("Dosya çok büyük.")

    satirlar = [["Kaynak", zip_url], ["İndirilen boyut (bayt)", len(r.content)]]
    ham = r.content
    if ham[:2] == b"PK":
        z = zipfile.ZipFile(io.BytesIO(ham))
        adlar = [n for n in z.namelist() if not n.endswith("/")]
        satirlar.append(["Zip içeriği", "%d dosya" % len(adlar)])
        for n in adlar[:30]:
            satirlar.append(["", n, z.getinfo(n).file_size])
        for n in adlar[:MAKS_UYE]:
            satirlar.append([])
            try:
                satirlar += uye_incele(n, z.read(n))
            except Exception as e:
                satirlar.append(["DOSYA", n, "HATA", kes(e)])
    else:
        satirlar.append([])
        satirlar += uye_incele(zip_url.rsplit("/", 1)[-1], ham)

    tablo = ortak.baglan()
    ws = ortak.sayfa_getir(tablo, SEKME)
    en_genis = max((len(s) for s in satirlar), default=1)
    ws.clear()
    if len(satirlar) + 5 > ws.row_count or en_genis > ws.col_count:
        ws.resize(rows=max(ws.row_count, len(satirlar) + 20), cols=max(ws.col_count, en_genis))
    ws.update(values=satirlar, range_name="A1", value_input_option="RAW")
    print("'%s' sekmesine %d satır yazıldı." % (SEKME, len(satirlar)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
