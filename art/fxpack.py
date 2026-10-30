# Packs all Buck Off art into the FX data and writes ../BuckOff/fxdata.h and ../BuckOff/tables.h.
# Run head.py, title.py, frames.py, controls.py and bucko.py first.
import os, sys, json, numpy as np
from scipy.ndimage import binary_dilation
ART = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ART, '..', 'BuckOff')
def bitmap(frames):                                   # plain: 1 = white
    n, H, W = frames.shape; out = bytearray([W >> 8, W & 255, H >> 8, H & 255])
    for m in frames:
        for p in range((H + 7) // 8):
            for x in range(W): out.append(sum(int(p * 8 + k < H and m[p * 8 + k, x]) << k for k in range(8)))
    return bytes(out)
def sprite(frames):                                   # masked: [ink, solid] -> black ink, white solid, rest see-through
    n, _, H, W = frames.shape; out = bytearray([W >> 8, W & 255, H >> 8, H & 255])
    for ink, sol in frames:
        for p in range((H + 7) // 8):
            for x in range(W):
                rows = [p * 8 + k for k in range(8)]
                out.append(sum(int(r < H and sol[r, x] and not ink[r, x]) << k for k, r in enumerate(rows)))
                out.append(sum(int(r < H and (sol[r, x] or ink[r, x])) << k for k, r in enumerate(rows)))
    return bytes(out)
D = np.load(os.path.join(ART, 'frames.npz')); S = json.load(open(os.path.join(ART, 'seats.json')))
import title as T
def lettering(txt, h, w):
    L = T.word(txt, h, w); sh = np.zeros_like(L)
    sh[2:, 2:] |= L[:-2, :-2]; sh &= ~binary_dilation(L, iterations=1)
    m = np.zeros((h + 3, w + 3), bool); m[:h, :w] = L; s2 = np.zeros_like(m); s2[:h + 2, :w + 2] = np.pad(sh, ((0, 2), (0, 2)))[:h + 2, :w + 2]
    ink = m | s2; return np.stack([ink, binary_dilation(ink, iterations=1) & ~ink])
from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
def clean(txt, w=110, h=14):                       # plain bold capitals, easy to read; centred on a 110x14 canvas
    f = _F.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf', 15)
    im = _I.new('1', (160, 30), 0); d = _D.Draw(im); d.fontmode = '1'; d.text((4, 4), txt, font=f, fill=1)
    a = np.array(im.crop(im.getbbox()), bool); ink = np.zeros((h, w), bool)
    y0 = (h - a.shape[0]) // 2; x0 = (w - a.shape[1]) // 2; ink[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a
    return np.stack([ink, binary_dilation(ink, iterations=1) & ~ink])
words = np.stack([clean('BUCKED OFF!'), clean('NEW RECORD!')])
RANKS = ['GROUND BEEF', 'HAY BALE', 'DUST EATER', 'BUCK BOY', 'RODEO CLOWN', 'SADDLE SORE', 'BUCKAROO',
         'BUCKSHOT', 'BUCK WILD', 'BALL BUSTER', 'BIG BUCKS', 'BULL WHISPERER', 'RODEO LEGEND', 'BUCK ALMIGHTY']
def rankword(txt, w=120, h=13):                    # the rank, big and bold, centred
    f = _F.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf', 14 if len(txt) < 14 else 13)
    im = _I.new('1', (220, 30), 0); d = _D.Draw(im); d.fontmode = '1'; d.text((4, 4), txt, font=f, fill=1)
    a = np.array(im.crop(im.getbbox()), bool); assert a.shape[1] <= w - 2 and a.shape[0] <= h - 2, (txt, a.shape)
    ink = np.zeros((h, w), bool); y0 = (h - a.shape[0]) // 2; x0 = (w - a.shape[1]) // 2; ink[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a
    return np.stack([ink, binary_dilation(ink, iterations=1) & ~ink])
ranks = np.stack([rankword(t) for t in RANKS])
def _line(txt, size, font='DejaVuSerifCondensed-Bold'):
    f = _F.truetype('/usr/share/fonts/truetype/dejavu/%s.ttf' % font, size)
    im = _I.new('1', (200, 40), 0); d = _D.Draw(im); d.fontmode = '1'; d.text((4, 4), txt, font=f, fill=1)
    return np.array(im.crop(im.getbbox()), bool)
def sndword(lines):                               # sound screen word: big crisp western letters on two staggered lines, clean, no shadow
    out = np.zeros((24, 46), bool)
    for (txt, size, x, y) in lines:
        a = _line(txt, size); out[y:y + a.shape[0], x:x + a.shape[1]] |= a[:24 - y, :46 - x]
    ink = out
    return np.stack([ink, binary_dilation(ink, iterations=1) & ~ink])
sndw = np.stack([sndword([('YEE-', 13, 1, 1), ('HAW!', 13, 6, 12)]), sndword([('SHHH', 13, 2, 6)])])
parts = [
    ('FX_SNDW',   sprite(sndw),                         'YEE-HAW! / SHHH for the sound screen, 46x24'),
    ('FX_COWBOY', bitmap(~np.load(os.path.join(ART, 'bucko.npy'))), 'the old cowboy and his speech bubble, 4 talking frames'),
    ('FX_RANKS',  sprite(ranks),                        'rank names, 14 frames 120x13'),
    ('FX_FENCE',  bitmap(~D['fence'][None]),            'fence + ground, 128x64 (drawn first)'),
    ('FX_BULL',   sprite(D['bull']),                    'bull, %d frames 128x64: %s' % (len(S['names']), ' '.join(S['names']))),
    ('FX_RIDERW', sprite(D['waver']),                   'cowboy taking his hat off: grab, lift, wave (13 leans each)'),
    ('FX_RIDER',  sprite(D['rider']),                   'cowboy leaning %d..%d in steps of 8' % (S['leans'][0], S['leans'][-1])),
    ('FX_TUMBLE', sprite(D['tumble']),                  'cowboy thrown, 8 turns, 44x44'),
    ('FX_HAT',    sprite(D['hat']),                     'hat 13x3'),
    ('FX_PROMPT', sprite(D['prompts']),                 'prompts 21x21 (17x17 + 2 px white border): up down left right inner outer'),
    ('FX_TITLE',  bitmap(~np.load(os.path.join(ART, 'title.npy'))), 'title screen, 6 frames'),
    ('FX_CTRL',   bitmap(np.load(os.path.join(ART, 'controls.npy')).astype(bool)), 'controls screen (POOM), 2 frames: how to play / any button'),
    ('FX_WORDS',  sprite(words),                        'BUCKED OFF! / NEW RECORD! lettering 110x14'),
]
data = bytearray(); hdr = []
for name, blob, note in parts:
    hdr.append('constexpr uint24_t %-10s = 0x%06X;   // %s' % (name, len(data), note)); data += blob
while len(data) % 256: data.append(0xFF)
page = 0x10000 - len(data) // 256
os.makedirs(os.path.join(OUT, 'fxdata'), exist_ok=True)
open(os.path.join(OUT, 'fxdata', 'fxdata.bin'), 'wb').write(data)
h = '// generated by art/fxpack.py - do not edit\n#pragma once\n#include <ArduboyFX.h>\n'
h += 'constexpr uint16_t FX_DATA_PAGE = 0x%04X;   // %d bytes of FX data\n' % (page, len(data)) + '\n'.join(hdr) + '\n'
open(os.path.join(OUT, 'fxdata.h'), 'w').write(h)
t = '// generated by art/fxpack.py - do not edit\n#pragma once\n'
t += '// rider seat (x, y on screen) and lean for each bull frame\n'
for f in (0, 1): S['seats'][f][1] = max(S['seats'][f][1], S['rider_seat'][1] - S['rider_top'] + 2)   # standing still: keep his raised hand 2 px below the top edge
t += 'const int8_t SEAT[%d][3] PROGMEM = { %s };\n' % (len(S['seats']), ', '.join('{%d, %d, %d}' % tuple(v) for v in S['seats']))
t += 'constexpr int8_t RIDER_SX = %d, RIDER_SY = %d, LEAN0 = %d;   // seat point inside the rider sprite; first lean\n' % (S['rider_seat'][0], S['rider_seat'][1], S['leans'][0])
t += 'constexpr uint8_t N_LEAN = %d;\n' % len(S['leans'])
open(os.path.join(OUT, 'tables.h'), 'w').write(t)
print(h); print(t)

# where prompts may pop up: anywhere the 17x17 icon misses the standing/snorting bull, the cowboy (even slipping),
# the timer (top left) and the hats left (top right)
busy = np.zeros((64, 128), bool)
for f in (0, 1):
    ink, sol = D['bull'][f]; busy |= ink | sol
    sx, sy, lean = S['seats'][f]
    for L in range(lean - 40, lean + 1, 8):
        k = min(max((L - S['leans'][0]) // 8, 0), len(S['leans']) - 1); r = D['rider'][k]; rm = r[0] | r[1]
        for slip in range(4):
            oy, ox = sy - S['rider_seat'][1], sx - S['rider_seat'][0] - slip * 2
            for y in range(rm.shape[0]):
                for x in range(rm.shape[1]):
                    if rm[y, x] and 0 <= oy + y < 64 and 0 <= ox + x < 128: busy[oy + y, ox + x] = True
busy[48:, :] = True; busy[0:12, 0:35] = True          # time, score and messages along the bottom; strikes top left
busy = binary_dilation(busy, iterations=2)
import random
rng = random.Random(1); cand = [(x, y) for y in range(0, 48 - 21) for x in range(0, 128 - 21 + 1) if not busy[y + 2:y + 19, x + 2:x + 19].any()]   # the black outline stays 2 px clear of every screen edge
rng.shuffle(cand); spots = []
for c in cand:
    if all(abs(c[0] - s[0]) + abs(c[1] - s[1]) >= 9 for s in spots): spots.append(c)
spots.sort(key=lambda c: (c[1], c[0]))
t = open(os.path.join(OUT, 'tables.h')).read()
t += '// empty spots around the bull where a prompt can pop up (top-left corner of the 21x21 icon)\n'
t += 'const uint8_t SPOTS[%d][2] PROGMEM = { %s };\n' % (len(spots), ', '.join('{%d, %d}' % c for c in spots))
open(os.path.join(OUT, 'tables.h'), 'w').write(t)
print(len(spots), 'prompt spots')
from PIL import Image
im = np.where(busy, 120, 255).astype(np.uint8)
for (x, y) in spots: im[y:y + 21, x:x + 21] = np.minimum(im[y:y + 21, x:x + 21], 40)
Image.fromarray(im).resize((512, 256), Image.NEAREST).save(__import__('tempfile').gettempdir() + '/bo_spots.png')
