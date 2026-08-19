"""Acte 2 — le détecteur de formes.

Une tâche unique pour tout l'acte : `comments` entre, une forme sort.
"""

import polars as pl
import torch

from bureau import entrainement, figures, jeu, mesures, modeles
from bureau.contexte import a_faire, titre
from bureau.entrainement import Chrono


def preparer_le_jeu(dossier):
    """Les trois décisions de la phase 3, appliquées une fois pour toutes.

    Tout l'acte compare des scores entre eux : ils portent tous sur cette découpe
    et sur ces classes. Changer l'une ou l'autre invalide les comparaisons.
    """
    textes, etiquettes, classes = jeu.construire(dossier.df)
    if dossier.rapide:
        textes, etiquettes = textes[:4000], etiquettes[:4000]

    dossier.textes, dossier.etiquettes, dossier.classes = textes, etiquettes, classes
    dossier.decoupe = jeu.decouper(len(textes), graine=dossier.graine)

    apprentissage = [textes[i] for i in dossier.decoupe["apprentissage"]]
    dossier.vocabulaire = jeu.Vocabulaire(apprentissage)

    longueurs = sorted(len(jeu.jetons(t)) for t in apprentissage)
    dossier.longueur = longueurs[int(0.99 * len(longueurs))]

    print(f"  classes retenues        : {len(classes)} — {', '.join(classes)}")
    print(f"  relevés gardés          : {len(textes)}")
    print(f"  découpe                 : "
          f"{len(dossier.decoupe['apprentissage'])} / "
          f"{len(dossier.decoupe['validation'])} / "
          f"{len(dossier.decoupe['test'])}  (apprentissage / validation / test)")
    print(f"  vocabulaire             : {len(dossier.vocabulaire)} mots "
          f"(construit sur l'apprentissage seul)")
    print(f"  longueur en jetons      : médiane {longueurs[len(longueurs) // 2]}, "
          f"retenue {dossier.longueur} (99e centile), maximum {longueurs[-1]}")
    return dossier


def tenseurs(dossier, partie):
    indices = dossier.decoupe[partie]
    return jeu.en_tenseurs(
        [dossier.textes[i] for i in indices],
        [dossier.etiquettes[i] for i in indices],
        dossier.vocabulaire,
        dossier.longueur,
    )


def phase02(dossier):
    """Le test d'acceptation du Bureau.

    8 relevés, appris par coeur, jusqu'à ne plus se tromper sur un seul. Ni
    généralisation, ni partie de test, ni score honnête : exactement l'inverse.
    Un montage qui échoue ici n'apprendra jamais rien sur la transmission entière.
    """
    titre(2, "le test d'acceptation du Bureau")
    entrainement.fixer_graine(dossier.graine)

    indices = dossier.decoupe["apprentissage"][:8]
    textes = [dossier.textes[i] for i in indices]
    etiquettes = [dossier.etiquettes[i] for i in indices]
    entrees, cibles = jeu.en_tenseurs(
        textes, etiquettes, dossier.vocabulaire, dossier.longueur
    )

    # Le montage testé est celui que la phase 3 entraîne : la règle du Bureau dit
    # qu'aucun entraînement ne démarre avant que LE montage ait passé son test.
    modele = modeles.Empilement(len(dossier.vocabulaire), len(dossier.classes),
                                oubli=0.0)  # apprendre par coeur est le but ici

    # Deux nombres, pas un. Les 8 prédictions tombent justes bien avant que quoi
    # que ce soit soit appris : avec 8 relevés aux mots presque disjoints, quelques
    # pas suffisent à faire basculer les argmax alors que la perte vaut encore près
    # de ln(18), c'est-à-dire le hasard. « Ne plus se tromper » n'est donc pas le
    # critère d'arrêt — la perte qui s'écrase l'est.
    perte = torch.nn.CrossEntropyLoss()
    optimiseur = torch.optim.AdamW(modele.parameters(), lr=1e-2)
    historique, premiere_reussite, iterations = [], None, 0
    for iterations in range(1, 2001):
        optimiseur.zero_grad()
        valeur = perte(modele(entrees), cibles)
        valeur.backward()
        optimiseur.step()
        historique.append(valeur.item())
        with torch.no_grad():
            if premiere_reussite is None and (
                modele(entrees).argmax(dim=-1) == cibles
            ).all():
                premiere_reussite = iterations
        if valeur.item() < 1e-3:
            break

    predits = modele(entrees).argmax(dim=-1).tolist()
    justes = sum(p == v for p, v in zip(predits, etiquettes))

    print(f"  8 prédictions justes dès : itération {premiere_reussite} "
          f"(perte encore {historique[premiere_reussite - 1]:.3f} — le hasard vaut "
          f"{torch.tensor(float(len(dossier.classes))).log():.3f})")
    print(f"  appris par coeur (perte < 1e-3) : itération {iterations}")
    print(f"  perte finale            : {historique[-1]:.6f}")
    print(f"  justes                  : {justes}/8")
    print(f"\n    {'prédite':<12}{'vraie':<12}  début du relevé")
    for texte, vraie, predit in zip(textes, etiquettes, predits):
        marque = " " if vraie == predit else "✗"
        print(f"  {marque} {dossier.classes[predit]:<12}{dossier.classes[vraie]:<12}"
              f"  « {texte[:52]} »")

    figures.courbes_de_perte(
        {"8 relevés appris par coeur": (range(1, len(historique) + 1), historique)},
        "phase02_test_acceptation.png",
        "Test d'acceptation : perte sur 8 relevés",
    )
    print("\n  Ce que ce test prouve : le montage relie bien l'entrée à la sortie et "
          "la correction circule.\n  Ce qu'il ne prouve pas : qu'il apprendra quoi que "
          "ce soit de généralisable.")

    return dossier.retenir(2, iterations=iterations, justes=justes,
                           premiere_reussite=premiere_reussite,
                           perte_finale=historique[-1])


