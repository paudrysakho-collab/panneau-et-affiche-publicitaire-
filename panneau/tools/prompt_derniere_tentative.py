"""Écrit le prompt de la dernière tentative (ChatGPT / Gemini) en deux versions complètes, à partir d'un seul
texte commun : 14 images (une par produit + photo modèle), ou 2 images (planche numérotée + photo modèle).
Les textes entre « » ont été transcrits puis vérifiés produit par produit sur les images du pack.

Usage (depuis panneau/) :
    python3 tools/prompt_derniere_tentative.py bouteilles-gemini/pack-derniere-tentative/PROMPT-ChatGPT-derniere-tentative.txt
"""
import sys

IMAGES_14 = """LES IMAGES JOINTES
- Images 1 à 13 : les produits n° 1 à n° 13, un par image. Ce sont les VRAIS produits : leur forme, leurs couleurs et leurs étiquettes doivent être recopiées fidèlement d'après ces images, sans rien redessiner ni inventer. Seul le produit compte : ignore le fond de ces photos (table en bois, étagère, main).
- Image 14 : la photo modèle (notre composition actuelle)."""

IMAGES_2 = """LES IMAGES JOINTES
- 1re image : une planche avec les 13 VRAIS produits, numérotés de 1 à 13 dans des ronds gris. Ces numéros ne sont que des repères : ne les reproduis pas. Leur forme, leurs couleurs et leurs étiquettes doivent être recopiées fidèlement d'après cette planche, sans rien redessiner ni inventer. Seul le produit compte : ignore le fond des photos de la planche (table en bois, étagère, main).
- 2e image : la photo modèle (notre composition actuelle)."""

