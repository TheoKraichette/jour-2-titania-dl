# Rapport au Conseil — le détecteur de formes

> Chaque chiffre de ce rapport est mesuré par `main.py` et se reproduit en le
> relançant. Les décisions qui ont mal tourné y sont aussi : un rapport qui ne
> contient que des réussites est incomplet.
>
> Phases traitées : 0 à 6.

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

Les dix journées les plus chargées du fichier :

| Rang | Journée | Relevés | |
|---|---|---|---|
| 1 | 2010-07-04 | 206 | 4 juillet |
| 2 | 1999-11-16 | 195 | ni fête ni férié |
| 3 | 2012-07-04 | 191 | 4 juillet |
| 4 | 2013-07-04 | 180 | 4 juillet |
| 5 | 2011-07-04 | 155 | 4 juillet |
| 6 | 2009-09-19 | 129 | ni fête ni férié |
| 7 | 2014-01-01 | 99 | Nouvel An |
| 8 | 2013-12-31 | 96 | Saint-Sylvestre |
| 9 | 2004-10-31 | 94 | Halloween |
| 10 | 2009-07-04 | 88 | 4 juillet |

Deux journées de ce classement ne correspondent à aucune fête — dont la deuxième
du fichier. C'est la matière de la phase 1.

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

8 relevés appris par coeur, par le montage du projet — celui que la phase 3
entraîne, la règle du Bureau l'exige. Figure : `figures/phase02_test_acceptation.png`.

- les 8 prédictions tombent justes dès l'itération 1, alors que la perte vaut
  encore 2,963 — c'est-à-dire **au-dessus** du hasard, ln(18) = 2,890. « Ne plus se
  tromper » n'est donc pas un critère d'arrêt sur 8 relevés ;
- mémorisation franche (perte < 1e-3) à l'itération **8**, perte finale 4,6e-4 ;
- les 8 prédictions finales, à côté des 8 vraies formes :

| Prédite | Vraie | Début du relevé |
|---|---|---|
| flash | flash | « Stationary intermitient flashes » |
| fireball | fireball | « Ball of flames moving quickly across the sky » |
| light | light | « White Light, circular, N to S flight path » |
| light | light | « On my way home from work heading north on the Florid… » |
| circle | circle | « UFO seen while driving the back roads of Wyoming. » |
| circle | circle | « Circular Orange object » |
| sphere | sphere | « 3 orange spheres. » |
| oval | oval | « observed tarnished, oval shaped object with black… » |

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
l'écart entre les deux est le résultat intéressant — sur le montage final : 1 pour
les prédictions, 8 pour la mémorisation réelle.

**Une note sur le montage.** Ce test a d'abord été passé par mon premier montage,
un sac de mots. Quand la phase 3 l'a remplacé par l'empilement à fenêtre glissante,
j'ai refait passer le test au nouveau montage — c'est lui qui s'entraîne, c'est
donc lui qui doit prouver que la correction circule. Les chiffres ci-dessus sont
les siens, et le piège du critère est le même dans les deux cas.

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

#### Les trois essais

| Essai | Taux | F1 moyen | Temps |
|---|---|---|---|
| toujours la forme la plus fréquente | 0,2423 | 0,0217 | — |
| linéaire du service statistique | 0,5368 | 0,4944 | 21 s |
| **réseau PyTorch** (moyenne de 3 initialisations) | **0,5406** | **0,5020** | 140 s |
| pire des trois essais du réseau | 0,5385 | 0,4975 | |

Le réseau passe devant sur les deux mesures, et pas seulement en moyenne : **les
trois initialisations battent le linéaire individuellement**. C'est le critère que
je retiens, parce qu'une moyenne se laisse tirer par un tirage chanceux — ça m'est
arrivé, voir plus bas. Chaque essai a ses deux courbes, perte d'apprentissage et
perte de validation sur la même figure : `figures/phase03_reseau_init0.png`,
`init1`, `init2`.

Le réseau coûte sept fois plus cher en temps machine que le linéaire pour ce gain.
C'est ce que la phase 5 devra réduire.

#### Comment j'y suis arrivé, et ce que ça m'a appris

J'ai d'abord passé six réglages à améliorer un montage en sac de mots : arrêt sur la
meilleure validation (+0,030), oubli de 0,3, maximum ajouté à la moyenne, pondération
des classes, dimension doublée. Résultat : 0,5385 de taux en moyenne, contre 0,5368
pour le linéaire. Autrement dit rien.

