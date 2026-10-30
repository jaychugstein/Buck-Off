# Bucking bull v4: proper bull anatomy (3-part legs, hump, dewlap, arched spine) posed after real rodeo photos.
import math, numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
S = 8; W, H = 128, 64; G = 1.16; GL = 60
def P(x, y): return (x * G * S, y * G * S)
def capsule(d, a, b, r0, r1, fill=255):
    ax, ay = a; bx, by = b; L = math.hypot(bx - ax, by - ay) or 1; nx, ny = -(by - ay) / L, (bx - ax) / L
    d.polygon([P(ax + nx * r0, ay + ny * r0), P(bx + nx * r1, by + ny * r1), P(bx - nx * r1, by - ny * r1), P(ax - nx * r0, ay - ny * r0)], fill=fill)
    d.ellipse([P(ax - r0, ay - r0), P(ax + r0, ay + r0)], fill=fill); d.ellipse([P(bx - r1, by - r1), P(bx + r1, by + r1)], fill=fill)
def seg(p, ang, L): a = math.radians(ang); return (p[0] + L * math.sin(a), p[1] + L * math.cos(a))
RIDER = [                          # 'X' black, 'o' white detail (bandana, vest seam)
"..........................",
"..........................",
"..........................",
"..........................",
"XXX.......................",
"..XXX........XXXX.........",
"..XXX.......XXXXXX........",
"...XXX......XXXXXX........",
"...XXXX..XXXXXXXXXXXX.....",
"....XXXX.....XXXXX........",
"....XXXXX....XXXXXX.......",
".....XXXXX...XXXXX........",
".....XXXXXX...XXX.........",
"......XXXXXXXXoooXX.......",
".......XXXXXXXXXXXXX......",
".........XXXXXoXXXXXX.....",
"..........XXXXoXXXXXXX....",
"..........XXXXoXXXX.XXX...",
"..........XXXXoXXXX..XXX..",
"..........XXXXoXXXX...XXX.",
"..........XXXXXXXXX....XX.",
"...........XXXXXXXX....XX.",
"...........XXXXXXXXX...XX.",
"...........XXXXXXXXXXX.XXX",
"............XXXXXXXXXXXXXX",
"............XXXX..XXXXXX..",
"...................XXXX...",
"...................XXXX...",
"...................XXXX...",
"...................XXXX...",
"...................XXXX...",
"..................XXXXX...",
"..................XXXXXXX.",
"..................XXXXXXXX",
"...................X....X.",
]
SEAT = (13, 24)                       # where his seat is in the sprite
def rider(img, sx, sy, lean, hatoff):
    from scipy.ndimage import binary_dilation
    h, w = len(RIDER), len(RIDER[0]); m = np.zeros((h, w + 12), bool)
    for y, row in enumerate(RIDER):
        if hatoff and y < 4 and y > 1: row = row.replace('X', '.') if False else row
        sh = int(round((SEAT[1] - y) * lean / 45.0)) if y < SEAT[1] else 0     # lean: upper body shifts
        for x, ch in enumerate(row):
            if ch == 'X' and not (hatoff and y in (3, 4, 5) and x >= 6): m[y, x + 6 + sh] = True
    full = np.zeros_like(img); halo = np.zeros_like(img)
    oy, ox = sy - SEAT[1], sx - SEAT[0] - 6
    for y in range(h):
        for x in range(w + 12):
            if m[y, x] and 0 <= oy + y < img.shape[0] and 0 <= ox + x < img.shape[1]: full[oy + y, ox + x] = True
    halo = binary_dilation(full, iterations=1)
    img &= ~halo; img |= full
    if hatoff:                                     # hat flying off above and behind
        hx, hy = ox + 2, oy - 5
        for y, row in enumerate(["...XXXXX...", "..XXXXXXX..", "XXXXXXXXXXX"]):
            for x, ch in enumerate(row):
                if ch == 'X' and 0 <= hy + y < img.shape[0] and 0 <= hx + x < img.shape[1]: img[hy + y, hx + x] = True
