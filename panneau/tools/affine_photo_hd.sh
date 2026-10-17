#!/bin/bash
# Agrandit la photo finale x4 avec Real-ESRGAN (recette du skill media-use), puis la ramène à 4000 px de large
# pour l'affiche A1 (la photo y fait ~3400 px). Real-ESRGAN rend le verre et les grandes lettres plus nets mais
# déforme les très petits textes : les étiquettes gardent un agrandissement classique fidèle (assemble_hd.py).
# Usage (depuis panneau/) : bash tools/affine_photo_hd.sh /chemin/vers/realesrgan-ncnn-vulkan [modeles/]
#   binaire : https://github.com/xinntao/Real-ESRGAN/releases (realesrgan-ncnn-vulkan-*-ubuntu.zip)
#   sans carte graphique : apt-get install mesa-vulkan-drivers (Vulkan sur processeur, ~45 min)
set -e
ESR=${1:?chemin du binaire realesrgan-ncnn-vulkan}
MOD=${2:-$(dirname "$ESR")/models}
B=bouteilles-gemini
T=$(mktemp -d)
python3 -c "from PIL import Image; Image.open('$B/resultat_chatgpt_v15_corrige.jpg').save('$T/in.png')"
"$ESR" -i "$T/in.png" -o "$T/x4.png" -n realesrgan-x4plus -m "$MOD" -t 192
python3 tools/reduit_hd.py "$T/x4.png" "$T/esr.jpg" 4000
# Real-ESRGAN invente des lettres sur les très petits textes : sur les étiquettes, agrandissement fidèle
python3 tools/assemble_hd.py $B/resultat_chatgpt_v15_corrige.jpg "$T/esr.jpg" public/produits/vitrine_sombre.jpg
rm -rf "$T"
