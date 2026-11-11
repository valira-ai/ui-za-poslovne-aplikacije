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

import shutil
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from plotnine import (aes, after_stat, coord_equal, coord_flip, element_blank, element_text,
                      geom_boxplot, geom_col, geom_density, geom_histogram, geom_text, geom_tile,
                      ggplot, labs, scale_fill_gradient2, scale_x_discrete, scale_x_log10,
                      scale_y_discrete, scale_y_log10, theme, theme_minimal, theme_set)
from plotnine.exceptions import PlotnineWarning

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


if __name__ == "__main__":
    poskrbi_za_podatke()
