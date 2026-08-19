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


def la_tete_de_la_phase10(dossier):
    """Le relevé, les vecteurs et la tête de la phase 10 — reconstruits à
    l'identique si la phase 11+ tourne seule (tout est déterministe par graine)."""
    if getattr(dossier, "attention", None):
        return dossier.attention
    indice, mots, i_nom, i_pronom = relever_un_temoignage(dossier)
    entree = vecteurs_d_entree(dossier, mots)
    tete = modeles.UneTete(DIMENSION)
    with torch.no_grad():
        _, poids = tete(entree)
    dossier.attention = {"indice": indice, "mots": mots, "entree": entree,
                         "tete": tete, "i_nom": i_nom, "i_pronom": i_pronom,
                         "poids": poids.squeeze(0)}
    return dossier.attention


def encodage_de_position(nombre, dimension):
    """Un vecteur par position, fabriqué à la main : sinus et cosinus à des
    fréquences décroissantes. Aucune valeur apprise — la position p et la
    position q donnent des vecteurs différents, c'est tout ce qu'on demande."""
    positions = torch.arange(nombre, dtype=torch.float32).unsqueeze(1)
    frequences = torch.exp(
        torch.arange(0, dimension, 2, dtype=torch.float32)
        * (-torch.log(torch.tensor(10000.0)) / dimension))
    encodage = torch.zeros(nombre, dimension)
    encodage[:, 0::2] = torch.sin(positions * frequences)
    encodage[:, 1::2] = torch.cos(positions * frequences)
    return encodage


def phase11(dossier):
    """Le Conseil mélange vos mots.

    D'abord lui donner raison, chiffres en main : le mécanisme de la phase 10 ne
    voit pas l'ordre. Puis faire bouger la sortie sans toucher au mécanisme —
    l'information de position s'injecte dans les vecteurs d'entrée, avant le
    calcul.
    """
    titre(11, "le Conseil mélange vos mots")
    attention = la_tete_de_la_phase10(dossier)
    mots, entree, tete = attention["mots"], attention["entree"], attention["tete"]

    # La bouillie du conseiller : les mêmes mots, tirés au sort.
    generateur = torch.Generator().manual_seed(dossier.graine)
    melange = torch.randperm(len(mots), generator=generateur)
    print(f"  la phrase correcte : {' '.join(mots)}")
    print(f"  la bouillie rendue : {' '.join(mots[i] for i in melange.tolist())}")

    def ecart_apres_permutation(vecteurs, vecteurs_melanges):
        """Le même écart, mesuré de la même façon deux fois : pour chaque mot, la
        distance entre sa sortie dans la phrase correcte et sa sortie dans la
        bouillie, puis le maximum sur les mots."""
        with torch.no_grad():
            sortie, poids = tete(vecteurs)
            sortie_melangee, poids_melanges = tete(vecteurs_melanges)
        return ((sortie[:, melange] - sortie_melangee).abs().max().item(),
                poids.squeeze(0), poids_melanges.squeeze(0))

    # --- Avant : le conseiller a raison ------------------------------------------
    ecart_avant, poids_avant, _ = ecart_apres_permutation(entree, entree[:, melange])
    print(f"\n  avant correction : écart maximal {ecart_avant:.2e} — la sortie de "
          f"chaque mot n'a pas bougé.\n  Pour ce mécanisme, une phrase n'est pas "
          f"une suite, c'est un sac.")

    # --- Après : la position injectée dans les vecteurs d'entrée ------------------
    positions = encodage_de_position(len(mots), DIMENSION)
    avec_positions = entree + positions
    melange_avec_positions = entree[:, melange] + positions
    ecart_apres, poids_apres, _ = ecart_apres_permutation(
        avec_positions, melange_avec_positions)
    print(f"  après correction : écart maximal {ecart_apres:.4f} — le même mot, "
          f"déplacé, ne pose plus\n  la même question.")

    figures.matrice_d_attention(
        poids_avant.numpy(), mots, mots, "phase11_sans_positions.png",
        "Phase 11 — sans positions : la matrice d'un sac de mots")
    figures.matrice_d_attention(
        poids_apres.numpy(), mots, mots, "phase11_avec_positions.png",
        "Phase 11 — avec positions : la même tête, l'ordre en plus")

    print("\n  Où l'information a été injectée, et pourquoi là : dans les vecteurs "
          "d'entrée, avant le\n  calcul — parce que la question, l'étiquette et le "
          "contenu de chaque mot dérivent tous\n  de son vecteur d'entrée, c'est "
          "le seul endroit que le mécanisme regarde. Injectée\n  après, les "
          "proportions du mélange seraient déjà tirées du sac.")

    dossier.attention["positions"] = positions
    return dossier.retenir(11, ecart_avant=ecart_avant, ecart_apres=ecart_apres)


