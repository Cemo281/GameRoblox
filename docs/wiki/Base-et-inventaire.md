# Base et inventaire

## Base joueur
Une parcelle par joueur (modèle `BaseJoueur` dans Studio), décor « Sanctuaire » (cour de sable de 90 × 102 studs, clôture de bois, torii d'entrée, lanternes de pierre, bannières) :
- **Allée** de dalles de l'entrée jusqu'à l'**autel d'invocation** (la machine RNG, au fond, en face de l'entrée).
- **10 socles** pour poser ses personnages (5 de chaque côté de l'allée, impairs à gauche, 1-2 près de l'entrée), chacun avec une stèle numérotée. Socle occupé : anneau de la couleur de la rareté, lumière, étiquette nom · rareté · gain par seconde. Socle libre : « Socle libre » ; socle pas encore débloqué : « Verrouillé ».
- **Collecte** juste après l'entrée, à droite : dalle dorée avec une colonne de lumière ; on marche dessus pour récupérer l'argent produit (voir [Économie](Economie.md)).
- **Panneau** du propriétaire devant l'entrée, à gauche : nom du joueur et niveau de l'autel.
- **Pupitre d'amélioration** près de l'autel, à gauche : améliore la machine (achat pas encore en place, coût **à définir**, voir [Machine RNG](Machine-RNG.md)).
- **Bases ouvertes** : pas de barrière, tous les joueurs peuvent entrer dans toutes les bases pour les regarder (décision du 08/11). Seul le propriétaire peut collecter et tirer.
- Plus de podium.

## Emplacements
- Un personnage posé sur un emplacement produit son revenu.
- **2 emplacements ouverts au départ** ; les 8 autres se **débloquent avec de l'argent**.
- Coût de chaque déblocage : **à définir** *(proposition : chaque emplacement ~2× plus cher que le précédent)*.
- Les emplacements débloqués sont conservés au rebirth.
- Quand les emplacements sont pleins, on peut **retirer** un personnage pour le **stocker dans l'inventaire**.

## Inventaire
- Contient les personnages obtenus qui ne sont pas posés.
- Taille max : **à définir**. Limite technique provisoire dans le code : 100 personnages au total (posés + inventaire) ; une fois atteinte, la machine refuse de tirer. Sans limite, la sauvegarde grossirait sans fin (tirage gratuit).
- Les personnages de l'inventaire ne produisent pas d'argent.

## État technique
Interface en place : le bouton **Inventaire** liste les personnages (posés d'abord, puis par rareté) avec **Poser** (premier emplacement libre) et **Retirer**. Un tirage va sur le premier emplacement libre, sinon dans l'inventaire.
Zone construite par `assets/zone/construire_zone.luau` (relançable, dans le repère du `Centre` de chaque base, +Z vers le Hub), puis `assets/autel/construire_autel.luau`. Affichage des socles, du panneau et du pupitre : `BaseService` ; étiquette de la collecte : `RevenuService` ; colonne et pièces animées : client `ZoneCollecte`.
