#!/usr/bin/env python3
"""Shadow-lift pass for Slime Slash art.

Handler's art law: the style forbids true black. This script raises the
black point of every PNG under assets/ (except the byte-frozen King sprite)
per channel:

    out = L + in * (255 - L) / 255,   L = 26

Pure black becomes (26,26,26), shadows lift proportionally, whites are
unchanged, hues are preserved. Alpha channels are never touched.

Sprites whose visible (alpha > 0) palette is <= 128 colours are re-quantised
back to that palette size (no dithering) so the limited-palette pixel art
stays crisp; richer images (NPC portraits, FX atlases) are lifted per-colour
without quantisation.

Run from the repo root:  python3 tools/lift_shadows.py
Writes a before/after contact sheet of the darkest offenders to
/tmp/lift-sheet.png and prints a per-file min-value table. Asserts, per
file: canvas size unchanged, alpha channel byte-identical (RGBA files),
and no visible pixel with any channel < 26 after the lift.
"""

from pathlib import Path
import hashlib
import sys

import numpy as np
from PIL import Image, ImageDraw

L = 26
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
KING = ASSETS / "img" / "slime-king.png"
KING_MD5 = "cb91b0e33d2ecee4c4b34cae0dc13ccc"
SHEET_PATH = Path("/tmp/lift-sheet.png")
SHEET_FILES = [
    "img/npc-elder.png", "img/npc-forge.png", "img/npc-pike.png",
    "img/npc-child.png", "img/slime-metal.png",
    "weapons/dagger.png", "weapons/sword.png", "weapons/katana.png",
    "weapons/spear.png", "weapons/great.png", "weapons/hammer.png",
    "weapons/pick.png",
]


def md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def lift_values(values):
    """Apply the black-point lift to an int array of channel values."""
    out = L + values.astype(np.float64) * (255 - L) / 255.0
    return np.clip(np.floor(out + 0.5), L, 255).astype(np.uint8)


def stats(arr):
    """arr: HxWx4 uint8. Returns (min channel, min luminance, exact-black px)
    over visible pixels (alpha > 0)."""
    vis = arr[arr[..., 3] > 0][:, :3]
    if len(vis) == 0:
        return None, None, 0
    lum = vis[:, 0] * 0.2126 + vis[:, 1] * 0.7152 + vis[:, 2] * 0.0722
    black = int(np.sum(np.all(vis == 0, axis=1)))
    return int(vis.min()), float(lum.min()), black


