"""Pripravi podatke Olist (spletna trgovina) za modele in jih shrani v mapo data/pripravljeno/.

Zagon v terminalu, iz mape repozitorija:

    python -m utils.pripravi_olist

Skripta naredi isto kot zvezka A2_Priprava_Olist in A2_Delitev_in_manjkajoce_Olist
(mapa 03_Uvod_v_strojno_ucenje/notebooks), brez raziskovanja, grafov in vmesnih izpisov:

    1. prebere tabele spletne trgovine in jih združi v eno vrstico na naročilo,
    2. jih očisti in doda izpeljane značilke; cilj je dni_dostave,
    3. razdeli naročila po času na učno, validacijsko in testno množico,
    4. dopolni manjkajoče vrednosti z mediano učne množice,
    5. besedilne stolpce dodatno zapiše kot stolpce 0/1,
    6. shrani tabele train.csv, val.csv in test.csv v data/pripravljeno/delitve/olist/.

Delitev je časovna, zato ne potrebuje semena: določajo jo datumi spodaj.
Odločitve in razlogi zanje so v obeh zvezkih. Če tabele že obstajajo in so novejše od skripte,
skupnih funkcij v utils in surovih podatkov, skripta dela ne ponavlja.
"""
import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KOREN = Path(__file__).resolve().parents[1]          # mapa repozitorija
sys.path.insert(0, str(KOREN))                       # da Python najde mapo utils


IME, KLJUC, CILJ = "olist", "order_id", "dni_dostave"
META = ["order_id", "customer_unique_id", "datum_nakupa", "datum_znanega_izida"]
DATUMI = ["datum_nakupa", "datum_znanega_izida"]
ZACETEK_VAL = pd.Timestamp("2018-03-01")             # učna: naročila in dostave pred tem datumom
ZACETEK_TEST = pd.Timestamp("2018-06-01")            # validacijska: od 1. 3. do pred 1. 6. 2018
KONEC_TEST = pd.Timestamp("2018-09-01")              # testna: od 1. 6. do pred 1. 9. 2018
NAJMANJ_VRSTIC = 100                                 # kategorija z manj učnimi vrsticami gre v stolpec DRUGO


# ---------------------------------------------------------------------------
# 1. del: čista tabela (zvezek A2_Priprava_Olist)
# ---------------------------------------------------------------------------

def razmerje(stevec, imenovalec):
    return stevec / imenovalec.where(imenovalec.gt(0))


def popolna_vsota(s):
    return s.sum(min_count=len(s))


