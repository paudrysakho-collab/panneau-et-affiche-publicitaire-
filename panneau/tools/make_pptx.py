"""Génère exports/panneau-cave71-A1-modifiable.pptx.

Fond = rendu Remotion de la composition « PanneauFond » (sans texte ni logo),
puis le logo en image déplaçable et chaque bloc de src/textes.json en zone de texte modifiable.

Usage (depuis panneau/) :
    npx remotion still src/index.ts PanneauFond exports/fond.png --scale=2.829
    python3 tools/make_pptx.py
"""
import json
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Mm, Pt

RACINE = Path(__file__).resolve().parent.parent
LARGEUR_PX, HAUTEUR_PX = 1240, 1754
LARGEUR_MM = 594.0
MM_PAR_PX = LARGEUR_MM / LARGEUR_PX
PT_PAR_PX = MM_PAR_PX / 0.352778

COULEURS = {
    'or': (0xCF, 0xA5, 0x48),
    'orPale': (0xE6, 0xCF, 0x98),
    'creme': (0xF4, 0xEC, 0xE0),
    'cremeDoux': (0xC8, 0xC1, 0xB7),
}
POLICES = {'serif': 'Cormorant Garamond', 'sans': 'Montserrat'}
ALIGN = {'left': PP_ALIGN.LEFT, 'center': PP_ALIGN.CENTER, 'right': PP_ALIGN.RIGHT}


def px(v):
    return Mm(v * MM_PAR_PX)


def main():
    textes = json.loads((RACINE / 'src/textes.json').read_text(encoding='utf-8'))

    fond_png = RACINE / 'exports/fond.png'
    fond_jpg = RACINE / 'exports/fond.jpg'
    Image.open(fond_png).convert('RGB').save(fond_jpg, quality=92)

    prs = Presentation()
    prs.slide_width = px(LARGEUR_PX)
    prs.slide_height = px(HAUTEUR_PX)
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    slide.shapes.add_picture(str(fond_jpg), 0, 0, prs.slide_width, prs.slide_height)
    slide.shapes.add_picture(str(RACINE / 'public/logo_cave71_transparent.png'), px(300), px(112), width=px(640))

    for bloc in textes['blocs']:
        interligne = bloc.get('interligne', 1.2)
        hauteur = sum(max(s['taille'] for s in ligne) * interligne for ligne in bloc['lignes'])
        boite = slide.shapes.add_textbox(px(bloc['x']), px(bloc['y']), px(bloc['w']), px(hauteur))
        boite.name = bloc['id']
        tf = boite.text_frame
        tf.word_wrap = False
        tf.auto_size = None
        tf.vertical_anchor = MSO_ANCHOR.TOP
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)

        for i, ligne in enumerate(bloc['lignes']):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.alignment = ALIGN[bloc['align']]
            para.line_spacing = Pt(max(seg['taille'] for seg in ligne) * interligne * PT_PAR_PX)
            for seg in ligne:
                run = para.add_run()
                run.text = seg['t']
                f = run.font
                f.name = POLICES[seg['police']]
                f.size = Pt(seg['taille'] * PT_PAR_PX)
                f.bold = seg.get('graisse', 400) >= 600
                f.italic = bool(seg.get('italique'))
                f.color.rgb = RGBColor(*COULEURS[seg['couleur']])
                if seg.get('espacement'):
                    run._r.get_or_add_rPr().set('spc', str(round(seg['espacement'] * PT_PAR_PX * 100)))
                rpr = run._r.get_or_add_rPr()
                for tag in ('a:latin', 'a:cs'):
                    el = rpr.find(qn(tag))
                    if el is None:
                        el = rpr.makeelement(qn(tag), {})
                        rpr.append(el)
                    el.set('typeface', POLICES[seg['police']])

    sortie = RACINE / 'exports/panneau-cave71-A1-modifiable.pptx'
    prs.save(sortie)
    print(sortie)


if __name__ == '__main__':
    main()
