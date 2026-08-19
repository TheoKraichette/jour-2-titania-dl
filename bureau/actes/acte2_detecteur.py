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
def essai_du_reseau(dossier, entrees, poids, graine, iterations, taille_lot, pas,
                    fabrique=None):
    """Un entraînement complet du réseau, rendu avec ses prédictions et sa courbe.

    `fabrique` : construit le modèle — par défaut l'empilement de la phase 3 ;
    la phase 6 passe le sien, plus profond.
    """
    entrainement.fixer_graine(graine)
    modele = (fabrique or (lambda: modeles.Empilement(
        len(dossier.vocabulaire), len(dossier.classes))))()
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
    dossier.dernier_modele = modele  # la phase 9 repasse des relevés dedans
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
        taux_pire=min(r["taux"] for r in resultats),
        f1_pire=min(r["f1"] for r in resultats),
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


# Le score que la phase 5 doit réatteindre, mesuré en phase 3 sur trois
# initialisations. Utilisé quand la phase 5 tourne seule ; si la phase 3 vient de
# tourner dans le même processus, ses chiffres frais priment.
PHASE3 = {"taux_pire": 0.5385, "f1_pire": 0.4975}


def phase05(dossier, graines=(0, 1, 2)):
    """Le budget de calcul.

    Réatteindre le score de la phase 3, même découpe et mêmes classes, en nettement
    moins de temps machine. La référence est la configuration exacte de la phase 3,
    rejouée ici même : les deux temps sortent du même chronomètre, sur la même
    machine, dans le même processus.

    Chaque réglage est changé seul et mesuré seul. Un réglage sans mesure ne compte
    pas, deux réglages en même temps non plus.
    """
    titre(5, "le budget de calcul")

    entrees = {}
    for partie in ("apprentissage", "validation", "test"):
        entrees[partie], entrees[f"cibles_{partie}"] = tenseurs(dossier, partie)
    vrais = entrees["cibles_test"]
    effectifs = torch.bincount(entrees["cibles_apprentissage"]).float()
    poids = effectifs ** -0.25
    poids = poids / poids.mean()

    def essai(intitule, iterations, taille_lot, graine=0):
        predits, _, historique, secondes = essai_du_reseau(
            dossier, entrees, poids, graine, iterations, taille_lot, 2e-3)
        resultat = {
            "iterations": iterations,
            "taille_lot": taille_lot,
            "taux": mesures.taux_de_reussite(predits, vrais),
            "f1": mesures.f1_moyen(predits, vrais, dossier.classes),
            "secondes": secondes,
            "historique": historique,
        }
        print(f"  {intitule:<46}{secondes:>7.1f} s   "
              f"taux {resultat['taux']:.4f}   F1 {resultat['f1']:.4f}")
        return resultat

    reference = essai("référence — la phase 3 (25 passages, lots 256)", 25, 256)

    # Réglage 1 : s'arrêter à 8 passages. La phase 3 a montré que le meilleur point
    # de validation tombe au passage 5 ou 6 — les passages suivants sont du temps
    # machine payé pour surapprendre, et l'état retenu est le même.
    reglage1 = essai("réglage 1 — 8 passages au lieu de 25", 8, 256)

    # Réglage 2 : des lots de 512 au lieu de 256. Moitié moins de tours de boucle
    # Python par passage ; le calcul par relevé ne change pas.
    reglage2 = essai("réglage 2 — et des lots de 512", 8, 512)

    # Un réglage ne se garde que s'il apporte un gain de temps réel — au-delà des
    # ±5 % de bruit de mesure constatés sur cette machine — ET ne coûte pas le
    # score. La référence de score est le PIRE essai de la phase 3.
    seuils = dict(PHASE3)
    if 3 in dossier.scores:
        seuils = {"taux_pire": dossier.scores[3]["taux_pire"],
                  "f1_pire": dossier.scores[3]["f1_pire"]}
    gagne_du_temps = reglage2["secondes"] < 0.95 * reglage1["secondes"]
    tient_le_score = (reglage2["taux"] >= seuils["taux_pire"]
                      and reglage2["f1"] >= seuils["f1_pire"])
    if gagne_du_temps and tient_le_score:
        retenu, config = reglage2, "8 passages, lots de 512"
    else:
        retenu, config = reglage1, "8 passages, lots de 256"
        raison = "aucun gain de temps" if not gagne_du_temps else "coûte du score"
        print(f"  → réglage 2 : {raison} — rendu, mais pas retenu")
    print(f"\n  configuration retenue : {config}")

    # Le score final ne doit pas être inférieur à celui de la phase 3 : validé sur
    # les mêmes trois initialisations, jugé sur le pire essai.
    finals = [retenu]
    for graine in graines[1:]:
        finals.append(essai(f"  configuration retenue, initialisation {graine}",
                            retenu["iterations"], retenu["taille_lot"], graine))
    pire_taux = min(r["taux"] for r in finals)
    pire_f1 = min(r["f1"] for r in finals)

    facteur = reference["secondes"] / retenu["secondes"]
    print(f"\n  temps de la phase 3   : {reference['secondes']:.1f} s")
    print(f"  temps de la phase 5   : {retenu['secondes']:.1f} s")
    print(f"  facteur               : ×{facteur:.1f}")
    print(f"  score (pire des {len(finals)})   : {pire_taux:.4f} / {pire_f1:.4f}"
          f"   plancher de la phase 3 : {seuils['taux_pire']:.4f} / "
          f"{seuils['f1_pire']:.4f}")
    tient = pire_taux >= seuils["taux_pire"] and pire_f1 >= seuils["f1_pire"]
    print("  " + ("✓ le score tient, le facteur est acquis" if tient
                  else "✗ le score est en dessous : le gain de temps ne compte pas"))

    # La figure du Conseil : l'abscisse est le temps écoulé, pas le nombre de
    # passages. Les deux courbes de validation superposées.
    figures.courbes_de_perte(
        {
            f"phase 3 — {reference['secondes']:.0f} s":
                (reference["historique"]["temps"],
                 reference["historique"]["perte_validation"]),
            f"phase 5 — {retenu['secondes']:.0f} s":
                (retenu["historique"]["temps"],
                 retenu["historique"]["perte_validation"]),
        },
        "phase05_budget.png",
        "Phase 5 — la même perte de validation, en une fraction du temps",
        abscisse="secondes écoulées",
    )

    return dossier.retenir(
        5,
        temps_reference=reference["secondes"],
        temps_final=retenu["secondes"],
        facteur=facteur,
        taux_pire=pire_taux,
        f1_pire=pire_f1,
        configuration=config,
    )