def pripravi_tabelo(data):
    """Ena vrstica = eno dostavljeno naročilo. Vrne čisto tabelo in njeno shemo (opis stolpcev)."""
    mapa = data / "trgovina"

    def preberi(ime):
        pot = mapa / ime
        stolpci = pd.read_csv(pot, nrows=0).columns
        tipi = {c: "string" for c in stolpci if c.endswith("_id") or "zip_code_prefix" in c}
        return pd.read_csv(pot, dtype=tipi).drop_duplicates()

    # Naložimo potrebne tabele in preverimo ključe.
    narocila = preberi("olist_orders_dataset.csv")
    postavke = preberi("olist_order_items_dataset.csv")
    izdelki = preberi("olist_products_dataset.csv")
    kupci = preberi("olist_customers_dataset.csv")
    prodajalci = preberi("olist_sellers_dataset.csv")
    prevod = preberi("product_category_name_translation.csv")
    for ime, df, kljuci in [("naročila", narocila, ["order_id"]), ("postavke", postavke, ["order_id", "order_item_id"]),
                            ("izdelki", izdelki, ["product_id"]), ("kupci", kupci, ["customer_id"]),
                            ("prodajalci", prodajalci, ["seller_id"]), ("prevod", prevod, ["product_category_name"])]:
        assert df[kljuci].notna().all().all(), f"Manjka ključ: {ime}"
        assert not df.duplicated(kljuci).any(), f"Različne vrstice istega ključa: {ime}"

    # Uredimo tipe in neveljavne vrednosti.
    for df, cols in [(izdelki, ["product_category_name"]), (prevod, ["product_category_name", "product_category_name_english"]),
                     (kupci, ["customer_state"]), (prodajalci, ["seller_state"])]:
        for c in cols:
            df[c] = df[c].astype("string").str.strip().replace("", pd.NA)
    for df, c in [(kupci, "customer_state"), (prodajalci, "seller_state")]:
        df[c] = df[c].str.upper()
    for df, cols, strogo_pozitivno in [
        (postavke, ["price", "freight_value"], False),
        (izdelki, ["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"], True),
        (izdelki, ["product_name_lenght", "product_description_lenght", "product_photos_qty"], False),
    ]:
        for c in cols:
            df[c] = pd.to_numeric(df[c], errors="coerce").replace([np.inf, -np.inf], np.nan)
            napaka = df[c].le(0) if strogo_pozitivno else df[c].lt(0)
            df[c] = df[c].mask(napaka)
    for c in ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]:
        narocila[c] = pd.to_datetime(narocila[c], errors="coerce")

    # Obogatimo postavke brez množenja vrstic.
    izdelki = izdelki.merge(prevod, on="product_category_name", how="left", validate="many_to_one")
    izdelki["kategorija"] = izdelki["product_category_name_english"].combine_first(izdelki["product_category_name"])
    izdelki["prostornina_cm3"] = izdelki["product_length_cm"] * izdelki["product_height_cm"] * izdelki["product_width_cm"]
    izdelki["najdaljsa_stranica_cm"] = izdelki[["product_length_cm", "product_height_cm", "product_width_cm"]].max(axis=1, skipna=False)

    lokacija_kupca = narocila[["order_id", "customer_id"]].merge(
        kupci[["customer_id", "customer_state"]], on="customer_id", how="left", validate="many_to_one")
    p = (postavke.merge(izdelki[["product_id", "kategorija", "product_weight_g", "prostornina_cm3",
                "najdaljsa_stranica_cm", "product_name_lenght", "product_description_lenght", "product_photos_qty"]],
                on="product_id", how="left", validate="many_to_one")
         .merge(prodajalci[["seller_id", "seller_state"]], on="seller_id", how="left", validate="many_to_one")
         .merge(lokacija_kupca[["order_id", "customer_state"]], on="order_id", how="left", validate="many_to_one"))
    assert len(p) == len(postavke)
    for c in ["product_weight_g", "prostornina_cm3", "kategorija", "seller_state", "price", "freight_value"]:
        p[c + "_manjka"] = p[c].isna().astype("int8")
    lokaciji_znani = p["customer_state"].notna() & p["seller_state"].notna()
    p["ista_drzava"] = p["customer_state"].eq(p["seller_state"]).astype("Float64").where(lokaciji_znani).astype(float)

    # Agregiramo na eno vrstico na naročilo. Ime: (izvor, agregacija, skupina, opis)
    agregati = {
        "st_postavk": ("order_item_id", "size", "kosarica", "Število postavk v naročilu."),
        "st_izdelkov": ("product_id", "nunique", "kosarica", "Število različnih izdelkov."),
        "st_prodajalcev": ("seller_id", "nunique", "lokacija", "Število različnih prodajalcev."),
        "vrednost": ("price", popolna_vsota, "kosarica", "Vsota cen vseh postavk brez poštnine, BRL; NaN ob delnem manjkanju."),
        "postnina": ("freight_value", popolna_vsota, "kosarica", "Vsota poštnine vseh postavk, BRL; NaN ob delnem manjkanju."),
        "cena_postavke_min": ("price", "min", "kosarica", "Najnižja znana cena postavke, BRL."),
        "cena_postavke_max": ("price", "max", "kosarica", "Najvišja znana cena postavke, BRL."),
        "cena_postavke_povp": ("price", "mean", "kosarica", "Povprečje znanih cen postavk, BRL."),
        "razpon_cen": ("price", lambda s: s.max() - s.min(), "kosarica", "Razlika med najvišjo in najnižjo znano ceno, BRL."),
        "teza_g": ("product_weight_g", popolna_vsota, "izdelki", "Skupna masa vseh postavk, g; NaN ob delnem manjkanju."),
        "teza_povp_g": ("product_weight_g", "mean", "izdelki", "Povprečna masa postavke z znano maso, g."),
        "teza_max_g": ("product_weight_g", "max", "izdelki", "Največja znana masa postavke, g."),
        "prostornina_cm3": ("prostornina_cm3", popolna_vsota, "izdelki", "Vsota prostornin izdelkov, cm³; ni prostornina transportnega paketa."),
        "prostornina_max_cm3": ("prostornina_cm3", "max", "izdelki", "Največja znana prostornina postavke, cm³."),
        "najdaljsa_stranica_cm": ("najdaljsa_stranica_cm", "max", "izdelki", "Najdaljša znana stranica med izdelki naročila, cm."),
        "dolzina_imena_povp": ("product_name_lenght", "mean", "katalog", "Povprečna dolžina znanih imen izdelkov, znaki."),
        "dolzina_opisa_povp": ("product_description_lenght", "mean", "katalog", "Povprečna dolžina znanih opisov izdelkov, znaki."),
        "stevilo_fotografij_povp": ("product_photos_qty", "mean", "katalog", "Povprečno število fotografij pri znanih izdelkih."),
        "st_znanih_kategorij": ("kategorija", "nunique", "katalog", "Število različnih znanih kategorij; neznanih ne štejemo."),
        "st_znanih_drzav_prodajalcev": ("seller_state", "nunique", "lokacija", "Število različnih znanih zveznih držav prodajalcev."),
        "delez_postavk_ista_drzava": ("ista_drzava", "mean", "lokacija", "Delež postavk iz iste države kot kupec, med postavkami z znanima lokacijama."),
        "delez_postavk_brez_teze": ("product_weight_g_manjka", "mean", "manjkanje", "Delež postavk brez veljavne mase."),
        "delez_postavk_brez_prostornine": ("prostornina_cm3_manjka", "mean", "manjkanje", "Delež postavk brez veljavnih mer."),
        "delez_postavk_brez_kategorije": ("kategorija_manjka", "mean", "manjkanje", "Delež postavk brez znane kategorije."),
        "delez_postavk_brez_lokacije_prodajalca": ("seller_state_manjka", "mean", "manjkanje", "Delež postavk brez znane države prodajalca."),
        "delez_postavk_brez_cene": ("price_manjka", "mean", "manjkanje", "Delež postavk brez veljavne cene."),
        "delez_postavk_brez_postnine": ("freight_value_manjka", "mean", "manjkanje", "Delež postavk brez veljavne poštnine."),
    }
    po_narocilu = p.groupby("order_id").agg(**{ime: pd.NamedAgg(column=vir, aggfunc=agg)
        for ime, (vir, agg, _, _) in agregati.items()}).reset_index()
    # Kategorija in prodajalec naročila: po najdražji postavki.
    glavna = (p.sort_values(["order_id", "price", "order_item_id"], ascending=[True, False, True], na_position="last")
              .drop_duplicates("order_id")[["order_id", "kategorija", "seller_state"]])
    po_narocilu = po_narocilu.merge(glavna, on="order_id", how="left", validate="one_to_one")
    assert po_narocilu["order_id"].is_unique
    assert po_narocilu["st_postavk"].sum() == len(postavke)

    # Določimo cilj in obseg zbirke.
    tabela = (narocila[["order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_delivered_customer_date",
                        "order_estimated_delivery_date"]]
        .merge(kupci[["customer_id", "customer_unique_id", "customer_state"]], on="customer_id", how="left", validate="many_to_one")
        .merge(po_narocilu, on="order_id", how="left", validate="one_to_one"))
    assert len(tabela) == len(narocila) and tabela["order_id"].is_unique
    # total_seconds ohrani tudi del dneva; .dt.days bi ga odrezal.
    tabela["dni_dostave"] = (tabela["order_delivered_customer_date"] - tabela["order_purchase_timestamp"]).dt.total_seconds() / 86400
    # Rok, ki ga trgovina pokaže kupcu ob nakupu: znan je ob oddaji naročila, zato je lahko značilka.
    tabela["obljubljeni_dnevi"] = (tabela["order_estimated_delivery_date"] - tabela["order_purchase_timestamp"]).dt.total_seconds() / 86400
    obdrzi = (tabela["order_status"].eq("delivered")
              & tabela[["order_purchase_timestamp", "order_delivered_customer_date"]].notna().all(axis=1)
              & tabela["dni_dostave"].ge(0)
              & tabela["st_postavk"].gt(0)
              & tabela["customer_unique_id"].notna())
    tabela = tabela.loc[obdrzi].drop(columns=["customer_id", "order_status", "order_estimated_delivery_date"]).rename(columns={
        "order_purchase_timestamp": "datum_nakupa", "order_delivered_customer_date": "datum_znanega_izida",
        "customer_state": "zvezna_drzava", "seller_state": "drzava_glavnega_prodajalca"}).copy()
    assert tabela["order_id"].is_unique

    # Slovar značilk izvozimo skupaj s tabelo.
    opisi = {}
    skupine = {}

    def dodaj(ime, vrednosti, skupina, opis, vir):
        tabela[ime] = vrednosti
        skupine.setdefault(skupina, []).append(ime)
        opisi[ime] = {"opis": opis, "vir": vir, "skupina": skupina}

    for ime, (vir, _, skupina, opis) in agregati.items():
        dodaj(ime, tabela[ime], skupina, opis, vir + " → agregat po order_id")
    for ime, skupina, opis, vir in [
        ("kategorija", "katalog", "Kategorija najdražje postavke; pri enaki ceni manjši order_item_id.", "product_category_name"),
        ("zvezna_drzava", "lokacija", "Brazilska zvezna država kupca pri naročilu.", "customer_state"),
        ("drzava_glavnega_prodajalca", "lokacija", "Zvezna država prodajalca najdražje postavke.", "seller_state"),
    ]:
        dodaj(ime, tabela[ime].astype("string"), skupina, opis, vir)

    # Časovne značilke, razmerja in transformacije. Uporabimo čas oddaje naročila, ne časa dostave.
    cas = tabela["datum_nakupa"]
    for ime, vrednost, opis in [
        ("leto_nakupa", cas.dt.year, "Koledarsko leto oddaje naročila."),
        ("mesec_nakupa", cas.dt.month, "Koledarski mesec, 1–12."),
        ("dan_v_mesecu", cas.dt.day, "Dan v mesecu, 1–31."),
        ("dan_v_tednu", cas.dt.day_of_week, "Ponedeljek=0, nedelja=6."),
        ("ura_nakupa", cas.dt.hour, "Ura naročila v zapisanem času izvoza, 0–23."),
        ("vikend", cas.dt.day_of_week.ge(5).astype("int8"), "1 = sobota ali nedelja."),
    ]:
        dodaj(ime, vrednost, "cas_narocila", opis, "order_purchase_timestamp")
    for ime, vrednost, perioda in [("mesec", tabela["mesec_nakupa"] - 1, 12),
                                  ("dan_tedna", tabela["dan_v_tednu"], 7), ("ura", tabela["ura_nakupa"], 24)]:
        dodaj(ime + "_sin", np.sin(2 * np.pi * vrednost / perioda), "cas_narocila", "Sinus ciklične časovne značilke.", "order_purchase_timestamp")
        dodaj(ime + "_cos", np.cos(2 * np.pi * vrednost / perioda), "cas_narocila", "Kosinus ciklične časovne značilke.", "order_purchase_timestamp")

    dodaj("obljubljeni_dnevi", tabela["obljubljeni_dnevi"], "obljuba",
          "Rok dostave, ki ga trgovina obljubi kupcu ob nakupu, v dnevih od oddaje naročila.", "order_estimated_delivery_date")
    for ime, stevec, imenovalec, opis in [
        ("postnina_na_vrednost", "postnina", "vrednost", "Razmerje poštnine in vrednosti blaga; ni delež celotnega računa."),
        ("postnina_na_postavko", "postnina", "st_postavk", "Povprečna poštnina na postavko, BRL."),
        ("delez_najdrazje_postavke", "cena_postavke_max", "vrednost", "Delež najdražje postavke v skupni vrednosti blaga."),
        ("masa_na_prostornino", "teza_g", "prostornina_cm3", "Razmerje skupne mase in vsote prostornin izdelkov, g/cm³."),
    ]:
        dodaj(ime, razmerje(tabela[stevec], tabela[imenovalec]), "izpeljane", opis, f"{stevec}, {imenovalec}")
    dodaj("vec_prodajalcev", tabela["st_prodajalcev"].gt(1).astype("int8"), "izpeljane", "1 = v naročilu sodeluje več prodajalcev.", "st_prodajalcev")
    dodaj("vec_postavk", tabela["st_postavk"].gt(1).astype("int8"), "izpeljane", "1 = naročilo vsebuje več postavk.", "st_postavk")
    for c in ["vrednost", "postnina", "teza_g", "prostornina_cm3"]:
        dodaj("log1p_" + c, np.log1p(tabela[c]), "transformirane", "Naravni logaritem (1 + vrednost).", c)

    # Označimo manjkanje.
    for c in ["teza_g", "prostornina_cm3", "vrednost", "postnina", "kategorija", "zvezna_drzava", "drzava_glavnega_prodajalca"]:
        dodaj(c + "_manjka", tabela[c].isna().astype("int8"), "manjkanje", "1 = podatek manjka ali je neveljaven.", c)
    for c in ["kategorija", "zvezna_drzava", "drzava_glavnega_prodajalca"]:
        tabela[c] = tabela[c].fillna("NEZNANO")

    # Nabori značilk ter meja med značilkami in metapodatki.
    for c, opis, vir in [
        ("order_id", "ID naročila; ključ, ne značilka.", "order_id"),
        ("customer_unique_id", "ID ponovnih nakupov istega kupca; za skupinsko delitev, ne značilka.", "customer_unique_id"),
        ("datum_nakupa", "Čas napovedi; metapodatek za časovno delitev.", "order_purchase_timestamp"),
        ("datum_znanega_izida", "Čas dostave; najzgodnejši trenutek znanega cilja, nikoli značilka.", "order_delivered_customer_date"),
        ("dni_dostave", "Pretečeni čas od naročila do dostave v dnevih, brez zaokroževanja na cele dneve.", "(order_delivered_customer_date - order_purchase_timestamp) / 1 dan"),
    ]:
        opisi[c] = {"opis": opis, "vir": vir, "skupina": "cilj" if c == CILJ else "metapodatki"}
    vse = [c for v in skupine.values() for c in v]
    osnovni = ["vrednost", "postnina", "st_postavk", "teza_g", "zvezna_drzava"]
    nabori = {
        "osnovni": osnovni,
        "kosarica_in_lokacija": list(dict.fromkeys(osnovni + skupine["kosarica"] + skupine["lokacija"])),
        "izvorni_agregati": [c for g in ["kosarica", "izdelki", "katalog", "lokacija", "cas_narocila"] for c in skupine[g]],
        "brez_kataloga": [c for c in vse if c not in skupine["katalog"] and c not in ["kategorija_manjka", "delez_postavk_brez_kategorije"]],
        "vsi": vse,
    }
    izloceni = ["order_status", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date",
        "shipping_limit_date", "review_score", "review_comment_message", "plačila"]
    opombe = ["Ni delitve, imputacije z naučeno statistiko, kodiranja, skaliranja ali modela.",
        "Napoved ob oddaji naročila; vhodne informacije o katalogu, košarici in lokaciji predpostavimo kot takrat znane.",
        "Vključena so dostavljena naročila z znanim ciljem, kupcem in vsaj eno postavko; nedostavljeni niso dobili izmišljenega y.",
        "datum_znanega_izida je metapodatek za poznejšo časovno delitev, nikoli značilka.",
        "Čas izida lahko v izvornem sistemu postane dostopen pozneje od same dostave; izvoz tega zamika ne vsebuje.",
        "Numerične NaN ohranimo, kategorije dopolnimo s stalno oznako NEZNANO.",
        "Vsota z vsaj eno neznano postavko ostane neznana; povprečja opisujejo znane postavke."]
    assert tabela[CILJ].ge(0).all()
    assert tabela["datum_znanega_izida"].ge(tabela["datum_nakupa"]).all()
    assert not set(izloceni) & set(vse)

    # Preverimo in sestavimo shemo.
    znacilke = [c for stolpci in skupine.values() for c in stolpci]
    assert len(znacilke) == len(set(znacilke))
    assert set(tabela.columns) == set(META + [CILJ] + znacilke)
    assert tabela[KLJUC].notna().all() and tabela[KLJUC].is_unique
    assert tabela[CILJ].notna().all()
    assert not np.isinf(tabela.select_dtypes(include="number").to_numpy(dtype=float)).any()
    assert all(set(v) <= set(znacilke) for v in nabori.values())

    kategoricne = [c for c in znacilke if not pd.api.types.is_numeric_dtype(tabela[c])]
    numericne = [c for c in znacilke if c not in kategoricne]
    tabela = tabela[META + [CILJ] + znacilke].sort_values(KLJUC).reset_index(drop=True)
    slovar = []
    for c in tabela:
        vloga = "cilj" if c == CILJ else ("metapodatek" if c in META else "znacilka")
        slovar.append({"stolpec": c, "vloga": vloga, "dtype": str(tabela[c].dtype),
            "manjkajocih": int(tabela[c].isna().sum()), **opisi[c]})
    shema = {
        "razlicica": 1, "zbirka": IME, "datoteka": f"{IME}_modeliranje.csv",
        "kljuc": KLJUC, "cilj": CILJ, "metapodatki": META, "datumski_stolpci": DATUMI,
        "numericne_znacilke": numericne, "kategoricne_znacilke": kategoricne,
        "znacilke": znacilke, "skupine_znacilk": skupine, "nabori_znacilk": nabori,
        "stolpci": slovar, "vrstic": len(tabela), "stevilo_znacilk": len(znacilke),
        "izloceni_vhodi": izloceni, "opombe": opombe,
    }
    return tabela, shema