def bull(p):
    big = Image.new('L', (W * S, H * S), 0); d = ImageDraw.Draw(big)
    cx, cy = p['at']; pitch = math.radians(p['pitch']); arch = math.radians(p.get('arch', 0))
    sq = p.get('squash', 1.0)         # < 1: the bull turning toward us (spin), so it looks shorter
    def R(x, y):                      # body point: front half and back half bend about the middle (arched spine)
        x = x * sq
        a = -pitch + (-arch / 2 if x > 0 else arch / 2) * min(1, abs(x) / 8)
        return (cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a))
    # body outline: rump, back, big hump over the shoulders, chest, belly
    top = [(-18, -1), (-16, -6), (-11, -8), (-4, -8), (3, -9), (8, -12), (12, -12), (16, -8), (18, -2)]
    bot = [(17, 5), (13, 9), (6, 8), (-2, 7), (-9, 7), (-15, 5), (-18, 2)]
    d.polygon([P(*R(x, y)) for x, y in top + bot], fill=255)
    # neck, head, horns, dewlap
    nk = R(16, 0); ha = math.radians(p['head']) - pitch
    hc = (nk[0] + 7 * math.cos(ha), nk[1] + 7 * math.sin(ha))
    capsule(d, R(13, -3), hc, 6.5, 3.6)
    if p.get('face'):                 # spinning: head swung round to face us, horns spread wide both ways
        fc = (hc[0] + 1, hc[1] + 2); d.ellipse([P(fc[0] - 5, fc[1] - 5), P(fc[0] + 5, fc[1] + 6)], fill=255)
        d.ellipse([P(fc[0] - 4, fc[1] + 2), P(fc[0] + 4, fc[1] + 9)], fill=255)
        for s in (-1, 1):
            b0 = (fc[0] + s * 4, fc[1] - 3); m1 = (fc[0] + s * 9, fc[1] - 5); t1 = (fc[0] + s * 11, fc[1] - 10)
            capsule(d, b0, m1, 1.9, 1.3); capsule(d, m1, t1, 1.3, 0.45)
            capsule(d, (fc[0] + s * 4, fc[1] - 1), (fc[0] + s * 8, fc[1] + 1), 1.5, 1.0)          # ears
        hc = fc; ha = math.radians(90)
    else:
        mz = (hc[0] + 4 * math.cos(ha), hc[1] + 4 * math.sin(ha)); capsule(d, hc, mz, 3.4, 2.5)
    dw = (nk[0] + 2 * math.cos(ha + 1.4), nk[1] + 2 * math.sin(ha + 1.4) + 2); capsule(d, R(13, 4), dw, 2.6, 1.4)
    up = (hc[0] - 2 * math.cos(ha) + 2.4 * math.sin(ha), hc[1] - 2 * math.sin(ha) - 2.4 * math.cos(ha))
    for s in ((-1, 1) if not p.get('face') else ()):                 # big horns: thick at the base, sweep out sideways, then curve up to a point
        mid = (up[0] + 3.6 * math.cos(ha - 1.25 + s * 0.75), up[1] + 3.6 * math.sin(ha - 1.25 + s * 0.75) - 1.2)
        tip = (mid[0] + 3.4 * math.cos(ha - 1.55 + s * 0.15), mid[1] + 3.4 * math.sin(ha - 1.55 + s * 0.15) - 2.2)
        capsule(d, up, mid, 1.9, 1.3); capsule(d, mid, tip, 1.3, 0.45)
    # legs: hind = thigh, gaskin, cannon; front = forearm, cannon (far legs a little behind the near ones)
    for far in (1, 0):
        o = far * p.get('spread', 8)
        hip = R(-12 + far * 1.5, 1)
        h = p['hind']; k = seg(hip, h[0] + o, 8); hk = seg(k, h[1] + o, 7); hf = seg(hk, h[2] + o, 5.5)
        capsule(d, hip, k, 5.0, 3.0); capsule(d, k, hk, 2.4, 1.6); capsule(d, hk, hf, 1.4, 1.3); capsule(d, hf, seg(hf, h[2] + o - 70, 1.6), 1.5, 1.3)
        sh = R(11 + far * 1.5, 4)
        f = p['front']; kn = seg(sh, f[0] - o, 8); ff = seg(kn, f[1] - o, 7)
        capsule(d, sh, kn, 3.6, 1.9); capsule(d, kn, ff, 1.6, 1.3); capsule(d, ff, seg(ff, f[1] - o + 70, 1.6), 1.5, 1.3)
    # tail with a tuft
    tb = R(-18, -2); t = p.get('tail', (-5, 6)); tt = (tb[0] + t[0], tb[1] + t[1]); capsule(d, tb, tt, 0.9, 0.6)
    d.ellipse([P(tt[0] - 1.6, tt[1] - 1.6), P(tt[0] + 1.6, tt[1] + 1.6)], fill=255)
    def down(m): return m.reshape(H, S, W, S).mean(axis=(1, 3)) > 0.5
    img = down(np.array(big) > 127)
    ex, ey = int(round((hc[0] + 0.8 * math.cos(ha) - 1.2 * math.sin(ha)) * G)), int(round((hc[1] - 1.4) * G))
    if 0 <= ey < H and 0 <= ex < W: img[ey, ex] = False                      # eye
    seat = R(4, -11)
    return img, (seat[0] * G, seat[1] * G)
