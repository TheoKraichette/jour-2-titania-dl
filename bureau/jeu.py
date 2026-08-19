"""Du témoignage brut au premier nombre qui entre dans le réseau.

La tâche de tout le projet : `comments` entre, une forme sort.

État du terrain, donné par l'énoncé et à revérifier par le code : `shape` a
2 922 trous, 29 valeurs distinctes dont 18 dépassent 300 relevés, deux fourre-tout
(`unknown`, `other`) et des doublons de sens (`round`/`circle`, `changed`/`changing`).

Les trois décisions de la phase 3 — trous, fourre-tout, doublons — sont les
constantes ci-dessous. Elles changent le nombre de classes, donc le score : un
score sans le nombre de classes en face ne veut rien dire.
"""

import re

import polars as pl

# --- Décision 1 : les doublons de sens ------------------------------------
# À défendre dans RAPPORT.md. Fusion vers la graphie retenue.
FUSIONS = {
    "round": "circle",
    "changed": "changing",
}

# --- Décision 2 : les fourre-tout -----------------------------------------
FOURRE_TOUT = {"unknown", "other"}

# --- Décision 3 : les trous -----------------------------------------------
# Les relevés sans forme n'ont pas d'étiquette à apprendre : ils sortent du jeu
# supervisé. Ils restent disponibles pour l'acte 4 (recherche sur le fichier entier).

SEUIL_CLASSE = 300  # sous ce compte, la classe est trop rare pour être apprise


def normaliser_forme(colonne=pl.col("shape")):
    """Minuscules, espaces retirés, doublons fusionnés. Aucune suppression ici."""
    forme = colonne.str.strip_chars().str.to_lowercase()
    for source, cible in FUSIONS.items():
        forme = pl.when(forme == source).then(pl.lit(cible)).otherwise(forme)
    return forme


JETON = re.compile(r"[a-z']+")
ENTITE = re.compile(r"&#?\w+;?")


def nettoyer(texte):
    """Le service de transmission a laissé passer des entités HTML.

    Les virgules des témoignages arrivent en « &#44 », souvent sans point-virgule
    final — html.unescape n'en voit que la moitié. Elles sont retirées avant le
    découpage, sinon elles se retrouvent dans le vocabulaire.
    """
    import html

    return ENTITE.sub(" ", html.unescape(texte or ""))


def jetons(texte):
    """Le découpage du projet, utilisé de la phase 3 à la phase 13.

    Volontairement simple et lisible : le Conseil doit pouvoir suivre le trajet
    du texte brut jusqu'au premier nombre. L'acte 4 utilisera le découpage du
    modèle emprunté, ce qui est un changement à documenter.
    """
    return JETON.findall(nettoyer(texte).lower())


def construire(df, garder_fourre_tout=False, seuil=SEUIL_CLASSE):
    """Le jeu supervisé : un témoignage, une forme, rien d'autre.

    Rend (textes, etiquettes, classes) où `classes` est la liste ordonnée des
    noms de formes retenus — l'indice dans cette liste est l'étiquette entière.
    """
    jeu = (
        df.select(
            texte=pl.col("comments").str.strip_chars(),
            forme=normaliser_forme(),
        )
        .filter(pl.col("forme").is_not_null() & (pl.col("forme") != ""))
        .filter(pl.col("texte").is_not_null() & (pl.col("texte") != ""))
    )
    if not garder_fourre_tout:
        jeu = jeu.filter(~pl.col("forme").is_in(list(FOURRE_TOUT)))

    comptes = jeu["forme"].value_counts(sort=True)
    classes = comptes.filter(pl.col("count") >= seuil)["forme"].to_list()
    jeu = jeu.filter(pl.col("forme").is_in(classes))

    index = {nom: i for i, nom in enumerate(classes)}
    return (
        jeu["texte"].to_list(),
        [index[nom] for nom in jeu["forme"]],
        classes,
    )


