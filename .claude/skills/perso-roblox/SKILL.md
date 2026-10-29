---
name: perso-roblox
description: Crée un personnage R15 « blocs arrondis » façon avatar Roblox haut de gamme (corps, tête, cheveux et tenue modélisés et texturés dans Blender, assemblage R15, animations et VFX dans Studio) via les MCP Blender et Roblox_Studio. Usage - /perso-roblox <fiche du personnage>
argument-hint: <fiche du personnage>
---

# Personnage R15 « blocs arrondis » : Blender + Studio

Fiche du personnage : $ARGUMENTS

Si la fiche est vide, liste les `Id` de `src/shared/Personnages.luau` avec leur rareté et demande-moi la fiche.
Avant tout, vérifie que le mannequin existe (`assets/persos/_mannequin/mannequin.blend` et `r15_bloc.json`, créés par le « prompt M »). Sinon, arrête-toi et dis-le-moi.

## 0. Règles de travail
- Blender : tout ce qui se voit (corps, tête et face, cheveux, tenue, accessoires, textures). Studio : assemblage R15, animations, VFX, finition.
- Petites étapes (un appel MCP = une étape), jamais de script géant. Après chaque étape visible : capture, auto-critique honnête en comparant avec les références (même angle), correction.
- Points de contrôle ✋ : arrête-toi, montre le résultat, attends mon « ok ».
- Les noms One Piece sont des noms de travail : aucun logo, texte ou emblème officiel. Pas de cigarette, d'alcool ni de sang (règles Roblox).
- Ne modifie jamais `src/` ni `default.project.json`. Ne committe rien sans me demander.
- Fichiers dans `assets/persos/<Id>/`. Tiens à jour une section `Personnage <Id>` dans `docs/wiki/TODO.md`.
- Ce que JE fais à la main (explique-moi en 3 lignes max) : importer les FBX (Fichier → Importer), importer les images si besoin, publier les animations. Regroupe ces actions.
- Si une info manque dans la fiche, choisis la solution la plus simple et dis-moi laquelle.

## 1. Style
Références à lire avant l'étape 1 :
- `assets/references/style-roblox-gojo.png` : la FINITION et la SILHOUETTE à atteindre (blocs arrondis, tête arrondie, tenue en couches, cheveux nets).
- `assets/references/style-roblox-zoro.png` : le niveau de détail peint d'un avatar Roblox (muscles, cicatrices, plis).
- `assets/references/<Id>.png` s'il existe : prioritaire pour la tenue, les couleurs et les traits du perso.

