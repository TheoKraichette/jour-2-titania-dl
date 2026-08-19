# Rapport au Conseil — le détecteur de formes

> Squelette. Chaque section porte les chiffres mesurés par `main.py` et les
> décisions prises. Une phase n'est finie que quand le chiffre demandé est ici
> **et** que `main.py` le reproduit. Les décisions qui ont mal tourné se
> racontent aussi : un rapport qui ne contient que des réussites est incomplet.

---

## Acte 1 — l'héritage

### Phase 0 — refaire les calculs du disparu

Date retenue : **`datetime`**, la date d'observation, et non `date_posted`, la
date de publication. À défendre en une phrase : la recommandation porte sur le
jour où la population regarde le ciel, pas sur le jour où le Bureau a saisi le
formulaire.

Période couverte : 1990-01-01 → 2014-05-08, soit **8 894 jours**, 81 501 relevés.

| Affirmation du dossier | Lui | Nous |
|---|---|---|
| jours couverts | 8 894 | 8 894 |
| relevés par jour | 9,2 | 9,2 |
| un 4 juillet | 51 | 51 |
| samedi | 17,7 % | 17,7 % |
| lundi | 12,6 % | 12,6 % |
| juillet | 11,3 % | 11,3 % |
| février | 6,2 % | 6,2 % |

