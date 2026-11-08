# Handoff : Tenue d'aventurier → rig Roblox R15

## Objectif
Recréer la tenue du personnage (`Personnage 3D.html`) **directement sur un rig R15 Roblox**, pour que chaque pièce suive les animations R15 standard (marche, course, saut, emotes, outils).

## À propos des fichiers
`Personnage 3D.html` est une **référence de design** construite avec three.js (primitives nommées, coordonnées exactes dans le code). Ce n'est pas un livrable à réutiliser tel quel : le but est de **reconstruire la tenue dans Blender (script Python bpy recommandé)** sur un rig R15, puis d'exporter en FBX pour Roblox Studio.
Les GLB exportés depuis la page peuvent servir de base de géométrie (`Download GLB` après avoir sélectionné une pièce).

## Fidélité
Haute fidélité pour formes, proportions et couleurs. Style « bloc » low-poly, sans textures : couleurs unies par matériau.

## Échelle et repères
- Référence modélisée en **mètres, Y vers le haut, face avant = +Z**, pieds à y = 0.
- 1 « bloc » de référence = 0,3 m. Hauteur personnage (sans chapeau) ≈ 1,6 m.
- Roblox : 1 stud ≈ 0,28 m. Mettre à l'échelle pour que le corps de référence coïncide avec le **rig R15 bloc standard** (UpperTorso 2×1,6×1 studs, etc.). Aligner sur le rig, pas sur les chiffres bruts.
- Rig de départ : exporter un R15 bloc vierge depuis Studio (Avatar → Rig Builder → Block, R15) ou utiliser le plugin Roblox pour Blender.

## Stratégie recommandée
Deux familles de pièces :

### A. Pièces déformables → Layered Clothing (WrapLayer)
Salopette (+ ceinture), chaussures, brassard.
- Partir des **cages officielles Roblox** (Inner/Outer cage du modèle de référence Layered Clothing).
- Mesh skinné sur les bones R15 (voir mapping ci-dessous), poids lissés aux articulations (genoux, hanches, coudes).
- Export FBX : mesh + `_InnerCage` + `_OuterCage`, puis Studio → Accessory Fitting Tool → type correspondant (Pants, Shoes…).

### B. Pièces rigides → Accessoires soudés via Attachments
| Pièce (groupe dans la réf.) | Type Roblox | Attachment R15 |
|---|---|---|
| `chapeau` (calotte, bord, ruban, lunettes) | Hat accessory | `HatAttachment` (Head) |
| `cheveux` (13 sphères bouclées) | Hair accessory | `HairAttachment` (Head) |
| `sac` (sac, bandoulière, boucle, écusson, pompon) | Shoulder/Back accessory | `BodyFrontAttachment` ou `LeftShoulderAttachment` (UpperTorso) — la bandoulière diagonale peut aussi être faite en layered clothing (Jacket) |
| `arme` / `baton_lance_pierre` | **Tool** (Handle) | `RightGripAttachment` (RightHand). Origine = point de prise (y = 0 dans la réf., manche de -0,56 à +1,02 m, anneau au-dessus) |
| `lunettes` | (incluses au chapeau) ou Face accessory | `HatAttachment` |

Alternative rigide pour la salopette si pas de layered clothing : découper en morceaux soudés à chaque part R15 (voir mapping).

## Mapping référence → parts R15
| Élément de la réf. | Part / bone R15 |
|---|---|
| `bavette`, `poche_bavette`, `crayon_poche`, `outil_poche`, bretelles avant/dos/épaule, `boucle_bretelle_*`, `bouton_*` | UpperTorso |
| `bassin`, `ceinture`, `boucle`, `passant_*`, `ardillon`, `trou_ceinture`, `bouton_hanche_*`, `poche_arriere_*` | LowerTorso |
| `pantalon_*` moitié haute, `poche_cuisse_*`, `rabat_poche_*`, `rivet_*` | Left/RightUpperLeg |
| `pantalon_*` moitié basse, `revers_*`, `piece_genou`, `croix_piece_*`, `piece_dos`, `couture_revers_*` | Left/RightLowerLeg |
| `chaussure_*`, `semelle_*`, `bout_chaussure_*`, `lacet_*`, `languette_*` | Left/RightFoot |
| `brassard_0..4` (bandes bleu/blanc) | LeftUpperArm |
| `tete_*`, nez, yeux, bouche | Head (le personnage R15 a déjà une tête : n'exporter le nez qu'en accessoire Face si voulu) |

