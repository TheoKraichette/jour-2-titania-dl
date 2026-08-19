"""Les montages PyTorch du Bureau.

Tout ce qui apprend est écrit avec PyTorch — c'est le framework imposé de la semaine.

L'acte 3 ajoute ici l'attention écrite à la main : produits matriciels, softmax et
couches linéaires uniquement. Rien qui porte déjà le mot « attention » dans son nom,
aucun bloc tout prêt, aucune bibliothèque de modèles préentraînés.
"""

import torch
from torch import nn


class Empilement(nn.Module):
    """Le montage qui a un avantage que le comptage ne peut pas avoir : l'ordre.

    Un sac de mots plafonne, et le linéaire du service statistique y est déjà : à
    information égale, il est optimal. La seule information qu'il n'a pas est la
    suite des mots — « lumière derrière la colline » et « colline derrière la
    lumière » sont le même sac.

    Chaque couche fait glisser une fenêtre sur le relevé et combine les positions
    voisines. Les poids sont partagés entre toutes les positions, donc le montage
    apprend une tournure (« bright light », « shaped object ») au lieu de retenir
    un relevé — donner les paires de mots comme jetons à part avait précisément
    échoué là-dessus, les paires rares servant d'empreintes des relevés.

    Toutes les positions sont traitées de front, jamais l'une après l'autre : la
    contrainte de la phase 6 est déjà respectée ici. Chaque couche ajoute
    `fenetre - 1` à l'étendue vue par une sortie, ce que la phase 6 devra tabuler.
    """

    def __init__(self, taille_vocabulaire, nombre_classes, dimension=64,
                 canaux=128, fenetre=3, couches=1, oubli=0.3):
        super().__init__()
        self.vecteurs = nn.Embedding(taille_vocabulaire, dimension, padding_idx=0)
        self.fenetre, self.couches_demandees = fenetre, couches
        entrees = dimension
        self.convolutions = nn.ModuleList()
        for _ in range(couches):
            self.convolutions.append(
                nn.Conv1d(entrees, canaux, kernel_size=fenetre, padding=fenetre // 2)
            )
            entrees = canaux
        self.oubli = nn.Dropout(oubli)
        self.tete = nn.Linear(canaux, nombre_classes)

    def etendue_par_couche(self):
        """Ce que chaque couche ajoute à l'étendue vue, et le cumul. Phase 6."""
        etendue, lignes = 1, []
        for numero in range(1, self.couches_demandees + 1):
            ajout = self.fenetre - 1
            etendue += ajout
            lignes.append({"couche": numero, "ajout": ajout, "cumul": etendue})
        return lignes

    def forward(self, jetons):
        presents = (jetons != 0).unsqueeze(1)
        sortie = self.vecteurs(jetons).transpose(1, 2)  # (relevés, canaux, positions)
        for convolution in self.convolutions:
            sortie = torch.relu(convolution(sortie))
        # Le remplissage est mis hors jeu avant le maximum sur les positions, sinon
        # les positions vides voteraient. Le maximum plutôt que la moyenne : une
        # tournure décisive peut n'apparaître qu'une fois dans le relevé.
        sortie = sortie.masked_fill(~presents[:, :, : sortie.shape[-1]], float("-inf"))
        resume = sortie.max(dim=-1).values.nan_to_num(neginf=0.0)
        return self.tete(self.oubli(resume))


# --- Acte 3 : à écrire à la main ------------------------------------------
#
# class UneTete(nn.Module):
#     """Phase 10. Trois vecteurs par mot : question, étiquette, contenu.
#
#         scores = questions @ etiquettes.transpose(-2, -1) / dimension ** 0.5
#         poids  = torch.softmax(scores, dim=-1)
#         sortie = poids @ contenus
#
#     La division par la racine de la dimension ne se saute pas.
#     Rendre aussi les poids : c'est la matrice « qui regarde qui » du rapport.
#     """
#
# class Positions(nn.Module):
#     """Phase 11. L'ordre n'est nulle part dans le calcul ci-dessus : on l'ajoute
#     aux vecteurs d'entrée, avant l'attention, jamais après."""
#
# class PlusieursTetes(nn.Module):
#     """Phase 13. Le même calcul en parallèle, avec des jeux de vecteurs
#     différents, puis on recolle et on repasse dans une couche."""


def geler(module, sauf=()):
    """Acte 4, premier régime : le cerveau emprunté ne bouge pas d'une valeur.

    `sauf` : fragments de noms de paramètres laissés libres — c'est ainsi qu'on
    dégèle « ce qui est près de la sortie » sans toucher au reste.
    """
    for nom, parametre in module.named_parameters():
        parametre.requires_grad = any(fragment in nom for fragment in sauf)
    return module