def justifier_les_decisions(dossier):
    """Les comptes qui appuient les trois décisions du jeu.

    Ces décisions changent le nombre de classes, donc le score : elles se défendent
    avec des nombres, pas avec des intentions.
    """
    formes = dossier.df.select(forme=jeu.normaliser_forme())["forme"]
    brutes = dossier.df["shape"].str.strip_chars().str.to_lowercase()

    trous = int((brutes.is_null() | (brutes == "")).sum())
    print(f"  relevés sans forme      : {trous}")
    print(f"  valeurs distinctes      : {brutes.n_unique()} avant fusion, "
          f"{formes.n_unique()} après")

    comptes = formes.value_counts(sort=True).drop_nulls()
    for source, cible in jeu.FUSIONS.items():
        avant = int((brutes == source).sum())
        apres = int((brutes == cible).sum())
        print(f"  fusion {source} → {cible:<10} {avant} + {apres} = {avant + apres}")

    for nom in sorted(jeu.FOURRE_TOUT):
        print(f"  fourre-tout {nom:<11} {int((brutes == nom).sum())} relevés écartés")

    sous_seuil = comptes.filter(pl.col("count") < jeu.SEUIL_CLASSE)
    print(f"  classes sous {jeu.SEUIL_CLASSE} relevés : {sous_seuil.height} "
          f"({int(sous_seuil['count'].sum())} relevés écartés) — "
          f"{', '.join(sous_seuil['forme'].head(6).to_list())}…")


def montrer_le_trajet(dossier):
    """Du texte brut d'un témoin au premier nombre qui entre dans le réseau."""
    indice = dossier.decoupe["apprentissage"][0]
    texte = dossier.textes[indice]
    mots = jeu.jetons(texte)
    indices = dossier.vocabulaire.encoder(texte, dossier.longueur)

    print(f"\n  Le trajet, sur un relevé réel :")
    print(f"    1. texte brut     « {texte[:70]} »")
    print(f"    2. nettoyé        « {jeu.nettoyer(texte)[:70].strip()} »")
    print(f"    3. jetons         {mots[:9]}")
    print(f"    4. indices        {indices[:9]}")
    print(f"       (vocabulaire de {len(dossier.vocabulaire)} mots ; 0 = remplissage, "
          f"1 = mot inconnu)")
    print(f"    5. le réseau reçoit un vecteur de {dossier.longueur} entiers, puis "
          f"remplace chaque entier par un vecteur appris.")


def textes_et_etiquettes(dossier, partie):
    return (
        [dossier.textes[i] for i in dossier.decoupe[partie]],
        [dossier.etiquettes[i] for i in dossier.decoupe[partie]],
    )


