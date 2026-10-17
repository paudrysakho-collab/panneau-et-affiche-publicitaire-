# Passation : affiche A1 Cave 71 (à lire en entier avant de commencer)

Tu reprends un projet en cours. Branche git : `claude/zealous-mayer-8zltpn`. Dossier de travail : `panneau/`. Le client parle français, de façon familière, et attend un résultat pro sans fautes.

## 1. Le client et l'objectif
- **Cave 71** est une cave à vins et épicerie fine, au 71 avenue de la Libération, 44400 Rezé.
- Il faut une affiche **A1** (chevalet de trottoir) en deux versions :
  - **sombre** (lie-de-vin), la version principale ;
  - **claire** (blanc chaud).
- Livrables : PNG 3508×4962, PDF 150 dpi, PPTX modifiable et aperçu.
- La mise en page (logo, titres, services, contact, QR code) est **finie et validée**. Elle est faite avec Remotion dans `src/Panneau.tsx`, et les textes sont dans `src/textes.json`.
- **Il reste UNE chose : la photo des 13 produits.** Le client veut qu'elle ait l'air d'une **vraie photo de studio** (lumière, reflets, profondeur, verre crédible). Les **étiquettes doivent être exactement les vraies** : le client a exigé « MAKE NO MISTAKES ».

## 2. Les 13 produits
Ils sont présentés de gauche à droite. Les hauteurs ont été vérifiées.

| N° | Produit | Hauteur | Remarque |
|---|---|---|---|
| 1 | Rhum La Favorite Cœur de Canne | ≈ 27 cm | bouchon à tête en bois |
| 2 | Jus de raisin Syrah 04 (Exea) | ≈ 17,5 cm | capsule argent |
| 3 | Whisky Suntory Toki | ≈ 25 cm | bouteille carrée |
| 4 | Whisky Tomatin Legacy | ≈ 26 cm | **version du magasin** : TOMATIN imprimé sur le verre, panneau bleu à partir de LEGACY seulement |
| 5 | Rosé Bastide de Blacailloux JOIO 2025 | ≈ 31 cm | |
| 6 | Châteauneuf-du-Pape Domaine Le Prieuré des Papes Vieilles Vignes | ≈ 30 cm | |
| 7 | Château de Gragnos Lou Daro 2022 | ≈ 30 cm | bourguignonne normale, élancée ; le client se plaint qu'elle soit « chelou » sur les images IA |
| 8 | Champagne Denis Frézier Cuvée des Trois Crus Premier Brut | ≈ 30 cm | |
| 9 | Bière Lutgarde Blonde | ≈ 18,5 cm | trapue |
| 10 | Bière Trompe Souris Blonde | ≈ 23 cm | long neck ; le client a validé son rendu |
| 11 | Sachet de chocolats Maison Guinguet, chocolat noir | ≈ 23 cm | cellophane et rose en papier |
| 12 | Terrine Goûts de Loire « Silure de Loire à la Tomate séchée » | ≈ 8 cm | |
| 13 | Pot L'Atelier d'Emile « Tartinable de Courgettes grillées » | ≈ 8,5 cm | **Emile sans accent** |

Le **texte exact de chaque étiquette**, vérifié lettre par lettre par plusieurs agents, se trouve dans `bouteilles-gemini/pack-derniere-tentative/PROMPT-ChatGPT-derniere-tentative.txt` (77 textes entre « »).

## 3. Ressources prêtes
- **`bouteilles-gemini/pack-derniere-tentative/`** :
  - `01…13_*.jpg` : une vraie photo par produit, nettoyée ;
  - `14_composition_actuelle_modele.jpg` : l'ancienne composition ;
  - `15_planche_13_produits.jpg` : planche numérotée des 13 produits ;
  - `fiches/` : chaque produit avec un gros plan de son étiquette ;
  - le prompt (versions A et B).
- **`bouteilles-gemini/detoures/`** : les 13 produits détourés en PNG transparent.
- **Outils (`tools/`) :**
  - `gemini_image.py` : appel à l'API Gemini image, avec **garde-fou de dépense** (journal CSV, plafond, coût réel calculé d'après usageMetadata) ;
  - `compose_produits.py` : composition des vrais détourages, avec marche, ombres et reflets ;
  - `remplace_etiquette.py` : recolle une vraie étiquette sur une image IA en gardant l'éclairage de la scène ;
  - `motif_photo.py`, `retouche_couleur.py`, `corrige_textes_photo.py`, `reforme_bouteille.py` : retouches ciblées ;
  - `photo_claire.py` : tire la version claire de la photo sombre ;
  - `assemble_hd.py` et `affine_photo_hd.sh` : agrandissement HD (Real-ESRGAN, sans toucher aux étiquettes) ;
  - `make_pptx.py` : PPTX modifiable ;
  - `prepare_photo_v15.sh` : toute la chaîne qui a produit l'affiche actuelle.
