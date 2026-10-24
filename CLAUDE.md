# GameRoblox

## Le jeu
Jeu Roblox Idle / Simulator / Gacha (RNG) sur le thème des cartes d'animé, avec des modèles 3D animés de personnages.

- **Boucle** : les animations des personnages rapportent de l'argent passivement → l'argent sert à améliorer la machine RNG (gacha), acheter des packs et augmenter les taux de rareté. Les combats utilisent aussi les animations.
- **Carte** : îles célestes en organisation radiale.
  - **Hub central (Sanctuaire Mère)** : zone sociale et marchande (ateliers d'amélioration globale, recyclage/vente, classements, piédestal d'événement).
  - **Bases joueurs** : îlots satellites reliés au Hub (machine RNG à l'entrée, enclos central de ferme passive, podiums d'exposition).
- **État** : grayboxing d'une base joueur dans Studio (placés à la main dans Workspace, pas dans Rojo) : le Model `Zone Joueur` (enclos délimité par des `Barrière`), avec à l'entrée le Part `RNG` (cube de la machine gacha) et le Model `Podium` (Podium1-3). Monnaie `Argent` en place (`DataService`). Le système de tirage (`GachaSystem`, raretés Commun/Rare/Légendaire) est à créer.

## Données sauvegardées
DataStore `PlayerData`, clé `Player_<UserId>`, valeur `{ Version: number, Argent: number }` (type `PlayerData` dans `src/server/DataService.luau`). Toute lecture/modification de l'argent passe par `DataService.GetArgent / AddArgent / SpendArgent` côté serveur. En Studio, sans « Enable Studio Access to API Services », la partie tourne sans sauvegarde.

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
