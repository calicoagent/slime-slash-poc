#!/usr/bin/env python3
"""prop_audit.py — Slime Slash prop placement audit (Handler, 2026-11-10:
'Tree shouldn't be on the road').

The game's scatter (genProps in index.html) originally placed trees and
rocks knowing only collision (canStandZ) — never the plates' PAINTED
roads — so trees landed mid-street in Alderwake and on the glade's dirt
track. v0.6.6 added a painted-road grid (buildWaterGrid) and a relocation
pass in genProps. This tool is the independent check of that system:

  1. It MIRRORS the game generator exactly (mulberry32 scatter, water
     grid, path grid, clear() rules, relocation ring search) and
     regenerates the before tables (scatter only) and after tables
     (scatter + relocation).
  2. It then verifies BOTH tables against GROUND TRUTH sampled from the
     full-resolution plate PNGs: a small disc (r=0.18u, 21 samples) at
     each prop's ground point, classified from the plate palette.
  3. Story-fixed placements (buildings, NPCs, shrines, the altar, and
     the authored set pieces: grave, tents, campfires, crate, logs)
     are checked report-only — the game never moves them.

Usage:
  python3 tools/prop_audit.py [--dump live-props.json]

--dump takes a JSON of the game's actual PROPS ({"zone":[{t,x,y},...]})
and cross-checks the mirror against it (position-for-position).

Terrain rules (PATH_RULES in index.html — keep the two in sync).
A pixel reads as ROAD when its red channel leads green by >= rg and
blue by >= rb at mean luminance >= lum (the warm-cobble test); the
cinderfell track is instead DARK warm ash: luminance <= lumMax.
Calibration evidence (plate pixels sampled 2026-11-10):
  town plaza cobble (188,167,135) rg21 rb53 lum163 -> road
  town lawn         (122,142, 55) rg-20           -> natural
  glade dirt track  (166,136, 82) rg30 rb84 lum128 -> road
  glade meadow      (118,140, 60) rg-22           -> natural
  hermit path       (183,136, 79) rg47 rb104      -> road
  hollow bracken    lum 66-93 (below lum 105)     -> natural
  hollow track      lum 116+                      -> road
  moor mid-browns   lum 84-96 (below lum 110)     -> natural
  moor track        lum ~122                      -> road
  cinderfell track  ( 84, 60, 45) lum 63, (75,52,42) lum 56 -> road (dark rule, lumMax 58 catches the darker of the pair in patches; the block vote smooths it)
  cinderfell ash    (105, 88, 76) lum 90          -> natural (too bright)
  cinderfell lava   (139, 52, 25) lum 72          -> natural (too bright — props may ring the lava field but the game's own water/block rules keep them off the cracks)
Water: mask zones (town, glade) read the .water.png alpha; other zones
use the game's colour rule (b > r+16 and b > 80 and g > 55, or the
darkWater variant for the moor).

Sampling geometry mirrors the game: the plate renders 2304px wide with
the diamond centred; world (x,y) -> plate pixel via cells I = x/0.6,
J = y/0.6: px = (I-J)*pw/48 + pw/2, py = (I+J+1)*pw/96.
The game's grids work on downsamples (192 wide for water, single centre
pixel per 0.3u block; 384 wide for roads, 40-sample patch per block,
block = road when >=45% of the patch reads road). PIL BILINEAR stands
in for the canvas resample; block counts can differ by a few blocks
from the browser's filter — the disc ground-truth check is the
authority, and --dump cross-checks the mirror against the real game.
"""
import argparse, json, math, os, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATES = os.path.join(ROOT, 'assets', 'isw', 'plates')

ZONE_U = 14.4
N = 48                      # WATER_GRID_N
ALTAR = (8.5, 6.4)
TOWN = (7.2, 7.2)

ZONES = {                   # mirror of ZONES_DEF (plate, mask, darkWater, blocks)
    'town':     dict(plate='alderwake.png',        mask=True),
    'glade':    dict(plate='landing_glade.png',    mask=True),
    'camp':     dict(plate='lakeside_camp.png'),
    'grove':    dict(plate='southwest_grove.png'),
    'hollow':   dict(plate='redbracken_hollow.png'),
    'wilds':    dict(plate='cinderfell.png',        blocks=[(1.2, 12.6, 1.35)]),
    'treasure': dict(plate='witherbriar_moor.png', darkWater=True, blocks=[(10.8, 10.6, 1.5)]),
    'hermit':   dict(plate='forest_path_1.png'),
}
COUNTS = {'town': (7, 4), 'glade': (26, 10), 'camp': (13, 6), 'grove': (30, 10),
          'hollow': (22, 10), 'wilds': (8, 16), 'treasure': (16, 12), 'hermit': (30, 8)}
