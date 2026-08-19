"""Acte 4 — emprunter un cerveau terrien.

« Ce qui est gros est bon. Ce qui est gros ne rentre pas. » Tout l'acte tient dans
cette tension. À partir d'ici, chaque affirmation du rapport s'accompagne de la
mesure qui la soutient, prise sur votre machine, avec le protocole décrit.

Dépendances : décommenter la section « acte 4 » de requirements.txt, puis
reconstruire l'image (docker compose build). Le cache des modèles va dans
/caches/huggingface, monté hors du dépôt.
"""

from bureau.contexte import a_faire, titre


def phase14(dossier):
    """Le cerveau emprunté, et sa facture."""
    titre(14, "le cerveau emprunté, et sa facture")
    a_faire(
        """
        Point de départ : le réseau de la phase 8 (vocabulaire des formes interdit) et son
        score, qui devient la ligne de référence. Mêmes relevés, même interdiction, même découpe.
        Choisir un modèle de langue déjà entraîné, librement récupérable, assez petit pour
        la machine. Trois régimes :
          1. aucune valeur interne modifiée — il lit, vous entraînez un minuscule étage au-dessus ;
          2. une partie dégelée, choisie et justifiée, et pas à la même vitesse selon qu'on est
             près de l'entrée ou près de la sortie (modeles.geler(..., sauf=...)) ;
          3. modèle intact, et n'entraîner que de très petites quantités de valeurs ajoutées à côté.
        Par régime, deux colonnes. Ce que ça donne : le score, comparé à celui de la phase 8.
        Ce que ça coûte : valeurs réellement modifiées (entrainement.compter_valeurs), temps
        d'un passage d'entraînement, mémoire maximale, poids de ce qu'il faut sauvegarder.
        Trancher en une phrase : lequel le Bureau peut se payer, et pourquoi.
        """
    )


def phase15(dossier):
    """Le Conseil pose des questions, vous citez vos sources."""
    titre(15, "le Conseil pose des questions, vous citez vos sources")
    a_faire(
        """
        Répondre en langue naturelle à des questions en langue naturelle, sur le fichier
        complet (88 875 relevés, y compris ceux sans forme, écartés de l'acte 2).
        Chaque réponse cite les relevés sur lesquels elle s'appuie, identifiables et
        retrouvables dans le fichier.
        Budget de texte donné au modèle avant qu'il réponde : c'est vous qui le fixez, il est
        écrit dans le rapport, il ne se dépasse jamais. La difficulté n'est pas de tenir dans
        le budget, c'est de choisir quoi y mettre parmi 88 875 candidats sans tout relire.
        La liste de questions s'écrit AVANT toute mesure et ne se retouche pas.
        Prévoir le cas où le fichier ne répond pas : « nous n'avons pas ce relevé » vaut
        mieux qu'une invention.
        Rendre : la liste, le budget, la proportion de réponses correctement sourcées, et la
        comparaison avec une recherche naïve par mots présents dans la question.
        Validé aussi quand la même question posée deux fois ramène les mêmes relevés.
        """
    )


def phase16(dossier):
    """Faire entrer le tout dans le vaisseau."""
    titre(16, "faire entrer le tout dans le vaisseau")
    a_faire(
        """
        AVANT de toucher à quoi que ce soit : mesurer le poids sur disque de ce que vous
        livreriez aujourd'hui et le temps de réponse sur votre machine. Puis annoncer par
        écrit la marge de score que vous acceptez de perdre. Cette phrase est datée par
        l'historique de commits et ne se réécrit pas après coup.
        Ensuite réduire : nettement moins lourd, nettement plus rapide, dans la marge annoncée.
        Mesurer et afficher les DEUX : le temps d'une réponse unique et le nombre de réponses
        par unité de temps. Ils ne varient pas ensemble et l'un peut cacher l'autre.
        Directions : représenter les valeurs plus grossièrement sans réentraîner ; livrer dans
        un format qui se charge et s'exécute seul ; ou faire apprendre à un petit modèle à
        reproduire les sorties du gros, hésitations comprises.
        Finir par la phrase : pourquoi vous vous êtes arrêté là.
        """
    )


def phase17(dossier):
    """Le faux témoignage."""
    titre(17, "le faux témoignage")
    a_faire(
        """
        Produire un faux témoignage que le Conseil ne saura pas distinguer des vrais :
        la longueur, le vocabulaire, la maladresse et la platitude des relevés du fichier.
        Règle absolue : aucune valeur interne du modèle ne bouge, ni par entraînement ni par
        ajustement. La seule marge d'action est la façon dont le modèle choisit chaque mot.
        Rendre les DEUX échecs : le réglage qui produit du texte propre et répétitif, et celui
        qui part n'importe où et invente des mots. Montrer que le point utilisable a été
        cherché méthodiquement (une grille), pas trouvé par hasard.
        Test en aveugle : mélanger les faux à de vrais relevés, faire trier par quelqu'un qui
        ne sait pas lesquels sont lesquels, rendre le résultat même s'il est mauvais.
        Prouver par le code qu'aucune valeur du modèle n'a bougé entre le premier essai et le dernier.
        """
    )
