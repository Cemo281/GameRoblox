# Import dans Roblox Studio : tenue d'aventurier (R15 bloc)

Fichiers générés par `tools/build_outfit_r15.py` (Blender 5.x) :

```
"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" -b --factory-startup --python tools/build_outfit_r15.py -- --quitter
```

Les valeurs ci-dessous viennent de `export/offsets.json`, réécrit à chaque lancement. Toutes les positions sont en studs.

## Avant de commencer

- **Envoi à Roblox** : importer ces FBX envoie des maillages et l'atlas `palette_tenue.png` (16 cases de couleur unie). Le contenu est neutre : tenue couvrante, aucun texte, aucun logo.
- **Personnage existant** : la tenue reprend celle d'un personnage d'animé connu. Pas de problème dans une place privée. Avant de publier ou de passer en public, il y a un risque de réclamation DMCA (voir le garde-fou de `CLAUDE.md`).
- **Couleurs** : chaque pièce n'a qu'un matériau, `atlas_tenue`, qui pointe vers `palette_tenue.png` (intégré au FBX). Dans Studio, garder `Material = Plastic`. La rugosité et le métal de la palette ne sont pas reproduits.
- **Échelle** : 1 unité Blender = 1 stud, avec les réglages d'export déjà validés pour ce projet (`axis_forward -Z`, `axis_up Y`, `FBX_SCALE_ALL`). Dans l'importateur 3D, vérifier que le chapeau mesure environ 2,84 studs de large. Sinon, choisir l'unité « Studs » dans les options de dimensions du fichier.
- **Repère** : positions relatives au `HumanoidRootPart` d'un R15 bloc par défaut (`assets/persos/_mannequin/r15_bloc.json`) : Y vers le haut, le perso regarde vers -Z, sa droite est +X.

## Récapitulatif