- **Clé API Google** : elle est **dans le secret réseau de l'environnement**. Le proxy ajoute l'en-tête `x-goog-api-key` vers `generativelanguage.googleapis.com`. Ne lis jamais la clé, ne l'écris jamais, ne la recopie jamais.
  - Facturation activée, 5 $ prépayés.
  - Déjà dépensé : **≈ 0,16 $**, journal copié dans `bouteilles-gemini/api-essais/depenses.csv` (à passer avec `--journal`).
  - Le client accepte de dépenser ces 5 $, mais avec soin : il veut **voir un premier résultat avant de continuer**.
- **Modèles disponibles** (vérifiés avec la liste des modèles) : `gemini-3-pro-image` (Nano Banana Pro), `gemini-nano-banana-2.1`, `gemini-3.1-flash-image`.
- **Prix officiels (octobre 2026) :**
  - Pro : 0,134 $ en 1K/2K, 0,24 $ en 4K.
  - 2.1 : 0,05 $ en 2K, 0,113 $ en 4K.
  - Entrée (prompt + 14 images) : ≈ 6 200 tokens, soit ≈ 0,01 $.

## 4. Ce qui a été essayé, et le verdict du client
1. **Affiche actuelle**, faite avec une image ChatGPT v15 sur laquelle on a recollé les vraies étiquettes une par une.
   - Fichiers : `exports/panneau-cave71-A1*.png/pdf/pptx`, sombre et clair.
   - Propre, mais l'image de départ vient de l'IA. Il reste des lettres cachées par d'autres produits, et le Gragnos est trapu.
2. **API, essai B** (Pro 2K, fiches + photo modèle), dans `bouteilles-gemini/api-essais/B_pro_fiches.png`.
   - Le modèle a **recopié la photo modèle (image 14)**, défauts compris, et ignoré la marche demandée.
   - Les grands noms sont justes, mais les textes moyens et petits sont déformés (« Jenis FRÉZIER », « DIETILLERIE »…).
   - **À retenir :** ne plus envoyer l'image 14, sinon le modèle la copie.
   - Les essais A et C ont échoué avec une erreur 502 « upstream request failed », non facturés. Il vaut mieux lancer **un appel à la fois**. Le paramètre `mediaResolution` est **refusé** par les modèles d'image.
3. **Modèles 1 et 2**, montages des vrais détourages sans IA :
   - fichiers : `exports/modele1-*`, `exports/modele2-*` ;
   - compositions : `PanneauModele1` et `PanneauModele2` dans `src/Root.tsx`.
   - Étiquettes parfaites, mais **le client trouve ça « mid »** : ça fait collage et catalogue, pas photo de studio. Les éclairages des différentes sources ne sont pas homogènes.

## 5. Ce que le client veut maintenant
Une **vraie image générée** qui ressemble à une photo de studio haut de gamme : lumière cohérente, reflets sur le verre, profondeur, ombres naturelles, fond lie-de-vin pour la version principale. Le tout avec les **vraies formes** de bouteilles et les **vraies étiquettes**.

## 6. Approche conseillée (la plus fiable)
1. **Générer la scène avec l'API** :
   - modèle Nano Banana Pro, essais en 2K, un appel à la fois ;
   - fiches produit (`fiches/`) en références, **sans** l'image 14 (prompt `prompt_A_fiches_sans14`, à régénérer avec `python3 tools/prompt_derniere_tentative.py --api DOSSIER`) ;
   - éventuellement 2 ou 3 variantes de mise en scène.
   - **Montrer au client avant de dépenser plus.**
   - Autre option : donner au modèle notre montage `compo_rangee_sombre.png` comme base (bonnes positions, vraies formes), en lui demandant seulement de **refaire la lumière et le rendu photo**.
2. **Garantir les étiquettes après coup** : sur l'image choisie, recoller les vraies étiquettes avec `remplace_etiquette.py`, qui transfère l'éclairage de la scène. C'est la méthode de l'affiche actuelle, qui a fait ses preuves.
3. **Rendu final en 4K**, puis :
   - version claire avec `photo_claire.py` ;
   - mettre à jour `PHOTOS` dans `src/Panneau.tsx` ;
   - rendus : `npx remotion still src/index.ts Panneau exports/… --scale=2.829`, et `PanneauClair` pour la version claire ;
   - PDF avec PIL `resolution=150` ;
   - `python3 tools/make_pptx.py [--clair]`.

