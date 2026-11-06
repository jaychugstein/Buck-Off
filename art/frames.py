# Buck Off art: bull frames (stand, snort, and 5 bucks with in-betweens), rider leans, thrown tumble, fence, prompts.
# Writes frames.npz (masked sprites as [ink, solid]) and seats.json (rider seat + lean for each bull frame).
import json, math, numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
import bullparts as B
POSES = dict(B.POSES)
POSES['snort'] = dict(at=(44, 27), pitch=3, head=18, hind=(10, -16, 6), front=(-6, 8), lean=0)
ST = POSES['stand']
# each buck: anticipation (wind-up), key pose (the big moment), flail (overshoot: legs, head and tail thrash further)
# played as  wind-up, halfway, key, flail, key, halfway  then back to standing
BUCKS = {
 'rear':  [dict(at=(44, 28), pitch=-6, head=55, hind=(20, -25, 0), front=(-5, 10), lean=-6),
           dict(at=(44, 24), pitch=50, head=-5, hind=(32, 5, 10), front=(70, -30), lean=30, tail=(0, 8)),
           dict(at=(44, 24), pitch=56, head=8, hind=(36, 8, 12), front=(105, 15), lean=34, tail=(4, 6), spread=14)],
 'kick':  [dict(at=(44, 26), pitch=12, head=20, hind=(-20, -30, -35), front=(40, -20), lean=8),
           dict(at=(45, 28), pitch=-40, arch=30, head=95, hind=(-120, -150, -160), front=(20, 15), lean=-38, tail=(-1, -9), spread=14),
           dict(at=(45, 28), pitch=-46, arch=36, head=102, hind=(-140, -175, -178), front=(8, 6), lean=-44, tail=(4, -9), spread=24)],
 'lunge': [dict(at=(44, 28), pitch=-8, head=50, hind=(30, -20, 5), front=(5, -5), lean=-4),
           dict(at=(44, 24), pitch=30, lift=6, head=5, hind=(-55, -75, -85), front=(95, -50), lean=26, tail=(-7, -2)),
           dict(at=(44, 24), pitch=22, lift=9, head=22, hind=(-72, -98, -112), front=(115, -25), lean=20, tail=(-8, -6), spread=16)],
 'drop':  [dict(at=(44, 25), pitch=20, head=10, hind=(10, -5, 5), front=(70, -40), lean=12),                       # front end up...
           dict(at=(45, 27), pitch=-14, head=-25, hind=(-55, -70, -80), front=(55, 50), lean=-18, tail=(2, -10), spread=12),   # ...slams down stiff-legged, head thrown UP bellowing
           dict(at=(45, 27), pitch=-10, head=-40, hind=(-20, -95, -60), front=(60, 55), lean=-24, tail=(6, -9), spread=40)],   # back legs split wide, head tossed right back
 'air':   [dict(at=(44, 29), pitch=0, head=45, hind=(38, -38, 10), front=(-22, 28), lean=-10),
           dict(at=(44, 22), pitch=6, lift=14, head=25, hind=(-70, -100, -110), front=(85, -60), lean=-4, tail=(-8, -3)),
           dict(at=(44, 22), pitch=-6, arch=-10, lift=16, head=48, hind=(-30, 20, -10), front=(60, -75), lean=-14, tail=(-6, 6), spread=14)],
 'spin':  [dict(at=(44, 27), pitch=4, squash=0.86, head=55, hind=(-20, -10, 0), front=(5, 5), lean=6),
           dict(at=(44, 26), pitch=8, squash=0.62, face=True, head=40, hind=(-55, -30, -20), front=(-25, 20), lean=24, tail=(-9, -6), spread=18),
           dict(at=(44, 26), pitch=0, squash=0.5, face=True, head=40, hind=(-78, -52, -40), front=(-38, 32), lean=30, tail=(-10, -2), spread=24)],
}
def lerp(a, b, t):
    out = {}
    for k in set(a) | set(b):
        va, vb = a.get(k, b.get(k)), b.get(k, a.get(k))
        if k == 'lift': va, vb = a.get(k, 0), b.get(k, 0)
        if k == 'squash': va, vb = a.get(k, 1.0), b.get(k, 1.0)
        if isinstance(va, (tuple, list)): out[k] = tuple(x + (y - x) * t for x, y in zip(va, vb))
        elif isinstance(va, (int, float)) and not isinstance(va, bool): out[k] = va + (vb - va) * t
        else: out[k] = vb if t > 0.5 else va
    return out
