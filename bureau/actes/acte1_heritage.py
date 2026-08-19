"""Acte 1 — l'héritage.

Phase 0 : refaire les calculs du disparu. Phase 1 : dire ce qu'ils ne disaient pas.
"""

import polars as pl

from bureau import figures
from bureau.contexte import a_faire, titre

# Les quatre affirmations laissées sur le bureau. Elles sont justes : le code doit
# retomber dessus, sans les recopier. Servent de contrôle, pas de source.
DOSSIER_DU_DISPARU = {
    "jours couverts": 8894,
    "relevés par jour": 9.2,
    "un 4 juillet": 51,
    "samedi %": 17.7,
    "lundi %": 12.6,
    "juillet %": 11.3,
    "février %": 6.2,
}

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]


def nombre_de_4_juillet(premier, dernier):
    """Combien de 4 juillet la période contient réellement."""
    import datetime

    return sum(
        1
        for annee in range(premier.year, dernier.year + 1)
        if premier <= datetime.date(annee, 7, 4) <= dernier
    )


def phase00(dossier):
    """Refaire les calculs du disparu.

    Deux dates dans la transmission : celle de l'observation (`datetime`) et celle
    de la publication (`date_posted`). Le dossier ne dit pas laquelle il a utilisée.
    On travaille sur `datetime` : la recommandation porte sur le jour où la
    population regarde le ciel, pas sur le jour où le Bureau a saisi le formulaire.
    À écrire tel quel dans le rapport, avec la raison.
    """
    titre(0, "refaire les calculs du disparu")

    observations = (
        dossier.df.select(pl.col("datetime"))
        .drop_nulls()
        .filter(pl.col("datetime").dt.year() >= 1990)
        .with_columns(jour=pl.col("datetime").dt.date())
    )

    premier, dernier = observations["jour"].min(), observations["jour"].max()
    couverture = (dernier - premier).days + 1
    total = observations.height

    print(f"  date retenue            : datetime (l'observation), pas date_posted")
    print(f"  période                 : {premier} → {dernier}")
    print(f"  jours couverts          : {couverture}")
    print(f"  relevés retenus         : {total}")
    print(f"  moyenne par jour        : {total / couverture:.1f}")

    # Le 4 juillet : la moyenne d'un 4 juillet, pas le total sur 25 ans.
    # Le dénominateur est le nombre de 4 juillet COUVERTS par la période, pas le
    # nombre d'années où il s'est trouvé un relevé ce jour-là : une année sans
    # relevé le 4 juillet est un 4 juillet à zéro, elle compte dans la moyenne.
    # La transmission s'arrêtant le 8 mai 2014, le 4 juillet 2014 n'existe pas.
    quatre_juillet = observations.filter(
        (pl.col("datetime").dt.month() == 7) & (pl.col("datetime").dt.day() == 4)
    )
    couverts = nombre_de_4_juillet(premier, dernier)
    print(f"  un 4 juillet moyen      : {quatre_juillet.height / couverts:.0f} "
          f"({quatre_juillet.height} relevés sur {couverts} 4 juillet couverts)")

    parts = {}
    par_jour_semaine = (
        observations.group_by(pl.col("datetime").dt.weekday().alias("jour_semaine"))
        .len()
        .sort("jour_semaine")
    )
    print("\n  part par jour de la semaine :")
    for ligne in par_jour_semaine.iter_rows(named=True):
        nom = JOURS[ligne["jour_semaine"] - 1]
        parts[nom] = 100 * ligne["len"] / total
        print(f"    {nom:<10} {parts[nom]:5.1f} %")

    par_mois = (
        observations.group_by(pl.col("datetime").dt.month().alias("mois"))
        .len()
        .sort("mois")
    )
    print("\n  part par mois :")
    for ligne in par_mois.iter_rows(named=True):
        nom = MOIS[ligne["mois"] - 1]
        parts[nom] = 100 * ligne["len"] / total
        print(f"    {nom:<10} {parts[nom]:5.1f} %")

    # Ce que le dossier ne donnait pas : le maximum en une journée, et le rang
    # du 4 juillet dans ce classement.
    par_journee = observations.group_by("jour").len().sort("len", descending=True)
    print(f"\n  maximum en une seule journée : {par_journee['len'][0]} "
          f"le {par_journee['jour'][0]}")

    print("\n  les dix journées les plus chargées :")
    print(f"    {'rang':>4}  {'journée':<12}{'relevés':>9}")
    for rang, ligne in enumerate(par_journee.head(10).iter_rows(named=True), start=1):
        print(f"    {rang:>4}  {str(ligne['jour']):<12}{ligne['len']:>9}")

    rangs = par_journee.with_row_index("rang", offset=1).filter(
        (pl.col("jour").dt.month() == 7) & (pl.col("jour").dt.day() == 4)
    )
    meilleur = rangs.row(0, named=True)
    print(f"\n  meilleur 4 juillet      : {meilleur['jour']} — {meilleur['len']} relevés,"
          f" rang {meilleur['rang']} sur {par_journee.height} journées")

    # « Le volume croît continûment jusqu'à la fin de la transmission » : c'est la
    # seule affirmation du dossier qui dépend de la date choisie. On rend les deux
    # séries, et le rapport dit laquelle le disparu a forcément utilisée.
    par_an = volume_annuel(dossier.df, "datetime")
    par_an_publication = volume_annuel(dossier.df, "date_posted")
    courbe_annuelle(par_an, par_an_publication)

    print("\n  années en baisse d'une année sur l'autre (dernière année exclue,"
          " tronquée) :")
    for intitule, serie in (("observation", par_an), ("publication", par_an_publication)):
        baisses = (serie["len"].head(-1).diff().drop_nulls() < 0).sum()
        verdict = "croît continûment" if baisses == 0 else f"{baisses} baisses"
        print(f"    {intitule:<12} {verdict}")

    confronter(
        {
            "jours couverts": couverture,
            "relevés par jour": total / couverture,
            "un 4 juillet": quatre_juillet.height / couverts,
            "samedi %": parts["samedi"],
            "lundi %": parts["lundi"],
            "juillet %": parts["juillet"],
            "février %": parts["février"],
        }
    )

    return dossier.retenir(
        0,
        couverture=couverture,
        total=total,
        moyenne_par_jour=total / couverture,
        un_4_juillet=quatre_juillet.height / couverts,
        maximum_journalier=int(par_journee["len"][0]),
        rang_4_juillet=int(meilleur["rang"]),
    )