HAND = {                    # authored set pieces pushed after the scatter
    'treasure': [('grave', 7.4, 6.6)],
    'hermit':   [('tent', 7.0, 6.8), ('campfire', 7.55, 7.35)],
    'hollow':   [('tent', 4.4, 11.0), ('campfire', 5.3, 11.7), ('crate', 6.2, 12.3),
                 ('log', 4.85, 12.15), ('log', 5.75, 11.25)],
}
EXITS = [('town', 0.55, 7.2), ('town', 13.85, 7.2), ('glade', 13.85, 7.2), ('glade', 7.2, 13.85),
         ('glade', 0.55, 10.4), ('camp', 7.2, 0.55), ('grove', 13.85, 7.2), ('grove', 7.2, 13.85),
         ('hollow', 7.2, 0.55), ('hollow', 7.2, 13.85), ('wilds', 7.2, 0.55), ('wilds', 13.85, 7.2),
         ('treasure', 0.55, 7.2), ('hermit', 0.55, 7.2)]
SHRINES = [('glade', 11.9, 4.4), ('grove', 11.9, 11.9), ('wilds', 4.6, 4.9), ('wilds', 10.6, 10.2)]
BUILDINGS = [('town', 5.4, 5.0), ('town', 9.2, 5.2), ('town', 5.6, 9.6),
             ('camp', 5.4, 10.2), ('camp', 6.8, 11.0), ('camp', 8.3, 11.5),
             ('hollow', 4.4, 11.0), ('hollow', 6.2, 12.3)]
NPCS = [('town', 'ELDER MIRRA', 7.7, 7.9), ('town', 'FORGE', 9.9, 6.3), ('town', 'WARDEN PIKE', 4.6, 7.1),
        ('town', 'THE CHILD', 6.2, 8.2), ('camp', 'BRAMBLE', 5.0, 9.2), ('camp', 'TANSY', 7.4, 10.0),
        ('camp', 'THE HERMIT', 3.8, 10.8), ('hollow', 'SCOUT VEX', 5.4, 11.8)]
STORY_FIXED = ([(z, 'building', x, y) for z, x, y in BUILDINGS] +
               [(z, 'npc:' + n, x, y) for z, n, x, y in NPCS] +
               [(z, 'shrine', x, y) for z, x, y in SHRINES] +
               [('glade', 'summoning altar', ALTAR[0], ALTAR[1])])

PATH_RULES = {
    'town': dict(rg=8, rb=25, lum=92), 'glade': dict(rg=8, rb=25, lum=92),
    'camp': dict(rg=8, rb=25, lum=92), 'grove': dict(rg=8, rb=25, lum=92),
    'hermit': dict(rg=8, rb=25, lum=92), 'hollow': dict(rg=8, rb=25, lum=105),
    'treasure': dict(rg=8, rb=25, lum=110),
    'wilds': dict(rg=8, rb=16, lumMax=58),
}


def jsround(v):
    return math.floor(v + 0.5)


def clamp(v, a, b):
    return max(a, min(b, v))


def road_px(rule, r, g, b):
    if 'lumMax' in rule:
        return (r - g >= rule['rg'] and r - b >= rule['rb'] and (r + g + b) / 3 <= rule['lumMax'])
    return (r - g >= rule['rg'] and r - b >= rule['rb'] and (r + g + b) / 3 >= rule['lum'])


def mulberry32(seed):
    a = seed & 0xFFFFFFFF

    def rnd():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = ((a ^ (a >> 15)) * (1 | a)) & 0xFFFFFFFF
        t = ((t + (((t ^ (t >> 7)) * (61 | t)) & 0xFFFFFFFF)) & 0xFFFFFFFF) ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return rnd


