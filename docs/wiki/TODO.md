# TODO

Suivi des tâches de développement. Les décisions de game design en attente sont dans [Questions ouvertes](Questions-ouvertes.md).

## En cours
### Personnage `zoro` (skill `/perso-roblox`, Mythique, fichiers dans `assets/persos/zoro/`)
- [x] Prérequis : mannequin (`assets/persos/_mannequin/`, `ServerStorage.Gabarits.MannequinR15`) présent, référence lue
- [x] Sabres sur la hanche **droite** (validé) : la main droite dégaine du même côté, la main gauche en travers du corps ; la Signature range à droite
- [x] 2. Vêtements peints (`peindre_zoro.py` → `shirt_zoro.png`, `pants_zoro.png`, `face_zoro.png`)
- [x] 2. Aperçu Blender (`zoro_apercu.blend`) ✋ validé
- [x] Retouches demandées : face (yeux plus grands et remontés, ombre du bandana en dents de scie, nez et bouche manga, sourcils fins), bandana en dôme lisse et détaillé, cheveux en lames superposées + sous-couche, cel-shading animé sur tout le corps et la tenue
- [x] 2. Envoi des images (Shirt 86313064432811, Pants 72370767099637, face 140683552962153), `Workspace.zoro` en (-14, 0, 300), captures Studio identiques à l'aperçu
- [x] 3. Accessoires Blender (`accessoires_zoro.py`, texture `texture_acc_zoro.py` → `acc_zoro.png`) : 11 objets, 5 456 triangles, `accessoires.json` ✋ validé
- [x] 3. Export des 11 FBX (`assets/persos/zoro/fbx/`), vérifiés par réimport (triangles, boîtes, texture intégrée, UV)
- [x] 3. Import des 11 FBX dans Studio (manuel) : arrivés ×100 (Blender en mètres → FBX en cm), orientation correcte (vérifiée par EditableMesh)
- [x] 3. Accessory + Attachment pour chacun (taille ÷ 100, `AccessoryWeld` créés à la main : `AddAccessory` n'en crée pas en mode édition), `VisibleParDefaut`, captures conformes à l'aperçu
- [x] Ouvrir l'éditeur d'animation sur `zoro` pour créer `ServerStorage.RBX_ANIMSAVES.zoro` (manuel)
- [x] 4a. `zoro_Idle` (`anims_zoro.py`, `anims/zoro_Idle.json`) : bras croisés par construction géométrique (épaules avancées de 0,45 et descendues de 0,1 à 0,2, effet élastique), validé ; KeyframeSequence dans `RBX_ANIMSAVES.zoro` (10 clés)
- [x] 4b. `zoro_Action` (105 images, 15 clés + 9 marqueurs) : bras visés main + lame, poignets ±30°, pieds plantés, lames jamais dans le corps
- [x] 4c. `zoro_Signature` (75 images, 6 clés + 5 marqueurs) : raccords exacts (Action[105] = Signature[0], Signature[75] = Idle[0]) ; lames à l'horizontale ramenées à la hanche (l'axe des fourreaux est hors d'atteinte)
- [x] Animation bloquée (éditeur et jeu) : Humanoid + AnimationController dans le même modèle se bloquent. AnimationController retiré de `Workspace.zoro`, `Animator` ajouté dans le Humanoid ; vérifié en Play (main aux bras croisés). Skill `/perso-roblox` corrigé
- [x] `BaseService` : l'Animator est cherché dans l'AnimationController puis dans le Humanoid (accord donné), selene OK, synchronisé par Rojo ; test en jeu après publication de l'Idle
- [x] Gabarit `MannequinR15` corrigé (AnimationController retiré, Animator dans le Humanoid) — enregistrer la place
- [x] Sabres épaissis ×1,6 (lames, poignées, gardes, fourreaux ; `ECH_SABRE`) et fourreaux collés au manteau en faisceau (recherche par grille, 14,7 s) ; animations revérifiées (lames jamais dans le corps), 5 FBX réexportés et vérifiés
- [x] 5 FBX réimportés (manuel), Handles remplacés dans `Workspace.zoro` (tailles vérifiées, visibilités et soudures conservées), capture Studio conforme
- Pose neutre des animations : bras écartés de 6° (sinon les mains traversent le manteau et l'écharpe)
- [ ] 4. Animations `zoro_Idle`, `zoro_Action`, `zoro_Signature` (`anims_zoro.py`, JSON, KeyframeSequence) ✋ ×3
- [x] 5. VFX (`vfx_zoro.py` → `vfx/entaille.png` 100815645874876, `anneau.png` 101774142734315, `eclat.png` 81528160627739) : dossier `VFX` (Trail_Lames en Duree 1,17 s ; Entaille_Droite / Gauche, Tornade_Sabres, Eclat_Garde en Burst, ≤ 31 particules), émetteurs liés par ObjectValue `Emetteur`, attribut `Quantite` ; aperçus Studio au ralenti (lumière baissée à cause du Bloom de la place)
- [x] Test en Play : marqueurs Montrer / Cacher / VFX reçus aux bons temps, sabres visibles et suivent les mains ; accessoires reliés au lancement par `AccessoryRigidConstraint` (les Weld manuels sont inutiles)
- [x] 6. Finition (Humanoid sans nom ni barre de vie, HRP ancré et invisible, collisions coupées, Animator dans le Humanoid) et rangement dans `ReplicatedStorage.ModelesPersonnages.zoro` (11 accessoires, 5 VFX) ; copie `Workspace.zoro` gardée pour la publication, à supprimer après
- [x] 4. Publication : `zoro_Idle` 91377258848316 et `zoro_Action` 102192436973689 vérifiées conformes, attributs `AnimationIdle` / `AnimationAction` posés sur `ModelesPersonnages.zoro`
- [x] 4. `zoro_Signature` republiée 73416757790535 (la 118275247847155 avait perdu un marqueur : l'éditeur fusionne deux `Cacher` sur la même image → second décalé à l'image 46), conforme, attribut `AnimationSignature` posé
- [x] `Workspace.zoro` supprimé ; test en Play sur Emplacement1 (logique de `BaseService`) : Idle publiée en boucle, enchaînement Action → Signature → Idle, 14 marqueurs reçus, sabres cachés et poignées revenues à la fin
- [ ] Enregistrer la place Studio (modèle, gabarit corrigé, animations, VFX : hors git) (manuel)
- [x] Outil Studio `ServerStorage.TestDonnerPersonnage` (GachaService) : donne un perso précis ; zoro donné à cemobozo (uid 18, puis 19 en test : doublon sauvegardé)
- [x] Vitrine en jeu (décision : Idle → Action → Signature en boucle, 2 s de pause, visible par tous ; wiki `Personnages.md`) : cycle joué par le serveur dans `BaseService` (dernière image figée pendant les pauses), marqueurs Montrer / Cacher / VFX appliqués par chaque client (`src/client/Vitrine.luau`) ; selene OK ; testé en Play côté client (cycle de 16 s, sabres visibles pendant l'Action et la pause en garde)

### Personnage `zoro` — ancienne tentative (skill `/perso-r6`, style B, Mythique, fichiers dans `assets/blender/zoro/`)
- [x] 1. Fiche validée : sabres sur la hanche **droite**, œil droit petit, ombre du bandana sur les yeux, pas d'yeux qui se ferment (tête baissée seulement)
- [x] 2. Blockout (copie du gabarit `nami.blend` : armature + 7 pièces reconstruites)
- [x] 3a. Modèle R6 (2 444 triangles) : refusé (bandana « bonnet », tête facettée, tenue pas assez détaillée)
- [ ] 3b. Modèle **R15** (essai demandé) : 15 pièces + `HumanoidRootPart`, tête et bandana lisses, manteau long, ceinture rouge à 2 pans, sangles à boucles dorées — en attente de validation
- [ ] Passage des nouveaux persos en **R15 bloc** (Nami reste en R6) :
  - [x] Relever le rig R15 en blocs de Roblox dans Studio → `assets/rig/r15_bloc.json`, modèle de test supprimé (relevé en Play : Roblox utilise des `AnimationConstraint` au lieu de Motor6D, C0/C1 = CFrame des attachments)
  - [x] Gabarit `assets/rig/r15_bloc.blend` (15 boîtes + HumanoidRootPart, armature `Rig_R15`), captures + pose test
  - [x] Skill `/perso-r6` : section « 2 bis. Structure R15 bloc », articulations, étapes 8 et 9, budgets +20 %
  - [ ] Valider le skill R15 (relecture du diff, captures du rig)
  - [ ] Refaire `zoro` sur le gabarit R15 bloc (ajouter « Rig : R15 bloc » à sa fiche)
    - [x] 1. Nouvelle fiche validée : sabres sur la hanche **droite**, sabre de bouche amené par la main droite (déjà armée), refait de zéro (ancienne tentative rangée dans `assets/blender/zoro/v1/`)
    - [x] 2. Blockout sur une copie de `assets/rig/r15_bloc.blend` (armature `Rig_zoro`)
    - [ ] 3. Modèle final + `Texture_zoro.png` (2 464 triangles / 6 000, `texture_zoro.py` + `uv_zoro.json`) ; retouches faites (manteau élargi jusqu'à mi-mollet, fourreaux écartés, mèches en touffes) — en attente de validation
- [ ] 4. Rig + parentage rigide (pièces et `Acc_`)
- [ ] 5a. Animation `zoro_Idle` (120 images, boucle)
- [ ] 5b. Animation `zoro_Action` (105 images, marqueurs)
- [ ] 5c. Animation `zoro_Signature` (75 images, marqueurs)
- [ ] 6. Export FBX (modèle + 3 animations), vérifié par réimport
- [ ] 7. Import dans Studio (manuel)
- [ ] 8. Finition Studio : redressement, Motor6D, `Accessoires` + Weld, VFX, rangement dans `ModelesPersonnages.zoro`
- [ ] 9. KeyframeSequences + marqueurs, publication des 3 animations (manuel), attributs `AnimationIdle` / `AnimationAction` / `AnimationSignature`
- [ ] Tester un export par skinning rigide (poids 1 sur un os), cf. leçon de `nami`

### Personnage `nami` (skill `/perso-r6`, fichiers dans `assets/blender/nami/`)
- [x] Fiche validée
- [x] Version 1 : modèle, rig, animation `nami_Idle`, export FBX (jugée pas assez belle avant import)
- [x] Version 2 : gabarit R6 standard (boîtes + tête Roblox), cheveux en mèches, visage plus détaillé, bâton tenu dans le poing (1 988 triangles)
- [x] Rig + animation refaits sur le nouveau gabarit (bâton planté au sol, car pas de coude en R6)
- [x] Validation de l'animation v2
- [x] Export FBX v2 (`nami.fbx`, `nami_Idle.fbx`), vérifié par réimport dans Blender
- [x] Import dans Studio (manuel : Fichier → Importer)
- [x] Finition via MCP : pièces redressées (l'importeur couche de ±90° les meshes parentés à un os), 6 Motor6D R6 standard, HumanoidRootPart 2×2×1, réglages, `AnimationController` + `Animator`, rangé dans `ReplicatedStorage.ModelesPersonnages.nami`
- [x] Animation (plan B) : `KeyframeSequence` `nami_Idle` générée depuis Blender dans `ServerStorage.RBX_ANIMSAVES.nami` (46 images, 3 s, boucle)
- [x] Animation publiée (ID 90443145794699, vérifiée : 46 images, 3 s, boucle, priorité Idle), attribut `AnimationIdle` sur le modèle, copie de travail supprimée
- [x] `BaseService` : personnage posé = clone du modèle 3D (pieds sur la case, tourné vers l'allée, `AnimationIdle` en boucle), bloc coloré en secours ; selene OK, placement vérifié en mode édition
- [ ] Test en jeu : poser Nami et vérifier modèle, orientation, animation, étiquette (manuel)
- [ ] Enregistrer la place Studio (caméra remise en `Fixed`, modèle et animation)
- [x] Skill `/perso-r6` corrigé avec les leçons de `nami` (style Roblox, objet tenu, pieds plantés, menu Fichier → Importer, redressement des pièces + Motor6D standard, KeyframeSequence en voie principale, piège de la caméra)
- [ ] Tester sur le prochain personnage un export par skinning rigide (poids 1 sur un os) pour voir si l'importeur garde alors les pièces droites

### Animation « Combat Idle » (rig R6) — à reprendre, résultat jugé mauvais
- [x] Partie A : générateur de KeyframeSequence `Fighter_CombatIdle` (`tools/studio/GenererCombatIdle.luau`, Command Bar)
- [x] Partie B : Script serveur de lecture à placer dans le modèle (`tools/studio/CombatIdle.server.luau`)
- [x] selene sur les deux fichiers
- [x] Test du générateur dans Studio (via MCP, rig R6 temporaire supprimé ensuite) : pieds au sol, sens des membres, boucle identique
- [x] Rig de prévisualisation `Workspace.Fighter_Test` (R6, sur le Hub) + séquence générée dans `ServerStorage.RBX_ANIMSAVES.Fighter_Test`
- [ ] Générer sur le vrai rig du combattant, publier l'animation et coller l'ID dans `ANIMATION_ID` (manuel, dans Studio)
- [ ] Coller `CombatIdle.server.luau` dans un Script du modèle du personnage (manuel, hors Rojo)
- [ ] Vérifier à l'œil dans l'Animation Editor le sens de l'easing Elastic/Out et les axes de la cape

## À faire
### Mannequin R15 (suites)
- [ ] Enregistrer la place Studio (mannequin dans `ServerStorage.Gabarits`, hors git) (manuel : Ctrl+S dans Studio)
- [x] Comparer `zoro.blend` et sa copie non enregistrée (seule différence : image courante 0 / 1) et supprimer la copie
- [x] Skill `/perso-roblox` mis à jour : références du mannequin, envoi des images par `upload_image`, empilement Shirt / Pants, lignes par pièce, parties cachées, face (fond transparent, zone utile), aperçu Blender (images `Shirt` / `Pants` / `Face`), conversion des axes, clones ancrés, pièges (premier plan, captures une par une, Highlight, `Clothing`, EditableMesh)
- [x] `assets/rig/r15_bloc.*` gardé tel quel : c'est le gabarit du skill `/perso-r6` sur lequel `zoro` est construit ; le nouveau mannequin sert au skill `/perso-roblox`
- [ ] (optionnel) Aligner la section R15 du skill `/perso-r6` sur le nouveau mannequin (tête 1,19 × 1,25, os verticaux, `axes_r15.json`) : à décider, change le gabarit de `zoro`

### Map (place Studio)
- [ ] Enregistrer / publier la place Studio (Hub, chemins, murs recentrés : hors git)
- [ ] Dupliquer `BaseJoueur` sur les 7 emplacements `Hub.EmplacementsBases/Base1..7`
- [ ] Vérifier que `BaseService` attribue correctement une base libre parmi les 7

### Hub
- [ ] ProximityPrompt et interface de chaque stand (Évolutions, Étoiles, Ateliers, Recyclage)
- [ ] Panneaux de classements
- [ ] Piédestal d'événement
- [ ] Modèles 3D des PNJ des stands (blocs provisoires)

### Interface
- [ ] Tester l'interface sur mobile (émulateur d'appareil de Studio)
- [ ] Remplacer l'initiale de la carte de tirage par le visuel du personnage (modèles 3D)
- [ ] Boutons des futures mécaniques (déblocage d'emplacement, machine, rebirth) quand leurs valeurs seront définies

### Boucle de base
- [ ] Modèles 3D des personnages (blocs colorés provisoires)
- [ ] Déblocage des emplacements 3 à 10
- [ ] Machine RNG améliorable (10 niveaux)
- [ ] Rebirth (dans la base)

### Avant publication
- [ ] Verrou de session sur les sauvegardes (ProfileStore ou verrou maison)
- [ ] Remplacer les noms One Piece par des personnages originaux

## Terminé
- [x] Mannequin R15 du skill `/perso-roblox` (`assets/persos/_mannequin/`, `ServerStorage.Gabarits.MannequinR15`)
  - [x] 1. Mannequin Studio : R15 en blocs, AnimationConstraint convertis en Motor6D, ragdoll supprimé, tête classique + Decal `face`, AnimationController + Animator, sans Animate
  - [x] 2. Relevé `r15_bloc.json` (pièces, Motor6D, Attachments, blocs visibles) ; seule la tête diffère de `assets/rig/r15_bloc.json`
  - [x] 3. Calibration des vêtements et de la face : `zones_vetements.json` (zones, sens de lecture, lignes par pièce, empilement, Decal `face`)
  - [x] 4. `mannequin.blend` (script `construire_mannequin.py`) : 8 vues identiques à Studio
  - [x] 5. `axes_r15.json` : 45 rotations identiques à 1e-5, pose test identique
  - [x] 6. Clones de test supprimés (Studio et Blender), gabarit vérifié intact
- [x] MCP Blender (ahujasid/blender-mcp) installé et connecté
  - [x] uv / uvx dans le PATH (uv 0.11.33)
  - [x] Blender 5.2.3 LTS (`C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`)
  - [x] `addon.py` v1.8 téléchargé et relu (serveur localhost:9876, télémétrie désactivée par défaut)
  - [x] Add-on installé et activé en ligne de commande, préférences sauvegardées
  - [x] `claude mcp add -s user blender uvx blender-mcp` (en portée locale il était rangé sous `C:/…` alors que VS Code ouvre le projet en `c:/…`, donc invisible dans `/mcp`)
  - [x] Connexion vérifiée depuis la session (lecture de la scène)
- [x] Boucle de base jouable en solo (attribution de base, tirage, emplacements, revenu, collecteur)
- [x] Wiki : page Hub (Sanctuaire Mère), plan validé, 7 bases, carte au sol, rebirth dans la base
- [x] Maquette grise du Hub dans Studio (plateau, piédestal, 7 chemins, 4 stands, classements)
- [x] Murs et sol recentrés sur le Hub
- [x] Suivi des tâches : règle dans `CLAUDE.md`, création de ce fichier, lien dans le README du wiki
- [x] `default.project.json` : Baseplate recentrée et agrandie, placée par `CFrame` (sinon `rojo serve` la remettait en (0, 0, 0))
- [x] Interface UI (HUD, carte de tirage, inventaire)
  - [x] Remotes partagés (`src/shared/Remotes.luau`), toutes créées d'un coup par le serveur
  - [x] `DataService.Retirer` / `PremierEmplacementLibre` (sans changer le format sauvegardé)
  - [x] `InterfaceService` serveur : envoi de l'inventaire, Poser / Retirer validés, notifications
  - [x] `GachaService` : résultat du tirage envoyé au client, notification inventaire plein
  - [x] `RevenuService` : attributs `ArgentNonCollecte` / `RevenuParSeconde`, événement de collecte
  - [x] Client : HUD (argent, revenu, à collecter)
  - [x] Client : carte de tirage animée
  - [x] Client : inventaire (poser / retirer)
  - [x] Client : notifications
  - [x] selene + test en Play dans Studio (tirage, poser, retirer, refus, collecte)
  - [x] Docs : `CLAUDE.md`, wiki (état technique)
