# Machine RNG

Le cube au fond de chaque base, en face de l'entrée.

## Tirage
- **Gratuit.**
- Donne un personnage du lot débloqué, selon les chances de rareté.
- **Pas de tickets ni de prix** : ce qui limite la fréquence, c'est l'**animation de tirage**. Pendant qu'elle se joue, le joueur ne peut pas relancer.
- Le serveur applique un temps de recharge égal à la durée de l'animation (le client ne peut pas le contourner).
- Durée de l'animation : **à définir** *(proposition : 3 à 5 s)*. Une amélioration pour la raccourcir : **à définir**.

## Améliorations
L'argent sert à améliorer la machine :
- **Meilleures chances** d'obtenir des raretés élevées.
- **Déblocage des nouveaux lots** (en lien avec le [rebirth](Rebirth-et-evolutions.md)).

Nombre de niveaux, coût de chaque niveau et chances par niveau : **à définir**.

## État technique
Tirage de test en place (`GachaSystem.server.luau`, réglages dans `src/shared/GachaConfig.luau`) : prix et chances provisoires, à remplacer par les valeurs de ce wiki.