class Plate:
    """One zone's plate + the game's sampled grids, mirrored."""

    def __init__(self, zid):
        zd = ZONES[zid]
        self.zid = zid
        self.img = Image.open(os.path.join(PLATES, zd['plate'])).convert('RGB')
        self.pw, self.ph = self.img.size
        self.mask_img = None
        if zd.get('mask'):
            self.mask_img = Image.open(os.path.join(
                PLATES, zd['plate'].replace('.png', '.water.png'))).convert('RGBA')
        self.water = self._build_water(zd)
        self.path = self._build_path(zid)

    def _small(self, img, sw):
        sh = max(2, jsround(sw * img.size[1] / img.size[0]))
        return img.resize((sw, sh), Image.BILINEAR), sw, sh

    def _centre(self, bx, by, sw, sh):
        I, J = (bx + .5) * .5, (by + .5) * .5
        px = (I - J) * self.pw / 48 + self.pw / 2
        py = (I + J + 1) * self.pw / 96
        return (clamp(jsround(px / self.pw * sw), 0, sw - 1),
                clamp(jsround(py / self.ph * sh), 0, sh - 1))

    def _build_water(self, zd):
        small, sw, sh = self._small(self.img, 192)
        px = small.load()
        mdata = None
        if self.mask_img is not None:
            msmall, _, _ = self._small(self.mask_img, 192)
            mdata = msmall.load()
        grid = [[0] * N for _ in range(N)]
        for by in range(N):
            for bx in range(N):
                sx, sy = self._centre(bx, by, sw, sh)
                if mdata is not None:
                    water = mdata[sx, sy][3] > 60
                else:
                    r, g, b = px[sx, sy]
                    water = (b > r + 16 and b > 80 and g > 55) or \
                        (zd.get('darkWater') and b >= r - 6 and b > 30 and (r + g + b) / 3 < 85)
                grid[by][bx] = 1 if water else 0
        return grid

    def _build_path(self, zid):
        rule = PATH_RULES[zid]
        small, sw, sh = self._small(self.img, 384)
        px = small.load()
        grid = [[0] * N for _ in range(N)]
        for by in range(N):
            for bx in range(N):
                sx, sy = self._centre(bx, by, sw, sh)
                road = tot = 0
                for dy in range(-2, 3):
                    for dx in range(-4, 4):
                        X = clamp(sx + dx, 0, sw - 1)
                        Y = clamp(sy + dy, 0, sh - 1)
                        if road_px(rule, *px[X, Y]):
                            road += 1
                        tot += 1
                grid[by][bx] = 1 if road / tot >= .45 else 0
        return grid

    # --- game-logic mirrors -------------------------------------------------
    def water_at(self, x, y):
        bx, by = int(x / ZONE_U * N), int(y / ZONE_U * N)
        if bx < 0 or by < 0 or bx >= N or by >= N:
            return False
        return self.water[by][bx] == 1

    def zone_blocked(self, x, y):
        if not (.25 <= x <= ZONE_U - .25 and .25 <= y <= ZONE_U - .25):
            return True
        for bx_, by_, br in ZONES[self.zid].get('blocks', []):
            if (x - bx_) ** 2 + (y - by_) ** 2 < br * br:
                return True
        for bz, bx_, by_ in BUILDINGS:
            if bz == self.zid and (x - bx_) ** 2 + (y - by_) ** 2 < .64:
                return True
        return self.water_at(x, y)

    def clear(self, x, y):
        if self.zone_blocked(x, y):
            return False
        if self.zid == 'town' and (x - TOWN[0]) ** 2 + (y - TOWN[1]) ** 2 < 5.3:
            return False
        for ez, ex, ey in EXITS:
            if ez == self.zid and (x - ex) ** 2 + (y - ey) ** 2 < 1.1:
                return False
        for sz, sx, sy in SHRINES:
            if sz == self.zid and (x - sx) ** 2 + (y - sy) ** 2 < 1.0:
                return False
        for bz, bx_, by_ in BUILDINGS:
            if bz == self.zid and (x - bx_) ** 2 + (y - by_) ** 2 < 1.3:
                return False
        for nz, _n, nx, ny in NPCS:
            if nz == self.zid and (x - nx) ** 2 + (y - ny) ** 2 < .8:
                return False
        if self.zid == 'glade' and (x - ALTAR[0]) ** 2 + (y - ALTAR[1]) ** 2 < 2.1:
            return False
        return True

    def on_road(self, x, y):
        bx, by = int(x / ZONE_U * N), int(y / ZONE_U * N)
        for oy in (-1, 0, 1):
            for ox in (-1, 0, 1):
                nx, ny = bx + ox, by + oy
                if 0 <= nx < N and 0 <= ny < N and self.path[ny][nx]:
                    return True
        return False

    def disc_road(self, x, y):
        """The game's full-res disc sampler (zoneDisc in buildWaterGrid)."""
        rf, _wf = self.classify(x, y)
        return rf >= .45

    # --- full-resolution ground truth ---------------------------------------
    def plate_px(self, x, y):
        I, J = x / .6, y / .6
        px = (I - J) * self.pw / 48 + self.pw / 2
        py = (I + J + 1) * self.pw / 96
        return (clamp(jsround(px), 0, self.pw - 1), clamp(jsround(py), 0, self.ph - 1))

    def classify(self, x, y):
        """Disc sample (r=0.18u) at full plate resolution -> (road_frac, water_frac)."""
        rule = PATH_RULES[self.zid]
        pix = self.img.load()
        mpix = self.mask_img.load() if self.mask_img is not None else None
        offs = [(dx, dy) for dx in (-.135, -.0675, 0, .0675, .135)
                for dy in (-.135, -.0675, 0, .0675, .135) if dx * dx + dy * dy <= .18 ** 2]
        road = water = 0
        for dx, dy in offs:
            px, py = self.plate_px(x + dx, y + dy)
            if mpix is not None:
                if mpix[px, py][3] > 60:
                    water += 1
            else:
                r, g, b = pix[px, py]
                if (b > r + 16 and b > 80 and g > 55) or \
                   (ZONES[self.zid].get('darkWater') and b >= r - 6 and b > 30 and (r + g + b) / 3 < 85):
                    water += 1
            if road_px(rule, *pix[px, py]):
                road += 1
        n = len(offs)
        return road / n, water / n


