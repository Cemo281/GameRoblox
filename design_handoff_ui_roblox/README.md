# Handoff : interface du jeu Roblox (GameRoblox)

Repo cible : `Cemo281/GameRoblox` (branche `master`). UI côté client en Luau (`src/client/Ui.luau`, `src/client/Hud.luau`).

## Overview
Refonte de l'interface du jeu : style « gacha moderne + manga », HUD avec offres et boutique, téléportation vers les stands du Hub, inventaire et index, animation de tirage, ainsi que de nouvelles mécaniques de progression et de rétention (améliorations de base, stats, roulette, potions, pass de saison, quêtes du jour).

## About the Design Files
Les fichiers `.dc.html` de ce dossier sont des **références de design en HTML**. Ce sont des prototypes qui montrent l'apparence et le comportement voulus, **pas du code à copier**. Le travail consiste à **les recréer dans Roblox Studio / Luau** avec les patterns existants du repo : ScreenGui, Frame, UIGradient, UIStroke, UICorner, TweenService, RemoteEvents et DataStore. Ouvre chaque fichier dans un navigateur pour voir et cliquer la maquette. Les valeurs exactes (couleurs, tailles, textes) sont dans les attributs `style` du HTML.

## Fidelity
**High-fidelity** pour les couleurs, la typographie, les formes et les états. Les maquettes PC font 1100 × 650 px. Convertis les tailles en `UDim2` (Scale) en partant de cette résolution, et ajoute un `UIScale` ou un `UIAspectRatioConstraint` pour le mobile. Tous les prix Robux, coûts, valeurs de bonus et chiffres de stats sont des **exemples (« R$ à définir »)** : ils doivent rester configurables dans un module de config partagé (`src/shared`).

