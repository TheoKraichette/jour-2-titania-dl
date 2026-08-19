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
                 canaux=128, fenetre=3, dilatations=(1,), oubli=0.3, residuel=False,
                 norme=None):
        super().__init__()
        self.vecteurs = nn.Embedding(taille_vocabulaire, dimension, padding_idx=0)
        self.fenetre, self.dilatations, self.residuel = fenetre, dilatations, residuel
        entrees = dimension
        self.convolutions = nn.ModuleList()
        self.normes = nn.ModuleList()
        # La dilatation espace la fenêtre : une couche à dilatation d relie des
        # positions distantes de d, donc l'étendue grandit exponentiellement avec
        # la profondeur au lieu de linéairement. C'est ce qui permet de couvrir le
        # relevé entier en quatre couches (phase 6) plutôt qu'en quatorze.
        for dilatation in dilatations:
            self.convolutions.append(
                nn.Conv1d(entrees, canaux, kernel_size=fenetre,
                          padding=(fenetre // 2) * dilatation, dilation=dilatation)
            )
            # « lot » : normalise chaque canal avec les statistiques DU LOT — la
            # sortie d'un relevé dépend alors des autres relevés du lot, ce que la
            # phase 7 met en cause. « groupe » : mêmes statistiques, mais calculées
            # dans le relevé seul — aucun regard sur les voisins.
            self.normes.append(
                nn.BatchNorm1d(canaux) if norme == "lot"
                else nn.GroupNorm(1, canaux) if norme == "groupe"
                else nn.Identity()
            )
            entrees = canaux
        self.oubli = nn.Dropout(oubli)
        self.tete = nn.Linear(canaux, nombre_classes)

    def etendue_par_couche(self):
        """Ce que chaque couche ajoute à l'étendue vue par une sortie, et le cumul.

        Une convolution de fenêtre f et de dilatation d ajoute (f-1)·d : elle va
        chercher (f-1)/2 positions de chaque côté, à d positions d'écart.
        """
        etendue, lignes = 1, []
        for numero, dilatation in enumerate(self.dilatations, start=1):
            ajout = (self.fenetre - 1) * dilatation
            etendue += ajout
            lignes.append({"couche": numero, "dilatation": dilatation,
                           "ajout": ajout, "cumul": etendue})
        return lignes

    def cartes(self, jetons):
        """Les sorties de l'empilement, position par position, avant le maximum.

        Exposé pour la vérification expérimentale de la phase 6 : on y mesure
        jusqu'où se propage la modification d'un mot.
        """
        sortie = self.vecteurs(jetons).transpose(1, 2)  # (relevés, canaux, positions)
        for convolution, norme in zip(self.convolutions, self.normes):
            couche = torch.relu(norme(convolution(sortie)))
            # Connexion résiduelle : la couche apprend un écart plutôt qu'une
            # transformation entière, et le gradient garde un chemin direct vers
            # l'entrée. C'est la solution connue au problème connu de la phase 6 —
            # l'empilement qui dégrade le score.
            sortie = sortie + couche if (self.residuel
                                         and couche.shape == sortie.shape) else couche
        return sortie

    def forward(self, jetons):
        presents = (jetons != 0).unsqueeze(1)
        sortie = self.cartes(jetons)
        # Le remplissage est mis hors jeu avant le maximum sur les positions, sinon
        # les positions vides voteraient. Le maximum plutôt que la moyenne : une
        # tournure décisive peut n'apparaître qu'une fois dans le relevé.
        sortie = sortie.masked_fill(~presents[:, :, : sortie.shape[-1]], float("-inf"))
        resume = sortie.max(dim=-1).values.nan_to_num(neginf=0.0)
        return self.tete(self.oubli(resume))


# --- Acte 3 : le mécanisme du tableau, écrit à la main ----------------------
# Rien que des tenseurs et des opérations de base : produits matriciels, softmax,
# couches linéaires. Aucun bloc tout prêt, rien qui porte déjà le mot
# « attention » dans son nom, aucun modèle préentraîné.


class UneTete(nn.Module):
    """Phase 10 : chaque mot interroge les autres.

    Chaque mot fabrique trois vecteurs à partir de lui-même — la question (ce
    qu'il cherche dans la phrase), l'étiquette (ce qu'il annonce aux autres, sa
    vitrine), le contenu (ce qu'il donne réellement quand on l'a choisi). On
    compare la question de chacun à l'étiquette de tous, les scores deviennent
    des proportions qui somment à un, et chaque mot se réécrit comme le mélange
    des contenus, pesé par ces proportions.
    """

    def __init__(self, dimension):
        super().__init__()
        self.dimension = dimension
        self.question = nn.Linear(dimension, dimension, bias=False)
        self.etiquette = nn.Linear(dimension, dimension, bias=False)
        self.contenu = nn.Linear(dimension, dimension, bias=False)

    def forward(self, vecteurs):
        questions = self.question(vecteurs)
        etiquettes = self.etiquette(vecteurs)
        contenus = self.contenu(vecteurs)
        # La division par la racine de la dimension ne se saute pas : sans elle,
        # les scores partent trop loin, le softmax devient du tout ou rien et
        # plus rien n'apprend.
        scores = questions @ etiquettes.transpose(-2, -1) / self.dimension ** 0.5
        poids = torch.softmax(scores, dim=-1)
        return poids @ contenus, poids


def geler(module, sauf=()):
    """Acte 4, premier régime : le cerveau emprunté ne bouge pas d'une valeur.

    `sauf` : fragments de noms de paramètres laissés libres — c'est ainsi qu'on
    dégèle « ce qui est près de la sortie » sans toucher au reste.
    """
    for nom, parametre in module.named_parameters():
        parametre.requires_grad = any(fragment in nom for fragment in sauf)
    return module
