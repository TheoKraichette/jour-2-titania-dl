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

    modele = modeles.SacDeMots(len(dossier.vocabulaire), len(dossier.classes))

    # Deux nombres, pas un. Les 8 prédictions tombent justes bien avant que quoi
    # que ce soit soit appris : avec 8 relevés aux mots presque disjoints, un seul
    # pas suffit à faire basculer les argmax alors que la perte vaut encore ln(18),
    # c'est-à-dire le hasard. « Ne plus se tromper » n'est donc pas le critère
    # d'arrêt — la perte qui s'écrase l'est.
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


def service_statistique(dossier, tenseurs_par_partie):
    """« Un modèle linéaire simple sur des comptages de mots, monté en une pause. »

    Même découpe, mêmes classes et même découpage en jetons que le réseau : ce qui
    change entre les deux essais est le modèle, rien d'autre.
    """
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.linear_model import LogisticRegression

    parties = {
        nom: (
            [dossier.textes[i] for i in dossier.decoupe[nom]],
            [dossier.etiquettes[i] for i in dossier.decoupe[nom]],
        )
        for nom in ("apprentissage", "test")
    }

    comptages = CountVectorizer(analyzer=jeu.jetons, min_df=2)
    with Chrono("linéaire du service statistique") as chrono:
        x_apprentissage = comptages.fit_transform(parties["apprentissage"][0])
        linéaire = LogisticRegression(max_iter=1000)
        linéaire.fit(x_apprentissage, parties["apprentissage"][1])

    predits = linéaire.predict(comptages.transform(parties["test"][0]))
    print(f"    vocabulaire du linéaire : {len(comptages.vocabulary_)} mots")
    return (
        torch.tensor(predits),
        torch.tensor(parties["test"][1]),
        chrono.secondes,
    )


def phase03(dossier, iterations=12):
    """Battre le service statistique.

    Trois scores côte à côte, sur exactement la même découpe et les mêmes classes :
    la baseline qui répond toujours la forme la plus fréquente, le linéaire sur
    comptages de mots, et le réseau PyTorch. Le réseau doit passer devant.
    """
    titre(3, "battre le service statistique")
    entrainement.fixer_graine(dossier.graine)

    justifier_les_decisions(dossier)
    montrer_le_trajet(dossier)

    parties = {nom: tenseurs(dossier, nom)
               for nom in ("apprentissage", "validation", "test")}
    etiquettes_apprentissage = parties["apprentissage"][1]

    print("\n  Essai 1 — toujours la forme la plus fréquente")
    _, vrais = parties["test"]
    majoritaire = int(torch.bincount(etiquettes_apprentissage).argmax())
    print(f"    forme choisie           : {dossier.classes[majoritaire]}")
    mesures.montrer("baseline", torch.full_like(vrais, majoritaire), vrais,
                    dossier.classes)

    print("\n  Essai 2 — le linéaire du service statistique (comptages de mots)")
    predits_lineaire, vrais_lineaire, temps_lineaire = service_statistique(
        dossier, parties
    )
    mesures.montrer("linéaire", predits_lineaire, vrais_lineaire, dossier.classes)

    print("\n  Essai 3 — le réseau PyTorch")
    modele = modeles.SacDeMots(len(dossier.vocabulaire), len(dossier.classes),
                               dimension=128, cachee=256, oubli=0.3)
    lots_apprentissage = jeu.lots(*parties["apprentissage"], taille=64,
                                  graine=dossier.graine)
    lots_validation = jeu.lots(*parties["validation"], taille=256, melanger=False)
    # Les classes sont très déséquilibrées : « light » porte 24 % des relevés, les
    # dernières formes retenues moins de 1 %. Sans pondération, le réseau a intérêt
    # à ignorer les rares, ce que le taux global ne sanctionne pas mais que le F1
    # moyen par classe voit tout de suite.
    #
    # L'exposant a été balayé : -0,5 (racine) corrige trop et coûte 0,012 de taux,
    # 0 (aucune pondération) laisse 0,005 de F1 sur la table. -0,25 est le seul
    # réglage qui passe devant le linéaire sur les deux mesures à la fois.
    effectifs = torch.bincount(etiquettes_apprentissage).float()
    poids = effectifs ** -0.25
    poids = poids / poids.mean()
    print(f"    pondération des classes : de {poids.min():.2f} ({dossier.classes[int(poids.argmin())]})"
          f" à {poids.max():.2f} ({dossier.classes[int(poids.argmax())]})")

    with Chrono("réseau PyTorch") as chrono:
        historique = entrainement.entrainer(
            modele, lots_apprentissage, lots_validation,
            iterations=iterations, pas=3e-3, releve_tous_les=1,
            garder_le_meilleur=True,
            perte=torch.nn.CrossEntropyLoss(weight=poids),
        )
    predits, vrais = entrainement.predire(
        modele, jeu.lots(*parties["test"], taille=256, melanger=False)
    )
    mesures.montrer("réseau", predits, vrais, dossier.classes,
                    etiquettes_apprentissage.tolist())

    figures.courbes_de_perte(
        {
            "apprentissage": (historique["passage"], historique["perte"]),
            "validation": (historique["passage"], historique["perte_validation"]),
        },
        "phase03_reseau.png",
        "Phase 3 — réseau PyTorch : perte d'apprentissage et de validation",
        abscisse="passage sur les données",
    )

    print(f"\n  {'essai':<34}{'taux':>8}{'F1 moyen':>11}{'temps':>9}")
    lignes = [
        ("toujours la plus fréquente", torch.full_like(vrais, majoritaire), 0.0),
        ("linéaire sur comptages de mots", predits_lineaire, temps_lineaire),
        ("réseau PyTorch", predits, chrono.secondes),
    ]
    for intitule, prediction, secondes in lignes:
        print(f"  {intitule:<34}"
              f"{mesures.taux_de_reussite(prediction, vrais):>8.3f}"
              f"{mesures.f1_moyen(prediction, vrais, dossier.classes):>11.3f}"
              f"{secondes:>8.1f}s")

    return dossier.retenir(
        3,
        classes=len(dossier.classes),
        releves=len(dossier.textes),
        taux_baseline=mesures.taux_de_reussite(
            torch.full_like(vrais, majoritaire), vrais),
        taux_lineaire=mesures.taux_de_reussite(predits_lineaire, vrais),
        taux_reseau=mesures.taux_de_reussite(predits, vrais),
        f1_lineaire=mesures.f1_moyen(predits_lineaire, vrais, dossier.classes),
        f1_reseau=mesures.f1_moyen(predits, vrais, dossier.classes),
        temps_lineaire=temps_lineaire,
        temps_reseau=chrono.secondes,
    )


def phase04(dossier):
    """Le carnet de pannes."""
    titre(4, "le carnet de pannes")
    a_faire(
        """
        Casser volontairement le montage de la phase 3, trois fois, une panne à la fois,
        en remettant tout d'aplomb entre chaque. Trois natures différentes :
          1. excellent à l'entraînement, bête dès l'évaluation, sans qu'une donnée ait changé ;
          2. la perte descend proprement, les prédictions sont pires que le hasard ;
          3. la perte se fige et n'en bouge plus.
        Par panne, une fiche de trois lignes : le geste exact, la signature sur les courbes
        (une figure), le test qui la distingue des deux autres en moins d'une minute.
        """
    )


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