**Un sac de mots plafonne autour de 0,54, et le linéaire y est déjà.** À information
égale il est optimal — il a un poids direct par couple (mot, forme), là où un réseau
comprime le vocabulaire dans un goulot. J'ai vérifié cette impasse trois fois : en
rendant au réseau les comptages qu'il effaçait (0,5308, pire), en lui donnant les
paires de mots voisins (0,5164, encore pire), en écrivant sa voie linéaire en PyTorch
(0,5313, toujours en dessous).

Ce qui a débloqué n'est pas un réglage, c'est un changement d'information : **la
suite des mots**, que le comptage ne peut pas voir. Une fenêtre glissante parcourt le
relevé et combine les positions voisines, avec les mêmes poids partout — donc elle
apprend une tournure au lieu de retenir un relevé.

L'épisode des paires de mots mérite d'être raconté, parce qu'il montre la différence.
En donnant les paires directement au modèle linéaire, la perte d'apprentissage est
tombée à 0,05 pendant que la validation montait à 5,4 : sur douze mots, une paire
comme « orange_spheres » n'apparaît que dans un ou deux relevés, et le modèle s'en
sert comme **empreinte** du relevé. La fenêtre glissante ne peut pas tricher ainsi,
puisque ses poids servent à toutes les positions de tous les relevés.

Second réglage décisif : **le pas d'apprentissage divisé par cinq**, de 1e-2 à 2e-3.
À 1e-2, le meilleur point de validation tombait au passage 2 sur 15 — je retenais
donc un modèle qui n'avait presque rien appris, et l'étendue entre initialisations
atteignait 0,0201. À 2e-3, le meilleur point arrive au passage 5 et l'étendue tombe à
0,0036.

#### La victoire qui n'existait pas

Avant d'arriver là, j'ai cru avoir gagné. Une configuration donnait 0,541 et 0,498
contre 0,537 et 0,494 : au-dessus sur les deux mesures. J'ai failli l'écrire.

L'écart était de 0,004, et l'incertitude d'échantillonnage sur 10 935 relevés de test
vaut déjà 0,005. J'ai donc relancé le **même** entraînement quatre fois, découpe et
classes identiques, en ne changeant que l'initialisation :

| Initialisation | Taux | F1 moyen |
|---|---|---|
| 0 | 0,5409 | 0,4978 |
| 1 | 0,5428 | 0,4983 |
| 2 | 0,5342 | 0,4914 |
| 3 | 0,5361 | 0,4795 |
| moyenne | 0,5385 | 0,4918 |
| étendue | 0,0086 | 0,0188 |

Sur quatre essais, le réseau était à +0,0015 de taux et **−0,0022 de F1** : il ne
battait pas le linéaire. Mon 0,541 était l'initialisation la plus favorable des
quatre. Sans cette vérification, j'aurais présenté un tirage chanceux comme un
résultat — exactement la faute du disparu avec son 51.

Conséquence pour tout le reste du dossier : **avant de comparer deux montages, il
faut connaître la dispersion de chacun**, et un écart plus petit qu'elle n'existe
pas. C'est aussi pourquoi le montage final est validé sur trois initialisations et
jugé sur son pire essai, pas sur sa moyenne.

### Phase 4 — le carnet de pannes

Le montage de la phase 3, cassé trois fois, une panne à la fois, remis d'aplomb
entre chaque. Montage sain de référence : **0,546** sur le test. Une figure par
panne : `figures/phase04_panne1_recite.png`, `phase04_panne2_etiquettes.png`,
`phase04_panne3_figee.png`.

| Panne | Le geste exact | Signature | Le test, en moins d'une minute |
|---|---|---|---|
| **1.** excellent à l'entraînement, bête à l'évaluation | retirer l'oubli : plus rien ne freine la mémorisation | les deux courbes divergent : l'apprentissage descend pendant que la validation remonte (1,684 → 1,818) | évaluer sur les relevés **d'apprentissage** : 0,716 contre 0,516 en test |
| **2.** la perte descend, les prédictions sont pires que le hasard | décaler les étiquettes d'un cran avant l'apprentissage | courbe d'apprentissage parfaitement saine (2,031 → 1,382), **indistinguable de la saine** — la figure les superpose | regarder la matrice de confusion : les erreurs forment une diagonale **décalée** |
| **3.** la perte se fige | le pas d'apprentissage n'arrive jamais à l'optimiseur | la perte ne bouge pas de la 3ᵉ décimale dès le premier passage (3,1694 → 3,1692) | comparer un poids avant et après un passage : identique au bit près |

