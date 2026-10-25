# Machine RNG

Le cube au fond de chaque base, en face de l'entrée.

## Tirage
- **Gratuit.**
- Donne un personnage du lot débloqué, selon les chances de rareté (voir [Personnages](Personnages.md)).
- **Pas de tickets ni de prix** : ce qui limite la fréquence, c'est l'**animation de tirage**. Pendant qu'elle se joue, le joueur ne peut pas relancer.
- Le serveur applique un temps de recharge égal à la durée de l'animation (le client ne peut pas le contourner).
- Durée de l'animation : **à définir**.

## Améliorations
Payées en argent.
- **10 niveaux.**
- Le coût est multiplié par environ **2,5** à chaque niveau. Coût du niveau 1 : **à définir**.
- Chaque niveau déplace une partie des chances du Commun vers les raretés supérieures. Chances exactes par niveau : **à définir**.
- Les améliorations participent au **déblocage des nouveaux lots** (en lien avec le [rebirth](Rebirth-et-evolutions.md)).
- Le niveau de la machine est **remis à zéro au rebirth**.

## État technique
Tirage gratuit en place (`src/server/GachaService.luau`), avec les chances de rareté et d'étoiles de ce wiki (`src/shared/GachaConfig.luau`). Durée d'animation provisoire : 3 s. Animation provisoire à l'écran : carte de résultat (défilement des personnages puis révélation), en attendant les modèles 3D. Pas encore d'améliorations.
