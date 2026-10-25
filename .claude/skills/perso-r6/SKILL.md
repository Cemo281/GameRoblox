---
name: perso-r6
description: Crée un personnage R6 low-poly dans Blender via le MCP Blender à partir d'une fiche, avec son animation idle en boucle, l'exporte en FBX puis vérifie et finalise l'import dans Roblox Studio via le MCP Roblox_Studio. Usage - /perso-r6 <fiche du personnage>
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
- Les accessoires (chapeau, cheveux, arme, instrument, livre…) sont FUSIONNÉS dans la pièce qui les porte (épée en main droite → dans `Right Arm`, chapeau → dans `Head`). Pas d'objet en plus.
- **Objet tenu en main** : un bras R6 n'a ni coude ni main séparée, la main est le bas du bras. L'objet doit TRAVERSER le poing (bas du bras, z ≈ 2,0–2,5) avec un angle franc par rapport au bras (≈ 65°), avec un pouce replié par-dessus. Jamais parallèle au bras. Une pose « objet posé contre l'épaule » est impossible sans coude (l'objet longerait le bras) : propose autre chose (bâton planté au sol, arme tenue devant…) et dis-le-moi.
- Transformations appliquées (Ctrl+A) sur les meshes, origine de chaque mesh au pivot de sa pièce.

