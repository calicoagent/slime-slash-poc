#!/usr/bin/env python3
"""Grade pass for the four settlement NPC sprites (Bramble, Tansy, Vex,
the Hermit) — the finish the PIL-drawn folk (tools/gen_npcs2.py) lacked
next to the generated original four and the hd2d-graded slimes.

The originals carry what the flat drawings don't: multi-step tonal
shading from an upper-left light, a dark varied outline ring, internal
form separation at colour boundaries, mottled fur/cloth grain, and
grounding occlusion at the feet.  This pass bakes the equivalent into
the settlement four WITHOUT touching their silhouettes, identity or the
512x688 canvas: the generator's flat art is rebuilt into a temp dir,
graded on its native 128x172 grid (the drawing's own resolution, so the
chunky pixel grain survives), then NEAREST x4 back to 512x688 exactly
as gen_npcs2.finish() does.  Alpha is byte-identical by construction
and asserted against the shipped file before anything is overwritten.

Machinery (geometry, tone field, rim fields, hash grain) is reused from
tools/hd2d/enhance.py — the pass Handler approved for the slimes.
Deterministic: every texture is a splitmix hash of (x, y, seed).

Art law: no true black — every visible channel ends >= 26
(tools/lift_shadows.py's black point), asserted per sprite.

Run from the repo root:  python3 tools/grade_npcs.py [--only bramble]
"""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
GRID_W, GRID_H, SCALE = 128, 172, 4
NAMES = ("bramble", "tansy", "vex", "hermit")

_spec = importlib.util.spec_from_file_location(
    "hd2d_enhance", Path(__file__).resolve().parent / "hd2d" / "enhance.py"
)
enh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(enh)

INK = (34, 30, 27)        # eye ink — never grained or bevelled
GLINT = (246, 241, 227)   # eye glint — never darkened
WARM_RIM = (1.0, 0.94, 0.80)


# ---------------------------------------------------------------- base art

