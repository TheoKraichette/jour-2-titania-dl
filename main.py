"""Bureau d'Analyse Terrestre — partie 2 : le détecteur de formes.

Rejoue toutes les phases d'une traite, du téléchargement des relevés au dernier
chiffre affiché.

    python main.py                  toutes les phases
    python main.py --phases 0,2     seulement celles-là (mise au point)
    python main.py --rapide         jeu réduit — jamais pour un chiffre du rapport
"""

import argparse

from bureau import transmission
from bureau.actes import DEPUIS_LE_JEU, PHASES
from bureau.actes.acte2_detecteur import preparer_le_jeu
from bureau.contexte import Dossier
from bureau.entrainement import Chrono, fixer_graine


def lire_les_options():
    options = argparse.ArgumentParser(description=__doc__)
    options.add_argument(
        "--phases",
        default="",
        help="numéros séparés par des virgules, ou intervalle « 3-8 ». Défaut : toutes.",
    )
    options.add_argument("--graine", type=int, default=0)
    options.add_argument(
        "--rapide",
        action="store_true",
        help="jeu réduit pour mettre au point ; les chiffres rendus au Conseil "
        "se prennent toujours sans cette option.",
    )
    return options.parse_args()


def phases_demandees(demande):
    if not demande:
        return sorted(PHASES)
    voulues = set()
    for morceau in demande.split(","):
        if "-" in morceau:
            debut, fin = morceau.split("-")
            voulues.update(range(int(debut), int(fin) + 1))
        else:
            voulues.add(int(morceau))
    inconnues = voulues - set(PHASES)
    if inconnues:
        raise SystemExit(f"Phases inconnues : {sorted(inconnues)}")
    return sorted(voulues)


def main():
    options = lire_les_options()
    voulues = phases_demandees(options.phases)
    fixer_graine(options.graine)

    dossier = Dossier(graine=options.graine, rapide=options.rapide)
    if options.rapide:
        print("⚠ mode rapide : jeu réduit. Aucun chiffre d'ici ne va dans le rapport.")

    print(f"\n{'=' * 72}\nLA TRANSMISSION\n{'=' * 72}")
    dossier.df, dossier.rejets = transmission.charger()

    if any(numero >= DEPUIS_LE_JEU for numero in voulues):
        print(f"\n{'=' * 72}\nLE JEU : comments entre, une forme sort\n{'=' * 72}")
        preparer_le_jeu(dossier)

    with Chrono() as total:
        for numero in voulues:
            PHASES[numero](dossier)

    print(f"\n{'=' * 72}")
    print(f"Fin. {len(voulues)} phase(s) rejouée(s) en {total.secondes:.1f} s.")


if __name__ == "__main__":
    main()
