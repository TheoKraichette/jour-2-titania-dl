"""Acte 3 — le Bureau apprend à relire.

Le mécanisme d'attention, écrit à la main. Droit aux tenseurs et aux opérations de
base : produits matriciels, softmax, couches linéaires. Exclus : les blocs tout
prêts, tout ce qui porte déjà le mot « attention » dans son nom, et les
bibliothèques de modèles préentraînés.

    scores = questions @ etiquettes.transpose(-2, -1) / dimension ** 0.5
    poids  = torch.softmax(scores, dim=-1)
    sortie = poids @ contenus

La division par la racine de la dimension ne se saute pas.
"""

from bureau.contexte import a_faire, titre


def phase10(dossier):
    """Chaque mot interroge les autres."""
    titre(10, "chaque mot interroge les autres")
    a_faire(
        """
        Partir d'un VRAI relevé du fichier, jamais d'une phrase inventée, contenant au
        moins un pronom ou une reprise. Découpage : celui du projet (jeu.jetons).
        Coder une seule tête entièrement à la main : trois vecteurs par mot, scores,
        proportions, mélange des contenus.
        Afficher la matrice des poids avec les mots en étiquettes de lignes et de
        colonnes (figures.matrice_d_attention).
        Validé quand : chaque ligne somme à 1, la sortie a la même forme que l'entrée,
        et vous savez désigner la case qui dit sur quel mot s'est appuyé le pronom.
        """
    )


def phase11(dossier):
    """Le Conseil mélange vos mots."""
    titre(11, "le Conseil mélange vos mots")
    a_faire(
        """
        D'abord prouver que le conseiller a raison : permuter les mots du relevé, refaire
        tourner le code de la phase 10, montrer chiffres en main que la sortie de chaque
        mot n'a pas bougé.
        Puis faire qu'elle bouge, SANS toucher au mécanisme : l'information de position
        s'ajoute aux vecteurs d'entrée, avant le calcul.
        Rendre le même écart mesuré de la même façon, avant et après. Le premier nul ou
        indistinguable de zéro, le second non. Les deux matrices de poids côte à côte.
        """
    )


def phase12(dossier):
    """Le Conseil demande la facture."""
    titre(12, "le Conseil demande la facture")
    a_faire(
        """
        Chronométrer votre propre attention (code de la phase 11, inchangé) sur des
        séquences de 32, 64, 128, 256 puis 512 jetons. Plusieurs mesures par longueur,
        on garde une valeur stable, pas un tir unique (bureau.entrainement.Chrono).
        Mesurer aussi la taille de la matrice de poids à chaque longueur, en nombre de cases.
        Une figure : longueur en abscisse, temps en ordonnée, axes nommés.
        Trois lignes : en doublant la longueur, par combien le temps est-il multiplié, et
        pourquoi ce facteur-là. Comparer vos mesures entre elles, pas à une référence.
        Finir par : à quelle longueur votre machine devient inutilisable, d'après vos chiffres.
        """
    )


def phase13(dossier):
    """Deux regards sur le même relevé."""
    titre(13, "deux regards sur le même relevé")
    a_faire(
        """
        Deux têtes en parallèle sur le même relevé, chacune avec ses propres vecteurs de
        question, d'étiquette et de contenu, recollées en une seule sortie.
        Démontrer qu'elles ne regardent pas la même chose : les deux matrices affichées
        côte à côte avec les mots en étiquettes, plus une mesure du désaccord, justifiée
        en une ligne.
        Le point de comparaison obligatoire : deux têtes qui partiraient identiques.
        Sans lui, le chiffre de désaccord ne veut rien dire.
        Écrire que les têtes ne sont pas entraînées, donc que les différences viennent de
        l'initialisation — et ce qu'on pourrait conclure de plus si elles l'étaient.
        """
    )