img0, _ = B.bull(ST); ys, xs = np.nonzero(img0); DX = 64 - (xs.min() + xs.max()) // 2   # the bull stays put sideways
def place(img, lift):
    ys, xs = np.nonzero(img); dy = int(round(B.GL - lift)) - ys.max()
    if ys.min() + dy < 1: dy = 1 - ys.min()
    return DX, dy
def shift(m, dx, dy):
    out = np.zeros_like(m); ys, xs = np.nonzero(m); y2, x2 = ys + dy, xs + dx
    ok = (y2 >= 0) & (y2 <= B.GL) & (x2 >= 0) & (x2 < B.W); out[y2[ok], x2[ok]] = True; return out
names, frames, seats = [], [], []
def add(label, pose):
    img, seat = B.bull(pose); dx, dy = place(img, pose.get('lift', 0))
    m = shift(img, dx, dy)
    from scipy.ndimage import binary_fill_holes
    sil = binary_fill_holes(m); ink = m; sol = binary_dilation(sil, iterations=2) & ~ink
    frames.append(np.stack([ink, sol])); names.append(label)
    seats.append([int(round(seat[0] + dx)), int(round(seat[1] + dy)), int(round(pose.get('lean', 0)))])
add('stand', ST); add('snort', POSES['snort'])
for b, (ant, key, flail) in BUCKS.items():
    add(b + '-windup', ant); add(b + '-half', lerp(ant, key, 0.55)); add(b + '-key', key); add(b + '-flail', flail)
# rider: pixel cowboy, sheared to lean (-56 .. +40 in steps of 8)
RIDER = B.RIDER; SEAT = B.SEAT
def rider_img(lean, arm=True, hat=True, detail=False, art=None):
    art = art or RIDER
    h, w = len(art), len(art[0]); m = np.zeros((h + 2, w + 16), bool); wd = np.zeros_like(m)
    for y, row in enumerate(art):
        sh = int(round((SEAT[1] - y) * lean / 110.0)) if y < SEAT[1] else 0
        for x, ch in enumerate(row):
            if ch == 'o': wd[y + 1, x + 8 + sh] = True
            if ch != 'X': continue
            if not hat and y in (5, 6, 7, 8) and x >= 8: continue
            m[y + 1, x + 8 + sh] = True
    return (m, wd) if detail else m
LEANS = list(range(-56, 41, 8))   # each step of 8 tips his upper body about 1.5 px at the hat
riders = []
for L in LEANS:
    m, wd = rider_img(L, detail=True); riders.append(np.stack([m, (binary_dilation(m | wd, iterations=1) & ~m) | wd]))
wavers = []                                     # 3 poses x 13 leans: grab, lift, wave
for art in (B.HATGRAB, B.HATLIFT, B.HATWAVE):
    for L in LEANS:
        m, wd = rider_img(L, detail=True, art=art); wavers.append(np.stack([m, (binary_dilation(m | wd, iterations=1) & ~m) | wd]))