def service_statistique(dossier):
    """« Un modèle linéaire simple sur des comptages de mots, monté en une pause. »

    L'adversaire est monté à pleine puissance : régression logistique menée à
    convergence, et non quelques passages de descente stochastique. Le battre en
    l'affaiblissant ne prouverait rien.

    Il reçoit EXACTEMENT la même entrée que le réseau — mêmes jetons, mêmes paires
    de mots, même seuil de fréquence. Ce qui change entre les deux essais est le
    modèle, rien d'autre.
    """
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import LogisticRegression

    textes_app, etiquettes_app = textes_et_etiquettes(dossier, "apprentissage")
    textes_test, etiquettes_test = textes_et_etiquettes(dossier, "test")

    comptages = CountVectorizer(analyzer=jeu.jetons, min_df=2)
    with Chrono("linéaire du service statistique") as chrono:
        linéaire = LogisticRegression(max_iter=1000)
        linéaire.fit(comptages.fit_transform(textes_app), etiquettes_app)

    predits = linéaire.predict(comptages.transform(textes_test))
    print(f"    jetons vus par le linéaire : {len(comptages.vocabulary_)}")
    return torch.tensor(predits), torch.tensor(etiquettes_test), chrono.secondes
def essai_du_reseau(dossier, entrees, poids, graine, iterations, taille_lot, pas):
    """Un entraînement complet du réseau, rendu avec ses prédictions et sa courbe."""
    entrainement.fixer_graine(graine)
    modele = modeles.Empilement(len(dossier.vocabulaire), len(dossier.classes))
    with Chrono() as chrono:
        historique = entrainement.entrainer(
            modele,
            jeu.lots(entrees["apprentissage"], entrees["cibles_apprentissage"],
                     taille=taille_lot, graine=graine),
            jeu.lots(entrees["validation"], entrees["cibles_validation"],
                     taille=1024, melanger=False),
            iterations=iterations, pas=pas, releve_tous_les=1,
            garder_le_meilleur=True, bavard=(graine == dossier.graine),
            perte=torch.nn.CrossEntropyLoss(weight=poids),
        )
    predits, vrais = entrainement.predire(
        modele, jeu.lots(entrees["test"], entrees["cibles_test"],
                         taille=1024, melanger=False))
    return predits, vrais, historique, chrono.secondes


