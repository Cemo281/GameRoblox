# Personnages

Chaque personnage a une **rareté** et des **statistiques** : revenu par seconde et dégâts en combat.
Les personnages sortent par **lots** ; un nouveau lot se débloque par [rebirth](Rebirth-et-evolutions.md).

> ⚠️ **Propriété intellectuelle — décision** : les noms One Piece (et DBZ, etc.) sont des **noms de travail**.
> Ils seront remplacés par des **personnages originaux** (mêmes rôles, raretés et stats) **avant publication**.
> Côté code : les noms et modèles sont des données (config), jamais écrits en dur dans la logique.

## Raretés
| Rareté | Ordre | Chance de tirage (machine niveau 0) |
|---|---|---|
| Commun | 1 | 60 % |
| Rare | 2 | 25 % |
| Légendaire | 3 | 10 % |
| Mythique | 4 | 4,9 % |
| Secret | 5 | 0,1 % |

Les améliorations de la [machine RNG](Machine-RNG.md) font évoluer ces chances.
Au sein d'une rareté, chaque personnage a la même chance : **à confirmer**.

## Lot 1 — thème One Piece (équipage du Chapeau de paille)
11 personnages : 10 + 1 Secret (obtenu par tirage, très rare).

| Personnage | Rareté | Revenu ($/s) | Dégâts |
|---|---|---|---|
| Nami | Commun | 10 | à définir |
| Usopp | Commun | 12 | à définir |
| Chopper | Commun | 15 | à définir |
| Franky | Rare | 30 | à définir |
| Brook | Rare | 35 | à définir |
| Robin | Légendaire | 60 | à définir |
| Jinbei | Légendaire | 70 | à définir |
| Sanji | Mythique | 85 | à définir |
| Zoro | Mythique | 90 | à définir |
| Luffy | Mythique | 100 | à définir |
| Luffy Gear 2 | Secret | 1000 | à définir |

## Étoiles
- Chaque personnage possède de **1 à 5 étoiles**.
- Effet : **+20 % de revenu par étoile**.
- À l'obtention (tirage), le personnage reçoit un **nombre d'étoiles aléatoire** :

  | Étoiles | 1 | 2 | 3 | 4 | 5 |
  |---|---|---|---|---|---|
  | Chance | 50 % | 30 % | 15 % | 4 % | 1 % |

- **Reroll** : chez un **marchand d'étoiles**, le joueur paie pour retirer au hasard le nombre d'étoiles d'un de ses personnages.
  - Le prix dépend de la **rareté** du personnage. Montants : **à définir**.
  - Le reroll **peut faire baisser** le nombre d'étoiles.
  - Probabilités du reroll (mêmes que le tirage ?) : **à définir**.
- Les étoiles sont conservées au rebirth.

## Animations de vitrine
Un personnage posé sur sa case joue en boucle ses animations de vitrine, avec **2 secondes de pause** entre chacune :
**Idle** (ex. bras croisés) → pause → **Action** (démonstration de pouvoir, ex. dégainer les trois sabres) → pause → **Signature** (geste typique, ex. ranger les sabres) → pause → Idle…
- Pendant une pause, le personnage reste figé sur la dernière image de l'animation (ex. en garde, sabres en main, après l'Action).
- **Visible par tous** les joueurs (sabres et effets compris).
- Un personnage qui n'a qu'une animation Idle la joue en boucle, sans pause.

État technique : cycle joué par le serveur (`BaseService`), sabres et effets affichés par chaque client à partir des marqueurs des animations (`src/client/Vitrine.luau`). Premier personnage concerné : Zoro.

## Lots suivants
**À définir.** Exemple donné : un lot sur le thème DBZ, avec une évolution « 10 Goku + 20 Vegeta → Vegeto ».
