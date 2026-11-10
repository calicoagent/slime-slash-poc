#!/usr/bin/env python3
"""pixels.py — pixel metrics for the Slime Slash basics gate.

Invoked by tools/basics-gate/run.cjs with a jobs JSON path as argv[1];
prints a results JSON to stdout. Uses PIL (same dependency as
tools/prop_audit.py). Jobs:

  trees:  {frame, dsf, trees:[{id, cx, cy, w, u}]}   (CSS px)
          VERTICAL self-reference: strips A (base+2..base+10) and B
          (base+10..base+22) below the sprite's visible base
          (base = cy + .03*u, width 0.5*w) are compared against strip
          C (base+26..base+40) in the SAME column. The pre-v0.6.6
          shadow ellipse (flat rgba(38,32,40,.18), centre ~base-.03*w,
          ry .068*w) reaches ~base+17, so it darkens A and B but never
          C; dip = min(A,B)/C drops. No shadow -> ~1 (same ground
          patch, 30px apart, texture is vertically correlated).
          Lateral reference strips were tried first and discarded:
          in a dense iso forest the neighbouring canopies (a tree
          sprite is ~440px wide on desktop) occupy the side bands and
          contaminate them worse than the signal.
  crowd:  {portrait, desktop, densePortrait, denseDesktop, carpet}
          frame paths (any may be null). Fraction of WHOLE-frame pixels
          matching the plate ground palette families (grass / path /
          water). Slime pastels are bright (lum >= ~195) and fall
          outside every family's luminance cap. (A central-region
          variant was tried first and discarded: the musou pack
          converges on the player, so the centre is the noisiest
          possible sample — whole-frame separates the v0.6.0 carpet,
          0.213, from healthy builds, 0.46+, with wide margins.)
  sword:  {frame, dsf, grip:{x,y}, tip:{x,y}}  (grip/tip in CSS px)
          Samples the segment grip->tip in the rest frame and reports
          the fraction of sample points matching the blade palette
          (pale steel: lum 140..240, low saturation, blue >= red).
          This measures the RENDERED blade — the v0.6.5 aliasing bug
          left the geometry probe reading full reach while only a 7px
          pommel dot was drawn; rendered fraction there is ~0.
  crops:  [{src, out, cx, cy, w, h}]   (device px) centred crops.
  montage:{out, cols, cellW, items:[{path, label}]}
"""
import json, sys
from PIL import Image, ImageDraw