def phase03(dossier, iterations=25, taille_lot=256, pas=2e-3, graines=(0, 1, 2)):
    """Battre le service statistique.

    Trois scores côte à côte, sur exactement la même découpe, les mêmes classes et
    la même entrée : la baseline qui répond toujours la forme la plus fréquente, le
    linéaire sur comptages, et le réseau PyTorch.

    Le réseau est mesuré sur plusieurs initialisations, pas une seule : sur cette
    tâche la dispersion atteint 0,009 en taux, donc un écart plus petit qu'elle ne
    veut rien dire. C'est la moyenne qui est rendue au Conseil, avec son étendue.
    """
    titre(3, "battre le service statistique")

    justifier_les_decisions(dossier)
    montrer_le_trajet(dossier)

    # L'entrée commune aux deux modèles : les mêmes relevés, le même découpage en
    # jetons, le même vocabulaire construit sur l'apprentissage seul. Le linéaire en
    # compte les occurrences, le réseau en garde la suite — c'est là toute la
    # différence, et c'est le seul avantage qu'il puisse revendiquer.
    entrees = {}
    for partie in ("apprentissage", "validation", "test"):
        entrees[partie], entrees[f"cibles_{partie}"] = tenseurs(dossier, partie)
    print(f"\n  entrée commune : {len(dossier.vocabulaire)} mots, "
          f"séquences de {dossier.longueur} positions")

    vrais = entrees["cibles_test"]

    print("\n  Essai 1 — toujours la forme la plus fréquente")
    majoritaire = int(torch.bincount(entrees["cibles_apprentissage"]).argmax())
    print(f"    forme choisie           : {dossier.classes[majoritaire]}")
    predits_baseline = torch.full_like(vrais, majoritaire)
    mesures.montrer("baseline", predits_baseline, vrais, dossier.classes)

    print("\n  Essai 2 — le linéaire du service statistique, mené à convergence")
    predits_lineaire, _, temps_lineaire = service_statistique(dossier)
    mesures.montrer("linéaire", predits_lineaire, vrais, dossier.classes)

    print(f"\n  Essai 3 — le réseau PyTorch, sur {len(graines)} initialisations")
    effectifs = torch.bincount(entrees["cibles_apprentissage"]).float()
    poids = effectifs ** -0.25
    poids = poids / poids.mean()

    resultats = []
    for graine in graines:
        predits, _, historique, secondes = essai_du_reseau(
            dossier, entrees, poids, graine, iterations, taille_lot, pas)
        resultats.append({
            "taux": mesures.taux_de_reussite(predits, vrais),
            "f1": mesures.f1_moyen(predits, vrais, dossier.classes),
            "secondes": secondes,
            "predits": predits,
        })
        print(f"    initialisation {graine} : taux {resultats[-1]['taux']:.4f}"
              f"   F1 {resultats[-1]['f1']:.4f}   ({secondes:.1f} s)")
        # « Aucun essai n'existe sans ses deux courbes » : une figure par essai,
        # perte d'apprentissage et de validation sur la même image.
        figures.courbes_de_perte(
            {
                "apprentissage": (historique["passage"], historique["perte"]),
                "validation": (historique["passage"],
                               historique["perte_validation"]),
            },
            f"phase03_reseau_init{graine}.png",
            f"Phase 3 — réseau, initialisation {graine}",
            abscisse="passage sur les données",
        )

    def moyenne(clef):
        return sum(r[clef] for r in resultats) / len(resultats)

    def etendue(clef):
        return max(r[clef] for r in resultats) - min(r[clef] for r in resultats)

    print(f"\n  {'essai':<34}{'taux':>8}{'F1 moyen':>11}{'temps':>9}")
    for intitule, taux, f1, secondes in (
        ("toujours la plus fréquente",
         mesures.taux_de_reussite(predits_baseline, vrais),
         mesures.f1_moyen(predits_baseline, vrais, dossier.classes), 0.0),
        ("linéaire sur comptages",
         mesures.taux_de_reussite(predits_lineaire, vrais),
         mesures.f1_moyen(predits_lineaire, vrais, dossier.classes), temps_lineaire),
        (f"réseau PyTorch (moyenne de {len(graines)})",
         moyenne("taux"), moyenne("f1"), moyenne("secondes")),
    ):
        print(f"  {intitule:<34}{taux:>8.4f}{f1:>11.4f}{secondes:>8.1f}s")
    print(f"  {'étendue du réseau':<34}{etendue('taux'):>8.4f}{etendue('f1'):>11.4f}")

    taux_lineaire = mesures.taux_de_reussite(predits_lineaire, vrais)
    f1_lineaire = mesures.f1_moyen(predits_lineaire, vrais, dossier.classes)
    # Le critère n'est pas « la moyenne dépasse-t-elle ? » : une moyenne se laisse
    # tirer par une initialisation chanceuse — c'est l'erreur que j'ai faite une
    # première fois. C'est le PIRE des essais qui doit passer devant, sur les deux
    # mesures à la fois. Là seulement l'écart se défend devant le Conseil.
    pire_taux = min(r["taux"] for r in resultats)
    pire_f1 = min(r["f1"] for r in resultats)
    solide = pire_taux > taux_lineaire and pire_f1 > f1_lineaire
    print(f"\n  gain moyen sur le linéaire : "
          f"{moyenne('taux') - taux_lineaire:+.4f} en taux, "
          f"{moyenne('f1') - f1_lineaire:+.4f} en F1")
    print(f"  pire essai du réseau       : {pire_taux:.4f} / {pire_f1:.4f}"
          f"   contre {taux_lineaire:.4f} / {f1_lineaire:.4f} pour le linéaire")
    print("  " + (f"✓ les {len(graines)} essais passent devant sur les deux mesures"
                  if solide
                  else "✗ un essai au moins repasse derrière : l'écart ne se défend pas"))

    return dossier.retenir(
        3,
        classes=len(dossier.classes),
        releves=len(dossier.textes),
        jetons=len(dossier.vocabulaire),
        taux_lineaire=mesures.taux_de_reussite(predits_lineaire, vrais),
        f1_lineaire=mesures.f1_moyen(predits_lineaire, vrais, dossier.classes),
        taux_reseau=moyenne("taux"),
        f1_reseau=moyenne("f1"),
        etendue_taux=etendue("taux"),
        etendue_f1=etendue("f1"),
        temps_lineaire=temps_lineaire,
        temps_reseau=moyenne("secondes"),
    )



