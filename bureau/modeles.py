"""Les montages PyTorch du Bureau.

Tout ce qui apprend est écrit avec PyTorch — c'est le framework imposé de la semaine.

L'acte 3 ajoute ici l'attention écrite à la main : produits matriciels, softmax et
couches linéaires uniquement. Rien qui porte déjà le mot « attention » dans son nom,
aucun bloc tout prêt, aucune bibliothèque de modèles préentraînés.
"""

import torch
from torch import nn


class SacDeMots(nn.Module):
    """Le montage de départ : chaque mot devient un vecteur, on en fait la moyenne.

    Il ignore complètement l'ordre — c'est assumé et c'est le point de départ de
    l'acte 3, où le Conseil demandera si « elle » sait qu'il s'agit de « la lumière ».
    """

    def __init__(self, taille_vocabulaire, nombre_classes, dimension=64, cachee=128,
                 oubli=0.0):
        super().__init__()
        self.vecteurs = nn.Embedding(taille_vocabulaire, dimension, padding_idx=0)
        self.tete = nn.Sequential(
            nn.Dropout(oubli),
            nn.Linear(dimension, cachee),
            nn.ReLU(),
            nn.Dropout(oubli),
            nn.Linear(cachee, nombre_classes),
        )

    def forward(self, jetons):
        vecteurs = self.vecteurs(jetons)
        presents = (jetons != 0).unsqueeze(-1).float()
        # Moyenne sur les mots réellement présents : le remplissage ne doit pas
        # diluer les relevés courts (la moitié font 13 mots ou moins).
        moyenne = (vecteurs * presents).sum(dim=1) / presents.sum(dim=1).clamp(min=1)
        return self.tete(moyenne)


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
