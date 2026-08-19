"""Acte 4 — emprunter un cerveau terrien.

« Ce qui est gros est bon. Ce qui est gros ne rentre pas. » Tout l'acte tient dans
cette tension. À partir d'ici, chaque affirmation du rapport s'accompagne de la
mesure qui la soutient, prise sur votre machine, avec le protocole décrit.

Le cerveau emprunté est bert-tiny (google/bert_uncased_L-2_H-128_A-2) : 4,4
millions de valeurs, deux couches, librement récupérable — et assez petit pour
cette machine sans accélérateur, ce qui est la contrainte de l'énoncé. Son cache
va dans /caches/huggingface, hors du dépôt.
"""

import io
import resource
import time

import torch
from torch import nn

from bureau import entrainement, jeu, mesures, modeles
from bureau.actes.acte2_detecteur import PHASE6, entrees_censurees
from bureau.contexte import a_faire, titre

EMPRUNTE = "google/bert_uncased_L-2_H-128_A-2"
LONGUEUR = 48  # jetons du modèle emprunté ; ses morceaux de mots sont plus courts

# Le score de la phase 8 (réseau maison, vocabulaire des formes interdit) : la
# ligne de référence de tout l'acte. Pire des trois initialisations.
PHASE8 = {"taux": 0.3299, "f1": 0.1547}


def jeu_pour_l_emprunte(dossier):
    """Les mêmes relevés, la même interdiction, la même découpe — mais le
    découpage en jetons du modèle emprunté, ce qui est un changement documenté."""
    from transformers import AutoTokenizer

    interdits = jeu.mots_interdits(dossier.classes)
    textes, _, _ = entrees_censurees(dossier, interdits)
    decoupeur = AutoTokenizer.from_pretrained(EMPRUNTE)
    parties = {}
    for partie in ("apprentissage", "validation", "test"):
        indices = dossier.decoupe[partie]
        jetons = decoupeur([textes[i] for i in indices], truncation=True,
                           max_length=LONGUEUR, padding="max_length",
                           return_tensors="pt")
        parties[partie] = {
            "entrees": jetons["input_ids"],
            "masque": jetons["attention_mask"],
            "cibles": torch.tensor([dossier.etiquettes[i] for i in indices]),
        }
    return parties


class EmprunteEtTete(nn.Module):
    """Le cerveau emprunté, une tête de classement posée dessus."""

    def __init__(self, emprunte, nombre_classes):
        super().__init__()
        self.emprunte = emprunte
        self.tete = nn.Linear(emprunte.config.hidden_size, nombre_classes)

    def forward(self, entrees, masque):
        sortie = self.emprunte(input_ids=entrees, attention_mask=masque)
        return self.tete(sortie.last_hidden_state[:, 0])  # le jeton de résumé


def memoire_maximale_mo():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def poids_a_sauvegarder(parametres):
    tampon = io.BytesIO()
    torch.save({str(i): p.detach() for i, p in enumerate(parametres)}, tampon)
    return tampon.tell() / 1e6


def entrainer_un_regime(modele, parties, poids_classes, passages=2, taille=128,
                        groupes_de_pas=None):
    """La boucle d'un régime : perte pondérée comme partout, état de meilleure
    validation, chrono du premier passage."""
    perte = nn.CrossEntropyLoss(weight=poids_classes)
    optimiseur = torch.optim.AdamW(
        groupes_de_pas or [{"params": [p for p in modele.parameters()
                                       if p.requires_grad], "lr": 1e-3}])
    app = parties["apprentissage"]
    meilleur, meilleur_etat, temps_premier_passage = float("inf"), None, None
    for passage in range(passages):
        modele.train()
        depart = time.perf_counter()
        ordre = torch.randperm(len(app["cibles"]))
        for debut in range(0, len(ordre), taille):
            tranche = ordre[debut:debut + taille]
            optimiseur.zero_grad()
            valeur = perte(modele(app["entrees"][tranche], app["masque"][tranche]),
                           app["cibles"][tranche])
            valeur.backward()
            optimiseur.step()
        if temps_premier_passage is None:
            temps_premier_passage = time.perf_counter() - depart
        validation = evaluer_perte_regime(modele, parties["validation"], perte)
        if validation < meilleur:
            meilleur = validation
            meilleur_etat = {n: v.detach().clone()
                             for n, v in modele.state_dict().items()}
    modele.load_state_dict(meilleur_etat)
    return temps_premier_passage


