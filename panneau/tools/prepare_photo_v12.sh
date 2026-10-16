#!/bin/bash
# Photo finale de l'affiche (version sombre) à partir de la photo Gemini à 13 produits :
# vraies étiquettes recollées, pot de courgettes au premier plan, textes corrigés.
# Usage (depuis panneau/) : bash tools/prepare_photo_v12.sh
set -e
B=bouteilles-gemini
T=$(mktemp -d)
R="python3 tools/remplace_etiquette.py"
$R $B/resultat_gemini_v12_13produits.jpg $T/1.jpg $B/3_rouge_Chateau_de_Gragnos_Lou_Daro.jpg 30 478 205 692 1112 424 1281 670
$R $T/1.jpg $T/2.jpg $B/4_rouge_Chateauneuf-du-Pape_Prieure_des_Papes.jpg 27 536 204 721 890 597 1090 830 880 722 1007 840
$R $T/2.jpg $T/3.jpg $B/6_champagne_Denis_Frezier_Trois_Crus.jpg 53 545 192 730 1302 598 1488 821 1457 590 1500 830
$R $T/3.jpg $T/4.jpg $B/2_rose_Bastide_de_Blacailloux.jpg 21 413 183 630 720 428 864 703 700 420 728 710
OVALE=1 $R $T/4.jpg $T/5.jpg $B/nouveaux-produits/biere_Lutgarde_Blonde_photo.jpg 43 256 243 509 1461 646 1613 855 1586 630 1620 870
python3 tools/ajoute_produit.py $T/5.jpg $T/6.jpg $B/nouveaux-produits/tartinable_courgettes_detoure.png 1196 708 232 \
    --etendre-bas 64 --ref 1150 860 1250 890 0.3 0.66 0.7 0.75
python3 tools/corrige_textes_photo.py $T/6.jpg $B/resultat_gemini_v12_final.jpg v12
cp $B/resultat_gemini_v12_final.jpg public/produits/vitrine_sombre.jpg
rm -rf $T
