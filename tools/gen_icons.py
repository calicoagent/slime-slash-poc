#!/usr/bin/env python3
"""Item icons for Slime Slash — soul gems, ore materials, ore nodes,
relics, and the Coin Purse (Handler, 2026-11-09: 'generate icons for
the gems ores etc').

Until now these items rendered as CSS rotated squares (soul gems in the
GEMS tab, mined materials as forge chips) or as bare text rows (relics,
purse). This tool draws real pixel-art icons in the game's language:

  * drawn on a 24x24 logical grid, NEAREST x2 to the shipped 48x48 —
    the same low-grid-then-upscale construction as the graded NPCs,
    crisp at the 24-26px the HUD/menu actually render;
  * directional light from the upper left, encoded as facet tones;
  * outline ring = deep shade of each edge pixel's OWN colour (the
    grade pass's varied ring), applied to the finished silhouette;
  * transparent background, strictly binary alpha (0/255);
  * art law: no true black — every visible channel ends >= 26.

Palettes are the game's own: soul-gem tiers use GEM_RARITY_COL,
materials use the GEMS table colours, node crystals use NODE_TYPES'
crystal lists, relics are miniatures of the RELICS table's objects.

Output: assets/img/icons/*.png + assets/img/icons/manifest.json
(filename -> item id / rarity / ore / relic) for the index.html wiring.
Deterministic: all grain is a splitmix hash of (x, y, seed).

Run from the repo root:  python3 tools/gen_icons.py
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "assets" / "img" / "icons"
GRID = 24
SCALE = 2
BLACK_POINT = 26


# ------------------------------------------------------------------ colour

def hx(s: str) -> tuple[float, float, float]:
    s = s.lstrip('#')
    return tuple(float(int(s[i:i + 2], 16)) for i in (0, 2, 4))


def mix(c, other, f):
    return tuple(a + (b - a) * f for a, b in zip(c, other))


def mul(c, f):
    return tuple(a * f for a in c)


WHITE = (255.0, 255.0, 255.0)


def splitmix(x: int) -> float:
    x = (x + 0x9E3779B9) & 0xFFFFFFFF
    x = ((x ^ (x >> 16)) * 0x85EBCA6B) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
    return ((x ^ (x >> 16)) & 0xFFFFFFFF) / 4294967296.0


# ------------------------------------------------------------------ canvas

class Grid:
    def __init__(self):
        self.px = [[None] * GRID for _ in range(GRID)]

    def set(self, x, y, c):
        if 0 <= x < GRID and 0 <= y < GRID:
            self.px[y][x] = c

    def get(self, x, y):
        if 0 <= x < GRID and 0 <= y < GRID:
            return self.px[y][x]
        return None

    def poly(self, pts, c):
        """Scanline point-in-polygon fill at pixel centres."""
        ys = [p[1] for p in pts]
        for y in range(max(0, int(min(ys))), min(GRID - 1, int(max(ys))) + 1):
            cy = y + 0.5
            xs = []
            for i in range(len(pts)):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % len(pts)]
                if (y1 <= cy < y2) or (y2 <= cy < y1):
                    xs.append(x1 + (cy - y1) / (y2 - y1) * (x2 - x1))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                for x in range(int(xs[k]), int(xs[k + 1]) + 1):
                    if x + 0.5 >= xs[k] and x + 0.5 <= xs[k + 1]:
                        self.set(x, y, c)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def grain(self, seed, amt, mask=None):
        for y in range(GRID):
            for x in range(GRID):
                c = self.px[y][x]
                if c is not None and (mask is None or mask(x, y, c)):
                    d = (splitmix((x * 73856093) ^ (y * 19349663) ^ seed) - 0.5) * 2 * amt
                    self.px[y][x] = tuple(v + d for v in c)

    def outline(self, factor=0.42):
        """Silhouette edge pixels -> deep shade of their own colour."""
        src = [row[:] for row in self.px]
        for y in range(GRID):
            for x in range(GRID):
                if src[y][x] is None:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < GRID and 0 <= ny < GRID) or src[ny][nx] is None:
                        self.px[y][x] = mul(src[y][x], factor)
                        break

    def finish(self) -> Image.Image:
        im = Image.new('RGBA', (GRID, GRID), (0, 0, 0, 0))
        data = []
        for y in range(GRID):
            for x in range(GRID):
                c = self.px[y][x]
                if c is None:
                    data.append((0, 0, 0, 0))
                else:
                    data.append(tuple(int(max(BLACK_POINT, min(255, round(v)))) for v in c) + (255,))
        im.putdata(data)
        return im.resize((GRID * SCALE, GRID * SCALE), Image.NEAREST)


# ------------------------------------------------------------------ pieces

def sparkle(g: Grid, cx, cy, c, big=False):
    g.set(cx, cy, c)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        g.set(cx + dx, cy + dy, c)
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            g.set(cx + dx, cy + dy, c)


def shard(g: Grid, cx, top, h, w, base):
    """One raw crystal prism: tip at (cx, top), body h tall, w wide."""
    pale, light, dark = mix(base, WHITE, 0.55), mix(base, WHITE, 0.30), mul(base, 0.62)
    hw = w / 2.0
    # right (dark) half then left (light) half, centre ridge pale
    g.poly([(cx, top), (cx + hw, top + h * 0.28), (cx + hw, top + h), (cx, top + h)], dark)
    g.poly([(cx, top), (cx, top + h), (cx - hw, top + h), (cx - hw, top + h * 0.28)], light)
    for y in range(int(top + h * 0.18), int(top + h * 0.92)):
        g.set(int(round(cx)), y, pale)
    g.set(int(round(cx)), int(top + 1), pale)


def mini_shard(g: Grid, cx, base_y, h, base):
    """Tiny embedded crystal: 2px wide spike sitting on base_y."""
    light, dark = mix(base, WHITE, 0.35), mul(base, 0.65)
    for i in range(h):
        w = 1 if i < h - 1 else 2
        for dx in range(0, w + 1):
            g.set(cx + dx - (1 if w == 2 else 0), base_y - i, light if dx == 0 else dark)
    g.set(cx, base_y - h, mix(base, WHITE, 0.6))


# ------------------------------------------------------------------ icons

def soul_gem(rarity: int, base_hex: str) -> Grid:
    base = hx(base_hex)
    pale, light, dark = mix(base, WHITE, 0.62), mix(base, WHITE, 0.34), mul(base, 0.64)
    g = Grid()
    crown_l = [(3.5, 11), (6.5, 6), (11.5, 6), (11.5, 11)]            # crown left
    crown_r = [(11.5, 6), (16.5, 6), (19.5, 11), (11.5, 11)]          # crown right
    table = [(7.5, 6), (15.5, 6), (16.8, 8.6), (6.2, 8.6)]            # table facet
    pav_l = [(3.5, 11), (11.5, 11), (11.5, 19.5)]                     # pavilion left
    pav_r = [(11.5, 11), (19.5, 11), (11.5, 19.5)]                    # pavilion right
    g.poly(pav_r, dark)
    g.poly(pav_l, light)
    g.poly(crown_r, mul(base, 0.82))
    g.poly(crown_l, light)
    g.poly(table, pale)
    if rarity >= 1:      # fine+: table split + girdle light line
        for x in range(5, 19):
            if g.get(x, 11) is not None:
                g.set(x, 11, light)
        g.set(11, 7, pale); g.set(12, 7, light)
    if rarity >= 2:      # rare+: keel facet — pale spine down the pavilion
        for y in range(12, 19):
            g.set(11, y, light)
            if y < 17:
                g.set(12, y, mul(base, 0.78))
    if rarity >= 3:      # epic+: crown edge glints
        g.set(7, 6, pale); g.set(8, 6, pale)
    g.outline(0.40)
    if rarity >= 3:
        sparkle(g, 4, 4, mix(base, WHITE, 0.75))
    if rarity >= 4:      # legendary: full regalia
        sparkle(g, 19, 3, mix(base, WHITE, 0.8), big=True)
        sparkle(g, 5, 16, mix(base, WHITE, 0.7))
        g.set(11, 12, pale); g.set(12, 13, pale)
    return g


def ore_cluster(base_hex: str, seed: int) -> Grid:
    base = hx(base_hex)
    g = Grid()
    rock = (104.0, 94.0, 84.0)
    # back shards (darker), then the hero shard, then the stone base
    g2 = Grid()
    shard(g2, 6.5, 8, 9, 4, mul(base, 0.8))
    shard(g2, 17.5, 7, 10, 4, mul(base, 0.88))
    for y in range(GRID):
        for x in range(GRID):
            if g2.px[y][x] is not None:
                g.set(x, y, g2.px[y][x])
    shard(g, 12, 3, 14, 6, base)
    # stone base mound the cluster grows from
    g.poly([(4, 21), (6, 16.5), (18, 16.5), (20, 21)], rock)
    g.poly([(4, 21), (6, 16.5), (12, 16.5), (12, 21)], mix(rock, WHITE, 0.14))
    g.grain(seed, 5, mask=lambda x, y, c: abs(c[0] - rock[0]) < 40 and c[2] < 120)
    g.outline(0.42)
    return g


def node_rock(body, crystals, kind: int, seed: int) -> Grid:
    """kind: 0 boulder, 1 river, 2 sunstone, 3 crag, 4 geode."""
    g = Grid()
    light, dark = mix(body, WHITE, 0.16), mul(body, 0.72)
    if kind == 0:        # mossy boulder — round, moss-capped
        g.poly([(5, 20), (3.5, 13), (5.5, 7), (10, 4.5), (15, 4.5), (19, 7.5), (20.5, 13), (19, 20)], body)
        g.poly([(5, 20), (3.5, 13), (5.5, 7), (10, 4.5), (11.5, 4.5), (11.5, 20)], light)
        moss = (88.0, 128.0, 62.0)
        for (x, y) in [(6, 6), (7, 5), (9, 5), (8, 7), (6, 8), (10, 6), (5, 10), (11, 5)]:
            g.set(x, y, moss)
        for (x, y) in [(7, 6), (9, 7)]:
            g.set(x, y, mix(moss, WHITE, 0.25))
        mini_shard(g, 14, 13, 4, hx(crystals[0][1]))
        mini_shard(g, 8, 16, 3, hx(crystals[1][1]))
    elif kind == 1:      # river rock — flat smooth oval
        g.poly([(3, 19), (3.5, 13), (7, 8.5), (12, 7.5), (17, 8.5), (20.5, 13), (21, 19)], body)
        g.poly([(3, 19), (3.5, 13), (7, 8.5), (12, 7.5), (12, 19)], light)
        for x in range(6, 13):     # waterline sheen
            if g.get(x, 10) is not None:
                g.set(x, 10, mix(body, WHITE, 0.38))
        mini_shard(g, 15, 15, 4, hx(crystals[0][1]))
        mini_shard(g, 9, 17, 3, hx(crystals[1][1]))
    elif kind == 2:      # sunstone — warm angular block
        g.poly([(5, 20), (4, 11), (8, 6), (16, 5), (20, 10), (19, 20)], body)
        g.poly([(5, 20), (4, 11), (8, 6), (12, 5.5), (12, 20)], light)
        g.poly([(12, 13), (20, 10), (19, 20), (12, 20)], dark)   # low shade only — a full-height split read as a door
        mini_shard(g, 9, 14, 5, hx(crystals[0][1]))
        mini_shard(g, 15, 17, 3, hx(crystals[1][1]))
    elif kind == 3:      # crimson crag — jagged
        g.poly([(4, 20), (3, 12), (6, 13), (7, 6), (10, 11), (12, 4), (15, 10), (17, 6), (20, 12), (19, 20)], body)
        g.poly([(4, 20), (3, 12), (6, 13), (7, 6), (10, 11), (11, 8), (11, 20)], light)
        mini_shard(g, 13, 15, 4, hx(crystals[0][1]))
        mini_shard(g, 8, 17, 3, hx(crystals[1][1]))
    else:                # void geode — dark shell, crystal heart
        g.poly([(5, 20), (3.5, 12), (6, 6), (11, 4), (16, 5), (20, 9), (20.5, 14), (19, 20)], body)
        g.poly([(5, 20), (3.5, 12), (6, 6), (11, 4), (11, 20)], light)
        inner = mix(hx(crystals[0][1]), WHITE, 0.25)
        g.disc(12, 13.5, 4.6, inner)
        g.disc(12, 13.5, 3.4, mix(hx(crystals[0][1]), WHITE, 0.45))
        mini_shard(g, 10, 16, 5, hx(crystals[0][1]))
        mini_shard(g, 13, 16, 6, hx(crystals[0][1]))
        mini_shard(g, 15, 15, 3, hx(crystals[1][1]))
    g.grain(seed, 4)
    g.outline(0.42)
    return g


def relic_pauldron() -> Grid:
    g = Grid()
    bronze = (104.0, 128.0, 74.0)
    gold = (196.0, 164.0, 84.0)
    g.poly([(4, 19), (3.5, 11), (6, 6), (11, 3.5), (16, 3.5), (19.5, 7), (20.5, 12), (20, 19)], bronze)
    g.poly([(4, 19), (3.5, 11), (6, 6), (11, 3.5), (11.5, 3.5), (11.5, 19)], mix(bronze, WHITE, 0.18))
    g.poly([(11.5, 3.5), (16, 3.5), (19.5, 7), (20.5, 12), (20, 19), (11.5, 19)], mul(bronze, 0.74))
    for y in (11, 15):   # lame band seams + gold trim
        for x in range(4, 21):
            if g.get(x, y) is not None:
                g.set(x, y, mul(bronze, 0.6))
        for x in range(4, 21):
            if g.get(x, y - 1) is not None and y == 11:
                g.set(x, y - 1, gold)
    for x in (6, 18):    # rivets
        g.set(x, 17, mix(gold, WHITE, 0.3))
    leaf = (70.0, 138.0, 54.0)   # leaf ridge at the crown of the dome
    g.poly([(11.5, 1.5), (13.5, 4), (11.5, 5), (9.5, 4)], leaf)
    g.outline(0.42)
    return g


def relic_crown() -> Grid:
    g = Grid()
    gold = (190.0, 156.0, 66.0)
    thorn = (128.0, 118.0, 58.0)
    for i, (tx, th) in enumerate([(5, 8), (8.5, 11), (12, 13), (15.5, 11), (19, 8)]):
        g.poly([(tx - 1.8, 14), (tx + 1.8, 14), (tx, 14 - th)], thorn if i % 2 else gold)
        g.set(int(tx), 14 - th + 1, mix(thorn, WHITE, 0.45))
    g.rect(4, 14, 20, 18, gold)
    g.rect(4, 14, 20, 15, mix(gold, WHITE, 0.22))
    g.rect(4, 18, 20, 18, mul(gold, 0.66))
    gem = hx('#3ddc84')
    g.poly([(12, 13.8), (13.6, 15.8), (12, 17.8), (10.4, 15.8)], gem)
    g.set(12, 15, mix(gem, WHITE, 0.5))
    for x in (6, 18):
        g.set(x, 16, mul(gold, 0.7))
    g.outline(0.42)
    return g


def relic_heart() -> Grid:
    g = Grid()
    base = (172.0, 60.0, 78.0)
    g.disc(7.8, 8.5, 4.6, base)
    g.disc(16.2, 8.5, 4.6, base)
    g.poly([(3.6, 9), (20.4, 9), (12, 20.5)], base)
    g.disc(7.8, 8.5, 4.6, mix(base, WHITE, 0.14))
    g.poly([(3.6, 9), (11, 9), (12, 20.5)], mix(base, WHITE, 0.07))
    g.poly([(13, 9), (20.4, 9), (12, 20.5)], mul(base, 0.78))
    g.set(6, 6, mix(base, WHITE, 0.4)); g.set(7, 5, mix(base, WHITE, 0.35))
    rot = (92.0, 46.0, 78.0)    # rot veins creeping in from the right
    for (x, y) in [(17, 10), (16, 11), (15, 12), (16, 13), (14, 13), (15, 15), (14, 16), (18, 12)]:
        if g.get(x, y) is not None:
            g.set(x, y, rot)
    g.disc(16.5, 15.5, 1.4, mul(rot, 0.8))
    g.outline(0.42)
    g.set(18, 17, (214.0, 178.0, 204.0))   # spore motes
    g.set(19, 15, (214.0, 178.0, 204.0))
    return g


def relic_sprout() -> Grid:
    g = Grid()
    rim = (156.0, 120.0, 66.0)
    g.disc(12, 12.5, 8.6, rim)
    g.disc(12, 12.5, 6.9, (80.0, 90.0, 56.0))
    g.disc(10.5, 10.5, 5.2, (92.0, 102.0, 62.0))
    g.set(12, 2, mix(rim, WHITE, 0.3))     # charm loop
    g.set(12, 3, mix(rim, WHITE, 0.15))
    stem = (66.0, 120.0, 52.0)
    for y in range(11, 18):
        g.set(12, y, stem)
    leaf_l, leaf_r = (104.0, 176.0, 78.0), (80.0, 148.0, 60.0)
    g.poly([(12, 12), (6, 6.5), (5, 10.5), (9, 13)], leaf_l)
    g.poly([(12, 11), (18, 5.5), (19, 9.5), (15, 12.5)], leaf_r)
    g.set(8, 9, mix(leaf_l, WHITE, 0.35))
    g.set(16, 8, mix(leaf_r, WHITE, 0.3))
    g.outline(0.42)
    return g


def relic_eye() -> Grid:
    g = Grid()
    gold = (198.0, 156.0, 54.0)
    for (tx, th) in [(7, 3), (12, 4), (17, 3)]:   # regal lash spikes
        g.poly([(tx - 1.4, 6.5), (tx + 1.4, 6.5), (tx, 6.5 - th)], gold)
    g.poly([(2.5, 12), (8, 5.5), (16, 5.5), (21.5, 12), (16, 18.5), (8, 18.5)], gold)
    g.poly([(4.8, 12), (8.8, 7.8), (15.2, 7.8), (19.2, 12), (15.2, 16.2), (8.8, 16.2)], (233.0, 229.0, 219.0))
    iris = (242.0, 172.0, 58.0)
    g.disc(12, 12, 4.1, iris)
    g.disc(12, 12, 2.0, (44.0, 36.0, 44.0))
    g.outline(0.40)
    g.set(10, 9, (255.0, 250.0, 235.0))    # glint
    g.set(13, 14, mix(iris, WHITE, 0.4))
    return g


def item_purse() -> Grid:
    g = Grid()
    gold = (242.0, 198.0, 82.0)
    g.disc(9.5, 6.5, 2.4, gold)            # coins peeking out
    g.disc(14.5, 5.8, 2.4, mix(gold, WHITE, 0.12))
    leather = (178.0, 140.0, 86.0)
    g.poly([(7, 9), (17, 9), (19.5, 14), (18.5, 19), (15, 21), (9, 21), (5.5, 19), (4.5, 14)], leather)
    g.poly([(7, 9), (11.5, 9), (11.5, 21), (9, 21), (5.5, 19), (4.5, 14)], mix(leather, WHITE, 0.13))
    g.poly([(12.5, 9), (17, 9), (19.5, 14), (18.5, 19), (15, 21), (12.5, 21)], mul(leather, 0.76))
    g.rect(6, 8, 18, 10, (122.0, 88.0, 50.0))          # cinch band
    g.set(10, 6, (96.0, 68.0, 40.0)); g.set(14, 5, (96.0, 68.0, 40.0))   # drawstring ends
    g.set(12, 9, mix(gold, WHITE, 0.25))               # knot stud
    g.grain(77, 4)
    g.outline(0.42)
    g.set(9, 6, mix(gold, WHITE, 0.55))
    return g


# ------------------------------------------------------------------ build

RARITY = [  # GEM_RARITY_NAME / GEM_RARITY_COL, index = rarity
    ('common', '#e8e4da'), ('fine', '#57d93d'), ('rare', '#5eb2ff'),
    ('epic', '#b388ff'), ('legendary', '#ffb52e'),
]
ORES = [    # GEMS table: id -> colour
    ('emerald', '#3ddc84'), ('topaz', '#ffd54a'), ('sapphire', '#5eb2ff'),
    ('ruby', '#ff5e6b'), ('amethyst', '#b388ff'), ('diamond', '#b2ebf2'),
]
NODES = [   # NODE_TYPES order: (slug, display name, body tone, [(crystal id, colour)])
    ('mossy-boulder', 'Mossy Boulder', (126.0, 120.0, 108.0), [('emerald', '#3ddc84'), ('topaz', '#ffd54a')]),
    ('river-rock', 'River Rock', (112.0, 126.0, 140.0), [('sapphire', '#5eb2ff'), ('emerald', '#3ddc84')]),
    ('sunstone', 'Sunstone', (170.0, 140.0, 98.0), [('topaz', '#ffd54a'), ('sapphire', '#5eb2ff')]),
    ('crimson-crag', 'Crimson Crag', (148.0, 86.0, 72.0), [('ruby', '#ff5e6b'), ('amethyst', '#b388ff')]),
    ('void-geode', 'Void Geode', (90.0, 78.0, 104.0), [('amethyst', '#b388ff'), ('diamond', '#b2ebf2')]),
]
RELICS = [
    ('pauldron', "Warden's Pauldron", relic_pauldron),
    ('crown', 'Thorn Crown', relic_crown),
    ('heart', 'Rotbloom Heart', relic_heart),
    ('sprout', 'Sprout Charm', relic_sprout),
    ('eye', "Emperor's Eye", relic_eye),
]


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []

    def emit(grid: Grid, fname: str, entry: dict):
        grid.finish().save(OUT_DIR / fname)
        manifest.append({ 'file': fname, **entry })
        print('wrote', fname)

    for i, (slug, col) in enumerate(RARITY):
        emit(soul_gem(i, col), f'gem-{slug}.png', {
            'kind': 'soul-gem', 'id': slug, 'rarityIndex': i,
            'gameRef': f'GEM_RARITY_NAME[{i}]',
            'label': f'Soul Gem — {slug.capitalize()} (rarity tier {i})',
            'note': 'Replaces the CSS .gemDot rotated square; tint colour is GEM_RARITY_COL[' + str(i) + ']. Stat type stays in the row label text.' })

    for j, (oid, col) in enumerate(ORES):
        emit(ore_cluster(col, seed=100 + j), f'ore-{oid}.png', {
            'kind': 'ore', 'id': oid, 'gameRef': f'GEMS.{oid}',
            'label': f'{oid.capitalize()} (mined material)',
            'note': 'Replaces the CSS .gemchip rotated square in forge costs and the GEMS inventory rows.' })

    for k, (slug, name, body, crystals) in enumerate(NODES):
        emit(node_rock(body, crystals, k, seed=200 + k), f'node-{slug}.png', {
            'kind': 'ore-node', 'id': slug, 'nodeIndex': k,
            'gameRef': f'NODE_TYPES[{k}]',
            'label': f'{name} (ore node)',
            'note': 'Menu/help icon for the mining node type; the world sprite remains decor-rock + drawn crystals.' })

    for rid, name, fn in RELICS:
        emit(fn(), f'relic-{rid}.png', {
            'kind': 'relic', 'id': rid, 'gameRef': f'RELICS.{rid}',
            'label': name,
            'note': 'Replaces the text-only relic row marker in the inventory RELICS section.' })

    emit(item_purse(), 'item-purse.png', {
        'kind': 'item', 'id': 'purse', 'gameRef': "SHOP_ITEMS[id='purse']",
        'label': 'Coin Purse',
        'note': 'The only SHOP_ITEMS entry with no icon anywhere (potion/bomb/shield already have SVG icons).' })

    (OUT_DIR / 'manifest.json').write_text(json.dumps({
        'generatedBy': 'tools/gen_icons.py',
        'size': 48, 'grid': 24, 'alpha': 'binary 0/255', 'minChannel': BLACK_POINT,
        'icons': manifest,
    }, indent=1) + '\n')
    print(f'manifest: {len(manifest)} icons')


if __name__ == '__main__':
    main()