@torch.no_grad()
def evaluer_perte_regime(modele, partie, perte):
    modele.eval()
    cumul, nombre = 0.0, 0
    for debut in range(0, len(partie["cibles"]), 512):
        tranche = slice(debut, debut + 512)
        cumul += perte(modele(partie["entrees"][tranche], partie["masque"][tranche]),
                       partie["cibles"][tranche]).item()
        nombre += 1
    return cumul / nombre


@torch.no_grad()
def predire_regime(modele, partie):
    modele.eval()
    predits = []
    for debut in range(0, len(partie["cibles"]), 512):
        tranche = slice(debut, debut + 512)
        predits.append(modele(partie["entrees"][tranche],
                              partie["masque"][tranche]).argmax(dim=-1))
    return torch.cat(predits)


def phase14(dossier):
    """Le cerveau emprunté, et sa facture.

    Trois régimes sur les mêmes relevés censurés, la même découpe, la même perte
    pondérée. Par régime, deux colonnes : ce que ça donne, ce que ça coûte.
    """
    from transformers import AutoModel

    titre(14, "le cerveau emprunté, et sa facture")
    entrainement.fixer_graine(dossier.graine)

    parties = jeu_pour_l_emprunte(dossier)
    vrais = parties["test"]["cibles"]
    effectifs = torch.bincount(parties["apprentissage"]["cibles"]).float()
    poids_classes = effectifs ** -0.25
    poids_classes = poids_classes / poids_classes.mean()

    print(f"  cerveau emprunté : {EMPRUNTE}")
    print(f"  mêmes relevés (censurés), même découpe, même perte que la phase 8 ; "
          f"le découpage en\n  jetons est celui du modèle emprunté — c'est le "
          f"changement documenté de l'acte.")
    print(f"  ligne de référence, le réseau de la phase 8 : "
          f"taux {PHASE8['taux']:.4f}   F1 {PHASE8['f1']:.4f}")
    print("  une seule initialisation par régime : les écarts attendus sont grands "
          "devant la\n  dispersion de 0,01 mesurée en phase 3.\n")

    bilans = []

    def mesurer_regime(nom, modele, temps_passage, parametres_entraines):
        predits = predire_regime(modele, parties["test"])
        bilan = {
            "nom": nom,
            "taux": mesures.taux_de_reussite(predits, vrais),
            "f1": mesures.f1_moyen(predits, vrais, dossier.classes),
            "modifiees": sum(p.numel() for p in parametres_entraines),
            "temps": temps_passage,
            "memoire": memoire_maximale_mo(),
            "disque": poids_a_sauvegarder(parametres_entraines),
        }
        bilans.append(bilan)
        print(f"    {nom:<34} taux {bilan['taux']:.4f}   F1 {bilan['f1']:.4f}"
              f"   {bilan['modifiees']:>9,} valeurs   {bilan['temps']:.0f} s/passage"
              f"   {bilan['disque']:.2f} Mo à sauvegarder".replace(",", " "))
        return bilan

    # --- Régime 1 : aucune valeur interne ne bouge --------------------------------
    print("  régime 1 — gelé : le cerveau lit, seule une tête minuscule s'entraîne")
    entrainement.fixer_graine(dossier.graine)
    emprunte = AutoModel.from_pretrained(EMPRUNTE)
    modele = EmprunteEtTete(emprunte, len(dossier.classes))
    modeles.geler(modele.emprunte)
    temps = entrainer_un_regime(modele, parties, poids_classes)
    mesurer_regime("gelé (tête seule)", modele, temps,
                   [p for p in modele.tete.parameters()])

    # --- Régime 2 : une partie dégelée, à des vitesses différentes ----------------
    # La dernière couche est celle qui fabrique le résumé : c'est elle qu'on
    # autorise à s'adapter à la tâche, dix fois plus lentement que la tête —
    # elle sait déjà lire, la tête ne sait encore rien.
    print("\n  régime 2 — dégel partiel : la dernière couche, dix fois plus "
          "lentement que la tête")
    entrainement.fixer_graine(dossier.graine)
    emprunte = AutoModel.from_pretrained(EMPRUNTE)
    modele = EmprunteEtTete(emprunte, len(dossier.classes))
    modeles.geler(modele.emprunte, sauf=("encoder.layer.1.", "pooler"))
    entraines = [p for p in modele.parameters() if p.requires_grad]
    temps = entrainer_un_regime(
        modele, parties, poids_classes,
        groupes_de_pas=[
            {"params": list(modele.tete.parameters()), "lr": 1e-3},
            {"params": [p for n, p in modele.emprunte.named_parameters()
                        if p.requires_grad], "lr": 1e-4},
        ])
    mesurer_regime("dégel partiel (dernière couche)", modele, temps, entraines)

    # --- Régime 3 : le modèle intact, de petites valeurs ajoutées à côté ----------
    print("\n  régime 3 — valeurs ajoutées : le cerveau intact, des détours de "
          "rang 4 sur ses\n  couches d'attention")
    entrainement.fixer_graine(dossier.graine)
    emprunte = AutoModel.from_pretrained(EMPRUNTE)
    modeles.geler(emprunte)
    for couche in emprunte.encoder.layer:
        couche.attention.self.query = modeles.AjoutBasRang(
            couche.attention.self.query)
        couche.attention.self.value = modeles.AjoutBasRang(
            couche.attention.self.value)
    modele = EmprunteEtTete(emprunte, len(dossier.classes))
    entraines = [p for p in modele.parameters() if p.requires_grad]
    temps = entrainer_un_regime(modele, parties, poids_classes)
    mesurer_regime("valeurs ajoutées (rang 4)", modele, temps, entraines)

    # --- Le tableau, et la décision ------------------------------------------------
    total = sum(p.numel() for p in modele.parameters())
    print(f"\n  {'régime':<34}{'taux':>8}{'F1':>8}{'valeurs modifiées':>19}"
          f"{'s/passage':>11}{'mémoire':>9}{'à garder':>10}")
    print(f"  {'réseau de la phase 8 (référence)':<34}{PHASE8['taux']:>8.4f}"
          f"{PHASE8['f1']:>8.4f}{'toutes (1,3 M)':>19}{'~25':>11}{'—':>9}{'—':>10}")
    for bilan in bilans:
        print(f"  {bilan['nom']:<34}{bilan['taux']:>8.4f}{bilan['f1']:>8.4f}"
              f"{bilan['modifiees']:>19,}{bilan['temps']:>11.0f}"
              f"{bilan['memoire']:>8.0f}M{bilan['disque']:>9.2f}M"
              .replace(",", " "))
    print(f"  (le cerveau compte {total:,} valeurs ; la mémoire est le pic du "
          f"processus, cumulatif)".replace(",", " "))

    dossier.emprunte = {"parties": parties, "poids_classes": poids_classes}
    return dossier.retenir(14, bilans=[{k: v for k, v in b.items()} for b in bilans])