Règles :
- **Silhouette « blocs arrondis »** : proportions exactes du R15 en blocs (`r15_bloc.json`), mais chaque bloc a ses arêtes arrondies (biseau ≈ 0,15 stud, 3 segments, pas de sphère molle). Lecture : cubique de loin, douce de près. Pas de muscles en géométrie.
- **Tête** : celle du mannequin (cube très arrondi, un peu plus large en haut). La **face est peinte dans la texture de la tête**, dépliée (UV) sur l'avant et le début des côtés, pour qu'elle épouse la forme de la tête : jamais un decal plat posé devant.
- **Face style anime / manga** : grands yeux avec contour noir épais en haut, iris en dégradé (foncé en haut, clair en bas) avec 1 ou 2 reflets blancs nets, ombre de paupière, sourcils fins et expressifs, petit nez suggéré, bouche simple, ombre douce sous la frange. Traits nets, pas de flou.
- **Cheveux très propres** : un seul mesh de mèches en pointes nettes, regroupées en grosses masses lisibles (pas de spaghetti), volume plus large que le crâne, frange qui descend sur le front. Pas de trous, pas d'intersection visible avec la tête. Ombrage façon cel-shading peint : 2 ou 3 tons nets + liserés clairs sur le dessus des mèches.
- **Tenue très détaillée, en couches 3D** : les vêtements sont des volumes qui enveloppent le corps (veste, manches amples, col, jupe de manteau, ceinture nouée…), légèrement décollés du corps. Plis modélisés légers + plis et ombres peints en dégradés doux (comme un bake d'occlusion ambiante), coutures, petits détails (cordelettes, glands, nœuds, boutons, matelassage, ourlets).
- **Rigide** : chaque morceau de vêtement est découpé selon les pièces R15 et fusionné dans la pièce qui le porte (manche haute → UpperArm, manche basse → LowerArm, pans de veste → LowerTorso…), pour suivre l'animation sans déformation. Découpe aux coudes et aux genoux avec un léger chevauchement pour ne pas voir de trou quand ça plie.
- **Textures** : 3 images de 1024×1024 maximum (`tex_corps_<Id>.png` corps + tête/face, `tex_cheveux_<Id>.png`, `tex_tenue_<Id>.png`). Couleurs de base, bake d'occlusion ambiante dans Blender pour les ombres douces, puis lignes et détails peints par script Python + Pillow (`uv run --with pillow assets/persos/<Id>/peindre_<Id>.py`), script gardé pour pouvoir retoucher un détail.
- **Budget** : 15 000 triangles maximum pour tout le perso, 10 000 maximum par MeshPart.

## 2. Modélisation (Blender)
1. **Fiche** : reformule en 10 lignes max (silhouette, palette en hex, pièces de tenue et pièce R15 qui porte chacune, accessoires séparés, déroulé des 3 animations). ✋
2. Copie `assets/persos/_mannequin/mannequin.blend` dans `assets/persos/<Id>/<Id>.blend`. Garde l'armature, les pivots et les 15 pièces arrondies (adapte seulement la couleur de peau).
3. **Blockout** des cheveux, de la tenue et des accessoires, sans texture. Captures face, profil, 3/4, dos.
4. **Modèle final** : détails, UV, textures (étape 1 « Textures »), face peinte. Compte de triangles par pièce. Captures face, 3/4, dos, profil, et gros plan de la face et des cheveux, à côté de la référence Gojo au même angle. ✋
5. **Accessoires séparés** (`Acc_<Nom>` dans la fiche, ex. un sabre dégainé) : objet séparé, parenté en rigide à l'os de la pièce qui le porte, avec la mention visible ou caché par défaut.

## 3. Export et assemblage (Blender → Studio)
1. Exporte `assets/persos/<Id>/corps_<Id>.fbx` : les 15 pièces + HumanoidRootPart (boîte invisible) + les `Acc_<Nom>`, SANS armature (le parentage aux os fait coucher les pièces à l'import), transformations appliquées, origine de chaque objet au centre de sa boîte R15, `axis_forward='-Z', axis_up='Y'`, `apply_scale_options='FBX_SCALE_ALL'`, textures intégrées. Vérifie le FBX en le réimportant dans une scène temporaire, puis supprime la scène et le dossier `.fbm`.
2. Je l'importe (Fichier → Importer). Dans Studio, via le MCP :
   - Vérifie chaque MeshPart (nom, taille, orientation : la face de la tête regarde vers -Z) en comparant à `r15_bloc.json`. Corrige une rotation en la calculant, jamais à l'œil.
   - Place chaque pièce à sa CFrame de `r15_bloc.json` (relative à HumanoidRootPart), crée les 15 Motor6D R15 standard avec leurs C0/C1 (Root, Waist, Neck, LeftShoulder, LeftElbow, LeftWrist, RightShoulder, RightElbow, RightWrist, LeftHip, LeftKnee, LeftAnkle, RightHip, RightKnee, RightAnkle) et vérifie `Part0.CFrame * C0 * C1:Inverse() == Part1.CFrame`.
   - Accessoires séparés : soudés à leur pièce (Weld, C0 calculé), attribut booléen `VisibleParDefaut`, Transparency 1 s'ils sont cachés par défaut.
   - Textures : chaque MeshPart a une TextureID ; sinon dis-moi quelles images importer.
   - Compare une capture Studio (face, 3/4) à la capture Blender du même angle. ✋

## 4. Animations (calculées par script, construites dans Studio)
Trois animations par perso, décrites dans la fiche : `<Id>_Idle` (en boucle), `<Id>_Action` (démonstration de pouvoir, une fois), `<Id>_Signature` (geste typique, une fois). Ce sont des animations de VITRINE, jouées sur la case du perso : pas des animations de combat.
- Sur place : `LowerTorso` ne s'éloigne jamais de plus de 0,5 stud de sa position de départ (les bras peuvent avancer en translation pour un effet élastique). VFX dans un rayon de 5 studs autour du perso.
- Raccords : Action et Signature commencent et finissent exactement sur l'image 0 de l'Idle (« pose neutre »), sauf si la fiche dit autre chose (ex. Zoro : l'Action finit sabres en main, la Signature les range) ; vérifie alors que les images de raccord sont identiques.
- Source de vérité : `assets/persos/<Id>/anims/<Id>_<Nom>.json`, généré par un script Python (`anims_<Id>.py`) : clés à 30 images/s, une rotation par articulation R15 dans les axes de `assets/persos/_mannequin/axes_r15.json` (calibrés par le prompt M), translation seulement sur Root (et sur un bras si la fiche le demande), easing par clé, marqueurs.
- Articulations : coude et genou ne plient que dans un sens (0 à 150°), poignets et chevilles ±30°, tête ±25°. Pieds plantés et mains posées sur un point (sol, poignée, menton, poche) : IK à deux os calculée dans le script. Vérifie sur toutes les images qu'aucun membre ne traverse la tenue, les cheveux ou un accessoire (calcul de collision grossier par boîtes, puis captures).
- Aperçu dans Blender d'abord (le JSON appliqué à l'armature de `<Id>.blend`), 4 images clés de face et de 3/4. ✋ après CHAQUE animation.
- Dans Studio : une `KeyframeSequence` par animation à partir du JSON (Pose hiérarchiques selon l'arbre des Motor6D : HumanoidRootPart → LowerTorso → UpperTorso → …). Idle : Loop = true, Priority = Idle. Action et Signature : Loop = false, Priority = Action.
- Marqueurs (JSON puis `KeyframeMarker` sur le Keyframe le plus proche, ajouté si besoin) : Name = `Montrer`, `Cacher` ou `VFX` ; Value = `Acc_<Nom>` ou `<NomEffet>`.
- Publication : range les KeyframeSequence dans l'entrée `ServerStorage.RBX_ANIMSAVES.<Id>` créée quand j'ouvre l'éditeur d'animation sur le modèle (demande-le-moi d'abord). Je les publie et je te donne les 3 IDs. Attributs texte sur le modèle : `AnimationIdle`, `AnimationAction`, `AnimationSignature`. Vérifie chaque ID avec `KeyframeSequenceProvider:GetKeyframeSequenceAsync`.

## 5. VFX (Studio)
- Dossier `VFX` dans le modèle, un sous-dossier par effet nommé comme dans la fiche. Émetteurs sur des Attachments des pièces ou des accessoires (ex. lame d'un sabre). Tout est désactivé par défaut.
- Attributs du sous-dossier : `Mode` = "Burst" (Emit(`Quantite`)) ou "Duree" (activé pendant `Duree` secondes). Un effet « de X à Y » : marqueurs `VFX <Nom>` et `VFX <Nom>_Fin`, ou Mode Duree.
- Style anime, net et lumineux, couleurs du perso, effets courts (0,2 à 1 s), 60 particules maximum à l'écran par effet. Textures : celles de Roblox, ou des images Pillow dans `assets/persos/<Id>/vfx/` (je les importerai avec le reste).
- Prévisualise chaque effet à l'image de son marqueur (Emit en mode édition), capture.
- Ne crée aucun script de jeu : la lecture des marqueurs en jeu sera codée à part, dans `src/`.

## 6. Finition dans Studio
- Un `AnimationController` avec son `Animator` à la racine du modèle (c'est ce que le code du jeu utilise). Pas de Humanoid.
- HumanoidRootPart : Anchored = true, Transparency = 1, PrimaryPart du modèle. Toutes les pièces : CanCollide, CanQuery, CanTouch = false, Material = SmoothPlastic, CastShadow = true (sauf HumanoidRootPart) ; les autres pièces Anchored = false.
- Range le modèle dans `ReplicatedStorage.ModelesPersonnages.<Id>`, supprime les copies de travail, et rappelle-moi d'enregistrer la place.

## 7. Bilan
5 lignes max : ce qui est fait, triangles, IDs des animations, ce qui reste à faire de mon côté.

## 8. Pièges connus
- Caméra de Studio : `screen_capture` avec `camera_position` peut laisser la caméra en `Scriptable` si l'appel expire. Après chaque capture, remets `workspace.CurrentCamera.CameraType` à `Fixed` si besoin.
- `list_roblox_studios` donne le `studio_id`, qui change à chaque relance de Studio.
- L'importeur de Studio couche de 90° les meshes parentés à un os : c'est pour ça qu'on exporte sans armature.
- MCP Blender : crée un calque de bmesh AVANT la géométrie (sinon les références de faces sont invalidées) ; faces de révolution dans l'ordre (bas k, bas k+1, haut k+1, haut k) pour des normales vers l'extérieur.
