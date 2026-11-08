#!/usr/bin/env python3
"""Port Isekai Slime World environment art into Slime Slash slots.

Source: bon5co/isekai-slime-world (Handler's own game), client-phaser
props atlas (props.png + props.json frames). Extracted frames are graded
toward Slime Slash's LOW-CONTRAST palette (desaturate, compress contrast,
lift shadows, posterise) — ISW's painterly art reads hotter than our
grade-pass sprites ungraded. Alpha is preserved exactly.

Slots with no ISW fit (checked 2026-11-08): ground/water/shore TILES —
ISW paints full-scene 'plates', it has no tile set; pond — no pond prop
exists in the atlas; grass tufts — no grass-clump prop. Those slots keep
the current grade-pass sprites; water/sand tiles are synthesised in our
own palette speckle style (same recipe family as tile-grass).
"""
import json, sys
from PIL import Image, ImageEnhance

ISW = sys.argv[1] if len(sys.argv) > 1 else '/tmp/isw2'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'assets/img'

PORTS = {
    'tree-oak':           'decor-tree.png',
    'rock-mossy':         'decor-rock.png',
    'inn-3x3':            'bld-hospital.png',
    'house-timber-a-2x2': 'bld-bank.png',
    'stall-awning-green': 'bld-shop.png',
}

def grade(im):
    """Compress toward the low-contrast palette; alpha untouched."""
    alpha = im.getchannel('A')
    rgb = im.convert('RGB')
    rgb = ImageEnhance.Color(rgb).enhance(0.80)        # desaturate
    rgb = ImageEnhance.Contrast(rgb).enhance(0.90)     # soften contrast
    rgb = ImageEnhance.Brightness(rgb).enhance(1.03)   # gentle shadow lift
    rgb = rgb.quantize(colors=72, method=Image.MEDIANCUT).convert('RGB')
    out = rgb.convert('RGBA'); out.putalpha(alpha)
    return out

def main():
    d = json.load(open(f'{ISW}/client-phaser/public/props/props.json'))
    sheet = Image.open(f'{ISW}/client-phaser/public/props/props.png').convert('RGBA')
    for key, dest in PORTS.items():
        f = d['frames'][key]['frame']
        crop = sheet.crop((f['x'], f['y'], f['x'] + f['w'], f['y'] + f['h']))
        grade(crop).save(f'{OUT}/{dest}')
        print(f'{key:22s} -> {dest}  {crop.size}')

    # --- own-art fallback tiles (no ISW tiles exist) -------------------
    import random
    rng = random.Random(20261108)
    def speckle_tile(base, dots, size=256, n=2600, dash_every=9):
        im = Image.new('RGB', (size, size), base)
        px = im.load()
        for i in range(n):
            x, y = rng.randrange(size), rng.randrange(size)
            c = dots[rng.randrange(len(dots))]
            if i % dash_every == 0:   # sparse short dashes (glints / grain)
                for dx in range(rng.choice((2, 3))):
                    if x + dx < size: px[x + dx, y] = c
            else:
                px[x, y] = c
        return im
    speckle_tile((20, 92, 108), [(28, 110, 126), (36, 128, 144), (16, 76, 92), (120, 200, 210)]).save(f'{OUT}/tile-water.png')
    speckle_tile((232, 212, 154), [(222, 198, 138), (240, 224, 174), (206, 178, 118), (246, 234, 192)]).save(f'{OUT}/tile-sand.png')
    print('own-art fallback tiles -> tile-water.png, tile-sand.png (256x256)')

if __name__ == '__main__':
    main()