# La liste de questions, figée avant toute mesure — elle ne se retouche pas.
# Le fichier est en anglais, les questions aussi ; leurs traductions sont dans le
# rapport. La dernière est le contrôle : le fichier n'a rien pour y répondre.
QUESTIONS = [
    "What do witnesses who mention a sound or a noise describe?",
    "What do witnesses report seeing over water or a lake?",
    "Do witnesses describe objects landing on the ground?",
    "What colors do witnesses associate with fast moving objects?",
    "Do sightings above cities have a particular shape?",
    "Did any witness describe an elephant flying over a city?",
]
BUDGET_JETONS = 600  # jetons donnés au modèle avant qu'il réponde ; jamais dépassé
CITES = 5            # relevés cités par réponse
SEUIL_PERTINENCE = 0.5  # cosinus minimal du meilleur relevé, fixé d'avance


def phase15(dossier):
    """Le Conseil pose des questions, vous citez vos sources.

    Le fichier complet — 88 875 relevés, y compris ceux sans forme, écartés de
    l'acte 2. Le cerveau emprunté résume chaque témoignage en un vecteur, une
    fois ; chaque question devient un vecteur comparé à tous, et seuls les
    relevés retenus entrent dans le budget de texte du modèle qui répond.
    """
    import polars as pl
    from transformers import (AutoModel, AutoModelForCausalLM, AutoTokenizer)

    titre(15, "le Conseil pose des questions, vous citez vos sources")
    entrainement.fixer_graine(dossier.graine)

    fichier = dossier.df.with_row_index("ligne").filter(
        pl.col("comments").is_not_null() & (pl.col("comments") != ""))
    textes = [jeu.nettoyer(t)[:135] for t in fichier["comments"]]
    print(f"  fichier complet : {len(textes)} témoignages (dont ceux sans forme)")
    print(f"  budget de texte : {BUDGET_JETONS} jetons, {CITES} relevés cités, "
          f"seuil de pertinence {SEUIL_PERTINENCE}")

    # --- Le fichier entier, résumé une fois en vecteurs ---------------------------
    decoupeur = AutoTokenizer.from_pretrained(EMPRUNTE)
    lecteur = AutoModel.from_pretrained(EMPRUNTE)
    lecteur.eval()

    def vecteurs_de(textes_a_lire, intitule):
        morceaux = []
        with torch.no_grad():
            for debut in range(0, len(textes_a_lire), 512):
                jetons = decoupeur(textes_a_lire[debut:debut + 512],
                                   truncation=True, max_length=LONGUEUR,
                                   padding=True, return_tensors="pt")
                sortie = lecteur(**jetons).last_hidden_state
                masque = jetons["attention_mask"].unsqueeze(-1)
                moyenne = (sortie * masque).sum(1) / masque.sum(1)
                morceaux.append(nn.functional.normalize(moyenne, dim=-1))
        return torch.cat(morceaux)

    depart = time.perf_counter()
    bibliotheque = vecteurs_de(textes, "fichier")
    print(f"  lecture du fichier par le cerveau emprunté : "
          f"{time.perf_counter() - depart:.0f} s, une seule fois")

    # --- Le modèle qui répond ------------------------------------------------------
    plume_jetons = AutoTokenizer.from_pretrained("distilgpt2")
    plume = AutoModelForCausalLM.from_pretrained("distilgpt2")
    plume.eval()

    mots_vides = set("what do witnesses who mention a the of or an any did over "
                     "above describe report seeing on to with is are have has".split())

    for numero, question in enumerate(QUESTIONS, start=1):
        print(f"\n  question {numero} : « {question} »")
        vecteur = vecteurs_de([question], "question")

        # Deux recherches : la sémantique (le cerveau emprunté) et la naïve
        # (les mots de la question présents tels quels dans le relevé).
        similarites = bibliotheque @ vecteur.squeeze(0)
        meilleurs = similarites.topk(CITES)
        mots_question = [m for m in jeu.jetons(question) if m not in mots_vides]
        comptes = torch.tensor([
            sum(m in texte.lower() for m in mots_question) for texte in textes])
        naifs = comptes.topk(CITES).indices

        if meilleurs.values[0].item() < SEUIL_PERTINENCE:
            print(f"    meilleur cosinus {meilleurs.values[0]:.3f} < "
                  f"{SEUIL_PERTINENCE} : nous n'avons pas ce relevé.")
            continue

        # Le budget : les relevés retenus, tronqués pour tenir, et pas un de plus.
        extraits, consommes = [], 0
        for rang, indice in enumerate(meilleurs.indices.tolist(), start=1):
            ligne = fichier.row(indice, named=True)
            extrait = textes[indice][:110]
            cout = len(plume_jetons.encode(extrait)) + 8
            if consommes + cout > BUDGET_JETONS - 60:  # 60 gardés pour la question
                break
            consommes += cout
            extraits.append((rang, ligne, extrait, similarites[indice].item()))

        amorce = ("Witness reports:\n"
                  + "\n".join(f"- {extrait}" for _, _, extrait, _ in extraits)
                  + f"\nQuestion: {question}\nAnswer from the reports: The witnesses")
        jetons_amorce = plume_jetons(amorce, return_tensors="pt")
        assert jetons_amorce["input_ids"].shape[1] <= BUDGET_JETONS, "budget dépassé"
        with torch.no_grad():
            suite = plume.generate(**jetons_amorce, max_new_tokens=45,
                                   do_sample=False, no_repeat_ngram_size=3,
                                   pad_token_id=plume_jetons.eos_token_id)
        reponse = plume_jetons.decode(
            suite[0][jetons_amorce["input_ids"].shape[1]:]).split("\n")[0].strip()

        print(f"    contexte : {jetons_amorce['input_ids'].shape[1]} jetons "
              f"(budget {BUDGET_JETONS})")
        print(f"    réponse  : The witnesses {reponse}")
        print(f"    sources  :")
        for rang, ligne, extrait, similarite in extraits:
            print(f"      [{similarite:.3f}] ligne {ligne['ligne']} — "
                  f"{ligne['datetime']} {str(ligne['city'])[:20]} : "
                  f"« {extrait[:70]} »")
        recouvrement = len(set(meilleurs.indices.tolist()) & set(naifs.tolist()))
        print(f"    recherche naïve (mots de la question) : "
              f"{recouvrement}/{CITES} relevés en commun ; ses meilleurs :")
        for indice in naifs.tolist()[:2]:
            print(f"      ({int(comptes[indice])} mots) "
                  f"« {textes[indice][:70]} »")

    # La même question posée deux fois : tout est déterministe (vecteurs figés,
    # génération sans tirage), les relevés cités sont les mêmes — vérifié :
    v1 = vecteurs_de([QUESTIONS[0]], "q")
    v2 = vecteurs_de([QUESTIONS[0]], "q")
    memes = torch.equal((bibliotheque @ v1.squeeze(0)).topk(CITES).indices,
                        (bibliotheque @ v2.squeeze(0)).topk(CITES).indices)
    print(f"\n  la même question posée deux fois ramène les mêmes relevés : {memes}")
    print("  la proportion de réponses correctement sourcées se juge en lisant : "
          "elle est dans le rapport.")
    return dossier.retenir(15, questions=len(QUESTIONS), budget=BUDGET_JETONS,
                           deterministe=bool(memes))