DILATATIONS = (1, 2, 4, 8)  # l'empilement de la phase 6 : étendue 31 > 29


def fabrique_empilement(dossier, residuel=False, norme=None):
    return lambda: modeles.Empilement(
        len(dossier.vocabulaire), len(dossier.classes),
        dilatations=DILATATIONS, residuel=residuel, norme=norme,
    )


def phase06(dossier, graines=(0, 1, 2), iterations=8, taille_lot=256):
    """Le champ de vision du modèle.

    Toutes les positions sont traitées de front — aucune ne dépend de la
    précédente, la contrainte de la salle des calculs est respectée par
    construction. La démonstration que la sortie dépend de toutes les positions se
    fait AVANT le premier entraînement : d'abord par le calcul de l'étendue,
    ensuite expérimentalement, sur le modèle encore vierge.
    """
    titre(6, "le champ de vision du modèle")
    entrainement.fixer_graine(dossier.graine)

    # --- Les longueurs ---------------------------------------------------------
    longueurs = sorted(
        len(jeu.jetons(dossier.textes[i])) for i in dossier.decoupe["apprentissage"])
    print(f"  longueur maximale acceptée en entrée : {dossier.longueur} jetons "
          f"(99e centile ; le plus long relevé du fichier en fait {longueurs[-1]}, "
          f"tronqué)")
    print(f"  longueur médiane                     : "
          f"{longueurs[len(longueurs) // 2]} jetons")

    # --- Le tableau couche par couche, avant tout entraînement ------------------
    modele = fabrique_empilement(dossier)()
    print(f"\n  l'empilement : fenêtre {modele.fenetre}, "
          f"dilatations {', '.join(str(d) for d in DILATATIONS)}")
    print(f"    {'couche':>7}{'dilatation':>12}{'ajout':>12}{'cumul':>8}")
    for ligne in modele.etendue_par_couche():
        print(f"    {ligne['couche']:>7}{ligne['dilatation']:>12}"
              f"{ligne['ajout']:>12}{ligne['cumul']:>8}")
    total = modele.etendue_par_couche()[-1]["cumul"]
    print(f"\n  étendue totale {total} > longueur maximale {dossier.longueur} : "
          f"la position centrale d'un relevé voit ses {dossier.longueur} positions, "
          f"et le maximum final fait dépendre la sortie de toutes.")

    # --- La vérification expérimentale, modèle encore vierge --------------------
    # Le relevé le plus long du jeu, un mot changé tout au début, et on mesure ce
    # qui bouge : la sortie du classement, et jusqu'où la modification se propage
    # dans les positions.
    indice = max(range(len(dossier.textes)),
                 key=lambda i: len(jeu.jetons(dossier.textes[i])))
    texte = dossier.textes[indice]
    original = torch.tensor(
        [dossier.vocabulaire.encoder(texte, dossier.longueur)])
    modifie = original.clone()
    remplacant = dossier.vocabulaire.index.get("light", 2)
    if modifie[0, 0].item() == remplacant:
        remplacant = dossier.vocabulaire.index.get("dark", 3)
    modifie[0, 0] = remplacant

    modele.eval()
    with torch.no_grad():
        ecart_sortie = (modele(original) - modele(modifie)).abs().max().item()
        ecart_positions = (modele.cartes(original) - modele.cartes(modifie)) \
            .abs().amax(dim=1).squeeze(0)
    touchees = (ecart_positions > 1e-9).nonzero().squeeze(-1)
    print(f"\n  vérification expérimentale (modèle non entraîné) :")
    print(f"    relevé : « {texte[:64]} »")
    print(f"    premier mot remplacé par "
          f"« {dossier.vocabulaire.mots[remplacant]} »")
    print(f"    la sortie bouge : écart maximal {ecart_sortie:.4f} sur les logits")
    print(f"    la modification se propage jusqu'à la position "
          f"{int(touchees.max()) + 1} — rayon mesuré {int(touchees.max())}, "
          f"rayon théorique {(total - 1) // 2}")

    # --- Puis on entraîne, et on compare au score défendu depuis la phase 3 -----
    entrees = {}
    for partie in ("apprentissage", "validation", "test"):
        entrees[partie], entrees[f"cibles_{partie}"] = tenseurs(dossier, partie)
    vrais = entrees["cibles_test"]
    effectifs = torch.bincount(entrees["cibles_apprentissage"]).float()
    poids = effectifs ** -0.25
    poids = poids / poids.mean()

    seuils = dict(PHASE3)
    if 3 in dossier.scores:
        seuils = {"taux_pire": dossier.scores[3]["taux_pire"],
                  "f1_pire": dossier.scores[3]["f1_pire"]}

    def trois_essais(residuel, norme, intitule):
        resultats = []
        for graine in graines:
            predits, _, historique, secondes = essai_du_reseau(
                dossier, entrees, poids, graine, iterations, taille_lot, 2e-3,
                fabrique=fabrique_empilement(dossier, residuel=residuel,
                                             norme=norme))
            resultats.append({
                "taux": mesures.taux_de_reussite(predits, vrais),
                "f1": mesures.f1_moyen(predits, vrais, dossier.classes),
                "secondes": secondes,
                "historique": historique,
            })
            print(f"    initialisation {graine} : taux {resultats[-1]['taux']:.4f}"
                  f"   F1 {resultats[-1]['f1']:.4f}   ({secondes:.1f} s)")
        pire = (min(r["taux"] for r in resultats), min(r["f1"] for r in resultats))
        print(f"    pire essai : {pire[0]:.4f} / {pire[1]:.4f}"
              f"   plancher phase 3 : {seuils['taux_pire']:.4f} / "
              f"{seuils['f1_pire']:.4f}")
        figures.courbes_de_perte(
            {
                "apprentissage": (resultats[0]["historique"]["passage"],
                                  resultats[0]["historique"]["perte"]),
                "validation": (resultats[0]["historique"]["passage"],
                               resultats[0]["historique"]["perte_validation"]),
            },
            f"phase06_{intitule}.png",
            f"Phase 6 — empilement dilaté ({intitule.replace('_', ' ')})",
            abscisse="passage sur les données",
        )
        return resultats, pire

    print(f"\n  entraînement de l'empilement ({len(DILATATIONS)} couches), "
          f"réglages de la phase 5 :")
    resultats, pire = trois_essais(residuel=False, norme=None,
                                   intitule="sans_residu")
    retenue = {"residuel": False, "norme": None}

    if pire[0] < seuils["taux_pire"] or pire[1] < seuils["f1_pire"]:
        # Le problème connu : en traversant quatre couches, le gradient s'affaiblit
        # et les premières couches n'apprennent presque plus — empiler dégrade.
        # La solution connue : les connexions résiduelles, qui donnent au gradient
        # un chemin direct vers l'entrée.
        print("\n  l'empilement dégrade le score : problème connu (le gradient "
              "s'affaiblit\n  en traversant les couches), solution connue "
              "(connexions résiduelles) —\n  appliquée et remesurée :")
        resultats_residu, pire_residu = trois_essais(residuel=True, norme=None,
                                                     intitule="avec_residu")

        # La recette standard des empilements profonds ne s'arrête pas au résidu :
        # elle normalise la sortie de chaque couche. Mesurée aussi, séparément.
        print("\n  la recette standard ajoute la normalisation par lot au résidu — "
              "mesurée aussi :")
        resultats_norme, pire_norme = trois_essais(residuel=True, norme="lot",
                                                   intitule="residu_et_norme")

        # On retient la recette complète si elle tient le plancher et ne cède pas
        # plus que le bruit au résidu seul ; sinon le résidu seul s'il tient.
        norme_tient = (pire_norme[0] >= seuils["taux_pire"]
                       and pire_norme[1] >= seuils["f1_pire"])
        norme_ne_cede_pas = (pire_norme[0] >= pire_residu[0] - 0.005
                             and pire_norme[1] >= pire_residu[1] - 0.005)
        if norme_tient and norme_ne_cede_pas:
            resultats, pire = resultats_norme, pire_norme
            retenue = {"residuel": True, "norme": "lot"}
        else:
            resultats, pire = resultats_residu, pire_residu
            retenue = {"residuel": True, "norme": None}
        print(f"\n  montage retenu : résidu"
              + (" + normalisation par lot" if retenue["norme"] else " seul"))

    tient = pire[0] >= seuils["taux_pire"] and pire[1] >= seuils["f1_pire"]
    print("\n  " + ("✓ l'empilement couvre le relevé entier et s'entraîne encore"
                    if tient else
                    "✗ le score reste en dessous du plancher de la phase 3"))

    return dossier.retenir(
        6,
        etendue=total,
        longueur=dossier.longueur,
        rayon_mesure=int(touchees.max()),
        ecart_sortie=ecart_sortie,
        residuel=retenue["residuel"],
        norme=retenue["norme"],
        taux_pire=pire[0],
        f1_pire=pire[1],
        taux_moyen=sum(r["taux"] for r in resultats) / len(resultats),
        f1_moyen=sum(r["f1"] for r in resultats) / len(resultats),
        temps_moyen=sum(r["secondes"] for r in resultats) / len(resultats),
    )


