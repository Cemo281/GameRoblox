# Handoff : Combattant élastique (Gear 2) — animations R15 Roblox

## Vue d'ensemble
Un personnage au corps en caoutchouc pour un jeu Roblox, avec un kit d'animations R15 :
- **Idle — Rebond** (boucle 1,4 s)
- **Transformation — Gear 2** (3,6 s) : pose accroupie tête baissée et poing au sol, pompes, explosion de vapeur, garde voûtée.
- **Combo** (3,8 s) : rafale de 12 coups, coup de pied étiré, saut, longue charge en l'air poing en feu, poing aérien étiré, atterrissage.
- **Séquence complète** : Gear 2 suivi du Combo (pour preview / cinématique).

Les **données d'animation sont finales** (keyframes, easings, marqueurs). Le reste (VFX, hitbox, déplacement réel, sons) est à implémenter côté jeu.

## À propos des fichiers
- `Combattant Elastique.dc.html` + `elastique.js` + `viewer-elastique.js` + `support.js` : **visualiseur de référence** en HTML/three.js (ouvrir le .html dans un navigateur via un serveur local). Il montre le rendu voulu : membres étirés, gonflement, vapeur, feu, étincelles, tremblement caméra, hit-stop. Ce n'est pas du code à embarquer dans le jeu ; c'est la référence visuelle et comportementale à reproduire dans Roblox.
- `elastique.js` est la **source de vérité** des animations (poses, timings, marqueurs). `toLuau()` génère le script d'import.
- `roblox/ElastiqueAnimations.lua` : script de **barre de commande Studio** déjà généré. Il crée les `KeyframeSequence` dans `ServerStorage.RBX_ANIMSAVES.<rig>` à partir du rig R15 sélectionné.
- `roblox/ElastiqueMembres.client.lua` : LocalScript runtime (tubes élastiques, accessoires, gonflement, hooks de marqueurs).
- `anim_summary.md` : durée, déplacement et liste exacte des marqueurs pour chaque animation.
- `references/` : vidéo de référence du Gear 2 et pose de référence pour la charge du poing.

## Fidélité
**Haute fidélité pour le mouvement** : les poses, timings et easings sont à reproduire tels quels (ils sont déjà exportés). **Basse fidélité pour les VFX** : ceux du visualiseur montrent seulement l'intention ; il faut les refaire avec des ParticleEmitter, Beam et ce qu'il faut côté Roblox.

## Conventions du rig (important)
- Rig **R15** standard. Les poses visent les `Motor6D` : `LowerTorso` (Root), `UpperTorso` (Waist), `Head` (Neck), `Right/LeftUpperArm` (Shoulder), `Right/LeftLowerArm` (Elbow), `Right/LeftHand` (Wrist), `Right/LeftUpperLeg` (Hip), `Right/LeftLowerLeg` (Knee), `Right/LeftFoot` (Ankle).
- Format d'une pose dans `elastique.js` : `[px, py, pz, rx, ry, rz]`, translations en studs et rotations en degrés. L'export applique `CFrame.new(px,py,pz) * CFrame.Angles(rad(rx), rad(ry), rad(rz))`. Le personnage regarde vers **−Z**.
- **Étirement** : on translate les poses `LowerArm/Hand/LowerLeg/Foot` le long de −Y du segment parent (helper `S(rot, len)`). Ça ouvre un trou entre les pièces, que `ElastiqueMembres.client.lua` remplit avec un cylindre par Motor6D (de `Part0.CFrame*C0` à `Part1.CFrame*C1`), recalculé à chaque `RenderStepped`.
- Easing : la propriété d'une pose s'applique à l'interpolation **vers la keyframe suivante**. Le style `Cubic` est exporté en `CubicV2` ; `Elastic` et `Linear` sont aussi utilisés.

## Accessoires attendus
| Nom | Attachment | Rôle |
|---|---|---|
| `ChapeauTete` | HatAttachment (Head) | chapeau de paille sur la tête (visible par défaut) |
| `ChapeauDos` | BodyBackAttachment (UpperTorso) | chapeau pendu dans le dos (caché par défaut) |