| Fichier | Type Roblox | Attachment | Triangles | Taille X × Y × Z |
|---|---|---|---|---|
| `salopette.fbx` | Layered **Pants** | `WaistCenterAttachment` (généré par l'AFT) | 1 260 | 2,12 × 3,67 × 1,15 |
| `chaussures.fbx` (ou `chaussure_gauche.fbx` + `chaussure_droite.fbx`) | Layered **LeftShoe** + **RightShoe** | généré par l'AFT | 168 + 168 | 1,04 × 0,57 × 1,12 chacune |
| `brassard.fbx` | Layered **Jacket** | généré par l'AFT | 92 | 1,06 × 0,45 × 1,06 |
| `chapeau.fbx` | Rigide **Hat** | `HatAttachment` | 1 062 | 2,84 × 1,69 × 1,98 |
| `cheveux.fbx` | Rigide **Hair** | `HairAttachment` | 2 184 | 1,58 × 1,82 × 1,12 |
| `sac.fbx` | Rigide **Back** | `BodyBackAttachment` | 1 520 | 2,30 × 3,08 × 1,39 |
| `lance_pierre.fbx` | **Tool** (`Handle`) | `RightGripAttachment` (main) | 2 912 | 1,49 × 6,51 × 0,20 |

Contrôles automatiques réussis pour toutes les pièces :
- moins de 4 000 triangles ;
- maillages fermés (aucune arête ouverte) ;
- aucune paire de faces coplanaires qui se recouvrent entre deux éléments (écart minimal de 4 millièmes de stud) ;
- au plus 4 os par sommet ;
- tous les sommets de chaque vêtement sont à l'intérieur de sa cage externe.

## Layered clothing : salopette, chaussures, brassard

Chaque FBX contient :
- l'armature `R15` : `Root` → `HumanoidRootNode` → `LowerTorso`…, noms officiels ; la tête de chaque os est sur l'articulation relevée dans Studio ;
- le maillage skinné, avec des poids lissés à la taille, aux hanches, aux genoux, aux chevilles et au coude ;
- `<nom>_InnerCage` et `<nom>_OuterCage`.

D'où viennent les cages :
- **Cage interne** : le `Clothing_Cage_Template.blend` officiel (dépôt `Roblox/avatar`, copie dans `tools/cages_roblox/`), recalé sur les blocs du R15. Mêmes 1 358 sommets, mêmes faces, mêmes UV `map1` : seules les positions changent.
- **Cage externe** : la cage interne poussée au-dessus du vêtement (jeu de 0,045 stud) et identique à la cage interne ailleurs.

Os utilisés :
- `salopette` : UpperTorso, LowerTorso, Left/RightUpperLeg, Left/RightLowerLeg ;
- `chaussure_gauche` : LeftLowerLeg, LeftFoot (`chaussure_droite` : RightLowerLeg, RightFoot) ;
- `brassard` : LeftLowerArm, plus LeftUpperArm au bord haut. Il est placé sous le coude, comme sur la référence ; pour le mettre sur le haut du bras comme dans le README, passer `BRASSARD_OS = "LeftUpperArm"` dans le script.

Étapes, pour chaque pièce :
1. **Fichier → Importer en 3D** → choisir le FBX. Dans l'aperçu, vérifier que les objets `_InnerCage` et `_OuterCage` sont reconnus comme cages du maillage et non comme maillages séparés.
2. Insérer le modèle à côté d'un **R15 bloc** (Avatar → Rig Builder → Block, R15).
3. Ouvrir **Avatar → Accessory Fitting Tool**, sélectionner le MeshPart, choisir **Clothing** puis le type :
   - `Pants` pour la salopette ;
   - `LeftShoe` / `RightShoe` pour chaque chaussure ;
   - `Jacket` pour le brassard : couche la plus extérieure du bras, il passe au-dessus d'une chemise.
4. Prévisualiser sur le mannequin **bloc / Classic**, lancer les animations de test de l'AFT (marche, course, emotes), puis **Generate MeshPart Accessory**. L'AFT crée l'Accessory, le `WrapLayer` et les Attachments.
5. Équiper le R15 bloc et vérifier avec l'`Animate` par défaut en Play.
6. Chaussures : deux accessoires distincts (gauche et droite). Si l'importateur gère mal les deux paires de cages de `chaussures.fbx`, importer `chaussure_gauche.fbx` puis `chaussure_droite.fbx`.

## Accessoires rigides : chapeau, cheveux, sac

Exportés à leur place sur le rig. Après import, le Handle est centré sur sa boîte englobante (comportement par défaut de Studio). L'Attachment à mettre dans le Handle est donc à la position ci-dessous, sans rotation : les axes de l'accessoire sont ceux du perso.

| Pièce | Accessoire | Attachment dans le Handle (position) | Attachment du corps (position dans sa pièce) | Centre du Handle (relatif au HRP) |
|---|---|---|---|---|
| chapeau (calotte, bord, lunettes) | Hat | `HatAttachment` = (-0,0206 ; 0,0607 ; -0,0291) | Head : (0 ; 0,5896 ; 0) | (0,0206 ; 2,2033 ; 0,0291) |
| cheveux (13 boucles) | Hair | `HairAttachment` = (0 ; 0,8877 ; -0,4290) | Head : (0 ; 0,5896 ; 0) | (0 ; 1,3762 ; 0,4290) |
| sac (sac, bandoulière, boucle, écusson, pompon) | Back | `BodyBackAttachment` = (0,5776 ; 0,2792 ; 0,5001) | UpperTorso : (0 ; -0,2122 ; 0,5020) | (-0,5776 ; -0,2419 ; 0,0019) |

Étapes :
1. Importer le FBX (Importer en 3D). Vérifier que la taille du MeshPart correspond à la colonne « Taille » du récapitulatif.
2. **Accessory Fitting Tool** → sélectionner le MeshPart → **Accessory** → type `Hat`, `Hair` ou `Back` → Generate MeshPart Accessory.
3. Dans l'Accessory généré, régler l'Attachment du Handle sur la position du tableau, sans rotation, puis équiper le R15 : la pièce se place exactement comme dans Blender.

Boîtes limites, mesurées depuis l'attachment, colonne **Classic** (corps bloc) des specs Roblox :

| Pièce | Étendue mesurée (min → max) | Limite Classic | Limite Normal |
|---|---|---|---|
| chapeau | X -1,40 → 1,44 ; Y -0,90 → 0,78 ; Z -0,96 → 1,02 | 3 × 4 × 3 centré : OK | 1,87 × 2,5 × 1,87 : **dépasse** |
| cheveux | X ±0,79 ; Y -1,80 → 0,02 ; Z -0,13 → 0,99 (Z+ = arrière) | 3 × 5 × 3,5 (2 haut, 3 bas, 1,5 avant, 2 arrière) : OK | 1,87 × 3,12 × 2,18 : OK |
| sac | X -1,73 → 0,57 ; Y -1,82 → 1,26 ; Z -1,19 → 0,19 (Z- = avant) | 10 × 7 × 4,5 (1,5 avant, 3 arrière) : OK | 9,86 × 8,59 × 4,87 : OK |

Ces limites ne servent qu'à la validation pour le Marketplace ; un accessoire utilisé dans le jeu peut les dépasser.
- **Chapeau** : avec ses pointes relevées sur les côtés, il fait 2,84 studs de large. Il tient dans la boîte Classic, pas dans la boîte Normal. Pour le vendre un jour en version Normal, il faudrait réduire le bord à environ 1,8 stud.
- **Sac** : le README proposait `BodyFrontAttachment` (type Front), mais l'ensemble sac + bandoulière dépasse la boîte Front (3 × 3 × 3 centrée sur la poitrine) : le sac pend sous la main gauche. D'où le type **Back**, que le README cite aussi.

## Lance-pierre (Tool)

- Le maillage s'appelle déjà `Handle`. Son origine dans Blender est le point de prise (y = 0 de la référence) ; le bâton monte le long de +Y (Roblox), avec l'anneau en haut, dans le plan XY.
- Après import, Studio centre le Handle sur sa boîte englobante : la prise est alors à **(0 ; -1,3879 ; 0)** dans le Handle.

Étapes :
1. Importer `lance_pierre.fbx`, créer un `Tool` dans StarterPack et y mettre le MeshPart (nom `Handle`, CanCollide désactivé).
2. Régler **`Tool.Grip = CFrame.new(0, -1.3879, 0)`** (GripPos = (0 ; -1,3879 ; 0), orientation par défaut). La soudure `RightGrip` met alors la prise sur le `RightGripAttachment` de la main droite.
3. En Play : avec l'animation « tool hold » par défaut, le bras se lève vers l'avant et le bâton se tient vertical, anneau en haut. Une animation de bâton à deux mains reste à faire si on la veut.

## Écarts avec le modèle HTML (référence suivie pour l'apparence)

| Élément | HTML | Construit (d'après `assets/references/`) |
|---|---|---|
| Bavette | boîte olive sur la poitrine + poche, crayon, outil, boucles et boutons de bretelle | pas de bavette sur la poitrine ; `bavette` = panneau brun sous la ceinture, `passepoil_bavette` gris en U, `couture_bavette` |
| Bretelles | olive | rouille (`bretelle`, #7A2E1C, **couleur ajoutée** à la palette) |
| Ceinture | cuir, boucle, ardillon, passants | large bande grise (`bandage`) + `lisere_ceinture` blanc |
| Poches | poches de cuisse avec rabats et rivets | `poche_hanche_*` brunes avec `rabat_poche_*` et `bouton_rabat_*` |
| Pièce au genou | `piece_genou` + croix | retirée (absente de la référence) ; `piece_dos` et `poche_arriere_*` gardées |
| Bas de jambe | pantalon jusqu'en bas, `revers`, chaussures basses | pantalon jusqu'à mi-mollet, `revers_*` gris, bottes montantes `chaussure_*` (cuir, semelle et bout noirs, lacets toile) |
| Bandoulière | cuir | blanc, en boucle (devant, épaule droite, dos) jusqu'au nœud du sac |
| Sac | à la hanche | sous la main gauche, à côté de la cuisse ; `rabat_sac` (demi-sphère ouverte) fusionné dans le sac (maillage fermé exigé) |
| Brassard | haut du bras | avant-bras, sous le coude (constante `BRASSARD_OS`) |
| Chapeau | posé tout en haut de la tête, bord rond, ruban | bord au-dessus des yeux, bord allongé sur les côtés avec pointes relevées (32 segments), calotte pincée et creusée, sans ruban |
| Lance-pierre | ouverture décalée de 40°, 4 dents, 10 anneaux noirs | ouverture de 68° à l'opposé du manche, 5 dents (la 5e dans l'axe du manche), bandage croisé (`bande_croisee_a/b`) |

Les autres pièces gardent les noms, tailles et couleurs du HTML, mises à l'échelle du rig : corps à 1/0,3 stud par mètre, tête à 3,3.
