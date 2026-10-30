# "Hey Bucko" screen: a grizzled old rodeo cowboy, shaded and dithered like the Glorb portrait,
# looking at you from the left, with a speech bubble on the right (bubble drawn in the game).
# Built as a tone map (0 = black, 1 = white), then ordered-dithered to 1 bit, then outlined.
import numpy as np, math
from PIL import Image, ImageDraw
S = 8; W, H = 60, 60
B4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]])
def layer(): im = Image.new('L', (W * S, H * S), 0); return im, ImageDraw.Draw(im)
def P(x, y): return (x * S, y * S)
def down(im): return np.array(im).reshape(H, S, W, S).mean(axis=(1, 3)) / 255.0
tone = np.ones((H, W)); shape = np.zeros((H, W), bool)
yy, xx = np.mgrid[0:H, 0:W]
def paint(mask, t):                                   # t: a number or an array (shading)
    global tone, shape
    m = mask > 0.5; tone = np.where(m, t, tone); shape |= m
def lit(cx, cy, rx, ry, base, amt):                   # light from the upper left, a soft round form
    nx = (xx - cx) / rx; ny = (yy - cy) / ry; nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    return np.clip(base + amt * (-0.55 * nx - 0.5 * ny + 0.6 * nz - 0.35), 0, 1)
cx = 30
# shirt and shoulders (dark denim) + bandana
im, d = layer(); d.polygon([P(4, 60), P(8, 50), P(20, 46), P(40, 46), P(52, 50), P(56, 60)], fill=255); paint(down(im), lit(30, 54, 30, 14, 0.55, 0.5))
im, d = layer(); d.polygon([P(19, 46), P(41, 46), P(36, 55), P(30, 58), P(24, 55)], fill=255); paint(down(im), 0.12)   # bandana
# neck
im, d = layer(); d.rectangle([P(23, 38), P(37, 47)], fill=255); paint(down(im), lit(30, 42, 10, 8, 0.55, 0.4))
# ears
for s in (-1, 1):
    im, d = layer(); d.ellipse([P(cx + s * 15 - 3, 24), P(cx + s * 15 + 3, 33)], fill=255); paint(down(im), lit(cx + s * 15, 28, 4, 5, 0.85, 0.4))
# face: long and craggy
im, d = layer(); d.ellipse([P(cx - 14, 14), P(cx + 14, 46)], fill=255); paint(down(im), lit(cx - 4, 26, 18, 20, 1.05, 0.45))
# heavy brows, squinting eyes, crow's feet
for s in (-1, 1):
    im, d = layer(); d.polygon([P(cx + s * 1.5, 22.5), P(cx + s * 11, 20.5), P(cx + s * 12.5, 23), P(cx + s * 3, 25)], fill=255); paint(down(im), 0.0)   # brow
    im, d = layer(); d.line([P(cx + s * 3.5, 27.2), P(cx + s * 10, 26.6)], fill=255, width=int(2.2 * S)); paint(down(im), 0.0)                          # squint
    im, d = layer(); d.ellipse([P(cx + s * 6.5 - 2, 25.2), P(cx + s * 6.5 + 2, 29)], fill=255); paint(down(im), 0.0)                       # glint-less eye
    im, d = layer(); d.line([P(cx + s * 11, 26), P(cx + s * 13, 25)], fill=255, width=S); d.line([P(cx + s * 11, 27.5), P(cx + s * 13, 28.5)], fill=255, width=S); paint(down(im), 0.25)