Côtés : dans la réf., `_d` = droite du personnage (x < 0), `_g` = gauche (x > 0).

## Palette (matériaux nommés, MeshStandard → SurfaceAppearance/couleur unie)
| Matériau | Hex | Rugosité | Métal |
|---|---|---|---|
| peau | #D9A67A | 0.7 | 0 |
| salopette | #9A8A3C | 0.9 | 0 |
| salopette_piece (pièces, coutures) | #7C6E2C | 0.9 | 0 |
| cuir (ceinture, chaussures, bandoulière) | #5A3A22 | 0.75 | 0 |
| noir (cheveux, semelles, yeux) | #161412 | 0.6 | 0 |
| chapeau | #E9E4CF | 0.85 | 0 |
| toile (ruban, lacets, écusson) | #C9B48A | 0.85 | 0 |
| orange (lunettes, crayon) | #E2662A | 0.55 | 0 |
| rouge_sac | #C8432A | 0.7 | 0 |
| bleu (brassard) | #2F4F9E | 0.7 | 0 |
| blanc | #F2F0EA | 0.7 | 0 |
| vert (lance-pierre) | #4F8A1F | 0.5 | 0 |
| vert_fonce | #3A6614 | 0.6 | 0 |
| bandage (manche) | #A9ACA8 | 0.85 | 0 |
| metal (boutons, rivets, boucles) | #B8B2A2 | 0.35 | 0.35 |

Roblox : une texture/couleur par MeshPart → regrouper par matériau ou bake les couleurs dans un petit atlas (palette 16×16 px, UV par matériau).

## Contraintes Roblox à respecter
- Accessoires : ≤ 4 000 triangles chacun ; layered clothing : ≤ 4 000 tris + cages non modifiées en topologie.
- Bounding box par type d'accessoire (le chapeau à bord large 0,84 m de diamètre doit rester dans les limites Hat — réduire légèrement si refusé).
- Pas de faces coplanaires (la réf. décale de ~0,001–0,01 m les détails).
- Noms d'Attachments exacts (sensibles à la casse).
- Le bord du chapeau est une révolution (LatheGeometry, profil ondulé) : 64 segments, à décimer à ~32 pour Roblox.

## Animations
- Une fois skinnée/soudée, la tenue suit toutes les animations R15 (Animate script par défaut, emotes).
- L'arme en Tool utilise l'animation « tool hold » par défaut ; prévoir une anim custom bâton (prise deux mains) si souhaité.

## Livrables attendus de Claude Code
1. Script Blender `build_outfit_r15.py` qui génère chaque pièce sur le rig R15 (noms identiques à la réf.).
2. FBX par pièce : `salopette.fbx` (+ cages), `chaussures.fbx`, `brassard.fbx`, `chapeau.fbx`, `cheveux.fbx`, `sac.fbx`, `lance_pierre.fbx`.
3. Notes d'import Studio (type d'accessoire, attachment, offsets).

## Fichiers
- `Personnage 3D.html` — référence 3D complète ; toutes les dimensions/positions sont dans le module script (fonction `build()`, groupes `corps`, `salopette`, `brassard`, `sac`, `tete_visage`, `cheveux`, `chapeau`, `baton_lance_pierre`).
- `three-d-stage.js` — viewer nécessaire pour ouvrir la référence.
- `reference_chapeau_roblox.png` — test d'import actuel du chapeau dans Roblox.
