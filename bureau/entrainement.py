"""La boucle d'apprentissage, et le chronomètre qui va avec.

Plusieurs phases se jugent au temps machine (5, 12, 14, 16) : l'historique porte
donc, pour chaque relevé de perte, le nombre de passages ET les secondes écoulées.
Une figure dont l'abscisse est le temps se trace directement depuis là.
"""

import random
import time

import numpy as np
import torch


def fixer_graine(graine=0):
    """Même graine, même tirage — mais pas forcément le même résultat au bit près.

    L'énoncé le dit : deux entraînements identiques divergent (ordre des additions
    flottantes, algorithmes choisis à la volée). Un écart plus petit que celui
    obtenu en relançant deux fois le même entraînement n'est pas un résultat.
    """
    random.seed(graine)
    np.random.seed(graine)
    torch.manual_seed(graine)


class Chrono:
    """Temps machine mesuré dans le code, affiché, comparable d'une phase à l'autre.

    Toujours comparer deux mesures prises sur la même machine : si un essai passe
    sur Colab, les deux essais passent sur Colab.
    """

    def __init__(self, intitule=""):
        self.intitule = intitule
        self.depart = None
        self.secondes = None

    def __enter__(self):
        self.depart = time.perf_counter()
        return self

    def __exit__(self, *_):
        self.secondes = time.perf_counter() - self.depart
        if self.intitule:
            print(f"  ⏱ {self.intitule} : {self.secondes:.2f} s")
        return False

    @property
    def ecoule(self):
        return time.perf_counter() - self.depart


def entrainer(
    modele,
    lots_apprentissage,
    lots_validation=None,
    iterations=100,
    pas=1e-3,
    perte=None,
    releve_tous_les=1,
    bavard=True,
    garder_le_meilleur=False,
    decroissance=1e-2,
):
    """Une boucle d'apprentissage nue, sans magie et sans dépendance à la tâche.

    `lots_apprentissage` : un itérable rejouable de (entrées, cibles).
    Rend l'historique : {"passage", "temps", "perte", "perte_validation"}.

    `garder_le_meilleur` : rendre le modèle dans l'état où sa perte de validation
    était la plus basse, et non dans son dernier état. Sans ça, on livre le modèle
    au moment où il a le plus surappris — c'est le dernier passage qui est le pire.
    """
    perte = perte or torch.nn.CrossEntropyLoss()
    optimiseur = torch.optim.AdamW(modele.parameters(), lr=pas,
                                   weight_decay=decroissance)
    historique = {"passage": [], "temps": [], "perte": [], "perte_validation": []}
    meilleure, meilleur_etat, meilleur_passage = float("inf"), None, None

    debut = time.perf_counter()
    for iteration in range(1, iterations + 1):
        modele.train()
        cumul, lots = 0.0, 0
        for entrees, cibles in lots_apprentissage:
            optimiseur.zero_grad()
            valeur = perte(modele(entrees), cibles)
            valeur.backward()
            optimiseur.step()
            cumul += valeur.item()
            lots += 1

        if iteration % releve_tous_les and iteration != iterations:
            continue

        historique["passage"].append(iteration)
        historique["temps"].append(time.perf_counter() - debut)
        historique["perte"].append(cumul / max(lots, 1))
        historique["perte_validation"].append(
            evaluer_perte(modele, lots_validation, perte)
            if lots_validation is not None
            else float("nan")
        )
        if historique["perte_validation"][-1] < meilleure:
            meilleure, meilleur_passage = historique["perte_validation"][-1], iteration
            if garder_le_meilleur:
                meilleur_etat = {n: v.detach().clone()
                                 for n, v in modele.state_dict().items()}
        if bavard and (iteration % (releve_tous_les * 10) == 0 or iteration == iterations):
            ligne = f"  passage {iteration:4d}  perte {historique['perte'][-1]:.4f}"
            if lots_validation is not None:
                ligne += f"  validation {historique['perte_validation'][-1]:.4f}"
            print(f"{ligne}  ({historique['temps'][-1]:.1f} s)")

    if garder_le_meilleur and meilleur_etat is not None:
        modele.load_state_dict(meilleur_etat)
        print(f"  état retenu : passage {meilleur_passage} "
              f"(validation {meilleure:.4f}), et non le dernier")
    historique["meilleur_passage"] = meilleur_passage
    return historique


@torch.no_grad()
def evaluer_perte(modele, lots, perte):
    modele.eval()
    cumul, nombre = 0.0, 0
    for entrees, cibles in lots:
        cumul += perte(modele(entrees), cibles).item()
        nombre += 1
    return cumul / max(nombre, 1)


@torch.no_grad()
def predire(modele, lots):
    """Les prédictions et les vérités, dans l'ordre des lots."""
    modele.eval()
    predits, vrais = [], []
    for entrees, cibles in lots:
        predits.append(modele(entrees).argmax(dim=-1))
        vrais.append(cibles)
    return torch.cat(predits), torch.cat(vrais)


def compter_valeurs(modele):
    """« Combien de valeurs vous avez réellement modifiées » — colonne coût, acte 4.

    Rend (modifiées, totales) : c'est l'écart entre les deux qui fait tout
    l'intérêt des régimes gelé / partiellement dégelé / petites valeurs ajoutées.
    """
    totales = sum(p.numel() for p in modele.parameters())
    modifiees = sum(p.numel() for p in modele.parameters() if p.requires_grad)
    return modifiees, totales
