"""Acte 2 — le détecteur de formes.

Une tâche unique pour tout l'acte : `comments` entre, une forme sort.
"""

import torch

from bureau import entrainement, figures, jeu, mesures, modeles
from bureau.contexte import a_faire, titre


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


def phase03(dossier):
    """Battre le service statistique."""
    titre(3, "battre le service statistique")
    a_faire(
        """
        Trois décisions écrites et défendues : les 2 922 relevés sans forme, les deux
          fourre-tout (unknown, other), les doublons de sens (round/circle, changed/changing).
        Deux modèles sur exactement la même découpe et les mêmes classes : le linéaire
          sur comptages de mots (scikit-learn) et le vôtre en PyTorch. Le vôtre doit gagner.
        Le troisième point de comparaison : toujours répondre la forme la plus fréquente.
        À chaque essai, perte d'apprentissage ET perte de validation sur la même figure.
        Rendre : nombre de classes, nombre de relevés gardés, les trois règles, les trois scores.
        Savoir montrer le trajet du texte brut jusqu'au premier nombre qui entre dans le réseau.
        """
    )
    # Le socle est déjà là : bureau/jeu.py porte les trois décisions, preparer_le_jeu
    # les applique, mesures.montrer rend les trois scores côte à côte.


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
