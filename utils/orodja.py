"""Pomožne funkcije za Akademijo UI (GZS).

Pravilo: vsako kodo najprej pokažemo v celoti v zvezku. Ko jo potrebujemo
ponovno, jo pokličemo kot funkcijo iz te datoteke. Pri vsaki funkciji piše,
v katerem zvezku je njena koda prvič prikazana.

Podatki:
    data/telekom.csv          izbor 22 stolpcev iz "Telecom customer churn" (abhinav89)
    data/telekom_slovar.csv   slovar stolpcev (slovensko ime, izvirno ime, opis)
    data/telekom_izvirni.csv  vseh 100 stolpcev z izvirnimi imeni za nadaljnje sklope
    data/trgovina/*.csv       tabele spletne trgovine Olist (brez geolokacije)

Vrednosti v podatkih NE spreminjamo — samo izberemo in preimenujemo stolpce.
Napake v podatkih so namerno ohranjene, ker jih na delavnici iščemo.

Zagon iz glavne mape projekta (prenese podatke):  python -m utils.orodja
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import to_rgb
from plotnine import (aes, after_stat, coord_equal, coord_flip, element_blank, element_text,
                      geom_boxplot, geom_col, geom_density, geom_histogram, geom_line, geom_point, geom_text,
                      geom_tile, ggplot, facet_wrap, labs, scale_color_manual, scale_fill_gradient2,
                      scale_fill_manual, scale_x_discrete, scale_x_log10, scale_y_discrete, scale_y_log10, theme,
                      theme_minimal, theme_set, theme_void)
from plotnine.exceptions import PlotnineWarning
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, plot_tree

KOREN = Path(__file__).resolve().parents[1]
DATA = KOREN / "data"

# ---------------------------------------------------------------------------
# Podatki — prvič prikazano v: A_prvi_stik_s_podatki (uvod)
# ---------------------------------------------------------------------------

TELEKOM_KAGGLE = "abhinav89/telecom-customer"
TRGOVINA_KAGGLE = "olistbr/brazilian-ecommerce"

# slovensko ime -> (izvirno ime, opis)
TELEKOM_STOLPCI: dict[str, tuple[str, str]] = {
    "id_stranke": ("Customer_ID", "Identifikator stranke"),
    "odhod": ("churn", "Ali je stranka odšla (1) ali ostala (0)"),
    "mesecev_narocnine": ("months", "Število mesecev, odkar je stranka naročnik"),
    "povp_mesecni_prihodek": ("rev_Mean", "Povprečni mesečni prihodek od stranke (USD)"),
    "povp_mesecna_narocnina": ("totmrc_Mean", "Povprečni fiksni mesečni strošek naročnine (USD)"),
    "povp_minute": ("mou_Mean", "Povprečno število porabljenih minut na mesec"),
    "povp_minute_6m": ("avg6mou", "Povprečne minute v zadnjih 6 mesecih"),
    "sprememba_minut": ("change_mou", "Sprememba minut glede na pretekle 3 mesece (%)"),
    "povp_minute_prekoracitev": ("ovrmou_Mean", "Povprečne minute nad vključenim paketom"),
    "povp_gostovanje": ("roam_Mean", "Povprečno število klicev v gostovanju"),
    "povp_klici_podpora": ("custcare_Mean", "Povprečno število klicev na podporo na mesec"),
    "povp_prekinjeni_klici": ("drop_vce_Mean", "Povprečno število prekinjenih klicev na mesec"),
    "stevilo_narocnin": ("uniqsubs", "Število naročnin v gospodinjstvu"),
    "stevilo_telefonov": ("phones", "Število telefonov, ki jih je stranka imela"),
    "dni_z_napravo": ("eqpdays", "Število dni, odkar ima stranka trenutno napravo"),
    "cena_naprave": ("hnd_price", "Cena trenutne naprave (USD)"),
    "splet_na_napravi": ("hnd_webcap", "Ali naprava podpira splet (WCMB, WC, UNKW = neznano)"),
    "dualband": ("dualband", "Ali je naprava dvopasovna (Y, N, T, U = neznano)"),
    "regija": ("area", "Geografsko območje"),
    "zakonski_stan": ("marital", "Zakonski stan (M, S, A, B, U = neznano)"),
    "dohodek_razred": ("income", "Razred dohodka gospodinjstva (1 = najnižji, 9 = najvišji)"),
    "stevilo_avtomobilov": ("numbcars", "Število avtomobilov v gospodinjstvu"),
}

TRGOVINA_TABELE = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def _prenesi(ime: str) -> Path:
    import kagglehub

    print(f"Prenašam {ime} s Kaggla ...")
    return Path(kagglehub.dataset_download(ime))


def _pripravi_telekom() -> None:
    celotni = DATA / "telekom_izvirni.csv"
    izbor = DATA / "telekom.csv"
    slovar_pot = DATA / "telekom_slovar.csv"

    if not celotni.is_file() or not izbor.is_file():
        # Ponovno uporabimo tudi podatke, prenesene pred uvedbo skupnega vhoda.
        lokalni = DATA / "telecom-customer" / "Telecom_customer churn.csv"
        if celotni.is_file():
            izvor = celotni
        elif lokalni.is_file():
            izvor = lokalni
        else:
            izvor = _prenesi(TELEKOM_KAGGLE) / "Telecom_customer churn.csv"

        if not celotni.is_file():
            shutil.copyfile(izvor, celotni)
        if not izbor.is_file():
            nova_imena = {izvirno: slovensko for slovensko, (izvirno, _) in TELEKOM_STOLPCI.items()}
            df = pd.read_csv(celotni, usecols=list(nova_imena)).rename(columns=nova_imena)
            df = df[list(TELEKOM_STOLPCI)]
            df["id_stranke"] = df["id_stranke"].astype("int64")
            df.to_csv(izbor, index=False)

    if not slovar_pot.is_file():
        slovar = pd.DataFrame(
            [(k, v[0], v[1]) for k, v in TELEKOM_STOLPCI.items()],
            columns=["stolpec", "izvirno_ime", "opis"],
        )
        slovar.to_csv(slovar_pot, index=False)


def _pripravi_trgovino() -> None:
    lokalni = DATA / "brazilian-ecommerce"
    if all((lokalni / ime).is_file() for ime in TRGOVINA_TABELE):
        izvor = lokalni
    else:
        izvor = _prenesi(TRGOVINA_KAGGLE)
    cilj = DATA / "trgovina"
    cilj.mkdir(parents=True, exist_ok=True)
    for ime in TRGOVINA_TABELE:
        if not (cilj / ime).is_file():
            shutil.copyfile(izvor / ime, cilj / ime)


def poskrbi_za_podatke() -> Path:
    """Skupni vhod za vse zvezke: pripravi manjkajoče datoteke in vrne DATA.

    Že pripravljene datoteke ostanejo nespremenjene. Če so izvirni podatki že
    lokalno, omrežja ne potrebujemo; sicer uporabimo Kaggle in njegov predpomnilnik.
    """
    DATA.mkdir(parents=True, exist_ok=True)
    if not all((DATA / ime).is_file() for ime in (
        "telekom.csv", "telekom_slovar.csv", "telekom_izvirni.csv"
    )):
        _pripravi_telekom()
    if not all((DATA / "trgovina" / t).is_file() for t in TRGOVINA_TABELE):
        _pripravi_trgovino()
    print(f"Podatki so pripravljeni v: {DATA}")
    return DATA


# ---------------------------------------------------------------------------
# Opis stolpca — prvič prikazano v: B_prvi_stik_s_podatki (B2)
# ---------------------------------------------------------------------------

def opis_stolpca(df, stolpec):
    s = df[stolpec]
    print("Tip v Pandasu:      ", s.dtype)
    print("Različnih vrednosti:", s.nunique())
    print("Manjkajočih (NaN):  ", s.isna().sum())
    print(s.value_counts(dropna=False).head(8).to_string())


# ---------------------------------------------------------------------------
# Slog grafov in tabela naročil — prvič prikazano v: A_vizualizacija (uvod)
# ---------------------------------------------------------------------------

# Barve, ki jih ločijo tudi barvno slepi.
MODRA, ORANZNA, ZELENA, SIVA = "#2a78d6", "#eb6834", "#1baf7a", "#9a9890"
BARVE_ODHOD = [MODRA, ORANZNA]          # 0 = ostal (modra), 1 = odšel (oranžna)


def nastavi_slog():
    """Enoten videz vseh grafov: bela podlaga, svetla mreža, krepak naslov."""
    theme_set(theme_minimal(base_size=11)
              + theme(figure_size=(8, 4.5),
                      plot_title=element_text(weight="bold", size=13),
                      panel_grid_minor=element_blank()))
    warnings.filterwarnings("ignore", category=PlotnineWarning)   # opozorila "Removed N rows ..."
    warnings.filterwarnings("ignore", message="divide by zero")    # log(0) na logaritemski osi


def pripravi_narocila(data=DATA):
    """Ena vrstica = eno naročilo spletne trgovine (združi več tabel Olist)."""
    d = Path(data) / "trgovina"
    narocila = pd.read_csv(d / "olist_orders_dataset.csv", parse_dates=[
        "order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"])
    postavke = pd.read_csv(d / "olist_order_items_dataset.csv")
    izdelki = pd.read_csv(d / "olist_products_dataset.csv")
    prevod = pd.read_csv(d / "product_category_name_translation.csv")
    placila = pd.read_csv(d / "olist_order_payments_dataset.csv")
    ocene = pd.read_csv(d / "olist_order_reviews_dataset.csv")
    stranke = pd.read_csv(d / "olist_customers_dataset.csv")

    # 1. postavke + izdelki (kategorija v angleščini, teža)
    izdelki = izdelki.merge(prevod, on="product_category_name", how="left")
    postavke = postavke.merge(izdelki[["product_id", "product_category_name_english", "product_weight_g"]],
                              on="product_id", how="left")
    # 2. postavke seštejemo po naročilu
    po_narocilu = postavke.groupby("order_id").agg(
        vrednost=("price", "sum"), postnina=("freight_value", "sum"), st_postavk=("order_item_id", "count"),
        teza_g=("product_weight_g", "sum"), kategorija=("product_category_name_english", "first")).reset_index()
    # 3. glavno plačilo naročila (največji znesek) in ocena kupca
    glavno_placilo = (placila.sort_values("payment_value", ascending=False).drop_duplicates("order_id")
                      .rename(columns={"payment_type": "nacin_placila", "payment_installments": "st_obrokov"})
                      [["order_id", "nacin_placila", "st_obrokov"]])
    ocena = (ocene.drop_duplicates("order_id")[["order_id", "review_score"]]
             .rename(columns={"review_score": "ocena"}))
    # 4. vse skupaj
    narocila = (narocila
                .merge(stranke[["customer_id", "customer_state"]], on="customer_id", how="left")
                .merge(po_narocilu, on="order_id", how="left")
                .merge(glavno_placilo, on="order_id", how="left")
                .merge(ocena, on="order_id", how="left"))
    narocila["dni_dostave"] = (narocila["order_delivered_customer_date"]
                               - narocila["order_purchase_timestamp"]).dt.days
    narocila["zamuda_dni"] = (narocila["order_delivered_customer_date"]
                              - narocila["order_estimated_delivery_date"]).dt.days
    narocila["ocena"] = narocila["ocena"].astype("Int64")
    narocila = narocila.rename(columns={"order_status": "status", "order_purchase_timestamp": "datum_nakupa",
                                        "customer_state": "zvezna_drzava"})
    return narocila[["order_id", "datum_nakupa", "status", "zvezna_drzava", "kategorija", "st_postavk",
                     "vrednost", "postnina", "teza_g", "nacin_placila", "st_obrokov",
                     "dni_dostave", "zamuda_dni", "ocena"]]


# ---------------------------------------------------------------------------
# Grafi — prvič prikazano v: A_vizualizacija (A2, A3, A7)
# ---------------------------------------------------------------------------

def histogram_in_skatla(df, stolpec, log=False):
    """Histogram s KDE (levo) in škatla z brki (desno) za en numerični stolpec."""
    podatki = df[df[stolpec].notna()]
    if log and (podatki[stolpec] <= 0).any():  # na logaritemski osi ni prostora za 0 in negativne vrednosti
        print(f"Na logaritemski osi ne prikažemo {(podatki[stolpec] <= 0).sum()} vrstic z vrednostjo <= 0.")
        podatki = podatki[podatki[stolpec] > 0]
    histogram = (ggplot(podatki, aes(x=stolpec))
                 + geom_histogram(aes(y=after_stat("density")), bins=50, fill=MODRA)
                 + geom_density()
                 + labs(y="gostota"))
    skatla = (ggplot(podatki, aes(x="''", y=stolpec))
              + geom_boxplot(width=0.4, outlier_alpha=0.3)
              + coord_flip()
              + labs(x=""))
    if log:
        histogram = histogram + scale_x_log10()
        skatla = skatla + scale_y_log10()
    return (histogram | skatla) + theme(figure_size=(11, 4))


def graf_pogostosti(df, stolpec, top=None):
    """Vodoravni stolpci: kolikokrat se pojavi vsaka vrednost. Manjkajoče pokaže kot 'manjka'."""
    stevila = (df[stolpec].astype("string")       # kot besedilo: deluje tudi za številske kode
               .fillna("manjka").value_counts().reset_index())
    if top:                                   # samo najpogostejše, 'manjka' pa vedno pokažemo
        stevila = stevila[(stevila.index < top) | (stevila[stolpec] == "manjka")]
    vrstni_red = stevila[stolpec][::-1].tolist()          # največja kategorija zgoraj
    return (ggplot(stevila, aes(x=stolpec, y="count"))
            + geom_col(fill=MODRA)
            + scale_x_discrete(limits=vrstni_red)
            + coord_flip()
            + labs(title=f"Pogostost: {stolpec}", x="", y="Število vrstic"))


def graf_korelacij(kor):
    """Korelacijska matrika: modra = negativna, oranžna = pozitivna korelacija."""
    dolga = (kor.round(2).rename_axis("stolpec_1").reset_index()
             .melt(id_vars="stolpec_1", var_name="stolpec_2", value_name="r"))
    imena = kor.columns.tolist()
    n = len(imena)
    return (ggplot(dolga, aes(x="stolpec_1", y="stolpec_2", fill="r"))
            + geom_tile(color="white")
            + geom_text(aes(label="r"), size=8 if n <= 10 else 6)
            + scale_fill_gradient2(low=MODRA, mid="#f0efec", high=ORANZNA, limits=(-1, 1))
            + scale_x_discrete(limits=imena)
            + scale_y_discrete(limits=imena[::-1])
            + coord_equal()
            + theme(figure_size=(max(6, 0.6 * n), max(5, 0.55 * n)),
                    axis_text_x=element_text(rotation=45, ha="right"))
            + labs(title="Korelacijska matrika", x="", y=""))


# ---------------------------------------------------------------------------
# Manjkajoče vrednosti — prvič prikazano v: A_manjkajoce_vrednosti (A6)
# ---------------------------------------------------------------------------

def primerjaj_pred_po(pred, po, naslov=""):
    """Histogram po obravnavi (modri stolpci) in obris porazdelitve pred njo (črna črta)."""
    meje = np.histogram_bin_edges(pd.concat([pred, po]).dropna(), bins=40)
    return (ggplot(mapping=aes(x="vrednost"))
            + geom_histogram(data=pd.DataFrame({"vrednost": po.dropna()}), breaks=meje, fill=MODRA)
            + geom_histogram(data=pd.DataFrame({"vrednost": pred.dropna()}), breaks=meje,
                             fill="none", color="black")
            + labs(title=naslov, x="", y="Število vrstic",
                   subtitle=f"modro: po (n = {po.notna().sum()}), črn obris: pred (n = {pred.notna().sum()})"))


# ---------------------------------------------------------------------------
# Osamelci — prvič prikazano v: A_osamelci (A2)
# ---------------------------------------------------------------------------

def meje_iqr(s, k=1.5):
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr

# ===========================================================================
# MODUL 2: zagon skript, izris dreves, lestvica "100 klicev", graf regresijskih modelov
# ===========================================================================

SEME = 42                      # isto seme povsod: vsi dobimo iste številke
IMENA_RAZREDOV = ["ostane", "odide"]

# 16 številskih značilk telekoma iz prvega modula (brez id_stranke in brez cilja odhod)
TELEKOM_STEVILSKE = [
    "mesecev_narocnine", "povp_mesecni_prihodek", "povp_mesecna_narocnina", "povp_minute",
    "povp_minute_6m", "sprememba_minut", "povp_minute_prekoracitev", "povp_gostovanje",
    "povp_klici_podpora", "povp_prekinjeni_klici", "stevilo_narocnin", "stevilo_telefonov",
    "dni_z_napravo", "cena_naprave", "dohodek_razred", "stevilo_avtomobilov",
]


# ---------------------------------------------------------------------------
# Zagon skripte za pripravo podatkov: utils/pripravi_telekom.py, utils/pripravi_olist.py
# ---------------------------------------------------------------------------

def pozeni_skripto(pot):
    """Požene skripto iz repozitorija. Isto kot v terminalu: python <pot>."""
    print(f"$ python {pot}")
    okolje = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    izid = subprocess.run([sys.executable, str(KOREN / pot)], cwd=KOREN, env=okolje,
                          capture_output=True, text=True, encoding="utf-8")
    print(izid.stdout, end="")
    if izid.returncode != 0:
        raise RuntimeError(f"Skripta {pot} se ni končala pravilno:\n{izid.stderr}")


# ---------------------------------------------------------------------------
# Mere za klasifikacijo — prvič prikazano v: A_klasifikacijsko_drevo (A2)
# ---------------------------------------------------------------------------

def mere(dejansko, napoved):
    """Matrika zamenjav in tri mere. 1 = odide (to napoved imenujemo pozitivna), 0 = ostane."""
    dejansko, napoved = np.asarray(dejansko), np.asarray(napoved)
    tp = int(((napoved == 1) & (dejansko == 1)).sum())      # TP, true positive: napovemo odhod, stranka odide
    fp = int(((napoved == 1) & (dejansko == 0)).sum())      # FP, false positive: napovemo odhod, stranka ostane
    fn = int(((napoved == 0) & (dejansko == 1)).sum())      # FN, false negative: napovemo, da ostane, stranka odide
    tn = int(((napoved == 0) & (dejansko == 0)).sum())      # TN, true negative: napovemo, da ostane, in ostane
    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
            "točnost": (tp + tn) / len(dejansko),                           # delež pravilnih napovedi
            "natančnost": tp / (tp + fp) if tp + fp > 0 else np.nan,       # brez napovedanih odhodov ni določena
            "priklic": tp / (tp + fn)}                                       # delež najdenih odhodov


def graf_matrike(dejansko, napoved, naslov=""):
    """Matrika zamenjav kot graf. Vrstice: kaj se je zgodilo. Stolpci: kaj smo napovedali."""
    m = mere(dejansko, napoved)
    polja = pd.DataFrame({"napoved": ["odide", "ostane", "odide", "ostane"],
                          "dejansko": ["odide", "odide", "ostane", "ostane"],
                          "oznaka": ["TP", "FN", "FP", "TN"]})
    polja["strank"] = [m[o] for o in polja["oznaka"]]
    polja["izid"] = np.where(polja["napoved"] == polja["dejansko"], "pravilno", "napaka")
    polja["besedilo"] = [f"{o}\n{s:,}".replace(",", " ") for o, s in zip(polja["oznaka"], polja["strank"])]
    return (ggplot(polja, aes(x="napoved", y="dejansko", fill="izid"))
            + geom_tile(color="white", size=2)
            + geom_text(aes(label="besedilo"), size=13)
            + scale_fill_manual(values={"pravilno": "#cfe8d9", "napaka": "#f6d5c7"})
            + scale_x_discrete(limits=["odide", "ostane"])
            + scale_y_discrete(limits=["ostane", "odide"])            # "odide" je zgoraj
            + coord_equal()
            + labs(title=naslov, x="napoved (predicted)", y="dejansko (actual)", fill="")
            + theme(panel_grid=element_blank(), axis_text=element_text(size=11), figure_size=(4.6, 3.6)))


# ---------------------------------------------------------------------------
# Izris drevesa — prvič prikazano v: A_klasifikacijsko_drevo (A3, A4, A7, A9)
# ---------------------------------------------------------------------------

def _mesanica(barva, moc):
    """Barva med belo (moc = 0) in izbrano barvo (moc = 1)."""
    return tuple(1 - moc * (1 - c) for c in to_rgb(barva))


def narisi_drevo(drevo, znacilke, globina=None, ax=None, velikost=(13, 5.5), pisava=9):
    """Nariše drevo s slovenskimi oznakami. Modro = večina ostane, oranžno = večina odide."""
    if ax is None:
        _, ax = plt.subplots(figsize=velikost)
    polja = plot_tree(drevo, feature_names=list(znacilke), max_depth=globina, impurity=False,
                      filled=True, rounded=True, fontsize=pisava, ax=ax)
    for polje in polja:
        besedilo = polje.get_text()
        stevila = re.search(r"value = \[([\d.]+), ([\d.]+)\]", besedilo)
        if stevila is None:                    # "(...)": veje pod prikazano globino
            continue
        ostane, odide = float(stevila.group(1)), float(stevila.group(2))
        delez = odide / (ostane + odide)
        prva = besedilo.split("\n")[0]
        vrstice = ([prva] if "<=" in prva else []) + [
            f"strank: {ostane + odide:,.0f}".replace(",", " "),
            f"odide: {delez:.0%}",
            "napoved: " + IMENA_RAZREDOV[int(delez > 0.5)],
        ]
        polje.set_text("\n".join(vrstice))
        okvir = polje.get_bbox_patch()
        okvir.set_facecolor(_mesanica(ORANZNA if delez > 0.5 else MODRA, 0.15 + 0.85 * abs(delez - 0.5) * 2))
        okvir.set_edgecolor("#8a8a8a")
    for oznaka in ax.texts:                    # oznaki na prvih vejah: True / False -> da / ne
        if oznaka.get_text().strip() in ("True", "False"):
            oznaka.set_text("da" if oznaka.get_text().strip() == "True" else "ne")
    return ax


def graf_obmocij(drevo, podatki, x, y, koraki=160):
    """Območja napovedi za drevo, ki je naučeno SAMO na dveh značilkah (x in y)."""
    meje_x = podatki[x].quantile([0.005, 0.995])
    meje_y = podatki[y].quantile([0.005, 0.995])
    mreza = pd.DataFrame([(a, b) for a in np.linspace(*meje_x, koraki) for b in np.linspace(*meje_y, koraki)],
                         columns=[x, y])
    mreza["verjetnost"] = drevo.predict_proba(mreza)[:, 1]
    return (ggplot(mreza, aes(x=x, y=y, fill="verjetnost"))
            + geom_tile()
            + scale_fill_gradient2(low=MODRA, mid="#f0efec", high=ORANZNA, midpoint=0.5, limits=(0, 1))
            + labs(fill="verjetnost\nodhoda")
            + theme(panel_grid=element_blank()))


def oceni_globine(X_ucni, y_ucni, X_val, y_val, globine=range(1, 21)):
    """Za vsako globino nauči drevo in vrne točnost na učni in validacijski množici."""
    vrstice = []
    for globina in globine:
        drevo = DecisionTreeClassifier(max_depth=globina, random_state=SEME).fit(X_ucni, y_ucni)
        vrstice.append({"globina": globina, "listov": drevo.get_n_leaves(),
                        "učna": drevo.score(X_ucni, y_ucni), "validacijska": drevo.score(X_val, y_val)})
    return pd.DataFrame(vrstice)


# ---------------------------------------------------------------------------
# Lestvica "100 klicev" — prvič prikazano v: A_poslovna_odlocitev (A1–A3)
# ---------------------------------------------------------------------------

def izberi_najbolj_tvegane(ocene, k=100):
    """Vrne k strank z najvišjo oceno. Stranke z enako oceno razvrstimo naključno (seme 42)."""
    premesane = ocene.dropna().sample(frac=1, random_state=SEME)
    return premesane.sort_values(ascending=False, kind="stable").index[:k]


def vrstica_lestvice(ime, ocene, odhod):
    """Koliko od izbranih 100 oziroma 1 000 strank je res odšlo."""
    return {"izbira": ime,
            "odšlo od 100": int(odhod.loc[izberi_najbolj_tvegane(ocene, 100)].sum()),
            "odšlo od 1 000": int(odhod.loc[izberi_najbolj_tvegane(ocene, 1000)].sum())}


def graf_izbranih(izbori):
    """izbori = {naslov: odhod izbranih 100 strank}. Za vsak izbor mreža 10 x 10: oranžna = odšla."""
    deli = []
    for naslov, odhod in izbori.items():
        urejene = odhod.sort_values(ascending=False).reset_index(drop=True)
        deli.append(pd.DataFrame({"x": urejene.index % 10, "y": 9 - urejene.index // 10,
                                  "stranka": urejene.map({1: "odšla", 0: "ostala"}),
                                  "izbor": f"{naslov}\nodšlo: {int(urejene.sum())} od {len(urejene)}"}))
    mreza = pd.concat(deli)
    mreza["izbor"] = pd.Categorical(mreza["izbor"], mreza["izbor"].unique())     # vrstni red kot v slovarju
    return (ggplot(mreza, aes(x="x", y="y", color="stranka"))
            + geom_point(size=7.5)
            + scale_color_manual(values={"odšla": ORANZNA, "ostala": MODRA})
            + facet_wrap("~izbor")
            + coord_equal()
            + labs(color="")
            + theme_void()
            + theme(figure_size=(0.9 + 3.9 * len(izbori), 4.5),
                    strip_text=element_text(size=11, weight="bold", linespacing=1.4)))


# ---------------------------------------------------------------------------
# Polinomska regresija in skupni graf regresijskih modelov — prvič prikazano v: A_regresija (A6)
# ---------------------------------------------------------------------------


def potence(X, stopnja):
    """Vsakemu stolpcu doda njegove potence: x, x², x³ … do izbrane stopnje."""
    return pd.DataFrame({f"{c}^{k}": X[c] ** k for c in X.columns for k in range(1, stopnja + 1)})


def nauci_polinom(X, y, stopnja):
    """Nauči polinom izbrane stopnje. Vrne funkcijo napovej: damo ji tabelo, vrne napovedi."""
    skala = StandardScaler().fit(potence(X, stopnja))                          # povprečje in odklon: samo iz podanih (učnih) podatkov
    model = LinearRegression().fit(skala.transform(potence(X, stopnja)), y)    # linearna regresija na vseh potencah

    def napovej(X_novi):
        return model.predict(skala.transform(potence(X_novi, stopnja)))        # isti koraki na novih podatkih
    return napovej


def graf_napovedi(modeli, podatki, x="obljubljeni_dnevi", y="dni_dostave", povprecja=True):
    """Napovedi več modelov na istem grafu. Vsak model uporablja eno značilko x.

    modeli = {ime: model}. Model je naučen model s funkcijo predict (premica, drevo)
    ali funkcija, ki za tabelo s stolpcem x vrne napovedi (tako funkcijo vrne nauci_polinom).
    Pike: povprečje y v 40 pasovih x (povprecja=True) ali vsaka vrstica posebej (False).
    """
    spodaj, zgoraj = podatki[x].quantile([0.01, 0.99]) if povprecja else (podatki[x].min(), podatki[x].max())
    znotraj = podatki[(podatki[x] >= spodaj) & (podatki[x] <= zgoraj)]
    pike = znotraj.groupby(pd.cut(znotraj[x], 40), observed=True)[[x, y]].mean() if povprecja else znotraj[[x, y]]
    mreza = pd.DataFrame({x: np.linspace(spodaj, zgoraj, 300)})
    crte = []
    for ime, model in modeli.items():
        napovej = model.predict if hasattr(model, "predict") else model      # naučen model ali funkcija
        crte.append(mreza.assign(napoved=napovej(mreza), model=ime))
    crte = pd.concat(crte)
    crte["model"] = pd.Categorical(crte["model"], list(modeli))
    barve = [MODRA, ORANZNA, ZELENA, "#8e44ad", "#555555"][:len(modeli)]
    return (ggplot()
            + geom_point(aes(x=x, y=y), data=pike, color=SIVA, size=2, alpha=0.8)
            + geom_line(aes(x=x, y="napoved", color="model"), data=crte, size=1.3)
            + scale_color_manual(values=barve)
            + labs(color="", subtitle="sive pike: " + ("povprečje v 40 pasovih x" if povprecja else "posamezne vrstice")))


if __name__ == "__main__":
    poskrbi_za_podatke()
