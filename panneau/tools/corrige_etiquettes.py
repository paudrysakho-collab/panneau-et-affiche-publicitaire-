import sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
src, out, font = sys.argv[1], sys.argv[2], sys.argv[3]
im = np.array(Image.open(src).convert('RGB'))

def inpaint(box, pred):
    x0, y0, x1, y1 = box
    reg = im[y0:y1, x0:x1].astype(int)
    m = pred(reg).astype(np.uint8) * 255
    m = cv2.dilate(m, np.ones((3, 3), np.uint8), iterations=2)
    full = np.zeros(im.shape[:2], np.uint8); full[y0:y1, x0:x1] = m
    return cv2.inpaint(im, full, 4, cv2.INPAINT_TELEA)

def lum(r): return 0.299 * r[..., 0] + 0.587 * r[..., 1] + 0.114 * r[..., 2]
def sat(r): return r.max(-1) - r.min(-1)

# 1) plaque Boitasac : texte gris-olive peu saturé, plus sombre que la plaque claire
x0, y0, x1, y1 = 1462, 938, 1648, 966
reg = im[y0:y1, x0:x1].astype(float)
L = lum(reg); Sat = sat(reg)
xs = np.arange(reg.shape[1])[None, :] + x0
choco = (Sat > 38) & (L < 150) & (xs < 1488)
fond = np.zeros_like(reg)
for yy in range(reg.shape[0]):
    ok = L[yy] > 175
    fond[yy] = np.median(reg[yy][ok], axis=0) if ok.sum() > 5 else (fond[yy - 1] if yy else reg[yy].mean(0))
rng = np.random.default_rng(0)
fond += rng.normal(0, 1.5, fond.shape)
plaque = np.zeros(L.shape, np.uint8)
poly = np.array([[1464, 937], [1645, 944], [1645, 964], [1464, 957]]) - [x0, y0]
cv2.fillPoly(plaque, [poly.astype(np.int32)], 255)
plaque = plaque.astype(bool)
lettres = (L < fond.mean(-1) - 18) & ~choco & plaque
lettres = cv2.dilate(lettres.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=1).astype(bool) & ~choco & plaque
reg = np.where(lettres[..., None], fond, reg)
im[y0:y1, x0:x1] = np.clip(reg, 0, 255).astype(np.uint8)
# 2) ligne Syrah : texte prune foncé sur fond rose
im = inpaint((410, 664, 540, 683), lambda r: lum(r) < 120)

pil = Image.fromarray(im)

def texte(txt, box_w, cap_h, color, center, angle=0, weight='Regular', track=0.0, squeeze=1.0):
    f = ImageFont.truetype(font, 200)
    try: f.set_variation_by_name(weight)
    except Exception: pass
    # rendu grand, puis réduction
    tmp = Image.new('L', (4000, 400), 0); d = ImageDraw.Draw(tmp)
    x = 20
    for ch in txt:
        d.text((x, 100), ch, font=f, fill=255)
        x += d.textlength(ch, font=f) + track * 200
    tmp = tmp.crop(tmp.getbbox())
    cap = f.getbbox('H')[3] - f.getbbox('H')[1]
    k = cap_h / cap
    w = int(tmp.width * k * squeeze); h = int(tmp.height * k)
    if box_w and w > box_w:
        w = box_w
    tmp = tmp.resize((max(1, w), max(1, h)), Image.LANCZOS)
    if angle: tmp = tmp.rotate(angle, resample=Image.BICUBIC, expand=True)
    layer = Image.new('RGBA', tmp.size, color + (0,)); layer.putalpha(tmp)
    pil.alpha_composite(layer, (int(center[0] - tmp.width / 2), int(center[1] - tmp.height / 2))) if pil.mode == 'RGBA' else None
    return layer, (int(center[0] - tmp.width / 2), int(center[1] - tmp.height / 2))

pil = pil.convert('RGBA')
l, pos = texte('CHOCOLAT NOIR', 176, 19, (104, 100, 82), (1553, 952), angle=-1.6, weight='Regular', track=0.08)
l, pos = texte('SANS SUCRE AJOUTÉ*', 124, 10.5, (74, 42, 52), (474, 674), weight='SemiBold', track=0.02, squeeze=0.82)
pil.convert('RGB').save(out, quality=95)