## Ordre d'implémentation conseillé
1. Tokens de style (palette, polices, boutons) → `Ui.luau`
2. HUD v3 (sans les offres d'abord)
3. Téléportation et mini-carte du Hub
4. Inventaire et Index
5. Animation de tirage
6. Offres et boutique (HUD v3, idées 1a–1f)
7. Nouvelles mécaniques (idées 2a–2f)

## Screens / Views

### 1. Planche de style v2 — `Planche de style v2.dc.html`
Source de vérité du style. Elle contient : palette, gemmes de rareté, boutons (normal / survol / appui), boutons icônes 60 × 60, onglets, panneaux, rubans et effets manga.
- Panneaux : dégradé vertical `#2A2350 → #17132E`, contour `#0D0A1C` de 2 px, liseré intérieur blanc à 35–55 % d'opacité, filet doré `#FFD66B → transparent` de 2 px sous les titres.
- Boutons : dégradé vertical à 3 tons (clair 0 %, base 50 %, foncé 100 %), bande de reflet blanche sur les 48 % du haut (opacité 0,12–0,3), ombre portée pleine `0 3px 0`. Survol : `scale(1.05)` et luminosité un peu plus forte. Appui : `translateY(3px)` et ombre à 0. Transition 120 ms `cubic-bezier(.3,1.8,.5,1)` (rebond).
- Effets manga (lignes de vitesse, trames, cadres d'impact) **réservés** au tirage, à la téléportation et au rebirth.

### 2. HUD v3 offres — `HUD v3 offres.dc.html` (+ `MiniCarteHub2.dc.html`)
HUD PC 1100 × 650, avec une variante mobile dans le même fichier.
- Barre de gauche : boutons icônes (Boutique, Inventaire, Index, Téléportation…). Raccourcis Hub, Évolutions et Étoiles en haut.
- Compteur d'argent en haut, avec la liasse de billets `icons/billets.png`. Les boosts actifs s'affichent sous l'argent (1f).
- Téléportation : panneau avec la mini-carte du Hub (MiniCarteHub2, 7 chemins espacés de 51,4°, ordre des stands repris de `docs/wiki/Hub.md`) et la liste des stands à droite. Survol d'un stand = surbrillance sur la carte ; clic = téléportation.
- Offres 1a–1f : pastille PROMO + minuteur sur Boutique (1a), encart « Offre du moment » refermable (1b), pack de départ après le 1er tirage (1c), Boutique avec passes (1d), bouton Cadeaux pour la connexion 7 jours et le temps de jeu (1e), boosts actifs sous l'argent (1f).
- Toasts de notification : succès (vert), argent (or), erreur (rouge).
- Les boutons « Simuler… » en haut de la page servent uniquement au prototype.

### 3. Inventaire et Index — `Inventaire et Index.dc.html`
Maquette 1100 × 650. Inventaire et Index s'ouvrent depuis la barre de gauche. Les données des personnages viennent de `src/shared/Personnages.luau`.

### 4. Tirage animé — `Tirage anime.dc.html` (+ `tirage-anim.jsx`, `animations-v3.jsx`)
Révélation du tirage : un rig R6 tout noir tourne sur lui-même, puis son liseré de rareté s'allume sur les bords, éclairé par le haut. Le minutage et les étapes sont dans `tirage-anim.jsx` (liste des scènes). Dans Roblox : ViewportFrame + TweenService, avec le résultat tiré **côté serveur** avant le lancement de l'animation. Chances : 60 / 25 / 10 / 4,9 / 0,1 % (voir `docs/wiki/Machine-RNG.md`).

### 5. Idées offres et promotions — `Idees offres et promotions.dc.html`
Section 2 (en haut), nouvelles mécaniques :
- **2a Améliorations de la base** : 3 améliorations (chance de tirage, chance étoile, argent par seconde), 5 niveaux chacune, payées en argent du jeu. Chaque ligne affiche : icône, nom, NIV. x / 5, pastilles de niveau, effet « actuel → suivant », bouton Améliorer (vert) ou Max (désactivé). Niveaux sauvés en DataStore, bonus appliqués côté serveur.
- **2b Mes stats** : bouton icône sous l'argent qui ouvre un panneau en verre (blanc à 16 % + flou). On y trouve les bonus actifs (somme base + potions + passes) et une grille 3 × 3 de compteurs : heures de jeu, tirages, meilleur tirage, argent gagné, étoiles obtenues, index, rebirths, jours connecté, quêtes finies. Une icône « stats » dédiée reste à créer.
- **2c Roulette de la chance** : 8 cases. Tours **gratuits uniquement** : 1 par jour, plus 1 par quête du jour finie. Jamais payée en Robux, car le tirage payant au hasard pose problème pour le public de 8–14 ans. Résultat tiré côté serveur ; la roue tourne 3,2 s `cubic-bezier(.17,.67,.2,1)` et s'arrête sur la case gagnante.
- **2d Potions ×2** : argent ×2 et chance ×2, 15 min. Les potions du même type **s'additionnent en temps, pas en multiplicateur**. Une potion active devient une pastille de boost dans le HUD (1f). Achat via Developer Product, stock en DataStore.
- **2e Pass de saison** : une piste gratuite et une piste Premium, avec des paliers et une barre de progression. On progresse avec les quêtes et les tirages. Un perso exclusif au dernier palier.
- **2f Quêtes du jour** : 3 quêtes avec barre de progression et minuteur de renouvellement. Bouton Récupérer (vert) quand une quête est finie. Une quête finie donne un lot, un tour de roulette et des points de pass.
- Fond de ces cartes : dégradé `#6A4BD8 → #3FA8C8` (160°), panneaux en verre `rgba(255,255,255,.16)`, textes blancs. **Plus de bleu foncé.**

Section 1 (en bas) : idées d'offres 1a–1f, déjà intégrées au HUD v3.

Boucle de jeu visée : quêtes → tours de roulette et points de pass → potions → argent → améliorations de base → stats.

## Design Tokens
- Trait sombre (contours, ombres) : `#0D0A1C`
- Fond : `#16122A` · Panneau : `#2A2350 → #17132E` · Zone contenu : `#1C1738` (ancienne UI, remplacée dans les idées 2a–2f) · Liserés : `#5A4E9E` / `#3E3478`
- Texte : `#FFFFFF` · Texte discret : `#A9A2CC` / `#C9C3E6` · Filet doré : `#FFD66B`
- Or / argent : `#FFF0A8 · #FFC93C · #F29A12`
- Vert / gains : `#B6FFB0 · #5EE06A · #2FAE45` (texte `#0B2A10`)
- Principal : `#B49CFF · #7454F0 · #5235C4`
- Danger : `#FF8C96 · #F0414F · #C42234` · Pastille : `#FF7A92 → #F0244A`
- Raretés (clair · base · foncé) :
  - Commun : `#E4E3E6 · #A3A2A5 · #5C5B60`
  - Rare : `#6CC0FF · #0078FF · #003A80`
  - Légendaire : `#FFE98A · #FFBE00 · #8A5A00`
  - Mythique : `#EBA0FF · #C800FF · #5A0080`
  - Secret : `#FF9A9A · #FF2828 · #6E0606` (avec un reflet animé)
- Polices : **Fredoka One** pour les titres, boutons et nombres ; **Montserrat** 500–800 pour les textes et labels. Dans Roblox : `Enum.Font.FredokaOne` et `Enum.Font.Montserrat` (ou leurs équivalents `Font.new`).
- Contour du texte des titres : ombre de 1,5 px en `#0D0A1C` → `UIStroke` (Thickness 1,5–2, ApplyStrokeMode Contextual).
- Rayons : petites pastilles 6–8 px, boutons 10–12 px, panneaux 12–16 px.
- Ombres : pleines, sans flou, `0 3px 0 #0D0A1C` → Frame décalée de 3 px sous l'élément.

## State Management (serveur)
- DataStore joueur : argent, niveaux d'amélioration `{tirage, etoile, argent}`, stock de potions, potions actives (fin en timestamp), tours de roulette et date du dernier tour gratuit, progression des quêtes et date de renouvellement, palier du pass et possession du Premium, compteurs de stats (temps de jeu, tirages, meilleure rareté, argent gagné…).
- Tout calcul de chance, d'argent ou de récompense se fait **côté serveur**. Le client se contente d'afficher et d'animer.

## Assets
- `icons/` : anciennes icônes, dont **`icons/billets.png` (liasse de billets), l'icône d'argent à utiliser** (`piece.svg` n'est plus utilisée).
- `icons2/` : icônes v2 (boutique, cadenas, classements, étoile, fermer, index, base, teleport…).
- `img/` : renders des personnages.
À importer dans Roblox comme Decals / ImageLabels (en PNG).

## Files
- `Planche de style v2.dc.html`
- `HUD v3 offres.dc.html`
- `MiniCarteHub2.dc.html`
- `Inventaire et Index.dc.html`
- `Tirage anime.dc.html`, `tirage-anim.jsx`, `animations-v3.jsx`
- `Idees offres et promotions.dc.html`
- `support.js`, `image-slot.js`, `tweaks-panel.jsx` : moteur du prototype, à ignorer pour l'implémentation.