Ils sont basculés par les marqueurs `Montrer` et `Cacher` (la valeur du marqueur est le nom de l'accessoire). Le Gear 2 envoie le chapeau dans le dos à 0,30 s.

## Marqueurs (KeyframeMarker) → comportement à implémenter
| Nom | Valeurs | À faire côté jeu | Référence visuelle |
|---|---|---|---|
| `Montrer` / `Cacher` | nom d'Accessory | Transparency 0/1 (déjà géré dans le runtime) | — |
| `Gonfler` | `Debut` / `Fin` | épaissir les bras et jambes ×1,12 en X/Z (déjà géré, Tween 0,3 s) | membres +14 % |
| `Pompe` | `1`…`4` | pulsation de gonflement ×1,24 puis retour à 1,12 (déjà géré), petite onde au sol | pulse + anneau |
| `Aura` | `Vapeur` | **mode Gear 2** : vapeur blanche continue autour du corps et peau qui vire au rose (`#f2858a`) | particules qui montent |
| `Explosion` | `Vapeur` | grosse explosion de vapeur blanche radiale, onde au sol, camera shake fort | 90 particules radiales, shake 0,7 |
| `Explosion` | `AirPoing` | explosion d'impact, gros camera shake | shake 1,4 |
| `Impact` | `Rafale` (×12), `Pied`, `AirPoing` | **hitbox** sur le membre le plus éloigné du torse (main ou pied), étincelles + flash, hit-stop 0,045 s (0,09 s pour Pied/AirPoing) | étincelles, shake 0,3 / 0,9 |
| `Feu` | `Debut` / `Fin` | feu sur la main droite (ParticleEmitter + PointLight orange `#ff8a2a`) | flammes jaune→rouge |
| `Esquive` | `Atterrissage` | poussière à l'atterrissage, son | — |

Le runtime expose `onMarker(character, name, value)` pour brancher tout ça.

## Déplacement réel (root motion)
Les animations déplacent le `LowerTorso` mais **pas** le `HumanoidRootPart`. Dans le Combo, le corps va jusqu'à −1,5 stud vers l'avant et monte jusqu'à environ 6 studs pendant la charge aérienne, puis il revient à 0 par un petit saut arrière. Si le gameplay veut un vrai déplacement, il faut piloter le HRP (LinearVelocity ou tween) en suivant ces offsets (voir `anim_summary.md`), ou bien remettre le root à zéro dans les poses et déplacer le HRP en parallèle.

## Moments clés (timing du Combo)
- 0,26 → 1,03 s : 12 coups de rafale (bras alternés, étirés de 3,2 + 3,2 studs)
- 1,20 s : coup de pied étiré
- 1,52 s : accroupi, puis saut
- 1,95 → 2,65 s : **suspension en l'air** pendant la charge, poing en feu près de la tête, coude plié, sans étirement (l'allongement ne se fait qu'au lancer, 2,65 → 2,75 s)
- 2,75 s : poing aérien étiré de 5,6 studs, impact + explosion
- 3,28 s : atterrissage ; 3,5 → 3,8 s : saut arrière et retour en garde

## Moments clés (Gear 2)
- 0,30 s : pose mythique (accroupi, tête baissée, poing droit au sol, avant-bras gauche sur le genou), gonflement
- 0,45 / 0,75 / 1,40 / 1,90 s : pompes ; vapeur à partir de 0,90 s
- 2,32 s : il reste accroupi, le poing au sol, et relève seulement la tête pendant que la vapeur explose
- 2,32 → 3,15 s : il tient la pose, tête levée
- 3,15 → 3,6 s : il se relève en garde

## Tâches suggérées pour Claude Code
1. Importer les animations : lancer `roblox/ElastiqueAnimations.lua` dans la barre de commande avec le rig sélectionné, publier, puis récupérer les IDs. (Option : convertir `elastique.js` en ModuleScript Luau pour générer les KeyframeSequence via Rojo.)
2. Placer `ElastiqueMembres.client.lua` dans `StarterPlayerScripts`.
3. Écrire un contrôleur de compétences (client + serveur) : jouer `Elastique_Gear2` puis activer l'état Gear 2 ; jouer `Elastique_Combo` sur input ; câbler les hitbox sur les marqueurs `Impact` avec validation serveur.
4. Créer les VFX listés dans le tableau des marqueurs (vapeur, explosion, feu, étincelles, onde au sol) et le camera shake côté client.
5. Ajouter un vrai déplacement du HRP pour la phase aérienne si nécessaire.

## Tokens du visualiseur (référence)
Peau `#d9a47a` (Gear 2 `#f2858a`), gilet `#c8372d`, short `#3b5a9a`, ceinture `#e2bd55`, chapeau `#e6c46a` avec bande `#b32a22`, sandales `#5a3a24`. Accent de l'UI `#ff7a59`.
