# Machine RNG

Le cube au fond de chaque base, en face de l'entrée.

## Tirage
- **Gratuit.**
- Donne un personnage du lot débloqué, selon les chances de rareté (voir [Personnages](Personnages.md)).
- **Pas de tickets ni de prix** : ce qui limite la fréquence, c'est l'**animation de tirage**. Pendant qu'elle se joue, le joueur ne peut pas relancer.
- Le serveur applique un temps de recharge égal à la durée de l'animation (le client ne peut pas le contourner).
- Durée de l'animation : **4 à 5 s** *(proposition, à régler en jeu)*.
- Le joueur n'est **pas bloqué** pendant le tirage : il peut bouger librement, seule la machine refuse de relancer tant que l'animation n'est pas finie.

## Animation de tirage
Tout se passe **dans le monde, à la machine** (plus d'animation plein écran qui cache la machine). Les autres joueurs voient les tirages.
1. **Néons de la machine** (≈ 1,5 s *(proposition)*) : clignotement de suspense, puis la machine prend la **couleur de la rareté** obtenue. Plus la rareté est haute, plus il y a d'effets (lumière, particules, éclairs, tremblement pour Mythique et Secret).
2. **Apparition du personnage** devant la machine, avec au-dessus de lui ses infos : **nom, rareté, étoiles, revenu**.
3. **Animation de révélation propre au personnage** (≈ 2,5 s *(proposition)*).
   - Au départ, une **animation de révélation commune** sert à tous les personnages ; des animations uniques sont ajoutées petit à petit, en commençant par les plus rares.
   - Un personnage sans modèle 3D apparaît en bloc coloré avec l'animation commune.
4. Le personnage **rejoint son emplacement** (ou disparaît s'il va dans l'inventaire).

Pour Mythique et Secret : en plus, un **court effet plein écran** (≈ 1 s *(proposition)*, flash de la couleur de rareté + nom) chez le joueur qui tire.

Style de la machine : **à définir** (pistes : autel d'invocation façon torii avec une carte géante qui tourne, distributeur de cartes façon borne d'arcade, gashapon géant). Maquette à tester sur Claude Design. Chaque niveau d'amélioration pourrait ajouter de la décoration visible *(proposition)*.

## Pass payants (Robux)
- **Tirage rapide** : raccourcit l'animation à ≈ 1,5 s *(proposition)* en sautant le suspense des néons et l'animation de révélation. Jamais 0 s : le serveur garde toujours un temps de recharge minimum. Mythique et Secret gardent une courte révélation.
- **Tirage auto** : la machine relance toute seule au rythme de l'animation (rapide si le joueur a aussi Tirage rapide). S'arrête si l'inventaire est plein ou si le joueur s'éloigne de la machine.
- Prix en Robux : **à définir**.
- À prévoir avec le Tirage auto : une option pour recycler automatiquement certaines raretés (voir [Hub](Hub.md), stand Recyclage), sinon l'inventaire se remplit vite.

## Améliorations
Payées en argent.
- **10 niveaux.**
- Le coût est multiplié par environ **2,5** à chaque niveau. Coût du niveau 1 : **à définir**.
- Chaque niveau déplace une partie des chances du Commun vers les raretés supérieures. Chances exactes par niveau : **à définir**.
- Les améliorations participent au **déblocage des nouveaux lots** (en lien avec le [rebirth](Rebirth-et-evolutions.md)).
- Le niveau de la machine est **remis à zéro au rebirth**.

## État technique
Tirage gratuit en place (`src/server/GachaService.luau`), avec les chances de rareté et d'étoiles de ce wiki (`src/shared/GachaConfig.luau`). Durée d'animation provisoire : 3 s. Animation provisoire à l'écran : carte de résultat plein écran (défilement des personnages puis révélation), **à remplacer** par l'animation à la machine décrite plus haut. Pas encore d'améliorations ni de pass.
