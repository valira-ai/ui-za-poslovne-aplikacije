# Osnove umetne inteligence in strojnega učenja za poslovne aplikacije

**GZS, 1. izvedba, november 2026** — gradivo za delavnico: predstavitve (PDF), Jupyter zvezki, pomožne funkcije in navodila za namestitev.

**Vsebina**

1. [Urnik](#urnik)
2. [Pred delavnico: namestitev](#pred-delavnico-namestitev)
3. [Na delavnici: zagon](#na-delavnici-zagon)
4. [Predstavitve](#predstavitve)
5. [Zvezki in vaje](#zvezki-in-vaje)
6. [Google Colab (rezerva)](#google-colab-rezerva)
7. [Pogoste težave](#pogoste-težave)
8. [Podatki](#podatki)

---

## Urnik

| Modul | Datum               | Vsebina                                                          |
| ----- | ------------------- | ---------------------------------------------------------------- |
| 1     | sreda, 11. 11. 2026 | Uvod v podatkovno znanost in eksplorativna analiza podatkov      |
| 2     | sreda, 18. 11. 2026 | Uvod v strojno učenje in nadzorovano učenje                    |
| 3     | sreda, 25. 11. 2026 | Evalvacija modelov, pomembnost značilk in nenadzorovano učenje |

Vsak dan od 9:00 do 16:30 (zbor udeležencev ob 8:30).

---

## Pred delavnico: namestitev

Prosimo, namestitev opravite **pred prvo delavnico** (≈ 10 minut). Potrebujete internetno povezavo in približno 1 GB prostora na disku.
Če namestitev ne uspe, lahko delate v [Google Colabu](#google-colab-rezerva).

### 1. Namestite Python

- Potrebujete **Python 3.10 ali novejši**. Preverite v terminalu: `python --version` (Windows: `py --version`).
- Če ga nimate, ga prenesite s [python.org/downloads](https://www.python.org/downloads/).
  **Windows:** pri namestitvi obkljukajte **"Add python.exe to PATH"**.

### 2. Prenesite gradivo

- Na vrhu te strani kliknite zeleni gumb **Code → Download ZIP** in ZIP razširite (npr. na Namizje).
  Mapa se imenuje `ui-za-poslovne-aplikacije-main`.
- Ali, če uporabljate git:
  ```bash
  git clone https://github.com/valira-ai/ui-za-poslovne-aplikacije.git
  ```

### 3. Ustvarite okolje in namestite knjižnice

Odprite terminal **v mapi z gradivom** (Windows: v mapi kliknite v naslovno vrstico, vpišite `cmd` in pritisnite Enter).

**Windows (cmd):**

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Namestitev traja nekaj minut.

### 4. Preverite, ali vse deluje

1. V istem terminalu (na začetku vrstice piše `(.venv)`) zaženite:
   ```bash
   jupyter lab
   ```
2. V brskalniku odprite `01_Uvod_v_podatkovno_znanost/notebooks/01_prvi_stik_s_podatki/B_prvi_stik_s_podatki.ipynb`.
3. Zaženite **prvi dve celici s kodo** (izberite celico in pritisnite **Shift + Enter**):
   - prva izpiše `Gradivo je v: ...`,
   - druga ob prvem zagonu prenese podatke s Kaggla (~1 minuta) in izpiše `Podatki so pripravljeni v: ...`.

Če vidite oba izpisa, je vse nared. Podatki se prenesejo samo enkrat — na delavnici bodo že na vašem računalniku.

---

## Na delavnici: zagon

Vsakič, ko začnete delo, odprite terminal v mapi z gradivom in zaženite:

| Windows (cmd)              | macOS / Linux                 |
| -------------------------- | ----------------------------- |
| `.venv\Scripts\activate` | `source .venv/bin/activate` |
| `jupyter lab`            | `jupyter lab`               |

Nato odprite zvezek za vajo (glej spodaj) in celice zaganjajte po vrsti, od zgoraj navzdol.

---

## Predstavitve

| Sklop | Predstavitev |
| --- | --- |
| Uvod v podatkovno znanost | [Uvod v podatkovno znanost (PDF)](01_Uvod_v_podatkovno_znanost/Uvod%20v%20podatkovno%20znanost.pdf) |
| Eksplorativna analiza podatkov | [Eksplorativna analiza podatkov (PDF)](02_Eksplorativna_analiza_podatkov/Eksplorativna%20analiza%20podatkov.pdf) |

---

## Zvezki in vaje

Vsak sklop ima dva zvezka:

- **Zvezki z začetnico `A` — prikaz.** Poganja jih predavatelj, vi spremljate razlago in rezultate.
- **Zvezki z začetnico `B` — vaja.** Koda je pripravljena; sami jo izvajate, izbirate predlagane stolpce in odgovarjate na vprašanja.
  Po spremembi izbranega stolpca ponovno izvedite tudi naslednje celice, ki uporabljajo njegove rezultate.

Pri opisni statistiki, odnosih med spremenljivkami, vizualizaciji, normalizaciji in oblikovanju značilk zvezki A uporabljajo podatke spletne trgovine **Olist**, zvezki B pa podatke **Telekoma**.
Pri manjkajočih vrednostih in osamelcih sta primera zamenjana: prikaz A je na Telekomu, vaja B pa na Olistu.
Na začetku zvezka so navodila, nastavitev okolja in nalaganje podatkov. Nato nadaljujte po vrsti.

### Modul 1 — sreda, 11. 11. 2026

| Sklop | Prikaz | Vaja | Google Colab |
| --- | --- | --- | --- |
| Prvi stik s podatki | [A](01_Uvod_v_podatkovno_znanost/notebooks/01_prvi_stik_s_podatki/A_prvi_stik_s_podatki.ipynb) | [B](01_Uvod_v_podatkovno_znanost/notebooks/01_prvi_stik_s_podatki/B_prvi_stik_s_podatki.ipynb) | [A](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/01_Uvod_v_podatkovno_znanost/notebooks/01_prvi_stik_s_podatki/A_prvi_stik_s_podatki.ipynb) · [B](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/01_Uvod_v_podatkovno_znanost/notebooks/01_prvi_stik_s_podatki/B_prvi_stik_s_podatki.ipynb) |
| Opisna statistika: ena spremenljivka | [A1](01_Uvod_v_podatkovno_znanost/notebooks/02_opisna_statistika/A1-Opisna-statistika.ipynb) | [B1](01_Uvod_v_podatkovno_znanost/notebooks/02_opisna_statistika/B1-Opisna-statistika.ipynb) | [A1](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/01_Uvod_v_podatkovno_znanost/notebooks/02_opisna_statistika/A1-Opisna-statistika.ipynb) · [B1](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/01_Uvod_v_podatkovno_znanost/notebooks/02_opisna_statistika/B1-Opisna-statistika.ipynb) |
| Odnosi med spremenljivkami | [A2](01_Uvod_v_podatkovno_znanost/notebooks/02_opisna_statistika/A2-Odnosi-med-spremenljivkami.ipynb) | [B2](01_Uvod_v_podatkovno_znanost/notebooks/02_opisna_statistika/B2-Odnosi-med-spremenljivkami.ipynb) | [A2](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/01_Uvod_v_podatkovno_znanost/notebooks/02_opisna_statistika/A2-Odnosi-med-spremenljivkami.ipynb) · [B2](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/01_Uvod_v_podatkovno_znanost/notebooks/02_opisna_statistika/B2-Odnosi-med-spremenljivkami.ipynb) |
| Vizualizacija podatkov | [A](01_Uvod_v_podatkovno_znanost/notebooks/03_vizualizacija/A_vizualizacija.ipynb) | [B](01_Uvod_v_podatkovno_znanost/notebooks/03_vizualizacija/B_vizualizacija.ipynb) | [A](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/01_Uvod_v_podatkovno_znanost/notebooks/03_vizualizacija/A_vizualizacija.ipynb) · [B](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/01_Uvod_v_podatkovno_znanost/notebooks/03_vizualizacija/B_vizualizacija.ipynb) |
| Manjkajoče vrednosti | [A](02_Eksplorativna_analiza_podatkov/notebooks/01_manjkajoce_vrednosti/A_manjkajoce_vrednosti.ipynb) | [B](02_Eksplorativna_analiza_podatkov/notebooks/01_manjkajoce_vrednosti/B_manjkajoce_vrednosti.ipynb) | [A](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/02_Eksplorativna_analiza_podatkov/notebooks/01_manjkajoce_vrednosti/A_manjkajoce_vrednosti.ipynb) · [B](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/02_Eksplorativna_analiza_podatkov/notebooks/01_manjkajoce_vrednosti/B_manjkajoce_vrednosti.ipynb) |
| Osamelci | [A](02_Eksplorativna_analiza_podatkov/notebooks/02_osamelci/A_osamelci.ipynb) | [B](02_Eksplorativna_analiza_podatkov/notebooks/02_osamelci/B_osamelci.ipynb) | [A](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/02_Eksplorativna_analiza_podatkov/notebooks/02_osamelci/A_osamelci.ipynb) · [B](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/02_Eksplorativna_analiza_podatkov/notebooks/02_osamelci/B_osamelci.ipynb) |
| Normalizacija in standardizacija | [A](02_Eksplorativna_analiza_podatkov/notebooks/03_normalizacija_in_standardizacija/A-Normalizacija-in-standardizacija.ipynb) | [B](02_Eksplorativna_analiza_podatkov/notebooks/03_normalizacija_in_standardizacija/B-Normalizacija-in-standardizacija.ipynb) | [A](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/02_Eksplorativna_analiza_podatkov/notebooks/03_normalizacija_in_standardizacija/A-Normalizacija-in-standardizacija.ipynb) · [B](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/02_Eksplorativna_analiza_podatkov/notebooks/03_normalizacija_in_standardizacija/B-Normalizacija-in-standardizacija.ipynb) |
| Oblikovanje značilk | [A](02_Eksplorativna_analiza_podatkov/notebooks/04_oblikovanje_znacilk/A-Oblikovanje-znacilk.ipynb) | [B](02_Eksplorativna_analiza_podatkov/notebooks/04_oblikovanje_znacilk/B-Oblikovanje-znacilk.ipynb) | [A](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/02_Eksplorativna_analiza_podatkov/notebooks/04_oblikovanje_znacilk/A-Oblikovanje-znacilk.ipynb) · [B](https://colab.research.google.com/github/valira-ai/ui-za-poslovne-aplikacije/blob/main/02_Eksplorativna_analiza_podatkov/notebooks/04_oblikovanje_znacilk/B-Oblikovanje-znacilk.ipynb) |

### Kaj je v repozitoriju

```
ui-za-poslovne-aplikacije/
├── README.md                                 ta navodila
├── requirements.txt                          seznam knjižnic za namestitev
├── utils/
│   ├── __init__.py
│   └── orodja.py                             prenos podatkov in funkcije, ki jih zvezki uporabljajo večkrat
├── data/                                     podatki (nastanejo ob prvem zagonu)
├── 01_Uvod_v_podatkovno_znanost/
│   ├── notebooks/
│   │   ├── 01_prvi_stik_s_podatki/
│   │   ├── 02_opisna_statistika/              opisna statistika in odnosi med spremenljivkami
│   │   └── 03_vizualizacija/
│   └── Uvod v podatkovno znanost.pdf          predstavitev
├── 02_Eksplorativna_analiza_podatkov/
│   ├── notebooks/
│   │   ├── 01_manjkajoce_vrednosti/
│   │   ├── 02_osamelci/
│   │   ├── 03_normalizacija_in_standardizacija/
│   │   └── 04_oblikovanje_znacilk/
│   └── Eksplorativna analiza podatkov.pdf     predstavitev
├── 03_Uvod_v_strojno_ucenje/                 trenutno prazno
├── 04_Nadzorovano_ucenje_v_praksi/
└── 05_Nenadzorovano_ucenje_v_praksi/
```

V `utils/orodja.py` so skupni prenos podatkov in pomožne funkcije za grafe. Izračuni in razlage za posamezne sklope so v zvezkih.

---

## Google Colab (rezerva)

Če lokalna namestitev ne deluje (npr. službeni računalnik brez pravic za namestitev), lahko delate v Google Colabu.
Na računalnik ni treba namestiti Pythona; potrebujete Google račun.

1. V stolpcu **Google Colab** v tabeli [Zvezki in vaje](#zvezki-in-vaje) izberite povezavo A ali B in se prijavite z Google računom.
2. Če Colab opozori, da zvezek ni od Googla, izberite **"Run anyway"**.
3. Zaženite nastavitvene celice na začetku zvezka in nato nadaljujte po vrsti. Te celice prenesejo gradivo, namestijo potrebne knjižnice in pripravijo podatke.

Dobro je vedeti:

- Colab uporablja začasno okolje. Ob novem okolju se namestitev knjižnic in prenos podatkov ponovita.
- Spremembe se ne shranijo same. Če želite obdržati svojo verzijo: **File → Save a copy in Drive**.

---

## Pogoste težave

| Težava                                                                    | Rešitev                                                                                                                            |
| -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `python` / `py` ni prepoznan                                           | Python ni v PATH. Ponovno zaženite namestitev in obkljukajte "Add python.exe to PATH".                                             |
| PowerShell ne dovoli `activate`                                          | Uporabite `cmd` namesto PowerShella ali najprej zaženite `Set-ExecutionPolicy -Scope Process RemoteSigned`.                    |
| `pip install` ne uspe (službeni računalnik, proxy)                     | Uporabite [Google Colab](#google-colab-rezerva).                                                                                     |
| `ModuleNotFoundError: No module named 'plotnine'` (ali druga knjižnica) | Okolje ni aktivirano. Na začetku vrstice v terminalu mora pisati `(.venv)`. Aktivirajte ga in ponovno zaženite `jupyter lab`. |
| `ModuleNotFoundError: No module named 'utils'`                          | Najprej zaženite nastavitveno celico zvezka. Mapa `utils/` mora ostati v glavni mapi gradiva.                                        |
| Prenos podatkov ne uspe                                                    | Preverite internetno povezavo in celico zaženite ponovno. Če ne gre, se obrnite na predavatelja.                                  |

---

## Podatki

Skupna funkcija iz `utils/orodja.py` pripravi podatke za zvezke:

```python
from utils.orodja import poskrbi_za_podatke
DATA = poskrbi_za_podatke()
```

Funkcija vrne mapo `data/` glede na lokacijo repozitorija, zato deluje tudi iz vseh podmap zvezkov.
Manjkajoče datoteke pripravi iz že lokalnih izvirnih podatkov ali jih prenese s Kaggla.
Ob ponovnem zagonu pripravljene datoteke ohrani; pripravi tudi posamezne manjkajoče datoteke predpomnilnika.
Ročno jih lahko prenesete tudi v terminalu iz glavne mape projekta: `python -m utils.orodja`.

- `DATA / "telekom.csv"`: izbor 22 stolpcev s slovenskimi imeni za uvod in vizualizacijo.
- `DATA / "telekom_slovar.csv"`: preslikava imen in opis stolpcev tega izbora.
- `DATA / "telekom_izvirni.csv"`: polna kopija izvirnega CSV-ja s 100 stolpci za nadaljnje vaje, ki potrebujejo dodatne agregate in kode.
- `DATA / "trgovina"`: osem izvirnih tabel Olista; vsaka vaja iz njih pripravi svojo zahtevano raven podatkov.

Vrednosti, manjkajoči podatki in napake ostanejo ohranjeni. Skupni vhod ne izvaja čiščenja ali agregiranja.
Pripravljeni CSV-ji niso del Gita. Knjižnice za lokalno namestitev so navedene v `requirements.txt`. V Colabu potrebne knjižnice namestijo nastavitvene celice na začetku posameznega zvezka.

Vira: [Telecom customer churn](https://www.kaggle.com/datasets/abhinav89/telecom-customer) in
[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (CC BY-NC-SA 4.0).

Koda v tem repozitoriju je objavljena pod licenco MIT (glej `LICENSE`). Za podatke veljajo licence njihovih virov.
