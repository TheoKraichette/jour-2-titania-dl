"""Acte 3 — le Bureau apprend à relire.

Le mécanisme d'attention, écrit à la main. Droit aux tenseurs et aux opérations de
base : produits matriciels, softmax, couches linéaires. Exclus : les blocs tout
prêts, tout ce qui porte déjà le mot « attention » dans son nom, et les
bibliothèques de modèles préentraînés.

    scores = questions @ etiquettes.transpose(-2, -1) / dimension ** 0.5
    poids  = torch.softmax(scores, dim=-1)
    sortie = poids @ contenus

La division par la racine de la dimension ne se saute pas.
"""

import torch
from torch import nn

from bureau import entrainement, figures, jeu, modeles
from bureau.contexte import a_faire, titre

DIMENSION = 32
PRONOMS = ("it", "they", "she", "he", "them")
ANTECEDENTS = ("object", "light", "craft", "orb", "ufo", "sphere", "ball",
               "thing", "lights", "objects")


def relever_un_temoignage(dossier):
    """Un vrai relevé du fichier, avec un pronom ET son antécédent probable.

    Jamais une phrase inventée : on parcourt le jeu dans l'ordre et on prend le
    premier témoignage de taille lisible où un pronom suit un nom d'objet.
    """
    for indice in range(len(dossier.textes)):
        mots = jeu.jetons(dossier.textes[indice])
        if not 8 <= len(mots) <= 14:
            continue
        noms = [i for i, m in enumerate(mots) if m in ANTECEDENTS]
        pronoms = [i for i, m in enumerate(mots) if m in PRONOMS]
        if noms and pronoms and pronoms[-1] > noms[0]:
            return indice, mots, noms[0], pronoms[-1]
    raise RuntimeError("aucun relevé avec pronom et antécédent — impossible ici")


def vecteurs_d_entree(dossier, mots):
    """Les vecteurs d'entrée du relevé : un vecteur appris (non entraîné) par mot."""
    entrainement.fixer_graine(dossier.graine)
    table = nn.Embedding(len(dossier.vocabulaire), DIMENSION)
    indices = torch.tensor([[dossier.vocabulaire.index.get(m, 1) for m in mots]])
    return table(indices)


def phase10(dossier):
    """Chaque mot interroge les autres.

    Une seule tête, entièrement à la main : trois vecteurs par mot, les scores,
    leur transformation en proportions, le mélange des contenus. Le modèle n'est
    pas entraîné — ce qu'on rend, c'est le mécanisme, pas les valeurs.
    """
    titre(10, "chaque mot interroge les autres")

    indice, mots, i_nom, i_pronom = relever_un_temoignage(dossier)
    print(f"  relevé n° {indice} du jeu : « {dossier.textes[indice][:90]} »")
    print(f"  jetons : {mots}")
    print(f"  la reprise : « {mots[i_pronom]} » (position {i_pronom + 1}) renvoie à "
          f"« {mots[i_nom]} » (position {i_nom + 1})")

    entree = vecteurs_d_entree(dossier, mots)
    tete = modeles.UneTete(DIMENSION)
    with torch.no_grad():
        sortie, poids = tete(entree)
    poids = poids.squeeze(0)

    # Les trois vérifications de l'énoncé.
    sommes = poids.sum(dim=-1)
    print(f"\n  chaque ligne somme à un : écart maximal "
          f"{(sommes - 1).abs().max().item():.2e}")
    print(f"  la sortie a la même forme que l'entrée : "
          f"{tuple(sortie.shape)} = {tuple(entree.shape)} → "
          f"{tuple(sortie.shape) == tuple(entree.shape)}")
    print(f"\n  la case du pronom : ligne « {mots[i_pronom]} », colonne "
          f"« {mots[i_nom]} » = {poids[i_pronom, i_nom].item():.4f}")
    print(f"  (la tête n'est pas entraînée : ce n'est pas la valeur qu'on rend, "
          f"c'est de savoir où elle est.\n   Pour mémoire, la ligne "
          f"« {mots[i_pronom]} » répartit son mélange ainsi :)")
    for mot, part in zip(mots, poids[i_pronom].tolist()):
        print(f"    {mot:<12}{part:.3f}  {'█' * round(30 * part)}")

    figures.matrice_d_attention(
        poids.numpy(), mots, mots,
        "phase10_qui_regarde_qui.png",
        "Phase 10 — la matrice « qui regarde qui » (tête non entraînée)")

    # Ce que les phases 11 à 13 réutilisent.
    dossier.attention = {"indice": indice, "mots": mots, "entree": entree,
                         "tete": tete, "i_nom": i_nom, "i_pronom": i_pronom,
                         "poids": poids}
    return dossier.retenir(10, releve=indice, pronom=mots[i_pronom],
                           antecedent=mots[i_nom],
                           case=poids[i_pronom, i_nom].item())


def phase11(dossier):
    """Le Conseil mélange vos mots."""
    titre(11, "le Conseil mélange vos mots")
    a_faire(
        """
        D'abord prouver que le conseiller a raison : permuter les mots du relevé, refaire
        tourner le code de la phase 10, montrer chiffres en main que la sortie de chaque
        mot n'a pas bougé.
        Puis faire qu'elle bouge, SANS toucher au mécanisme : l'information de position
        s'ajoute aux vecteurs d'entrée, avant le calcul.
        Rendre le même écart mesuré de la même façon, avant et après. Le premier nul ou
        indistinguable de zéro, le second non. Les deux matrices de poids côte à côte.
        """
    )


def phase12(dossier):
    """Le Conseil demande la facture."""
    titre(12, "le Conseil demande la facture")
    a_faire(
        """
        Chronométrer votre propre attention (code de la phase 11, inchangé) sur des
        séquences de 32, 64, 128, 256 puis 512 jetons. Plusieurs mesures par longueur,
        on garde une valeur stable, pas un tir unique (bureau.entrainement.Chrono).
        Mesurer aussi la taille de la matrice de poids à chaque longueur, en nombre de cases.
        Une figure : longueur en abscisse, temps en ordonnée, axes nommés.
        Trois lignes : en doublant la longueur, par combien le temps est-il multiplié, et
        pourquoi ce facteur-là. Comparer vos mesures entre elles, pas à une référence.
        Finir par : à quelle longueur votre machine devient inutilisable, d'après vos chiffres.
        """
    )


def phase13(dossier):
    """Deux regards sur le même relevé."""
    titre(13, "deux regards sur le même relevé")
    a_faire(
        """
        Deux têtes en parallèle sur le même relevé, chacune avec ses propres vecteurs de
        question, d'étiquette et de contenu, recollées en une seule sortie.
        Démontrer qu'elles ne regardent pas la même chose : les deux matrices affichées
        côte à côte avec les mots en étiquettes, plus une mesure du désaccord, justifiée
        en une ligne.
        Le point de comparaison obligatoire : deux têtes qui partiraient identiques.
        Sans lui, le chiffre de désaccord ne veut rien dire.
        Écrire que les têtes ne sont pas entraînées, donc que les différences viennent de
        l'initialisation — et ce qu'on pourrait conclure de plus si elles l'étaient.
        """
    )