# Le montage et le score de la phase 6, pour quand la phase 7 tourne seule.
PHASE6 = {"taux_pire": 0.5387, "f1_pire": 0.5018,
          "residuel": True, "norme": None}


def phase07(dossier, graines=(0, 1, 2), iterations=8):
    """Quatre relevés à la fois.

    Le Conseil a revendu la moitié de la salle des calculs : 4 relevés par lot.
    L'entraînement de la phase 6 est relancé tel quel, sans rien changer d'autre —
    puis la phase répond à la vraie question : qu'est-ce qui, dans un montage, a
    le droit de dépendre des autres relevés du lot ? Le montage retenu en phase 6
    n'a rien de tel — c'est un choix mesuré. La recette écartée en phase 6, la
    normalisation par lot, en dépendait : la voici mise à l'épreuve, puis corrigée
    en modifiant le modèle, pas le lot.
    """
    titre(7, "quatre relevés à la fois")

    config = dict(PHASE6)
    if 6 in dossier.scores:
        config.update({k: dossier.scores[6][k]
                       for k in ("taux_pire", "f1_pire", "residuel", "norme")})

    entrees = {}
    for partie in ("apprentissage", "validation", "test"):
        entrees[partie], entrees[f"cibles_{partie}"] = tenseurs(dossier, partie)
    vrais = entrees["cibles_test"]
    effectifs = torch.bincount(entrees["cibles_apprentissage"]).float()
    poids = effectifs ** -0.25
    poids = poids / poids.mean()

    def un_essai(norme, taille_lot, graine=0):
        predits, _, historique, secondes = essai_du_reseau(
            dossier, entrees, poids, graine, iterations, taille_lot, 2e-3,
            fabrique=fabrique_empilement(dossier, residuel=config["residuel"],
                                         norme=norme))
        return {
            "taux": mesures.taux_de_reussite(predits, vrais),
            "f1": mesures.f1_moyen(predits, vrais, dossier.classes),
            "secondes": secondes,
            "historique": historique,
        }

    # --- Le point de départ : l'entraînement de la phase 6, à 4 par lot ---------
    # Une seule initialisation par courbe : un entraînement à 4 par lot fait
    # 12 759 mises à jour par passage, la comparaison de courbes se fait à graine
    # égale et le score final se confirme à 256 sur les trois graines.
    print("  l'entraînement de la phase 6, relancé à 4 relevés par lot, sans rien "
          "changer d'autre :")
    retenu4 = un_essai(norme=config["norme"], taille_lot=4)
    print(f"    montage retenu (résidu seul) : taux {retenu4['taux']:.4f}   "
          f"F1 {retenu4['f1']:.4f}   ({retenu4['secondes']:.0f} s)"
          f"   — phase 6 à 256 : {config['taux_pire']:.4f} / "
          f"{config['f1_pire']:.4f}")
    print("    rien n'y dépend des autres relevés du lot — et ce n'est pas un "
          "hasard, c'est la\n    conséquence d'un choix mesuré en phase 6. La "
          "recette qui en dépendait :")

    # --- Ce qui aurait dépendu du lot, et n'aurait jamais dû en dépendre --------
    # La normalisation par lot centre et réduit chaque canal avec la moyenne et la
    # variance DU LOT : la sortie d'un relevé dépend des trois autres relevés
    # tirés avec lui. À 256 le lot ressemble à la population et ça ne se voit
    # pas ; à 4, chaque relevé est normalisé contre trois voisins de hasard.
    print("\n  la normalisation par lot (écartée en phase 6), à 4 relevés par lot :")
    avant = un_essai(norme="lot", taille_lot=4)
    print(f"    norme par lot    : taux {avant['taux']:.4f}   F1 {avant['f1']:.4f}"
          f"   ({avant['secondes']:.0f} s)")

    # Démonstration directe de la dépendance, avant toute correction :
    entrainement.fixer_graine(dossier.graine)
    temoin = fabrique_empilement(dossier, residuel=config["residuel"],
                                 norme="lot")()
    temoin.train()
    seul = entrees["test"][:1]
    accompagne = entrees["test"][:4]
    with torch.no_grad():
        ecart = (temoin(seul) - temoin(accompagne)[:1]).abs().max().item()
    print(f"    le même relevé, seul puis accompagné de trois autres, dans ce "
          f"modèle en mode\n    entraînement : écart maximal {ecart:.4f} sur les "
          f"logits — sa sortie dépend de ses\n    voisins de lot.")

    # --- La correction : modifier le modèle, pas le lot --------------------------
    # Normalisation par groupe : les mêmes statistiques, calculées dans le relevé
    # seul. Le modèle ne regarde plus jamais ses voisins de lot.
    print("\n  correction — normalisation par groupe (statistiques calculées dans "
          "le relevé seul) :")
    apres = un_essai(norme="groupe", taille_lot=4)
    print(f"    norme par groupe : taux {apres['taux']:.4f}   F1 {apres['f1']:.4f}"
          f"   ({apres['secondes']:.0f} s)")

    figures.courbes_de_perte(
        {
            "norme par lot — avant correction":
                (avant["historique"]["passage"],
                 avant["historique"]["perte_validation"]),
            "norme par groupe — après correction":
                (apres["historique"]["passage"],
                 apres["historique"]["perte_validation"]),
            "montage retenu (résidu seul)":
                (retenu4["historique"]["passage"],
                 retenu4["historique"]["perte_validation"]),
        },
        "phase07_quatre_par_lot.png",
        "Phase 7 — perte de validation à 4 relevés par lot, avant et après",
        abscisse="passage sur les données",
    )

    # --- Le montage corrigé quand la machine va bien -----------------------------
    print("\n  le montage corrigé, relancé à la taille de lot de la phase 6 (256), "
          "trois initialisations :")
    controles = []
    for graine in graines:
        controles.append(un_essai(norme="groupe", taille_lot=256, graine=graine))
        print(f"    initialisation {graine} : taux {controles[-1]['taux']:.4f}"
              f"   F1 {controles[-1]['f1']:.4f}   ({controles[-1]['secondes']:.0f} s)")
    pire = (min(c["taux"] for c in controles), min(c["f1"] for c in controles))
    print(f"    pire essai : {pire[0]:.4f} / {pire[1]:.4f}"
          f"   phase 6 : {config['taux_pire']:.4f} / {config['f1_pire']:.4f}")

    # --- Et sur un seul relevé ? --------------------------------------------------
    with torch.no_grad():
        corrige = fabrique_empilement(dossier, residuel=config["residuel"],
                                      norme="groupe")()
        corrige.train()
        ecart_corrige = (corrige(seul) - corrige(accompagne)[:1]).abs().max().item()
    print(f"\n  la même expérience sur le montage corrigé : écart "
          f"{ecart_corrige:.6f} — un relevé seul\n  donne exactement la même "
          f"sortie qu'accompagné. L'ancien montage, lui, se normalise\n  contre "
          f"lui-même en mode entraînement, et en mode évaluation il s'appuie sur "
          f"des\n  moyennes mémorisées — apprises sur des lots de 4, donc bruitées.")

    return dossier.retenir(
        7,
        taux_avant=avant["taux"], f1_avant=avant["f1"],
        taux_apres=apres["taux"], f1_apres=apres["f1"],
        taux_controle=pire[0], f1_controle=pire[1],
        ecart_lot=ecart, ecart_corrige=ecart_corrige,
    )


