"""Pripravi podatke Telekom za modele in jih shrani v mapo data/pripravljeno/.

Zagon v terminalu, iz mape repozitorija:

    python -m utils.pripravi_telekom

Skripta naredi isto kot zvezka A1_Priprava_Telekom in A1_Delitev_in_manjkajoce_Telekom
(mapa 03_Uvod_v_strojno_ucenje/notebooks), brez raziskovanja, grafov in vmesnih izpisov:

    1. prebere surove podatke in izbere stolpce,
    2. jih očisti in doda izpeljane značilke,
    3. razdeli vrstice na učno, validacijsko in testno množico (60 / 20 / 20, seme 42),
    4. dopolni manjkajoče vrednosti z mediano učne množice,
    5. besedilne stolpce dodatno zapiše kot stolpce 0/1,
    6. shrani tabele train.csv, val.csv in test.csv v data/pripravljeno/delitve/telekom/.

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
from sklearn.model_selection import train_test_split

KOREN = Path(__file__).resolve().parents[1]          # mapa repozitorija
sys.path.insert(0, str(KOREN))                       # da Python najde mapo utils

from utils.orodja import TELEKOM_STOLPCI

IME, KLJUC, CILJ = "telekom", "id_stranke", "odhod"
META, DATUMI = [KLJUC], []
SEME = 42                                            # isto seme povsod: vsi dobimo isto delitev
DELEZ_TRAIN, DELEZ_VAL, DELEZ_TEST = 0.60, 0.20, 0.20
NAJMANJ_VRSTIC = 100                                 # kategorija z manj učnimi vrsticami gre v stolpec DRUGO


# ---------------------------------------------------------------------------
# 1. del: čista tabela (zvezek A1_Priprava_Telekom)
# ---------------------------------------------------------------------------

def razmerje(stevec, imenovalec):
    return stevec / imenovalec.where(imenovalec.gt(0))


def kazalnik(pogoj, znano):
    return pogoj.astype(float).where(znano)


def pripravi_tabelo(data):
    """Ena vrstica = en naročnik. Vrne čisto tabelo in njeno shemo (opis stolpcev)."""
    # Naložimo in preverimo ključe.
    surovi = pd.read_csv(data / "telekom_izvirni.csv", dtype={"Customer_ID": "string"})
    surovi = surovi.drop_duplicates().copy()
    surovi["Customer_ID"] = surovi["Customer_ID"].str.strip().replace("", pd.NA)
    assert not surovi.loc[surovi["Customer_ID"].notna(), "Customer_ID"].duplicated().any(), "Nasprotujoči zapisi iste stranke."
    surovi["churn"] = pd.to_numeric(surovi["churn"], errors="coerce")
    veljavno = surovi["Customer_ID"].notna() & surovi["churn"].isin([0, 1])
    surovi = surovi.loc[veljavno].copy()

    # Izberemo širši, razumljiv nabor stolpcev.
    osnovni_slovar = {ime: (vir, opis) for ime, (vir, opis) in TELEKOM_STOLPCI.items()
                      if ime not in ["id_stranke", "odhod"]}
    osnovni_slovar["sprememba_minut"] = ("change_mou", "Sprememba minut; ohranimo izvorno mero, ne trdimo, da je odstotek.")
    osnovni_slovar["povp_gostovanje"] = ("roam_Mean", "Izvorni povprečni agregat gostovanja; enoto preverimo v podatkovnem viru.")
    dodatni_slovar = {
        "povp_minute_3m": ("avg3mou", "Povprečne mesečne minute v 3-mesečnem agregatu."),
        "povp_prihodek_3m": ("avg3rev", "Povprečni mesečni prihodek v 3-mesečnem agregatu, USD."),
        "povp_prihodek_6m": ("avg6rev", "Povprečni mesečni prihodek v 6-mesečnem agregatu, USD."),
        "povp_klici_3m": ("avg3qty", "Povprečno število klicev v 3-mesečnem agregatu."),
        "povp_klici_6m": ("avg6qty", "Povprečno število klicev v 6-mesečnem agregatu."),
        "sprememba_prihodka": ("change_rev", "Izvorna sprememba prihodka; lahko je negativna."),
        "aktivne_narocnine": ("actvsubs", "Število aktivnih naročnin."),
        "stevilo_modelov_telefonov": ("models", "Število modelov telefonov, ki jih je stranka imela."),
        "obnovljena_naprava": ("refurb_new", "Izvorna koda nove oziroma obnovljene naprave (N/R)."),
        "povp_blokirani_klici": ("blck_vce_Mean", "Povprečno število blokiranih glasovnih klicev."),
        "povp_odhodni_klici": ("plcd_vce_Mean", "Povprečno število poskusov odhodnih glasovnih klicev."),
        "povp_dohodni_klici": ("recv_vce_Mean", "Povprečno število prejetih glasovnih klicev."),
        "povp_uspesni_klici": ("comp_vce_Mean", "Povprečno število vzpostavljenih odhodnih glasovnih klicev."),
        "povp_minute_konice": ("mou_peav_Mean", "Povprečne glasovne minute v konici."),
        "povp_minute_izven_konic": ("mou_opkv_Mean", "Povprečne glasovne minute zunaj konice."),
        "povp_klici_konice": ("peak_vce_Mean", "Povprečno število glasovnih klicev v konici."),
        "povp_klici_izven_konic": ("opk_vce_Mean", "Povprečno število glasovnih klicev zunaj konice."),
    }
    slovar_vhodov = osnovni_slovar | dodatni_slovar
    preimenovanje = {vir: ime for ime, (vir, _) in slovar_vhodov.items()}
    tabela = surovi[["Customer_ID", "churn", *preimenovanje]].rename(
        columns={"Customer_ID": "id_stranke", "churn": "odhod", **preimenovanje}).copy()
    tabela["odhod"] = tabela["odhod"].astype("int8")

    # Slovar značilk izvozimo skupaj s tabelo.
    opisi = {}
    skupine = {}

    def dodaj(ime, vrednosti, skupina, opis, vir):
        tabela[ime] = vrednosti
        skupine.setdefault(skupina, []).append(ime)
        opisi[ime] = {"opis": opis, "vir": vir, "skupina": skupina}

    kat_stolpci = ["regija", "zakonski_stan", "splet_na_napravi", "dualband", "obnovljena_naprava"]
    num_stolpci = [c for c in slovar_vhodov if c not in kat_stolpci]
    naprava = {"cena_naprave", "dni_z_napravo", "stevilo_telefonov", "stevilo_modelov_telefonov",
               "splet_na_napravi", "dualband", "obnovljena_naprava"}
    demografija = {"zakonski_stan", "dohodek_razred", "stevilo_avtomobilov"}
    prihodki = {"povp_mesecni_prihodek", "povp_mesecna_narocnina", "povp_prihodek_3m",
                "povp_prihodek_6m", "sprememba_prihodka"}
    razmerje_narocnika = {"mesecev_narocnine", "stevilo_narocnin", "aktivne_narocnine", "regija"}
    for ime, (vir, opis) in slovar_vhodov.items():
        skupina = ("naprava" if ime in naprava else "demografija" if ime in demografija else
                   "prihodki" if ime in prihodki else "narocnisko_razmerje" if ime in razmerje_narocnika else "poraba_in_klici")
        dodaj(ime, tabela[ime], skupina, opis, vir)

    # Poenotimo manjkajoče vrednosti in preverimo domenske omejitve.
    for c in kat_stolpci:
        tabela[c] = tabela[c].astype("string").str.strip().str.upper().replace("", pd.NA)
    for c, oznake in {"zakonski_stan": ["U"], "dualband": ["U"], "splet_na_napravi": ["UNKW"]}.items():
        tabela[c] = tabela[c].replace(oznake, pd.NA)
    for c in num_stolpci:
        tabela[c] = pd.to_numeric(tabela[c], errors="coerce").replace([np.inf, -np.inf], np.nan)

    # Izjeme so spremembe in prihodki, ne števci/trajanja.
    lahko_negativni = {"sprememba_minut", "sprememba_prihodka", "povp_mesecni_prihodek",
                       "povp_prihodek_3m", "povp_prihodek_6m"}
    for c in num_stolpci:
        napaka = tabela[c].lt(0) if c not in lahko_negativni else pd.Series(False, index=tabela.index)
        if c == "dohodek_razred":
            napaka = tabela[c].notna() & (~tabela[c].between(1, 9) | tabela[c].mod(1).ne(0))
        tabela[c] = tabela[c].mask(napaka)

    # Izpeljane značilke.
    razmerja = [
        ("razmerje_minut_3m_6m", "povp_minute_3m", "povp_minute_6m"),
        ("razmerje_prihodka_3m_6m", "povp_prihodek_3m", "povp_prihodek_6m"),
        ("razmerje_klicev_3m_6m", "povp_klici_3m", "povp_klici_6m"),
        ("razmerje_minut_trenutno_6m", "povp_minute", "povp_minute_6m"),
        ("prihodek_na_minuto", "povp_mesecni_prihodek", "povp_minute"),
    ]
    for ime, stevec, imenovalec in razmerja:
        dodaj(ime, razmerje(tabela[stevec], tabela[imenovalec]), "izpeljane",
              f"Razmerje {stevec} / {imenovalec}; NaN pri nepozitivnem ali neznanem imenovalcu.", f"{stevec}, {imenovalec}")
    for ime, a, b in [("razlika_minut_3m_6m", "povp_minute_3m", "povp_minute_6m"),
                      ("razlika_prihodka_3m_6m", "povp_prihodek_3m", "povp_prihodek_6m")]:
        dodaj(ime, tabela[a] - tabela[b], "izpeljane", f"Razlika {a} − {b}.", f"{a}, {b}")
    dodaj("delez_minut_konice", razmerje(tabela["povp_minute_konice"],
          tabela["povp_minute_konice"] + tabela["povp_minute_izven_konic"]), "izpeljane",
          "Delež minut v konici med minutami v konici in zunaj nje.", "mou_peav_Mean, mou_opkv_Mean")
    dodaj("stik_s_podporo", kazalnik(tabela["povp_klici_podpora"].gt(0), tabela["povp_klici_podpora"].notna()),
          "izpeljane", "1 = pozitiven agregat stikov s podporo; neznano ostane NaN.", "custcare_Mean")
    dodaj("brez_porabe_minut", kazalnik(tabela["povp_minute"].eq(0), tabela["povp_minute"].notna()),
          "izpeljane", "1 = znana ničelna poraba minut.", "mou_Mean")
    dodaj("trajanje_skupina", pd.cut(tabela["mesecev_narocnine"], [0, 12, 24, np.inf],
          labels=["DO_12", "13_DO_24", "NAD_24"], include_lowest=True).astype("string").fillna("NEZNANO"),
          "izpeljane", "Fiksne skupine trajanja naročnine; izvorne mesece ohranimo.", "months")
    for izvor in ["povp_minute", "cena_naprave", "povp_klici_podpora"]:
        dodaj("log1p_" + izvor, np.log1p(tabela[izvor]), "transformirane",
              "Naravni logaritem (1 + vrednost); brez učenja parametrov.", izvor)
    dodaj("predznacen_log_prihodka", np.sign(tabela["povp_mesecni_prihodek"]) * np.log1p(tabela["povp_mesecni_prihodek"].abs()),
          "transformirane", "Predznačeni logaritem ohrani tudi negativne prihodke.", "rev_Mean")

    # Ohranimo informacijo o manjkanju.
    spremljaj_manjkanje = ["povp_minute", "povp_minute_6m", "povp_prihodek_6m", "dni_z_napravo",
        "povp_mesecna_narocnina", "dohodek_razred", "stevilo_avtomobilov", "zakonski_stan",
        "splet_na_napravi", "regija", "razmerje_minut_3m_6m", "prihodek_na_minuto"]
    for c in spremljaj_manjkanje:
        dodaj(c + "_manjka", tabela[c].isna().astype("int8"), "manjkanje",
              "1 = manjka ali je po čiščenju nedoločeno; 0 = znano.", c)
    for c in kat_stolpci:
        tabela[c] = tabela[c].fillna("NEZNANO")

    # Nabori značilk za kasnejše poskuse.
    opisi[KLJUC] = {"opis": "ID naročnika; samo povezava, ni vhod v model.", "vir": "Customer_ID", "skupina": "metapodatki"}
    opisi[CILJ] = {"opis": "Oznaka odhoda 0/1; časovni horizont ni potrjen.", "vir": "churn", "skupina": "cilj"}
    vse = [c for v in skupine.values() for c in v]
    nabori = {
        "osnovni": ["mesecev_narocnine", "povp_minute", "povp_mesecni_prihodek", "povp_klici_podpora", "dni_z_napravo", "regija"],
        "izvorni": list(slovar_vhodov),
        "brez_demografije": [c for c in vse if c not in skupine["demografija"] and
            c not in [d + "_manjka" for d in skupine["demografija"]]],
        "vsi": vse,
    }
    izloceni = sorted(set(surovi.columns) - set(preimenovanje) - {"Customer_ID", "churn"})
    opombe = ["Ni delitve, imputacije z naučeno statistiko, kodiranja, skaliranja ali modela.",
        "NaN so namerno ohranjeni; mediane in kodiranje določimo po delitvi.",
        "Časovni horizont in časovna dostopnost agregatov v izvozu nista potrjena.",
        "Veljavnih ekstremov ne režemo; negativne prihodke ohranimo, negativno redno naročnino označimo kot manjkajočo."]
    assert tabela["odhod"].isin([0, 1]).all()
    assert tabela["dni_z_napravo"].dropna().ge(0).all()
    assert tabela["delez_minut_konice"].dropna().between(0, 1).all()

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
# 2. del: delitev, manjkajoče vrednosti in stolpci 0/1 (zvezek A1_Delitev_in_manjkajoce_Telekom)
# ---------------------------------------------------------------------------

def razdeli(podatki):
    """Stratificirana naključna delitev 60 / 20 / 20. Vrne vlogo vsake vrstice."""
    train_i, ostalo_i = train_test_split(podatki.index,
        test_size=DELEZ_VAL + DELEZ_TEST, stratify=podatki[CILJ], random_state=SEME)
    val_i, test_i = train_test_split(ostalo_i,
        test_size=DELEZ_TEST / (DELEZ_VAL + DELEZ_TEST),
        stratify=podatki.loc[ostalo_i, CILJ], random_state=SEME)
    vloge = pd.Series("", index=podatki.index, dtype="string")
    for ime, indeksi in [("train", train_i), ("val", val_i), ("test", test_i)]:
        vloge.loc[indeksi] = ime
    razlogi = pd.Series("vkljuceno", index=podatki.index, dtype="string")
    parametri = {"metoda": "stratificirana_nakljucna", "seme": SEME,
        "delezi": {"train": DELEZ_TRAIN, "val": DELEZ_VAL, "test": DELEZ_TEST}, "stratifikacija": CILJ}
    assert vloge.ne("").all()
    return vloge, razlogi, parametri


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
    """Prebere čisto tabelo, jo razdeli, dopolni, kodira in shrani train.csv, val.csv, test.csv."""
    shema = json.loads(pot_sheme.read_text(encoding="utf-8"))
    ZNACILKE = shema["znacilke"]
    NUM = shema["numericne_znacilke"]
    KAT = shema["kategoricne_znacilke"]
    tipi = {r["stolpec"]: r["dtype"] for r in shema["stolpci"] if r["stolpec"] not in DATUMI}
    podatki = pd.read_csv(pot_csv, dtype=tipi, parse_dates=DATUMI,
        keep_default_na=False, na_values=[""])
    assert podatki[KLJUC].notna().all() and podatki[KLJUC].is_unique
    assert podatki[CILJ].notna().all(), "Cilja ne dopolnjujemo."

    # Najprej delitev. Stabilen vrstni red pomeni, da preurejanje CSV-ja ne spremeni delitve.
    podatki = podatki.sort_values(KLJUC).reset_index(drop=True)
    vloge, razlogi, parametri_delitve = razdeli(podatki)
    zbirke_pred = {ime: podatki.loc[vloge.eq(ime)].copy() for ime in ["train", "val", "test"]}
    kljuci = {ime: set(df[KLJUC]) for ime, df in zbirke_pred.items()}
    assert kljuci["train"].isdisjoint(kljuci["val"])
    assert kljuci["train"].isdisjoint(kljuci["test"])
    assert kljuci["val"].isdisjoint(kljuci["test"])
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