def gen_tables(plate):
    """Mirror of genProps: returns (before, after) prop lists [{t,x,y}]."""
    zid = plate.zid
    rng = mulberry32(20261109 + len(zid) * 131 + ord(zid[0]) * 17)
    items = []

    def scatter(n, t):
        for _ in range(n):
            for _try in range(14):
                x = .7 + rng() * (ZONE_U - 1.4)
                y = .7 + rng() * (ZONE_U - 1.4)
                if not plate.clear(x, y):
                    continue
                items.append({'t': t, 'x': x, 'y': y, 's': .8 + rng() * .5})
                break

    scatter(COUNTS[zid][0], 'tree')
    scatter(COUNTS[zid][1], 'rock')
    before = [dict(i) for i in items]
    for t, x, y in HAND.get(zid, []):
        items.append({'t': t, 'x': x, 'y': y, 's': 1})

    def legal(nx, ny, self_i):
        if not plate.clear(nx, ny) or plate.on_road(nx, ny) or plate.disc_road(nx, ny):
            return False
        return all(o is self_i or (nx - o['x']) ** 2 + (ny - o['y']) ** 2 >= .1225 for o in items)

    for it in items:
        if it['t'] not in ('tree', 'rock'):
            continue
        if not plate.on_road(it['x'], it['y']) and not plate.disc_road(it['x'], it['y']) \
                and not plate.zone_blocked(it['x'], it['y']):
            continue
        moved = False
        r = .15
        while r <= 2.0 and not moved:
            for i in range(12):
                a = i / 12 * math.pi * 2 + r
                nx, ny = it['x'] + math.cos(a) * r, it['y'] + math.sin(a) * r
                if legal(nx, ny, it):
                    it['x'], it['y'] = nx, ny
                    moved = True
                    break
            r += .15
        if not moved:
            it['dropped'] = True
    after = [i for i in items if not i.get('dropped')]
    return before, after


