#!/usr/bin/env python3
"""Fix pass: replace the slime face-band slab with blended clean-face zones.

Commit ac487e3 restored face-band rows 120-215 byte-for-byte from the old
flat art; against the new detailed art that band reads as a pale horizontal
slab with hard seams at both edges.  This pass regenerates the exact same
conformed new art as ``deep_conform.py`` (asserted byte-identical to the
shipped sprites everywhere outside the old band), then finishes each slime
with ``deep_conform.finish_slime`` — whose face treatment is now small
feathered elliptical clean zones around the runtime face anchors,
locally smoothed and luminance-matched to the old face area.  Nothing
outside the feathered zones changes by a single byte.

Proof sheets (default /tmp/hd2d2-sheets):
* ``slimes-fixed.png`` — all 9 slimes at 2x;
* ``face-zoom.png`` — 3x crop of the pink face area, before/after, with a
  sample runtime face (droopy eyes + smile, style 0) drawn at the anchors.

``slime-king.png`` is never opened for writing; its md5 is guarded.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deep_conform as dc  # noqa: E402

IMG_DIR = dc.IMG_DIR
SLIMES = ["pink", *dc.SLIME_TARGETS.keys(), "metal"]
FACE_COL = (51, 38, 46)  # #33262e, the runtime FACE_COL


def finish_untreated(rgba: np.ndarray, current: Image.Image) -> np.ndarray:
    """deep_conform's old finish minus any face treatment (quantise only)."""
    alpha = np.asarray(current.convert("RGBA"))[:, :, 3]
    output = np.asarray(dc.quantise(rgba, alpha)).copy()
    output[:, :, 3] = alpha
    output[alpha == 0] = (0, 0, 0, 0)
    return output


def draw_sample_face(img: Image.Image) -> Image.Image:
    """Replicate drawSlimeFace style 0 (droopy eyes) + style 0 (smile) at
    master scale: eye oval 15x21 at (62,166)/(162,166) with slanted lid
    chord and highlight; smile arc width 37 centred (109,196)."""
    out = img.convert("RGBA").copy()
    d = ImageDraw.Draw(out)
    lw = max(2, round(256 * 0.013))  # runtime line width at master scale
    for cx, left in ((62, True), (162, False)):
        cy, ew, eh = 166, 15, 21
        d.ellipse((cx - ew / 2, cy - eh / 2, cx + ew / 2, cy + eh / 2), fill=FACE_COL + (255,))
        if left:
            chord = (cx + ew * .55, cy - eh * .30, cx - ew * .55, cy - eh * .02)
        else:
            chord = (cx - ew * .55, cy - eh * .30, cx + ew * .55, cy - eh * .02)
        d.line(chord, fill=FACE_COL + (255,), width=round(lw * 1.5))
        hx, hy, hr = cx - ew * .14, cy - eh * .14, ew * .15
        d.ellipse((hx - hr, hy - hr, hx + hr, hy + hr), fill=(255, 255, 255, 255))
    mx, my, mw = 109, 196, 37
    r = mw * .5
    cy = my - mw * .16
    # Runtime: ctx.arc(mx, my - mw*.16, mw*.5, PI*.18, PI*.82) -> 32.4..147.6 deg
    d.arc((mx - r, cy - r, mx + r, cy + r), start=32.4, end=147.6,
          fill=FACE_COL + (255,), width=lw)
    return out


def checkerboard(size: tuple[int, int], cell: int = 16) -> Image.Image:
    width, height = size
    board = Image.new("RGBA", size, (54, 57, 66, 255))
    draw = ImageDraw.Draw(board)
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(72, 75, 84, 255))
    return board