def process(path):
    im = Image.open(path)
    orig_mode, orig_size = im.mode, im.size
    rgba = np.array(im.convert("RGBA"))
    alpha_before = rgba[..., 3].copy()
    before = stats(rgba)
    vis_mask = rgba[..., 3] > 0
    vis_colors = np.unique(rgba[..., :3][vis_mask].reshape(-1, 3), axis=0) \
        if vis_mask.any() else np.zeros((0, 3), dtype=np.uint8)
    n_vis = len(vis_colors)

    # Map every distinct RGB triplet in the file (visible or not).
    flat = rgba[..., :3].reshape(-1, 3)
    uniq, inverse = np.unique(flat, axis=0, return_inverse=True)
    if 0 < n_vis <= 128:
        # Lift the visible palette, then re-quantise it to its own size.
        swatch = Image.fromarray(vis_colors.reshape(1, -1, 3), "RGB")
        lifted = Image.fromarray(
            lift_values(np.array(swatch)).reshape(1, -1, 3), "RGB")
        if n_vis > 1:
            q = lifted.quantize(colors=n_vis,
                                method=Image.Quantize.MEDIANCUT,
                                dither=Image.Dither.NONE)
            palette = np.array(q.getpalette()[: n_vis * 3],
                               dtype=np.uint8).reshape(-1, 3)
            # quantize returns palette entries in swatch order via indices
            pal = palette[np.array(q)]
            pal = np.maximum(pal.reshape(-1, 3), L)
            vis_map = {tuple(c): tuple(p) for c, p in zip(vis_colors, pal)}
        else:
            vis_map = {tuple(vis_colors[0]):
                       tuple(np.maximum(lift_values(vis_colors)[0], L))}
        mapped = np.empty_like(uniq)
        for i, c in enumerate(uniq):
            t = tuple(c)
            mapped[i] = vis_map.get(
                t, tuple(lift_values(np.array([c]))[0]))
    else:
        mapped = lift_values(uniq)
    out_rgb = mapped[inverse].reshape(rgba.shape[0], rgba.shape[1], 3)

    if orig_mode == "RGB":
        Image.fromarray(out_rgb, "RGB").save(path)
    else:
        out = np.dstack([out_rgb, alpha_before])
        Image.fromarray(out, "RGBA").save(path)

    # Verify from disk.
    im2 = Image.open(path)
    assert im2.size == orig_size, f"{path}: size changed"
    rgba2 = np.array(im2.convert("RGBA"))
    if orig_mode == "RGBA":
        assert np.array_equal(rgba2[..., 3], alpha_before), \
            f"{path}: alpha channel changed"
    after = stats(rgba2)
    if after[0] is not None:
        assert after[0] >= L, f"{path}: channel {after[0]} < {L} after lift"
    colors_after = len(np.unique(rgba2[..., :3][rgba2[..., 3] > 0]
                                 .reshape(-1, 3), axis=0)) \
        if (rgba2[..., 3] > 0).any() else 0
    return before, after, n_vis, colors_after


def make_sheet(befores, files):
    cell_w, cell_h, label_h = 420, 210, 24
    rows = len(files)
    sheet = Image.new("RGB", (cell_w * 2 + 24, (cell_h + label_h) * rows + 8),
                      (216, 223, 210))
    d = ImageDraw.Draw(sheet)
    ink = (51, 38, 46)
    for r, rel in enumerate(files):
        y = 4 + r * (cell_h + label_h)
        d.text((8, y + 4), f"{rel}   BEFORE | AFTER", fill=ink)
        for c, key in enumerate(("before", "after")):
            src = befores[rel] if key == "before" else \
                Image.open(ASSETS / rel).convert("RGBA")
            thumb = src.copy()
            thumb.thumbnail((cell_w - 16, cell_h - 8))
            bg = Image.new("RGBA", (cell_w - 8, cell_h - 4), (128, 128, 128, 255))
            bg.alpha_composite(thumb, ((bg.width - thumb.width) // 2,
                                       (bg.height - thumb.height) // 2))
            sheet.paste(bg.convert("RGB"), (8 + c * (cell_w + 8), y + label_h))
    sheet.save(SHEET_PATH)


def main():
    if md5(KING) != KING_MD5:
        sys.exit("King md5 mismatch BEFORE the pass — aborting.")
    files = sorted(p for p in ASSETS.rglob("*.png") if p != KING)
    befores = {rel: Image.open(ASSETS / rel).convert("RGBA")
               for rel in SHEET_FILES}
    print(f"{'file':38} {'minCh':>10} {'minLum':>14} {'blkPx':>8} "
          f"{'colours':>12}")
    n_black_files = 0
    for p in files:
        rel = str(p.relative_to(ASSETS))
        before, after, n_before, n_after = process(p)
        if before[2] > 0:
            n_black_files += 1
        print(f"{rel:38} {before[0]:>4}->{after[0]:<5} "
              f"{before[1]:>6.1f}->{after[1]:<7.1f} {before[2]:>8} "
              f"{n_before:>5}->{n_after:<6}")
    make_sheet(befores, SHEET_FILES)
    assert md5(KING) == KING_MD5, "King md5 changed!"
    print(f"\nProcessed {len(files)} files; {n_black_files} contained "
          f"exact-black visible pixels.")
    print(f"King md5 unchanged: {KING_MD5}")
    print(f"Contact sheet: {SHEET_PATH}")


if __name__ == "__main__":
    main()
