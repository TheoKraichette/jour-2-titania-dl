"""Les montages PyTorch du Bureau.

Tout ce qui apprend est écrit avec PyTorch — c'est le framework imposé de la semaine.

L'acte 3 ajoute ici l'attention écrite à la main : produits matriciels, softmax et
couches linéaires uniquement. Rien qui porte déjà le mot « attention » dans son nom,
aucun bloc tout prêt, aucune bibliothèque de modèles préentraînés.
"""

import torch
from torch import nn


class SacDeMots(nn.Module):
    """Le montage de départ : chaque mot devient un vecteur, on résume le relevé.

    Il ignore complètement l'ordre — c'est assumé et c'est le point de départ de
    l'acte 3, où le Conseil demandera si « elle » sait qu'il s'agit de « la lumière ».

    Deux résumés côte à côte plutôt qu'un seul. La moyenne dit de quoi parle
    l'ensemble du relevé ; le maximum dit si un mot déterminant est présent
    quelque part. Sur des témoignages de douze mots, la moyenne seule dilue le mot
    qui décide dans les onze autres.
    """

    def __init__(self, taille_vocabulaire, nombre_classes, dimension=64, cachee=128,
                 oubli=0.0, avec_maximum=True):
        super().__init__()
        self.vecteurs = nn.Embedding(taille_vocabulaire, dimension, padding_idx=0)
        self.avec_maximum = avec_maximum
        self.tete = nn.Sequential(
            nn.Dropout(oubli),
            nn.Linear(dimension * (2 if avec_maximum else 1), cachee),
            nn.ReLU(),
            nn.Dropout(oubli),
            nn.Linear(cachee, nombre_classes),
        )

    def forward(self, jetons):
        vecteurs = self.vecteurs(jetons)
        presents = (jetons != 0).unsqueeze(-1)
        # Moyenne sur les mots réellement présents : le remplissage ne doit pas
        # diluer les relevés courts (la moitié font 13 mots ou moins).
        compte = presents.sum(dim=1).clamp(min=1)
        resume = (vecteurs * presents).sum(dim=1) / compte
        if self.avec_maximum:
            # Le remplissage est mis hors jeu avant le maximum, sinon un relevé
            # court verrait ses zéros de remplissage gagner le maximum.
            masque = vecteurs.masked_fill(~presents, float("-inf"))
            # Un relevé sans un seul jeton connu a toutes ses positions masquées :
            # son maximum vaut -inf et suffit à mettre toute la perte à NaN.
            # Il existe : des témoignages ne contiennent que des entités HTML.
            maximum = masque.max(dim=1).values.nan_to_num(neginf=0.0)
            resume = torch.cat([resume, maximum], dim=-1)
        return self.tete(resume)


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
