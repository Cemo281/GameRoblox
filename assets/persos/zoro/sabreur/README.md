# Handoff : Sabreur à trois sabres — animations R15 + intégration combat Roblox

## Overview
Personnage Roblox (rig **R15**) qui combat avec trois sabres : main droite, main gauche, et un dans la bouche. **Périmètre : uniquement la « Séquence complète »** (Dégainage → Charge d'aura → Combat → Rengainage). Ce package contient **5 animations** déjà keyframées, prêtes à importer, et la spec pour les brancher en jeu : visibilité des sabres, hitbox, effets (VFX), déplacements.

Ce qu'il faut faire dans le jeu :
1. Importer les animations dans le projet Roblox et les publier pour obtenir leurs `AnimationId`.
2. Créer les 4 Accessory de sabres sur le personnage.
3. Écrire le système de combat qui joue les animations et réagit à leurs marqueurs (`KeyframeMarker`).

## About the Design Files
- **`Sabreur Animations.dc.html`, `viewer.js` et `anims.js` sont des références de design** : un visualiseur web (three.js) qui montre le mouvement attendu. Ce n'est pas du code à livrer dans le jeu.
- **`anims.js` est la source de vérité des poses**. Toutes les keyframes y sont définies ; le visualiseur et le script Luau sont générés à partir de ce fichier.
- **`roblox/SabreurAnimations.lua`** a été généré depuis `anims.js`. Il est utilisable tel quel dans Studio pour créer les `KeyframeSequence`.
- **`roblox/SabreurMarqueurs.client.lua`** est un exemple de LocalScript qui gère la visibilité des sabres. À adapter à l'architecture du jeu.

Si les poses changent : modifier `anims.js`, puis régénérer le Luau. Dans le navigateur, `SABRE.toLuau()` renvoie le script ; le visualiseur a aussi un bouton « Copier le script Luau ».

## Fidelity
**Haute fidélité pour le mouvement** : les angles, le timing et l'easing sont définitifs. Le visualiseur est approximatif sur les proportions du rig (dimensions R15 « blocky » standard). Il faut vérifier le rendu final sur le vrai personnage dans l'Animation Editor.

## Import des animations (Studio)
1. Sélectionner le Model R15 du personnage, celui qui contient le `Humanoid`, dans l'Explorer.
2. Ouvrir la barre de commande (Affichage › Barre de commande), coller `roblox/SabreurAnimations.lua`, puis Entrée.
   - Le script crée `ServerStorage.RBX_ANIMSAVES.<NomDuRig>` (un `ObjectValue` qui pointe vers le rig) et y ajoute une `KeyframeSequence` par animation.
   - Si une séquence du même nom existe déjà, elle est remplacée.
3. Dans Avatar › Éditeur d'animation, choisir le rig, puis ⋯ › Charger › `Sabreur_…`, puis ⋯ › Publier sur Roblox.
4. Noter chaque `rbxassetid://…`. Les centraliser dans un module, par exemple `ReplicatedStorage/Shared/SabreurAnims.lua` → `{ [nom] = "rbxassetid://..." }`.

Détails techniques des séquences :
- Pose racine `HumanoidRootPart` avec Weight 0, puis la hiérarchie R15 complète. Chaque Pose a Weight 1.
- `Pose.CFrame = CFrame.new(px,py,pz) * CFrame.Angles(rad(rx),rad(ry),rad(rz))` : c'est la valeur du `Motor6D.Transform`.
- Easing `Cubic` émis en `Enum.PoseEasingStyle.CubicV2` (sens In/Out correct). Les autres styles utilisés sont `Linear` et `Constant`.
- Priorité : `Action` pour les 5 animations.

## Animations
Durées en secondes. Les marqueurs sont notés `t → Nom(valeur)`.

| Nom | Durée | Boucle | Rôle |
|---|---|---|---|
| Sabreur_Sequence_Complete | 9.2 | non | Les 4 animations ci-dessous, concaténées en un seul clip, avec tous leurs marqueurs décalés. Dégainage 0–1.4 · Aura 1.4–4.4 · Combat 4.4–7.8 · Rengainage 7.8–9.2 |
| Sabreur_Combat_Esquives | 3.4 | non | Esquive G (2 studs) + double coupe ; esquive D + double revers ; double coupe montante ; pas arrière ; saut + impact ; coupe X |
| Sabreur_Charge_Aura | 3.0 | non | Au sol, bras tendus écartés vers le bas, lames vers l'extérieur, respiration |
| Sabreur_Degainage | 1.4 | non | Dégaine droite, gauche, puis sabre en bouche, et passe en garde |
| Sabreur_Rengainage | 1.4 | non | Inverse du dégainage, finit bras relâchés |

Deux façons de jouer la séquence en jeu : lancer `Sabreur_Sequence_Complete` d'un bloc, ou jouer les 4 animations à la suite, chacune lancée quand la précédente a fini (`track.Stopped`). La deuxième façon permet d'interrompre ou de déclencher chaque phase séparément.

Marqueurs détaillés :
- **Combat_Esquives** : 0.16 Esquive(Gauche) · 0.4 Impact(Contre1) · 0.72 Esquive(Droite) · 0.96 Impact(Contre2) · 1.2 Impact(Contre3) · 1.38 Esquive(Arriere) · 2.12 Impact(Sol) · 2.48 Impact(CoupeX)
- **Charge_Aura** : 0.05 Aura(Debut) · 0.4 Explosion(Aura) · 2.8 Fin(Aura)
- **Degainage** :
  - à 0 : Montrer(SabresHanche) et Cacher(SabreDroit, SabreGauche, SabreBouche)
  - 0.22 Montrer(SabreDroit) · 0.55 Montrer(SabreGauche)
  - 0.95 Montrer(SabreBouche) et Cacher(SabresHanche)
- **Rengainage** : 0.25 Cacher(SabreBouche) · 0.65 Cacher(SabreGauche) et Montrer(SabresHanche) · 1.05 Cacher(SabreDroit)
- **Sequence_Complete** : mêmes marqueurs que les 4 animations, décalés de +1.4 (Aura), +4.4 (Combat) et +7.8 (Rengainage)

## Accessory requis sur le personnage
Il faut 4 `Accessory` rigides, chacun avec un `Handle` et un Attachment du même nom que celui du corps :

| Nom (exact) | Attachment | Contenu | Orientation |
|---|---|---|---|
| SabresHanche | LeftHipAttachment (LowerTorso) | 3 sabres au fourreau | pointent vers l'arrière et le bas |
| SabreDroit | RightGripAttachment (RightHand) | katana, poignée blanche | lame vers -Z de la main (convention Tool) |
| SabreGauche | LeftGripAttachment (LeftHand) | katana, poignée noire | lame vers -Z de la main |
| SabreBouche | FaceFrontAttachment (Head) | katana horizontal | lame vers +X (droite du perso), poignée à la bouche |

Les animations ont été calées sur ces orientations. Si un modèle arrive mal orienté, corriger le `CFrame` de son Attachment, pas les animations.

## Marqueurs → comportements à implémenter
| Marqueur | Valeur | Action en jeu |
|---|---|---|
| Montrer / Cacher | nom de l'Accessory | Transparency 0/1 sur les BasePart et Decal de l'Accessory. Déjà fait côté client dans `SabreurMarqueurs.client.lua` |
| Impact | id du coup | Hitbox devant le perso au moment du coup (validée **côté serveur**), dégâts, knockback, hit-stop d'environ 0.06 s, VFX de slash |
| Esquive | Gauche / Droite / Arriere | Déplacement réel : 2 studs (1 case) latéral ou arrière, plus i-frames d'environ 0.2 s |
| Aura | Debut | Démarrer les particules d'aura vertes sur le corps et les lames |
| Explosion | Aura | Onde de choc au sol, flash, éventuellement un tremblement de caméra |
| Fin | Aura | Couper l'aura |

⚠ **Pas de root motion.** Les fentes, esquives et sauts déplacent seulement le `LowerTorso` par rapport au `HumanoidRootPart`. À la fin du clip, le corps revient à sa place. Pour un vrai déplacement, il faut bouger le `HumanoidRootPart` par script (LinearVelocity ou tween de CFrame) sur les marqueurs Esquive et Impact. Les offsets prévus :
- Esquive : 2 studs
- Fentes : environ 1.2 à 1.6 studs vers l'avant
- Saut : aller-retour vertical d'environ 5.6 studs

## Architecture suggérée
- `ReplicatedStorage/Shared/SabreurAnims` : la table des IDs d'animation.
- **Client** : input, lecture via `Animator:LoadAnimation`, VFX locaux, et la logique Montrer/Cacher pour tous les personnages (Animator.AnimationPlayed).
- **Serveur** : RemoteEvent « Attaque ». Le serveur valide le cooldown et la distance, puis calcule la hitbox au timing de l'Impact. On peut lire les temps de marqueurs depuis une table partagée, plutôt que de faire confiance au client.
- **Déclenchement** : une touche lance la séquence complète, avec un cooldown. Le personnage commence et finit rengainé ; à la fin, revenir aux animations par défaut du Humanoid.

## Visualiseur (référence)
Ouvrir `Sabreur Animations.dc.html` dans un navigateur. Le fichier a besoin de `support.js`, de `anims.js` et de `viewer.js` dans le même dossier, et d'internet pour charger three.js r128.

Ce qu'on peut y faire :
- choisir une animation ;
- scrubber la timeline, avec les ticks de keyframes et les losanges de marqueurs ;
- changer la vitesse (0.1× à 1×) ;
- activer ou couper la boucle et les traînées de lames.

Les anneaux au sol (sur Impact et Explosion) et la lueur verte (entre Aura et Fin) représentent les VFX attendus.

Convention des angles dans `anims.js` (degrés, ordre `CFrame.Angles` X puis Y puis Z) :
- Épaule : +X lève le bras vers l'avant. +Z écarte le bras droit ; -Z écarte le gauche.
- Coude : +X plie le coude. Genou : -X plie le genou. Hanche : +X lève la jambe vers l'avant.
- Waist (UpperTorso) : +Y tourne le buste vers la gauche ; -X penche en avant.
- Root (LowerTorso) : position en studs, -Z = avant.

## Captures
`captures/` contient 12 images des poses clés, prises dans le visualiseur. Chaque nom de fichier donne l'animation et le temps (`t`) de la pose. Ces images servent de référence visuelle pour vérifier le rendu dans Studio. Les anneaux et la lueur verte qu'on y voit représentent les VFX attendus ; ils ne font pas partie des animations.

## Files
- `captures/*.jpg` — poses clés (référence visuelle)
- `Sabreur Animations.dc.html` — visualiseur
- `support.js` — runtime du visualiseur
- `anims.js` — données des poses, générateur Luau, script marqueurs
- `viewer.js` — rendu three.js (mannequin, sabres, traînées)
- `roblox/SabreurAnimations.lua` — script barre de commande Studio (5 KeyframeSequence)
- `roblox/SabreurMarqueurs.client.lua` — LocalScript Montrer/Cacher, avec un hook `onMarker` à compléter
