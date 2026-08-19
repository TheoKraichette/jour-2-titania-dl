"""Les figures du rapport. Aucune fenêtre : le Conseil lit des fichiers."""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DOSSIER = "figures"


def chemin(nom):
    os.makedirs(DOSSIER, exist_ok=True)
    return os.path.join(DOSSIER, nom)


def poser(fig, nom):
    """Enregistre et annonce le chemin : le rapport pointe dessus."""
    cible = chemin(nom)
    fig.savefig(cible, dpi=120, bbox_inches="tight")
    plt.close(fig)
    print(f"  figure → {cible}")
    return cible


def courbes_de_perte(historiques, nom, titre, abscisse="itération"):
    """Perte d'apprentissage et perte de validation sur la même figure.

    L'énoncé, phase 3 : « aucun essai n'existe sans ses deux courbes ».

    historiques : {intitulé: (x, y)} — chaque courbe avec sa propre abscisse, pour
    pouvoir superposer deux essais qui n'ont ni la même durée ni le même nombre
    de passages (phase 5, phase 7).
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for intitule, (x, y) in historiques.items():
        ax.plot(x, y, label=intitule, linewidth=1.6)
    ax.set_xlabel(abscisse)
    ax.set_ylabel("perte")
    ax.set_title(titre)
    ax.legend()
    ax.grid(alpha=0.3)
    return poser(fig, nom)


def matrice_d_attention(poids, jetons_lignes, jetons_colonnes, nom, titre):
    """Une case par couple de mots, les mots eux-mêmes en étiquettes.

    L'énoncé, phase 10 : « un tableau de nombres bruts sans en-têtes ne passera pas ».
    """
    fig, ax = plt.subplots(figsize=(max(5, 0.5 * len(jetons_colonnes) + 2),
                                    max(4, 0.5 * len(jetons_lignes) + 1.5)))
    image = ax.imshow(poids, cmap="viridis", aspect="auto", vmin=0)
    ax.set_xticks(range(len(jetons_colonnes)), jetons_colonnes, rotation=60, ha="right")
    ax.set_yticks(range(len(jetons_lignes)), jetons_lignes)
    ax.set_xlabel("mot consulté")
    ax.set_ylabel("mot qui interroge")
    ax.set_title(titre)
    fig.colorbar(image, ax=ax, label="part du mélange")
    return poser(fig, nom)
