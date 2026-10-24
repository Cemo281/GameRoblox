---
name: nouveau-module
description: Crée un nouveau module Luau (serveur, client ou partagé) en suivant l'architecture Rojo du projet, puis lance selene. Usage - /nouveau-module <serveur|client|partagé> <NomDuModule> [description]
argument-hint: <serveur|client|partagé> <NomDuModule> [description]
---

# Nouveau module

Arguments : `$ARGUMENTS`

## 1. Interpréter les arguments
- 1er argument = emplacement :
  - `serveur` → `src/server/` (Studio : `ServerScriptService.Server`)
  - `client` → `src/client/` (Studio : `StarterPlayer.StarterPlayerScripts.Client`)
  - `partagé` / `partage` / `shared` → `src/shared/` (Studio : `ReplicatedStorage.Shared`)
- 2e argument = nom du module en PascalCase (ex. `GachaService`, `RarityConfig`).
- Le reste = description de ce que fait le module.
- Si l'emplacement ou le nom manque ou est ambigu, demander avant de créer quoi que ce soit.

## 2. Vérifier avant de créer
- Lire `CLAUDE.md` et `default.project.json` pour confirmer le mapping.
- Vérifier qu'aucun fichier du même nom n'existe déjà (Glob `src/**/<Nom>*`). S'il existe, s'arrêter et demander.
- Regarder les fichiers voisins pour reprendre leurs conventions.

## 3. Créer le fichier
- Nom : `<Nom>.luau` (ModuleScript). Ne créer un `.server.luau` / `.client.luau` que si l'utilisateur demande explicitement un script exécutable.
- Squelette :

```luau
--!strict
-- <Nom> : <description en une phrase>

local ReplicatedStorage = game:GetService("ReplicatedStorage")

local <Nom> = {}

-- Types exportés si utile
-- export type Foo = { ... }

function <Nom>.Init()
end

return <Nom>
```

- Règles : `--!strict`, services via `game:GetService`, `task.*` uniquement (jamais `wait`/`spawn`/`delay`), types annotés sur les fonctions publiques, indentation par tabulations.
- Module serveur qui écoute des Remotes : valider chaque argument client (types, distances, cooldowns, possession).
- Module client : aucune logique d'autorité (argent, RNG, inventaire) — seulement de l'affichage et des requêtes au serveur.

## 4. Vérifier
- Lancer `selene <chemin du fichier>` et corriger les problèmes signalés dans ce fichier.
- Indiquer à l'utilisateur : le chemin créé, l'emplacement dans Studio, et comment le `require` depuis un autre script.