Le dénominateur du 4 juillet est le nombre de 4 juillet **couverts par la
période** (24 : la transmission s'arrête le 8 mai 2014), pas le nombre d'années
où il s'est trouvé un relevé ce jour-là.

Ce que le dossier ne donnait pas :

- maximum en une seule journée : **206 relevés, le 4 juillet 2010** ;
- rang du 4 juillet dans le classement des journées : **1er sur 7 663**. Quatre
  des cinq journées les plus chargées de toute la transmission sont des 4 juillet.

La cinquième affirmation, « le volume croît continûment d'une année sur l'autre
jusqu'à la fin de la transmission », ne se vérifie pas au pied de la lettre : il y
a 8 baisses d'une année sur l'autre sur la date d'observation, 4 sur la date de
publication. C'est une tendance, pas une monotonie. Figure :
`figures/phase00_volume_annuel.png`.

#### À quelle question chaque chiffre répond

C'est le point qui manquait au dossier du disparu : ses chiffres étaient justes,
mais il ne disait pas ce qu'ils mesuraient, et c'est ce flou qui a permis de leur
faire dire autre chose.

**8 894 jours** répond à : sur quelle étendue de temps la transmission s'étale-t-elle,
du premier au dernier relevé ? Ce n'est pas le nombre de jours où quelque chose a
été signalé — il n'y a de relevés que sur 7 663 journées distinctes. C'est le
dénominateur de la moyenne suivante, et rien d'autre.

**9,2 relevés par jour** répond à : combien de signalements une journée quelconque
de la période porte-t-elle en moyenne ? C'est un repère, celui qui permet de dire
qu'une journée est chargée ou non. Ce n'est pas le nombre d'observations d'un jour
typique : la distribution est très déséquilibrée, la moyenne est tirée vers le haut
par les dernières années et par une poignée de journées énormes.

**51 relevés un 4 juillet** répond à : combien de signalements un 4 juillet porte-t-il
en moyenne, sur les 24 4 juillet couverts par la transmission ? Le dénominateur est
le nombre de 4 juillet de la période, pas le nombre d'années où il s'est trouvé un
relevé ce jour-là — une année sans aucun signalement le 4 juillet compte comme un
4 juillet à zéro. En divisant par 23 au lieu de 24, on obtient 53 et on ne retombe
plus sur le dossier.

**17,7 % le samedi et 12,6 % le lundi** répondent à : comment les signalements se
répartissent-ils sur les sept jours de la semaine ? Ils mesurent une habitude
humaine — on sort le samedi soir — et pas une activité du ciel, qui n'a aucune
raison de connaître les jours de la semaine.

**11,3 % en juillet et 6,2 % en février** répondent à la même question sur les douze
mois. Là encore, cela parle du comportement des témoins : les nuits d'été sont
douces et on est dehors.

**206 relevés le 4 juillet 2010** répond à : quelle est la journée la plus chargée de
toute la transmission, et combien porte-t-elle ? C'est un maximum ponctuel, sur une
seule journée d'une seule année, pas une moyenne.

**Rang 1 sur 7 663 journées** répond à : où se situe le 4 juillet dans le classement
des journées les plus chargées ? Quatre des cinq premières places sont des 4 juillet,
mais toutes se situent entre 2009 et 2013.

Sur la date, enfin : j'utilise `datetime`, la date de l'observation, parce que toutes
ces questions portent sur le moment où les gens ont regardé le ciel. `date_posted`
répond à une autre question, celle de savoir quand le Bureau a enregistré le
formulaire, et elle donne d'ailleurs une courbe annuelle différente.

### Phase 1 — le chiffre était vrai, la flotte est perdue

#### Ce que le chiffre disait réellement

Le chiffre du dossier est juste : un 4 juillet, la transmission enregistre 51
relevés, contre 9,2 un jour ordinaire. Cinq fois et demie plus. Ce que ce chiffre
dit, et c'est tout ce qu'il dit : ce jour-là, il y a beaucoup plus de signalements
enregistrés que d'habitude.

Le dossier en a tiré autre chose. Il a écrit que la population est habituée à voir
des choses dans le ciel ce soir-là, donc qu'elle ne prêtera pas attention à une
flotte. C'est un saut. Le chiffre compte des signalements, pas de l'inattention.

Trois autres lectures tiennent aussi bien, à partir du même nombre.

D'abord, il y a simplement plus de monde dehors. Jour férié, soirée d'été, les gens
sont dans la rue et regardent en l'air. Le pic mesure alors la taille du public, pas
son indifférence — et un public nombreux est le contraire de ce qu'on cherche pour
passer inaperçu.

Ensuite, il y a réellement plus de choses dans le ciel : feux d'artifice, lanternes,
avions de parade. Dans ce cas le pic ne mesure ni l'attention au ciel ni des objets
inconnus, il mesure des confusions.

Enfin, un pic ne suppose pas une fête. Le 16 novembre 1999 porte 195 relevés et
c'est le deuxième jour le plus chargé du fichier. Ce n'est ni Halloween ni le
Nouvel An. Le raisonnement du dossier ne s'applique pas à cette journée-là, alors
qu'elle ressemble beaucoup au 4 juillet du point de vue du comptage.

Il faut ajouter une remarque sur la solidité de ce chiffre. Les grands 4 juillet
sont 2010 (206 relevés), 2012 (191), 2013 (180) et 2011 (155). Le pic est concentré
sur la fin de la transmission. Ce n'est pas une régularité observée depuis 1990.

Rien dans les nombres ne permet de choisir entre « les gens sont blasés et
ignoreront » et « les gens regardent et signaleront ». Les deux produisent le même
51. Pour trancher, il faut lire ce que les témoins écrivent. Le dossier ne l'a pas
fait, et c'est là que la flotte a été perdue.

#### Trois relevés, recopiés tels quels

`1993-07-04 23:45 — tooele city — shape: sphere`

> 4 intense glowing green &quot;Stop-light&quot; type orbs holding tight diamond
> formation.  Not Fireworks...

Le témoin écarte lui-même l'explication du feu d'artifice. Il n'est pas blasé, il
trie, et il tient à le préciser. Pour le comptage, ce relevé est une unité parmi 51.

`1995-07-04 22:00 — tacoma (waterfront area) — shape: circle`

> MANY PEOPLE ON DOCK WAITING FOR FIREWORKS DISPLAY SEE A RED CIRCLE HOVERING AND
> THEN MOVE SLOWLY WEST.

Une foule immobile, rassemblée, qui attend un spectacle dans le ciel et qui a donc
déjà les yeux levés. C'est l'inverse exact de l'inattention supposée par le dossier.

`1997-07-04 20:30 — st. charles — shape: light`

> We were at a local fireworks display.  Just before dusk&#44 I looked up in the
> sky with my son and saw a large green object shooting acros

Même configuration, et le témoin distingue nettement le spectacle auquel il assiste
de la chose qu'il a vue passer.

Ces trois textes racontent la même journée que le chiffre 51, et ils en donnent une
lecture opposée : le 4 juillet est le moment où le plus grand nombre de personnes
regardent volontairement le ciel, et où elles font la différence entre un feu
d'artifice et autre chose. Le pic n'était pas une couverture, c'était un avertissement.

#### La commande passée au Conseil

Ce que le comptage ne tranchera jamais : parmi les 51 signalements d'un 4 juillet,
combien décrivent un objet structuré, et combien décrivent un feu d'artifice ? Le
comptage répond 51 dans les deux cas. Il faudrait lire les 51 textes.

D'où la tâche demandée, en une phrase que le Conseil peut répéter :

> **Entre** : le texte écrit par un témoin. **Sort** : la forme qu'il décrit, choisie
> parmi les formes connues du Bureau.

La colonne `shape` du fichier contient déjà cette information pour les relevés
existants. Elle sert donc à vérifier les réponses du système avant de lui faire
confiance sur un relevé neuf.

---

## Acte 2 — le détecteur de formes

Tâche : `comments` entre, une forme sort.

### Phase 2 — le test d'acceptation du Bureau

8 relevés appris par coeur. Figure : `figures/phase02_test_acceptation.png`.

- les 8 prédictions tombent justes dès l'itération 2, alors que la perte vaut
  encore 2,36 pour un hasard à ln(18) = 2,89. « Ne plus se tromper » n'est donc pas
  le bon critère d'arrêt sur 8 relevés ;
- mémorisation franche (perte < 1e-3) à l'itération **17**, perte finale 5,9e-4 ;
- les 8 prédictions finales tombent sur les 8 vraies formes.

Ce que ce test prouve : le montage relie l'entrée à la sortie et la correction
circule. Ce qu'il ne prouve pas : qu'il apprendra quoi que ce soit de généralisable.

#### Ce qui a cédé, dans l'ordre

Ça n'a pas marché du premier coup, mais pas comme je l'attendais : le montage a
réussi le test trop vite, et c'est le test qui était faux.

**Premier essai.** J'avais écrit exactement ce que demande l'énoncé : entraîner
jusqu'à ne plus se tromper sur un seul des 8 relevés, et rendre le nombre
d'itérations qu'il a fallu. Le script a annoncé 1 itération, 8/8 justes, perte 2,88.
Le chiffre de la perte m'a arrêté : ln(18) vaut 2,89, c'est-à-dire qu'un modèle qui
répondrait au hasard sur 18 classes aurait cette perte-là. Le montage avait donc
« réussi » sans avoir rien appris.

**Ce que j'ai compris.** Avec seulement 8 relevés dont les mots sont presque tous
différents, un seul pas d'optimisation suffit à pousser le bon logit au-dessus des
17 autres pour chacun des 8. Les prédictions deviennent justes alors que les
probabilités sont encore quasi uniformes. Sur 8 exemples, « ne plus se tromper » est
un critère qui se satisfait par accident.

**Ce que j'ai changé.** Un seul geste : le critère d'arrêt. Je continue jusqu'à ce
que la perte passe sous 1e-3, et je relève au passage l'itération où les 8
prédictions deviennent justes. Le script rend maintenant les deux nombres, parce que
l'écart entre les deux est le résultat intéressant : 2 pour les prédictions, 17 pour
la mémorisation réelle.

**Ce que ça m'a appris pour la suite.** Un compte de bonnes réponses sur un petit
échantillon ne prouve pas qu'un montage apprend, et un chiffre ne vaut rien sans la
valeur à laquelle on le compare. Ici c'est ln(18) qui a servi de révélateur : sans
ce point de comparaison, j'aurais validé le test d'acceptation sur un montage dont je
ne savais rien.

### Phase 3 — battre le service statistique

#### Les quatre décisions sur le jeu

Chaque décision change le nombre de classes, donc le score. Les comptes ci-dessous
sont ceux que le script affiche, pas des estimations.

**Les 2 922 relevés sans forme : écartés du jeu supervisé.** Ils n'ont pas
d'étiquette à apprendre, et en inventer une reviendrait à fabriquer la réponse que
je prétends prédire. Je ne les supprime pas pour autant : ils restent dans le
fichier chargé et l'acte 4 travaillera dessus, puisque la recherche par question ne
demande pas d'étiquette.

**Les deux fourre-tout `unknown` et `other` : écartés, 12 566 relevés.** C'est la
décision la plus coûteuse, elle retire un relevé sur six. Elle se défend parce que
ces deux valeurs ne sont pas des formes : ce sont l'absence de forme. Demander à un
réseau de reconnaître « la description d'une chose qu'on n'a pas su nommer » n'a pas
de sens, et les garder aurait gonflé le score global sans qu'on sache de quoi —
`unknown` aurait servi de fourre-tout aux prédictions incertaines.

**Les doublons de sens : fusionnés vers la graphie la plus fréquente.** `round` →
`circle` (2 + 8 453 relevés) et `changed` → `changing` (1 + 2 140). Les deux
graphies rares sont anecdotiques, mais les laisser à part créerait deux classes
impossibles à départager d'une classe voisine — un réseau qui hésite entre `round`
et `circle` serait compté en erreur alors qu'il a raison. La fusion fait passer les
valeurs distinctes de 30 à 28.

**Les classes sous 300 relevés : écartées, 7 classes pour 279 relevés.** `cross`,
`delta`, `crescent`, `pyramid`, `flare`, `hexagon`, `dome`. Avec la découpe en
trois, une classe de 30 relevés n'en a que 4 ou 5 en test : son score serait
gouverné par le hasard du tirage, et elle abîmerait le F1 moyen par classe sans rien
mesurer de réel. Le seuil de 300 vient de l'énoncé lui-même, qui signale que 18 des
29 valeurs dépassent ce compte.

**Ce qu'il reste : 18 classes, 72 904 relevés**, découpés en 51 034 / 10 935 /
10 935 (apprentissage / validation / test). Cette découpe est tirée une seule fois
et réutilisée par toutes les phases suivantes, sans quoi aucun score ne serait
comparable à un autre.

#### Du texte brut au premier nombre

Sur un relevé réel de la partie apprentissage :

```
1. texte brut  « Stationary intermitient flashes »
2. nettoyé     « Stationary intermitient flashes »      (entités HTML retirées)
3. jetons      ['stationary', 'intermitient', 'flashes']
4. indices     [139, 1, 452, 0, 0, 0, 0, 0, 0, …]
```

Le premier nombre qui entre dans le réseau est donc **139**, le rang du mot
`stationary` dans un vocabulaire de 10 093 mots construit sur la seule partie
apprentissage. Deux valeurs sont réservées : `0` pour le remplissage et `1` pour un
mot inconnu — c'est le sort de `intermitient`, faute de frappe du témoin vue une
seule fois, donc absente du vocabulaire. Le réseau reçoit un vecteur de 29 entiers
(le 99ᵉ centile des longueurs), puis remplace chaque entier par un vecteur qu'il
apprend.

Le vocabulaire est construit sur l'apprentissage seul, jamais sur tout le jeu :
sinon un mot vu uniquement en test serait déjà connu du réseau, et la découpe
fuirait.

#### Le journal des réglages

Le premier montage du réseau perdait contre le linéaire. Voici ce que j'ai touché,
un réglage à la fois, chacun avec sa mesure — y compris celui qui n'a rien rapporté.
Le point de comparaison est le linéaire du service statistique : **taux 0,537, F1
moyen par classe 0,494**.

| Réglage | Taux | F1 moyen | Temps |
|---|---|---|---|
| montage de départ | 0,495 | 0,428 | 83 s |
| 1 — garder l'état de meilleure validation, pas le dernier | 0,525 | 0,437 | 83 s |
| 2 — oubli de 0,3 sur la tête | 0,540 | 0,462 | 133 s |
| 3 — maximum concaténé à la moyenne | 0,544 | 0,480 | 124 s |
| 4 — 30 passages au lieu de 12 | 0,544 | 0,480 | 330 s |
| 5 — pondération des classes en 1/√effectif | 0,532 | 0,496 | 105 s |

**Réglage 1.** La perte de validation est au plus bas dès le passage 2 sur 12 :
tout ce que le réseau gagne ensuite en apprentissage, il le perd en validation.
Livrer le dernier état, c'est livrer le modèle au moment où il a le plus surappris.
L'entraînement va quand même jusqu'au bout, pour que la courbe montre la divergence.

**Réglage 2.** L'oubli déplace le meilleur point du passage 2 au passage 5 : le
réseau peut enfin apprendre un moment avant de mémoriser. La perte d'apprentissage
cesse de plonger — 1,24 au lieu de 0,73 — et c'est le but, pas un échec.

**Réglage 3.** La moyenne des vecteurs de mots dit de quoi parle le relevé entier ;
le maximum dit si un mot déterminant est présent quelque part. Sur douze mots, la
moyenne seule dilue le mot qui décide dans les onze autres. C'est le F1 par classe
qui en profite le plus, ce qui est cohérent : une forme rare se reconnaît à un mot
précis.

En chemin, une panne : perte à NaN dès le premier passage, taux retombé exactement
sur celui de la baseline. Le maximum est pris après avoir mis le remplissage à
moins l'infini, mais certains témoignages ne contiennent aucun jeton connu — il en
existe qui ne sont faits que d'entités HTML. Toutes leurs positions sont masquées,
leur maximum vaut moins l'infini, et un seul suffit à mettre toute la perte à NaN.

**Réglage 4, sans effet, annulé.** Le meilleur point de validation restait le
passage 7 : le réseau avait convergé, je le croyais interrompu trop tôt, il ne
l'était pas. Les 23 passages suivants ne servaient qu'à surapprendre — validation de
1,60 à 2,35 pendant que l'apprentissage descendait de 1,42 à 0,99 — pour un temps
machine multiplié par 2,7. Je le note parce qu'un réglage qui ne rapporte rien est
une information, et parce que c'est exactement le genre de dépense que la phase 5
devra chasser.

**Réglage 5.** `light` porte 24 % des relevés, les dernières formes retenues moins
de 1 %. Sans pondération, le réseau a intérêt à ignorer les rares : le taux global
ne le sanctionne pas, le F1 moyen par classe si. La racine adoucit la correction —
la pondération pleine en 1/effectif retourne complètement le problème et sacrifie
les classes fréquentes.

Ce réglage a mis en évidence un point que je n'attendais pas ici : **les deux
résumés du score ne se déplacent pas ensemble**. Le réglage 5 gagne 0,016 de F1 et
perd 0,012 de taux. Selon celui qu'on regarde, le réseau bat le linéaire ou lui
passe derrière. C'est le sujet annoncé pour la phase 8, rencontré cinq phases plus
tôt, et ça règle une question de méthode : je rends les deux, toujours, et je ne
choisis pas celui qui m'arrange.

### Phase 4 — le carnet de pannes

| Panne | Le geste exact | Signature sur les courbes | Le test qui la distingue |
|---|---|---|---|
| bon à l'entraînement, bête à l'évaluation | | | |
| perte qui descend, prédictions pires que le hasard | | | |
| perte figée | | | |

### Phase 5 — le budget de calcul

**À rendre :** le temps de la phase 3, le nouveau, le facteur entre les deux ; la
figure avec le temps écoulé en abscisse ; les réglages touchés un par un, chacun
avec son gain et son coût en score ; pourquoi aller trop vite finit par coûter
plus cher.

### Phase 6 — le champ de vision du modèle

Longueur en jetons : médiane **12**, retenue **29** (99e centile), maximum 35.

| Couche | Ce qu'elle ajoute à l'étendue vue | Cumul |
|---|---|---|

**À rendre :** la comparaison du cumul à la longueur maximale en une ligne, la
vérification expérimentale (changer un mot au tout début fait bouger la sortie),
puis le score comparé à la phase 3.

### Phase 7 — quatre relevés à la fois

**À rendre :** la courbe à 4 relevés par lot avant et après correction sur la même
figure ; le montage corrigé relancé à la taille de lot de la phase 6 ; ce qui, dans
l'ancien montage, dépendait des autres relevés du lot.

### Phase 8 — le Conseil a lu trois relevés

Liste des mots interdits : **à écrire ici**, en entier.

Compte de relevés contenant encore un mot interdit après traitement : **doit être 0**.

| | Taux global | Moyenne par classe |
|---|---|---|
| avant interdiction | | |
| après interdiction | | |

**À rendre :** lequel des deux résumés chute le plus et pourquoi, et le nom des
deux ou trois classes qui se sont effondrées.

### Phase 9 — rendre des comptes sur trois décisions

Trois relevés (un réussi, un raté, un hésitant), chacun avec la part de chaque mot
dans la décision, lisible par quelqu'un qui ne code pas.

---

## Acte 3 — le Bureau apprend à relire

### Phase 10 — chaque mot interroge les autres

Relevé retenu (un vrai, avec un pronom ou une reprise) : **à choisir**.

**À rendre :** la matrice des poids avec les mots en étiquettes ; chaque ligne
somme à 1 ; la sortie a la même forme que l'entrée ; la case qui dit sur quel mot
s'est appuyé le pronom.

### Phase 11 — le Conseil mélange vos mots

| | Écart entre phrase correcte et phrase mélangée |
|---|---|
| avant correction | |
| après correction | |

**À écrire :** où l'information manquante a été injectée, et pourquoi là et pas ailleurs.

### Phase 12 — le Conseil demande la facture

| Longueur (jetons) | Temps d'un passage avant | Cases de la matrice de poids |
|---|---|---|
| 32 | | |
| 64 | | |
| 128 | | |
| 256 | | |
| 512 | | |

**À écrire :** en doublant la longueur, par combien le temps est multiplié et
pourquoi ce facteur-là ; à quelle longueur la machine devient inutilisable.

### Phase 13 — deux regards sur le même relevé

Mesure du désaccord entre les deux têtes : **à choisir et justifier en une ligne**.
Point de comparaison obligatoire : deux têtes qui partiraient identiques.

---

## Acte 4 — emprunter un cerveau terrien

Ligne de référence : le score de la phase 8, vocabulaire des formes interdit.

### Phase 14 — le cerveau emprunté, et sa facture

Modèle emprunté : **à choisir**.

| Régime | Score | Valeurs modifiées | Temps / passage | Mémoire max | Poids à sauvegarder |
|---|---|---|---|---|---|
| réseau de la phase 8 (référence) | | | | | |
| 1 — rien ne bouge | | | | | |
| 2 — une partie dégelée | | | | | |
| 3 — petites valeurs ajoutées | | | | | |

**À trancher en une phrase :** lequel le Bureau peut se payer, et pourquoi.

### Phase 15 — le Conseil pose des questions, vous citez vos sources

Liste de questions, **figée avant toute mesure** :

1.
2.
3.

Budget de texte donné au modèle avant qu'il réponde : **à fixer ici**, jamais dépassé.

**À rendre :** la proportion de réponses dont les relevés cités soutiennent
réellement ce qui est affirmé, et la comparaison avec une recherche naïve par mots.

### Phase 16 — faire entrer le tout dans le vaisseau

Marge de score acceptée, **annoncée avant toute optimisation** (cette phrase est
datée par l'historique de commits et ne se réécrit pas) :

| | Poids sur disque | Temps d'une réponse | Réponses par unité de temps | Score |
|---|---|---|---|---|
| avant | | | | |
| après | | | | |

**À écrire :** pourquoi vous vous êtes arrêté là, et ce que vous auriez tenté ensuite.

### Phase 17 — le faux témoignage

| Réglage | Sortie obtenue |
|---|---|
| trop propre, répétitif | |
| trop libre, invente des mots | |
| retenu | |

Résultat du tri en aveugle : **à rendre même s'il est mauvais**.
Preuve par le code qu'aucune valeur du modèle n'a bougé : **à joindre**.
