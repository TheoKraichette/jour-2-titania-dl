"""Le registre des phases : numéro → fonction. main.py ne connaît que ça."""

from bureau.actes import acte1_heritage as a1
from bureau.actes import acte2_detecteur as a2
from bureau.actes import acte3_attention as a3
from bureau.actes import acte4_emprunt as a4

PHASES = {
    0: a1.phase00,
    1: a1.phase01,
    2: a2.phase02,
    3: a2.phase03,
    4: a2.phase04,
    5: a2.phase05,
    6: a2.phase06,
    7: a2.phase07,
    8: a2.phase08,
    9: a2.phase09,
    10: a3.phase10,
    11: a3.phase11,
    12: a3.phase12,
    13: a3.phase13,
    14: a4.phase14,
    15: a4.phase15,
    16: a4.phase16,
    17: a4.phase17,
}

# Les phases qui ont besoin du jeu texte → forme construit (acte 2 et au-delà).
DEPUIS_LE_JEU = 2
