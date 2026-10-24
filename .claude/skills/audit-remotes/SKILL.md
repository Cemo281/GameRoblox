---
name: audit-remotes
description: Liste toutes les RemoteEvents/RemoteFunctions du projet et signale celles dont les entrées client ne sont pas validées côté serveur. Lecture seule, produit un rapport.
allowed-tools: Read, Grep, Glob
---

# Audit des Remotes (lecture seule)

Ne modifier AUCUN fichier. Produire uniquement un rapport.

## 1. Recenser
Chercher dans `src/` et `default.project.json` :
- Créations : `Instance.new("RemoteEvent")`, `"RemoteFunction"`, `"UnreliableRemoteEvent"`, et les `$className` de ces types dans les `*.project.json` / `*.model.json`.
- Récupérations : `WaitForChild`/`FindFirstChild` avec des noms de remotes, dossiers `Remotes`/`Events`/`Network`.
- Côté serveur : `.OnServerEvent:Connect`, `.OnServerInvoke =`.
- Côté client : `:FireServer(`, `:InvokeServer(`, `.OnClientEvent`, `.OnClientInvoke`.

Associer chaque remote à son handler serveur et à ses appels client.

## 2. Vérifier chaque handler serveur
Le premier paramètre est toujours le `player` (fourni par Roblox, fiable). Tous les autres viennent du client et ne sont pas fiables. Vérifier :
- **Types** : `typeof(arg) == "..."` pour chaque argument ; nombres finis (pas NaN/inf : `x == x` et `math.abs(x) ~= math.huge`) ; bornes min/max ; chaînes de longueur limitée.
- **Existence / possession** : l'objet visé existe et appartient bien à ce joueur (personnage, base, inventaire).
- **Distance** : le joueur est assez proche de l'objet (machine RNG, stand, podium…).
- **Cooldown / rate limit** : limitation par joueur des appels répétés.
- **Autorité** : prix, gains, résultats de tirage RNG calculés par le serveur, jamais reçus du client.
- **OnClientInvoke** utilisé par le serveur (InvokeClient) : risque de blocage → signaler.
- **OnServerInvoke** : erreurs non gérées / valeurs retournées sensibles.

## 3. Rapport
Tableau :

| Remote | Fichier:ligne (handler) | Arguments client | Types | Possession | Distance | Cooldown | Gravité |
|---|---|---|---|---|---|---|---|

Gravité : 🔴 critique (argent/RNG/inventaire contrôlé par le client), 🟠 moyen (validation partielle), 🟢 OK.
Puis, pour chaque 🔴/🟠 : une phrase sur le risque (comment un exploiteur en profiterait) et la correction suggérée (sans l'appliquer).
Signaler aussi les remotes sans handler serveur et les handlers sans remote correspondante. Si aucune remote n'existe, le dire simplement.
