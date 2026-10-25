# TODO

Suivi des tâches de développement. Les décisions de game design en attente sont dans [Questions ouvertes](Questions-ouvertes.md).

## En cours
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