## 7. Règles à respecter
- Ne jamais modifier les couleurs du logo officiel : CAVE blanc, 71 bordeaux, sur bloc noir.
- Aucune dépense en dehors des 5 $ de l'API Google.
- Ne jamais mettre d'identifiant de modèle dans les commits.
- Pas de PR sans demande.
- Fin de chaque commit :
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`
  `Claude-Session: https://claude.ai/code/session_01MhDWXdDg6yxkfVQXWRp9UB`
- Toujours vérifier à la loupe chaque étiquette avant de livrer, comparée aux vraies photos du pack.
- Répondre au client en français, court et clair. Lui envoyer les images (aperçu, puis PDF).

---

## 8. Mise à jour (session suivante, 17/10/2026) : à lire en priorité

### Où on en est
- **Le client a obtenu lui-même une image qu'il valide** (rangée de 11 bouteilles sur une marche noire, terrine et pot de courgettes devant, morceaux de chocolat à droite, fond lie-de-vin, sol brillant).
  - **Prochaine étape : l'intégrer dans l'affiche** (version sombre + claire, PNG/PDF/PPTX, voir section 6.3).
  - Le fichier doit être déposé par le client dans `panneau/bouteilles-gemini/` (par ex. `photo-finale.png`). S'il n'y est pas, le lui demander : une image collée dans le chat n'arrive pas en fichier.
- **Défauts déjà repérés sur son image**, à corriger en recollant la vraie étiquette avec `tools/recolle_scene.py` ou `tools/remplace_etiquette.py` :
  - Trompe Souris : le nom en bas de l'étiquette est déformé ;
  - Gragnos : le millésime doit être « 2022 ».
  - Vérifier à la loupe toutes les autres étiquettes.
- **Attention aux noms :** le vrai nom est « Domaine **Le Prieuré des Papes** ». « Le Frieclé des Pates » est une invention de l'IA que le client a recopiée par erreur.

### Ce que le client veut / ne veut pas
- **Il veut :** une vraie photo de groupe générée par l'API, qui fasse studio (référence de ton : `bouteilles-gemini/resultat_gemini_v8_sombre_corrige.jpg`), puis seulement les lettres corrigées.
- **Il ne veut PAS :**
  - les montages de produits détourés alignés un par un par code : ça fait « découpé » ;
  - la retouche IA produit par produit recomposée par code.
- **Budget :** dépensé au total ≈ 0,72 $ réels sur les 5 $. Le journal `bouteilles-gemini/api-essais/depenses.csv` compte aussi une ancienne réservation fantôme de 0,20 $. Toujours un appel à la fois, et montrer avant de continuer.

### Essais de cette session
| Fichier | Contenu | Verdict |
|---|---|---|
| `bouteilles-gemini/api-essais/tour2/essai1_pro_relumiere.png` | montage refait en photo, rangée | fond bien, rendu un peu plat |
| `bouteilles-gemini/api-essais/tour2/essai2_pro_studio_fort.png` | idem, lumière poussée | bien plus photo ; textes inventés |
| `studio/groupe/groupe_essai1.png` | maquette en quinconce façon v8 (`studio/groupe/base.jpg`) refaite par Pro 2K | très photo ; projecteur ajouté en haut à gauche (effacé dans `_propre.png`) ; textes inventés |
| `studio/groupe/groupe_essai1_etiquettes.png` | même image avec les vraies étiquettes recollées | **dernière version, à vérifier** |

### Découvertes techniques importantes
- **Résolution des images envoyées :** l'API réduit chaque image envoyée à 258 tokens, en très basse définition.
  - `media_resolution` est refusé par les modèles d'image (testé gratuitement avec countTokens).
  - Conséquence : aucun modèle ne peut recopier les petits textes. Il faut **toujours recoller les vraies étiquettes après coup**.
- **Recette qui marche pour la génération :**
  - donner au modèle une maquette avec les vrais produits détourés aux bonnes places ;
  - lui demander de la « re-photographier » en studio (prompts dans `api-essais/tour2/prompt_2_studio_fort.txt` et `studio/groupe/prompt_groupe_1.txt`).
  - Il garde les places et les formes, et refait lumière, verre et reflets.
  - Il peut ajouter du matériel de studio : écrire « no studio equipment visible » dans le prompt.
