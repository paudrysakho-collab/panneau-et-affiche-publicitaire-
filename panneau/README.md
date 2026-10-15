# Panneau chevalet Cave 71

Affiche A1 portrait (594 × 841 mm) pour le stop-trottoir devant la cave, construite avec
[Remotion](https://www.remotion.dev) (composition React rendue en image fixe).

## Fichiers prêts à imprimer

- `exports/panneau-cave71-A1.pdf` : PDF A1, 150 dpi, à envoyer à l'imprimeur
- `exports/panneau-cave71-A1.png` : même visuel en PNG 3508 × 4962 px
- `exports/apercu.jpg` : aperçu léger pour partager
- `exports/panneau-cave71-A1-modifiable.pptx` : même affiche dans PowerPoint, textes modifiables
  (installer d'abord les polices de `public/fonts/` : Cormorant Garamond et Montserrat)

## Modifier l'affiche

```bash
npm install
npm run studio   # aperçu en direct dans le navigateur
npm run render   # régénère exports/panneau-cave71-A1.png
```

Les textes sont dans `src/textes.json` (utilisé à la fois par l'affiche et par le PPTX).
Pour régénérer le PPTX :

```bash
npx remotion still src/index.ts PanneauFond exports/fond.png --scale=2.829
python3 tools/make_pptx.py
```

Le reste se règle dans `src/Panneau.tsx` : la liste `BOUTEILLES` (position `x`, hauteur `h`, base `base`, empilement `z`),
la liste `TERRINES`, les `SERVICES`, les textes et les couleurs `C`.
Les photos sont dans `public/produits/` (PNG détourés), le logo dans `public/`.

## Contenu

- Vins (photos du catalogue caviste 2026) : Bastide de Blacailloux rosé, Château de Gragnos
  Lou Daro, Châteauneuf-du-Pape Prieuré des Papes, Château Balac, Champagne Denis Frezier
- Spiritueux : Suntory Toki, rhum La Favorite Cœur de Canne
- Sans alcool : Divin Sauvignon blanc 0,0 %, jus de cépage Syrah Famille d'Exea
- Épicerie : terrines Goûts de Loire (silure à la tomate séchée, poissons de Loire au
  Touraine Sauvignon), chocolats Maison Guinguet (Boitasac noir)

## Avant impression

- Vérifier le format exact du cadre du chevalet (A1 supposé). Si l'imprimeur demande des
  fonds perdus, ajouter 3 mm de chaque côté.
- Le logo vient du site cave71.com (701 px de large). Un fichier vectoriel (PDF, AI, SVG)
  le rendrait encore plus net.
- La mention « L'abus d'alcool est dangereux pour la santé… » est obligatoire (loi Évin).
