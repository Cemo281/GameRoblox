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

## Direction artistique *(validée le 2026-10-31)*
Thème : **sanctuaire de festival animé** (matsuri). Objectif : un lieu lisible et chaleureux, qui se distingue des bases au premier coup d'œil.

- **Rendu** : aplats `SmoothPlastic` (pas de textures réalistes type Slate / Cobblestone), couleurs pastel saturées en **tons moyens** (l'éclairage actuel, OutdoorAmbient rose et contraste élevé, brûle les teintes très claires).
- **Palette** : sol en pierre beige, vermillon (torii, losanges de la place), noir prune (toits des torii), bois (bancs, stands), pierre grise et toit ardoise (lanternes), bordure en tuiles grises sur muret clair, or (liserés, estrade, cœur). Le **rose est réservé aux cerisiers** (feuillage, pétales) : retour du 31/10, « trop rose ». Chaque stand garde **sa couleur** (Évolutions violet, Étoiles jaune, Ateliers bleu, Recyclage vert) sur le comptoir, l'enseigne, le toit rayé et les noren.
- **Repères** : un **torii** à l'arrivée de chaque chemin (porte d'entrée du Hub, flanquée de 2 lanternes de pierre) ; au centre, **estrade à gradins** autour du piédestal et **cœur lumineux flottant** (≈ 35 studs de haut, orbites, rayon de lumière) visible depuis les bases.
- **Stands** : façon **yatai** (toit rayé incliné, lambrequin festonné, 2 lanternes en papier, noren derrière le PNJ, caisses). Le centre du comptoir reste dégagé pour le futur ProximityPrompt.
- **Ambiance** : cerisiers avec pétales en particules (2 grands cerisiers à banc circulaire dans les intervalles libres, des petits en bordure), bancs face à la place, panneau de classements encadré comme un panneau de sanctuaire.
- **Règle** : rien ne doit gêner les chemins (bordure ouverte de ±9° à chaque arrivée) ni l'avant des comptoirs.
- **Éclairage** : OutdoorAmbient mauve doux, contraste modéré, saturation légèrement relevée (réglages de la place, communs à toute la carte).
- **Pièces sculptées** : cerisiers, torii, lanternes modélisés dans Blender (`assets/hub/decor_hub.py`), ombrage peint en dégradés dans une palette partagée, jamais de traits noirs.
- **Technique** : décor dans `Workspace.Hub.Decor` (≈ 570 pièces, ~30 lumières, 13 émetteurs), séparé des pièces de jeu ; torii, lanternes de pierre, cerisiers et chochin en MeshParts (gabarits dans `ServerStorage.Gabarits.DecorHub`, posés par `assets/hub/remplacer_decor_hub.luau`), collisions sur des pièces invisibles `Collision` (piliers, troncs, pieds de lanterne) ; états d'avant dans `ServerStorage.Sauvegarde_AvantDecorHub` et `ServerStorage.Sauvegarde_AvantMeshDecorHub`.

## À définir
- Zone de combat : au Hub ou dans une zone dédiée (voir [Combats](Combats.md)) ?
- Liste des améliorations globales, règles du recyclage, critères des classements, fonctionnement du piédestal d'événement.