def phase04(dossier, iterations=8, taille_lot=256):
    """Le carnet de pannes.

    Le montage de la phase 3, cassé volontairement trois fois, une panne à la fois,
    remis d'aplomb entre chaque. Le Conseil ne veut pas un modèle qui marche : il
    veut la preuve qu'on sait reconnaître un modèle qui ne marche pas.
    """
    titre(4, "le carnet de pannes")

    entrees = {}
    for partie in ("apprentissage", "validation", "test"):
        entrees[partie], entrees[f"cibles_{partie}"] = tenseurs(dossier, partie)
    lots_app = jeu.lots(entrees["apprentissage"], entrees["cibles_apprentissage"],
                        taille=taille_lot, graine=dossier.graine)
    lots_val = jeu.lots(entrees["validation"], entrees["cibles_validation"],
                        taille=1024, melanger=False)
    lots_test = jeu.lots(entrees["test"], entrees["cibles_test"],
                         taille=1024, melanger=False)
    hasard = torch.tensor(float(len(dossier.classes))).log().item()
    fiches = []

    def monter(pas=2e-3, oubli=0.3, cibles=None, perte=None):
        entrainement.fixer_graine(dossier.graine)
        modele = modeles.Empilement(len(dossier.vocabulaire), len(dossier.classes),
                                    oubli=oubli)
        lots = lots_app if cibles is None else jeu.lots(
            entrees["apprentissage"], cibles, taille=taille_lot, graine=dossier.graine)
        historique = entrainement.entrainer(
            modele, lots, lots_val, iterations=iterations, pas=pas,
            releve_tous_les=1, bavard=False, perte=perte)
        return modele, historique

    # --- Le montage sain, pour avoir le point de comparaison -----------------
    print("  montage sain (référence)")
    modele, historique = monter()
    predits, vrais = entrainement.predire(modele, lots_test)
    reference = mesures.taux_de_reussite(predits, vrais)
    print(f"    taux sur le test : {reference:.3f}   perte finale "
          f"{historique['perte'][-1]:.3f}")

    # --- Panne 1 : l'oubli retiré ---------------------------------------------
    # Le geste : retirer l'oubli. Le réseau apprend les relevés d'apprentissage
    # par coeur — il les récite — et n'a plus rien à dire sur les autres. Aucune
    # donnée n'a changé entre les deux mesures ci-dessous.
    print("\n  panne 1 — l'oubli retiré")
    modele_par_coeur, historique_coeur = monter(oubli=0.0)
    lots_app_ordonnes = jeu.lots(entrees["apprentissage"],
                                 entrees["cibles_apprentissage"],
                                 taille=1024, melanger=False)
    predits_app, vrais_app = entrainement.predire(modele_par_coeur, lots_app_ordonnes)
    predits_par_coeur, _ = entrainement.predire(modele_par_coeur, lots_test)
    taux_app = mesures.taux_de_reussite(predits_app, vrais_app)
    taux_malade = mesures.taux_de_reussite(predits_par_coeur, vrais)
    figures.courbes_de_perte(
        {
            "apprentissage": (historique_coeur["passage"], historique_coeur["perte"]),
            "validation": (historique_coeur["passage"],
                           historique_coeur["perte_validation"]),
        },
        "phase04_panne1_recite.png",
        "Panne 1 — les deux courbes divergent : le réseau récite",
        abscisse="passage sur les données",
    )
    print(f"    taux sur les relevés d'apprentissage : {taux_app:.3f}")
    print(f"    taux sur les relevés de test         : {taux_malade:.3f}"
          f"   (montage sain : {reference:.3f})")
    print(f"    perte de validation : {historique_coeur['perte_validation'][0]:.3f} → "
          f"{historique_coeur['perte_validation'][-1]:.3f} — elle remonte")
    fiches.append({
        "titre": "excellent à l'entraînement, bête à l'évaluation",
        "geste": "retirer l'oubli : plus rien ne freine la mémorisation",
        "signature": "les deux courbes divergent — l'apprentissage descend, la "
                     "validation remonte ; l'écart entre les deux ne cesse de croître",
        "test": "évaluer sur les relevés d'apprentissage : si le score y est très "
                "supérieur à celui du test, le réseau récite au lieu de généraliser",
        "mesure": f"{taux_app:.3f} en apprentissage contre {taux_malade:.3f} en test",
    })

    # --- Panne 2 : les étiquettes décalées -----------------------------------
    # Le geste : décaler toutes les cibles d'un cran. Le réseau apprend une tâche
    # cohérente — donc la perte descend proprement — mais ce n'est pas la nôtre.
    print("\n  panne 2 — les étiquettes décalées d'un cran à l'apprentissage")
    decalees = (entrees["cibles_apprentissage"] + 1) % len(dossier.classes)
    modele_decale, historique_decale = monter(cibles=decalees)
    predits_decale, _ = entrainement.predire(modele_decale, lots_test)
    taux_decale = mesures.taux_de_reussite(predits_decale, vrais)
    # La figure met la courbe malade à côté de la courbe saine : elles sont
    # indistinguables, et c'est précisément la signature — cette panne ne se voit
    # pas sur la perte d'apprentissage, seulement sur les prédictions.
    figures.courbes_de_perte(
        {
            "étiquettes décalées": (historique_decale["passage"],
                                    historique_decale["perte"]),
            "montage sain": (historique["passage"], historique["perte"]),
        },
        "phase04_panne2_etiquettes.png",
        "Panne 2 — la courbe malade est indistinguable de la saine",
        abscisse="passage sur les données",
    )
    print(f"    perte d'apprentissage : {historique_decale['perte'][0]:.3f} → "
          f"{historique_decale['perte'][-1]:.3f} (elle descend proprement)")
    print(f"    taux sur le test      : {taux_decale:.3f}   "
          f"le hasard donnerait {1 / len(dossier.classes):.3f}")
    fiches.append({
        "titre": "la perte descend, les prédictions sont pires que le hasard",
        "geste": "décaler les étiquettes d'un cran avant l'apprentissage",
        "signature": "courbe d'apprentissage parfaitement saine, score de test "
                     "au niveau du hasard ou en dessous",
        "test": "regarder la matrice de confusion : si les erreurs sont "
                "concentrées sur une diagonale décalée, l'alignement est en cause",
        "mesure": f"{taux_decale:.3f} pour un hasard à {1 / len(dossier.classes):.3f}",
    })

    # --- Panne 3 : le pas d'apprentissage resté à zéro ------------------------
    # Le geste : le pas ne parvient jamais à l'optimiseur — variable écrasée,
    # planificateur mal branché, ou simplement l'appel à optimiseur.step() oublié.
    # Le montage est parfait, la boucle tourne, et rien n'apprend.
    print("\n  panne 3 — le pas d'apprentissage n'arrive jamais à l'optimiseur")
    modele_fige, historique_fige = monter(pas=0.0)
    pertes = historique_fige["perte"]
    figures.courbes_de_perte(
        {
            "perte figée": (historique_fige["passage"], pertes),
            f"hasard = ln({len(dossier.classes)})": (historique_fige["passage"],
                                                     [hasard] * len(pertes)),
        },
        "phase04_panne3_figee.png",
        "Panne 3 — la perte ne bouge plus, au ras du hasard",
        abscisse="passage sur les données",
    )
    print(f"    perte : {pertes[0]:.4f} → {pertes[-1]:.4f}   "
          f"(le hasard vaut ln({len(dossier.classes)}) = {hasard:.4f})")
    print(f"    variation sur les {len(pertes)} derniers passages : "
          f"{max(pertes[1:]) - min(pertes[1:]):.2e}")
    fiches.append({
        "titre": "la perte se fige et n'en bouge plus",
        "geste": "le pas d'apprentissage reste à zéro : la boucle tourne, "
                 "rien ne se met à jour",
        "signature": f"la perte colle à ln(nombre de classes) = {hasard:.2f} "
                     "dès le premier passage et ne varie plus d'une décimale",
        "test": "comparer un poids avant et après un passage : s'il est "
                "identique au bit près, rien n'apprend",
        "mesure": f"{pertes[-1]:.4f} contre {hasard:.4f}",
    })

    print("\n  Le carnet")
    for numero, fiche in enumerate(fiches, start=1):
        print(f"\n  {numero}. {fiche['titre']}\n     mesure    : {fiche['mesure']}")
        print(f"     geste     : {fiche['geste']}")
        print(f"     signature : {fiche['signature']}")
        print(f"     test      : {fiche['test']}")

    return dossier.retenir(4, reference=reference, panne1=taux_malade,
                           panne2=taux_decale, panne3=pertes[-1], hasard=hasard)