# ---------------------------------------------------------------------------
# 2. del: časovna delitev, manjkajoče vrednosti in stolpci 0/1 (zvezek A2_Delitev_in_manjkajoce_Olist)
# ---------------------------------------------------------------------------

def casovna_delitev(df, zacetek_val, zacetek_test, konec_test):
    """V učni in validacijski množici so samo naročila, ki so bila do meje že dostavljena."""
    nakup, izid = df["datum_nakupa"], df["datum_znanega_izida"]
    pred_val = nakup.lt(zacetek_val)
    v_val = nakup.ge(zacetek_val) & nakup.lt(zacetek_test)
    v_test = nakup.ge(zacetek_test) & nakup.lt(konec_test)
    vloge = pd.Series("izloceno", index=df.index, dtype="string")
    razlog = pd.Series("izven_dogovorjenih_obdobij", index=df.index, dtype="string")
    razlog.loc[pred_val & izid.ge(zacetek_val)] = "ucni_izid_ob_meji_se_ni_znan"
    razlog.loc[v_val & izid.ge(zacetek_test)] = "validacijski_izid_ob_meji_se_ni_znan"
    for ime, maska in [
        ("train", pred_val & izid.lt(zacetek_val)),
        ("val", v_val & izid.lt(zacetek_test)),
        ("test", v_test),
    ]:
        vloge.loc[maska] = ime
        razlog.loc[maska] = "vkljuceno"
    return vloge, razlog


