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
):
    """Une boucle d'apprentissage nue, sans magie et sans dépendance à la tâche.

    `lots_apprentissage` : un itérable rejouable de (entrées, cibles).
    Rend l'historique : {"passage", "temps", "perte", "perte_validation"}.
    """
    perte = perte or torch.nn.CrossEntropyLoss()
    optimiseur = torch.optim.AdamW(modele.parameters(), lr=pas)
    historique = {"passage": [], "temps": [], "perte": [], "perte_validation": []}

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
        if bavard and (iteration % (releve_tous_les * 10) == 0 or iteration == iterations):
            ligne = f"  passage {iteration:4d}  perte {historique['perte'][-1]:.4f}"
            if lots_validation is not None:
                ligne += f"  validation {historique['perte_validation'][-1]:.4f}"
            print(f"{ligne}  ({historique['temps'][-1]:.1f} s)")

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
