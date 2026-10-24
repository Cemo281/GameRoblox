# GameRoblox

## Le jeu
Jeu Roblox Idle / Simulator / Gacha (RNG) sur le thème des cartes d'animé, avec des modèles 3D animés de personnages.

- **Boucle** : les animations des personnages rapportent de l'argent passivement → l'argent sert à améliorer la machine RNG (gacha), acheter des packs et augmenter les taux de rareté. Les combats utilisent aussi les animations.
- **Carte** : îles célestes en organisation radiale.
  - **Hub central (Sanctuaire Mère)** : zone sociale et marchande (ateliers d'amélioration globale, recyclage/vente, classements, piédestal d'événement).
  - **Bases joueurs** : îlots satellites reliés au Hub (machine RNG à l'entrée, enclos central de ferme passive, podiums d'exposition).
- **État** : grayboxing d'une base joueur dans Studio (construite dans la place, pas dans Rojo ni dans git), Model `Workspace.BaseJoueur` (PrimaryPart `Centre`, pour être dupliqué autour du Hub) :
  - `Zone Joueur` (enclos délimité par des `Barrière`, entrée au milieu du côté avant), `Sol`, `Allee` (de l'entrée au cube RNG) ;
  - `RNG` : cube de la machine gacha au fond, en face de l'entrée, tagué `MachineRNG` (CollectionService) ;
  - `Emplacements/Emplacement1..10` : cases pour poser les personnages gagnés (attribut `Index`), 5 de chaque côté de l'allée (impairs à gauche, pairs à droite, 1-2 près de l'entrée) ;
  - `Podium` (Podium1-3) à gauche de l'entrée, `Panneau` (TextLabel `NomProprietaire`) à droite, `PointApparition` devant l'entrée ;
  - sauvegarde de l'état précédent : `ServerStorage.Sauvegarde_AvantBaseJoueur`. Monnaie `Argent` en place (`DataService`). Tirage de test en place : `GachaSystem.server.luau` (ProximityPrompt sur `RNG`, bloc coloré par rareté), réglages dans `src/shared/GachaConfig.luau` (prix et chances PROVISOIRES, gameplay pas encore défini). `RevenuTest.server.luau` (+1 Argent/s) est provisoire, à supprimer quand la ferme passive sera codée.

## Données sauvegardées
DataStore `PlayerData`, clé `Player_<UserId>`, valeur `{ Version: number, Argent: number }` (type `PlayerData` dans `src/server/DataService.luau`). Toute lecture/modification de l'argent passe par `DataService.GetArgent / AddArgent / SpendArgent` côté serveur. En Studio, sans « Enable Studio Access to API Services », la partie tourne sans sauvegarde.

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

Workspace (Baseplate), Lighting et SoundService sont définis dans `default.project.json`.

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
