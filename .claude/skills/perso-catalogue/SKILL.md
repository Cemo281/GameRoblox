---
name: perso-catalogue
description: Crée un personnage à partir d'un avatar Roblox classique habillé avec des articles du catalogue Roblox (cheveux, vêtements, accessoires), assemblé dans Studio via le MCP Roblox_Studio, avec ses 3 animations de vitrine et leurs VFX. Usage - /perso-catalogue <fiche du personnage>
argument-hint: <fiche du personnage>
---

# Personnage à partir du catalogue Roblox

Fiche du personnage : $ARGUMENTS

Si la fiche est vide, liste les `Id` de `src/shared/Personnages.luau` avec leur rareté et demande-moi la fiche.
Pour les animations, il faut `assets/persos/_rig/axes_r15.json` (créé par le « prompt C »). S'il manque, dis-le-moi avant l'étape 5.

## 0. Règles de travail
- Base : un avatar Roblox R15 classique, habillé avec des articles du catalogue Roblox (Marketplace). Tout se passe dans Studio via le MCP Roblox_Studio. Blender ne sert qu'en dernier recours (étape 4).
- Petites étapes, captures après chaque étape visible, auto-critique honnête en comparant à `assets/references/<Id>.png` (même angle).
- Points de contrôle ✋ : arrête-toi, montre le résultat, attends mon « ok ». Quand je demande une modif, fais seulement celle-là, puis montre un avant/après.
- Pas de cigarette, d'alcool, de sang ni de tenue suggestive (règles Roblox).
- Ne modifie jamais `src/` ni `default.project.json`. Ne committe rien sans me demander.
- Fichiers dans `assets/persos/<Id>/`. Tiens à jour une section `Personnage <Id>` dans `docs/wiki/TODO.md`.
- Ce que JE fais à la main (explique-moi en 3 lignes max) : choisir entre les articles que tu proposes, publier les animations.

