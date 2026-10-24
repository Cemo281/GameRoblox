# Hub — Sanctuaire Mère

Place centrale de la carte, commune à tous les joueurs du serveur. Zone **sociale et marchande** : on y dépense son argent et ses doublons, on ne gagne pas d'argent sur place.
Les bases joueurs sont des parcelles au sol disposées en étoile autour du Hub (voir [Concept](Concept.md)).

## Ce qui se fait au Hub et ce qui reste dans la base
| Au Hub | Dans la base |
|---|---|
| Évolutions (marchand d'évolutions) | Tirage (machine RNG) |
| Reroll des étoiles (marchand d'étoiles) *(proposition, question 7)* | Amélioration de la machine RNG |
| Améliorations globales (ateliers) | Déblocage des emplacements |
| Recyclage / vente de personnages | Collecte de l'argent (collecteur) |
| Classements | Pose / retrait des personnages |
| Piédestal d'événement | Rebirth |

## Stands
Chaque stand = un PNJ (modèle 3D animé) + un comptoir + un ProximityPrompt qui ouvre son interface. Toutes les transactions sont validées côté serveur.

| Stand | Rôle | Statut |
|---|---|---|
| **Marchand d'évolutions** | N personnages + argent → carte d'évolution (voir [Rebirth et évolutions](Rebirth-et-evolutions.md)) | Validé (au Hub) |
| **Marchand d'étoiles** | Reroll payant des étoiles d'un personnage (voir [Personnages](Personnages.md)) | Au Hub *(proposition)* |
| **Atelier d'améliorations globales** | Bonus permanents achetés avec de l'argent | Liste et effets **à définir** |
| **Recyclage / vente** | Échanger les personnages inutiles contre de l'argent | Prix et règles **à définir** |
| **Classements** | Panneaux (argent total, rebirths, personnage le plus rare…) | Critères **à définir** |
| **Piédestal d'événement** | Personnage ou bonus d'événement temporaire | Fonctionnement **à définir** |

## Plan (validé)
- **Forme** : plateau circulaire, rayon ≈ 70 studs, au centre de la carte.
- **Centre** : piédestal d'événement, entouré d'une place dégagée (point de repère visible depuis les bases).
- **Couronne de stands** : les stands sont répartis sur un anneau (rayon ≈ 45 studs), face au centre, **entre** les arrivées des chemins pour ne pas bloquer le passage.
- **Classements** : sur le bord du plateau, lisibles depuis la place centrale.
- **Chemins** : un chemin par base, de l'entrée de la base au bord du Hub (≈ 57 studs). Bases à ≈ 178 studs du centre, entrée tournée vers le Hub.
- **Apparition** : les joueurs apparaissent dans leur base (déjà en place), pas au Hub.
- **Nombre de bases** : **7** (un chemin tous les ≈ 51,4°). Les 7 intervalles entre chemins accueillent, dans l'ordre à partir du chemin 1 : Évolutions, Classements, Étoiles, libre, Ateliers, Recyclage, libre.

```
                  [Base 1]
        (libre)      |      Évolutions
 [Base 7]                          [Base 2]
     Recyclage              Classements
 [Base 6]       (Piédestal)        [Base 3]
     Ateliers                 Étoiles
        [Base 5]  (libre)  [Base 4]
```
Sens de rotation : tel que vu de dessus dans Studio, en partant du chemin 1 (base existante, côté -Z).

## À définir
- Zone de combat : au Hub ou dans une zone dédiée (voir [Combats](Combats.md)) ?
- Liste des améliorations globales, règles du recyclage, critères des classements, fonctionnement du piédestal d'événement.