## 3. Étapes
1. **Fiche** : reformule la fiche en 10 lignes max (silhouette, palette en hex, accessoires et pièce qui les porte, déroulé de l'animation). Signale tout de suite ce qui est impossible en R6 (voir « Objet tenu en main »). ✋
2. **Blockout** : formes grossières des 7 pièces + accessoires, sans couleur. Captures face, profil, 3/4.
3. **Modèle final** : détails, palette, UV, visage, cheveux. Vérifie le budget de triangles (affiche le compte par pièce). Captures face, 3/4, dos, profil, et un gros plan du visage. Simule aussi la pose principale de l'objet tenu (rotation temporaire de l'objet bras, puis remise à zéro). Sauvegarde `assets/blender/<Id>/<Id>.blend`. ✋
4. **Rig** : armature + parentage rigide. Teste en tournant chaque os de 45° (capture), puis remets tout à zéro.
5. **Animation** : action `<Id>_Idle`, 30 images/s, durée de la fiche. Clés sur les os en rotation (quaternions, signes continus d'une clé à l'autre) ; translation seulement sur `Torso` (petit rebond) ou si la fiche le demande. Jamais d'échelle (Roblox l'ignore). Première et dernière image identiques pour une boucle parfaite (vérifie toutes les courbes). Interpolation Bézier avec easing (auto clamped), petits décalages entre les membres (overlap).
   - **Pieds plantés** : à chaque clé, recalcule la rotation des jambes pour que le bout de chaque jambe vise son point au sol (différence de rotation entre la direction actuelle et la direction hanche → pied, ramenée dans le repère de l'os). Puis mesure sur toutes les images le point le plus bas des jambes, et remonte le torse aux clés où les pieds passent sous le sol.
   - **Objet planté au sol** (bâton…) : même calcul sur le bras qui le tient, avec un point fixe au sol. La longueur est fixe : l'objet décolle un peu quand le torse monte, garde ce rebond petit.
   - **Cheveux fusionnés à la tête** : limite les rotations de la tête à ≈ 10° (tourner, pencher) et vérifie qu'aucun sommet de cheveux n'entre dans la boîte du torse sur toute l'animation.
   - Pour trouver une pose (ex. « bourse devant le visage »), cherche les angles par calcul (grille de valeurs X/Z, distance au point visé) plutôt qu'à l'œil.
   - Captures à 4 moments clés, de face et de 3/4. ✋
6. **Export** (sélectionner l'armature + les 7 meshes ; pour le modèle, retirer l'action et remettre le rig en pose de repos, puis la remettre) :
   - `assets/blender/<Id>/<Id>.fbx` : `bpy.ops.export_scene.fbx(use_selection=True, object_types={'ARMATURE','MESH'}, apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', axis_forward='-Z', axis_up='Y', add_leaf_bones=False, mesh_smooth_type='FACE', path_mode='COPY', embed_textures=True, bake_anim=False)`
   - `assets/blender/<Id>/<Id>_Idle.fbx` : mêmes options mais `bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True, bake_anim_simplify_factor=0.0`, avec l'action `<Id>_Idle` active (archive ; l'animation passe par l'étape 9).
   - Enregistre aussi `Palette_<Id>.png` dans le même dossier.
   - Vérifie en réimportant chaque FBX dans une scène temporaire (os, meshes, triangles, texture, hauteur), puis supprime la scène ET les dossiers `<Id>.fbm` / `<Id>_Idle.fbm` que la réimport crée à côté des FBX.
7. **Import (c'est moi qui clique)** : explique-moi en 3 lignes : Studio → **Fichier → Importer** (Ctrl+M) ou Accueil → **Importer** → `<Id>.fbx` → clic sur sa ligne dans la file d'attente d'importation (en bas) pour l'aperçu → unité « Stud » / rig « R6 » si proposés → bouton **Importer**. Pas de bouton « Import 3D » dans l'onglet Avatar. Attends que je dise « importé ».
8. **Vérification et finition dans Studio (MCP Roblox_Studio, en Luau)** :
   - Récupère le `studio_id` avec `list_roblox_studios` (il change à chaque relance de Studio).
   - Trouve le modèle importé (`Workspace.<Id>`). Liste ses descendants : l'importeur ajoute en général une Part `RootPart`, un dossier `InitialPoses`, un `AnimationController`, et des Motor6D nommés `<Pièce>Motor6D` (dont un HumanoidRootPart→HumanoidRootPart).
   - **Pièces couchées** : l'importeur couche chaque mesh parenté à un os de 90° (tailles avec la hauteur sur Z, jambes vers l'arrière). Contrôle : la taille du Torso doit être ≈ 2×2×1 (X×Y×Z) une fois en place. Correction, dans cet ordre :
     1. ancre toutes les pièces et **détruis tous les Motor6D d'abord** (sinon chaque pièce déplacée entraîne tout l'assemblage) ;
     2. si l'assemblage a bougé, ramène-le avec la pose d'origine (HumanoidRootPart sans rotation) ;
     3. tourne chaque pièce de **+90° autour de l'axe X du monde, autour de SON articulation**. Correspondance Blender → Roblox autour du centre du torse : (x, y, z) → (-x, z - 3, y). Vérifie que le centre de chaque pièce retombe là où il est dans Blender, et regarde de face (visage visible, rayures en haut du torse) ;
     4. remplace HumanoidRootPart par une `Part` 2×2×1 sans rotation au centre du torse ; supprime `RootPart` et `InitialPoses`.
   - **Motor6D** : crée les 6 Motor6D R6 standard (`RootJoint` dans HumanoidRootPart : HumanoidRootPart→Torso ; dans Torso : `Neck`, `Left Shoulder`, `Right Shoulder`, `Left Hip`, `Right Hip`). Repère R = `CFrame.new(HumanoidRootPart.Position)` ; articulation J = R * repère standard R6 (RootJoint `CFrame.new(0,0,0, -1,0,0, 0,0,1, 0,1,0)`, Neck `(0,1,0, -1,0,0, 0,0,1, 0,1,0)`, Right Shoulder `(1,0.5,0, 0,0,1, 0,1,0, -1,0,0)`, Left Shoulder `(-1,0.5,0, 0,0,-1, 0,1,0, 1,0,0)`, Right Hip `(1,-1,0, 0,0,1, 0,1,0, -1,0,0)`, Left Hip `(-1,-1,0, 0,0,-1, 0,1,0, 1,0,0)`) ; `C0 = Part0.CFrame:Inverse() * J`, `C1 = Part1.CFrame:Inverse() * J`. Vérifie `Part0.CFrame * C0 * C1:Inverse() == Part1.CFrame`.
   - Hauteur totale entre 3,5 et 6,5 studs, sinon `Model:ScaleTo()` pour corriger.
   - Orientation : `HumanoidRootPart.CFrame:PointToObjectSpace(model["Right Arm"].Position).X` doit être > 0 (le perso regarde vers l'avant). Sinon, corrige dans Blender (rotation 180°) et réexporte.
   - Textures : chaque MeshPart a une TextureID non vide, sinon dis-moi d'importer `Palette_<Id>.png`.
   - Réglages : `PrimaryPart` = HumanoidRootPart ; HumanoidRootPart Anchored = true, Transparency = 1 ; toutes les pièces CanCollide = false, CanQuery = false, CanTouch = false, CastShadow = true (sauf HumanoidRootPart), Material = SmoothPlastic ; les autres pièces Anchored = false.
   - Ajoute un `AnimationController` avec un `Animator` (plus léger qu'un Humanoid pour des dizaines de persos posés). Si l'éditeur d'animation refuse le rig, ajoute plutôt un `Humanoid` (RigType R6, DisplayDistanceType None).
   - Range le modèle dans `ReplicatedStorage.ModelesPersonnages` (crée le dossier s'il n'existe pas), nommé `<Id>`.
9. **Animation : KeyframeSequence générée (voie principale)**. L'import FBX de l'éditeur d'animation passe par le même importeur (orientation des os fausse) : ne l'utilise pas.
   - Dans Blender : mémorise la matrice monde de chaque pièce en pose de repos (action retirée), puis pour une image sur deux : `D = matrice_monde(image) @ matrice_repos⁻¹`, translation ramenée au centre du torse (`R·c + t - c`, c = (0,0,3)), puis passage dans le repère Roblox avec `A = ((-1,0,0),(0,0,1),(0,1,0))` : rotation `A·R·Aᵀ` en quaternion, translation `A·t`. Écris le tout en JSON dans `assets/blender/<Id>/<Id>_Idle_roblox.json`.
   - Dans Studio : pièce animée = `CFrame(D) * repos` (repos relatif à HumanoidRootPart) ; pour chaque Motor6D, `Pose.CFrame = C0⁻¹ · Part0_animée⁻¹ · Part1_animée · C1` (vérifie l'aller-retour). `KeyframeSequence` `<Id>_Idle` : Loop = true, Priority = Idle, poses en Linear, hiérarchie HumanoidRootPart (Weight 0) → Torso → les 5 autres.
   - Prévisualise 2 ou 3 images sur des clones ancrés posés au sol (lancer de rayon), capture, puis supprime les clones.
   - Mets une copie de travail du modèle dans le Workspace. Demande-moi d'abord d'ouvrir l'éditeur d'animation dessus : il crée sa propre entrée `ServerStorage.RBX_ANIMSAVES.<Id>` (ObjectValue, avec « Automatic Save »). Range la `KeyframeSequence` DANS cette entrée-là, sinon « Charger » ne la propose pas.
   - **C'est moi qui clique** : explique-moi : sélectionner `Workspace.<Id>` → onglet Avatar → **Animation…** → « … » → **Charger** → `<Id>_Idle` → Lecture pour vérifier → « … » → **Publier sur Roblox** → me donner l'ID.
   - Avec l'ID : vérifie qu'il se charge (`KeyframeSequenceProvider:GetKeyframeSequenceAsync`), ajoute l'attribut texte `AnimationIdle = "rbxassetid://<ID>"` sur le modèle de ReplicatedStorage, supprime la copie de travail, et rappelle-moi d'enregistrer la place.
10. **Bilan** : 5 lignes max : ce qui est fait, triangles, durée de l'anim, ce qui reste à faire de mon côté.

## 4. Pièges connus
- **Caméra de Studio** : `screen_capture` avec `camera_position` déplace la caméra ; si l'appel expire, elle reste en `Scriptable` (plus de contrôle souris, et c'est enregistré avec la place). Après chaque capture, vérifie `workspace.CurrentCamera.CameraType` et remets `Fixed` si besoin ; demande-moi d'enregistrer la place ensuite. Préfère les captures Blender (`look`) quand c'est possible.
- Le MCP Blender : un calque `int` créé sur un bmesh invalide les références de faces déjà créées ; crée le calque de couleur AVANT la géométrie.
- Faces de révolution (tête, calotte) : ordre des sommets (bas k, bas k+1, haut k+1, haut k) pour des normales vers l'extérieur ; les surfaces ouvertes ne sont pas corrigées par le recalcul des normales.