def verdict(plate, x, y):
    rf, wf = plate.classify(x, y)
    if wf >= .45:
        return 'water'
    if rf >= .45:
        return 'road'
    return 'natural'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dump', help='JSON of live game PROPS to cross-check the mirror against')
    args = ap.parse_args()
    live = None
    if args.dump:
        with open(args.dump) as f:
            live = json.load(f)
        if isinstance(live, dict) and 'props' in live:
            live = live['props']

    print('PROP AUDIT — before = scatter only, after = scatter + relocation')
    print('(ground truth: full-res plate disc, r=0.18u; road/water at >=45% of the disc)\n')
    tot = dict(checked=0, road=0, water=0, moved=0, dropped=0, road_after=0, water_after=0)
    for zid in ZONES:
        plate = Plate(zid)
        before, after = gen_tables(plate)
        # match before->after by identity of scatter order: gen_tables mutates in
        # place, so recompute movement by re-running with tracking instead:
        # (before list holds pre-relocation copies of the scatter items only)
        b_verd = [verdict(plate, p['x'], p['y']) for p in before]
        a_verd = {}
        for p in after:
            a_verd.setdefault((p['t'], round(p['x'], 3), round(p['y'], 3)), verdict(plate, p['x'], p['y']))
        n_road = b_verd.count('road')
        n_water = b_verd.count('water')
        # moved/dropped: a before-item counts as moved if no after-item of the
        # same type sits at its spot; dropped if the zone total shrank.
        moved = 0
        for p in before:
            if not any(q['t'] == p['t'] and abs(q['x'] - p['x']) < .01 and abs(q['y'] - p['y']) < .01 for q in after):
                moved += 1
        dropped = len(before) + len(HAND.get(zid, [])) - len(after)
        a_road = sum(1 for v in a_verd.values() if v == 'road')
        a_water = sum(1 for v in a_verd.values() if v == 'water')
        print(f"{zid:9s} checked={len(before):3d}  on-road={n_road:2d}  in-water={n_water:2d}  "
              f"moved={moved:2d}  dropped={dropped}  | after: on-road={a_road} in-water={a_water} (of {len(after)} incl. set pieces)")
        for p, v in zip(before, b_verd):
            if v != 'natural':
                print(f"    before {v:5s}: {p['t']:5s} ({p['x']:.2f},{p['y']:.2f})")
        scatter_after = [p for p in after if p['t'] in ('tree', 'rock')]
        for p in scatter_after:
            v = verdict(plate, p['x'], p['y'])
            if v != 'natural':
                print(f"    !! after {v:5s}: {p['t']:5s} ({p['x']:.2f},{p['y']:.2f}) — STILL BAD")
        tot['checked'] += len(before); tot['road'] += n_road; tot['water'] += n_water
        tot['moved'] += moved; tot['dropped'] += dropped
        tot['road_after'] += a_road; tot['water_after'] += a_water
        if live and zid in live:
            lp = live[zid]
            match = sum(1 for p in after if any(q['t'] == p['t'] and abs(q['x'] - p['x']) < .01
                                                and abs(q['y'] - p['y']) < .01 for q in lp))
            print(f"    mirror vs live game: {match}/{len(after)} after-positions match "
                  f"(live total {len(lp)})")
            for q in lp:
                v = verdict(plate, q['x'], q['y'])
                if v != 'natural':
                    print(f"    live {v:5s}: {q['t']:5s} ({q['x']:.2f},{q['y']:.2f})")
    print(f"\nTOTAL     checked={tot['checked']}  on-road={tot['road']}  in-water={tot['water']}  "
          f"moved={tot['moved']}  dropped={tot['dropped']}  | after: on-road={tot['road_after']} in-water={tot['water_after']}")

    print('\nSTORY-FIXED PLACEMENTS (report-only — never moved by the game):')
    plates = {}
    bad = 0
    for zid, label, x, y in STORY_FIXED:
        if zid not in plates:
            plates[zid] = Plate(zid)
        v = verdict(plates[zid], x, y)
        if v != 'natural':
            bad += 1
            print(f"    !! {zid:9s} {label:18s} ({x:.2f},{y:.2f}) sits on {v}")
    if not bad:
        print('    all story-fixed placements sit on natural ground')
    print('\nHAND-PLACED SET PIECES (report-only):')
    bad = 0
    for zid, lst in HAND.items():
        if zid not in plates:
            plates[zid] = Plate(zid)
        for t, x, y in lst:
            v = verdict(plates[zid], x, y)
            if v != 'natural':
                bad += 1
                print(f"    !! {zid:9s} {t:9s} ({x:.2f},{y:.2f}) sits on {v}")
    if not bad:
        print('    all set pieces sit on natural ground')


if __name__ == '__main__':
    main()
