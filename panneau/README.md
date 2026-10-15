# Panneau chevalet Cave 71

Affiche A1 portrait (594 × 841 mm) pour le stop-trottoir devant la cave, construite avec
[Remotion](https://www.remotion.dev) (composition React rendue en image fixe).

## Fichiers prêts à imprimer

- `exports/panneau-cave71-A1.pdf` : PDF A1, 150 dpi, à envoyer à l'imprimeur
- `exports/panneau-cave71-A1.png` : même visuel en PNG 3508 × 4962 px
- `exports/apercu.jpg` : aperçu léger pour partager

## Modifier l'affiche

```bash
npm install
npm run studio   # aperçu en direct dans le navigateur
npm run render   # régénère exports/panneau-cave71-A1.png
```

Tout se règle dans `src/Panneau.tsx` : la liste `BOUTEILLES` (position `x`, hauteur `h`),
la liste `TERRINES`, les `SERVICES`, les textes et les couleurs `C`.
Les photos sont dans `public/produits/` (PNG détourés), le logo dans `public/`.

## Contenu

- Vins (photos du catalogue caviste 2026) : Bastide de Blacailloux rosé, Château de Gragnos
  Lou Daro, Châteauneuf-du-Pape Prieuré des Papes, Château Balac, Champagne Denis Frezier
- Spiritueux : Suntory Toki, rhum La Favorite Cœur de Canne
- Épicerie : terrines de faisan et de perdrix (Saveurs de Gallinacés), silure de Loire et
  poissons de Loire (Goûts de Loire)

## Avant impression

- Vérifier le format exact du cadre du chevalet (A1 supposé). Si l'imprimeur demande des
  fonds perdus, ajouter 3 mm de chaque côté.
- Le logo vient du site cave71.com (701 px de large). Un fichier vectoriel (PDF, AI, SVG)
  le rendrait encore plus net.
- La mention « L'abus d'alcool est dangereux pour la santé… » est obligatoire (loi Évin).