def phase05(dossier):
    """Le budget de calcul."""
    titre(5, "le budget de calcul")
    a_faire(
        """
        Réatteindre le score de la phase 3, même découpe et mêmes classes, en nettement
        moins de temps machine. Temps mesuré dans le code (bureau.entrainement.Chrono),
        affiché, et sur la même machine dans les deux cas.
        Une figure dont l'abscisse est le temps écoulé, pas le nombre de passages, avec
        l'ancienne et la nouvelle courbe superposées.
        Un réglage changé sans mesure ne compte pas ; deux réglages changés en même temps
        non plus. Un par un, chacun avec son gain et son coût en score.
        """
    )


def phase06(dossier):
    """Le champ de vision du modèle."""
    titre(6, "le champ de vision du modèle")
    a_faire(
        """
        Interdit : parcourir un témoignage mot après mot en attendant le précédent.
        Toutes les positions traitées de front.
        AVANT le premier entraînement, démontrer par le calcul de votre propre code que
        la sortie dépend de toutes les positions du relevé le plus long accepté.
        Rendre : longueur maximale et médiane en jetons ; un tableau couche par couche
        (ce que chaque couche ajoute à l'étendue vue, et le cumul) ; la comparaison du
        total à la longueur maximale en une ligne ; la vérification expérimentale
        (changer un mot au tout début, montrer que la sortie bouge).
        Si l'empilement dégrade le score : problème connu, solution connue, la nommer.
        """
    )


