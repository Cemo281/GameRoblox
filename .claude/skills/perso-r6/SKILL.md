---
name: perso-r6
description: Crée un personnage R6 (ou R15 bloc si la fiche le dit) low-poly dans Blender via le MCP Blender à partir d'une fiche, avec ses trois animations (Idle en boucle, Action, Signature), ses accessoires séparés et ses VFX, l'exporte en FBX puis vérifie et finalise l'import dans Roblox Studio via le MCP Roblox_Studio. Usage - /perso-r6 <fiche du personnage>
argument-hint: <fiche du personnage>
---

# Personnage R6 : Blender → Roblox Studio

Fiche du personnage : $ARGUMENTS

Si la fiche est vide, ne commence pas : liste les `Id` de `src/shared/Personnages.luau` avec leur rareté et demande-moi la fiche.

## 0. Règles de travail
- Tout se fait par petits blocs Python envoyés au MCP Blender (un bloc = une étape), jamais un script géant. Les fonctions utilitaires (formes, palette, finition des meshes) peuvent être gardées d'un appel à l'autre dans `bpy.app.driver_namespace["<Id>"]`.
- Après chaque étape visible : capture du viewport (vue de face ET vue de 3/4), auto-critique honnête (proportions, couleurs, lisibilité de loin), correction si besoin.
- Points de contrôle ✋ : arrête-toi, montre le résultat, attends mon « ok » avant de continuer.
- Inspiré, pas copié : reprendre la silhouette, les couleurs et le rôle, mais aucun logo, texte, emblème ou symbole officiel. Pas de cigarette, d'alcool ni de sang (règles Roblox).
- Ne modifie jamais `src/`, `default.project.json` ni le code du jeu. Ne committe rien sans me demander (les .blend sont lourds).
- `Id` = l'identifiant du perso dans `src/shared/Personnages.luau` (ex. `nami`). Fichiers dans `assets/blender/<Id>/`.
- Si une info manque dans la fiche, choisis la solution la plus simple et dis-moi laquelle.
- Tiens à jour une section `Personnage <Id>` dans `docs/wiki/TODO.md`.

## 1. Style (validé sur `nami`)
- **Silhouette d'avatar Roblox** : gabarit R6 standard (torse 2×2×1, bras et jambes 1×1×2 en boîtes légèrement chanfreinées, tête Roblox classique = cylindre arrondi d'environ 1,4 de diamètre et 1,3 de haut). Pas de corps « chibi » affiné : c'est ce qui fait reconnaître un perso Roblox.
- Détails par la géométrie et les couleurs : rayures et bandes de vêtements (anneaux de prisme), ourlets en léger relief, ceinture, revers, semelles et lanières, bijoux.
- **Visage** plaqué sur la tête (polygones plats décalés de 0,01 à 0,05 du cylindre) : blanc de l'œil en amande, iris coloré, pupille, 1 ou 2 reflets blancs, cils épais du haut qui remontent vers l'extérieur, sourcils fins, petit nez, bouche expressive. Chercher les traits qui font reconnaître le perso.
- **Cheveux** : calotte volumineuse (plus large que le crâne, façon accessoire Roblox) + mèches effilées (section en losange qui finit en pointe) : frange, mèches qui encadrent le visage, nappe dans le dos. Deux tons (clair dessus, plus foncé dessous) pour le relief.
- Budget triangles selon la rareté : Commun ≤ 2 000, Rare ≤ 3 000, Légendaire ≤ 4 000, Mythique ≤ 5 000, Secret ≤ 6 000. Max 10 000 par pièce. Pour tenir le budget : moins de segments sur les petits cylindres et sphères, rien sous les faces cachées.
- Couleurs : une seule image `Palette_<Id>.png` (64×64, grille 4×4 de cases unies de 16 px, une case par couleur). Chaque face est dépliée (UV) au centre de sa case. Un seul matériau par mesh. Une couleur ajoutée à la fiche (noir des yeux, ton foncé des cheveux…) doit m'être signalée.
- Shading plat (Flat), normales recalculées vers l'extérieur (volume signé positif), pas de faces en double.