def entrees_censurees(dossier, interdits):
    """Le jeu entier, sans un mot de forme, découpe et classes inchangées.

    Les textes sont censurés en place dans l'ordre du jeu : les indices de la
    découpe restent valables, les étiquettes ne bougent pas. Le vocabulaire est
    reconstruit sur les textes censurés de la seule partie apprentissage.
    """
    textes = [jeu.censurer(t, interdits) for t in dossier.textes]
    vocabulaire = jeu.Vocabulaire(
        [textes[i] for i in dossier.decoupe["apprentissage"]])
    entrees = {}
    for partie in ("apprentissage", "validation", "test"):
        indices = dossier.decoupe[partie]
        entrees[partie], entrees[f"cibles_{partie}"] = jeu.en_tenseurs(
            [textes[i] for i in indices],
            [dossier.etiquettes[i] for i in indices],
            vocabulaire, dossier.longueur)
    return textes, vocabulaire, entrees


def phase08(dossier, graines=(0, 1, 2), iterations=8, taille_lot=256):
    """Le Conseil a lu trois relevés.

    « Nous ne payons pas pour une machine qui recopie un mot. » Le vocabulaire des
    formes est interdit au modèle, à l'apprentissage comme à l'évaluation, la
    preuve du zéro est calculée par le code, et la chute est rendue sans être
    maquillée.
    """
    titre(8, "le Conseil a lu trois relevés")

    config = dict(PHASE6)
    if 6 in dossier.scores:
        config.update({k: dossier.scores[6][k] for k in ("residuel", "norme")})

    # --- 1. La liste des mots interdits ------------------------------------------
    interdits = jeu.mots_interdits(dossier.classes)
    print(f"  mots interdits : {len(interdits)}")
    print("    " + ", ".join(sorted(m for m in interdits if "'" not in m)))
    print("    (plus la variante « 's » de chacun)")

    # Les comptes du Conseil, refaits : le mot de la forme, présent tel quel.
    contient_sa_forme = [
        dossier.classes[dossier.etiquettes[i]] in jeu.jetons(dossier.textes[i])
        for i in range(len(dossier.textes))
    ]
    part_globale = sum(contient_sa_forme) / len(contient_sa_forme)
    print(f"\n  le mot de la forme est présent tel quel dans "
          f"{part_globale:.1%} des relevés")
    for forme in ("light", "circle"):
        indice_forme = dossier.classes.index(forme)
        concernes = [contient_sa_forme[i] for i in range(len(dossier.textes))
                     if dossier.etiquettes[i] == indice_forme]
        print(f"    {forme:<8}: {sum(concernes) / len(concernes):.1%}")

    # --- 2. et 3. L'interdiction, et la preuve du zéro ---------------------------
    textes_censures, vocabulaire, censure = entrees_censurees(dossier, interdits)
    restants = sum(1 for t in textes_censures if set(jeu.jetons(t)) & interdits)
    avant_censure = sum(1 for t in dossier.textes
                        if set(jeu.jetons(t)) & interdits)
    print(f"\n  relevés contenant un mot interdit avant traitement : "
          f"{avant_censure} ({avant_censure / len(dossier.textes):.1%})")
    print(f"  relevés contenant encore un mot interdit après traitement : "
          f"{restants}")
    assert restants == 0, "l'interdiction n'est pas effective"
    print(f"  vocabulaire censuré : {len(vocabulaire)} mots")

    # --- 4. Réentraîner à l'identique --------------------------------------------
    entrees = {}
    for partie in ("apprentissage", "validation", "test"):
        entrees[partie], entrees[f"cibles_{partie}"] = tenseurs(dossier, partie)
    vrais = entrees["cibles_test"]
    effectifs = torch.bincount(entrees["cibles_apprentissage"]).float()
    poids = effectifs ** -0.25
    poids = poids / poids.mean()

    def trois_essais(entrees_du_jeu, taille_vocabulaire):
        resultats, premier_modele = [], None
        for graine in graines:
            fabrique = lambda: modeles.Empilement(
                taille_vocabulaire, len(dossier.classes),
                dilatations=DILATATIONS, residuel=config["residuel"],
                norme=config["norme"])
            predits, _, historique, secondes = essai_du_reseau(
                dossier, entrees_du_jeu, poids, graine, iterations, taille_lot,
                2e-3, fabrique=fabrique)
            if graine == graines[0]:
                premier_modele = dossier.dernier_modele
            resultats.append({
                "graine": graine, "predits": predits,
                "taux": mesures.taux_de_reussite(predits, vrais),
                "f1": mesures.f1_moyen(predits, vrais, dossier.classes),
            })
            print(f"    initialisation {graine} : taux {resultats[-1]['taux']:.4f}"
                  f"   F1 {resultats[-1]['f1']:.4f}   ({secondes:.0f} s)")
        return resultats, premier_modele

    print("\n  le montage de la phase 6, sur le texte intact :")
    avant, _ = trois_essais(entrees, len(dossier.vocabulaire))
    print("\n  le même montage, réentraîné à l'identique sur le texte censuré :")
    apres, modele_censure = trois_essais(censure, len(vocabulaire))

    # --- La chute, sur les deux résumés -------------------------------------------
    def bilan(resultats):
        return (sum(r["taux"] for r in resultats) / len(resultats),
                sum(r["f1"] for r in resultats) / len(resultats))

    taux_avant, f1_avant = bilan(avant)
    taux_apres, f1_apres = bilan(apres)
    print(f"\n  {'':<22}{'taux global':>13}{'F1 moyen par classe':>21}")
    print(f"  {'avant interdiction':<22}{taux_avant:>13.4f}{f1_avant:>21.4f}")
    print(f"  {'après interdiction':<22}{taux_apres:>13.4f}{f1_apres:>21.4f}")
    print(f"  {'chute':<22}{taux_avant - taux_apres:>13.4f}"
          f"{f1_avant - f1_apres:>21.4f}"
          f"   ({(taux_avant - taux_apres) / taux_avant:.1%} et "
          f"{(f1_avant - f1_apres) / f1_avant:.1%} en relatif)")

    # --- Le score par classe avant et après, et les classes effondrées ------------
    par_classe_avant = {l["forme"]: l for l in mesures.par_classe(
        avant[0]["predits"], vrais, dossier.classes)}
    par_classe_apres = {l["forme"]: l for l in mesures.par_classe(
        apres[0]["predits"], vrais, dossier.classes)}
    chutes = sorted(
        dossier.classes,
        key=lambda f: par_classe_apres[f]["rappel"] - par_classe_avant[f]["rappel"])
    print(f"\n  rappel par classe (initialisation 0), les plus touchées d'abord :")
    print(f"    {'forme':<12}{'effectif':>9}{'avant':>8}{'après':>8}{'chute':>8}")
    for forme in chutes[:8]:
        a, b = par_classe_avant[forme], par_classe_apres[forme]
        print(f"    {forme:<12}{a['effectif']:>9}{a['rappel']:>8.3f}"
              f"{b['rappel']:>8.3f}{b['rappel'] - a['rappel']:>8.3f}")
    print(f"\n  les classes effondrées : "
          f"{', '.join(chutes[:3])}")

    # Ce que la phase 9 réutilise : le jeu censuré, le modèle entraîné dessus
    # (initialisation 0) et la configuration du montage.
    dossier.censure = {
        "textes": textes_censures, "vocabulaire": vocabulaire,
        "entrees": censure, "poids": poids, "interdits": interdits,
        "config": config, "modele": modele_censure,
    }

    return dossier.retenir(
        8,
        interdits=len(interdits),
        restants=restants,
        taux_avant=taux_avant, f1_avant=f1_avant,
        taux_apres=taux_apres, f1_apres=f1_apres,
        effondrees=chutes[:3],
    )


