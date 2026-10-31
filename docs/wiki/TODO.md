# TODO

Suivi des tâches de développement. Les décisions de game design en attente sont dans [Questions ouvertes](Questions-ouvertes.md).

## En cours
### Décor du Hub, style animé « sanctuaire de festival » (place Studio, pièces seulement, sans Blender)
- [x] Sauvegarde du Hub actuel dans `ServerStorage.Sauvegarde_AvantDecorHub`
- [x] Sol : plateau, place centrale et chemins en SmoothPlastic pastel (tons moyens : l'éclairage brûle les teintes claires), bordure du plateau ouverte aux chemins, liserés et dalles rondes sur les chemins
- [x] Centre : estrade à gradins autour du piédestal (piédestal passé en SmoothPlastic doré + liseré Neon), 4 lanternes, cœur lumineux flottant à y = 36 (orbites, étincelles, rayon)
- [x] Torii vermillon à l'arrivée des 7 chemins + 2 lanternes de pierre chacun
- [x] Stands façon yatai (toit rayé, lambrequin, chochin, noren, caisses) ; couleurs des comptoirs / enseignes adoucies
- [x] 12 cerisiers (pétales en particules), 2 bancs circulaires, 7 bancs autour de la place
- [x] Cadre du panneau de classements (toit noir, linteau vermillon, cadre doré)
- [x] Captures et vérification (passages libres, 846 pièces dans `Hub.Decor`)
- [x] Wiki : section « Direction artistique » dans `Hub.md` + journal
- [ ] Valider la direction artistique (utilisateur) et enregistrer la place (Ctrl+S, hors git)
- [x] Éclairage (place Studio, hors Rojo) : OutdoorAmbient 249,201,255 → 190,172,206 ; ColorCorrection luminosité 0,10 → 0,02, contraste 0,25 → 0,12, saturation 0,10 → 0,18, teinte 255,248,250 ; Bloom intensité 1 → 0,6, seuil 2 → 1,6 (bases plus lisibles aussi)
- [x] Blender (accord reçu) : `assets/hub/decor_hub.py` (lancé en arrière-plan, sans toucher le Blender ouvert) → `fbx/decor_hub.fbx`, `palette_hub.png`, `decor_hub.json`, `apercu/ensemble.png` : CerisierA / B (≈ 4 300 tri.), Torii courbé (4 248), LanternePierre (2 542), Chochin (840) ; ombrage peint dans une palette en dégradés, sans traits noirs
- [x] Cerisier v2 (retour : « trop chewing-gum, pas assez arbre ») : tronc noueux fourchu en 4 branches et 8 rameaux visibles, touffes séparées et étagées en dôme (dessous aplati, bosselées, facettes peintes), rose moins bonbon ; ≈ 7 100 triangles
- [ ] Import de `assets/hub/fbx/decor_hub.fbx` dans Studio (manuel)
- [ ] Remplacer les pièces provisoires par les MeshParts (torii, lanternes de pierre, cerisiers, chochin), gabarits dans `ServerStorage.Gabarits.DecorHub`
- [x] `src/client/DecorAnime.luau` : tags `DecorTournant` (orbites, attribut `Vitesse`) et `DecorFlottant` (cœur, `Amplitude`, `Periode`), testé en Play

### Calibration R15 pour `/perso-catalogue` (Studio seulement, fichiers dans `assets/persos/_rig/`)
- [x] Avatar R15 de test créé en mode édition (`CreateHumanoidModelFromDescription`) : articulations = AnimationConstraint, pas de Motor6D
- [x] Relevé des 15 articulations et 16 pièces → `r15.json` (identique à `_mannequin/releve_brut.json`)
- [x] 45 cas (+30° X/Y/Z) et pose test → `axes_r15.json` (mêmes signes que la calibration du mannequin)
- [ ] Chaîne JSON → KeyframeSequence → aperçu sur clones (coucou du bras droit, 2 s)
- [ ] Vérification dans l'éditeur d'animation (manuel)
- [ ] Ranger l'avatar dans `ServerStorage.Gabarits.AvatarTestR15`, supprimer le reste

### Personnage `luffy` (skill `/perso-catalogue`, Mythique, fichiers dans `assets/persos/luffy/`)
- [x] 1. Fiche reformulée et validée (référence prioritaire : chemise à manches courtes, revers blancs ; chapeau sur la tête)
- [x] 2. Recherche catalogue → `catalogue.md` + `catalogue/planche*.png`
- [x] 2b. Choix : catalogue (chapeau, cheveux, viande) + modèle Toolbox 16939724553 (visage, écharpe, short avec revers et sandales)
- [x] 4. Chemise sur mesure dans Blender : `chemise_luffy.py` + `peindre_chemise_luffy.py` → `chemise_luffy.blend`, `fbx/chemise_luffy.fbx`, `chemise_luffy.json` (tailles, décalages)
- [x] 4. Chemise v2 détaillée (image fournie) : plis en relief, manches évasées froissées, ourlet ondulé, col roulé, revers ; ombrage cuit (Cycles, `cuisson/`) + plis peints ; 7 112 triangles, texture 2048
- [x] Chemise v3 : col roulé retiré, chemise allongée jusqu'au bas de LowerTorso (ourlet -1,02), ouverture élargie (0,30 → 0,50), 5 boutons, traits noirs effilés le long des plis, aplats d'ombre plus francs
- [x] Chemise v4 : traits noirs le long des plis retirés (pas naturels), contours en rouge sombre au lieu de presque noir ; `tex_chemise_luffy.png` repeinte
- [x] Texture rechargée dans `chemise_luffy.blend`, `fbx/chemise_luffy.fbx` réexporté (7 120 triangles, tailles inchangées)
- [x] Chemise v5 : 3 boutons au lieu de 5, ourlet à -1,32 (sous l'écharpe, haut des cuisses), manches longues jusqu'au coude + poignets à revers sur LowerArm (milieu de l'avant-bras) ; recuisson (2 min 45 s), 5 pièces, 9 880 triangles, `chemise_luffy.json` à jour
- [ ] Dans Studio : vérifier que le bas de la chemise (rigide sur UpperTorso) ne traverse pas trop les cuisses pendant les animations
- [ ] **Chemise refaite de zéro** (sur le vrai corps R15 exporté de Studio, les anciens fichiers `chemise_luffy*` restent jusqu'à validation) :
  - [x] Corps R15 bloc de `Workspace.AvatarTestR15` sélectionné dans Studio (15 MeshParts, sans HumanoidRootPart)
  - [x] Nouveau fichier `chemise_r15.blend` : copie de `chemise_luffy.blend` sans la chemise v5 (mannequin en blocs + torse peint seulement)
  - [x] Abdos retirés ; mannequin « Roblox parfait » (torse 2 × 2,1 × 1, hanches = tronc, bras 1 × 2,1 alignés en haut sur le torse, jambes 1 × 2,2) ; objet `veste` (LowerTorso + UpperTorso + 2 UpperArm) gonflé de 0,06 stud, matériau `Mat_Veste`
  - [x] Rig R15 GitHub (`Downloads/Rig15ik.blend`, vrais maillages Roblox, bones + Child Of) utilisé à la place de l'export Studio
  - [x] Veste sur ce rig : LowerTorso + UpperTorso + 2 UpperArm recousus, gonflés de 0,05 stud (0,08 jugé trop), coupés net (ourlet, bas des manches), Solidify 0,05, `Mat_Veste` rouge ; copie `assets/persos/luffy/chemise_rig15.blend` (sauvegarde cachée `veste_sauvegarde`)
  - [x] Torse de la veste d'un seul tenant : UpperTorso gonflé prolongé jusqu'au bas du LowerTorso (plus de rebord à la taille) ; version modifiée à la main gardée cachée (`veste_modifiee`)
  - [x] Réparations (trous de la manche droite, débris sous l'aisselle gauche, manches coupées au ras du flanc et fermées) ; bord en vagues arrondies irrégulières (torse 0,35-0,7 × 0,06-0,12 stud, manches 0,2-0,4 × 0,03-0,06), Solidify sans « even thickness » (pointes) ; copies cachées `veste_avant_reparation*`, `veste_avant_zigzag`
  - [x] **Chemise v6** (`chemise_v6.py`, d'après la référence fournie) : Chemise_Torse / MancheD / MancheG = copies des pièces du rig (suivent leurs os) ; torse ample ouvert devant (+Y = avant du perso), revers, patte et 4 boutons ; manches évasées au bas effiloché (vagues + déchirures) et plis en relief ; épaisseur 0,035 ; cuisson Cycles (≈ 5 min) + peinture numpy (`tex_chemise_v6.png`, plis peints, bord roulé, grain) ; 10 812 + 2 × 8 160 triangles
  - [x] Style anime testé (`peindre(anime=True)` → `tex_chemise_v6_anime.png`, 4 aplats) ; rendu peint sauvegardé (`tex_chemise_v6_peint.png`, `chemise_rig15_v6_peint.blend`)
  - [x] Ceinture + short v6 (`bas_v6.py`, style anime) : écharpe jaune serrée sur le LowerTorso (z 2,19 → 2,59, sous la chemise, visible dans l'ouverture), nœud au centre et 2 pans effilochés ; haut du short resserré sous la chemise (suit LowerTorso) ; short en jean évasé jusqu'au bas de la cuisse (z 1,10), écharpe peinte en 3 épaisseurs horizontales, plis, couture latérale, revers blanc duveteux (suit les UpperLeg) ; cuisson ≈ 5 min 30 ; `tex_bas_v6_anime.png` ; 6 504 + 2 × 8 064 triangles
  - [ ] Choisir le rendu final de la chemise (peint ou anime) avant export
  - [ ] Export FBX de la v6 (chemise + ceinture + short) (UV des faces intérieures vers la zone sombre), import et soudure dans Studio
  - [ ] (ancienne `veste`) son ouverture était percée dans le dos (-Y) : à abandonner au profit de la v6
  - [ ] Alléger la veste avant export : 207 936 triangles avec l'épaisseur (base subdivisée à 45 000 sommets), limite Roblox par MeshPart bien plus basse
  - [ ] Faire suivre les manches aux os des bras (aujourd'hui toute la veste suit LowerTorso)
- [x] Torse peint : `peindre_torse_luffy.py` → `torse_luffy.png` (décalque Front de UpperTorso : pectoraux, abdos, obliques, clavicules, cicatrice en X ; pas de nombril)
- [x] Torse en style anime : `peindre_torse_anime.py` → `torse_luffy_anime.png` (aplats en croissant, sans contours, X brun déchiqueté (branches effilées, éclats en V, pointes à ±0,46 en partie sous la chemise, branches fines), 4 abdos seuls en ombres et reflets translucides (la peau vient de la skin), pas de nombril) ; aperçu `Decal_Torse` dans `chemise_rig15.blend`
- [x] Pecs ajoutés au décalque anime (ombre en croissant sous chaque pec, reflet en haut, sillon central) ; image à renvoyer dans Studio (`Torse_Luffy`)
- [x] Images envoyées (torse 75774906927040, bas 109932566809619 ; chemise : 127883377469673 envoyée par l'import 3D, la 93829095451933 ne se charge pas) ; Decal `Torse_Luffy` sur UpperTorso
- [x] 4b. `export_v6.py` → `fbx/tenue_v6.fbx` + `tenue_v6.json` ; importé à la main ; 6 pièces soudées dans `luffy.Tenue` (meshes tournés de 180° autour de Y par l'import)
- [x] Manches v6 allongées à 0,12 sous le bas de UpperArm (`M_BAS` 0,25 → -0,12) et bas effiloché comme le bas du torse (larges vagues douces + 2 déchirures) ; recuisson (≈ 4 min) + `peindre(anime=True)` ; sauvegarde cachée `Chemise_Manche*_avant_allongement`
- [ ] Réexporter la tenue (`export_v6.py`), réimporter les 2 manches et la texture chemise dans Studio (IDs de `tenue.json` à mettre à jour)
- [x] Choix du torse : notre décalque (pas les articles du catalogue ni le Shirt Toolbox)
- [x] 3. Modèle `Workspace.luffy` (R15 blocs, peau #E8B48C, chapeau 13043540601, cheveux 13832918624, sandales 13753582199, visage Toolbox) ; `tenue.json` ; captures face / 3/4 / dos / profil
- [x] Écharpe : essai de celle du modèle Toolbox, puis retour à la Ceinture v6 (l'écharpe Toolbox est gardée dans `ServerStorage.Sauvegarde_luffy`)
- [x] Chapeau agrandi ×1,25 et un peu plus bas ; cheveux raccourcis (hauteur ×0,68) : plus rien ne dépasse
- [x] Abdos : Shirt classique du modèle Toolbox (template 13497309617, abdos + X + muscles des bras) ; notre Decal `Torse_Luffy` masqué
- [x] Nouvelle chemise (manches plus longues, réimport du 31/10) posée sur `luffy`, `luffy_essaiB`, `luffy_essaiC` ; import gardé dans `ServerStorage.Sauvegarde_luffy.tenue_v6_import2`
- [x] Tête : visage Toolbox, Black Spiky Hair taille d'origine, Pirate Straw Hat ×1,1 posé un peu plus haut (meilleur que 12993465889 et 13146004106, percés par les mèches) ; copies d'essai supprimées
- [x] Torse : Shirt Toolbox remis (`Shirt_Abdos`), décalque masqué ; tête : pièce cheveux + chapeau du Toolbox (`CheveuxChapeau`, 12678766775) à la place du Pirate Straw Hat et du Black Spiky Hair
- [ ] (abandonné pour l'instant) visage qui rit `visage_luffy_rire.png` : l'envoi 111985977929747 n'est pas servi par Roblox
- [ ] Vérifier les sandales (vêtement en couches : invisibles en mode édition) en mode Play
- [ ] 4. Éléments absents du catalogue (si besoin, Blender seulement avec accord)
- [ ] 5. Animations `luffy_Idle` / `luffy_Action` / `luffy_Signature` (nouvelle fiche : rire + moulinet, rafale + poing élastique, bras de Haki)
  - [x] Rig relevé dans Studio (`rig_luffy.json`, AnimationConstraint) ; `anims_luffy.py` (moteur de nami : IK, pieds plantés, `etirer` = translation de l'épaule le long du bras) ; `apercu_studio.py`, `vers_studio.py`
  - [x] Idle calculée (90 images, 20 clés) : main gauche au bord du chapeau, poing droit sur la hanche (coude sorti en arrière : vrai poing tourné vers l'intérieur impossible avec ce rig), rire, moulinet 2 tours, étirement en V
  - [x] Action calculée (150 images) : rafale 11 coups étirés de 1,5, charge genou levé, fente + bras étiré de 3 (poing à 5,7 studs du centre), LowerTorso 0,48 max ; marqueurs Rafale 20 / Charge_Poing 70 / Poing_Elastique 94 / Impact_Final 98
  - [x] Signature calculée (120 images) : marqueurs Montrer Acc_Haki 30 / Acc_Haki_Main 31, VFX Eclairs_Haki 30 / Onde_Haki 31 / Eclairs_Haki_Fin 90, Cacher 90 / 91
  - [x] Signature : buste tourné vers sa droite, le poing ne cache plus qu'une partie du visage (validé) ; main gauche sur le biceps = bras croisé (chevauchement ~0,3 avec le torse)
  - [x] Coordination avec l'autre session : passe `_anim/finition.py` gardée, chaque lancement écrit `luffy_<Nom>.json` (blocage) et `luffy_<Nom>_fini.json` (finie)
  - [x] KeyframeSequence de blocage `luffy_Idle/Action/Signature` dans `RBX_ANIMSAVES.luffy`, à côté des `*_fini` (comparaison) ; `vers_studio.py` envoie des angles (3× plus court)
  - [x] Choix : version finie. Les 3 KeyframeSequence officielles `luffy_Idle/Action/Signature` sont construites depuis `luffy_<Nom>_fini.json` (lues par HttpService sur un serveur local, `HttpEnabled` remis à false) ; copies `*_fini` et blocage retirées de `RBX_ANIMSAVES.luffy`
  - [x] Action : l'épaule reste collée, seul l'avant-bras s'allonge (`etirer` = translation du coude, ressort `RightElbowPos` dans `finition.py`) ; Beams `BrasElastique_*` déplacés au coude (peau entre la manche et l'avant-bras) ; charge : le bras s'allonge vers l'arrière (signe corrigé), retour : dépassement -0,15
  - [ ] **Prochaine session : bras élastique de `luffy_Action` en cube.** Remplacer le Beam `BrasElastique_*` (ruban plat face caméra) par un cube couleur peau de la largeur du bras (≈ 1 × 1 stud, comme l'avant-bras R15) qui s'étire entre le coude (bas de la manche) et l'avant-bras. Rien n'a été fait de ce côté ; contrainte : pas de script de jeu dans le modèle (taille d'une pièce non animable par KeyframeSequence) → piste à étudier : plusieurs segments de cube répartis le long de l'étirement, chacun soudé/translaté par la même translation de coude, ou mise à l'échelle lue côté client dans `Vitrine.luau` (modifie `src/`, à demander)
  - [ ] Vérifier `luffy_Action` dans l'Animation Editor (pas encore fait par l'utilisateur)
  - [ ] Publication (manuel, pas encore faite) → 3 IDs → attributs `AnimationIdle/Action/Signature`, vérification `GetKeyframeSequenceAsync`
  - [ ] 7. Finition : AnimationController + Animator, ancrage, `ModelesPersonnages.luffy` ; supprimer `ServerStorage.Outil_Apercu_luffy`, `Outil_Seul_luffy`, `Outil_VFX_luffy`, `Outil_KS_luffy`
  - [ ] Enregistrer la place Studio (Acc_Haki, VFX, Beams, KeyframeSequence n'existent que dans la place, pas dans git)
  - [ ] KeyframeSequence dans `RBX_ANIMSAVES.luffy` → publication (manuel) → attributs `AnimationIdle/Action/Signature`
- [ ] 6. Accessoires et VFX (dans `Workspace.luffy`)
  - [x] `Acc_Viande` : n'existait pas (rien à supprimer)
  - [x] `Acc_Haki` (coque avant-bras) + `Acc_Haki_Main` (coque main) : 2 accessoires car `Vitrine.luau` ne montre que le `Handle` ; Attachment unique sur la pièce porteuse (sinon le Humanoid les soude à la tête)
  - [x] `BrasElastique_Right/Left` : Beam couleur peau du pivot d'épaule au haut du bras (invisible au repos, s'étire avec la translation)
  - [x] Textures `vfx/poing.png` 118675450303720, `vfx/trait.png` 82179997647549 (`vfx_luffy.py`)
  - [x] VFX Rafale, Charge_Poing (sphère `VFX_ZoneCharge` soudée à la main), Poing_Elastique, Impact_Final, Eclairs_Haki, Onde_Haki ; aperçus rafale, impact, Haki
  - [x] Vrais éclairs du Haki : planche `vfx/eclairs_haki.png` 4×4 (73977543565746, Flipbook Random) ; `Eclairs_Haki` = crépitement sur l'avant-bras (zone `VFX_ZoneHaki`), grands éclairs autour du buste (`VFX_ZoneHakiLarge`), aura rouge, étincelles ; `Onde_Haki` + salve d'éclairs au sol et flash rouge
- [ ] 7. Finition (AnimationController, ancrage, `ModelesPersonnages.luffy`)
- [ ] 8. Bilan ; garder `assets/persos/luffy/` pour `luffy_gear2`

### Modération (avertissement Roblox reçu, 2026-10-29)
- [x] Décalque du ventre (nombril, traits du bassin) retiré de `ModelesPersonnages.nami` ; `ventre_nami.png` supprimé, `peindre_ventre.py` archivé
- [x] Bikini remplacé par le haut couvrant rayé (géométrie d'origine) ; nombril et ligne du ventre retirés de l'atlas `tex_corps_nami.png` ; export 4 808 triangles
- [x] Détails du ventre : décision de ne remettre aucun détail anatomique (nombril, traits du bassin = cause probable de l'avertissement) ; à la place, décalque d'ombre neutre `ombre_torse_nami.png` (`peindre_ombre_torse.py` : ombre sous le haut, côtés) envoyé (118639795987019) et posé (`UpperTorso.OmbreTorse`)
- [x] Réimport : 9 Vet_<Piece> remplacés (haut couvrant, texture 85250372065604)
- [x] Bug corrigé : dans `ModelesPersonnages.nami`, HumanoidRootPart était en (0, 2, 0) et le corps en (-2, 3,44, 300) ; au clonage, les Motor6D recalaient le corps mais pas les pièces soudées (vêtements décalés en jeu). HRP replacé d'après Root (écart des 15 Motor6D au repos : 0), modèle ramené à l'origine ; clone vérifié (vêtements et accessoires : écart 0)
- [ ] Supprimer les images déjà envoyées (Creator Dashboard, manuel) : ventre 108726701111437, 117000828854926, 113918571546651 ; textures d'atlas avec bikini 119937557598628, 99672583625574
- [x] Rig de la nouvelle nami relevé dans Studio (`rig_nami.json`) ; `anims_nami.py` (IK, pieds plantés, bras dirigés par directions, vérifications) ; `apercu_studio.py` (copies figées posées dans `Workspace.Apercu_Anim`)
- [x] 4. `nami_Idle` (90 images, 13 clés, 3 marqueurs) validée ✋ ; KeyframeSequence dans `RBX_ANIMSAVES.nami` (14 keyframes) ; ancienne Idle R6 renommée `nami_Idle_ancien` ; `vers_studio.py`
- [x] 4. `nami_Action` (105 images, 13 clés, marqueurs VFX Nuage 15 / Etincelles 30 / Eclair 55) validée ✋ ; KeyframeSequence (14 keyframes) — abattu = arc vers le bas (rotation du bras sur lui-même impossible : pivot d'épaule décalé de 0,5)
- [x] 4. `nami_Signature` (105 images, 10 clés, marqueurs Montrer Acc_Carte 15 / VFX Pieces 40 / Cacher Acc_Carte 75) validée ✋ ; KeyframeSequence (10 keyframes) — saut : corps entier +0,2 depuis la pose aux pieds plantés
- [x] 4. Aperçu en mode édition sans publier (`RegisterKeyframeSequence` + `Animator:StepAnimations` sur une copie, marqueurs Montrer/Cacher appliqués)
- [x] 4. Publication (manuel, clic droit → Save to Roblox ; l'éditeur d'animation ne chargeait pas les séquences) : Idle 87321310286727, Action 129343429620585, Signature 88856705155105 — vérifiées conformes (clés, durée, boucle, priorité, marqueurs) ; attributs posés sur `ModelesPersonnages.nami` ; copie `Workspace.nami` supprimée. (Un premier ID 124402299654762 n'est pas une animation valide : à ignorer)
- [x] 5. VFX dans `ModelesPersonnages.nami.VFX` (format lu par `src/client/Vitrine.luau`) : Pieces_Brillent (Duree 0,5, étincelles dorées sur la bourse), Nuage (Duree 2,2, fumée gris foncé étalée, 3 studs devant au-dessus), Etincelles (Burst 25, bâton), Eclair (Duree 0,35 : 4 Beam en zigzag du nuage au sol + flash + anneau au sol), Pieces (Burst 20 pièces + 12 éclats) ; texture `vfx/piece.png` (`vfx_nami.py`) 91715201786333, anneau de zoro réutilisé ; aperçus Studio aux images des marqueurs (éclair, pièces, bourse)
- [ ] Retouches demandées après test :
  - [x] Bâton (Clima-Tact) allongé ×1,6 (2,22 → 3,56 studs, embouts reportés, soudures refaites)
  - [x] Bras droit au repos à 45° (coude 45, poignet 30 : bâton toujours vertical) ; 3 animations recalculées (Action : marqueurs Charge 16 et Rafales 56 en plus) ; KeyframeSequence corrigées sur place (bras droit des clés en pose de repos : Idle 13, Action 4, Signature 10 ; marqueurs Charge 16 / Rafales 56 ajoutés) — à republier
  - [x] Bourse remplacée par un vrai sachet (`bourse()` : révolution plissée, col serré, collerette dans le poing, cordon et 2 bouts) ; export `accessoires_nami.fbx` (1 460 triangles) importé, Handle remplacée ; soudure calculée pour qu'il pende quand la main le lève (REL_BOURSE), vérifiée
  - [x] Textures `vfx/eclair.png` 88432637509015, `vfx/arc.png` 116921766737586
  - [x] VFX Charge (Duree 1,35 : arcs `arc.png` aux 2 bouts et au centre du bâton, lueur, étincelles), Nuage (pièce-zone 6 × 0,8 × 4,5 : fumée noire étalée + éclairs internes, Duree 2,7), Rafales (Duree 1 : éclairs `eclair.png` en salves dans une zone 5 × 4 + flashs et anneaux au sol), sachet rebranché ; aperçus figés (images 30 et 57) et cycle complet en mouvement dans Studio
  - [x] Bug en jeu « la bourse affiche la carte, la Signature n'affiche rien » : la logique Montrer/Cacher était bonne (journal client en Play), mais la bourse pendait dans l'avant-bras levé (on n'en voyait qu'un bout plat) et la carte était vue par la tranche. Prises refaites sur les poses figées (Idle 30, Signature 30) : bourse debout sur le poing (×1,3), carte dressée devant la main, dessin vers l'avant (×1,5) ; vérifié sur une copie (écart 0)
  - [x] Pièces qui jaillissent de la bourse pendant les secousses (Idle 30-45) : émetteur `VFX_Pieces` (texture pièce, gravité) ajouté à l'effet `Pieces_Brillent` (Duree 0,5, déjà déclenché à l'image 30 : pas de republication), ~53 particules max
  - [x] Effet `Pieces` de la Signature retiré (dossier `VFX.Pieces` et émetteurs `HumanoidRootPart.VFX_Pieces` supprimés ; le marqueur VFX Pieces de l'animation publiée est ignoré par Vitrine)
  - [x] Republiées : Idle 101809439483044, Action 75447177403978, Signature 123951473389227 — vérifiées conformes (coude 45, marqueurs Charge / Rafales), attributs mis à jour
- [ ] 7. Bilan ; tester la vitrine en jeu (Play) ; images d'interface refaites depuis Studio et envoyées (2026-10-29, voir Assets GUI)
### Mannequin v2 « blocs arrondis » (skill `/perso-roblox`, fichiers dans `assets/persos/_mannequin/`)
Version 1 (boîtes nettes + Shirt/Pants, tête classique) archivée dans `assets/persos/_mannequin/v1/` ; `r15_bloc.json`, `zones_vetements.json` et `axes_r15.json` restent en place (lus par les scripts de `zoro`).
- [x] 1. Relevé du R15 en blocs (mode édition, `releve_brut.json`) : corps identique à la v1 à 2 mm près, tête dynamique 1,159 × 1,182 × 1,161 ; `rig_r15.py` → `r15_bloc.json` v2 (symétrisé, écart du relevé 0,000015) ; modèle supprimé
- [x] `anims_zoro.py` pointé sur `_mannequin/v1/r15_bloc.json` (zoro est construit sur la v1)
- [x] 2. `construire_mannequin.py` → `mannequin.blend` v2 : 15 pièces arrondies (biseau 0,15 / 3 segments, 0,126 sur mains et pieds, normales durcies), cylindre de jointure aux coudes et genoux, tête superellipsoïde (1,24 en haut, 1,08 en bas, 1,182 de haut), atlas 1024² (tête en haut, croix par pièce à 45 px/stud), `uv_mannequin.json` (grille de la face), armature `Rig_R15` (os verticaux comme la v1), parentage rigide ; 3 712 + 3 000 triangles
- [x] 2. `peindre_mannequin.py` → `tex_corps_mannequin.png` (peau + face de test), `controle_uv.png` (damier) ; dépliage vérifié
- [x] 2. Captures face / profil / 3/4 / dos + planche Gojo + pose test (coude droit, genou gauche à 90°) : pivots justes, pas de trou
- [ ] 2. ✋ validation
- [ ] 3. Export `mannequin.fbx`, import (manuel), assemblage Studio, comparaison des captures ✋
- [ ] 4. Calibration des articulations (Studio + Blender), `axes_r15.json`, pose test ✋
- [ ] 5. `ServerStorage.Gabarits.MannequinR15` remplacé, clones supprimés, bilan
### Assets GUI (images d'interface rendues depuis Blender, fichiers dans `assets/gui/`)
- [x] 1. `assets/gui/rendu_gui.py` (`rendre(id)`, MCP Blender) : copie du .blend dans un dossier temporaire, studio photo commun (fond transparent, 3 soleils, EEVEE, Standard, contour Freestyle silhouette + contour extérieur), 3/4 pris du côté droit du perso (azimut 30°)
  - [x] `portrait.png` 512² (buste 3/4, image de l'Idle dans `POSES_PORTRAIT`, sinon la plus éloignée de l'image 0)
  - [x] `pied.png` 1024² (plein pied, contre-plongée de 8°, marge 6 %)
  - [x] `silhouette.png` 512² (alpha du portrait, noir pur, bord durci)
  - [x] `idle_sheet.png` 1024² (4×4 images de 256², cadrage commun aux 16, raccord fin → début vérifié)
  - [x] `infos.json` (images, durée, ordre, fps conseillé)
  - [x] Lecture des poses JSON (perso-roblox) vérifiée sur `zoro` (pose, raccord 0, image expressive auto = 38), rendus de zoro non lancés
- [x] 2. `assets/gui/cadres.py` (Pillow) : 5 cadres 280×368, `secret_reflet.png`, `apercu.png`, `cadres/infos.json` (zone intérieure du portrait)
- [x] 3. Test sur `nami` (pose 40 : orbe levé près du visage ; 13 s de rendu) : images montrées
- [x] 3. ✋ Style validé par l'utilisateur (2026-10-29)
- [x] Rendre `zoro` (`rendre("zoro")`, 18 s, pose 38)
- [x] `zoro` : les bras croisés de l'Idle cachent le visage sur `pied.png` (même caméra au-dessus des yeux) → pose dédiée (décision) : main droite posée sur les poignées, bras gauche le long du corps (`assets/gui/pose_gui_zoro.py` → `anims/zoro_PoseGUI.json`, recherche en grille sur `bras_dirige`, 29 s ; le solveur L-BFGS-B restait bloqué). La grille reste l'Idle réelle (visage caché pendant les bras croisés)
- [x] 4. Envoi sur Roblox (`upload_image` du MCP Studio) : nami (portrait 110078464763952, pied 97800145793498, silhouette 125258690878522, idle_sheet 134326278156812) et cadres (Commun 73991991603192, Rare 90758012188875, Legendaire 139155695753037, Mythique 75830200946156, Secret 78993290810706, secret_reflet 97681142840985) ; IDs dans les `infos.json` (`ids_roblox`, conservé par les scripts quand ils réécrivent le fichier)
- [x] 4. Envoi de `zoro` (portrait 122981940555502, pied 80949230946055, silhouette 117718428690224, idle_sheet 83426259296376), IDs dans `assets/gui/zoro/infos.json`
- [x] Contrôle « tous » (2026-10-29) : aucun nouveau perso à rendre (seuls `nami` et `zoro` ont un .blend, déjà rendus ; les 9 autres n'ont pas de modèle). nami et zoro : fond transparent (coins alpha 0), rien de coupé en haut du portrait ni sur les bords du plein pied et des 16 cases, raccord de boucle 0
- [x] Cadrage du portrait sur la tête du rig (décision) : centre sur l'os `Head` à 0,625 stud du cou, image de 4,75 studs, caméra à 8,75 studs ; même zoom pour tous, alerte si le bord haut est touché. nami et zoro re-rendus (29 s), planche comparée, rien de coupé
- [x] Métadonnées PNG de Blender désactivées (date, chemin local) : rendus identiques à l'octet près
- [x] Renvoi des portraits et silhouettes : nami portrait 110253584605339, silhouette 73798628894301 ; zoro portrait 140034364207144, silhouette 112226033450017 (pied et idle_sheet inchangés au pixel près : IDs conservés)
- [ ] Images d'interface de `nami` refaites (2026-10-29) :
  - [x] `rendu_gui.py` : source `assets/persos/<Id>/<Id>.blend` acceptée ; textures en chemin relatif (`//`) rattachées au dossier de l'original (sinon magenta) ; accessoires montrés / cachés selon les marqueurs `Montrer` / `Cacher` de l'Idle, comme `Vitrine.luau` ; refuse un perso dont les images viennent de Studio
  - [x] Rendu Blender de `nami.blend` fait puis écarté : ce n'est pas la vraie nami. Décision : la référence est `ModelesPersonnages.nami` dans Studio (corps R15 en blocs de Roblox, tête classique + décalque `face` 7948257917, cheveux du catalogue 4232058809, bâton `Part` Deep orange ; seuls les `Vet_*` et accessoires viennent de Blender) ; images rendues depuis Studio (choix de l'utilisateur)
  - [x] `assets/gui/plateau_studio.luau` (MCP, en Play côté client : 34 plateaux = 17 poses de l'Idle publiée × fond noir / gris, perso tourné pour que le soleil du jeu vienne de 35° à sa droite avant, cadrages de `rendu_gui.py`, passage de chauffe) + `assets/gui/rendu_studio.py` (détourage par différence des deux fonds, reprojection exacte des captures vers la caméra cible, plein pied en 2 bandes, cadrage sur l'alpha, contour sombre, silhouette, grille, `infos.json`) ; 38 captures, 24 s de traitement
  - [x] Vérifié : coins transparents ; rien de coupé (haut du portrait, bords du plein pied et des 16 cases, bâton et bourse entiers) ; raccord de l'Idle 0 ; écart case 15 → 0 (1,85) sous l'écart moyen entre cases (3,44). Éclairage = celui du jeu (peau plus claire que les rendus Blender), tête classique plus grosse que celle de zoro au même zoom (même règle de cadrage)
  - [x] Bug en jeu corrigé : les 4 embouts du bâton (`Acc_Baton.Part`) étaient soudés à ≈ 480 studs du bâton ; ramenés sur son axe (bagues ±1,49, boules ±2,10), soudures refaites ; place enregistrée
  - [x] Envoi sur Roblox (`upload_image`) : portrait 140496050097409, pied 114044211519143, silhouette 111957893757960, idle_sheet 122462618381607 ; `ids_roblox` et `src/shared/ImagesPersonnages.luau` mis à jour
  - [ ] Supprimer les anciennes images de nami (Creator Dashboard, manuel) : 110253584605339, 97800145793498, 73798628894301, 134326278156812
  - [x] Vérifié en Play : carte d'inventaire de nami avec le nouveau portrait ; silhouette, plein pied et grille chargés (`IsLoaded`) et affichés sur un écran de test provisoire (supprimé). Révélation du tirage non rejouée (tirage aléatoire ; même module `Images` que la carte)
- [ ] (optionnel) Grille idle de `zoro` lisible : croiser les bras plus bas dans `zoro_Idle` (change l'animation du jeu, republication manuelle)
- [x] Images installées en jeu (demande « installes tout ça in game ») :
  - [x] `src/shared/ImagesPersonnages.luau` (IDs) et `src/client/Images.luau` (cadre, grille Idle animée, reflet Secret, préchargement), skill `/nouveau-module`
  - [x] Inventaire : carte 140×184 = cadre de la rareté, portrait rogné au buste, rareté, nom, étoiles, revenu, badge `#N` si posé, bouton ; bloc + initiale sans images ; reflet sur les Secret
  - [x] Tirage : carte 300×394 (proportions du cadre), cadre de chaque candidat, silhouettes pendant le suspense, grille Idle animée à la révélation, reflet Secret dès la révélation (le DelayTime du TweenInfo retardait le premier passage), pulsation Mythique / Secret
  - [x] selene OK ; testé en Play : 27 cartes avec cadre, 8 portraits, images chargées (AssetFetchStatus Success), révélation zoro animée (≈ 4 images/s), reflet Secret ; 5 persos de test donnés à cemobozo (luffy_gear2, robin, franky, nami, zoro)
- [ ] Textes de rareté peu lisibles sur un cadre de la même couleur (Mythique sur violet) : passer en blanc avec contour coloré ? (à voir à l'œil)
- [ ] Silhouettes du suspense : vérifier à l'œil qu'elles se voient sur le haut sombre des cadres
### Personnage `nami` v2 (skill `/perso-roblox`, Commun, fichiers dans `assets/persos/nami/`)
Refonte de l'ancien modèle R6 (section plus bas). Premier perso construit sur le mannequin v2 « blocs arrondis ».
- [x] Inventaire de l'existant ; référence copiée dans `assets/references/nami.png`
- [x] 1. Fiche reformulée ✋ validée
- [x] 2. Copie du mannequin → `nami.blend`
- [x] 2. Blockout (`construire_nami.py` : `cheveux()`, `tenue()`, `accessoires()`) ; bâton perpendiculaire à l'avant-bras (vertical et planté au sol coude plié à 90°)
- [x] 2. Normales des mèches corrigées (étaient vers l'intérieur : invisibles dans Roblox) ; contrôle par volume signé
- [x] 2. Atlas unique `tex_corps_nami.png` (une MeshPart = une texture : tête + cheveux, torse + haut + nappe du dos) : `uv_nami.py` (`atlas()`, `ombrage()` : occlusion par lancers de rayons), `peindre_nami.py` (face, cel-shading 3 tons + liserés des mèches, pois, jean surpiqué, tatouage) ; accessoires dans `tex_acc_nami.png` (carte au trésor dessinée)
- [x] 2. Racine des cheveux lisse (calotte qui rentre sous la peau au lieu d'être coupée en marches)
- [x] 2. Accessoires séparés `Acc_Baton` (visible), `Acc_Bourse`, `Acc_Carte` (cachés, attribut `VisibleParDefaut`)
- [x] 2. Premier modèle final montré (14 399 triangles) ; retours : cheveux en « dreadlocks », tête pas assez Roblox, corps trop arrondi (« bouée »), visage à refaire d'après une image de référence
- [x] 2. Retouches : corps à biseau 0,05 (au lieu de 0,15), tête en bloc arrondi 1,2 × 1,16 × 1,182 (face plate projetée à 380 px/stud), cheveux en nappes lisses (`nappe()`, pointes en dents de scie) + frange et mèches avant en rubans plats, cheveux peints (anneau de lumière, sillons, liserés), grands yeux ambre façon référence
- [ ] 2. Modèle final v2 ✋ (10 411 triangles, Head 2 659)
- [x] Essai « tout depuis le Creator Store » (`Workspace.Test_Nami_Store`, en (-14, y, 300)) : 5 modèles Nami trouvés, 4 piégés (scripts cachés « LightConfig », « CoreSkyboxSystem », « Runtime », supprimés) ; seul propre : 8225914709 (R6, tenue de Wano). Coiffure propre : « Silk Orange Hair » 5361730648. Vêtements du catalogue avatar introuvables via le MCP (le Creator Store ne les contient pas)
- [x] Décision : mélange. Avatar R15 vide (`Gabarits.MannequinR15`) + tête, visage, coiffure et bâton (Clima-Tact) de la Nami du store (8225914709) + vêtements 3D de Blender
- [x] `Workspace.Test_Nami_Store.Nami_Mix` monté (peau, tête/visage/coiffure de A soudés à Head, bâton soudé à RightHand)
- [x] Export `fbx/vetements_nami.fbx` (`export_vetements.py` : 9 maillages Vet_<Piece>, 3 728 triangles, texture intégrée) + `vetements_nami.json` (tailles, décalages), vérifié par réimport
- [x] Import de `vetements_nami.fbx` dans Studio (manuel) : tailles exactes, sans rotation, texture 106676499903452 ; Vet_<Piece> posés sur `Nami_Mix.Vetements` (CFrame = pièce * décalage, WeldConstraint)
- [ ] Captures validées ✋ (face et 3/4 faites ; la texture met quelques secondes à s'afficher en mode édition)
- [ ] Tatouage de l'épaule gauche (Decal sur LeftUpperArm, image à envoyer)
- [x] Retouches d'après l'image de référence n° 2 : haut rayé (vert foncé / blanc / vert clair, arqué en deux bonnets, forme couvrante gardée), ceinture noire cloutée portée de travers + boucle ronde (`LowerTorso_Ceinture`, `LowerTorso_Clous`, pastilles fixes hors rangement), export refait (4 880 triangles)
- [x] Décalque du ventre `ventre_nami.png` (`peindre_ventre.py` : nombril, ligne médiane, traits du bassin, taille, clavicules) envoyé (108726701111437), posé sur `Nami_Mix.UpperTorso` (face avant)
- [x] Haut remplacé par un vrai bikini (demande de l'utilisateur, la fiche disait l'inverse) : 2 triangles rayés bombés (`nappe()`), tour de cou, bande dans le dos, anneau ; aucune ombre de poitrine. Décalque du ventre refait (ombre sous les triangles) : 117000828854926. Export 5 312 triangles
- [x] Bikini agrandi (triangles 0,82 de large, pointe à 4,05), bas arrondi, détails du tissu peints (ombrage, plis, liseré, surpiqûres) ; pas de détails anatomiques de poitrine (refusé : règles Roblox). Décalque du ventre : 113918571546651. Export 5 512 triangles
- [x] Réimport (bikini + ceinture + rayures), 9 Vet_<Piece> remplacés (texture 119937557598628)
- [x] Bug : peau visible aux pieds (pied de l'avatar 1,009 x 1,001 x 0,312, bride à 0,5) → chaussures fermées 1,07 x 1,07 x 0,35 + semelle + talon + bride ; réimportées, texture remise sur celle des autres vêtements, capture : plus de peau
- [x] Captures validées ✋ (« ok »)
- [x] 6. Finition : Humanoid sans nom ni barre de vie (Animator dedans, pas d'AnimationController), HumanoidRootPart ancré et invisible = PrimaryPart, autres pièces non ancrées, collisions coupées ; bâton converti en Accessory `Acc_Baton` (Handle + pièces soudées, `VisibleParDefaut` = true) ; 31 pièces vérifiées dans l'assemblage de HumanoidRootPart (copie temporaire dans le Workspace)
- [x] 6. Rangement : ancien modèle R6 renommé `ModelesPersonnages.nami_ancien` (garde `AnimationIdle`), nouveau = `ModelesPersonnages.nami` ; `Workspace.Test_Nami_Store` supprimé
- [ ] Enregistrer la place (manuel)
- [x] Export `fbx/accessoires_nami.fbx` (`exporter_accessoires()` : Acc_Bourse 336 triangles, Acc_Carte 228, texture tex_acc_nami.png) + `accessoires_nami.json` (décalages par rapport à LeftHand), vérifié par réimport. Bug corrigé : l'export effaçait les objets sources du même nom (renommés le temps de l'export)
- [ ] Import de `accessoires_nami.fbx` (manuel), Accessory + soudure à LeftHand, cachés par défaut
- [ ] Proposer de reporter les retouches de style (biseau 0,05, tête en bloc) dans le mannequin v2 et le skill `/perso-roblox`
- [ ] 3. Export `corps_nami.fbx` + vérification par réimport
- [ ] 3. Import Studio (manuel), assemblage R15 (15 Motor6D, soudures, textures) ✋
- [ ] 4. `nami_Idle` « Compter le butin » (90 images, boucle) ✋
- [ ] 4. `nami_Action` « Coup de tonnerre » (105 images) ✋
- [ ] 4. `nami_Signature` « Carte au trésor » (105 images) ✋
- [ ] 4. KeyframeSequence dans `RBX_ANIMSAVES.nami`, publication (manuel), attributs, vérification des IDs
- [x] 5. VFX dans `ModelesPersonnages.nami.VFX` (format lu par `src/client/Vitrine.luau`) : Pieces_Brillent (Duree 0,5, étincelles dorées sur la bourse), Nuage (Duree 2,2, fumée gris foncé étalée, 3 studs devant au-dessus), Etincelles (Burst 25, bâton), Eclair (Duree 0,35 : 4 Beam en zigzag du nuage au sol + flash + anneau au sol), Pieces (Burst 20 pièces + 12 éclats) ; texture `vfx/piece.png` (`vfx_nami.py`) 91715201786333, anneau de zoro réutilisé ; aperçus Studio aux images des marqueurs (éclair, pièces, bourse)
- [ ] Retouches demandées après test :
  - [x] Bâton (Clima-Tact) allongé ×1,6 (2,22 → 3,56 studs, embouts reportés, soudures refaites)
  - [x] Bras droit au repos à 45° (coude 45, poignet 30 : bâton toujours vertical) ; 3 animations recalculées (Action : marqueurs Charge 16 et Rafales 56 en plus) ; KeyframeSequence corrigées sur place (bras droit des clés en pose de repos : Idle 13, Action 4, Signature 10 ; marqueurs Charge 16 / Rafales 56 ajoutés) — à republier
  - [x] Bourse remplacée par un vrai sachet (`bourse()` : révolution plissée, col serré, collerette dans le poing, cordon et 2 bouts) ; export `accessoires_nami.fbx` (1 460 triangles) importé, Handle remplacée ; soudure calculée pour qu'il pende quand la main le lève (REL_BOURSE), vérifiée
  - [x] Textures `vfx/eclair.png` 88432637509015, `vfx/arc.png` 116921766737586
  - [x] VFX Charge (Duree 1,35 : arcs `arc.png` aux 2 bouts et au centre du bâton, lueur, étincelles), Nuage (pièce-zone 6 × 0,8 × 4,5 : fumée noire étalée + éclairs internes, Duree 2,7), Rafales (Duree 1 : éclairs `eclair.png` en salves dans une zone 5 × 4 + flashs et anneaux au sol), sachet rebranché ; aperçus figés (images 30 et 57) et cycle complet en mouvement dans Studio
  - [x] Bug en jeu « la bourse affiche la carte, la Signature n'affiche rien » : la logique Montrer/Cacher était bonne (journal client en Play), mais la bourse pendait dans l'avant-bras levé (on n'en voyait qu'un bout plat) et la carte était vue par la tranche. Prises refaites sur les poses figées (Idle 30, Signature 30) : bourse debout sur le poing (×1,3), carte dressée devant la main, dessin vers l'avant (×1,5) ; vérifié sur une copie (écart 0)
  - [x] Pièces qui jaillissent de la bourse pendant les secousses (Idle 30-45) : émetteur `VFX_Pieces` (texture pièce, gravité) ajouté à l'effet `Pieces_Brillent` (Duree 0,5, déjà déclenché à l'image 30 : pas de republication), ~53 particules max
  - [x] Effet `Pieces` de la Signature retiré (dossier `VFX.Pieces` et émetteurs `HumanoidRootPart.VFX_Pieces` supprimés ; le marqueur VFX Pieces de l'animation publiée est ignoré par Vitrine)
  - [x] Republiées : Idle 101809439483044, Action 75447177403978, Signature 123951473389227 — vérifiées conformes (coude 45, marqueurs Charge / Rafales), attributs mis à jour
- [ ] 7. Bilan ; tester la vitrine en jeu (Play) ; images d'interface refaites depuis Studio et envoyées (2026-10-29, voir Assets GUI)
- [x] 6. Finition, ancien modèle renommé `nami_ancien`, nouveau rangé dans `ModelesPersonnages.nami`
- [x] 6. Anciens fichiers `assets/blender/nami/` rangés dans `assets/archives/nami/` (`git mv`) ; source de `assets/gui/nami/infos.json` mise à jour
- [x] 7. Images d'interface re-rendues depuis le nouveau modèle (`assets/gui/nami/`, voir Assets GUI)
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

### Personnage `nami` — ancien modèle R6 (skill `/perso-r6`, fichiers archivés dans `assets/archives/nami/`, remplacé par la v2)
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
### Finition des animations (fluidité, impact) — pilote : luffy
- [x] Diagnostic : pourquoi les animations actuelles paraissent simples (clés communes à tout le corps, 2 easings, poses figées)
- [x] Module partagé `assets/persos/_anim/finition.py` : cuisson à 30 i/s, easings d'impact, ressorts par articulation (décalage et dépassement), respiration, secousse d'impact, raccords exacts
- [x] Appliquer à `anims_luffy.py` (Idle, Action, Signature) : version « fini » à côté de la version actuelle
- [x] Vérifications (pénétrations, LowerTorso ≤ 0,5, raccords) sur chaque image ; contacts exacts (main au chapeau, main sur le biceps)
- [x] KeyframeSequence `luffy_*_fini` (80, 144, 78 clés) dans `RBX_ANIMSAVES.luffy` (les `luffy_*` du blocage sont construites par l'autre session /perso-catalogue)
- [ ] Comparer blocage / fini dans l'éditeur d'animation et choisir (manuel)
- [ ] Relancer `anims_luffy.py Signature` quand la nouvelle signature() est stable (contacts à recaler si le minutage change) dans `ServerStorage.RBX_ANIMSAVES.luffy` pour comparer dans l'éditeur d'animation
- [ ] Recette d'impact VFX en couches (flash, éclats, onde, poussière, braises) pour les effets de luffy
- [x] Rendu validé par l'utilisateur (31/10)
- [x] `finition.finir()` commun (cuisson + allègement) ; nami et zoro branchés (`finir()` dans leurs scripts, courbes d'impact : éclair de nami en `Entree`, saut en `Sortie`/`Entree`, dégainages et entailles de zoro en `Sortie`, clac en `Entree` ; secousses)
- [x] Vérifié sur chaque image : rien de pire que le blocage (+0,03) sauf zoro Action image 75 (avant-bras dans le torse 0,05, une image, invisible) ; zoro Idle : bras exacts au retour (98-120)
- [x] KeyframeSequence `nami_*_fini`, `zoro_*_fini` dans `RBX_ANIMSAVES.nami` / `.zoro`
- [ ] **Reprise 01/11** : revoir les 6 `*_fini` dans l'éditeur d'animation (comparer aux versions publiées), retoucher si besoin
- [ ] Publier les 6 `*_fini` (manuel) puis remplacer les attributs `AnimationIdle/Action/Signature` de `ModelesPersonnages.nami` et `.zoro` par les nouveaux IDs
- [x] Étape « Finition » ajoutée aux skills `/perso-catalogue` et `/perso-roblox` (section Animations)
- [ ] Recette d'impact VFX en couches pour nami et zoro (après luffy)

### Bible d'animation du lot 1 (propositions, artifact du 31/10/2026)
- [x] Proposer Idle / Action / Signature pour les 11 persos, avec aperçus animés en blocs R15, storyboards et marqueurs (`Montrer` / `Cacher` / `VFX`)
- [ ] Valider ou corriger les propositions perso par perso (Usopp, Chopper, Franky, Brook, Robin, Jinbei, Sanji, Gear 2)
- [ ] Reporter les animations validées dans le wiki (`Personnages.md`, section Animations de vitrine)
- [ ] (code, proposition) Délai aléatoire 0-2 s au lancement des vitrines dans `BaseService` (désynchronisation)
- [ ] (code, proposition) Effets permanents (attribut `Permanent`) et images rémanentes (marqueur `Echo`) dans `Vitrine.luau`, nécessaires pour Gear 2
- [ ] (idée) Animation d'entrée en scène quand on pose un perso

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
- [x] Remplacer l'initiale de la carte de tirage par le visuel du personnage (images rendues, voir « Assets GUI ») ; les persos sans modèle gardent l'initiale
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