def lum(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def rect_mean_lum(img, x0, y0, x1, y1):
    x0 = max(0, int(x0)); y0 = max(0, int(y0))
    x1 = min(img.width, int(x1)); y1 = min(img.height, int(y1))
    if x1 <= x0 or y1 <= y0:
        return None
    crop = img.crop((x0, y0, x1, y1)).convert('RGB')
    px = list(crop.getdata())
    return sum(lum(r, g, b) for r, g, b in px) / len(px)


def tree_metrics(job):
    img = Image.open(job['frame']).convert('RGB')
    dsf = job.get('dsf', 1)
    out = []
    for t in job['trees']:
        cx, cy, w = t['cx'] * dsf, t['cy'] * dsf, t['w'] * dsf
        # the sprite's visible base (its bottom edge) sits at cy + .03*u
        # in game space; the ground strips sample BELOW that base. The
        # pre-v0.6.6 shadow ellipse (centre ~base-.03*w, ry .068*w)
        # reaches ~base+17 game px, so strips A/B sit inside its span.
        base = cy + .03 * t['u'] * dsf
        res = {'id': t['id']}
        lums = {}
        for (dy0, dy1, key) in [(2, 10, 'lumA'), (10, 22, 'lumB'), (26, 40, 'lumC')]:
            v = rect_mean_lum(img, cx - .25 * w, base + dy0 * dsf, cx + .25 * w, base + dy1 * dsf)
            lums[key] = v
            res[key] = round(v, 1) if v else None
        if lums['lumA'] and lums['lumB'] and lums['lumC']:
            res['dip'] = round(min(lums['lumA'], lums['lumB']) / lums['lumC'], 4)
        else:
            res['dip'] = None
        out.append(res)
    return out


def ground_fraction(path):
    if not path:
        return None
    img = Image.open(path).convert('RGB')
    img = img.resize((480, max(1, int(480 * img.height / img.width))), Image.BILINEAR)
    px = list(img.getdata())
    fam = {'grass': 0, 'path': 0, 'water': 0}
    ground = 0
    for r, g, b in px:
        L = lum(r, g, b)
        if g > r + 8 and g > b + 10 and 55 < L < 195:
            fam['grass'] += 1; ground += 1
        elif r > g + 10 and g > b + 10 and 85 < L < 195:
            fam['path'] += 1; ground += 1
        elif b > r + 10 and b > 60 and g > 40 and L < 190:
            fam['water'] += 1; ground += 1
    n = len(px)
    return {'fraction': round(ground / n, 4),
            'families': {k: round(v / n, 4) for k, v in fam.items()},
            'regionPx': n}


def sword_metrics(job):
    img = Image.open(job['frame']).convert('RGB')
    dsf = job.get('dsf', 1)
    gx, gy = job['grip']['x'] * dsf, job['grip']['y'] * dsf
    tx, ty = job['tip']['x'] * dsf, job['tip']['y'] * dsf
    hits, total = 0, 0
    for i in range(41):
        t = .12 + (.95 - .12) * i / 40
        x = int(gx + (tx - gx) * t); y = int(gy + (ty - gy) * t)
        if x < 0 or y < 0 or x >= img.width or y >= img.height:
            continue
        r, g, b = img.getpixel((x, y))
        total += 1
        L = lum(r, g, b)
        # measured blade steel on the fixed build: ~(163,177,192) —
        # blue channel clearly above red; ground/stone/path never is
        if 140 <= L <= 240 and max(r, g, b) - min(r, g, b) <= 60 and b >= r + 10:
            hits += 1
    return {'bladeFraction': round(hits / total, 4) if total else 0, 'samples': total}


def do_crops(jobs):
    made = []
    for c in jobs:
        img = Image.open(c['src'])
        x0 = max(0, min(img.width - c['w'], int(c['cx'] - c['w'] / 2)))
        y0 = max(0, min(img.height - c['h'], int(c['cy'] - c['h'] / 2)))
        img.crop((x0, y0, x0 + c['w'], y0 + c['h'])).save(c['out'])
        made.append(c['out'])
    return made


def do_montage(job):
    cols = job.get('cols', 3)
    cellW = job.get('cellW', 620)
    labelH = 26
    thumbs = []
    for it in job['items']:
        try:
            img = Image.open(it['path']).convert('RGB')
        except Exception:
            continue
        h = max(1, int(cellW * img.height / img.width))
        thumbs.append((it['label'], img.resize((cellW, h), Image.BILINEAR)))
    if not thumbs:
        return None
    rows = (len(thumbs) + cols - 1) // cols
    cellH = max(t.height for _, t in thumbs) + labelH
    sheet = Image.new('RGB', (cols * cellW, rows * cellH), (24, 20, 18))
    d = ImageDraw.Draw(sheet)
    for i, (label, t) in enumerate(thumbs):
        x = (i % cols) * cellW
        y = (i // cols) * cellH
        sheet.paste(t, (x, y + labelH))
        d.rectangle([x, y, x + cellW - 1, y + labelH - 1], fill=(38, 32, 40))
        d.text((x + 8, y + 7), label, fill=(255, 233, 168))
    sheet.save(job['out'])
    return job['out']


def main():
    jobs = json.load(open(sys.argv[1]))
    res = {}
    if 'trees' in jobs:
        res['trees'] = tree_metrics(jobs['trees'])
    if 'crowd' in jobs:
        res['crowd'] = {k: ground_fraction(v) for k, v in jobs['crowd'].items()}
    if 'sword' in jobs:
        res['sword'] = {k: sword_metrics(v) for k, v in jobs['sword'].items()}
    if 'crops' in jobs:
        res['crops'] = do_crops(jobs['crops'])
    if 'montage' in jobs:
        res['montage'] = do_montage(jobs['montage'])
    print(json.dumps(res))


if __name__ == '__main__':
    main()