def jeu_et_modele_de_la_phase8(dossier):
    """La phase 9 part du modèle de la phase 8. S'il n'est pas déjà dans le
    dossier (phase 9 lancée seule), il est réentraîné à l'identique,
    initialisation 0."""
    if getattr(dossier, "censure", None) and dossier.censure.get("modele"):
        return dossier.censure
    print("  (modèle de la phase 8 absent du dossier : réentraîné à l'identique, "
          "initialisation 0)")
    config = dict(PHASE6)
    if 6 in dossier.scores:
        config.update({k: dossier.scores[6][k] for k in ("residuel", "norme")})
    interdits = jeu.mots_interdits(dossier.classes)
    textes, vocabulaire, entrees = entrees_censurees(dossier, interdits)
    effectifs = torch.bincount(entrees["cibles_apprentissage"]).float()
    poids = effectifs ** -0.25
    poids = poids / poids.mean()
    essai_du_reseau(
        dossier, entrees, poids, dossier.graine, 8, 256, 2e-3,
        fabrique=lambda: modeles.Empilement(
            len(vocabulaire), len(dossier.classes), dilatations=DILATATIONS,
            residuel=config["residuel"], norme=config["norme"]))
    dossier.censure = {"textes": textes, "vocabulaire": vocabulaire,
                       "entrees": entrees, "interdits": interdits,
                       "config": config, "modele": dossier.dernier_modele}
    return dossier.censure


