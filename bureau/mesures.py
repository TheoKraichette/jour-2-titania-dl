"""Les scores rendus au Conseil, et les points de comparaison sans lesquels
ils ne veulent rien dire.

Deux façons de résumer un score donnent deux histoires différentes (phase 8) :
le taux global suit les classes nombreuses, la moyenne par classe suit les rares.
Les deux se rendent, toujours ensemble.
"""

import torch


def taux_de_reussite(predits, vrais):
    return (predits == vrais).float().mean().item()


def par_classe(predits, vrais, classes):
    """Rappel, précision et effectif pour chaque forme.

    C'est ce tableau qui montre, phase 8, quelles classes se sont effondrées quand
    on a interdit le vocabulaire des formes.
    """
    lignes = []
    for indice, nom in enumerate(classes):
        attendus = vrais == indice
        annonces = predits == indice
        justes = (attendus & annonces).sum().item()
        lignes.append(
            {
                "forme": nom,
                "effectif": int(attendus.sum().item()),
                "rappel": justes / max(int(attendus.sum().item()), 1),
                "precision": justes / max(int(annonces.sum().item()), 1),
            }
        )
    return lignes


def f1_moyen(predits, vrais, classes):
    """Moyenne non pondérée des F1 : une classe rare pèse autant qu'une fréquente."""
    total = 0.0
    for ligne in par_classe(predits, vrais, classes):
        r, p = ligne["rappel"], ligne["precision"]
        total += 2 * r * p / (r + p) if (r + p) else 0.0
    return total / max(len(classes), 1)


def toujours_la_plus_frequente(etiquettes_apprentissage, vrais):
    """Le point de comparaison le moins cher : répondre toujours la même chose.

    Phase 3 : le score du modèle se donne à côté de celui-là, sinon on ne sait pas
    ce qu'il a apporté.
    """
    majoritaire = torch.bincount(torch.as_tensor(etiquettes_apprentissage)).argmax()
    return taux_de_reussite(torch.full_like(vrais, int(majoritaire)), vrais)


def montrer(intitule, predits, vrais, classes, etiquettes_apprentissage=None):
    """Le bloc affiché à chaque essai : les deux résumés, et la baseline s'il y a."""
    print(f"\n  {intitule}")
    print(f"    classes                 : {len(classes)}")
    print(f"    relevés évalués         : {len(vrais)}")
    print(f"    taux de réussite        : {taux_de_reussite(predits, vrais):.3f}")
    print(f"    F1 moyen par classe     : {f1_moyen(predits, vrais, classes):.3f}")
    if etiquettes_apprentissage is not None:
        socle = toujours_la_plus_frequente(etiquettes_apprentissage, vrais)
        print(f"    toujours la plus fréquente : {socle:.3f}")


def tableau_par_classe(predits, vrais, classes, combien=None):
    lignes = sorted(par_classe(predits, vrais, classes), key=lambda l: -l["effectif"])
    print(f"\n    {'forme':<14}{'effectif':>9}{'rappel':>9}{'précision':>11}")
    for ligne in lignes[:combien]:
        print(
            f"    {ligne['forme']:<14}{ligne['effectif']:>9}"
            f"{ligne['rappel']:>9.3f}{ligne['precision']:>11.3f}"
        )
    return lignes
