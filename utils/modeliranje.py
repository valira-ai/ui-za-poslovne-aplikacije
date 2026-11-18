"""Skupna priprava in branje podatkov za drugi modul.

Postopki čiščenja in delitve so prikazani v zvezkih 01_priprava_podatkov in
02_preverjanje_modela; njihova izvedba je v utils/pripravi_{telekom,olist}.py.
Priprava shrani tudi testno množico, branje pa odpre samo zahtevano tabelo.
"""

import importlib
import json
from pathlib import Path

import pandas as pd

from utils import orodja


def preberi_shemo(pot):
    """Prebere opis stolpcev, značilk in priprave iz datoteke JSON."""
    return json.loads(Path(pot).read_text(encoding="utf-8"))


def preberi_tabelo(pot, shema, *, stolpci=None):
    """Prebere samo izbrani CSV s tipi, datumi in manjkajočimi vrednostmi iz sheme.

    Besedilo, kot sta 'NA' in 'NULL', ostane besedilo; manjkajoča je prazna
    vrednost. Identifikatorji ostanejo nizi, vključno z začetnimi ničlami.
    Funkcija ne pripravlja podatkov in ne odpira drugih množic.
    """
    datumi = [s for s in shema["datumski_stolpci"] if stolpci is None or s in stolpci]
    tipi = {s["stolpec"]: s["dtype"] for s in shema["stolpci"]
            if s["stolpec"] not in shema["datumski_stolpci"]
            and (stolpci is None or s["stolpec"] in stolpci)}
    return pd.read_csv(pot, dtype=tipi, parse_dates=datumi, usecols=stolpci,
                       keep_default_na=False, na_values=[""])


def _so_sveze(izhodi, vhodi):
    najnovejsi_vhod = max(p.stat().st_mtime_ns for p in vhodi)
    return all(p.is_file() and p.stat().st_mtime_ns >= najnovejsi_vhod for p in izhodi)


def poskrbi_za_modeliranje(zbirka, *, delitve=True):
    """Pripravi manjkajoče ali zastarele podatke in vrne mapo z izhodi.

    zbirka: 'telekom' ali 'olist'. Privzeto vrne mapo s train/val/test in
    shema.json. Z delitve=False pripravi samo čisto tabelo in njeno shemo,
    brez delitve, dopolnjevanja ali kodiranja (za prikaza delitve).
    Že veljavni izhodi ostanejo nespremenjeni. Nobenega testnega CSV-ja ne bere.
    """
    if zbirka not in ("telekom", "olist"):
        raise ValueError("Zbirka mora biti 'telekom' ali 'olist'.")
    skripta = importlib.import_module(f"utils.pripravi_{zbirka}")
    data = orodja.poskrbi_za_podatke()
    pripravljeno = data / "pripravljeno"
    pot_csv = pripravljeno / f"{zbirka}_modeliranje.csv"
    pot_sheme = pripravljeno / f"{zbirka}_shema.json"
    vhodi = [Path(__file__), Path(orodja.__file__), Path(skripta.__file__)]
    vhodi += ([data / "telekom_izvirni.csv"] if zbirka == "telekom" else
              [data / "trgovina" / ime for ime in orodja.TRGOVINA_TABELE])

    if not _so_sveze([pot_csv, pot_sheme], vhodi):
        tabela, shema = skripta.pripravi_tabelo(data)
        pripravljeno.mkdir(parents=True, exist_ok=True)
        tabela.to_csv(pot_csv, index=False, encoding="utf-8", date_format="%Y-%m-%d %H:%M:%S")
        pot_sheme.write_text(json.dumps(shema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Čista tabela {zbirka}: {len(tabela)} vrstic -> {pot_csv}")
    if not delitve:
        return pripravljeno

    izhod = pripravljeno / "delitve" / zbirka
    datoteke = [izhod / ime for ime in (
        "train.csv", "val.csv", "test.csv", "delitev.csv",
        "dopolnjevanje.json", "kodiranje.json", "shema.json",
    )]
    if not _so_sveze(datoteke, vhodi + [pot_csv, pot_sheme]):
        shema = skripta.razdeli_in_shrani(pot_csv, pot_sheme, izhod)
        print(f"Delitev {zbirka}: {shema['vrstice_po_zbirkah']}")
    print(f"Podatki za modeliranje so pripravljeni v: {izhod}")
    return izhod
