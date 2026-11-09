#!/usr/bin/env python3
"""gen_tiles.py — synthesise the missing floor tiles for the TILESET FLOOR
(Handler ruling 2026-11-09: the world floor is a tile map, tiles only).

The shipped tiles (tile-grass / tile-sand / tile-water, ISW family) are
256x256 fields of near-flat colour with sparse pixel speckle:
  grass base ~(201,229,187), dark blade (171,204,147), light (223,239,189)
  sand  base  (234,216,164), speckles (211,186,132) / (247,236,198)
  water base  (44,109,123)
The four tiles made here — grass2, dirt, path, stone — live in the same
light, low-contrast family, built from toroidal value noise (wraps on
both axes, so they tile seamlessly at the 0.55u pitch) quantised to a
small palette + hash speckle, exactly the shipped tiles' recipe.

Art law: no channel of any pixel ever drops below 26 (the palettes sit
far above that; a clamp enforces it anyway). Deterministic seeds —
rerunning reproduces the same files byte-for-byte.
"""
import numpy as np
from PIL import Image
import os, hashlib

OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'img')
S = 256

def vnoise(rng, cells, size=S):
    """Toroidal value noise: a cells x cells random grid, bilinearly
    interpolated with wraparound on both axes -> seamless tile."""
    g = rng.random((cells, cells))
    xs = np.linspace(0, cells, size, endpoint=False)
    x0 = np.floor(xs).astype(int) % cells; xf = xs - np.floor(xs)
    x1 = (x0 + 1) % cells
    top = g[np.ix_(x0, x0)] * 0  # placeholder shape guard (unused)
    # interpolate along x for both y rows happens via 2D lerp below
    gy = np.linspace(0, cells, size, endpoint=False)
    y0 = np.floor(gy).astype(int) % cells; yf = gy - np.floor(gy)
    y1 = (y0 + 1) % cells
    xf2 = xf[None, :]; yf2 = yf[:, None]
    v00 = g[np.ix_(y0, x0)]; v01 = g[np.ix_(y0, x1)]
    v10 = g[np.ix_(y1, x0)]; v11 = g[np.ix_(y1, x1)]
    return (v00 * (1 - xf2) + v01 * xf2) * (1 - yf2) + (v10 * (1 - xf2) + v11 * xf2) * yf2

def field(rng, weights=(0.55, 0.30, 0.15)):
    n = vnoise(rng, 4) * weights[0] + vnoise(rng, 8) * weights[1] + vnoise(rng, 16) * weights[2]
    return n / n.max()

def quantise(f, palette, rng, speckle=()):
    """Map a 0..1 field onto palette bands (list of (cutoff, rgb)),
    then scatter hash speckle: (probability, rgb) pairs."""
    img = np.zeros((S, S, 3), dtype=np.uint8)
    for cut, rgb in palette:
        mask = f <= cut
        img[mask] = rgb
    # everything above the last cutoff takes the last colour
    img[f > palette[-1][0]] = palette[-1][1]
    h = rng.random((S, S))
    for p, rgb in speckle:
        img[h < p] = rgb
        h = h + p  # shift so speckles don't fully overlap
    return img

def save(name, img):
    img = np.clip(img, 26, 255).astype(np.uint8)
    p = os.path.join(OUT, name)
    Image.fromarray(img, 'RGB').save(p)
    print(name, 'min channel', int(img.min()), 'sha', hashlib.md5(open(p, 'rb').read()).hexdigest()[:10])

# --- GRASS2: the speckle-variant grass — same family as tile-grass but a
# touch deeper, with denser dark blade speckle so big fields don't read
# as one flat sheet when the two grasses hash-mix.
rng = np.random.default_rng(20261121)
f = field(rng)
save('tile-grass2.png', quantise(f, [
    (0.30, (183, 220, 158)),
    (0.72, (193, 226, 172)),
    (1.00, (203, 231, 188)),
], rng, speckle=[(0.012, (171, 204, 147)), (0.010, (223, 239, 189)), (0.004, (198, 228, 150))]))

# --- DIRT: trampled settlement earth — the sand family pushed browner
# and darker, with pebble flecks. Yards (town outskirts, Thornwick,
# Rotwatch) wear this.
rng = np.random.default_rng(20261122)
f = field(rng)
save('tile-dirt.png', quantise(f, [
    (0.28, (172, 136, 92)),
    (0.70, (186, 152, 106)),
    (1.00, (200, 166, 120)),
], rng, speckle=[(0.012, (150, 116, 72)), (0.010, (216, 184, 134)), (0.005, (160, 148, 128))]))

# --- PATH: worn walking dirt — between dirt and sand, lighter in the
# middle of its range, a few pale stone flecks. The corridors wear this.
rng = np.random.default_rng(20261123)
f = field(rng)
save('tile-path.png', quantise(f, [
    (0.28, (172, 134, 84)),
    (0.70, (186, 150, 100)),
    (1.00, (200, 164, 114)),
], rng, speckle=[(0.010, (148, 112, 64)), (0.010, (222, 192, 140)), (0.004, (176, 162, 140))]))

# --- STONE: plaza flagstones — 4x4 wrapped flags per tile (basics
# gate: the old 2x2 flags made each 0.55u cell one giant slab and the
# plaza read as bathroom tiles), grey family of the old plaza curb
# (#a89f92 / #c2bab0) lifted into the tile light. Each flag gets a
# small hash brightness step so neighbours read as separate stones;
# seams are 2px and HALF-blended — a grout hint, not a grid stamp.
rng = np.random.default_rng(20261124)
f = field(rng, weights=(0.4, 0.35, 0.25))
img = quantise(f, [
    (0.30, (186, 177, 161)),
    (0.72, (198, 190, 176)),
    (1.00, (210, 203, 190)),
], rng, speckle=[(0.008, (168, 158, 142)), (0.008, (222, 216, 202))]).astype(np.int16)
FL = S // 4   # one flag = 64px
for fy in range(4):
    for fx in range(4):
        hsh = ((fx * 73856093) ^ (fy * 19349663) ^ 20261124) % 3   # -1, 0, +1 step
        img[fy*FL:(fy+1)*FL, fx*FL:(fx+1)*FL] += (int(hsh) - 1) * 6
# fine grain so no flag is one flat tone edge to edge
img += ((vnoise(rng, 16) - .5) * 10).astype(np.int16)[:, :, None]
# running bond: odd flag rows shift half a flag (toroidal roll keeps
# the tile seamless) — a perfect square grid is what read as tiles.
for fy in (1, 3):
    img[fy*FL:(fy+1)*FL] = np.roll(img[fy*FL:(fy+1)*FL], FL // 2, axis=1)
seam = np.array((178, 169, 154), dtype=np.int16)
for b in (0, 64, 128, 192):   # horizontal seams straddle each row boundary
    idx = [(b - 1) % S, b % S]
    img[idx, :] = (img[idx, :] + seam) // 2
for fy in range(4):           # vertical seams follow the bond offset
    off = (FL // 2) if fy % 2 else 0
    band = img[fy*FL:(fy+1)*FL]
    for b in (0, 64, 128, 192):
        bb = (b + off) % S
        idx = [(bb - 1) % S, bb]
        band[:, idx] = (band[:, idx] + seam) // 2
    img[fy*FL:(fy+1)*FL] = band
save('tile-stone.png', img)
print('done')
