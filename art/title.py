# Buck Off title: western wood-type lettering (DejaVu Serif Condensed Bold, made into a "wanted poster" look:
# tall slab letters, a white line inside each stroke and a 3D drop shadow), and the funny picture:
# the bull mid-kick with the cowboy launched sky-high, tumbling, hat flying off. 4 frames.
import numpy as np, math
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import binary_erosion, binary_dilation
import bullparts as B
F = '/usr/share/fonts/truetype/dejavu/DejaVuSerifCondensed-Bold.ttf'
def word(txt, h, w):
    f = ImageFont.truetype(F, 300); im = Image.new('L', (2400, 600), 0); ImageDraw.Draw(im).text((20, 20), txt, font=f, fill=255)
    im = im.crop(im.getbbox()).resize((w * 4, h * 4), Image.LANCZOS)
    return np.array(im.resize((w, h), Image.LANCZOS)) > 110
def lettering():
    a = word('BUCK', 23, 63); b = word('OFF', 23, 48)
    L = np.zeros((52, 68), bool); L[0:23, 0:63] = a; L[27:50, 8:56] = b
    sh = np.zeros_like(L)
    for k in (2, 3): sh[k:, k:] |= L[:-k, :-k]                                          # 3D block shadow down-right,
    sh &= ~binary_dilation(L, iterations=1)                                            # split from the letters by a white line
    return L | sh, binary_dilation(L | sh, iterations=1)
def bull_small(pose, scale):
    old = B.G; B.G = scale
    try: img, seat = B.bull(pose)
    finally: B.G = old
    return img
def frames():                                   # lettering on the left, the bull's head on the right
    ink, solid = lettering(); H = np.load('head.npy'); out = []
    for f in range(len(H)):
        S = np.zeros((64, 128), bool)
        S[2:2 + ink.shape[0], 2:2 + ink.shape[1]] = ink                     # 2 px clear of the edges
        S[1:64, 65:127] |= H[f][0:63]
        out.append(S)
    return out
if __name__ == '__main__':
    fr = frames(); np.save('title.npy', np.stack(fr))
    row = np.hstack([np.pad(np.where(f, 0, 255).astype(np.uint8), 2, constant_values=120) for f in fr[:2]])
    Image.fromarray(row).resize((row.shape[1] * 4, row.shape[0] * 4), Image.NEAREST).save(__import__('tempfile').gettempdir() + '/bo_title.png')