CORPS = """Photo publicitaire photoréaliste (une vraie photo de studio, pas une illustration) pour l'affiche A1 de ma cave à vins : les 13 produits joints réunis sur une seule photo de groupe.

{images}
La photo modèle sert pour l'ambiance : fond, lumière, reflets, ordre général des produits. Elle a deux défauts à corriger : certains produits y cachent les étiquettes d'autres, et les tailles n'y sont pas justes. Pour le placement et les tailles, suis donc COMPOSITION ci-dessous. Si un détail d'un produit diffère entre la photo modèle et l'image du produit, c'est l'image du produit qui a raison.

DÉCOR ET LUMIÈRE
Fond lie-de-vin très sombre avec un halo chaud au centre, derrière les bouteilles. Lumière de studio douce venant de la gauche, reflets blancs nets sur le verre, liquides lumineux (rhum, whiskies, rosé), noirs profonds mais détaillés. Surface sombre et brillante qui reflète doucement la base des produits.

COMPOSITION
- Les 10 bouteilles et le sachet de chocolats sont debout côte à côte sur une marche basse, noire et brillante, d'environ 10 cm de haut, qui traverse toute la photo. De gauche à droite : n° 1 rhum, n° 2 jus de raisin, n° 3 et n° 4 whiskies, n° 5 rosé, n° 6 et n° 7 vins rouges, n° 8 champagne, n° 9 et n° 10 bières, n° 11 sachet de chocolats.
- Devant la marche, plus bas, sur la surface brillante : le n° 12 (terrine) et le n° 13 (pot de courgettes) en bas au centre, côte à côte ; et un seul petit groupe de morceaux de chocolat (ceux de l'image du n° 11) devant la bière n° 9.
- La marche est assez haute pour que les deux pots et les morceaux de chocolat ne cachent aucune étiquette. Les produits sont légèrement espacés : aucun ne cache l'étiquette d'un autre.
- Exactement 13 produits, chacun une seule fois.
- Tailles réelles, à respecter entre elles : vins et champagne ≈ 30 cm ; rhum ≈ 27 cm ; Tomatin ≈ 26 cm ; Toki ≈ 25 cm ; bière n° 10 ≈ 23 cm (fine) ; sachet de chocolats ≈ 23 cm ; bière n° 9 ≈ 19 cm (trapue) ; jus de raisin ≈ 17 cm ; terrine ≈ 8 cm (aussi large que haute) ; pot de courgettes ≈ 8,5 cm (plus haut que large).
- Rien de coupé : de la marge tout autour, le bas des pots et leurs reflets compris.

LES 13 PRODUITS
Les titres (avant les deux-points) ne sont que des repères pour toi : sur les produits, n'écris QUE les textes entre « ». Recopie chacun EXACTEMENT (orthographe, accents, majuscules), une seule fois, à sa place sur son produit (seul « CHAMPAGNE » apparaît deux fois, sur le n° 8 : sur la coiffe et sur l'étiquette). Tous les autres petits textes des étiquettes : rends-les flous et illisibles, comme sur une vraie photo vue de loin ; ne les écris jamais lisiblement.

N° 1, rhum : bouteille droite au corps large, épaules arrondies et long col droit, verre transparent, rhum ambré doré, bouchon à tête en bois clair (pas de capsule). Étiquette crème bordée de cannes à sucre dorées, gravure d'une distillerie au centre. Textes : « DISTILLERIE » (en arc), « La Favorite » (grande écriture script brun-noir, sur deux niveaux comme sur l'image), « Cœur de Canne » (doré, avec la lettre œ), « RHUM AGRICOLE AMBRÉ », pastille rouge « 2 ans » (en blanc, le chiffre au-dessus du mot), bandeau brun foncé « MARTINIQUE ».

N° 2, jus de raisin : petite bouteille ronde type bouteille de lait, capsule en métal argenté, jus presque noir aux reflets prune. Étiquette rose en haut, blanche en bas. Textes : « 04 » (petite case blanche en haut), « CÉPAGE », « SYRAH » (grand, en blanc), « PUR JUS DE RAISINS », « SANS SUCRE AJOUTÉ* », sceau rond « ƎXE » (le premier E retourné en miroir), logo bio vert « AB ».

N° 3, whisky : bouteille carrée en verre épais, gros bouchon noir mat, whisky or pâle. Étiquette blanc cassé. À gauche : « SUNTORY », « WHISKY » (noir), « TOKI™ » (rouge), « FROM THE HOUSE OF », « SUNTORY WHISKY », « JAPANESE WHISKY ». À droite : le grand idéogramme japonais « 季 » tracé au pinceau noir, avec un petit sceau carré rouge, exactement comme sur l'image.

N° 4, whisky : bouteille ronde à larges épaules et pied évasé, whisky ambre doré, capsule bleu nuit avec « Highlands » en écriture script dorée. Le haut de l'étiquette est TRANSPARENT : « EST » suivi d'un petit D surélevé et souligné, un blason argenté et « 1897 », puis « TOMATIN » (grand), « HIGHLAND SINGLE MALT » et « SCOTCH WHISKY », imprimés en blanc crème directement sur le verre (on voit le whisky derrière). Plus bas seulement, un panneau bleu marine avec « LEGACY » (doré, entre deux ornements) et un petit paragraphe flou, puis un bandeau crème « BOURBON & VIRGIN OAK CASKS » (lettres bleu marine).

N° 5, rosé : bouteille élancée en verre extra-blanc, rosé très pâle couleur pêche, capsule crème à liseré doré. Étiquette blanche avec un petit médaillon gravé en haut. Textes : « BASTIDE DE », « BLACAILLOUX », « JOIO » (lettres très fines or pâle ; le I est surmonté d'un point détaché), « 2025 » (petit), « VIN DE PROVENCE ».

N° 6, vin rouge : bouteille bourguignonne en verre noir, capsule bordeaux brillante. Étiquette crème placée bas, gravure du domaine à gauche. Textes : « DOMAINE », « LE PRIEURÉ », « DES PAPES » (serif brun-rouge), « Châteauneuf-du-Pape » (lettres gothiques), « VIEILLES VIGNES ».

N° 7, vin rouge : bouteille bourguignonne en verre noir, capsule noire. Étiquette ivoire avec un arbre dessiné en bas à gauche. Textes : « CHÂTEAU », « DE GRAGNOS », « DEPUIS 1710 » ; à droite « LOU » (le L un peu plus haut que les deux autres lettres), « DARO », « SAINT-CHINIAN » (la dernière lettre est bien un N), « 2022 ».

N° 8, champagne : bouteille de champagne en verre vert olive foncé, coiffe noire avec « CHAMPAGNE » écrit verticalement en argent, collerette cuivrée. Étiquette blanc cassé avec un petit écusson en haut. Textes : « CHAMPAGNE », « DENIS FRÉZIER » (en petites capitales, initiales plus hautes), « PRODUCED IN THE HEART OF CHAMPAGNE » (petit), « Cuvée des Trois Crus » (écriture manuscrite : le premier mot en or pâle, la suite en noir), « PREMIER BRUT », « ESTATE BOTTLED » (petit).

N° 9, bière : petite bouteille trapue en verre brun très foncé, capsule rouge. Étiquette ovale : anneau rouge et centre crème avec une religieuse au voile bleu marine. Textes : « BELGIAN ABBEY BEER » (en arc en haut), « LUTGARDE » (grand, rouge), « BLONDE » (dans un cartouche rouge), « 33 cl », « Alc vol 6% », « Abbaye d'Aywiers » (en arc en bas).

N° 10, bière : bouteille de bière élancée (long neck) en verre brun ambré, bière blonde, capsule jaune. Étiquette entièrement illustrée, sans cadre, recopiée exactement d'après l'image : deux souris sur une mobylette bleue, toutes deux avec un casque rose et des lunettes, le mot « BLONDE » en jaune, et en bas le nom de la bière en grandes lettres noires fines, tel qu'il apparaît sur l'image.

N° 11, chocolats : sachet en cellophane transparent fermé par une rose en papier beige, rempli d'éclats de chocolat et de billes chocolatées, posé dans un étui en carton brun chocolat au bord festonné doré. Textes : « MAISON » et « GUINGUET » (crème, sous un médaillon rond), bandeau crème « CHOCOLAT NOIR ».

N° 12, terrine : verrine basse, couvercle en métal argenté, chair de poisson beige visible sous l'étiquette. Étiquette noire. Textes : « GOÛTS », « DE », « LOIRE » (serif rouge en petites capitales, première lettre plus haute, le I de la fin pointé ; le mot du milieu est en haut du médaillon blanc), médaillon blanc avec une barque bleue dessinée, « Silure de Loire » (blanc, très gras), bande rouge « à la Tomate séchée » (écriture script brun-noir), languette rouge « BIO ».

N° 13, pot de courgettes : pot en verre, capsule noire brillante, tartinade vert foncé. Étiquette blanche. Textes : monogramme « E » noir géométrique (un rond vert à la place de la barre du milieu, deux feuilles vertes à gauche), « L’ATELIER », « d’Emile » (écriture script, le prénom en vert, sans accent sur le E), à gauche « Fabriqué » / « à la ferme » sur deux lignes entre deux petits coins d'angle, « Tartinable de », « COURGETTES » (gras), « GRILLÉES », bande vert clair en bas avec un petit drapeau français.

INTERDIT
Aucun texte ajouté, aucun filigrane, aucun logo inventé, aucun produit en plus ou en double, aucune étiquette redessinée à la manière de l'originale. Ne change ni les couleurs des étiquettes ni la forme des bouteilles.

FORMAT
Paysage 16:9, la plus haute définition possible, mise au point nette sur toutes les étiquettes."""

