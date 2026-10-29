---
name: perso-roblox
description: Crée un personnage façon avatar Roblox (rig R15 en blocs dans Studio, vêtements Shirt/Pants et face peints en 2D, accessoires 3D modélisés dans Blender) avec ses 3 animations de vitrine et leurs VFX, via les MCP Roblox_Studio et Blender. Usage - /perso-roblox <fiche du personnage>
argument-hint: <fiche du personnage>
---

# Personnage façon avatar Roblox : Studio + Blender

Fiche du personnage : $ARGUMENTS

Si la fiche est vide, liste les `Id` de `src/shared/Personnages.luau` avec leur rareté et demande-moi la fiche.
Avant tout, vérifie que le mannequin existe (`assets/persos/_mannequin/` et `ServerStorage.Gabarits.MannequinR15`, créés par le « prompt M »). Sinon, arrête-toi et dis-le-moi.

Références du mannequin (à lire avant l'étape concernée) :
- `r15_bloc.json` : pièces, Motor6D (C0 / C1), Attachments, `blocs_visibles` (boîtes réelles des maillages R15, d'une articulation à la suivante), tête classique.
- `zones_vetements.json` : zones des modèles Shirt / Pants, sens de lecture de chaque face, lignes de chaque pièce, empilement, parties cachées, et la section `face` (Decal de la tête).
- `axes_r15.json` : sens de chaque mouvement par articulation, conversion Blender → Studio, limites.
- `mannequin.blend` (reconstruit par `construire_mannequin.py`) : mêmes UV que Studio, images nommées `Shirt`, `Pants`, `Face`, armature rigide `Rig_R15`, caméra `Camera_Studio` (fonction `camera_studio` du script pour reproduire une capture Studio).

## 0. Règles de travail
- Studio est la base : corps, vêtements, face, animations, VFX. Blender sert seulement aux accessoires 3D (cheveux, couvre-chefs, armes, manteaux, objets tenus) et à l'aperçu des vêtements sur le mannequin.
- Petites étapes (un appel MCP = une étape), jamais de script géant. Après chaque étape visible : capture, auto-critique honnête (comparaison avec les images de référence), correction.
- Points de contrôle ✋ : arrête-toi, montre le résultat, attends mon « ok ».
- Les noms One Piece sont des noms de travail : aucun logo, texte ou emblème officiel. Pas de cigarette, d'alcool ni de sang (règles Roblox).
- Ne modifie jamais `src/` ni `default.project.json`. Ne committe rien sans me demander.
- Fichiers dans `assets/persos/<Id>/`. Tiens à jour une section `Personnage <Id>` dans `docs/wiki/TODO.md`.
- Images (vêtements, face, textures de VFX) : tu les envoies toi-même avec `upload_image` du MCP Studio. L'outil ne lit que des URL : copie les PNG dans un dossier dédié du scratchpad, sers-le avec `python -I -m http.server <port> --bind 127.0.0.1 --directory <dossier>` en arrière-plan, envoie `http://localhost:<port>/<fichier>.png`, puis arrête le serveur.
- Ce que JE fais à la main (tu me l'expliques en 3 lignes max à chaque fois) : importer les FBX des accessoires (Fichier → Importer), publier les animations, enregistrer la place. Regroupe ces actions pour me faire cliquer le moins souvent possible.
- Si une info manque dans la fiche, choisis la solution la plus simple et dis-moi laquelle.

## 1. Style (référence : `assets/references/style-roblox-zoro.png`)
- Lis cette image et `assets/references/<Id>.png` s'il existe (prioritaire pour la tenue et les couleurs) avant l'étape 1.
- Corps : rig R15 en blocs de Roblox, sans modification. Couleur de peau via BodyColors.
- Les détails sont PEINTS dans les vêtements 2D, comme les vêtements Roblox de qualité : aplats + ombrages doux, contours sombres de 2 à 3 px, muscles dessinés (pectoraux, abdominaux, bras), plis de tissu, coutures en pointillés, boutons, motifs, cicatrices. Les détails qui passent d'une face à l'autre se raccordent. Pas de rendu photo, pas de bruit.
- Face : dessin anime sur fond transparent, lisible de loin : contour noir épais, iris en dégradé, reflets, ombre de paupière, sourcils expressifs, bouche, cicatrices et marques du perso.
- Volume = accessoires 3D, en couches, comme les accessoires Roblox : mèches de cheveux en volume, couvre-chefs, manteaux, écharpes, ceintures, armes. Chacun a sa petite texture peinte (plis, ombres, coutures), formes nettes et un peu cubiques pour aller avec le corps.
- Budget : 4 000 triangles maximum par accessoire, 12 000 pour tout le perso.

## 2. Corps et vêtements (Studio + scripts Python)
1. Corps : copie `ServerStorage.Gabarits.MannequinR15` (créé par le prompt M) dans le Workspace, nommé `<Id>`. Règle les BodyColors selon la fiche.
2. Peins trois images avec Python + Pillow (`uv run --with pillow assets/persos/<Id>/peindre_<Id>.py`), en gardant le script pour pouvoir retoucher un détail sans tout refaire :
   - `shirt_<Id>.png` et `pants_<Id>.png` (585×559), en respectant EXACTEMENT les zones de `assets/persos/_mannequin/zones_vetements.json` (calibrées par le prompt M) : rectangle, sens de lecture et lignes de chaque pièce (bras et jambes : 0–64 haut, 64–112 bas, 112–128 main ou pied ; torse : 0–96 UpperTorso, 96–128 LowerTorso). La peau visible (torse nu, bras nus) est peinte aussi, avec ses muscles et ses ombres.
   - Empilement : le Shirt couvre le torse ENTIER (UpperTorso et LowerTorso) et les bras ; le Pants couvre aussi le torse entier et les jambes ; le Shirt passe PAR-DESSUS le Pants. Pour qu'un pantalon (ceinture, bassin) se voie, laisse la zone torse du Shirt transparente sur les lignes 96 à 128 (et plus haut si le haut du pantalon remonte).
   - Parties cachées au repos mais visibles en mouvement (voir `parties_cachees`) : haut des cuisses (lignes 0–16), haut de l'avant-bras et du mollet (lignes 56–64, visibles quand le coude ou le genou plie) : continue les motifs dessus.
   - `face_<Id>.png` (512×512) : fond TRANSPARENT obligatoire (Studio étale le pixel du coin haut-gauche sur les côtés, le dos et le dessus de la tête). Zone utile : x de 64 à 448 (les colonnes 64–96 et 416–448 sont très écrasées sur l'arrondi), toute la hauteur ; détail de la projection dans `zones_vetements.json` → `face`.
3. Aperçu dans Blender, AVANT tout envoi dans Studio : copie `assets/persos/_mannequin/mannequin.blend` dans `assets/persos/<Id>/<Id>_apercu.blend` et remplace les fichiers des images `Shirt`, `Pants` et `Face` (même nom, `filepath` vers tes PNG, puis `reload()`). La couleur de peau est le nœud `Peau` des matériaux `Mat_Torse`, `Mat_Bras`, `Mat_Jambes` et la couleur de base de `Mat_Tete`. Captures face, dos, profil, 3/4 et gros plan de la face. ✋
4. Quand c'est validé : envoie les trois images (`upload_image`). Ajoute au modèle un `Shirt` et un `Pants` (renomme-les : `Instance.new` les nomme `Clothing`) et remplace la texture du Decal `face` de la tête. Capture dans Studio avec les mêmes caméras que l'aperçu (`camera_studio`) pour vérifier que tout tombe au même endroit.

## 3. Accessoires (Blender → Studio)
1. Modélise chaque accessoire dans `<Id>_apercu.blend`, posé sur le mannequin (le mannequin donne l'échelle exacte : 1 unité = 1 stud). Chaque accessoire = un objet séparé nommé `Acc_<Nom>` (ou `<Nom>` s'il ne bouge jamais), avec UV et une texture peinte avec Pillow (`acc_<Id>.png`, 1024 max, une zone par accessoire).
2. Pour chaque accessoire, choisis l'attachment R15 du corps qui le porte (HairAttachment, HatAttachment, FaceFrontAttachment, NeckAttachment, BodyBackAttachment, WaistCenterAttachment, WaistBackAttachment, WaistFrontAttachment, LeftGripAttachment, RightGripAttachment, …) et calcule le décalage de l'accessoire par rapport à cet attachment depuis sa position sur le mannequin. Écris tout dans `assets/persos/<Id>/accessoires.json` (nom, attachment, décalage, visible par défaut ou non).
3. Captures du perso complet dans Blender (face, 3/4, dos, profil). ✋
4. Export : un FBX par accessoire (`acc_<Nom>.fbx`, sans armature, transformations appliquées, origine au point d'attache, `axis_forward='-Z', axis_up='Y'`, texture intégrée). Vérifie chaque FBX en le réimportant dans une scène temporaire, puis supprime la scène et les dossiers `.fbm` créés.
5. Je les importe tous d'un coup dans Studio. Tu crées pour chacun un `Accessory` dont le `Handle` est le MeshPart importé, avec un Attachment du même nom que celui du corps et le décalage du JSON, puis `Humanoid:AddAccessory()`. Vérifie que l'orientation est la bonne (comparaison avec l'aperçu Blender) ; si l'importeur a tourné un mesh, corrige la rotation dans l'Attachment, pas à l'œil. Handles : CanCollide, CanQuery, CanTouch = false, Massless = true.
6. Un accessoire qui doit suivre un membre précis (manche, gantelet, genouillère, botte) : soude son Handle directement à la pièce (Weld, C0 calculé depuis l'aperçu) au lieu de `AddAccessory`, car certains attachments existent en double (torse et bras).
7. Accessoires qui apparaissent et disparaissent (`Acc_<Nom>` avec « caché par défaut » dans la fiche) : attribut booléen `VisibleParDefaut` sur l'Accessory, Transparency du Handle = 1 si caché.

## 4. Animations (calculées par script, construites dans Studio)
Trois animations par perso, décrites dans la fiche : `<Id>_Idle` (en boucle), `<Id>_Action` (démonstration de pouvoir, une fois), `<Id>_Signature` (geste typique, une fois). Ce sont des animations de VITRINE, jouées sur la case du perso : ce ne sont pas des animations de combat.
- Sur place : `LowerTorso` ne s'éloigne jamais de plus de 0,5 stud de sa position de départ (les bras peuvent avancer en translation pour un effet élastique). VFX dans un rayon de 5 studs autour du perso.
- Raccords : Action et Signature commencent et finissent exactement sur l'image 0 de l'Idle (« pose neutre »), sauf si la fiche dit autre chose (ex. Zoro : l'Action finit sabres en main, la Signature les range) ; vérifie alors que les images de raccord sont identiques.
- Source de vérité : `assets/persos/<Id>/anims/<Id>_<Nom>.json`, généré par un script Python (`anims_<Id>.py`) : clés à 30 images/s, une rotation par articulation R15 (Root, Waist, Neck, épaules, coudes, poignets, hanches, genoux, chevilles) exprimée comme le `Motor6D.Transform` de Studio (axes de `assets/persos/_mannequin/axes_r15.json`, calibrés par le prompt M), translation seulement sur Root, easing par clé, et les marqueurs. Pour l'aperçu Blender, convertis avec la formule de `conversion_blender_vers_studio` (B · R · B, B = diag(-1,-1,1) os vers le bas, diag(-1,1,-1) os vers le haut).
- Articulations : coude et genou ne plient que dans un sens (0 à 150°) : coude = Studio X+, genou = Studio X− ; poignets et chevilles ±30°, tête ±25°. Les épaules pivotent 0,5 stud à l'intérieur du centre du bras : une rotation Y fait aussi avancer ou reculer le bras. Pieds plantés et mains posées sur un point (sol, poignée, menton, poche) : IK à deux os calculée dans le script, pas à l'œil. Accessoires : vérifie sur toutes les images qu'un bras ou une jambe ne traverse pas un manteau, un fourreau ou les cheveux.
- Dans Studio : construis une `KeyframeSequence` par animation à partir du JSON (Pose hiérarchiques selon l'arbre des Motor6D : HumanoidRootPart → LowerTorso → UpperTorso → …). Idle : Loop = true, Priority = Idle. Action et Signature : Loop = false, Priority = Action. Poses en Cubic ou Linear selon l'easing.
- Marqueurs (dans le JSON puis en `KeyframeMarker` sur le Keyframe le plus proche, ajouté si besoin) : Name = `Montrer`, `Cacher` ou `VFX` ; Value = `Acc_<Nom>` ou `<NomEffet>`.
- Prévisualisation : pose des clones aux images clés, captures, puis supprime les clones. En mode édition, `Motor6D.Transform` ne déplace rien et changer la CFrame d'une pièce reliée déplace tout l'assemblage : sur chaque clone, ancre toutes les pièces, mets les Motor6D en `Enabled = false`, puis calcule chaque pièce depuis le HumanoidRootPart (`Part1.CFrame = Part0.CFrame * C0 * Transform * C1:Inverse()`). Montre aussi 4 images clés dans l'aperçu Blender (les mêmes JSON appliqués au mannequin). ✋ après CHAQUE animation.
- Publication : range les KeyframeSequence dans l'entrée `ServerStorage.RBX_ANIMSAVES.<Id>` créée quand j'ouvre l'éditeur d'animation sur le modèle (demande-le-moi d'abord). Je les charge et je les publie, je te donne les 3 IDs. Attributs texte sur le modèle : `AnimationIdle`, `AnimationAction`, `AnimationSignature`. Vérifie chaque ID avec `KeyframeSequenceProvider:GetKeyframeSequenceAsync`.

## 5. VFX (Studio)
- Dossier `VFX` dans le modèle, un sous-dossier par effet nommé comme dans la fiche. Émetteurs sur des Attachments des pièces ou des Handles (ex. lame d'un sabre). Tout est désactivé par défaut.
- Attributs du sous-dossier : `Mode` = "Burst" (Emit(`Quantite`)) ou "Duree" (activé pendant `Duree` secondes). Un effet « de X à Y » : marqueurs `VFX <Nom>` et `VFX <Nom>_Fin`, ou Mode Duree.
- Style anime, net et lumineux, couleurs du perso, effets courts (0,2 à 1 s), 60 particules maximum à l'écran par effet. Textures : celles de Roblox, ou des images Pillow dans `assets/persos/<Id>/vfx/` (je les importerai avec le reste).
- Prévisualise chaque effet à l'image de son marqueur (Emit en mode édition), capture.
- Ne crée aucun script de jeu : la lecture des marqueurs en jeu sera codée à part, dans `src/`.

## 6. Finition dans Studio
- Humanoid : DisplayDistanceType = None, HealthDisplayType = AlwaysOff, pas de nom affiché. Supprime le script `Animate` s'il existe.
- PAS d'`AnimationController` dans le modèle : un Humanoid et un AnimationController ensemble se bloquent (aucune animation ne joue, ni en jeu ni dans l'éditeur d'animation ; vérifié sur `zoro` le 2026-10-29). Le Humanoid (vêtements, accessoires) porte l'`Animator`. Le code du jeu doit chercher l'Animator dans le Humanoid (ou dans un AnimationController pour les persos sans Humanoid, comme `nami`). Vérifie en mode Play qu'une animation jouée sur `Humanoid.Animator` anime bien le corps (la position d'une main change).
- HumanoidRootPart : Anchored = true, Transparency = 1, PrimaryPart du modèle. Toutes les pièces et Handles : CanCollide, CanQuery, CanTouch = false ; les autres pièces Anchored = false.
- Range le modèle dans `ReplicatedStorage.ModelesPersonnages.<Id>`, supprime la copie de travail, et rappelle-moi d'enregistrer la place.

## 7. Bilan
5 lignes max : ce qui est fait, triangles, IDs (images, animations), ce qui reste à faire de mon côté.

## 8. Pièges connus
- Caméra de Studio : `screen_capture` avec `camera_position` laisse souvent la caméra en `Scriptable` (même sans expiration, et parfois APRÈS une remise à `Fixed` faite juste derrière). Remets `workspace.CurrentCamera.CameraType` à `Fixed` après chaque série de captures, puis revérifie-le au moment de rendre la main (avant chaque ✋ ou action manuelle demandée).
- Captures Studio : la vue 3D est noire si Studio n'est pas au premier plan (mets-le devant avec `SetForegroundWindow` en PowerShell avant de capturer). Une capture à la fois : deux `screen_capture` en parallèle se gênent (expiration, image d'une autre vue).
- Couleurs : sur un modèle avec Humanoid, le `BodyColors` réapplique ses couleurs par membre et l'apparence des MeshParts R15 reste en cache : pour colorer une pièce à l'écran (pièce tournée, repère), utilise un `Highlight` (31 maximum à l'écran), pas `Color`.
- Une `HumanoidDescription` vide donne un corps noir et une tête dynamique : passe toujours par `ServerStorage.Gabarits.MannequinR15`, jamais par `CreateHumanoidModelFromDescription`.
- Lire un maillage Roblox (sommets, faces, UV) : `AssetService:CreateEditableMeshAsync(Content.fromUri(meshPart.MeshId))`, coordonnées à multiplier par `Size / MeshSize`.
- Import FBX depuis Blender : les MeshParts arrivent 100 fois trop grands (Blender en mètres, FBX en cm, Studio lit 1 cm = 1 stud) et éparpillés sur la carte, sans rotation (repère Roblox = (-xB, zB, yB), vérifié avec EditableMesh). Corriger par `Size = MeshSize / 100`, puis placer le Handle depuis `accessoires.json`.
- Le gabarit `ServerStorage.Gabarits.MannequinR15` contient un AnimationController : sur la copie du perso, supprime-le et mets un `Animator` dans le Humanoid (voir section 6).
- `Humanoid:AddAccessory()` en mode édition ne crée pas de soudure, et un `Weld` ajouté à la main peut disparaître en mode édition. Ce n'est pas grave : au lancement du jeu, le Humanoid relie chaque Handle par une `RigidConstraint` (`AccessoryRigidConstraint`) construite à partir des deux attachments de même nom. Ce qui compte, c'est l'Attachment du Handle (nom identique à celui du corps, CFrame juste). Vérification : en mode Play, distance Handle / pièce du corps stable.
- Jamais deux marqueurs de même nom sur la même image (ex. deux `Cacher` à l'image 45) : l'éditeur d'animation n'en garde qu'un, à la publication et même en réécrivant la séquence locale quand on la charge. Décaler le second d'une image. Après publication, comparer le nombre de marqueurs de chaque ID (`GetKeyframeSequenceAsync`) au JSON.
- Vérifier les marqueurs en mode Play : `KeyframeSequenceProvider:RegisterKeyframeSequence` + `Humanoid.Animator:LoadAnimation`, puis `GetMarkerReachedSignal("Montrer" / "Cacher" / "VFX")` qui change la transparence des Handles (gestionnaire temporaire, rien dans `src/`).
- `list_roblox_studios` donne le `studio_id`, qui change à chaque relance de Studio.
- MCP Blender : crée un calque de bmesh AVANT la géométrie (sinon les références de faces sont invalidées) ; faces de révolution dans l'ordre (bas k, bas k+1, haut k+1, haut k) pour des normales vers l'extérieur.
