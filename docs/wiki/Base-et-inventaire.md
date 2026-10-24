# Base et inventaire

## Base joueur
Une parcelle par joueur (modèle `BaseJoueur` dans Studio) :
- **Enclos** avec une allée centrale de l'entrée jusqu'à la **machine RNG** (au fond, en face de l'entrée).
- **10 emplacements** pour poser ses personnages (5 de chaque côté de l'allée).
- **Collecteur** unique, dans l'enclos, pour récupérer l'argent produit (voir [Économie](Economie.md)). Position exacte : **à définir**.
- **Podium** à gauche de l'entrée, **panneau** avec le nom du propriétaire à droite.
- Rôle du podium : **à définir** (exposer ses meilleurs personnages ?).

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