def regenerate_flat() -> dict[str, np.ndarray]:
    """Run tools/gen_npcs2.py in a temp cwd; return {name: grid RGBA}."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "assets" / "img").mkdir(parents=True)
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "gen_npcs2.py")],
            cwd=tmp, check=True, capture_output=True, text=True,
        )
        out = {}
        for name in NAMES:
            with Image.open(Path(tmp) / "assets" / "img" / f"npc-{name}.png") as im:
                arr = np.asarray(im.convert("RGBA"))
            grid = arr[::SCALE, ::SCALE]
            if grid.shape != (GRID_H, GRID_W, 4):
                raise AssertionError(f"{name}: unexpected grid {grid.shape}")
            out[name] = grid.copy()
    return out


# ---------------------------------------------------------------- helpers

def col_mask(flat: np.ndarray, visible: np.ndarray, *cols) -> np.ndarray:
    m = np.zeros(flat.shape[:2], dtype=bool)
    for c in cols:
        m |= np.all(flat[..., :3] == np.array(c), axis=2)
    return m & visible


def grain(rgb, ctx, mask, seed, amp, cell=2):
    """Stepped hash grain: factors land on discrete pixel-art steps."""
    n = enh.hash01(ctx["x"], ctx["y"], seed, cell, cell) * 0.65 \
        + enh.hash01(ctx["x"], ctx["y"], seed + 7) * 0.35
    q = np.round((n - 0.5) * 4.0)
    factor = np.where(mask, 1.0 + q * amp / 2.0, 1.0)
    return enh.clamp01(enh.scale_rgb(rgb, factor))


def stepped_blend(rgb, ctx, mask, centre, radii, colour, amount, steps=4):
    field = enh.stepped(enh.ellipse_field(ctx, *centre, *radii), steps)
    return enh.blend_to(rgb, colour, np.where(mask, field * amount, 0.0))


# ---------------------------------------------------------------- common

def grade_common(rgb, flat, ctx, seed, clean):
    """Directional tone, internal bevel, unified grain, outline, rim, AO."""
    visible = ctx["visible"]
    gx, gy = ctx["x"], ctx["y"]

    rgb = enh.tone_and_light(
        rgb, ctx, contrast=0.24, saturation_factor=1.05,
        top=0.10, bottom=0.12, left=0.045, right=0.035, rim_amount=0.0,
    )

    # Internal form separation: across a flat colour boundary the
    # up-left pixel is the lit face, the down-right pixel the drop.
    frgb = flat[..., :3]
    lit = np.zeros(visible.shape, dtype=bool)
    shade = np.zeros(visible.shape, dtype=bool)
    edge_ok = visible & (ctx["depth"] >= 1)
    diff_r = np.zeros(visible.shape, bool)
    diff_r[:, :-1] = np.any(frgb[:, :-1] != frgb[:, 1:], axis=2) \
        & visible[:, :-1] & visible[:, 1:]
    diff_d = np.zeros(visible.shape, bool)
    diff_d[:-1] = np.any(frgb[:-1] != frgb[1:], axis=2) \
        & visible[:-1] & visible[1:]
    lit[:, :-1] |= diff_r[:, :-1]; shade[:, 1:] |= diff_r[:, :-1]
    lit[:-1] |= diff_d[:-1]; shade[1:] |= diff_d[:-1]
    factor = np.ones(visible.shape)
    factor[edge_ok & lit & clean] *= 1.05
    factor[edge_ok & shade & clean] *= 0.935
    rgb = enh.clamp01(enh.scale_rgb(rgb, factor))

    # One light unified grain over everything that isn't eye detail.
    rgb = grain(rgb, ctx, visible & (ctx["depth"] >= 1) & clean,
                seed + 101, 0.028, cell=2)

    # Outline ring: depth-0 pixels blend toward a deep shade of their own
    # flat colour — deeper on the shadow side, lighter toward the light,
    # so the outline varies like the generated folks' does.
    depth = ctx["depth"]
    ring = depth == 0
    amt = 0.36 + 0.26 * ctx["rim_dark"] - 0.16 * ctx["rim_light"]
    target = np.clip(flat[..., :3].astype(np.float64) / 255.0 * 0.40,
                     26.0 / 255.0, 1.0)
    rgb = np.where(ring[..., None],
                   rgb * (1 - amt[..., None]) + target * amt[..., None], rgb)
    inner = (depth == 1) & (ctx["rim_dark"] > 0.4)
    rgb = enh.blend_to(rgb, (0.10, 0.09, 0.085),
                       np.where(inner, 0.10, 0.0))

    # Rim light on the upper-left silhouette, kept off pale faces/glints.
    pale = enh.luminance(flat[..., :3].astype(np.float64) / 255.0) > 0.90
    rim = (depth <= 1) & (ctx["rim_light"] > 0.28) & ~pale
    ramt = ctx["rim_light"] * np.where(depth == 0, 0.15, 0.08)
    rgb = enh.blend_to(rgb, WARM_RIM, np.where(rim, ramt, 0.0))

    # Grounding: contact occlusion at the feet.
    ao = (depth <= 2) & (ctx["ny"] > 0.86)
    rgb = enh.scale_rgb(rgb, np.where(ao, 0.94, 1.0))
    rgb = enh.clamp01(rgb)
    _ = gx, gy
    return rgb


# ---------------------------------------------------------------- sprites

def grade_bramble(rgb, flat, ctx, seed, clean):
    v = ctx["visible"]; gy = ctx["y"]
    SP, SPD, SPL = (74, 56, 38), (50, 38, 27), (112, 88, 58)
    CRM, CRM2 = (232, 211, 172), (242, 224, 188)
    dome = col_mask(flat, v, SP, SPD, SPL)
    # the dome stops being one brown: coarse tonal drift + fine speckle.
    # Spine TIPS stay sparse and live where the light lives (upper-left);
    # an even glitter reads as noise, not spines.
    rgb = grain(rgb, ctx, dome, seed + 11, 0.065, cell=3)
    rgb = grain(rgb, ctx, dome, seed + 13, 0.028, cell=1)
    roll = enh.hash01(ctx["x"], gy, seed + 17)
    lit_side = (1.0 - ctx["ny"]) * 0.6 + (1.0 - ctx["nx"]) * 0.4
    tips = dome & (roll > 0.955) & (lit_side > 0.35)
    rgb = enh.blend_to(rgb, (0.78, 0.65, 0.48), np.where(tips, 0.40, 0.0))
    pits = dome & (roll < 0.04)
    rgb = enh.scale_rgb(rgb, np.where(pits, 0.76, 1.0))
    rgb = grain(rgb, ctx, col_mask(flat, v, SPL), seed + 19, 0.05, cell=2)
    # face: soft upper-left light, a whisper of jaw shade
    face = col_mask(flat, v, CRM)
    rgb = stepped_blend(rgb, ctx, face, (0.42, 0.46), (0.30, 0.24),
                        tuple(c / 255 for c in CRM2), 0.38)
    rgb = enh.scale_rgb(rgb, np.where(face & (gy >= 118), 0.96, 1.0))
    muzzle = col_mask(flat, v, CRM2)
    rgb = stepped_blend(rgb, ctx, muzzle, (0.50, 0.60), (0.17, 0.11),
                        (0.985, 0.94, 0.82), 0.20)
    # apron cloth + strap + feet
    rgb = grain(rgb, ctx, col_mask(flat, v, (239, 230, 207), (150, 120, 84)),
                seed + 23, 0.032, cell=2)
    feet = col_mask(flat, v, (90, 66, 44))
    rgb = enh.scale_rgb(rgb, np.where(feet, 0.93, 1.0))
    return rgb


def grade_tansy(rgb, flat, ctx, seed, clean):
    v = ctx["visible"]; gx, gy = ctx["x"], ctx["y"]
    FU, FUD, FUL = (176, 106, 52), (138, 79, 36), (200, 134, 76)
    CRM = (240, 220, 184)
    fur = col_mask(flat, v, FU, FUD, FUL)
    # the tail: real banding across the curl + the strongest grain on her
    tail = fur & (gx >= 86)
    band = ((gy - 24) // 9) % 2 == 0
    rgb = enh.scale_rgb(rgb, np.where(tail, np.where(band, 1.045, 0.945), 1.0))
    rgb = grain(rgb, ctx, tail, seed + 11, 0.055, cell=2)
    rgb = grain(rgb, ctx, fur, seed + 13, 0.045, cell=2)
    rgb = grain(rgb, ctx, fur, seed + 15, 0.032, cell=5)
    # creams lit from upper-left; belly settles at the bottom
    cream = col_mask(flat, v, CRM)
    rgb = stepped_blend(rgb, ctx, cream, (0.40, 0.38), (0.34, 0.30),
                        (0.99, 0.955, 0.86), 0.22)
    rgb = enh.scale_rgb(rgb, np.where(cream & (gy > 140), 0.96, 1.0))
    rgb = enh.scale_rgb(rgb, np.where(fur & (gy < 14), 1.05, 1.0))
    # acorn: two-tone nut, grained cap
    nut = col_mask(flat, v, (201, 160, 106))
    rgb = enh.scale_rgb(rgb, np.where(nut, np.where(gy <= 127, 1.045, 0.95), 1.0))
    roll = enh.hash01(gx, gy, seed + 19)
    rgb = enh.scale_rgb(rgb, np.where(nut & (roll > 0.92), 1.07, 1.0))
    rgb = grain(rgb, ctx, col_mask(flat, v, (110, 74, 38)), seed + 23, 0.05, cell=2)
    rgb = enh.scale_rgb(rgb, np.where(col_mask(flat, v, FUD) & (gy > 158), 0.94, 1.0))
    return rgb


def grade_vex(rgb, flat, ctx, seed, clean):
    v = ctx["visible"]; gx, gy = ctx["x"], ctx["y"]
    FU, FUD, WHT = (201, 122, 48), (164, 94, 36), (242, 234, 216)
    DRK = (74, 52, 33)
    head = col_mask(flat, v, FU, (222, 168, 120)) & (gy < 90)
    rgb = stepped_blend(rgb, ctx, head, (0.38, 0.28), (0.45, 0.32),
                        (0.87, 0.59, 0.28), 0.20)
    rgb = enh.scale_rgb(rgb, np.where(head & (gy >= 72), 0.965, 1.0))
    white = col_mask(flat, v, WHT)
    muzzle = white & (gy < 90)
    settle = enh.smoothstep(70, 86, gy)
    rgb = enh.scale_rgb(rgb, np.where(muzzle, 1.0 - 0.05 * settle, 1.0))
    chest = white & (gy >= 90)
    rgb = enh.scale_rgb(rgb, np.where(chest & (ctx["nx"] > 0.60), 0.96, 1.0))
    # scarf: fold stripes on the hanging tail, lit band top, grain
    scarf = col_mask(flat, v, (85, 125, 60), (64, 98, 44))
    folds = (gx // 3) % 2 == 0
    rgb = enh.scale_rgb(rgb, np.where(scarf & (gy >= 86),
                                      np.where(folds, 0.93, 1.0), 1.0))
    rgb = enh.scale_rgb(rgb, np.where(scarf & (gy >= 76) & (gy <= 79), 1.06, 1.0))
    rgb = grain(rgb, ctx, scarf, seed + 11, 0.04, cell=2)
    # tail: gentle bands; the white tip settles grey at its foot
    tail = col_mask(flat, v, FU) & (gx < 48)
    band = (gy // 13) % 2 == 0
    rgb = enh.scale_rgb(rgb, np.where(tail, np.where(band, 1.02, 0.975), 1.0))
    rgb = enh.scale_rgb(rgb, np.where(white & (gx < 48) & (gy > 152), 0.95, 1.0))
    # socks get a top rim; ear tips vary a touch
    socks = col_mask(flat, v, DRK) & (gy >= 148)
    rgb = enh.scale_rgb(rgb, np.where(socks & (gy <= 152), 1.07, 1.0))
    rgb = grain(rgb, ctx, col_mask(flat, v, DRK), seed + 13, 0.035, cell=2)
    rgb = grain(rgb, ctx, col_mask(flat, v, FUD), seed + 17, 0.04, cell=2)
    # his body is the biggest single orange field of the four: give the
    # fur itself grain and a settled lower body, and break the chest's
    # paper flatness with a whisper of grain
    body = col_mask(flat, v, FU) & (gy >= 90)
    rgb = grain(rgb, ctx, body, seed + 19, 0.042, cell=2)
    rgb = enh.scale_rgb(rgb, np.where(body & (gy >= 128), 0.97, 1.0))
    rgb = grain(rgb, ctx, white, seed + 23, 0.018, cell=2)
    return rgb


def grade_hermit(rgb, flat, ctx, seed, clean):
    v = ctx["visible"]; gx, gy = ctx["x"], ctx["y"]
    MD, MS, MSL = (43, 96, 48), (79, 143, 68), (116, 175, 98)
    shawl = col_mask(flat, v, MD, MS, MSL)
    # drape shading: each scallop row sits a step deeper than the last,
    # vertical fold stripes run down the fall, scale tops catch light
    rows = np.clip(((gy - 94) // 10), 0, 5)
    rgb = enh.scale_rgb(rgb, np.where(shawl, 1.0 - 0.03 * rows, 1.0))
    folds = (gx // 4) % 2 == 0
    rgb = enh.scale_rgb(rgb, np.where(shawl & (gy >= 92),
                                      np.where(folds, 0.95, 1.0), 1.0))
    above = np.zeros(shawl.shape, bool)
    above[1:] = ~shawl[:-1]
    rgb = enh.scale_rgb(rgb, np.where(shawl & above & v, 1.07, 1.0))
    rgb = grain(rgb, ctx, shawl, seed + 11, 0.05, cell=2)
    # robe: quiet vertical folds + grain
    robe = col_mask(flat, v, (92, 84, 72), (64, 58, 50))
    rfolds = (gx // 5) % 2 == 0
    rgb = enh.scale_rgb(rgb, np.where(robe, np.where(rfolds, 0.955, 1.0), 1.0))
    rgb = grain(rgb, ctx, robe, seed + 13, 0.045, cell=2)
    rgb = enh.scale_rgb(rgb, np.where(robe & (gy > 160), 0.95, 1.0))
    # grey fur grain; blaze lit at the brow, muzzle settled
    fur = col_mask(flat, v, (141, 146, 145), (96, 102, 101), (170, 174, 170))
    rgb = grain(rgb, ctx, fur, seed + 17, 0.04, cell=2)
    rgb = grain(rgb, ctx, fur, seed + 19, 0.03, cell=4)
    blaze = col_mask(flat, v, (238, 233, 220))
    rgb = enh.scale_rgb(rgb, np.where(blaze & (gy < 38), 1.02, 1.0))
    rgb = enh.scale_rgb(rgb, np.where(
        col_mask(flat, v, (226, 219, 203)) & (gy > 88), 0.96, 1.0))
    # the badger stripes stop being voids: a whisper of variation
    rgb = grain(rgb, ctx, col_mask(flat, v, (51, 48, 44)), seed + 23, 0.05, cell=2)
    # staff: vertical wood grain, darker far edge
    staff = col_mask(flat, v, (110, 74, 38), (84, 58, 30))
    rgb = enh.scale_rgb(rgb, np.where(staff, np.where(gx % 2 == 0, 0.95, 1.0), 1.0))
    rgb = enh.scale_rgb(rgb, np.where(staff & (gx >= 104), 0.94, 1.0))
    rgb = enh.scale_rgb(rgb, np.where(col_mask(flat, v, (70, 74, 72)), 0.93, 1.0))
    return rgb


GRADERS = {
    "bramble": grade_bramble,
    "tansy": grade_tansy,
    "vex": grade_vex,
    "hermit": grade_hermit,
}


# ---------------------------------------------------------------- pipeline

def grade_sprite(name: str, flat_grid: np.ndarray) -> Image.Image:
    alpha = flat_grid[..., 3].copy()
    flat = flat_grid.copy()
    ctx = enh.geometry(alpha)
    seed = 0x5EED + NAMES.index(name) * 977
    rgb = flat[..., :3].astype(np.float64) / 255.0

    clean = ctx["visible"] \
        & ~col_mask(flat, ctx["visible"], INK, GLINT, (40, 34, 30))

    rgb = GRADERS[name](rgb, flat, ctx, seed, clean)
    rgb = grade_common(rgb, flat, ctx, seed, clean)

    out8 = np.rint(enh.clamp01(rgb) * 255.0)
    out8 = np.round(out8 / 5.0) * 5.0                      # stepped tones
    vis = alpha > 0
    out8[vis] = np.maximum(out8[vis], 26.0)                # art law
    grid_rgba = np.dstack((out8.astype(np.uint8), alpha))
    grid_rgba[~vis] = (0, 0, 0, 0)
    return Image.fromarray(grid_rgba, mode="RGBA").resize(
        (GRID_W * SCALE, GRID_H * SCALE), Image.NEAREST)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", action="append", choices=list(NAMES))
    args = parser.parse_args()
    selected = args.only or list(NAMES)

    flats = regenerate_flat()
    for name in selected:
        path = REPO_ROOT / "assets" / "img" / f"npc-{name}.png"
        with Image.open(path) as im:
            before = np.asarray(im.convert("RGBA"))
        if before.shape != (GRID_H * SCALE, GRID_W * SCALE, 4):
            raise AssertionError(f"{name}: shipped canvas is {before.shape}")
        if not np.array_equal(before[..., 3], np.asarray(
                Image.fromarray(flats[name]).resize(
                    (GRID_W * SCALE, GRID_H * SCALE), Image.NEAREST))[..., 3]):
            raise AssertionError(f"{name}: regenerated alpha != shipped alpha")

        graded = grade_sprite(name, flats[name])
        result = np.asarray(graded)
        if not np.array_equal(result[..., 3], before[..., 3]):
            raise AssertionError(f"{name}: alpha changed")
        vis = result[..., 3] > 0
        min_ch = int(result[vis][..., :3].min())
        if min_ch < 26:
            raise AssertionError(f"{name}: visible channel {min_ch} < 26")
        n_before = len(np.unique(before[vis][..., :3], axis=0))
        n_after = len(np.unique(result[vis][..., :3], axis=0))
        graded.save(path)
        print(f"{name}: 512x688, alpha identical, min visible channel "
              f"{min_ch}, visible colours {n_before} -> {n_after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
