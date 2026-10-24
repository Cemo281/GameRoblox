# Économie

## Monnaie
- **Argent** (`$`), affiché dans les leaderstats et sauvegardé (DataStore).
- Gagné par : les personnages posés sur la base (revenu par seconde), les combats.

## Dépenses
| Dépense | Page |
|---|---|
| Rebirth | [Rebirth et évolutions](Rebirth-et-evolutions.md) |
| Déblocage des emplacements de personnages | [Base et inventaire](Base-et-inventaire.md) |
| Reroll des étoiles d'un personnage (prix selon la rareté) | [Personnages](Personnages.md) |
| Évolutions (en plus des doublons) | [Rebirth et évolutions](Rebirth-et-evolutions.md) |
| Améliorations de la machine RNG | [Machine RNG](Machine-RNG.md) |

Le **tirage reste gratuit** : il ne fait pas partie des dépenses.
Les montants de chaque dépense sont **à définir**.

## Revenu des personnages
- Chaque personnage posé sur un emplacement produit son revenu par seconde (voir [Personnages](Personnages.md)), augmenté par ses étoiles et par le bonus de rebirth.
- Formule *(proposition, ordre de calcul à confirmer)* : `revenu de base × (1 + 0,2 × étoiles) × (1 + 0,5 × rebirths)`.
- L'argent **n'arrive pas directement** sur le compte : il s'accumule et le joueur doit **le collecter**.
- Un **collecteur unique**, placé **dans l'enclos**, récupère d'un coup l'argent de tous les personnages posés.
- **Pas de plafond** d'accumulation avant collecte.

## Revenu hors ligne
- Oui : le joueur gagne de l'argent pendant qu'il est déconnecté.
- Limite : **à définir** (durée max et/ou pourcentage du revenu normal).

## Rythme
Règle de conception : le premier tirage doit être possible dans les 30 premières secondes ; la progression ralentit ensuite.
Le tirage est gratuit et seulement limité par son animation (voir [Machine RNG](Machine-RNG.md)) : la progression repose donc sur les **chances de rareté**, les **dépenses** ci-dessus et le **rebirth**.
