"""La transmission Klaxo-3 : la récupérer, l'ouvrir, la typer.

Même fichier qu'à la partie 1 : 88 875 relevés, 11 colonnes, aucune ligne d'en-tête.
Il ne se commite pas, il se télécharge.
"""

import csv
import os
import urllib.request

import polars as pl

URL = (
    "https://raw.githubusercontent.com/planetsig/ufo-reports/master/csv-data/"
    "ufo-complete-geocoded-time-standardized.csv"
)
CSV = "releves_klaxo3.csv"

# Le fichier est livré sans en-tête : on la fournit à la lecture.
COLONNES = [
    "datetime",
    "city",
    "state",
    "country",
    "shape",
    "duration_seconds",
    "duration_hours_min",
    "comments",
    "date_posted",
    "latitude",
    "longitude",
]

NUMERIQUES = ["duration_seconds", "latitude", "longitude"]


def recuperer(chemin=CSV):
    if os.path.exists(chemin):
        print(f"{chemin} déjà présent ({os.path.getsize(chemin) / 1e6:.1f} Mo)")
        return chemin
    print(f"Téléchargement depuis {URL}")
    urllib.request.urlretrieve(URL, chemin)
    print(f"Reçu : {os.path.getsize(chemin) / 1e6:.1f} Mo")
    return chemin


def ouvrir(chemin=CSV, bavard=True):
    """Charge tout le fichier en chaînes de caractères, sans rien perdre en silence.

    Parcours manuel plutôt qu'un read_csv tolérant : les lignes qui n'ont pas
    11 champs sont comptées et rendues, pas escamotées.
    """
    conformes, rejets = [], []
    with open(chemin, encoding="utf-8", errors="replace", newline="") as f:
        for numero, champs in enumerate(csv.reader(f), start=1):
            if len(champs) == len(COLONNES):
                conformes.append(champs)
            else:
                rejets.append((numero, champs))

    df = pl.DataFrame(
        conformes, schema={col: pl.String for col in COLONNES}, orient="row"
    )
    if bavard:
        total = df.height + len(rejets)
        print(f"Chargés : {df.height}   mis à part : {len(rejets)}   total : {total}")
    return df, rejets


def conversions(avec_recuperation=True):
    """Les expressions de typage, sans rien afficher.

    Un relevé neuf doit pouvoir emprunter exactement le même chemin que le fichier
    d'origine : ces expressions sont la seule définition du typage du projet.
    """
    expressions = {col: pl.col(col).cast(pl.Float64, strict=False) for col in NUMERIQUES}
    expressions["datetime"] = pl.col("datetime").str.to_datetime(
        "%m/%d/%Y %H:%M", strict=False
    )
    # date_posted n'a pas d'heure : une vraie date, pas un datetime à minuit.
    expressions["date_posted"] = pl.col("date_posted").str.to_date(
        "%m/%d/%Y", strict=False
    )
    if avec_recuperation:
        # « 24:00 » n'existe pas pour polars ; c'est minuit le lendemain.
        expressions["datetime"] = (
            pl.when(pl.col("datetime").str.contains(" 24:"))
            .then(
                pl.col("datetime")
                .str.replace(" 24:", " 00:")
                .str.to_datetime("%m/%d/%Y %H:%M", strict=False)
                .dt.offset_by("1d")
            )
            .otherwise(expressions["datetime"])
        )
    return expressions


def typer(df):
    """Chaque champ dans son vrai type. Aucune ligne supprimée ici."""
    return df.with_columns(**conversions())


def charger(chemin=CSV, bavard=True):
    """Le chemin complet : récupération, ouverture, typage. Rendu tel quel."""
    recuperer(chemin)
    df, rejets = ouvrir(chemin, bavard=bavard)
    return typer(df), rejets
