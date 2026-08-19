# Bureau d'Analyse Terrestre — le détecteur de formes

À partir du témoignage écrit par un témoin, retrouver la forme qu'il a observée.
88 875 relevés, un réseau écrit en PyTorch, l'attention codée à la main, puis un
modèle de langue emprunté. Les résultats sont dans `RAPPORT.md`.

## Lancer

```bash
pip install -r requirements.txt
python main.py
```

Le script télécharge lui-même la transmission (~15 Mo, non versionnée) et rejoue
toutes les phases d'une traite, du téléchargement au dernier chiffre affiché.

Avec Docker, sans rien installer :

```bash
docker compose run --rm bureau          # exécution courante
docker compose run --rm machine-neuve   # conteneur vierge, sans montage
```

## Options

```bash
python main.py --phases 0,2     # quelques phases seulement (mise au point)
python main.py --phases 10-13   # un acte entier
python main.py --rapide         # jeu réduit — aucun chiffre du rapport ne vient de là
python main.py --graine 1       # relancer à l'identique, pour mesurer la dispersion
```
