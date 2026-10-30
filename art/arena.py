# Rodeo arena background, 128x64, 1-bit, kept light so the bull and prompts stay easy to read:
# a strip of crowd in the stands (heads, hats, a few waving arms), a sturdy plank arena wall with posts,
# and a few specks of dirt on the ground.
import numpy as np, random
from PIL import Image
W, H = 128, 64
A = np.zeros((H, W), bool)
def px(x, y):
    if 0 <= x < W and 0 <= y < H: A[y, x] = True
random.seed(7)
# crowd: two rows of round heads peeking over the wall, some in cowboy hats, a few arms waving
for y0, step, off in [(29, 7, 0), (32, 7, 3)]:
    for x in range(off, W, step):
        x += random.choice((0, 0, 1)); hy = y0 + random.choice((0, 0, 1))
        for (dx, dy) in ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2), (0, 2), (2, 2)): px(x + dx, hy + dy)   # round head
        r = random.random()
        if r < 0.35: [px(x + dx, hy - 1) for dx in (-1, 0, 1, 2, 3)]; [px(x + dx, hy - 2) for dx in (0, 1, 2)]   # cowboy hat
        elif r < 0.5:
            sx = x + (4 if random.random() < 0.5 else -2); px(sx, hy + 2); px(sx, hy + 1); px(sx, hy); px(sx, hy - 1)   # arm up
# bunting: little pennants on a line sagging between the corners
for x in range(2, W - 2):                                                  # rope tied off 2 px in from the edges
    y = int(2 + 5 * (1 - ((x - 64) / 62) ** 2)); px(x, y)
    if x % 8 == 4:
        for k in range(4): [px(x + dx, y + 1 + k) for dx in range(-(3 - k) // 2 - 0, (3 - k) // 2 + 1)]
# arena wall: a top rail, planks, a bottom rail, posts with caps
A[35:47, :] = False
A[36:38, :] = True                                                        # top rail (2 px)
A[46, :] = True                                                           # bottom rail
for y in (40, 43): A[y, ::1] = np.arange(W) % 2 == 0                      # plank seams, dotted
for x0 in range(10, W, 36):                                               # posts
    A[34:47, x0:x0 + 3] = True; A[33, x0 - 1:x0 + 4] = True
# dirt: a few specks and little tufts
for _ in range(26):
    x = random.randrange(W); y = random.randrange(49, 59)
    px(x, y)
    if random.random() < 0.3: px(x + 1, y)
A[61, :] = True                                                           # ground line
np.save('arena.npy', A)
if __name__ == '__main__':
    d = np.load('frames.npz'); b = d['bull'][0]; ink, solid = b[0], b[1]
    S = A.copy(); S &= ~(ink | solid); S |= ink
    Image.fromarray(np.where(S, 0, 255).astype(np.uint8)).resize((512, 256), 0).save(__import__('tempfile').gettempdir() + '/arena.png')