**Panne 1 — 0,716 en apprentissage contre 0,516 en test.** Le réseau récite les
relevés qu'on lui a montrés. Le point important est qu'**aucune donnée n'a changé**
entre les deux mesures : c'est le même modèle, sur le même fichier, et c'est le
choix de la partie évaluée qui révèle la panne.

**Panne 2 — 0,038 alors que le hasard donne 0,056.** C'est la plus sournoise : la
courbe d'apprentissage est irréprochable, elle descend proprement, et un rapport qui
ne rendrait que cette courbe ressemblerait à un succès. Le réseau a parfaitement
appris une tâche — simplement pas la nôtre. Être *sous* le hasard est la signature :
un modèle qui se trompe systématiquement en sait autant qu'un modèle juste, il est
mal branché.

**Panne 3 — perte figée à 3,1692.** Elle ne tombe pas exactement sur
ln(18) = 2,8904, et c'est instructif : les poids de départ ne sont pas nuls, donc le
réseau démarre avec des préférences arbitraires qu'il ne corrigera jamais. Il fait
donc légèrement pire que le hasard parfait, et pour toujours.

**Comment je les distingue sur une courbe inconnue.** Si les deux courbes divergent,
c'est la 1. Si elles descendent toutes les deux normalement, la panne n'est pas dans
l'entraînement mais dans le branchement des étiquettes, c'est la 2. Si la courbe est
plate dès le premier passage, c'est la 3. Une seule question suffit à trancher :
**est-ce que la perte bouge ?** Non → panne 3. Oui et les deux courbes divergent →
panne 1. Oui et elles restent ensemble → panne 2.

### Phase 5 — le budget de calcul

La référence n'est pas le temps noté en phase 3 : c'est la configuration exacte de
la phase 3, **rejouée dans le même processus** que les essais accélérés, pour que
les deux temps sortent du même chronomètre sur la même machine au même moment.
D'un lancement à l'autre, la même configuration varie de ±10 % selon la charge du
PC — comparer des temps pris à des moments différents n'aurait rien prouvé.

| | Temps | Taux | F1 moyen |
|---|---|---|---|
| référence — phase 3 (25 passages, lots de 256) | 126,4 s | 0,5421 | 0,5083 |
| réglage 1 — 8 passages au lieu de 25 | **40,0 s** | 0,5421 | 0,5083 |
| réglage 2 — et des lots de 512 | 50,1 s | 0,5421 | 0,5041 |

**Temps de la phase 3 : 126,4 s. Temps de la phase 5 : 40,0 s. Facteur : ×3,2.**
Figure, avec le temps écoulé en abscisse et les deux courbes de validation
superposées : `figures/phase05_budget.png`.

**Réglage 1 — s'arrêter à 8 passages. Gain ×3,2, coût en score : rigoureusement
zéro.** Le score n'est pas « équivalent », il est identique à la décimale près, et
ce n'est pas une coïncidence : la phase 3 avait montré que le meilleur point de
validation tombe au passage 5, et l'état rendu est celui de ce meilleur point. Les
17 passages économisés ne servaient qu'à surapprendre — on payait de l'électricité
pour dégrader le modèle, puis on jetait le résultat de cette dégradation.

**Réglage 2 — des lots de 512 au lieu de 256. Gain : aucun (50,1 s, plus lent que
le réglage 1 seul), coût : 0,004 de F1. Rendu, mais pas retenu.** L'hypothèse était
que la moitié des tours de boucle Python ferait gagner du temps ; la mesure dit que
non. À lots de 256, la boucle ne coûte déjà presque rien : le temps est dans la
convolution des 51 034 relevés, qui ne dépend pas du découpage en lots. C'est le
réglage qui ne rapporte rien, et il est au rapport parce qu'un réglage sans mesure
ne compte pas — celui-ci a sa mesure, et elle dit de ne pas le garder.

**Le score final n'est pas inférieur à celui de la phase 3.** Vérifié comme en
phase 3, sur les trois mêmes initialisations : 0,5421 / 0,5385 / 0,5412 de taux —
les mêmes valeurs qu'en phase 3, puisque l'état retenu par initialisation est le
même. Le pire essai (0,5385 / 0,4975) égale exactement le plancher de la phase 3.