# nose: big and bulbous with a shadow underneath
im, d = layer(); d.polygon([P(cx - 1.5, 25), P(cx + 1.5, 25), P(cx + 3.5, 33), P(cx - 3.5, 33)], fill=255); paint(down(im), lit(cx - 1, 30, 4, 5, 1.05, 0.4))
im, d = layer(); d.ellipse([P(cx - 4.5, 31), P(cx + 4.5, 36)], fill=255); paint(down(im), lit(cx - 1, 33, 5, 3, 1.0, 0.5))
im, d = layer(); d.ellipse([P(cx - 3, 34), P(cx - 1, 35.5)], fill=255); d.ellipse([P(cx + 1, 34), P(cx + 3, 35.5)], fill=255); paint(down(im), 0.0)   # nostrils
im, d = layer(); d.arc([P(cx - 4.5, 31), P(cx + 4.5, 36)], 200, 340, fill=255, width=S); d.line([P(cx + 1.5, 25), P(cx + 3.6, 32)], fill=255, width=S); paint(down(im), 0.0)   # nose edge
# big handlebar moustache
im, d = layer()
d.polygon([P(cx, 35.5), P(cx - 5, 35.5), P(cx - 10, 37), P(cx - 14, 36), P(cx - 16, 33), P(cx - 15, 37.5), P(cx - 11, 40), P(cx - 4, 39.5), P(cx, 38.5)], fill=255)
d.polygon([P(cx, 35.5), P(cx + 5, 35.5), P(cx + 10, 37), P(cx + 14, 36), P(cx + 16, 33), P(cx + 15, 37.5), P(cx + 11, 40), P(cx + 4, 39.5), P(cx, 38.5)], fill=255)
paint(down(im), 0.0)
im, d = layer(); d.line([P(cx - 12, 37), P(cx - 5, 36.6)], fill=255, width=S); d.line([P(cx + 5, 36.6), P(cx + 12, 37)], fill=255, width=S); paint(down(im), 1.0)   # shine on the moustache
# grin under the moustache, a tooth missing
MOUTH = globals().get('MOUTH', 1)                 # 1 = mouth open (talking), 0 = shut under the moustache
if MOUTH:
    im, d = layer(); d.chord([P(cx - 7, 36), P(cx + 7, 45)], 0, 180, fill=255); paint(down(im), 0.0)
    im, d = layer(); d.rectangle([P(cx - 5, 40), P(cx + 5, 42)], fill=255); paint(down(im), 1.0)
    im, d = layer(); d.rectangle([P(cx + 1, 40), P(cx + 2.5, 42)], fill=255); paint(down(im), 0.0)
else:
    im, d = layer(); d.line([P(cx - 4, 41), P(cx + 4, 41)], fill=255, width=S); paint(down(im), 0.0)
# stubble on the chin
st = (np.random.RandomState(3).rand(H, W) < 0.22) & (yy > 42) & (yy < 46) & (np.abs(xx - cx) < 10)
# hat: tall dented crown with a band, wide curled brim
im, d = layer(); d.polygon([P(cx - 12, 15), P(cx - 11, 4), P(cx - 5, 1), P(cx, 3), P(cx + 5, 1), P(cx + 11, 4), P(cx + 12, 15)], fill=255); paint(down(im), lit(cx - 4, 7, 14, 10, 0.75, 0.6))
im, d = layer(); d.rectangle([P(cx - 12, 11.5), P(cx + 12, 15)], fill=255); paint(down(im), 0.08)                                            # band
im, d = layer(); d.ellipse([P(cx - 27, 13), P(cx + 27, 21)], fill=255); d.ellipse([P(cx - 29, 9.5), P(cx - 22, 17)], fill=255); d.ellipse([P(cx + 22, 9.5), P(cx + 29, 17)], fill=255)
paint(down(im), lit(cx - 6, 15, 28, 5, 0.70, 0.5))
im, d = layer(); d.chord([P(cx - 14, 17), P(cx + 14, 21)], 0, 180, fill=255); paint(down(im), 0.45)                                       # shadow under the brim
# dither the tones, then outline the whole figure
th = (B4[yy % 4, xx % 4] + 0.5) / 16
ink = (tone < th) & shape
ink |= st
from scipy.ndimage import binary_erosion
ink |= shape & ~binary_erosion(shape)
ink &= shape
RESULT = ink


if __name__ == '__main__' or 'MOUTH' not in globals() or True:
    pass
