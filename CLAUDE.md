# GameRoblox

## Le jeu
Jeu Roblox Idle / Simulator / Gacha (RNG) sur le thème des cartes d'animé, avec des modèles 3D animés de personnages.

Règles détaillées : voir le wiki (`docs/wiki/`). Résumé : tirage gratuit → personnage (rareté + étoiles) posé sur un emplacement → revenu à récupérer au collecteur → argent pour améliorer la machine, débloquer des emplacements, rebirth… Carte au sol (pas d'îles flottantes) : 7 bases en étoile autour d'un Hub (Sanctuaire Mère).

- **Map (dans la place Studio, pas dans Rojo ni dans git)** : Model `Workspace.BaseJoueur` (tag `BaseJoueur`, PrimaryPart `Centre`, prévu pour être dupliqué autour du Hub) :
  - `Zone Joueur` (enclos délimité par des `Barrière`, entrée au milieu du côté avant), `Sol`, `Allee` (de l'entrée au cube RNG) ;
  - `RNG` : cube de la machine gacha au fond, en face de l'entrée, tag `MachineRNG` ;
  - `Emplacements/Emplacement1..10` : cases des personnages (attribut `Index`), impairs à gauche, pairs à droite, 1-2 près de l'entrée ;
  - `Collecteur` : dalle dorée (tag `Collecteur`) à droite de l'allée près de l'entrée ;
  - `Podium` à gauche de l'entrée, `Panneau` (TextLabel `NomProprietaire`) à droite, `PointApparition` devant l'entrée ;
  - sauvegardes des états précédents dans `ServerStorage.Sauvegarde_*`.
- **Hub (maquette grise)** : Model `Workspace.Hub` (tag `Hub`, PrimaryPart `Centre` en (-14, 1.5, 0), aligné sur `BaseJoueur`) : `Plateau` (cylindre r = 70), `PlaceCentrale`, `Piedestal` (attribut `Role`), `Chemins/Chemin1..7` (attribut `Index`, Chemin1 = base existante vers -Z), `EmplacementsBases/Base1..7` (pièces invisibles = CFrame du `Centre` de chaque copie de `BaseJoueur`), `Stands/Stand<Id>` (attribut `Stand` : `Evolutions`, `Etoiles`, `Ateliers`, `Recyclage` ; `Comptoir`, `PNJ` provisoire, `Enseigne`), `Classements`.
- **Limite de carte** : anneau `Wall` (18 `Mur`) + `Wall_Grass` centré sur le Hub, face intérieure à ≈ 254 studs (bases jusqu'à ≈ 236) ; sol `Base` / `Baseplate` centrés sur le Hub. État d'avant dans `ServerStorage.Sauvegarde_AvantRecentrageMurs`.
- **Code en place** : boucle de base jouable en solo (1 base) avec interface (HUD, carte de tirage, inventaire poser/retirer, notifications). Modèles 3D : seulement `nami` (`ReplicatedStorage.ModelesPersonnages.<Id>`, dans la place, faits avec le skill `/perso-r6`) ; les autres personnages restent des blocs colorés. Pas encore de déblocage d'emplacements, de machine améliorable, de rebirth.

## Code serveur
`src/server/init.server.luau` est le seul Script : il initialise les services (ModuleScripts) dans l'ordre :
- `DataService` : chargement/sauvegarde, leaderstats `Argent`, seules fonctions qui modifient les données.
- `BaseService` : attribue une base libre (tag `BaseJoueur`) au chargement des données, panneau, apparition, affichage des personnages posés (clone de `ModelesPersonnages.<Id>` tourné vers l'allée, animation `AnimationIdle` en boucle ; bloc coloré si pas de modèle) ; `GetProprietaire(instance)` pour vérifier la possession.
- `GachaService` : ProximityPrompt sur chaque `MachineRNG`, tirage serveur (propriétaire, distance, cooldown = `DureeAnimation`). En Studio : `ServerStorage.TestTirage` (BindableFunction) pour tester.
- `InterfaceService` : lien avec l'interface client. Envoie inventaire, résultat de tirage, collectes, notifications ; RemoteFunctions `Poser` / `Retirer` validées (type, possession, cadence).
- `RevenuService` : revenu chaque seconde → `ArgentNonCollecte`, collecte au toucher du `Collecteur` ; attributs du Player `ArgentNonCollecte` / `RevenuParSeconde` pour le HUD.
Config partagée (données uniquement) : `src/shared/Personnages.luau`, `GachaConfig.luau`, `Economie.luau` (formule de revenu).
`src/shared/Remotes.luau` : noms et types de toutes les remotes (`ReplicatedStorage.Remotes`, créées d'un coup par le serveur). Ajouter une remote = l'ajouter au type **et** à la liste `EVENEMENTS` / `FONCTIONS`.

## Code client
`src/client/init.client.luau` crée le ScreenGui `Interface` (construit en code, pas dans Studio) et branche les remotes :
- `Ui` : construction d'éléments, couleurs, police, `Ui.Adapter` (UIScale selon la taille d'écran, base 1100 × 650), format des nombres (`1,23K`).
- `Hud` (argent, revenu, à collecter, « +X $ »), `Tirage` (carte suspense puis révélation, dans `GachaConfig.DureeAnimation`), `Inventaire` (grille, Poser / Retirer), `Notifications`.
- Police `FredokaOne` : certains symboles (✕) n'existent pas, vérifier à l'écran.

## Données sauvegardées
DataStore `PlayerData`, clé `Player_<UserId>`, format v2 (type `PlayerData` dans `src/server/DataService.luau`) :
`{ Version, Argent, ArgentNonCollecte, Personnages = {[uid] = {Id, Etoiles}}, Emplacements = {[index texte] = uid}, EmplacementsDebloques, NiveauMachine, Rebirths, ProchainUid }`.
`lireDonnees` migre les anciennes versions et valide chaque champ ; une sauvegarde de version plus récente ou de type inattendu n'est ni chargée ni écrasée. Les sauvegardes d'un même joueur sont sérialisées et `BindToClose` attend celles en cours.
**À faire avant publication** : verrou de session (ProfileStore ou verrou maison) pour éviter qu'un joueur qui change vite de serveur écrase sa progression. Les `Id` de personnages sont sauvegardés : ne jamais les renommer après publication. En Studio, sans « Enable Studio Access to API Services », la partie tourne sans sauvegarde.

## Wiki de game design
`docs/wiki/` fait foi pour les règles du jeu (personnages, raretés, économie, rebirth, combats). Le lire avant de coder une mécanique.
Dès qu'une décision de game design est prise : mettre à jour la page concernée, ajouter une ligne au journal de `docs/wiki/README.md` et retirer la question de `Questions-ouvertes.md`. Ne jamais inventer une valeur : la marquer *(proposition)* ou **à définir**.

## Stack et commandes
Rojo 7.7.1, selene, StyLua, gérés par Rokit (`rokit.toml`). Modèles 3D : Blender.

```
rojo serve                          # synchro VS Code → Studio (plugin Rojo)
rojo build -o GameRoblox.rbxlx      # construit le fichier place
rojo sourcemap -o sourcemap.json    # pour Luau LSP
selene src                          # lint
stylua src                          # formatage
```

## Architecture (`default.project.json`)
| Dossier | Dans Studio | Contenu |
|---|---|---|
| `src/server` | `ServerScriptService.Server` | Scripts serveur |
| `src/client` | `StarterPlayer.StarterPlayerScripts.Client` | LocalScripts |
| `src/shared` | `ReplicatedStorage.Shared` | ModuleScripts partagés |

Workspace (Baseplate), Lighting et SoundService sont définis dans `default.project.json` : `rojo serve` réapplique ces propriétés (Baseplate placée par `CFrame`, pas `Position`).

- Suffixes Rojo : `*.server.luau` → Script, `*.client.luau` → LocalScript, `*.luau` → ModuleScript. `init.server.luau` / `init.client.luau` : le dossier devient lui-même le script.
- VS Code est la source de vérité : ne pas créer de scripts depuis Studio dans les dossiers gérés par Rojo (ils peuvent être écrasés à la synchro).
- Conventions observées : indentation par tabulations, modules partagés qui `return` une valeur, extension `.luau` partout.

## Règles de code
- `--!strict` en tête de chaque nouveau fichier.
- APIs modernes : `task.wait` / `task.spawn` / `task.delay`, jamais `wait` / `spawn` / `delay`.
- Ne jamais faire confiance au client : valider côté serveur tous les arguments des RemoteEvents/RemoteFunctions (types, distances, cooldowns, possession). Tirages RNG, gains d'argent et achats sont calculés uniquement côté serveur.
- Ne pas modifier `Packages/` (dépendances externes).
- Demander avant de changer le format des données sauvegardées (DataStore).

## Workflow
- Après chaque modification : `selene <fichiers modifiés>`. Le formatage StyLua est appliqué automatiquement par un hook (`.claude/hooks/format-lua.ps1`).
- Environnement : Windows, PowerShell.
- Skills : `/nouveau-module`, `/audit-remotes`. Agent de relecture : `relecteur-roblox`.
- MCP `Roblox_Studio` (`.mcp.json`, serveur MCP intégré à Studio) : sert à inspecter Studio (Workspace, grayboxing, console). Le code reste écrit dans `src/`, jamais directement dans Studio via le MCP.

## Suivi des tâches
- Tiens à jour le fichier `docs/wiki/TODO.md` en permanence.
- Avant de commencer un travail, liste les étapes sous forme de cases à cocher (- [ ]).
- Coche chaque tâche (- [x]) dès qu'elle est terminée, et ajoute les nouvelles tâches découvertes en cours de route.
- Garde une section "En cours", une section "À faire" et une section "Terminé".
