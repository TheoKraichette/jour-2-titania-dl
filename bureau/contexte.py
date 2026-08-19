"""Ce qui circule d'une phase à l'autre.

Les phases ne sont pas indépendantes : la 5 rejoue la 3, la 8 part de la 7, la 14
prend le score de la 8 comme ligne de référence. Ce qu'une phase établit et que
les suivantes doivent retrouver à l'identique passe par ici — surtout la découpe
et la liste des classes, qui doivent être les mêmes partout ou les scores ne se
comparent plus.
"""

from dataclasses import dataclass, field


@dataclass
class Dossier:
    graine: int = 0
    rapide: bool = False  # jeu réduit : pour mettre au point, jamais pour rendre

    # Acte 1 — la transmission
    df: object = None
    rejets: list = field(default_factory=list)

    # Acte 2 — le jeu texte → forme, fixé une fois pour toutes
    textes: list = field(default_factory=list)
    etiquettes: list = field(default_factory=list)
    classes: list = field(default_factory=list)
    decoupe: dict = field(default_factory=dict)
    vocabulaire: object = None
    longueur: int = 0

    # Les scores que les phases suivantes doivent battre ou retrouver
    scores: dict = field(default_factory=dict)
    temps: dict = field(default_factory=dict)

    def retenir(self, phase, **mesures):
        """Un chiffre mesuré ne se retape pas dans le rapport : il se relit ici."""
        self.scores.setdefault(phase, {}).update(mesures)
        return mesures


def titre(numero, nom):
    print(f"\n{'=' * 72}\nPHASE {numero} — {nom}\n{'=' * 72}")


def a_faire(exigences):
    """Ce qu'une phase non traitée affiche : sa liste de validation, pas un silence."""
    print("  ⧗ phase non traitée. Ce que le Conseil attend :")
    for ligne in exigences.strip().splitlines():
        print(f"    {ligne.strip()}")