- **Modèles :** vérifiés via la liste des modèles et la doc officielle. `gemini-3-pro-image` est le meilleur ; `gemini-nano-banana-2.1` est moins cher (0,034 $ en 1K).
- **SDK google-genai :** il fonctionne via le proxy avec `genai.Client(api_key='cle-injectee-par-le-proxy')` (voir `tools/packshot_ia.py`).

### Outils ajoutés (dans `tools/`)
- `recolle_scene.py` **(le plus utile)** : recolle les vraies étiquettes (détourages HD) sur une photo générée.
  - Recalage par points SIFT et RANSAC, puis ECC ; garde-fou si le recalage s'écarte de plus de 5 % de la place connue.
  - Transfère la lumière de la scène (médiane et flou) et contrôle les lettres tuile par tuile.
  - Option `--placement` (positions exactes et parties visibles venant de `base_groupe.py`).
  - Sans `--placement`, il repère les produits dans `base_montage_16x9.jpg`.
  - Pour une image qui ne vient d'aucune maquette (comme celle du client), il faudra un repérage initial : la position approximative de chaque étiquette à la main, puis SIFT.
- `base_groupe.py` + `studio/groupe.json` : maquette de groupe en quinconce, avec les vrais produits ; elle signale les étiquettes cachées.
- `nettoie_fond.py` : efface un élément parasite du fond (projecteur…) en recalculant le dégradé, sans toucher aux produits.
- `packshot_controle.py` : contrôle des lettres. Corrélation par tuile du détail fin, seuil 0,90 (une étiquette identique ré-éclairée donne 0,99 ; des lettres redessinées par l'IA 0,72 à 0,84) ; plus un OCR tesseract fiable (mots stables sur 4 lectures).
- `packshot_ia.py`, `studio_packshot.py`, `studio/config.json` : pipeline produit par produit (fond fixe, reflets, ombres). **Rejeté par le client pour le rendu**, mais `studio/config.json` contient des données réutilisables : zones d'étiquettes par produit, inclinaisons, corrections de couleur.
- Dépendances installées dans cette session, à réinstaller si besoin : `pip install opencv-python-headless google-genai scikit-image "rembg[cpu]" pytesseract` et `apt-get install tesseract-ocr tesseract-ocr-fra`.

---

## 9. Mise à jour (17/10/2026, soir) : la photo du client est intégrée

### Fait
- Le client a envoyé sa photo validée **dans le chat, et cette fois elle est bien arrivée en fichier** : copiée dans `bouteilles-gemini/photo-finale.png` (1672 × 941).
- **Elle est intégrée dans l'affiche**, versions sombre et claire, et tous les livrables sont régénérés :
  `exports/panneau-cave71-A1*.png` (3508 × 4962), `*.pdf` (150 dpi), `*-modifiable.pptx`, `apercu*.jpg`.
- `src/Panneau.tsx` : `PHOTOS.sombre` et `PHOTOS.clair` pointent sur la nouvelle photo
  (`photo_finale_sombre.jpg`, `photo_finale_claire.png`). L'ancienne photo reste accessible sous la clé `vitrine`.
  Nouveau réglage `bas` : début du fondu du bas (72 % ici), pour que le reflet du sol se dissolve au lieu d'être coupé net.
- **`tools/photo_claire_finale.py`** (nouveau) : tire la version claire de cette photo.
  Détourage BiRefNet, marche crème à la place de la marche noire, ombres de contact, reflets doux,
  raccords de plans adoucis verticalement. Repères de la photo : plateau 631–667, façade 667–788, sol à partir de 788.
  `CACHE_ALPHA=chemin.npy` garde le détourage entre deux essais.

### Limite connue
- La photo reçue fait **1672 × 941**, alors que la zone photo de l'affiche fait ~3395 px de large : elle est
  agrandie en **Lanczos + accentuation** (pas de Real-ESRGAN : le conteneur n'a ni GPU ni pilote Vulkan,
  `mesa-vulkan-drivers` n'est pas installable). Ça tient pour un chevalet de trottoir, vu à 1–2 m.
  **Si le client a l'original en plus grand, le reprendre** : on gagnerait en netteté.

### Reste à faire : les étiquettes
Défauts relevés à la loupe sur la photo du client (à corriger avec `tools/recolle_scene.py`, en repérant d'abord
à la main la position de chaque étiquette — cette image ne vient d'aucune de nos maquettes) :
| Produit | Défaut | Vrai texte |
|---|---|---|
| Terrine Goûts de Loire | « à la **Tamate** séchée » — le plus visible, en gros et en rouge | « à la **Tomate** séchée » |
| Trompe Souris | nom du bas illisible (« PUMPSTAIRS ») | « Trompe Souris » + « BLONDE » |
| Château de Gragnos | « DEPUIS **ITIO** », millésime illisible, « SAINT-CHINIAN » déformé | « DEPUIS 1710 », « 2022 », « SAINT-CHINIAN » |
| Tomatin | « ESTᴰ 18?7 », « BOUR**D**ON » | « ESTᴰ 1897 », « BOURBON & VIRGIN OAK CASKS » |
| L'Atelier d'Emile | « Fabriq**até** à la ferme » | « Fabriqué à la ferme » |
| Denis Frézier | « PRODUCED IN THE HEART OF **CHAMSAOHE** » | « … OF CHAMPAGNE » |
| La Favorite, Suntory Toki, Blacailloux, Lutgarde | petits textes brouillés (lisibles de loin, faux de près) | voir `pack-derniere-tentative/` |
Les **grands noms sont tous justes** (La Favorite, Suntory Toki, TOMATIN, Bastide de Blacailloux, Domaine Le Prieuré
des Papes, Châteauneuf-du-Pape, Château de Gragnos, Lou Daro, Champagne Denis Frézier, Lutgarde, Maison Guinguet,
Silure de Loire, Courgettes grillées).

---

## 10. Mise à jour (17/10/2026, suite) : bières dans le titre, et palettes claires et vives

### Titre
- Le grand titre devient **« Vins, bières, spiritueux & épicerie fine »** (`src/textes.json`, bloc `titre`).
- Il passe de 94 à **82 px** pour tenir sur une ligne (mesuré avec la vraie police : 1118 px de large à 84 px,
  1092 px à 82 px, pour 1160 px utiles entre les filets dorés), et `y` passe de 258 à 264 pour rester centré
  entre le logo et le sous-titre.
- **Deux lignes ne passent pas** sans rapetisser la photo : le logo descend à y≈250 et la photo commence à y≈410.
  Si le client veut le titre plus gros, il faut choisir entre titre sur deux lignes et photo pleine largeur.

### Palettes
`src/Panneau.tsx` : les couleurs ne sont plus deux constantes mais **`PALETTES`**, une entrée par version
(mêmes noms de couleurs — `or`, `creme`, `orPale`, `cremeDoux` — donc `src/textes.json` ne change pas).
Chaque palette porte aussi sa photo, ses trois arrêts de halo et la taille du halo.
`src/Root.tsx` fabrique pour chaque variante `Panneau<Nom>` et `Panneau<Nom>Fond` (fond sans texte, pour le PPTX).

| Clé | Fond | Famille |
|---|---|---|
| `sombre` | lie-de-vin (version validée) | sombre |
| `clair` | crème | claire |
| `grenat`, `vert`, `bleu` | grenat vif, vert bouteille, bleu nuit | sombres, faites avant que le client demande du clair |
| `safran` | safran | **claire et vive** |
| `corail` | corail | **claire et vive** |
| `anis` | vert anis | **claire et vive** |
| `turquoise` | turquoise | **claire et vive** |
| `framboise` | framboise | **claire et vive** |

### Photos assorties
La photo doit suivre le fond, sinon le lie-de-vin de l'image jure avec l'affiche. Deux outils :
- **`tools/photo_couleur.py`** (fonds sombres) : repeint le décor, la marche et le sol par leur luminance,
  passée dans une rampe de trois couleurs ; les reflets vifs du sol gardent leur ambre d'origine ;
  les produits ne sont pas touchés.
- **`tools/photo_claire_finale.py`** (fonds clairs) : détourage, marche et sol reconstruits en clair, puis
  **teintés à 33 % vers la couleur du fond** (`TEINTES` + `FORCE`), sans quoi la marche fait une bande blanche
  collée sur un fond coloré.
Les deux acceptent un détourage fait sur une image plus petite (`CACHE_ALPHA`) et le remettent à l'échelle :
le détourage BiRefNet prend ~1 min, la photo HD est le même cadrage agrandi.

### Livrables
- Versions principales (lie-de-vin, crème) : jeu complet dans `exports/` (PNG, PDF, PPTX, aperçu).
- Cinq variantes claires et vives : **`exports/variantes/cave71-A1-<nom>.pdf`** et `apercu-<nom>.jpg`.
  Le PNG pleine résolution et le PPTX ne sont pas générés pour elles (poids du dépôt) :
  dès que le client choisit sa couleur, `npx remotion still src/index.ts Panneau<Nom> … --scale=2.829`
  et `Panneau<Nom>Fond` donnent le jeu complet.
