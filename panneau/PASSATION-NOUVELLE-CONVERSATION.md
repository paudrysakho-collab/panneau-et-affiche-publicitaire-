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