def nauci_dopolnjevanje(X_train, numericni, kategoricni):
    """Vrednosti za dopolnjevanje določimo samo iz podanega učnega X."""
    mediane = X_train[numericni].astype(float).median()
    prazni = mediane.index[mediane.isna()].tolist()
    return {
        "numericni": list(numericni), "kategoricni": list(kategoricni),
        "mediane": mediane.fillna(0.0).to_dict(),
        "povsem_prazni_ucni_stolpci": prazni,
        "nadomestilo_za_prazen_numericni_stolpec": 0.0,
        "neznana_kategorija": "NEZNANO",
    }


def dopolni(X, pravila):
    """Uporaba že določenih pravil; nobene nove mediane ali drugega učenja."""
    rezultat = X.copy()
    for c in pravila["numericni"]:
        rezultat[c] = rezultat[c].astype(float).fillna(pravila["mediane"][c])
    for c in pravila["kategoricni"]:
        rezultat[c] = rezultat[c].astype("string").fillna(pravila["neznana_kategorija"])
    return rezultat


def nauci_kodiranje(X_train, kategoricni, najmanj=NAJMANJ_VRSTIC):
    """Seznam kategorij določimo samo iz podanega učnega X."""
    pravila = {"najmanj_ucnih_vrstic": najmanj, "skupna_kategorija": "DRUGO", "stolpci": {}}
    for c in kategoricni:
        stevilo = X_train[c].astype("string").value_counts()
        pravila["stolpci"][c] = {
            "kategorije": sorted(stevilo.index[stevilo >= najmanj]),
            "v_skupni_kategoriji": sorted(stevilo.index[stevilo < najmanj]),
        }
    return pravila