# thrown: the cowboy tumbling (8 turns), no hat, and lying in the dirt
from PIL import Image as I
base = rider_img(0, hat=False); tumble = []
for k in range(8):
    big = I.fromarray((base * 255).astype(np.uint8)).resize((base.shape[1] * 4, base.shape[0] * 4), I.NEAREST)
    big = big.rotate(-45 * k, resample=I.BILINEAR, expand=True)
    sm = np.array(big.resize((36 * 4 // 4 * 1, 36), I.BILINEAR)) > 100 if False else None
    bb = np.array(big) > 100; ys, xs = np.nonzero(bb); bb = bb[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    hh, ww = (bb.shape[0] + 3) // 4, (bb.shape[1] + 3) // 4
    pad = np.zeros((hh * 4, ww * 4), bool); pad[:bb.shape[0], :bb.shape[1]] = bb
    m = pad.reshape(hh, 4, ww, 4).mean(axis=(1, 3)) > 0.35
    c = np.zeros((44, 44), bool); oy, ox = (44 - m.shape[0]) // 2, (44 - m.shape[1]) // 2; c[oy:oy + m.shape[0], ox:ox + m.shape[1]] = m
    tumble.append(np.stack([c, binary_dilation(c, iterations=1) & ~c]))
HAT = np.array([[ch == 'X' for ch in r] for r in ["....XXXXX....", "...XXXXXXX...", "XXXXXXXXXXXXX"]])
hat = np.stack([HAT, binary_dilation(HAT, iterations=1) & ~HAT])[None]
# lying in the dirt (dazed, a little star over his head)
lying = np.rot90(rider_img(0, hat=False), 1)
ys, xs = np.nonzero(lying); lying = lying[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
lie = np.stack([lying, binary_dilation(lying, iterations=1) & ~lying])[None]
# background: the rodeo arena (arena.py)
import arena; FENCE = arena.A
# prompts, 17x17: 4 arrows and the two buttons (the one to press filled in)
AR = ["......X......", ".....XXX.....", "....XXXXX....", "...XXXXXXX...", "..XXXXXXXXX..", ".XXXXXXXXXXX.", "XXXXXXXXXXXXX",
      "....XXXXX....", "....XXXXX....", "....XXXXX....", "....XXXXX....", "....XXXXX....", "....XXXXX...."]
# arrows: a 9x9 arrow inside a white 17x17 box with a bold 2 px black outline (rounded corners)
AR9 = ["....X....", "...XXX...", "..XXXXX..", ".XXXXXXX.", "XXXXXXXXX", "..XXXXX..", "..XXXXX..", "..XXXXX..", "..XXXXX.."]
a9 = np.array([[c == 'X' for c in r] for r in AR9])
PS = 17
box = np.ones((PS, PS), bool)
for (y, x) in ((0, 0), (0, PS - 1), (PS - 1, 0), (PS - 1, PS - 1)): box[y, x] = False
def bordered(ink, solid):                          # add a 2 px white border all the way round (21x21), so it stands out from the crowd
    i2 = np.pad(ink, 2); s2 = np.pad(ink | solid, 2)
    return np.stack([i2, binary_dilation(s2, iterations=2) & ~i2])
inner = np.zeros_like(box); inner[2:PS - 2, 2:PS - 2] = True
for (y, x) in ((2, 2), (2, PS - 3), (PS - 3, 2), (PS - 3, PS - 3)): inner[y, x] = False
outline = box & ~inner
def arrow(a):
    ink = outline.copy(); ink[4:13, 4:13] |= a; return np.stack([ink, box & ~ink])
yy, xx = np.mgrid[0:PS, 0:PS]
import re
SRC = open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), '..', 'BuckOff', 'font.h')).read()
FONT = [int(v) for v in re.search(r'FONT\[\] PROGMEM = \{(.*?)\};', SRC, re.S).group(1).replace(' ', '').split(',') if v]
def btn(letter):                                   # a white round button with a bold 2 px black ring and a bold black letter
    d = np.hypot(xx - 8, yy - 8); disc = d <= 8.0
    ink = disc & (d > 6.1)
    g = ord(letter) - 32
    for i in range(5):
        col = FONT[g * 5 + i]
        for j in range(7):
            if col >> j & 1: ink[5 + j, 6 + i] = True; ink[5 + j, 7 + i] = True     # bold: each column doubled
    return np.stack([ink, disc & ~ink])
prompts = [arrow(a9), arrow(a9[::-1]), arrow(a9.T), arrow(a9.T[:, ::-1])]   # up, down, left, right
prompts += [btn('A'), btn('B')]                                            # A_BUTTON, B_BUTTON (order matches BTN[] in the game)
prompts = [bordered(p[0], p[1]) for p in prompts]
np.savez('frames.npz', bull=np.stack(frames), rider=np.stack(riders), waver=np.stack(wavers), tumble=np.stack(tumble), hat=hat, lie=lie,
         fence=FENCE, prompts=np.stack(prompts))
json.dump(dict(names=names, seats=seats, leans=LEANS, rider_seat=[SEAT[0] + 8, SEAT[1] + 1], rider_top=5), open('seats.json', 'w'))
# preview
def show(fr, path, cols=6, scale=3):
    tiles = []
    for f in fr:
        ink, sol = f; im = np.full(ink.shape, 150, np.uint8); im[sol] = 255; im[ink] = 0; tiles.append(np.pad(im, 1, constant_values=90))
    h = max(t.shape[0] for t in tiles); w = max(t.shape[1] for t in tiles)
    tiles = [np.pad(t, ((0, h - t.shape[0]), (0, w - t.shape[1])), constant_values=90) for t in tiles]
    rows = [np.hstack(tiles[i:i + cols] + [np.full((h, w), 90, np.uint8)] * (cols - len(tiles[i:i + cols]))) for i in range(0, len(tiles), cols)]
    Image.fromarray(np.vstack(rows)).resize((cols * w * scale, len(rows) * h * scale), Image.NEAREST).save(path)
show(frames, __import__('tempfile').gettempdir() + '/bo_bull.png', 6, 2); show(riders + tumble + [hat[0], lie[0]], __import__('tempfile').gettempdir() + '/bo_rider.png', 12, 4); show(prompts, __import__('tempfile').gettempdir() + '/bo_prompts.png', 6, 6)
print(len(frames), 'bull frames;', names)