def phase12(dossier, longueurs=(32, 64, 128, 256, 512), repetitions=50):
    """Le Conseil demande la facture.

    L'attention de la phase 11, inchangée, chronométrée sur des séquences de plus
    en plus longues — des vrais jetons du fichier, enchaînés. Plusieurs mesures
    par longueur, on garde la médiane, pas un tir unique.
    """
    import statistics
    import time

    titre(12, "le Conseil demande la facture")
    attention = la_tete_de_la_phase10(dossier)
    tete = attention["tete"]

    # Des séquences de vrais jetons : les témoignages du fichier, mis bout à bout.
    mots = []
    for indice in range(len(dossier.textes)):
        mots.extend(jeu.jetons(dossier.textes[indice]))
        if len(mots) >= max(longueurs):
            break
    entrainement.fixer_graine(dossier.graine)
    table = nn.Embedding(len(dossier.vocabulaire), DIMENSION)
    indices = torch.tensor([[dossier.vocabulaire.index.get(m, 1)
                             for m in mots[: max(longueurs)]]])
    with torch.no_grad():
        vecteurs = table(indices) + encodage_de_position(max(longueurs), DIMENSION)

    lignes = []
    with torch.no_grad():
        for n in longueurs:
            entree = vecteurs[:, :n].contiguous()
            for _ in range(5):  # chauffe : les premiers passages paient les caches
                tete(entree)
            temps = []
            for _ in range(repetitions):
                depart = time.perf_counter()
                _, poids = tete(entree)
                temps.append(time.perf_counter() - depart)
            lignes.append({"n": n, "ms": statistics.median(temps) * 1000,
                           "cases": poids.shape[-1] * poids.shape[-2]})

    print(f"  {repetitions} passages avant par longueur, on garde la médiane :\n")
    print(f"  {'jetons':>8}{'temps (ms)':>12}{'cases de la matrice':>21}"
          f"{'facteur vs longueur/2':>23}")
    for i, ligne in enumerate(lignes):
        facteur = ligne["ms"] / lignes[i - 1]["ms"] if i else None
        print(f"  {ligne['n']:>8}{ligne['ms']:>12.3f}{ligne['cases']:>21,}"
              + (f"{facteur:>22.1f}×" if facteur else f"{'—':>23}"))

    figures.ligne([l["n"] for l in lignes], [l["ms"] for l in lignes],
                  "phase12_facture.png",
                  "Phase 12 — le coût d'un passage avant de l'attention",
                  "longueur de la séquence (jetons)",
                  "temps d'un passage avant (ms)")

    # À quelle longueur la machine devient inutilisable, d'après NOS chiffres :
    # le terme quadratique est estimé sur les deux plus grandes longueurs, et le
    # critère est posé : « inutilisable » quand relire les 88 875 relevés du
    # fichier prendrait plus d'une heure, soit 40,5 ms par relevé.
    n1, n2 = lignes[-2], lignes[-1]
    quadratique = (n2["ms"] - n1["ms"]) / (n2["n"] ** 2 - n1["n"] ** 2)
    constante = n2["ms"] - quadratique * n2["n"] ** 2
    seuil_ms = 3600 * 1000 / 88875
    n_limite = int(((seuil_ms - constante) / quadratique) ** 0.5)
    print(f"\n  terme quadratique estimé sur 256 → 512 : "
          f"{quadratique * 1000:.2f} µs pour 1000 cases")
    limite_lisible = f"{n_limite:,}".replace(",", " ")
    print(f"  critère « inutilisable » : relire les 88 875 relevés du fichier en "
          f"plus d'une heure,\n  soit {seuil_ms:.1f} ms par relevé — atteint vers "
          f"{limite_lisible} jetons par relevé.")

    return dossier.retenir(
        12,
        temps_ms={l["n"]: l["ms"] for l in lignes},
        facteur_256_512=lignes[-1]["ms"] / lignes[-2]["ms"],
        n_limite=n_limite,
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
