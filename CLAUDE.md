# GameRoblox

## Le jeu
Jeu Roblox Idle / Simulator / Gacha (RNG) sur le thème des cartes d'animé, avec des modèles 3D animés de personnages.

Règles détaillées : voir le wiki (`docs/wiki/`). Résumé : tirage gratuit → personnage (rareté + étoiles) posé sur un emplacement → revenu à récupérer au collecteur → argent pour améliorer la machine, débloquer des emplacements, rebirth… Carte = une seule île volante : 7 bases en étoile autour d'un Hub (Sanctuaire Mère).

- **Map (dans la place Studio, pas dans Rojo ni dans git)** : Model `Workspace.BaseJoueur` (tag `BaseJoueur`, PrimaryPart `Centre`, prévu pour être dupliqué autour du Hub) :
  - `Zone Joueur` (enclos délimité par des `Barrière`, entrée au milieu du côté avant), `Sol`, `Allee` (de l'entrée au cube RNG) ;
  - `RNG` : cube de la machine gacha au fond, en face de l'entrée, tag `MachineRNG` ;
  - `Emplacements/Emplacement1..10` : cases des personnages (attribut `Index`), impairs à gauche, pairs à droite, 1-2 près de l'entrée ;
  - `Collecteur` : dalle dorée (tag `Collecteur`) à droite de l'allée près de l'entrée ;
  - `Podium` à gauche de l'entrée, `Panneau` (TextLabel `NomProprietaire`) à droite, `PointApparition` devant l'entrée ;
  - sauvegardes des états précédents dans `ServerStorage.Sauvegarde_*`.
- **Hub (décor « sanctuaire de festival animé » v1, voir `docs/wiki/Hub.md`)** : Model `Workspace.Hub` (tag `Hub`, PrimaryPart `Centre` en (-14, 1.5, 0), aligné sur `BaseJoueur`) : `Plateau` (cylindre r = 70), `PlaceCentrale`, `Piedestal` (attribut `Role`), `Chemins/Chemin1..7` (attribut `Index`, Chemin1 = base existante vers -Z), `EmplacementsBases/Base1..7` (pièces invisibles = CFrame du `Centre` de chaque copie de `BaseJoueur`), `Stands/Stand<Id>` (attribut `Stand` : `Evolutions`, `Etoiles`, `Ateliers`, `Recyclage` ; `Comptoir`, `PNJ` provisoire, `Enseigne`), `Classements`, `Decor` (purement visuel : sol, centre et cœur flottant, torii, habillage des stands, cerisiers, bancs ; état d'avant dans `ServerStorage.Sauvegarde_AvantDecorHub`).
- **Île volante** : Model `Workspace.Ile` (construit par `assets/ile/construire_ile.luau`, lancé par MCP, relançable), centré sur le Hub : `Dessus.Sol` (cylindre d'herbe r = 265, dessus à y = 1, seul sol marchable), `Bordure` (muret bas), `Dessous` (strates, rochers, pointes), `Cristaux`, `Decor` (dessus, par `assets/ile/decorer_ile.luau`, relançable : ≈ 3 100 pièces, laisse libres le Hub, les 7 `EmplacementsBases` et les chemins), `MursInvisibles` (48 pièces, Transparency 1, hauteur 120, juste derrière le muret). Plus de `Baseplate` (retiré de `default.project.json`). Anciens `Wall` / `Wall_Grass` / `Base` / `Baseplate` dans `ServerStorage.Sauvegarde_AvantIleVolante`. Dessous : mer en eau du Terrain (surface y = -380, 8192 × 8192 studs, `assets/ile/construire_mer.luau`).
- **Code en place** : boucle de base jouable en solo (1 base) avec interface (HUD, carte de tirage, inventaire poser/retirer, notifications). Modèles 3D (`ReplicatedStorage.ModelesPersonnages.<Id>`, dans la place) : `nami` (skill `/perso-r6`, Idle seule) et `zoro` (skill `/perso-roblox`, R15 habillé, accessoires, 3 animations de vitrine, VFX ; sources dans `assets/persos/zoro/`) ; les autres personnages restent des blocs colorés. Pas encore de déblocage d'emplacements, de machine améliorable, de rebirth.

## Code serveur
`src/server/init.server.luau` est le seul Script : il initialise les services (ModuleScripts) dans l'ordre :
- `DataService` : chargement/sauvegarde, leaderstats `Argent`, seules fonctions qui modifient les données.
- `BaseService` : attribue une base libre (tag `BaseJoueur`) au chargement des données, panneau, apparition, affichage des personnages posés (clone de `ModelesPersonnages.<Id>` tourné vers l'allée, tagué `PersonnageVitrine` ; vitrine en boucle `AnimationIdle` → `AnimationAction` → `AnimationSignature` avec 2 s de pause, dernière image figée ; Idle seule si pas d'Action ; si l'attribut `AnimationSequence` existe, cette seule animation en boucle (pause de 2 s) à la place du cycle, avec arrêt sur image de 0,06 s à chaque marqueur `Impact` ; bloc coloré si pas de modèle ; Animator cherché dans l'AnimationController puis le Humanoid) ; `GetProprietaire(instance)` pour vérifier la possession.
- `GachaService` : ProximityPrompt sur chaque `MachineRNG`, tirage serveur (propriétaire, distance, cooldown = `DureeAnimation`). En Studio : `ServerStorage.TestTirage` (BindableFunction) pour tester, `ServerStorage.TestDonnerPersonnage` (player, id, étoiles) pour ajouter un perso précis à l'inventaire.
- `InterfaceService` : lien avec l'interface client. Envoie inventaire, résultat de tirage, collectes, notifications ; RemoteFunctions `Poser` / `Retirer` validées (type, possession, cadence).
- `RevenuService` : revenu chaque seconde → `ArgentNonCollecte`, collecte au toucher du `Collecteur` ; attributs du Player `ArgentNonCollecte` / `RevenuParSeconde` pour le HUD.
Config partagée (données uniquement) : `src/shared/Personnages.luau`, `GachaConfig.luau`, `Economie.luau` (formule de revenu), `ImagesPersonnages.luau` (IDs des images d'interface).
`src/shared/Remotes.luau` : noms et types de toutes les remotes (`ReplicatedStorage.Remotes`, créées d'un coup par le serveur). Ajouter une remote = l'ajouter au type **et** à la liste `EVENEMENTS` / `FONCTIONS`.

## Code client
`src/client/init.client.luau` crée le ScreenGui `Interface` (construit en code, pas dans Studio) et branche les remotes :
- `Ui` : construction d'éléments, couleurs, police, `Ui.Adapter` (UIScale selon la taille d'écran, base 1100 × 650), format des nombres (`1,23K`).
- `Hud` (argent, revenu, à collecter, « +X $ »), `Tirage` (carte suspense puis révélation, dans `GachaConfig.DureeAnimation` : cadre de la rareté, silhouettes pendant le suspense, grille Idle animée à la révélation, reflet pour Secret), `Inventaire` (grille de cartes avec cadre et portrait, Poser / Retirer), `Notifications`.
- `Images` : cadres de rareté, portraits, grille Idle animée (`ImageRectOffset`, une boucle Heartbeat), reflet Secret (CanvasGroup), préchargement. IDs dans `src/shared/ImagesPersonnages.luau`, recopiés des `assets/gui/*/infos.json` (`ids_roblox`) ; un perso sans images garde le bloc coloré avec son initiale.
- `DecorAnime` : animations visuelles du décor, côté client (tags `DecorTournant` : attribut `Vitesse` en °/s ; `DecorFlottant` : `Amplitude`, `Periode`) ; utilisé par le cœur du Hub.
- `Vitrine` : sur les modèles tagués `PersonnageVitrine`, applique les marqueurs des animations jouées par le serveur (`Montrer` / `Cacher` un accessoire, `VFX` du dossier `VFX` du modèle : Mode `Burst` → Emit(`Quantite`), `Duree` → allumé `Duree` s (émetteurs, traînées, faisceaux et lumières), `<Nom>_Fin` éteint ; Mode `Eteindre` + `Cible` ; en `Burst`, les lumières s'allument `DureeFlash` s ; attributs `Secousse` (caméra des joueurs à moins de 40 studs) et `Fantome` (Color3, image rémanente) ; les marqueurs `Impact` / `Esquive` / `Aura` / `Explosion` / `Fin` déclenchent l'effet `<Marqueur>_<Valeur>` s'il existe ; chaque piste n'est branchée qu'une fois, le serveur la relance à chaque cycle). Le serveur lit l'attribut `HitStop` de `VFX.Impact_<valeur>` pour l'arrêt sur image. Côté client car `Emit` n'est pas répliqué. ⚠ L'Éditeur d'animation ne publie qu'**un marqueur de chaque nom par image clé** : deux `VFX` (ou deux `Cacher`) au même instant → un seul survit.
- Séquence du sabreur (vitrine de zoro) : sources dans `assets/persos/zoro/sabreur/` (`anims.js` = source de vérité des poses, visualiseur `Sabreur Animations.dc.html`). `adapter_sequences.py` génère `creer_sequences.luau` (5 KeyframeSequence sur `Workspace.Sabreur_Apercu`, marqueurs renommés vers `Acc_Sabre_*` et marqueurs `VFX` ajoutés) ; `vfx_sabreur.luau` crée les effets `Sabreur_*` de `zoro.VFX`. Les deux scripts sont relançables par MCP.
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

## Garde-fou : charte de Roblox (compte déjà sanctionné)
Historique : avertissement le 29/10/2026, ban d'un jour le 31/10/2026, à cause d'images envoyées par le MCP. Les sanctions s'aggravent (3 jours, 7 jours, puis suppression du compte).

**Règle : avant toute action qui pourrait enfreindre la charte de Roblox, s'arrêter et demander à l'utilisateur.** Dire en une ou deux lignes ce qui va être fait, pourquoi c'est risqué et proposer une alternative plus sûre ; attendre sa réponse. Ne jamais contourner un refus (autre outil, script `execute_luau`, autre nom de fichier). Dans le doute, demander.

Actions concernées :
- **Envoi de contenu à Roblox** (images, textures, decals, meshes, sons, animations, `upload_image`, `store_image`, `generate_*`, `AssetService` dans un script) : toujours annoncer quoi et pourquoi avant. Demander obligatoirement si le contenu montre :
  - de la peau ou de l'anatomie : torse nu, ventre, nombril, abdos, muscles, veines, poitrine, fesses, cicatrices ou blessures ;
  - des tenues révélatrices (bikini, sous-vêtements, maillot), une pose ou un cadrage suggestif ;
  - du sang, du gore, des armes réalistes, de la drogue, de l'alcool, du tabac ;
  - du texte (insulte, mot ambigu dans une autre langue, lien, nom d'un autre jeu ou réseau social), un symbole qui peut être mal lu ;
  - un logo, une image ou une musique pris tels quels d'une œuvre protégée (anime, marque).
- **Personnages d'animé existants** : noms, visuels et textures très fidèles à une licence = risque de réclamation DMCA (strike sur le compte) ; le signaler quand on publie ou rend public.
- **Gacha et argent réel** : tout tirage, boîte ou bonus aléatoire payé en Robux (Developer Product, Game Pass) doit afficher les chances avant l'achat ; récompenses contre un avis, un like ou un abonnement interdites ; demander avant d'ajouter un achat Robux.
- **Texte écrit par les joueurs** (noms de base, messages, recherche) : filtré par `TextService:FilterStringAsync` avant d'être montré aux autres ; demander avant d'ajouter un champ de saisie libre.
- **Assets de la Toolbox / insert_asset** : peuvent contenir des scripts cachés (backdoor) ou du contenu non conforme ; inspecter et demander avant d'insérer.
- **Publication** de la place ou passage en public, questionnaire de maturité, réglages de confidentialité.

Ce qui ne demande pas d'accord : le code, la géométrie et les textures neutres (vêtements couvrants, décor, effets abstraits), les articles du catalogue déjà approuvés par Roblox.

Les outils MCP d'envoi et de génération sont en `ask` dans `.claude/settings.json` : Claude Code demande confirmation à chaque appel.

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