## 1 bis. Style B : avatar Roblox détaillé
S'applique quand la fiche contient « Style : B ». Cette section remplace la section 1 ; le corps est le rig R15 bloc de la section 2 bis (même si la fiche ne dit pas « Rig : R15 bloc »), et tout le reste du skill (section 1 ter, étapes, pièges) s'applique avec les adaptations de la section 2 bis.
- **Référence visuelle obligatoire** : `assets/references/style-roblox-zoro.png`, plus `assets/references/<Id>.png` s'il existe (prioritaire pour les couleurs et la tenue du perso). Lis-les avant l'étape 1. Si la référence de style manque, arrête-toi et dis-le-moi.
- **Corps** : rig R15 en blocs (section 2 bis). Boîtes à arêtes nettes (biseau ≤ 0,03), tête Roblox classique, aucune forme de muscle en géométrie.
- **Texture peinte au lieu de la palette** : une image `Texture_<Id>.png` de 1024×1024. Chaque face visible de chaque boîte a son propre rectangle UV, à environ 128 px par stud (même logique que les modèles Shirt / Pants de Roblox), plus des zones pour le visage et pour chaque accessoire.
- **Peinture façon vêtements Roblox de qualité** : aplats + ombrages doux en dégradé, contours sombres de 2 à 3 px, plis de tissu, coutures en pointillés, boutons, motifs, muscles dessinés (pectoraux, abdominaux, bras) avec traits et ombres, cicatrices. Les détails qui passent d'une face à l'autre (ceinture, plis, cicatrice) doivent se raccorder. Pas de rendu photo, pas de bruit.
- **Visage** : dessin animé peint sur l'avant de la tête, avec au moins 256×256 px de texture pour lui. Yeux avec contour noir épais, iris en dégradé, reflet, ombre de paupière ; sourcils expressifs ; bouche ; cicatrices et marques du perso. Il doit être lisible de loin. Gros plan obligatoire à l'étape 3.
- **Vêtements et accessoires en 3D, en couches**, comme des accessoires Roblox : cheveux (mèches en volume, deux tons peints), couvre-chef, manteau, pans de veste, écharpes, ceintures, armes au fourreau. Ils ont leur propre zone de texture peinte (plis, ombres, coutures). Les couches qui pendent du torse (`LowerTorso` en R15 : manteau, jupe, pans) restent un peu écartées des jambes pour limiter les traversées pendant l'animation, à vérifier sur toutes les images.
- **Méthode** : peins la texture avec un script Python + Pillow lancé hors de Blender (`uv run --with pillow assets/blender/<Id>/texture_<Id>.py`), garde le script pour pouvoir retoucher un détail sans tout refaire, puis charge l'image dans Blender. À chaque capture, montre la texture à plat ET le modèle texturé (rendu avec la texture visible, éclairage doux proche de Studio).
- **Export et Studio** : comme en section 3, avec `Texture_<Id>.png` à la place de `Palette_<Id>.png` (1024 px maximum, c'est la limite de Roblox).
- **Budgets de triangles** : pas de supplément pour le style B, ce sont ceux du rig (section 2 bis pour le R15 bloc). Les détails sont dans la texture, pas dans la géométrie.

## 1 ter. Trois animations, accessoires séparés et VFX
Valable pour les deux styles (sections 1 et 1 bis) et les deux rigs (sections 2 et 2 bis).

**Trois actions par perso**, décrites dans la fiche :
- `<Id>_Idle` : pose de base, en boucle (première et dernière image identiques). Priority = Idle.
- `<Id>_Action` : démonstration de pouvoir, jouée une fois. Priority = Action. Ce n'est PAS une animation de combat (le vrai combat aura ses propres animations plus tard).
- `<Id>_Signature` : geste typique, joué une fois. Priority = Action.

Règles communes aux trois :
- **Sur place**, sur la case du perso : le corps (`LowerTorso` en R15 bloc, `Torso` en R6) ne s'éloigne jamais de plus de 0,5 stud de sa position de départ (les bras peuvent avancer en translation pour un effet élastique). Les VFX restent dans un rayon de 5 studs autour du perso, pour ne pas déborder sur les cases voisines ni gêner les joueurs. Vérifie les deux par calcul sur toutes les images.
- **Raccords** : par défaut, Action et Signature commencent et finissent exactement sur l'image 0 de l'Idle (« pose neutre »), pour s'enchaîner sans saut. Si la fiche dit autre chose (ex. Zoro : l'Action finit sabres en main et la Signature les range), respecte la fiche. Dans tous les cas, vérifie que les images de raccord sont identiques (rotations et translations de tous les os, visibilité des accessoires).
- Mêmes règles qu'en étape 5 pour chaque action : pieds plantés, pas d'échelle, tête ≤ 10° si cheveux fusionnés, angles trouvés par calcul, captures à 4 moments clés. Point de contrôle ✋ après CHAQUE animation.

**Accessoires séparés** (objets qui apparaissent ou disparaissent) — exception à la règle « accessoires fusionnés » des sections 2 et 2 bis :
- Chaque objet nommé `Acc_<Nom>` dans la fiche est un mesh séparé (pas fusionné), parenté en rigide à l'os de la pièce qui le porte (même méthode que les pièces), avec sa zone dans la texture (ses cases de palette en style A). Il compte dans le budget de triangles.
- La fiche dit s'il est visible ou caché par défaut.
- Dans Studio : MeshPart `Acc_<Nom>` rangé dans un dossier `Accessoires` du modèle ; CanCollide / CanQuery / CanTouch = false, Massless = true, Anchored = false ; relié à sa pièce par un `Weld` (Part0 = la pièce, Part1 = l'accessoire, `C0 = Part0.CFrame:Inverse() * Acc.CFrame`, C1 = identité, pour qu'il ne bouge pas) ; attribut booléen `VisibleParDefaut` ; Transparency = 0 ou 1 selon cet attribut. Il passe par le même redressement que les pièces du corps après l'import (étape 8).

**Marqueurs** :
- Dans Blender, des marqueurs propres à chaque action (`action.pose_markers`, pas les marqueurs de la scène), nommés `Montrer Acc_<Nom>`, `Cacher Acc_<Nom>` ou `VFX <NomEffet>`.
- Exportés dans le JSON de l'action : `"marqueurs": [{"image": 12, "nom": "VFX Coupure"}, …]`.
- Dans Studio, un `KeyframeMarker` par marqueur (Name = `Montrer`, `Cacher` ou `VFX` ; Value = `Acc_<Nom>` ou `<NomEffet>`), dans le Keyframe le plus proche ; s'il n'y a pas de Keyframe à cette image, ajoute-en un (exporte aussi les images des marqueurs dans le JSON pour avoir leurs poses exactes).