TRAIT = '-' * 96

ENTETE = f"""=== DERNIÈRE TENTATIVE : CHATGPT (génération d'images) ===

VERSION A (conseillée) : 14 images
1. Ouvre une NOUVELLE conversation sur chatgpt.com (site web, pas l'appli téléphone).
   Si tu as un abonnement, choisis le modèle « Thinking » : il gère mieux les images complexes.
2. Joins les 14 images DANS L'ORDRE, en un seul message : 01_... 02_... jusqu'à 14_composition_actuelle_modele.jpg
   (ChatGPT web accepte jusqu'à 20 fichiers par message). N'envoie PAS la 15 (planche).
3. Colle tout le texte de la VERSION A (entre les deux lignes de tirets), puis envoie.
4. Envoie-moi l'image obtenue : je vérifie chaque étiquette à la loupe et je recolle les vraies là où il
   faut, comme pour la version actuelle.

VERSION B : 2 images, si ChatGPT refuse 14 images, ou pour Gemini (10 images maximum)
Joins dans cet ordre : 15_planche_13_produits.jpg puis 14_composition_actuelle_modele.jpg,
et colle tout le texte de la VERSION B. Dans Gemini, choisis le modèle « Pro » ou « Thinking », pas « Rapide ».
"""


def main():
    a = CORPS.format(images=IMAGES_14)
    b = CORPS.format(images=IMAGES_2).replace("d'après l'image", "d'après la planche").replace(
        "entre la photo modèle et l'image du produit, c'est l'image du produit qui a raison",
        "entre la photo modèle et la planche, c'est la planche qui a raison").replace(
        "(ceux de l'image du n° 11)", "(ceux du n° 11 sur la planche)").replace(
        "exactement comme sur l'image", "exactement comme sur la planche").replace(
        "tel qu'il apparaît sur l'image", "tel qu'il apparaît sur la planche").replace(
        "sur deux niveaux comme sur l'image", "sur deux niveaux comme sur la planche")
    texte = (ENTETE + f"\n\n=== VERSION A : 14 IMAGES ===\n{TRAIT}\n{a}\n{TRAIT}\n\n\n"
             f"=== VERSION B : PLANCHE + PHOTO MODÈLE (2 IMAGES) ===\n{TRAIT}\n{b}\n{TRAIT}\n")
    open(sys.argv[1], 'w').write(texte)
    print(sys.argv[1], len(a.split()), 'mots (version A)')
    reste = [m for m in ("l'image", 'image 14', 'Image 14') if m in b]
    print('version B, références à une image restantes :', reste or 'aucune')


if __name__ == '__main__':
    main()