## 1. Fiche ✋
Reformule la fiche en 10 lignes max : silhouette, couleurs principales (hex), liste des « emplacements » à remplir (corps et peau, tête et face, cheveux, couvre-chef, haut, bas, veste ou manteau, chaussures, accessoires de taille, de dos, d'épaule, de visage, objet tenu), accessoires qui apparaissent ou disparaissent dans les animations, déroulé des 3 animations.

## 2. Recherche dans le catalogue
- Pour chaque emplacement, cherche dans le catalogue Roblox avec l'API publique de recherche (catalog.roblox.com, recherche par mot-clé et par catégorie : cheveux, chapeaux, vêtements classiques, vêtements en couches, accessoires) et récupère les vignettes (thumbnails.roblox.com) pour les regarder. Essaie plusieurs mots-clés en anglais (ex. « green spiky hair », « open green coat », « katana waist »). Si tu n'as pas accès au web, demande-moi de te coller des liens d'articles.
- Propose 2 ou 3 candidats par emplacement, du plus ressemblant au moins ressemblant, dans `assets/persos/<Id>/catalogue.md` : nom, ID, lien (https://www.roblox.com/catalog/<ID>), type, et en une phrase pourquoi il colle (ou ce qui ne colle pas). Montre-moi les vignettes. ✋
- Préférences : articles vendus par Roblox ou par des créateurs avec beaucoup de ventes (moins de risque qu'ils soient supprimés), vêtements en couches pour les vestes et manteaux, cheveux en un seul morceau propre. Évite les articles qui portent un logo ou un nom officiel.

## 3. Assemblage dans Studio ✋
- Construis une `HumanoidDescription` avec les articles choisis : parties du corps (corps en blocs par défaut = IDs 0, sauf si la fiche demande autre chose), tête et face, couleurs de peau (HeadColor, TorsoColor, …), Shirt / Pants / T-Shirt classiques, accessoires et vêtements en couches avec `SetAccessories` (ordre des couches : sous-vêtements d'abord, manteaux en dernier), échelles du corps si la fiche le demande.
- Crée le modèle avec `Players:CreateHumanoidModelFromDescription(description, Enum.HumanoidRigType.R15)`, nomme-le `<Id>` et pose-le dans le Workspace. Si ça échoue en mode édition, montre-moi l'erreur et propose une autre voie (par exemple `InsertService:LoadAsset` article par article).
- Enregistre la description finale dans `assets/persos/<Id>/tenue.json` (tous les IDs, couleurs, échelles, réglages de position des accessoires) : c'est elle qui permet de reconstruire le perso à tout moment.
- Captures de face, 3/4, dos et profil, à côté de la référence. ✋
- Retouches possibles quand je les demande : changer un article (nouveaux candidats), déplacer, tourner ou agrandir un accessoire (Position / Rotation / Scale de l'accessoire dans la description), changer la couleur de peau, les proportions, la face. Mets à jour `tenue.json` à chaque fois.

## 4. Ce que le catalogue n'a pas (dernier recours)
Si aucun article ne convient pour un élément important, dis-le-moi et propose : (a) l'article le plus proche, ou (b) un accessoire sur mesure modélisé dans Blender via le MCP Blender (mesh simple, texture peinte avec Pillow, export FBX sans armature, je l'importe, tu en fais un `Accessory` avec le bon Attachment). Ne fais (b) que si je dis oui.

## 5. Animations (calculées par script, construites dans Studio)
Trois animations par perso, décrites dans la fiche : `<Id>_Idle` (en boucle), `<Id>_Action` (démonstration de pouvoir, une fois), `<Id>_Signature` (geste typique, une fois). Ce sont des animations de VITRINE, jouées sur la case du perso : pas des animations de combat.
- Sur place : `LowerTorso` ne s'éloigne jamais de plus de 0,5 stud de sa position de départ (les bras peuvent avancer en translation pour un effet élastique). VFX dans un rayon de 5 studs autour du perso.
- Raccords : Action et Signature commencent et finissent exactement sur l'image 0 de l'Idle (« pose neutre »), sauf si la fiche dit autre chose (ex. Zoro : l'Action finit sabres en main, la Signature les range) ; vérifie alors que les images de raccord sont identiques.
- Source de vérité : `assets/persos/<Id>/anims/<Id>_<Nom>.json`, généré par un script Python (`anims_<Id>.py`) : clés à 30 images/s, une rotation par articulation R15 dans les axes de `assets/persos/_rig/axes_r15.json`, translation seulement sur Root (et sur un bras si la fiche le demande), easing par clé, marqueurs.
- Articulations : coude et genou ne plient que dans un sens (0 à 150°), poignets et chevilles ±30°, tête ±25°. Pieds plantés et mains posées sur un point (sol, poignée, menton, poche) : IK à deux os calculée dans le script.
- Finition (obligatoire, validée sur luffy) : après le blocage, `finir()` (module `assets/persos/_anim/finition.py`, branchement : voir `anims_luffy.py`, `anims_nami.py`, `anims_zoro.py`) cuit l'animation image par image dans `anims/<Id>_<Nom>_fini.json` ; c'est cette version qui est publiée. Elle ajoute les ressorts par articulation (retard en cascade buste → épaule → coude → poignet, léger dépassement), la respiration et les secousses d'impact (`secousses=[(image, durée, degrés)]`). Les jambes et Root restent ceux du blocage (pieds plantés) ; `contacts={articulation: [(début, fin)]}` garde exactes les articulations d'une main posée (chapeau, biceps, bras croisés). Viser l'impact dès le blocage : anticipation, courbe `Sortie` (départ explosif) sur les coups et dégainages, `Entree` sur ce qui accélère jusqu'au contact (chute, coup au sol), `Rebond` sur un retour élastique, arrêt sur image (2 clés identiques à 4 – 6 images) à l'impact. Vérifier la version finie sur chaque image (mêmes contrôles que le blocage). Transfert vers Studio : le JSON est trop lourd pour du code inline ; le copier en module JSON temporaire dans `src/server/_transfert/` (Rojo le synchronise), construire la KeyframeSequence en lisant le module, puis supprimer le dossier (sur disque et dans Studio).
- Dans Studio : une `KeyframeSequence` par animation à partir du JSON (Pose hiérarchiques selon l'arbre des Motor6D : HumanoidRootPart → LowerTorso → UpperTorso → …). Idle : Loop = true, Priority = Idle. Action et Signature : Loop = false, Priority = Action.
- Prévisualisation : pose des clones ancrés aux images clés, captures de face et de 3/4 (vérifie qu'aucun membre ne traverse un vêtement en couches, les cheveux ou un accessoire), puis supprime les clones. ✋ après CHAQUE animation.
- Objets qui apparaissent ou disparaissent : renomme l'Accessory en `Acc_<Nom>`, attribut booléen `VisibleParDefaut`, Transparency des pièces de l'accessoire à 1 s'il est caché. Un objet tenu en main (sabre dégainé…) : soude son Handle à la main avec un Weld calculé, au lieu de son attachment d'origine.
- Marqueurs (JSON puis `KeyframeMarker` sur le Keyframe le plus proche, ajouté si besoin) : Name = `Montrer`, `Cacher` ou `VFX` ; Value = `Acc_<Nom>` ou `<NomEffet>`.
- Publication : range les KeyframeSequence dans l'entrée `ServerStorage.RBX_ANIMSAVES.<Id>` créée quand j'ouvre l'éditeur d'animation sur le modèle (demande-le-moi d'abord). Je les publie et je te donne les 3 IDs. Attributs texte sur le modèle : `AnimationIdle`, `AnimationAction`, `AnimationSignature`. Vérifie chaque ID avec `KeyframeSequenceProvider:GetKeyframeSequenceAsync`.

## 6. VFX (Studio)
- Dossier `VFX` dans le modèle, un sous-dossier par effet nommé comme dans la fiche. Émetteurs sur des Attachments des pièces ou des accessoires (ex. lame d'un sabre). Tout est désactivé par défaut.
- Attributs du sous-dossier : `Mode` = "Burst" (Emit(`Quantite`)) ou "Duree" (activé pendant `Duree` secondes). Un effet « de X à Y » : marqueurs `VFX <Nom>` et `VFX <Nom>_Fin`, ou Mode Duree.
- Style anime, net et lumineux, couleurs du perso, effets courts (0,2 à 1 s), 60 particules maximum à l'écran par effet. Textures : celles de Roblox, ou des images Pillow dans `assets/persos/<Id>/vfx/` (je les importerai).
- Prévisualise chaque effet à l'image de son marqueur (Emit en mode édition), capture.
- Ne crée aucun script de jeu : la lecture des marqueurs en jeu sera codée à part, dans `src/`.

## 7. Finition dans Studio
- Garde le Humanoid (il affiche les vêtements et les vêtements en couches) : DisplayDistanceType = None, HealthDisplayType = AlwaysOff. Supprime le script `Animate` et l'Animator du Humanoid.
- Ajoute un `AnimationController` avec son `Animator` à la racine du modèle (c'est ce que le code du jeu utilise). Vérifie en mode Play qu'une animation jouée sur cet Animator anime bien le corps et les accessoires.
- HumanoidRootPart : Anchored = true, Transparency = 1, PrimaryPart du modèle. Toutes les pièces et accessoires : CanCollide, CanQuery, CanTouch = false, Massless = true pour les accessoires.
- Range le modèle dans `ReplicatedStorage.ModelesPersonnages.<Id>`. S'il y avait déjà un modèle `<Id>`, renomme l'ancien en `<Id>_ancien` (je le supprimerai moi-même). Supprime les copies de travail et rappelle-moi d'enregistrer la place.

## 8. Bilan
5 lignes max : articles utilisés, IDs des animations, ce qui reste à faire de mon côté.

## 9. Pièges connus
- Caméra de Studio : `screen_capture` avec `camera_position` peut laisser la caméra en `Scriptable` si l'appel expire. Après chaque capture, remets `workspace.CurrentCamera.CameraType` à `Fixed` si besoin.
- `list_roblox_studios` donne le `studio_id`, qui change à chaque relance de Studio.
- Un article du catalogue peut être supprimé par Roblox (modération, droits d'auteur) : son mesh ne se charge plus. Si ça arrive, `tenue.json` sert à remplacer l'article sans tout refaire.