# La marge de score annoncée avant toute optimisation, datée par l'historique de
# commits : voir RAPPORT.md, phase 16. Elle ne se réécrit pas après coup.
MARGE_DE_SCORE = 0.01  # en taux et en F1 : au-delà, la réduction est refusée


def mesurer_le_systeme(modele, parties, repetitions=200):
    """Les trois mesures du vaisseau : poids sur disque, temps d'une réponse
    unique, réponses par seconde en traitement par lots. Les deux dernières ne
    varient pas ensemble — c'est pour ça qu'on les affiche toutes les deux."""
    tampon = io.BytesIO()
    torch.save(modele, tampon)
    poids_mo = tampon.tell() / 1e6

    seul = (parties["test"]["entrees"][:1], parties["test"]["masque"][:1])
    lot = (parties["test"]["entrees"][:256], parties["test"]["masque"][:256])
    with torch.no_grad():
        for _ in range(10):
            modele(*seul)
        temps = []
        for _ in range(repetitions):
            depart = time.perf_counter()
            modele(*seul)
            temps.append(time.perf_counter() - depart)
        temps.sort()
        latence_ms = temps[len(temps) // 2] * 1000
        depart = time.perf_counter()
        for _ in range(5):
            modele(*lot)
        debit = 5 * 256 / (time.perf_counter() - depart)
    return poids_mo, latence_ms, debit


def phase16(dossier):
    """Faire entrer le tout dans le vaisseau.

    D'abord mesurer ce qu'on livrerait aujourd'hui, la marge de score étant déjà
    annoncée et commitée. Ensuite réduire, remesurer au même protocole, et dire
    pourquoi on s'est arrêté là.
    """
    from transformers import AutoModel

    titre(16, "faire entrer le tout dans le vaisseau")
    entrainement.fixer_graine(dossier.graine)

    if getattr(dossier, "emprunte", None) is None:
        dossier.emprunte = {"parties": jeu_pour_l_emprunte(dossier)}
        effectifs = torch.bincount(
            dossier.emprunte["parties"]["apprentissage"]["cibles"]).float()
        poids = effectifs ** -0.25
        dossier.emprunte["poids_classes"] = poids / poids.mean()
    parties = dossier.emprunte["parties"]
    vrais = parties["test"]["cibles"]

    # Ce qu'on livrerait aujourd'hui : le régime gelé de la phase 14, réentraîné
    # à l'identique (déterministe par graine).
    print("  le système livré : le cerveau emprunté et sa tête (régime gelé de la "
          "phase 14)")
    emprunte = AutoModel.from_pretrained(EMPRUNTE)
    modele = EmprunteEtTete(emprunte, len(dossier.classes))
    modeles.geler(modele.emprunte)
    entrainer_un_regime(modele, parties, dossier.emprunte["poids_classes"])
    modele.eval()

    def score_de(m):
        predits = predire_regime(m, parties["test"])
        return (mesures.taux_de_reussite(predits, vrais),
                mesures.f1_moyen(predits, vrais, dossier.classes))

    print(f"\n  marge annoncée d'avance (commitée avant toute optimisation) : "
          f"{MARGE_DE_SCORE} de taux et de F1")
    taux_avant, f1_avant = score_de(modele)
    poids_avant, latence_avant, debit_avant = mesurer_le_systeme(modele, parties)
    print(f"\n  {'':<24}{'poids disque':>14}{'réponse unique':>16}"
          f"{'réponses/s':>12}{'taux':>8}{'F1':>8}")
    print(f"  {'avant':<24}{poids_avant:>12.1f} Mo{latence_avant:>13.1f} ms"
          f"{debit_avant:>12.0f}{taux_avant:>8.4f}{f1_avant:>8.4f}")

    # --- Direction 1 : représenter les valeurs plus grossièrement, sans
    # réentraîner — les couches linéaires passent en entiers de 8 bits.
    reduit = torch.ao.quantization.quantize_dynamic(
        modele, {nn.Linear}, dtype=torch.qint8)
    taux_apres, f1_apres = score_de(reduit)
    poids_apres, latence_apres, debit_apres = mesurer_le_systeme(reduit, parties)
    print(f"  {'quantifié 8 bits':<24}{poids_apres:>12.1f} Mo"
          f"{latence_apres:>13.1f} ms{debit_apres:>12.0f}"
          f"{taux_apres:>8.4f}{f1_apres:>8.4f}")

    # --- Direction 2 : un format qui se charge et s'exécute seul, sans
    # l'attirail d'entraînement ni le code du projet.
    exemple = (parties["test"]["entrees"][:1], parties["test"]["masque"][:1])
    with torch.no_grad():
        autonome = torch.jit.trace(reduit, exemple, strict=False)
    tampon = io.BytesIO()
    torch.jit.save(autonome, tampon)
    print(f"  {'+ format autonome':<24}{tampon.tell() / 1e6:>12.1f} Mo"
          f"{'(se charge et s’exécute seul, sans le code du projet)':>52}")

    dans_la_marge = (taux_avant - taux_apres <= MARGE_DE_SCORE
                     and f1_avant - f1_apres <= MARGE_DE_SCORE)
    print(f"\n  facteurs : poids ÷{poids_avant / poids_apres:.1f}, réponse unique "
          f"×{latence_avant / latence_apres:.1f} plus rapide, débit "
          f"×{debit_apres / debit_avant:.1f}")
    print(f"  écart de score : {taux_avant - taux_apres:+.4f} de taux, "
          f"{f1_avant - f1_apres:+.4f} de F1 — "
          + ("dans la marge annoncée ✓" if dans_la_marge
             else "HORS de la marge annoncée ✗"))
    print("\n  pourquoi s'arrêter là : la troisième direction — apprendre à un "
          "petit modèle à imiter\n  le gros — coûte des heures d'entraînement pour "
          "un cerveau qui ne pèse déjà que quelques\n  mégaoctets ; le gain "
          "suivant est réel mais la facture d'électricité de l'obtenir dépasse\n  "
          "ce que le vaisseau y gagnerait.")

    return dossier.retenir(
        16, marge=MARGE_DE_SCORE,
        avant={"poids": poids_avant, "latence": latence_avant,
               "debit": debit_avant, "taux": taux_avant, "f1": f1_avant},
        apres={"poids": poids_apres, "latence": latence_apres,
               "debit": debit_apres, "taux": taux_apres, "f1": f1_apres},
        dans_la_marge=dans_la_marge,
    )


GRILLE = [(0.2, 20), (0.5, 20), (0.7, 50), (0.9, 50), (1.2, 200), (1.6, 0)]
RECOMMANDE = (0.9, 50)


def empreinte_des_valeurs(modele):
    """Une empreinte de toutes les valeurs internes : si une seule bouge, elle change."""
    import hashlib

    condensat = hashlib.sha256()
    for _, parametre in sorted(modele.state_dict().items()):
        condensat.update(parametre.numpy().tobytes())
    return condensat.hexdigest()[:16]


def phase17(dossier):
    """Le faux témoignage.

    Le modèle emprunté, tel quel : aucune valeur interne ne bouge, ni par
    entraînement ni par ajustement — la preuve par l'empreinte. La seule marge
    d'action est la façon de choisir chaque mot au moment d'écrire, et elle est
    cherchée méthodiquement, sur une grille.
    """
    import polars as pl
    from transformers import AutoModelForCausalLM, AutoTokenizer

    titre(17, "le faux témoignage")

    plume_jetons = AutoTokenizer.from_pretrained("distilgpt2")
    plume = AutoModelForCausalLM.from_pretrained("distilgpt2")
    plume.eval()
    empreinte_avant = empreinte_des_valeurs(plume)

    # L'étalon de style : de vrais relevés courts, tirés de façon reproductible.
    fichier = dossier.df.filter(
        pl.col("comments").is_not_null()
        & (pl.col("comments").str.len_chars().is_between(50, 120)))
    generateur = torch.Generator().manual_seed(dossier.graine)
    tirage = torch.randperm(fichier.height, generator=generateur)[:8].tolist()
    etalons = [jeu.nettoyer(fichier["comments"][i]).strip() for i in tirage]
    amorce = ("".join(f"Report: {t}\n" for t in etalons[:3]) + "Report:")
    jetons_amorce = plume_jetons(amorce, return_tensors="pt")

    def ecrire(temperature, tronque, graine):
        torch.manual_seed(graine)
        with torch.no_grad():
            suite = plume.generate(
                **jetons_amorce, max_new_tokens=32, do_sample=True,
                temperature=temperature,
                top_k=tronque if tronque else 0,
                pad_token_id=plume_jetons.eos_token_id)
        texte = plume_jetons.decode(suite[0][jetons_amorce["input_ids"].shape[1]:])
        return texte.split("\n")[0].strip()

    # --- La grille, parcourue méthodiquement ---------------------------------------
    print("  la grille : température × nombre de mots candidats (0 = tous)\n")
    for temperature, tronque in GRILLE:
        exemple = ecrire(temperature, tronque, dossier.graine)
        marque = ("  ← trop propre, tourne en rond" if temperature <= 0.2
                  else "  ← part n'importe où" if temperature >= 1.6
                  else "  ← retenu" if (temperature, tronque) == RECOMMANDE else "")
        print(f"    t={temperature:<4} k={tronque:<4} « {exemple[:76]} »{marque}")

    # --- Le tri en aveugle -----------------------------------------------------------
    faux = [ecrire(*RECOMMANDE, graine=dossier.graine + i) for i in range(1, 6)]
    vrais_temoins = etalons[3:8]
    melange = [(t, "faux") for t in faux] + [(t, "vrai") for t in vrais_temoins]
    ordre = torch.randperm(len(melange),
                           generator=torch.Generator().manual_seed(7)).tolist()
    print("\n  le tri en aveugle — dix témoignages mélangés, à trier par quelqu'un "
          "qui ne sait pas :\n")
    for numero, indice in enumerate(ordre, start=1):
        print(f"    {numero:>2}. {melange[indice][0][:100]}")
    print("\n  la clef du tri (à ne pas montrer au trieur) : "
          + ", ".join(f"{n}={melange[i][1]}"
                      for n, i in enumerate(ordre, start=1)))
    print("  le résultat du tri est dans le rapport, rendu même s'il est mauvais.")

    empreinte_apres = empreinte_des_valeurs(plume)
    print(f"\n  empreinte des valeurs du modèle avant le premier essai : "
          f"{empreinte_avant}")
    print(f"  empreinte après le dernier essai                        : "
          f"{empreinte_apres}")
    print(f"  aucune valeur n'a bougé : {empreinte_avant == empreinte_apres}")

    return dossier.retenir(17, empreintes_identiques=empreinte_avant == empreinte_apres,
                           reglage=RECOMMANDE)
