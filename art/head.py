# Title picture: a big mean bull's head, face on. Pale horns with dark tips, ears, a white blaze, angry eyes,
# pale muzzle, flared nostrils and a scowl. 6 frames: stare, stare, blink, snort/bellow (head dips, mouth open), grind left, grind right.
import numpy as np, math
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, binary_erosion
S = 8; W, H = 62, 64; cx = 31
def P(x, y): return (x * S, (y - 2.5) * S)          # whole head drawn 2.5 px higher so PRESS ANY BUTTON fits under it
def down(a): return a.reshape(H, S, W, S).mean(axis=(1, 3)) > 0.5
def layer(): im = Image.new('L', (W * S, H * S), 0); return im, ImageDraw.Draw(im)
def head(f):
    dy = 1 if f == 3 else 0
    face, d = layer(); horn, h = layer(); white, w = layer(); dark, k = layer(); teeth, t2 = layer()
    for s in (-1, 1):                                                   # horns: out, then curling up, thick at the root
        for t in np.linspace(0, 1, 80):
            x = cx + s * (9 + 18 * math.sin(t * 1.75)); y = 18 + dy - 13.5 * t ** 1.5; r = 4.2 * (1 - t) ** 0.7 + 0.7
            h.ellipse([P(x - r, y - r), P(x + r, y + r)], fill=255)
            if t > 0.82: k.ellipse([P(x - r, y - r), P(x + r, y + r)], fill=255)          # dark tips
        d.polygon([P(cx + s * 10, 21 + dy), P(cx + s * 24, 19 + dy), P(cx + s * 25, 23 + dy), P(cx + s * 13, 28 + dy)], fill=255)   # ear
    d.polygon([P(cx - 13, 12 + dy), P(cx + 13, 12 + dy), P(cx + 15, 22 + dy), P(cx + 11, 33 + dy), P(cx + 12, 41 + dy),
               P(cx - 12, 41 + dy), P(cx - 11, 33 + dy), P(cx - 15, 22 + dy)], fill=255)
    for x0 in (-6, -2, 2, 6): d.ellipse([P(cx + x0 - 3, 9 + dy), P(cx + x0 + 3, 15 + dy)], fill=255)   # curly topknot
    jaw = 3 if f == 3 else 0                                                                          # jaw drops on the bellow
    d.rounded_rectangle([P(cx - 15, 36 + dy), P(cx + 15, 55 + dy + jaw)], radius=8 * S, fill=255)           # broad muzzle outline
    w.rounded_rectangle([P(cx - 13.5, 37.5 + dy), P(cx + 13.5, 53.5 + dy + jaw)], radius=7 * S, fill=255)   # pale muzzle
    # mouth: gritted teeth; frames 4/5 grind the bottom teeth side to side; the snort (3) opens wide and bellows
    if f == 3:
        k.rounded_rectangle([P(cx - 9, 47 + dy), P(cx + 9, 56 + dy)], radius=2.5 * S, fill=255)
        tb, bb, g = (48.2, 49.6), (53.4, 54.8), 0
    else:
        k.rounded_rectangle([P(cx - 9, 46.5 + dy), P(cx + 9, 53 + dy)], radius=1.5 * S, fill=255)
        tb, bb, g = (48, 49.4), (50.6, 52), (-2 if f == 4 else 2 if f == 5 else 0)
    for x0 in (-6, -3, 0, 3, 6):                                                                        # white teeth, top and bottom row
        t2.rectangle([P(cx + x0 - 1, tb[0] + dy), P(cx + x0 + 1, tb[1] + dy)], fill=255)
        if abs(x0 + g) <= 7.5: t2.rectangle([P(cx + x0 + g - 1, bb[0] + dy), P(cx + x0 + g + 1, bb[1] + dy)], fill=255)
    for s in (-1, 1):
        w.polygon([P(cx + s * 3, 26 + dy), P(cx + s * 13.5, 18.5 + dy), P(cx + s * 13.5, 27 + dy), P(cx + s * 10, 30.5 + dy), P(cx + s * 5, 30.5 + dy)], fill=255)   # eye whites, brows slammed down steep to the middle
        if f == 2: k.polygon([P(cx + s * 2, 26 + dy), P(cx + s * 14.5, 17.5 + dy), P(cx + s * 14.5, 28 + dy), P(cx + s * 10, 32 + dy), P(cx + s * 4, 32 + dy)], fill=255)        # blink
        else: k.ellipse([P(cx + s * 7.5 - 2.3, 25.4 + dy), P(cx + s * 7.5 + 2.3, 30.6 + dy)], fill=255)    # small pupils glaring in
        r = 2.8 if f == 3 else 2.3
        k.ellipse([P(cx + s * 7 - r, 41.5 + dy - r * 0.4), P(cx + s * 7 + r, 44.5 + dy + r * 0.4)], fill=255)   # flared nostrils
    m = down(np.array(face) > 127); hm = down(np.array(horn) > 127) & ~m
    wm = down(np.array(white) > 127); km = down(np.array(dark) > 127)
    ink = (m & ~wm) | km
    ink |= hm & ~binary_erosion(hm, iterations=1)                     # horns: pale with a dark outline
    ink &= ~(hm & binary_erosion(hm, iterations=1) & ~km)
    ink |= (binary_dilation(m, iterations=1) & ~m & ~hm)              # crisp edge
    ink &= ~down(np.array(teeth) > 127)
    return ink
fr = [head(f) for f in range(6)]
np.save('head.npy', np.stack(fr))
row = np.hstack([np.pad(np.where(f, 0, 255).astype(np.uint8), 2, constant_values=120) for f in fr])
Image.fromarray(row).resize((row.shape[1] * 5, row.shape[0] * 5), Image.NEAREST).save(__import__('tempfile').gettempdir() + '/bo_head.png')