def phase09(dossier):
    """Rendre des comptes sur trois décisions.

    « Si votre réponse est que la machine est ainsi faite, nous fermerons le
    Bureau. » Trois relevés de la partie test, repassés dans le modèle de la
    phase 8, avec la part de chaque mot dans la décision — mesurée en retirant le
    mot et en regardant ce que la confiance du modèle y perd.
    """
    titre(9, "rendre des comptes sur trois décisions")
    censure = jeu_et_modele_de_la_phase8(dossier)
    modele, entrees = censure["modele"], censure["entrees"]
    vrais = entrees["cibles_test"]
    modele.eval()

    # Les probabilités sur toute la partie test, par paquets.
    probabilites = []
    with torch.no_grad():
        for debut in range(0, len(vrais), 1024):
            probabilites.append(
                torch.softmax(modele(entrees["test"][debut:debut + 1024]), dim=-1))
    probabilites = torch.cat(probabilites)
    deux_meilleures, indices_2 = probabilites.topk(2, dim=-1)
    predits = indices_2[:, 0]
    corrects = predits == vrais

    # Les trois dossiers : le réussi le plus sûr, le raté le plus sûr (l'erreur
    # assumée est plus instructive que l'erreur hésitante), et l'hésitation la
    # plus serrée entre deux formes.
    confiance = deux_meilleures[:, 0]
    ecart_12 = deux_meilleures[:, 0] - deux_meilleures[:, 1]
    choisis = {
        "réussi": int(torch.where(corrects, confiance,
                                  torch.zeros_like(confiance)).argmax()),
        "raté": int(torch.where(~corrects, confiance,
                                torch.zeros_like(confiance)).argmax()),
        "hésitant": int(torch.where(corrects, ecart_12,
                                    torch.full_like(ecart_12, 2.0)).argmin()),
    }

    for numero, (nature, indice_test) in enumerate(choisis.items(), start=1):
        indice_jeu = dossier.decoupe["test"][indice_test]
        texte_original = dossier.textes[indice_jeu]
        texte_censure = censure["textes"][indice_jeu]
        mots = jeu.jetons(texte_censure)[: dossier.longueur]
        entree = entrees["test"][indice_test:indice_test + 1]
        prediction = int(predits[indice_test])

        # La part d'un mot : ce que la confiance dans la forme prédite perd
        # quand on le retire. Positif, le mot poussait la décision ; négatif,
        # il la freinait.
        with torch.no_grad():
            base = torch.softmax(modele(entree), dim=-1)[0, prediction].item()
            parts = []
            for position in range(len(mots)):
                ampute = entree.clone()
                ampute[0, position] = 0
                parts.append(
                    base
                    - torch.softmax(modele(ampute), dim=-1)[0, prediction].item())

        print(f"\n  dossier {numero} — {nature}")
        print(f"    témoignage    : « {texte_original[:96]} »")
        print(f"    vraie forme   : {dossier.classes[int(vrais[indice_test])]}")
        print(f"    prédiction    : {dossier.classes[prediction]} "
              f"(confiance {confiance[indice_test]:.0%}"
              + (f", devant {dossier.classes[int(indices_2[indice_test, 1])]} à "
                 f"{deux_meilleures[indice_test, 1]:.0%}"
                 if nature == "hésitant" else "") + ")")
        echelle = max(abs(p) for p in parts) or 1.0
        for mot, part in zip(mots, parts):
            barre = "█" * round(14 * abs(part) / echelle)
            signe = "+" if part >= 0 else "−"
            print(f"      {mot:<16}{signe}{abs(part):.3f}  {barre}")

        figures.parts_des_mots(
            mots, parts, f"phase09_dossier{numero}_{nature.replace('é', 'e')}.png",
            f"Dossier {numero} ({nature}) — prédit « {dossier.classes[prediction]} », "
            f"vrai « {dossier.classes[int(vrais[indice_test])]} »")

    print("\n  Les trois commentaires sont dans RAPPORT.md — c'est ce qui manquait "
          "au dossier du disparu.")
    return dossier.retenir(9, **{nature: int(i) for nature, i in choisis.items()})