def phase07(dossier):
    """Quatre relevés à la fois."""
    titre(7, "quatre relevés à la fois")
    a_faire(
        """
        Relancer l'entraînement de la phase 6 avec des lots de 4 (jeu.lots(taille=4)),
        sans rien changer d'autre, et noter ce qui se passe : c'est le point de départ.
        Puis faire tenir l'entraînement à 4, en modifiant le modèle plutôt que le lot.
        Rendre : la courbe à 4 avant et après correction sur la même figure ; le montage
        corrigé relancé à la taille de lot de la phase 6 (la correction coûte-t-elle
        quelque chose quand la machine va bien ?) ; la phrase qui dit ce qui, dans
        l'ancien montage, dépendait des autres relevés du lot.
        Question à savoir trancher : que se passe-t-il si on prédit sur un seul relevé ?
        """
    )


def phase08(dossier):
    """Le Conseil a lu trois relevés."""
    titre(8, "le Conseil a lu trois relevés")
    a_faire(
        """
        Le mot de la forme est présent tel quel dans 34,7 % des relevés, 72,6 % pour light,
        9,9 % pour circle : le score global ne vient pas du même endroit selon les classes.
        1. Construire la liste des mots interdits (jeu.mots_interdits est un début à compléter) ;
        2. l'appliquer au texte, à l'apprentissage comme à l'évaluation ;
        3. prouver par le code qu'il reste zéro relevé contenant un mot interdit, et l'afficher ;
        4. réentraîner à l'identique et rendre la chute.
        Rendre les deux résumés de score (taux global et moyenne par classe) avant et après,
        dire lequel chute le plus et pourquoi, nommer les classes qui s'effondrent.
        """
    )


def phase09(dossier):
    """Rendre des comptes sur trois décisions."""
    titre(9, "rendre des comptes sur trois décisions")
    a_faire(
        """
        Trois relevés de la partie test repassés dans le modèle de la phase 8 : un réussi,
        un raté, un où le modèle a hésité entre deux formes très proches.
        Pour chacun, le témoignage entier avec, mot par mot, la part prise dans la décision.
        Figure ou texte coloré, mais lisible par quelqu'un qui ne code pas.
        Puis trois commentaires de trois lignes : ce que la machine a retenu, ce qu'elle a
        ignoré alors qu'un humain l'aurait vu, ce que le raté apprend sur le JEU DE DONNÉES.
        """
    )
