# Machine RNG

L'**autel d'invocation** au fond de chaque base, en face de l'entrée (remplace le cube depuis le 2026-11-08) : estrade de pierre, portique torii vermillon, carte géante qui tourne au-dessus de l'autel, 2 lanternes. Les néons, le faisceau et la lumière prennent la couleur de la rareté du dernier tirage ; avant le premier tirage, l'autel est **éteint** (néons gris mats, carte immobile). Au-dessus du toit, un compte à rebours indique le temps de recharge, puis « PRÊT ! ».

Apparence selon le niveau de la machine (cumulatif) : 2 boules d'or sur le toit, 3 lanternes suspendues, 4 néons sur les piliers, 5 lanternes arrière, 6 halo tournant, 7-9 cartes en orbite (2, 4 puis 6), 10 aura, étincelles et « MAX ».

## Tirage
- **Gratuit.**
- Donne un personnage du lot débloqué, selon les chances de rareté (voir [Personnages](Personnages.md)).
- **Pas de tickets ni de prix** : ce qui limite la fréquence, c'est l'**animation de tirage**. Pendant qu'elle se joue, le joueur ne peut pas relancer.
- Le serveur applique un temps de recharge égal à la durée de l'animation (le client ne peut pas le contourner).
- Durée de l'animation *(validée le 2026-11-05)* : celle de l'animation de révélation, qui dépend de la rareté obtenue (un palier de montée de plus par rareté) : Commun 6 s, Rare ≈ 9,4 s, Légendaire ≈ 10,1 s, Mythique ≈ 10,9 s, Secret 11,6 s. Pas de bouton pour passer l'animation gratuitement.

## Offres liées au tirage (plus tard)
Décidé le 2026-11-05, à faire **à la fin** avec les autres achats Robux (prix **à définir**) :
- **Passer les animations** (offre payante).
- **Tirage automatique** (offre payante).
Les tirages restent gratuits : on paie le confort, pas un tirage au hasard.

## Améliorations
Payées en argent.
- **10 niveaux.**
- Le coût est multiplié par environ **2,5** à chaque niveau. Coût du niveau 1 : **à définir**.
- Chaque niveau déplace une partie des chances du Commun vers les raretés supérieures. Chances exactes par niveau : **à définir**.
- Les améliorations participent au **déblocage des nouveaux lots** (en lien avec le [rebirth](Rebirth-et-evolutions.md)).
- Le niveau de la machine est **remis à zéro au rebirth**.

## État technique
Tirage gratuit en place (`src/server/GachaService.luau`), avec les chances de rareté et d'étoiles de ce wiki (`src/shared/GachaConfig.luau`). Animation de révélation plein écran (`src/client/Tirage.luau`, maquette du handoff `design_handoff_ui_roblox`) ; son minutage est dans `GachaConfig.Animation` / `GachaConfig.Minutage`, et le serveur bloque la machine pendant `GachaConfig.DureeTirage(rareté)`. Pas encore d'améliorations.
Autel : construit par `assets/autel/construire_autel.luau` (MCP, relançable) dans `BaseJoueur.AutelInvocation` ; la Part `RNG` (tag `MachineRNG`) en est le volume invisible où se trouve le ProximityPrompt. Attributs du modèle posés par le serveur : `Level` (= `NiveauMachine`, 1 minimum, `BaseService.RafraichirAutel`) et `Rarete` (dernier tirage, posé à la révélation) ; affichage et animations dans `src/client/Autel.luau`.