def fixed_sheet(fixed: dict[str, Image.Image], path: Path) -> None:
    names = [n for n in [*SLIMES, "king"] if n in fixed]
    scale = 2
    cols, label_h = 3, 26
    tw = 256 * scale
    th = 255 * scale
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * tw, rows * (th + label_h)), (35, 37, 43, 255))
    draw = ImageDraw.Draw(sheet)
    for i, name in enumerate(names):
        x = (i % cols) * tw
        y = (i // cols) * (th + label_h)
        note = "untouched" if name == "king" else "face-zone blend fix"
        draw.text((x + 8, y + 7), f"slime-{name}.png  ({note})", fill=(255, 225, 130, 255))
        tile = checkerboard((tw, th), cell=32)
        big = fixed[name].resize((tw, th), Image.Resampling.NEAREST)
        tile.alpha_composite(big)
        sheet.alpha_composite(tile, (x, y + label_h))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(path)


def face_zoom_sheet(before: Image.Image, after: Image.Image, path: Path) -> None:
    crop = (20, 128, 200, 232)  # face area: eyes, mouth, and art around them
    scale = 3
    label_h = 26
    panels = []
    for label, img in (("BEFORE (band slab)", before), ("AFTER (blended zones)", after)):
        faced = draw_sample_face(img).crop(crop)
        faced = faced.resize((faced.width * scale, faced.height * scale), Image.Resampling.NEAREST)
        panels.append((label, faced))
    width = sum(p.width for _, p in panels)
    height = max(p.height for _, p in panels) + label_h
    sheet = Image.new("RGBA", (width, height), (35, 37, 43, 255))
    draw = ImageDraw.Draw(sheet)
    x = 0
    for label, panel in panels:
        draw.text((x + 8, 7), label, fill=(255, 225, 130, 255))
        tile = checkerboard(panel.size, cell=24)
        tile.alpha_composite(panel)
        sheet.alpha_composite(tile, (x, label_h))
        x += panel.width
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contact-dir", type=Path, default=Path("/tmp/hd2d2-sheets"))
    args = parser.parse_args()

    king_before = dc.md5(dc.KING)
    hero_master = dc.single_subject(dc.latest("media-generation-hero-slime-pink-*.png"))

    currents = {n: Image.open(IMG_DIR / f"slime-{n}.png").convert("RGBA") for n in SLIMES}
    hero_rgba = dc.conform_rgb(currents["pink"], hero_master)

    def variant_for(name: str) -> np.ndarray:
        v = hero_rgba.copy()
        v[:, :, 3] = np.asarray(currents[name])[:, :, 3]
        return v

    bases = {"pink": hero_rgba}
    for colour, hue in dc.SLIME_TARGETS.items():
        bases[colour] = dc.palette_remap(variant_for(colour), hue)
    bases["metal"] = dc.chrome_derivative(variant_for("metal"))

    weights = dc.face_zone_weights((255, 256))
    zone_area = weights > 0
    report: dict[str, dict] = {}
    fixed: dict[str, Image.Image] = {}

    for name in SLIMES:
        current = currents[name]
        cur = np.asarray(current)
        untreated = finish_untreated(bases[name], current)

        # Determinism proof: the regenerated pipeline must reproduce the
        # shipped sprite byte-for-byte everywhere outside the old band.
        outside = np.ones(cur.shape[:2], dtype=bool)
        outside[dc.FACE_BAND, :] = False
        assert np.array_equal(untreated[outside], cur[outside]), \
            f"{name}: regenerated art differs from shipped art outside the old band"

        out_img = dc.finish_slime(bases[name], current)
        out = np.asarray(out_img)

        # Geometry proof: size + alpha identical to the pre-fix sprite.
        assert out_img.size == current.size, f"{name}: canvas changed"
        assert np.array_equal(out[:, :, 3], cur[:, :, 3]), f"{name}: alpha changed"

        # Locality proof: not one byte changes outside the feathered zones.
        assert np.array_equal(out[~zone_area], untreated[~zone_area]), \
            f"{name}: pixels changed outside the face zones"

        fixed[name] = out_img
        core = (weights >= 0.999) & (cur[:, :, 3] > 0)
        lum = np.array([0.2126, 0.7152, 0.0722])
        report[name] = {
            "size": list(out_img.size),
            "alpha_identical": True,
            "zone_core_old_lum": round(float((cur[:, :, :3].astype(float) @ lum)[core].mean()), 2),
            "zone_core_new_lum": round(float((out[:, :, :3].astype(float) @ lum)[core].mean()), 2),
            "changed_px": int(np.count_nonzero(np.any(out != cur, axis=2))),
        }

    sheet_set = dict(fixed)
    sheet_set["king"] = Image.open(dc.KING).convert("RGBA")  # display only, never written
    fixed_sheet(sheet_set, args.contact_dir / "slimes-fixed.png")
    face_zoom_sheet(currents["pink"], fixed["pink"], args.contact_dir / "face-zoom.png")

    for name, img in fixed.items():
        img.save(IMG_DIR / f"slime-{name}.png")

    king_after = dc.md5(dc.KING)
    assert king_before == king_after == "cb91b0e33d2ecee4c4b34cae0dc13ccc", "king md5 guard failed"
    print(json.dumps({"king_md5": king_after, "slimes": report}, indent=2))


if __name__ == "__main__":
    main()