**VFX** (créés dans Studio via le MCP Roblox_Studio, pas dans Blender) :
- Dossier `VFX` dans le modèle, un sous-dossier par effet, nommé comme dans la fiche. Les émetteurs (ParticleEmitter, Trail, Beam) sont placés sur des Attachments des pièces (ex. Attachment sur la lame d'`Acc_Sabre_Droit`), nommés `<NomEffet>_<n>` ; le sous-dossier contient un `ObjectValue` par émetteur (Value = l'émetteur) pour les retrouver.
- Tout est désactivé par défaut : ParticleEmitter Enabled = false, Trail Enabled = false, Beam Enabled = false.
- Attributs du sous-dossier, qui disent comment le jouer : `Mode` = `"Burst"` (`Emit(Quantite)`) ou `"Duree"` (activé pendant `Duree` secondes), `Quantite` (nombre), `Duree` (secondes).
- Un Trail ou un effet « activé de X à Y » dans la fiche : soit deux marqueurs (`VFX <Nom>` au début, `VFX <Nom>_Fin` à la fin), soit Mode `Duree`.
- Style : anime, net et lumineux, couleurs du perso, effets courts (0,2 à 1 s).
- Textures de particules : celles de Roblox, ou des images générées avec Pillow dans `assets/vfx/` (c'est moi qui les importe : arrête-toi et demande-moi les ID).
- Budget : 60 particules maximum à l'écran par effet (`Quantite` + `Rate × Lifetime` max), car plusieurs persos peuvent jouer en même temps. Rayon de 5 studs : distance de l'Attachment au centre du perso + `Speed` max × `Lifetime` max (+ taille des particules) ≤ 5.

**Publication** : 3 animations à publier (c'est moi qui clique, comme pour l'Idle). Attributs texte sur le modèle de ReplicatedStorage : `AnimationIdle`, `AnimationAction`, `AnimationSignature`.

**Prévisualisation dans Studio** : pour chaque action, 3 images sur des clones ancrés, avec les accessoires visibles au bon moment et les VFX allumés à l'image de leur marqueur ; capture, puis supprime les clones. Ne crée aucun script de jeu : la lecture des marqueurs en jeu sera codée à part.

## 2. Structure R6 (non négociable)
Le perso doit être un rig R6 : 7 pièces, chacune un objet mesh séparé, nommé exactement :
`HumanoidRootPart`, `Torso`, `Head`, `Left Arm`, `Right Arm`, `Left Leg`, `Right Leg`.

Unités : 1 unité Blender = 1 stud. Le perso regarde vers -Y dans Blender (vers la caméra en vue de face). Pieds à Z = 0. Hauteur totale entre 3,5 et 6,5 studs (cheveux compris).
Les pivots sont EXACTEMENT ceux des Motor6D R6 de Roblox (les animations R6 standard marcheront aussi) :

| Pièce | Taille X×Y×Z | Centre | Pivot (articulation) |
|---|---|---|---|
| HumanoidRootPart | 2×1×2 (boîte invisible) | (0, 0, 3) | — |
| Torso | 2×1×2 | (0, 0, 3) | (0, 0, 3) racine |
| Head | tête Roblox + cheveux | (0, 0, ≈4.65) | cou (0, 0, 4) |
| Right Arm | 1×1×2 | (-1.5, 0, 3) | épaule (-1, 0, 3.5) |
| Left Arm | 1×1×2 | (1.5, 0, 3) | épaule (1, 0, 3.5) |
| Right Leg | 1×1×2 | (-0.5, 0, 1) | hanche (-1, 0, 2) |
| Left Leg | 1×1×2 | (0.5, 0, 1) | hanche (1, 0, 2) |

(Le perso regarde vers -Y, donc SA droite est du côté -X.)

- Armature `Rig_<Id>` avec 7 os du même nom que les pièces. Hiérarchie : `HumanoidRootPart` → `Torso` → (`Head`, `Left Arm`, `Right Arm`, `Left Leg`, `Right Leg`). La tête (head) de chaque os est au pivot de sa pièce ; os du torse et de la tête vers le haut, bras et jambes droits vers le bas, roll 0. Avec ces os : pour les membres, rotation X– = vers l'avant, X+ = vers l'arrière ; pour le torse et la tête, X+ = penché en avant, Y+ = tête tournée vers SA gauche.
- La `location` d'un os est dans SON repère : pour `Torso`, la verticale du monde est l'axe Y local, pas Z.
- Chaque mesh est parenté à SON os en mode rigide (parent_type = 'BONE', `matrix_parent_inverse` calculé pour qu'il ne bouge pas), sans poids de vertex. Aucune déformation : en R6 chaque pièce bouge d'un bloc.
- Les accessoires (chapeau, cheveux, arme, instrument, livre…) sont FUSIONNÉS dans la pièce qui les porte (épée en main droite → dans `Right Arm`, chapeau → dans `Head`). Pas d'objet en plus, sauf les `Acc_<Nom>` de la fiche (section 1 ter).
- **Objet tenu en main** : un bras R6 n'a ni coude ni main séparée, la main est le bas du bras. L'objet doit TRAVERSER le poing (bas du bras, z ≈ 2,0–2,5) avec un angle franc par rapport au bras (≈ 65°), avec un pouce replié par-dessus. Jamais parallèle au bras. Une pose « objet posé contre l'épaule » est impossible sans coude (l'objet longerait le bras) : propose autre chose (bâton planté au sol, arme tenue devant…) et dis-le-moi.
- Transformations appliquées (Ctrl+A) sur les meshes, origine de chaque mesh au pivot de sa pièce.

## 2 bis. Structure R15 bloc
S'applique quand la fiche contient « Rig : R15 bloc ». Cette section remplace la section 2 ; le style (section 1 ou 1 bis), la section 1 ter, les étapes et les pièges s'appliquent avec les adaptations ci-dessous. Sans cette mention, le perso reste en R6 (`nami` est en R6 : ne touche pas à ses fichiers).

**Référence** : `assets/rig/r15_bloc.json`, relevé sur le rig R15 en blocs de Roblox (`Players:CreateHumanoidModelFromDescription` avec la HumanoidDescription par défaut). Il contient la taille et la CFrame (relative à HumanoidRootPart) des 16 pièces, Part0 / Part1 / C0 / C1 des 15 articulations, et une section `blender` (articulations et centres déjà convertis, `hauteurHRP`). Roblox n'y met plus de Motor6D mais des `AnimationConstraint` : C0 / C1 sont les CFrame de leurs Attachment0 / Attachment1, ce qui est équivalent. Toutes ces CFrame sont sans rotation.

**Gabarit** : copie `assets/rig/r15_bloc.blend` dans `assets/blender/<Id>/<Id>.blend`, puis renomme l'armature `Rig_R15` en `Rig_<Id>`. Ne modifie jamais le gabarit lui-même.

16 pièces, chacune un objet mesh séparé, nommé exactement :
`HumanoidRootPart`, `LowerTorso`, `UpperTorso`, `Head`, `LeftUpperArm`, `LeftLowerArm`, `LeftHand`, `RightUpperArm`, `RightLowerArm`, `RightHand`, `LeftUpperLeg`, `LeftLowerLeg`, `LeftFoot`, `RightUpperLeg`, `RightLowerLeg`, `RightFoot`.

Repère : le même qu'en R6 (1 unité = 1 stud, le perso regarde vers -Y, SA droite est -X, pieds à Z = 0), mais le centre de HumanoidRootPart est à Z = `hauteurHRP` ≈ 3,1924 au lieu de 3. Correspondance (vérifiée sur le JSON) : Blender (x, y, z) = (-xR, zR, yR + hauteurHRP), c'est-à-dire la même matrice `A = ((-1,0,0),(0,0,1),(0,1,0))` qu'en R6.

| Pièce | Taille X×Y×Z (Blender) | Centre | Pivot (articulation, Motor6D) |
|---|---|---|---|
| HumanoidRootPart | 2×1×2 (boîte invisible) | (0, 0, 3.192) | — |
| LowerTorso | 1.991×1.004×0.401 | (0, 0, 2.392) | `Root` (0, 0, 2.192) |
| UpperTorso | 1.943×1.004×1.698 | (0, 0, 3.441) | `Waist` (0, 0, 2.592) |
| Head | tête Roblox classique (comme `nami`) + cheveux | bas de la tête au cou | `Neck` (0, 0, 4.290) |
| Right/LeftUpperArm | 1.001×1.002×1.242 | (∓1.472, 0, 3.620) | `…Shoulder` (∓0.972, 0, 4.039) |
| Right/LeftLowerArm | 1.001×1.002×1.118 | (∓1.472, 0, 2.990) | `…Elbow` (∓1.472, 0, 3.265) |
| Right/LeftHand | 0.984×1.028×0.316 | (∓1.472, 0, 2.327) | `…Wrist` (∓1.472, 0, 2.458) |
| Right/LeftUpperLeg | 0.993×0.973×1.363 | (∓0.5, 0, 1.721) | `…Hip` (∓0.5, 0, 2.192) |
| Right/LeftLowerLeg | 0.993×0.973×1.301 | (∓0.5, 0, 0.859) | `…Knee` (∓0.5, 0, 1.272) |
| Right/LeftFoot | 1.009×1.001×0.312 | (∓0.5, 0, 0.156) | `…Ankle` (∓0.5, 0, 0.262) |

(∓ : signe du haut pour la droite. Valeurs arrondies : les exactes sont dans le JSON.) Dans le rig Roblox, les segments se chevauchent aux articulations (au coude, chaque segment dépasse d'environ 0,27 dans l'autre ; au genou, d'environ 0,24) : c'est normal, garde-le pour que rien ne s'ouvre quand le membre plie.

- **Armature** `Rig_<Id>`, un os par pièce, même nom. Hiérarchie = celle des Motor6D : `HumanoidRootPart` → `LowerTorso` → (`UpperTorso` → (`Head`, `LeftUpperArm` → `LeftLowerArm` → `LeftHand`, `RightUpperArm` → `RightLowerArm` → `RightHand`), `LeftUpperLeg` → `LeftLowerLeg` → `LeftFoot`, `RightUpperLeg` → `RightLowerLeg` → `RightFoot`). La tête de chaque os est à son articulation (position monde de `Part0.CFrame * C0`), os du torse et de la tête vers le haut, os des membres verticaux vers le bas, roll 0. Mêmes conventions qu'en R6 : membres X– = vers l'avant, X+ = vers l'arrière (vérifié sur le gabarit) ; torse et tête X+ = penché en avant.
- **Aucune déformation** : chaque mesh est parenté en rigide à SON os (parent_type = 'BONE', `matrix_parent_inverse` calculé), sans poids de vertex. Chaque pièce bouge d'un bloc.
- **Style en blocs** : boîtes à arêtes nettes (biseau ≤ 0,03) aux tailles du tableau, comme `assets/references/style-roblox-zoro.png`. Les détails sont dans la texture (style B) ou dans des reliefs fins (style A), pas en déformant les boîtes. Origine de chaque mesh au pivot de sa pièce, transformations appliquées.
- **Accessoires fusionnés** dans la pièce qui les porte : objet tenu → `RightHand` / `LeftHand`, chapeau et cheveux → `Head`, fourreau, ceinture et pans de ceinture → `LowerTorso`, sac à dos, cape et col → `UpperTorso`. Un vêtement qui couvre deux pièces (manteau long) est coupé à l'articulation : le haut dans `UpperTorso`, les pans dans `LowerTorso` (ou dans `UpperLeg` s'ils doivent suivre la jambe). Pas d'objet en plus, sauf les `Acc_<Nom>` de la fiche (section 1 ter), parentés à l'os de la pièce qui les porte.
- **Objet tenu en main** : il traverse le poing de la `Hand` (fusionné dans la main), avec un angle franc par rapport à l'avant-bras ; la règle R6 « l'objet traverse le bas du bras » ne s'applique pas.
- **Articulations** :
  - coude et genou ne plient que dans un sens, de 0 à 150° : coude vers l'avant (X–), genou vers l'arrière (X+). Jamais d'angle négatif ni de rotation autour des autres axes sur ces deux os ;
  - poignets et chevilles : ±30° sur chaque axe ;
  - **pieds plantés et mains posées sur un point** (sol, poignée, menton, hanche) : résous-les en IK à deux os (hanche–genou ou épaule–coude), pas en tournant la jambe ou le bras entier. Calcul : distance articulation → cible, angle du genou / coude par la loi des cosinus (longueurs des os du gabarit), puis orientation de l'os du haut pour viser la cible, en gardant le plan de flexion (genou vers l'avant, coude vers l'arrière et l'extérieur). La cheville ou le poignet compense ensuite pour garder le pied à plat ou la main orientée (dans ±30°). Vérifie sur toutes les images la distance du pied à son point au sol (< 0,02) ;
  - les règles R6 « pas de coude / pas de genou » (bâton planté, jambes tendues, objet impossible contre l'épaule) ne s'appliquent pas au R15.
- **Ce qui change dans les étapes** : partout où les étapes disent `Torso`, lis `LowerTorso` (racine du corps : translation, rebond ≤ 0,5 stud, centre c = (0, 0, `hauteurHRP`)) ; « boîte du torse » = `UpperTorso` ; « 7 pièces / 7 meshes » = 16 ; « bras » pour l'effet élastique = `UpperArm`. Les étapes 8 et 9 ont chacune leur variante R15 ci-dessous.
- **Budgets de triangles** : +20 % par rapport au R6 : Commun ≤ 2 400, Rare ≤ 3 600, Légendaire ≤ 4 800, Mythique ≤ 6 000, Secret ≤ 7 200. Max 10 000 par pièce.
- Hauteur totale entre 3,5 et 6,5 studs (gabarit nu : 5,59 avec la tête classique).

## 3. Étapes
1. **Fiche** : reformule la fiche en 10 lignes max (silhouette, palette en hex, accessoires et pièce qui les porte, `Acc_<Nom>` visibles ou cachés par défaut, déroulé des 3 animations avec leurs marqueurs et VFX). Signale tout de suite ce qui est impossible en R6 (voir « Objet tenu en main »). ✋
2. **Blockout** : formes grossières des 7 pièces + accessoires, sans couleur. Captures face, profil, 3/4.
3. **Modèle final** : détails, palette, UV, visage, cheveux. Vérifie le budget de triangles (affiche le compte par pièce). Captures face, 3/4, dos, profil, et un gros plan du visage. Simule aussi la pose principale de l'objet tenu (rotation temporaire de l'objet bras, puis remise à zéro). Sauvegarde `assets/blender/<Id>/<Id>.blend`. ✋
4. **Rig** : armature + parentage rigide (pièces et `Acc_<Nom>`, chacun à l'os de la pièce qui le porte). Teste en tournant chaque os de 45° (capture), puis remets tout à zéro.
5. **Animations** : trois actions dans cet ordre, `<Id>_Idle`, `<Id>_Action`, `<Id>_Signature` (section 1 ter), 30 images/s, durées de la fiche. Pour chacune : clés sur les os en rotation (quaternions, signes continus d'une clé à l'autre) ; translation seulement sur le corps (`Torso` en R6, `LowerTorso` en R15 bloc : petit rebond, ≤ 0,5 stud de sa position de départ), sur les bras (effet élastique) ou si la fiche le demande. Jamais d'échelle (Roblox l'ignore). Interpolation Bézier avec easing (auto clamped), petits décalages entre les membres (overlap).
   - **Idle** : première et dernière image identiques pour une boucle parfaite (vérifie toutes les courbes).
   - **Action et Signature** : première et dernière image = image 0 de l'Idle, sauf raccords différents dans la fiche ; compare les valeurs de tous les os aux images de raccord (et la visibilité des accessoires).
   - **Marqueurs** `Montrer Acc_<Nom>` / `Cacher Acc_<Nom>` / `VFX <NomEffet>` dans `action.pose_markers`. Pour les captures, applique la visibilité des `Acc_` selon les marqueurs à l'image capturée (et repère la position des VFX par un petit objet temporaire si utile, supprimé ensuite).
   - Chaque action a `use_fake_user = True` (sinon Blender supprime à l'enregistrement les actions non assignées) ; pour passer de l'une à l'autre, change `rig.animation_data.action`.
   - **Pieds plantés** : à chaque clé, recalcule la rotation des jambes pour que le bout de chaque jambe vise son point au sol (différence de rotation entre la direction actuelle et la direction hanche → pied, ramenée dans le repère de l'os). Puis mesure sur toutes les images le point le plus bas des jambes, et remonte le torse aux clés où les pieds passent sous le sol. En R15 bloc, résous plutôt chaque pied en IK à deux os hanche–genou (section 2 bis).
   - **Objet planté au sol** (bâton…) : même calcul sur le bras qui le tient, avec un point fixe au sol. La longueur est fixe : l'objet décolle un peu quand le torse monte, garde ce rebond petit.
   - **Cheveux fusionnés à la tête** : limite les rotations de la tête à ≈ 10° (tourner, pencher) et vérifie qu'aucun sommet de cheveux n'entre dans la boîte du torse sur toute l'animation.
   - Pour trouver une pose (ex. « bourse devant le visage »), cherche les angles par calcul (grille de valeurs X/Z, distance au point visé) plutôt qu'à l'œil.
   - Captures à 4 moments clés, de face et de 3/4. ✋ après CHAQUE animation (Idle, puis Action, puis Signature).
6. **Export** (sélectionner l'armature + les 7 meshes + les `Acc_<Nom>`, tous rendus visibles le temps de l'export, sinon ils ne sont pas sélectionnables ; pour le modèle, retirer l'action et remettre le rig en pose de repos, puis la remettre) :
   - `assets/blender/<Id>/<Id>.fbx` : `bpy.ops.export_scene.fbx(use_selection=True, object_types={'ARMATURE','MESH'}, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', add_leaf_bones=False, mesh_smooth_type='FACE', path_mode='COPY', embed_textures=True, bake_anim=False)`
   - `assets/blender/<Id>/<Id>_Idle.fbx`, `<Id>_Action.fbx`, `<Id>_Signature.fbx` : mêmes options mais `bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0`, avec l'action correspondante active (archives ; les animations passent par l'étape 9).
   - Enregistre aussi `Palette_<Id>.png` dans le même dossier.
   - Vérifie en réimportant chaque FBX dans une scène temporaire (os, meshes dont les `Acc_`, triangles, texture, hauteur), puis supprime la scène ET les dossiers `.fbm` (`<Id>.fbm`, `<Id>_Idle.fbm`, `<Id>_Action.fbm`, `<Id>_Signature.fbm`) que la réimport crée à côté des FBX.
7. **Import (c'est moi qui clique)** : explique-moi en 3 lignes : Studio → **Fichier → Importer** (Ctrl+M) ou Accueil → **Importer** → `<Id>.fbx` → clic sur sa ligne dans la file d'attente d'importation (en bas) pour l'aperçu → unité « Stud » / rig « R6 » si proposés → bouton **Importer**. Pas de bouton « Import 3D » dans l'onglet Avatar. Attends que je dise « importé ».
8. **Vérification et finition dans Studio (MCP Roblox_Studio, en Luau)** :
   - Récupère le `studio_id` avec `list_roblox_studios` (il change à chaque relance de Studio).
   - Trouve le modèle importé (`Workspace.<Id>`). Liste ses descendants : l'importeur ajoute en général une Part `RootPart`, un dossier `InitialPoses`, un `AnimationController`, et des Motor6D nommés `<Pièce>Motor6D` (dont un HumanoidRootPart→HumanoidRootPart).
   - **Pièces couchées** : l'importeur couche chaque mesh parenté à un os de 90° (tailles avec la hauteur sur Z, jambes vers l'arrière). Contrôle : la taille du Torso doit être ≈ 2×2×1 (X×Y×Z) une fois en place. Correction, dans cet ordre :
     1. ancre toutes les pièces et **détruis tous les Motor6D d'abord** (sinon chaque pièce déplacée entraîne tout l'assemblage) ;
     2. si l'assemblage a bougé, ramène-le avec la pose d'origine (HumanoidRootPart sans rotation) ;
     3. tourne chaque pièce de **+90° autour de l'axe X du monde, autour de SON articulation**. Correspondance Blender → Roblox autour du centre du torse : (x, y, z) → (-x, z - 3, y). Vérifie que le centre de chaque pièce retombe là où il est dans Blender, et regarde de face (visage visible, rayures en haut du torse) ;
     4. remplace HumanoidRootPart par une `Part` 2×2×1 sans rotation au centre du torse ; supprime `RootPart` et `InitialPoses`.
   - **Accessoires `Acc_<Nom>`** : ils sont couchés comme les pièces : même rotation de +90° autour de l'axe X du monde, autour de l'articulation de la pièce qui les porte (avant de créer les Weld). Vérifie leur position par rapport à leur pièce comme dans Blender. Si l'importeur leur a créé un Motor6D, il part avec les autres. Puis finition selon la section 1 ter (dossier `Accessoires`, Weld, Massless, `VisibleParDefaut`, Transparency).
   - **Motor6D** : crée les 6 Motor6D R6 standard (`RootJoint` dans HumanoidRootPart : HumanoidRootPart→Torso ; dans Torso : `Neck`, `Left Shoulder`, `Right Shoulder`, `Left Hip`, `Right Hip`). Repère R = `CFrame.new(HumanoidRootPart.Position)` ; articulation J = R * repère standard R6 (RootJoint `CFrame.new(0,0,0, -1,0,0, 0,0,1, 0,1,0)`, Neck `(0,1,0, -1,0,0, 0,0,1, 0,1,0)`, Right Shoulder `(1,0.5,0, 0,0,1, 0,1,0, -1,0,0)`, Left Shoulder `(-1,0.5,0, 0,0,-1, 0,1,0, 1,0,0)`, Right Hip `(1,-1,0, 0,0,1, 0,1,0, -1,0,0)`, Left Hip `(-1,-1,0, 0,0,-1, 0,1,0, 1,0,0)`) ; `C0 = Part0.CFrame:Inverse() * J`, `C1 = Part1.CFrame:Inverse() * J`. Vérifie `Part0.CFrame * C0 * C1:Inverse() == Part1.CFrame`.
   - **Variante R15 bloc** (section 2 bis), à la place des points « Pièces couchées » et « Motor6D » ci-dessus (le point « Accessoires » s'applique tel quel) :
     - même redressement : ancre tout, détruis tous les Motor6D de l'importeur, ramène l'assemblage si besoin, puis tourne chaque pièce (et chaque `Acc_<Nom>`) de +90° autour de l'axe X du monde, autour de SON articulation. Correspondance autour du centre de HumanoidRootPart : (x, y, z) → (-x, z - hauteurHRP, y). Contrôle : la taille de `UpperTorso` doit être ≈ 1,94×1,70×1,00 (X×Y×Z) une fois en place ; le centre de chaque pièce retombe là où il est dans Blender ;
     - HumanoidRootPart = `Part` 2×2×1 sans rotation à (0, `hauteurHRP`, 0) au-dessus du sol du perso, comme dans le JSON ; supprime `RootPart` et `InitialPoses` ;
     - crée les 15 Motor6D R15 standard, chacun rangé dans son Part1 (comme le champ `parent` du JSON) : `Root` (HumanoidRootPart → LowerTorso), `Waist` (LowerTorso → UpperTorso), `Neck` (UpperTorso → Head), `LeftShoulder` / `RightShoulder` (UpperTorso → …UpperArm), `LeftElbow` / `RightElbow` (…UpperArm → …LowerArm), `LeftWrist` / `RightWrist` (…LowerArm → …Hand), `LeftHip` / `RightHip` (LowerTorso → …UpperLeg), `LeftKnee` / `RightKnee` (…UpperLeg → …LowerLeg), `LeftAnkle` / `RightAnkle` (…LowerLeg → …Foot) ;
     - C0 / C1 tirés de `assets/rig/r15_bloc.json` : articulation J = HumanoidRootPart.CFrame * `CFrame.new(pieces[Part0].cframe) * CFrame.new(motors[n].c0)` (sans rotation), puis `C0 = Part0.CFrame:Inverse() * J`, `C1 = Part1.CFrame:Inverse() * J`. Sur une pièce restée une boîte nue, ça redonne exactement les C0 / C1 du JSON (vérifie-le, écart < 0,01) ; sur une pièce qui porte un accessoire fusionné (tête, main avec arme…), le centre du MeshPart bouge, donc C0 / C1 diffèrent du JSON mais l'articulation reste au même endroit, et c'est ce qui compte. Vérifie pour les 15 l'aller-retour `Part0.CFrame * C0 * C1:Inverse() == Part1.CFrame` (position < 0,001, rotation identique) ;
     - n'ajoute ni `AnimationConstraint` ni `BallSocketConstraint` (c'est le système des avatars joueurs, pas celui de nos modèles posés) ; la suite (orientation avec `RightUpperArm`, textures, réglages des 16 pièces, `AnimationController` + `Animator`, VFX, rangement) est la même qu'en R6. Si l'éditeur d'animation refuse le rig, `Humanoid` avec RigType R15.
   - Hauteur totale entre 3,5 et 6,5 studs, sinon `Model:ScaleTo()` pour corriger.
   - Orientation : `HumanoidRootPart.CFrame:PointToObjectSpace(model["Right Arm"].Position).X` doit être > 0 (le perso regarde vers l'avant). Sinon, corrige dans Blender (rotation 180°) et réexporte.
   - Textures : chaque MeshPart a une TextureID non vide, sinon dis-moi d'importer `Palette_<Id>.png`.
   - Réglages : `PrimaryPart` = HumanoidRootPart ; HumanoidRootPart Anchored = true, Transparency = 1 ; toutes les pièces CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = true (sauf HumanoidRootPart), Material = SmoothPlastic ; les autres pièces Anchored = false.
   - Ajoute un `AnimationController` avec un `Animator` (plus léger qu'un Humanoid pour des dizaines de persos posés). Si l'éditeur d'animation refuse le rig, ajoute plutôt un `Humanoid` (RigType R6, DisplayDistanceType None).
   - **VFX** : crée le dossier `VFX` et un sous-dossier par effet de la fiche (section 1 ter : Attachments, émetteurs désactivés, ObjectValue, attributs `Mode` / `Quantite` / `Duree`). Si des textures Pillow sont nécessaires, génère-les dans `assets/vfx/`, puis arrête-toi pour que je les importe et te donne les ID. Vérifie par calcul le budget de 60 particules et le rayon de 5 studs de chaque effet.
   - Range le modèle dans `ReplicatedStorage.ModelesPersonnages` (crée le dossier s'il n'existe pas), nommé `<Id>`.
9. **Animations : KeyframeSequences générées (voie principale)**, une par action (`<Action>` = `Idle`, `Action`, `Signature`). L'import FBX de l'éditeur d'animation passe par le même importeur (orientation des os fausse) : ne l'utilise pas.
   - Dans Blender : mémorise la matrice monde de chaque pièce en pose de repos (action retirée), puis pour chaque action, pour une image sur deux, plus la dernière image et les images des marqueurs : `D = matrice_monde(image) @ matrice_repos⁻¹`, translation ramenée au centre du torse (`R·c + t - c`, c = (0,0,3)), puis passage dans le repère Roblox avec `A = ((-1,0,0),(0,0,1),(0,1,0))` : rotation `A·R·Aᵀ` en quaternion, translation `A·t`. Seulement les 7 pièces : les `Acc_` suivent leur pièce par leur Weld. Écris le tout en JSON dans `assets/blender/<Id>/<Id>_<Action>_roblox.json`, avec la liste `marqueurs` (image + nom).
   - Dans Studio : pièce animée = `CFrame(D) * repos` (repos relatif à HumanoidRootPart) ; pour chaque Motor6D, `Pose.CFrame = C0⁻¹ · Part0_animée⁻¹ · Part1_animée · C1` (vérifie l'aller-retour). `KeyframeSequence` `<Id>_<Action>` : poses en Linear, hiérarchie HumanoidRootPart (Weight 0) → Torso → les 5 autres ; Idle : Loop = true, Priority = Idle ; Action et Signature : Loop = false, Priority = Action. Ajoute les `KeyframeMarker` (section 1 ter) dans le Keyframe de l'image de chaque marqueur.
   - **Variante R15 bloc** : même conversion, avec c = (0, 0, `hauteurHRP`) au lieu de (0, 0, 3), et les 16 pièces (toujours sans les `Acc_`). Une `Pose` par pièce, nommée comme elle, et la hiérarchie des Pose suit l'arbre des Motor6D R15 : `HumanoidRootPart` (Weight 0) → `LowerTorso` → (`UpperTorso` → (`Head`, `LeftUpperArm` → `LeftLowerArm` → `LeftHand`, `RightUpperArm` → `RightLowerArm` → `RightHand`), `LeftUpperLeg` → `LeftLowerLeg` → `LeftFoot`, `RightUpperLeg` → `RightLowerLeg` → `RightFoot`). La Pose d'une pièce porte la CFrame du Motor6D dont elle est Part1 (formule ci-dessus). Avant d'écrire la séquence, vérifie sur 3 images que les CFrame recomposées depuis la racine (`Part0 * C0 * Pose * C1⁻¹`) redonnent les pièces animées, et que coudes et genoux restent dans 0–150° du bon côté.
   - **Prévisualisation** : pour chaque action, 3 images sur des clones ancrés posés au sol (lancer de rayon), avec la visibilité des `Acc_` selon les marqueurs passés à cette image et les VFX allumés à l'image de leur marqueur (`Emit` ou Enabled = true sur le clone) ; capture, puis supprime les clones. Aucun script de jeu : la lecture des marqueurs en jeu sera codée à part.
   - Mets une copie de travail du modèle dans le Workspace. Demande-moi d'abord d'ouvrir l'éditeur d'animation dessus : il crée sa propre entrée `ServerStorage.RBX_ANIMSAVES.<Id>` (ObjectValue, avec « Automatic Save »). Range les 3 `KeyframeSequence` DANS cette entrée-là, sinon « Charger » ne les propose pas.
   - **C'est moi qui clique**, 3 fois : explique-moi : sélectionner `Workspace.<Id>` → onglet Avatar → **Animation…** → « … » → **Charger** → `<Id>_<Action>` → Lecture pour vérifier (les marqueurs apparaissent au-dessus de la timeline) → « … » → **Publier sur Roblox** → me donner l'ID ; recommencer pour les deux autres.
   - Avec les 3 ID : vérifie que chacun se charge (`KeyframeSequenceProvider:GetKeyframeSequenceAsync`) et que ses `KeyframeMarker` sont toujours là ; ajoute les attributs texte `AnimationIdle`, `AnimationAction`, `AnimationSignature` = `"rbxassetid://<ID>"` sur le modèle de ReplicatedStorage, supprime la copie de travail, et rappelle-moi d'enregistrer la place.
10. **Bilan** : 5 lignes max : ce qui est fait, triangles, durée des 3 animations, accessoires et VFX créés, ce qui reste à faire de mon côté.

## 4. Pièges connus
- **Caméra de Studio** : `screen_capture` avec `camera_position` déplace la caméra ; si l'appel expire, elle reste en `Scriptable` (plus de contrôle souris, et c'est enregistré avec la place). Après chaque capture, vérifie `workspace.CurrentCamera.CameraType` et remets `Fixed` si besoin ; demande-moi d'enregistrer la place ensuite. Préfère les captures Blender (`look`) quand c'est possible.
- Le MCP Blender : un calque `int` créé sur un bmesh invalide les références de faces déjà créées ; crée le calque de couleur AVANT la géométrie.
- Faces de révolution (tête, calotte) : ordre des sommets (bas k, bas k+1, haut k+1, haut k) pour des normales vers l'extérieur ; les surfaces ouvertes ne sont pas corrigées par le recalcul des normales.