def confronter(obtenus):
    """Nos chiffres contre ceux du dossier. Ils sont justes : on doit tomber dessus."""
    print(f"\n  {'affirmation du dossier':<22}{'lui':>10}{'nous':>10}")
    for intitule, attendu in DOSSIER_DU_DISPARU.items():
        obtenu = obtenus[intitule]
        # Arrondi au même nombre de décimales que le dossier avant de comparer.
        decimales = 0 if float(attendu).is_integer() else 1
        marque = "✓" if round(obtenu, decimales) == round(attendu, decimales) else "✗"
        print(f"  {marque} {intitule:<20}{attendu:>10}{obtenu:>10.{decimales}f}")


def volume_annuel(df, colonne):
    return (
        df.select(pl.col(colonne))
        .drop_nulls()
        .filter(pl.col(colonne).dt.year() >= 1990)
        .group_by(pl.col(colonne).dt.year().alias("annee"))
        .len()
        .sort("annee")
    )


def courbe_annuelle(par_observation, par_publication):
    from matplotlib import pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(par_observation["annee"], par_observation["len"], marker="o",
            linewidth=1.6, label="date d'observation")
    ax.plot(par_publication["annee"], par_publication["len"], marker="s",
            linewidth=1.6, label="date de publication")
    ax.set_xlabel("année")
    ax.set_ylabel("relevés")
    ax.set_title("Volume annuel de relevés de la transmission Klaxo-3")
    ax.legend()
    ax.grid(alpha=0.3)
    figures.poser(fig, "phase00_volume_annuel.png")


def phase01(dossier):
    """Le chiffre était vrai, la flotte est perdue.

    Phase sans code : une page dans RAPPORT.md. Ce qui suit sert à la nourrir —
    trois relevés recopiés tels quels, choisis pour montrer ce qu'un comptage ne
    verra jamais.
    """
    titre(1, "le chiffre était vrai, la flotte est perdue")
    a_faire(
        """
        1. Ce que le chiffre du 4 juillet disait réellement, et les deux ou trois
           autres explications qu'il autorise tout autant.
        2. Trois relevés recopiés tels quels (voir les candidats affichés ci-dessous).
        3. La commande passée au Conseil : la tâche, ce qui entre, ce qui sort —
           en une phrase que le Conseil peut répéter.
        """
    )

    candidats = (
        dossier.df.filter(
            (pl.col("datetime").dt.month() == 7)
            & (pl.col("datetime").dt.day() == 4)
            & pl.col("comments").is_not_null()
            & (pl.col("comments").str.len_chars() > 60)
        )
        .select("datetime", "city", "shape", "comments")
        .head(6)
    )
    print("\n  Candidats du 4 juillet (à trier à la main, pas à recopier en vrac) :")
    for ligne in candidats.iter_rows(named=True):
        print(f"\n    {ligne['datetime']}  {ligne['city']}  [{ligne['shape']}]")
        print(f"    « {ligne['comments']} »")
