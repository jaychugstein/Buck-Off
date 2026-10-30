# the "Hey Bucko" screen: the old cowboy on the left, an empty speech bubble on the right (the game types the words in)
import numpy as np
from PIL import Image, ImageDraw
SRC = open('cowboy.py').read()
def face(mouth):
    g = {'MOUTH': mouth, '__name__': 'cowboy'}; exec(SRC, g); return g['RESULT']
# 4 frames while he talks: mouth open / shut, swaying a pixel left and right
FR = []
for (mouth, dx) in ((1, 0), (0, 1), (1, 1), (0, 0)):
    S = np.zeros((64, 128), bool); S[2:62, 2 + dx:62 + dx] = face(mouth); FR.append(S)
S = FR[0]
big = Image.new('L', (128 * 8, 64 * 8), 0); d = ImageDraw.Draw(big)
def P(x, y): return (int(x * 8), int(y * 8))
d.rounded_rectangle([P(64, 2), P(126, 56)], radius=7 * 8, fill=255)
d.polygon([P(66, 34), P(66, 44), P(55, 45)], fill=255)                     # the tail, pointing at his mouth
outer = np.array(big).reshape(64, 8, 128, 8).mean(axis=(1, 3)) > 127
big2 = Image.new('L', (128 * 8, 64 * 8), 0); d2 = ImageDraw.Draw(big2)
d2.rounded_rectangle([P(66, 4), P(124, 54)], radius=5 * 8, fill=255)
d2.polygon([P(68, 36.5), P(68, 42), P(59, 44)], fill=255)
inner = np.array(big2).reshape(64, 8, 128, 8).mean(axis=(1, 3)) > 127
out = []
for S in FR:
    S = S & ~outer; S |= outer & ~inner                                    # bold 2 px bubble outline, white inside
    out.append(S)
np.save('bucko.npy', np.stack(out)); S = out[0]
Image.fromarray(np.where(S, 0, 255).astype(np.uint8)).resize((512, 256), Image.NEAREST).save(__import__('tempfile').gettempdir() + '/bucko.png')