def mots_interdits(classes):
    """Phase 8 : le vocabulaire des formes, que la machine n'a pas le droit de lire.

    Les valeurs de `shape`, leurs variantes d'écriture, leurs pluriels, et tout ce
    que la fusion des doublons a produit. La liste part dans le rapport, et le code
    doit prouver qu'il en reste zéro dans le texte traité.
    """
    interdits = set()
    for nom in list(classes) + list(FUSIONS) + list(FOURRE_TOUT):
        mot = nom.lower()
        interdits.update({mot, mot + "s", mot + "es"})
        if mot.endswith("e"):
            interdits.add(mot[:-1] + "ing")  # change → changing
    # TODO phase 8 : compléter à la main les variantes que la morphologie rate
    # (lights/lighted, fire ball, cigar-shaped, triangular…), les défendre dans
    # le rapport, puis vérifier par le code qu'il en reste zéro.
    return interdits


class Vocabulaire:
    """Les mots que le réseau connaît, et rien d'autre.

    Construit sur la seule partie apprentissage : un mot vu pour la première fois
    en validation ou en test doit tomber sur « inconnu », sinon la découpe fuit.
    """

    VIDE, INCONNU = 0, 1

    def __init__(self, textes, minimum=2, taille_max=20000):
        from collections import Counter

        comptes = Counter(mot for texte in textes for mot in jetons(texte))
        retenus = [
            mot
            for mot, compte in comptes.most_common(taille_max)
            if compte >= minimum
        ]
        self.mots = ["<vide>", "<inconnu>"] + retenus
        self.index = {mot: i for i, mot in enumerate(self.mots)}

    def __len__(self):
        return len(self.mots)

    def encoder(self, texte, longueur):
        """Un texte, une suite d'indices de longueur fixe. Le premier nombre qui
        entre dans le réseau — c'est ce trajet que la phase 3 demande de montrer."""
        indices = [self.index.get(mot, self.INCONNU) for mot in jetons(texte)][:longueur]
        return indices + [self.VIDE] * (longueur - len(indices))


def en_tenseurs(textes, etiquettes, vocabulaire, longueur):
    import torch

    entrees = torch.tensor(
        [vocabulaire.encoder(texte, longueur) for texte in textes], dtype=torch.long
    )
    return entrees, torch.tensor(etiquettes, dtype=torch.long)


def lots(entrees, cibles, taille=64, melanger=True, graine=0):
    """Un itérable rejouable de (entrées, cibles).

    Rejouable et pas générateur : la boucle d'entraînement le parcourt à chaque
    passage. La taille de lot est un réglage à part entière — la phase 7 la
    descend à 4 et regarde ce qui casse.
    """
    import torch

    class Lots:
        def __iter__(self):
            if melanger:
                generateur = torch.Generator().manual_seed(graine)
                ordre = torch.randperm(len(cibles), generator=generateur)
            else:
                ordre = torch.arange(len(cibles))
            for debut in range(0, len(ordre), taille):
                tranche = ordre[debut : debut + taille]
                yield entrees[tranche], cibles[tranche]

        def __len__(self):
            return (len(cibles) + taille - 1) // taille

    return Lots()


def decouper(nombre, part_validation=0.15, part_test=0.15, graine=0):
    """Une découpe unique, tirée une fois, réutilisée par toutes les phases.

    Les scores de la phase 3, 5, 6, 7, 8 et 14 se comparent entre eux : ils
    doivent porter sur exactement la même découpe et exactement les mêmes classes.
    """
    import torch

    generateur = torch.Generator().manual_seed(graine)
    melange = torch.randperm(nombre, generator=generateur).tolist()
    n_test = int(nombre * part_test)
    n_validation = int(nombre * part_validation)
    return {
        "test": melange[:n_test],
        "validation": melange[n_test : n_test + n_validation],
        "apprentissage": melange[n_test + n_validation :],
    }