# Poses copied from rodeo photos. Leg angles are measured from straight down, + = toward the head (right).
POSES = {
  'stand': dict(at=(44, 27), pitch=0,   head=40, hind=(12, -18, 4),     front=(2, 0),     lean=-4),
  'lunge': dict(at=(44, 24), pitch=26,  head=10, hind=(-28, -45, -55),  front=(85, -35),  lean=22, tail=(-6, 4)),      # front end up, pushing off
  'kick':  dict(at=(45, 28), pitch=-32, arch=22, head=88, hind=(-115, -140, -150), front=(18, 12), lean=-30, tail=(-2, -8), spread=12),  # head down, heels high
  'air':   dict(at=(44, 21), pitch=4,   head=30, hind=(-65, -95, -105), front=(70, -55),  lean=-6, tail=(-7, -3), hatoff=True),          # all four off the ground
  'rear':  dict(at=(44, 24), pitch=48,  head=0,  hind=(28, 0, 8),       front=(55, -15),  lean=32, tail=(-1, 7)),      # standing up on the back legs
  'spin':  dict(at=(44, 26), pitch=6, squash=0.68, face=True, head=40, hind=(-45, -20, -10), front=(-20, 15), lean=22, tail=(-8, -6), spread=16),  # spinning: turned toward us, back end swinging round
  'drop':  dict(at=(45, 27), pitch=-16, arch=12, head=62, hind=(-55, -80, -95), front=(35, 32), lean=-22, tail=(-6, -5), spread=10),  # front feet slam down
}

# ---- taking his hat off (the first 4 rows are empty room above him)
def _hat_in_hand(arm_rows, grip, ang):          # arm_rows: rows 0-8 without a hat; the hat drawn tilted, brim held at grip
    from PIL import Image as _I, ImageDraw as _D
    k = 8; big = _I.new('L', (26 * k, 9 * k), 0); d = _D.Draw(big)
    a = math.radians(ang); gx, gy = grip
    def T(x, y):                                # hat coords: brim along x (0..12) at y = 0, crown up to y = -4.5; rotate about the grip
        x -= 1; return ((gx + 0.5 + x * math.cos(a) + y * math.sin(a)) * k, (gy + 0.5 - x * math.sin(a) + y * math.cos(a)) * k)
    d.polygon([T(-0.6, -0.9), T(12.4, -0.9), T(12.4, 0.9), T(-0.6, 0.9)], fill=255)                                  # brim
    d.polygon([T(3.2, -0.5), T(3.6, -4.2), T(4.8, -5.2), T(7.2, -5.2), T(8.4, -4.2), T(8.8, -0.5)], fill=255)        # crown
    hat = np.array(big).reshape(9, k, 26, k).mean(axis=(1, 3)) > 110
    rows = [list(r) for r in arm_rows]
    for y in range(9):
        for x in range(26):
            if hat[y, x]: rows[y][x] = 'X'
    return [''.join(r) for r in rows]
_E = ".........................."
# reaching up: elbow bent, hand on the hat brim (hat still on his head)
HATGRAB = [_E] * 4 + [_E,
           ".............XXXX.........",
           ".........XXXXXXXXX........",
           "......XXXX..XXXXXX........",
           "....XXXX.XXXXXXXXXXXX....."] + RIDER[9:]
# lifting it off: elbow still bent, the hat tipped right up on its side
HATLIFT = _hat_in_hand([_E] * 4 + [_E, _E,
           "......XX..................",
           "......XXX.................",
           "....XXXX......XXXX........"], (7, 6), 24) + RIDER[9:]
# waving it high overhead, tilted back
HATWAVE = _hat_in_hand([_E] * 4 + ["XXX.......................",
           "..XXX.....................",
           "..XXX.....................",
           "...XXX....................",
           "...XXXX......XXXX........."], (1, 4), -28) + RIDER[9:]