def ime_kodiranega(stolpec, kategorija):
    # V imenu stolpca pustimo samo črke, številke in podčrtaje.
    return stolpec + "_" + re.sub(r"[^0-9A-Za-z]+", "_", kategorija).strip("_")


def kodiraj(X, pravila):
    """Uporaba že določenih kategorij; novih kategorij se ne učimo."""
    novi = {}
    for c, p in pravila["stolpci"].items():
        vrednosti = X[c].astype("string")
        for k in p["kategorije"]:
            novi[ime_kodiranega(c, k)] = vrednosti.eq(k).astype("int8")
        if p["v_skupni_kategoriji"]:
            novi[ime_kodiranega(c, pravila["skupna_kategorija"])] = (~vrednosti.isin(p["kategorije"])).astype("int8")
    return pd.DataFrame(novi, index=X.index)


def razdeli_in_shrani(pot_csv, pot_sheme, izhod):
    """Prebere čisto tabelo, jo razdeli po času, dopolni, kodira in shrani train.csv, val.csv, test.csv."""
    shema = json.loads(pot_sheme.read_text(encoding="utf-8"))
    ZNACILKE = shema["znacilke"]
    NUM = shema["numericne_znacilke"]
    KAT = shema["kategoricne_znacilke"]
    tipi = {r["stolpec"]: r["dtype"] for r in shema["stolpci"] if r["stolpec"] not in DATUMI}
    podatki = pd.read_csv(pot_csv, dtype=tipi, parse_dates=DATUMI,
        keep_default_na=False, na_values=[""])
    assert podatki[KLJUC].notna().all() and podatki[KLJUC].is_unique
    assert podatki[CILJ].notna().all(), "Cilja ne dopolnjujemo."

    # Najprej delitev po koledarskih obdobjih.
    podatki = podatki.sort_values(["datum_nakupa", KLJUC]).reset_index(drop=True)
    parametri_delitve = {"metoda": "casovna_s_preverjanjem_znanega_izida",
        "zacetek_val": ZACETEK_VAL.isoformat(), "zacetek_test": ZACETEK_TEST.isoformat(),
        "konec_test": KONEC_TEST.isoformat(), "cas_napovedi": "datum_nakupa",
        "cas_izida": "datum_znanega_izida", "meje": "spodnja vključena, zgornja izključena",
        "opomba": "Čas znanega izida je približek: izvoz ne beleži dodatnega zamika vnosa podatka."}
    vloge, razlogi = casovna_delitev(podatki, ZACETEK_VAL, ZACETEK_TEST, KONEC_TEST)
    zbirke_pred = {ime: podatki.loc[vloge.eq(ime)].copy() for ime in ["train", "val", "test"]}
    assert zbirke_pred["train"]["datum_znanega_izida"].max() < ZACETEK_VAL
    assert zbirke_pred["train"]["datum_nakupa"].max() < zbirke_pred["val"]["datum_nakupa"].min()
    assert zbirke_pred["val"]["datum_nakupa"].max() < zbirke_pred["test"]["datum_nakupa"].min()
    evidenca = podatki[META].copy()
    evidenca["zbirka"] = vloge
    evidenca["razlog"] = razlogi

    # Manjkajoče vrednosti: pravila se naučimo samo iz učne množice.
    pravila = nauci_dopolnjevanje(zbirke_pred["train"][ZNACILKE], NUM, KAT)
    zbirke = {}
    for ime, df in zbirke_pred.items():
        X_po = dopolni(df[ZNACILKE], pravila)
        assert not X_po.isna().any().any()
        zbirke[ime] = pd.concat([df[META + [CILJ]], X_po], axis=1)

    # Besedilni stolpci: kategorije spremenimo v stolpce 0/1. Seznam kategorij je samo iz učne množice.
    kodiranje = nauci_kodiranje(zbirke["train"][ZNACILKE], KAT)
    kodirane = {ime: kodiraj(df[ZNACILKE], kodiranje) for ime, df in zbirke.items()}
    KODIRANE = {c: [ime_kodiranega(c, k) for k in p["kategorije"] + [kodiranje["skupna_kategorija"]] * bool(p["v_skupni_kategoriji"])]
                for c, p in kodiranje["stolpci"].items()}
    KODIRANE_VSE = [s for stolpci in KODIRANE.values() for s in stolpci]
    assert KODIRANE_VSE == kodirane["train"].columns.tolist() and len(KODIRANE_VSE) == len(set(KODIRANE_VSE))
    assert not set(KODIRANE_VSE) & set(META + [CILJ] + ZNACILKE), "Ime novega stolpca že obstaja."
    ZNACILKE_ZA_MODEL = NUM + KODIRANE_VSE

    # Shranimo delitve, pravila in shemo. Vse tri datoteke imajo iste stolpce in tipe.
    stolpci_izhoda = META + [CILJ] + ZNACILKE + KODIRANE_VSE
    koncne = {ime: pd.concat([df, kodirane[ime]], axis=1) for ime, df in zbirke.items()}

    def za_model(stolpci):
        # Besedilni stolpec zamenjamo z njegovimi stolpci 0/1, vrstni red ostane.
        return [s for c in stolpci for s in KODIRANE.get(c, [c])]

    izhodna_shema = copy.deepcopy(shema)
    izhodna_shema.pop("datoteka", None)
    izhodna_shema["razlicica"] = 2
    izhodna_shema["vrstic"] = sum(len(df) for df in zbirke.values())
    izhodna_shema["datoteke"] = {ime: f"{ime}.csv" for ime in zbirke}
    izhodna_shema["vrstice_po_zbirkah"] = {ime: len(df) for ime, df in zbirke.items()}
    izhodna_shema["izlocenih_vrstic"] = int(vloge.eq("izloceno").sum())
    izhodna_shema["delitev"] = parametri_delitve
    izhodna_shema["vhodna_tabela"] = str(pot_csv.relative_to(KOREN))
    izhodna_shema["vhodna_shema"] = str(pot_sheme.relative_to(KOREN))
    izhodna_shema["sha256_vhoda"] = hashlib.sha256(pot_csv.read_bytes()).hexdigest()
    izhodna_shema["sha256_vhodne_sheme"] = hashlib.sha256(pot_sheme.read_bytes()).hexdigest()
    izhodna_shema["dopolnjevanje"] = "dopolnjevanje.json"
    izhodna_shema["kodiranje"] = "kodiranje.json"
    izhodna_shema["kodirane_znacilke"] = KODIRANE
    izhodna_shema["znacilke_za_model"] = ZNACILKE_ZA_MODEL
    izhodna_shema["skupine_za_model"] = {k: za_model(v) for k, v in shema["skupine_znacilk"].items()}
    izhodna_shema["nabori_za_model"] = {k: za_model(v) for k, v in shema["nabori_znacilk"].items()}
    izhodna_shema["stevilo_znacilk_za_model"] = len(ZNACILKE_ZA_MODEL)
    izhodna_shema["evidenca_delitve"] = "delitev.csv"
    izhodna_shema["opombe_priprave_pred_delitvijo"] = izhodna_shema.pop("opombe")
    izhodna_shema["opombe"] = [
        "Delitev je fiksna in določena pred dopolnjevanjem. Pravila so izključno iz train.",
        "Dopolnjene so samo značilke, cilj in metapodatki ostanejo nespremenjeni.",
        "Besedilne značilke so ohranjene in dodatno kodirane v stolpce 0/1; kategorije so izključno iz train.",
        "Značilke niso skalirane; napovedni model ni naučen.",
        "Test je tehnično pripravljen, vendar ga ne uporabljamo za izbor modelov ali nastavitev.",
        "Za CV obnovimo nedopolnjene učne vrstice iz vhoda; pripravo ponovno učimo znotraj vsakega kroga.",
    ]
    opis_stolpca = {r["stolpec"]: r for r in izhodna_shema["stolpci"]}
    for c, stolpci in KODIRANE.items():
        for s, k in zip(stolpci, kodiranje["stolpci"][c]["kategorije"] + [kodiranje["skupna_kategorija"]]):
            izhodna_shema["stolpci"].append({"stolpec": s, "vloga": "znacilka", "dtype": "int8", "manjkajocih": 0,
                "opis": f"1 = {c} je {k}; 0 = ni.", "vir": c, "skupina": opis_stolpca[c]["skupina"]})
    for r in izhodna_shema["stolpci"]:
        r["manjkajocih_v_vhodu"] = r.pop("manjkajocih")
        r["dtype"] = str(koncne["train"][r["stolpec"]].dtype)
        r["manjkajocih_po_zbirkah"] = {ime: int(df[r["stolpec"]].isna().sum()) for ime, df in koncne.items()}

    izhod.mkdir(parents=True, exist_ok=True)
    for ime, df in koncne.items():
        df[stolpci_izhoda].to_csv(izhod / f"{ime}.csv", index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
    evidenca.to_csv(izhod / "delitev.csv", index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
    for ime, vsebina in [("dopolnjevanje.json", pravila), ("kodiranje.json", kodiranje), ("shema.json", izhodna_shema)]:
        (izhod / ime).write_text(json.dumps(vsebina, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return izhodna_shema


# ---------------------------------------------------------------------------
# Zagon
# ---------------------------------------------------------------------------

def main():
    from utils.modeliranje import poskrbi_za_modeliranje

    poskrbi_za_modeliranje(IME)


if __name__ == "__main__":
    main()
