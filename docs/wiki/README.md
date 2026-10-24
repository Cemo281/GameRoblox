# Wiki du jeu — GameRoblox

Référence des décisions de game design. **Ce wiki fait foi** : le code suit ce qui est écrit ici.
Une valeur marquée *(proposition)* n'est pas encore validée. Une valeur marquée **à définir** n'a pas encore été décidée.

## Pages
| Page | Contenu |
|---|---|
| [Concept](Concept.md) | Vision, boucle de jeu, carte |
| [Personnages](Personnages.md) | Lots, raretés, liste des personnages et statistiques |
| [Économie](Economie.md) | Argent, collecte, revenu hors ligne |
| [Machine RNG](Machine-RNG.md) | Tirages, chances, améliorations |
| [Base et inventaire](Base-et-inventaire.md) | Emplacements, stockage |
| [Rebirth et évolutions](Rebirth-et-evolutions.md) | Rebirth, déblocage des lots, marchand, évolutions |
| [Combats](Combats.md) | Combats automatiques, récompenses, mutations |
| [Questions ouvertes](Questions-ouvertes.md) | Ce qui reste à décider |

## Journal des décisions
| Date | Décision |
|---|---|
| 2026-10-24 | Concept : Idle / Simulator / Gacha d'animé, îles célestes en étoile autour d'un Hub. |
| 2026-10-24 | Base joueur : 10 emplacements pour poser ses personnages. |
| 2026-10-24 | 5 raretés : Commun, Rare, Légendaire, Mythique, Secret. |
| 2026-10-24 | Personnages sortis par lots ; lot suivant débloqué par rebirth. Lot 1 : thème One Piece (équipage), 10 personnages + 1 secret. |
| 2026-10-24 | Tirage gratuit. L'amélioration de la machine augmente les chances et débloque les nouveaux lots. |
| 2026-10-24 | Argent à collecter (pas automatique). Revenu hors ligne avec une limite. |
| 2026-10-24 | Doublons utiles : évolutions chez le marchand (ex. N exemplaires de A + M de B → carte C). |
| 2026-10-24 | Emplacements pleins : on peut retirer un personnage et le stocker dans l'inventaire. |
| 2026-10-24 | Combats automatiques contre des ennemis du jeu ; le joueur choisit son équipe. Récompenses : argent et mutations. |
| 2026-10-24 | Noms One Piece = noms de travail, remplacés par des personnages originaux avant publication. |
| 2026-10-24 | Pas de limite de tirage autre que l'animation de tirage (servant de temps de recharge, appliqué côté serveur). |
| 2026-10-24 | Collecte de l'argent par un collecteur unique dans la base. |
| 2026-10-24 | Luffy Gear 2 (Secret) s'obtient par tirage, très rare. Lot 1 = 11 personnages. |
| 2026-10-24 | Chances au niveau 0 : Commun 60 %, Rare 25 %, Légendaire 10 %, Mythique 4,9 %, Secret 0,1 %. |
| 2026-10-24 | Revenus du lot 1 validés (Nami 10 → Luffy Gear 2 1000 $/s). |
| 2026-10-24 | Dépenses d'argent : rebirth, déblocage des emplacements, étoiles (reroll), évolutions, machine RNG. |
| 2026-10-24 | Machine RNG : 10 niveaux, coût ×2,5 par niveau, chances déplacées du Commun vers les raretés supérieures. |
| 2026-10-24 | Collecteur dans l'enclos, sans plafond d'accumulation. |
| 2026-10-24 | Rebirth : remet à zéro l'argent et la machine, garde les personnages, +50 % de revenu par rebirth. |
| 2026-10-24 | Nouvelle mécanique : étoiles des personnages, obtenues par reroll payant. |
| 2026-10-24 | Le tirage reste gratuit. |
| 2026-10-24 | 2 emplacements ouverts au départ, les 8 autres à débloquer avec de l'argent. |
| 2026-10-24 | Étoiles : 5 max, +20 % de revenu par étoile, nombre aléatoire au tirage, reroll payant chez un marchand (prix selon la rareté). |
| 2026-10-24 | Rebirth : bonus additif (+50 % par rebirth) ; emplacements débloqués et étoiles conservés. |
| 2026-10-24 | Étoiles au tirage : 1★ 50 %, 2★ 30 %, 3★ 15 %, 4★ 4 %, 5★ 1 %. Le reroll peut faire baisser les étoiles. |
| 2026-10-24 | Revenu = base × (1 + 0,2 × étoiles) × (1 + 0,5 × rebirths). |