**Pourquoi aller trop vite finit par coûter plus cher.** Je l'ai payé pour le
mesurer, en phase 3. Le pas d'apprentissage à 1e-2 — cinq fois plus « rapide » en
apparence — donnait un meilleur point de validation au passage 2 et une dispersion
de 0,020 entre initialisations : impossible de savoir ce qu'on avait sans relancer
plusieurs fois. Un entraînement deux fois plus court qu'il faut relancer quatre
fois pour s'y fier coûte deux fois plus cher que l'entraînement lent lancé une
fois. La vitesse qui se paie en incertitude n'est pas de la vitesse, c'est un
report de la facture.

### Phase 6 — le champ de vision du modèle

La contrainte de la salle des calculs est respectée par construction : le montage
est fait de convolutions, chaque position est traitée en même temps que toutes les
autres, aucune n'attend la précédente.

Longueur maximale acceptée en entrée : **29 jetons** (le 99ᵉ centile ; le plus
long relevé du fichier en fait 35, il est tronqué). Longueur médiane : **12**.

#### Le tableau, avant tout entraînement

Une convolution de fenêtre 3 ne voit que 3 positions : pour couvrir 29 positions
en empilant des fenêtres ordinaires, il faudrait quatorze couches. J'espace donc
les fenêtres — la dilatation double à chaque couche, et l'étendue vue par une
sortie grandit exponentiellement avec la profondeur :

| Couche | Dilatation | Ce qu'elle ajoute | Cumul |
|---|---|---|---|
| 1 | 1 | 2 | 3 |
| 2 | 2 | 4 | 7 |
| 3 | 4 | 8 | 15 |
| 4 | 8 | 16 | 31 |

**Étendue totale 31 > longueur maximale 29** : la position centrale d'un relevé
voit ses 29 positions, et le maximum final fait dépendre la sortie de toutes.

#### La vérification expérimentale, modèle encore vierge

Sur le relevé le plus long du jeu (« I was on my way to bed n I sleep next to the
window n when I lay… »), le premier mot est remplacé par un autre, et on mesure ce
qui bouge — sur le modèle **non entraîné**, comme l'exige l'énoncé :

- la sortie du classement bouge : écart maximal de 0,004 sur les logits ;
- la modification se propage jusqu'à la position 16 : **rayon mesuré 15, rayon
  théorique 15** — l'expérience tombe exactement sur le calcul.

#### Puis on entraîne, et l'énoncé avait raison : empiler dégrade

Trois configurations, trois initialisations chacune, réglages de la phase 5 :

| Montage | Init 0 | Init 1 | Init 2 | Pire essai |
|---|---|---|---|---|
| empilement nu | 0,5228 / 0,4614 | 0,5280 / 0,4741 | 0,5282 / 0,4831 | 0,5228 / 0,4614 ✗ |
| + connexions résiduelles | 0,5396 / 0,5072 | 0,5394 / 0,5018 | 0,5387 / 0,5020 | **0,5387 / 0,5018 ✓** |
| + résidu + normalisation par lot | 0,5397 / 0,5056 | 0,5349 / 0,5007 | 0,5362 / 0,5004 | 0,5349 / 0,5004 ✗ |

(plancher de la phase 3 : 0,5385 / 0,4975 ; figures `phase06_sans_residu.png`,
`phase06_avec_residu.png`, `phase06_residu_et_norme.png`)

**Le problème connu, et sa solution.** L'empilement nu perd 0,016 de taux et 0,04
de F1 : en traversant quatre couches, le gradient s'affaiblit et les premières
couches n'apprennent presque plus. La solution connue, ce sont les **connexions
résiduelles** — chaque couche apprend un écart plutôt qu'une transformation
entière, et le gradient garde un chemin direct vers l'entrée. Appliquées, elles
récupèrent tout : les trois initialisations repassent au-dessus du plancher.

**La recette standard complète a aussi été mesurée, et écartée.** Les empilements
profonds s'accompagnent d'ordinaire d'une normalisation par lot. Ajoutée au
résidu, elle donne un pire essai à 0,5349 — sous le plancher. La règle de
rétention, fixée avant la mesure, tranche : **montage retenu, résidu seul**. La
normalisation reviendra en phase 7, où le Conseil demandera précisément ce qui,
dans un montage, a le droit de dépendre des autres relevés du lot.

Le montage couvre le relevé entier et s'entraîne encore : la phase est validée,
au prix d'une leçon — la profondeur ne se paie pas en score si le gradient a son
chemin, mais elle se paie en temps (≈ 180 s l'entraînement, contre 40 s pour une
couche en phase 5).

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
