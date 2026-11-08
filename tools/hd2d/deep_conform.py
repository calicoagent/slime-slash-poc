#!/usr/bin/env python3
"""Deep-detail HD-2D conforming pass for Slime Slash.

This pass starts from generated, richly detailed masters in ``gen/hd2d2``
and conforms them to the sprites already shipped in ``assets/img``:

* the generated RGB art is warped from its own subject bounding box into the
  current sprite's alpha bounding box;
* missing samples are filled from the nearest generated foreground pixel, so
  no white sheet background can bleed into a silhouette;
* the current sprite's alpha channel and canvas size are copied back exactly;
* after palette work and quantisation, small elliptical zones around the
  runtime face anchors are blended to a locally smoothed, luminance-matched
  version of the new art (see ``face_zone_blend``), so runtime faces sit on
  clean gel with no seam against the detailed art around them;
* the coloured slime family is palette-remapped from the conformed pink hero;
* metal is a cool chrome derivative of the same hero.

``slime-king.png`` is never opened for writing and is only hashed before and
after as a guard.  The script also asserts, for every output, that canvas size
and every alpha value match the pre-pass sprite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage


REPO_ROOT = Path(__file__).resolve().parents[2]
IMG_DIR = REPO_ROOT / "assets" / "img"
GEN_DIR = REPO_ROOT / "gen" / "hd2d2"
KING = IMG_DIR / "slime-king.png"
FACE_BAND = slice(120, 216)  # rows 120..215 inclusive
MAX_COLOURS = 128

SLIME_TARGETS = {
    "blue": 196.2,
    "green": 120.8,
    "mint": 156.2,
    "orange": 25.9,
    "purple": 269.2,
    "yellow": 47.7,
}
SOURCE_PINK_HUE = 333.4


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def latest(pattern: str) -> Path:
    matches = sorted(GEN_DIR.glob(pattern), key=lambda p: p.stat().st_mtime)
    if not matches:
        raise FileNotFoundError(f"no generated master matching {pattern} in {GEN_DIR}")
    return matches[-1]


def external_white_mask(rgb: np.ndarray) -> np.ndarray:
    """Return True for near-white pixels connected to an image border."""
    near_white = (rgb.min(axis=2) > 238) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 25)
    labels, count = ndimage.label(near_white)
    if count == 0:
        return np.zeros(rgb.shape[:2], dtype=bool)
    border = set(np.unique(np.concatenate([
        labels[0, :], labels[-1, :], labels[:, 0], labels[:, -1]
    ])))
    border.discard(0)
    return np.isin(labels, list(border))


def subject_from_panel(panel: Image.Image) -> tuple[Image.Image, np.ndarray, tuple[int, int, int, int]]:
    """Extract one generated subject and its foreground mask from a panel."""
    rgb = np.asarray(panel.convert("RGB"))
    foreground = ~external_white_mask(rgb)

    # Keep meaningful components only.  This matters for the rock, whose
    # shipped design is a main stone plus a smaller satellite stone.
    labels, count = ndimage.label(foreground)
    keep = np.zeros_like(foreground)
    panel_area = foreground.size
    sizes = ndimage.sum(foreground, labels, range(1, count + 1))
    largest = int(np.argmax(sizes)) + 1 if count else 0
    for label in range(1, count + 1):
        component = labels == label
        if component.sum() < max(250, panel_area * 0.001):
            continue
        # A neighbour panel's subject can bleed a sliver across the panel
        # border (the rock's tip enters the tree panel).  The panel's own
        # subject is the largest component; smaller components touching a
        # vertical panel border belong to the neighbour.
        touches_side = bool(
            component[:, 0].any() or component[:, -1].any()
        )
        if touches_side and label != largest:
            continue
        keep |= component
    if not np.any(keep):
        raise ValueError("generated panel contains no foreground subject")

    ys, xs = np.where(keep)
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    return panel.convert("RGB"), keep, bbox


def split_sheet(path: Path) -> list[tuple[Image.Image, np.ndarray, tuple[int, int, int, int]]]:
    sheet = Image.open(path).convert("RGB")
    width, height = sheet.size
    if width % 3:
        raise ValueError(f"sheet width {width} is not divisible into three panels")
    panel_w = width // 3
    return [
        subject_from_panel(sheet.crop((i * panel_w, 0, (i + 1) * panel_w, height)))
        for i in range(3)
    ]


def single_subject(path: Path) -> tuple[Image.Image, np.ndarray, tuple[int, int, int, int]]:
    return subject_from_panel(Image.open(path).convert("RGB"))


def alpha_bbox(alpha: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(alpha > 0)
    if xs.size == 0:
        raise ValueError("target sprite has no visible pixels")
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def conform_rgb(
    current: Image.Image,
    subject: tuple[Image.Image, np.ndarray, tuple[int, int, int, int]],
) -> np.ndarray:
    """Warp generated RGB into the current sprite's alpha bounding box."""
    current_rgba = current.convert("RGBA")
    target_alpha = np.asarray(current_rgba.getchannel("A"))
    tx0, ty0, tx1, ty1 = alpha_bbox(target_alpha)
    target_w, target_h = tx1 - tx0, ty1 - ty0

    source_image, source_mask, (sx0, sy0, sx1, sy1) = subject
    source_rgb = source_image.crop((sx0, sy0, sx1, sy1)).resize(
        (target_w, target_h), Image.Resampling.LANCZOS
    )
    source_alpha = Image.fromarray(
        np.where(source_mask, 255, 0).astype(np.uint8), mode="L"
    ).crop((sx0, sy0, sx1, sy1)).resize(
        (target_w, target_h), Image.Resampling.BILINEAR
    )

    rgb = np.asarray(source_rgb).astype(np.float64)
    mask = np.asarray(source_alpha).astype(np.float64) / 255.0

    solid = mask > 0.72
    if not np.any(solid):
        solid = mask > 0.05
    if not np.any(solid):
        raise ValueError("warped generated subject has no solid foreground")
    nearest = ndimage.distance_transform_edt(
        ~solid, return_distances=False, return_indices=True
    )
    filled = rgb[tuple(nearest)]
    warped = rgb * mask[..., None] + filled * (1.0 - mask[..., None])

    output = np.asarray(current_rgba).copy()
    output[ty0:ty1, tx0:tx1, :3] = np.rint(np.clip(warped, 0, 255)).astype(np.uint8)
    return output


def quantise(rgba: np.ndarray, alpha: np.ndarray) -> Image.Image:
    rgb = rgba[:, :, :3].copy()
    rgb[alpha == 0] = 0
    paletted = Image.fromarray(rgb, mode="RGB").quantize(
        colors=MAX_COLOURS,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    output = np.dstack((np.asarray(paletted.convert("RGB")), alpha))
    output[alpha == 0] = (0, 0, 0, 0)
    return Image.fromarray(output.astype(np.uint8), mode="RGBA")


def rgb_to_hsv(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rgb = rgb.astype(np.float64) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    maxc = rgb.max(axis=2)
    minc = rgb.min(axis=2)
    delta = maxc - minc
    hue = np.zeros_like(maxc)
    nonzero = delta > 1e-9
    idx = nonzero & (maxc == r)
    hue[idx] = (60.0 * ((g - b)[idx] / delta[idx]) + 360.0) % 360.0
    idx = nonzero & (maxc == g)
    hue[idx] = 60.0 * ((b - r)[idx] / delta[idx]) + 120.0
    idx = nonzero & (maxc == b)
    hue[idx] = 60.0 * ((r - g)[idx] / delta[idx]) + 240.0
    saturation = np.divide(delta, maxc, out=np.zeros_like(delta), where=maxc > 1e-9)
    return hue, saturation, maxc


def hsv_to_rgb(hue: np.ndarray, saturation: np.ndarray, value: np.ndarray) -> np.ndarray:
    hue = np.mod(hue, 360.0)
    chroma = value * saturation
    x = chroma * (1.0 - np.abs(np.mod(hue / 60.0, 2.0) - 1.0))
    m = value - chroma
    zero = np.zeros_like(hue)
    conditions = [
        hue < 60, hue < 120, hue < 180, hue < 240, hue < 300, hue >= 300
    ]
    r = np.select(conditions, [chroma, x, zero, zero, x, chroma])
    g = np.select(conditions, [x, chroma, chroma, x, zero, zero])
    b = np.select(conditions, [zero, zero, x, chroma, chroma, x])
    return np.rint(np.clip(np.dstack((r, g, b)) + m[..., None], 0, 1) * 255.0).astype(np.uint8)


def palette_remap(hero_rgba: np.ndarray, target_hue: float) -> np.ndarray:
    hue, saturation, value = rgb_to_hsv(hero_rgba[:, :, :3])
    delta = (hue - SOURCE_PINK_HUE + 180.0) % 360.0 - 180.0
    # Compress hue variation around the family hue: gel bubbles, sparkles and
    # swirls stay in-family instead of becoming unrelated accent colours.
    remapped_hue = target_hue + delta * 0.22
    output = hero_rgba.copy()
    output[:, :, :3] = hsv_to_rgb(remapped_hue, saturation, value)
    return output


def chrome_derivative(hero_rgba: np.ndarray) -> np.ndarray:
    rgb = hero_rgba[:, :, :3].astype(np.float64) / 255.0
    luminance = rgb @ np.array([0.2126, 0.7152, 0.0722])
    height, width = luminance.shape
    yy, xx = np.mgrid[0:height, 0:width]
    nx = xx / max(1, width - 1)
    ny = yy / max(1, height - 1)

    broad_band = np.exp(-((ny - (0.72 - 0.38 * nx)) ** 2) / (2 * 0.09**2))
    fine_bands = 0.055 * np.sin((ny * 3.2 + nx * 0.45 + luminance * 0.8) * np.pi)
    chrome_value = np.clip(
        0.10 + luminance * 0.96 + broad_band * 0.13 + fine_bands - ny * 0.05,
        0.0,
        1.0,
    )

    stops = np.array([0.0, 0.22, 0.48, 0.68, 0.84, 1.0])
    colours = np.array([
        [30, 42, 60],
        [86, 108, 138],
        [168, 190, 212],
        [245, 250, 255],
        [150, 174, 202],
        [62, 80, 105],
    ], dtype=np.float64)
    chrome = np.empty_like(rgb)
    for channel in range(3):
        chrome[..., channel] = np.interp(chrome_value, stops, colours[:, channel]) / 255.0

    output = hero_rgba.copy()
    output[:, :, :3] = np.rint(chrome * 255.0).astype(np.uint8)
    return output


# Runtime face anchors on the 256x255 master (see drawSlimeFace in
# index.html): eye centres (62,166) and (162,166), eye oval ~15x21; mouth
# centre (109,196), smile width 37. Clean zones are ellipses (cx, cy, rx, ry)
# around those anchors with margin for the strokes, feathered ~12px.
FACE_ZONES = ((62, 166, 26, 24), (162, 166, 26, 24), (109, 196, 32, 20))
FACE_FEATHER_PX = 12.0
FACE_SMOOTH_SIGMA = 5.5


def face_zone_weights(shape: tuple[int, int]) -> np.ndarray:
    """Feathered 0..1 weight map: 1 inside each face zone, smoothstep to 0
    across ~FACE_FEATHER_PX outside it, so the blend has no visible edge."""
    height, width = shape
    yy, xx = np.mgrid[0:height, 0:width]
    weight = np.zeros((height, width), dtype=np.float64)
    for cx, cy, rx, ry in FACE_ZONES:
        d = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
        feather = FACE_FEATHER_PX / ((rx + ry) / 2.0)
        t = np.clip((1.0 + feather - d) / feather, 0.0, 1.0)
        weight = np.maximum(weight, t * t * (3.0 - 2.0 * t))
    return weight


def alpha_weighted_smooth(rgb: np.ndarray, alpha: np.ndarray, sigma: float) -> np.ndarray:
    """Local average of rgb weighted by alpha (transparent pixels contribute
    nothing), used to calm gel detail under the runtime face."""
    a = (alpha.astype(np.float64) / 255.0)[..., None]
    num = ndimage.gaussian_filter(rgb * a, sigma=(sigma, sigma, 0))
    den = ndimage.gaussian_filter(a, sigma=(sigma, sigma, 0))
    return np.divide(num, den, out=rgb.copy(), where=den > 1e-4)


def face_zone_blend(rgba: np.ndarray, old_rgba: np.ndarray) -> np.ndarray:
    """Blend the face zones of the new art toward a smoothed version of
    itself, luminance-matched to the old sprite's face area, feathered so
    no boundary shows. Everything outside the zones is byte-identical."""
    alpha = rgba[:, :, 3]
    weight = face_zone_weights(rgba.shape[:2])
    rgb = rgba[:, :, :3].astype(np.float64)
    smooth = alpha_weighted_smooth(rgb, alpha, FACE_SMOOTH_SIGMA)

    core = (weight >= 0.999) & (alpha > 0)
    gain = 1.0
    if np.any(core):
        lum = np.array([0.2126, 0.7152, 0.0722])
        old_mean = float((old_rgba[:, :, :3].astype(np.float64) @ lum)[core].mean())
        new_mean = float((smooth @ lum)[core].mean())
        if new_mean > 1e-6:
            gain = float(np.clip(old_mean / new_mean, 0.75, 1.35))

    treated = np.clip(smooth * gain, 0.0, 255.0)
    blended = rgb * (1.0 - weight[..., None]) + treated * weight[..., None]
    output = rgba.copy()
    output[:, :, :3] = np.rint(blended).astype(np.uint8)
    output[:, :, 3] = alpha
    output[alpha == 0] = (0, 0, 0, 0)
    return output


def finish_slime(rgba: np.ndarray, current: Image.Image) -> Image.Image:
    current_rgba = np.asarray(current.convert("RGBA"))
    alpha = current_rgba[:, :, 3]
    finished = quantise(rgba, alpha)
    output = np.asarray(finished).copy()
    output[:, :, 3] = alpha
    output[alpha == 0] = (0, 0, 0, 0)
    # Blended clean-face zones (replaces the old byte-for-byte face-band
    # restore, whose hard seams read as a pale slab across the face).
    output = face_zone_blend(output, current_rgba)
    return Image.fromarray(output, mode="RGBA")


def finish_sprite(rgba: np.ndarray, current: Image.Image) -> Image.Image:
    alpha = np.asarray(current.convert("RGBA"))[:, :, 3]
    finished = quantise(rgba, alpha)
    output = np.asarray(finished).copy()
    output[:, :, 3] = alpha
    output[alpha == 0] = (0, 0, 0, 0)
    return Image.fromarray(output, mode="RGBA")


def checkerboard(size: tuple[int, int]) -> Image.Image:
    width, height = size
    board = Image.new("RGBA", size, (54, 57, 66, 255))
    draw = ImageDraw.Draw(board)
    cell = 16
    for y in range(0, height, cell):
        for x in range(0, width, cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(72, 75, 84, 255))
    return board


def contact_sheet(entries: list[tuple[str, Image.Image, Image.Image]], path: Path) -> None:
    label_h = 24
    width = max(before.width + after.width for _, before, after in entries)
    height = sum(max(before.height, after.height) + label_h for _, before, after in entries)
    sheet = Image.new("RGBA", (width, height), (35, 37, 43, 255))
    draw = ImageDraw.Draw(sheet)
    y = 0
    for name, before, after in entries:
        row_h = max(before.height, after.height)
        draw.text((8, y + 5), f"{name}  |  BEFORE  ->  AFTER", fill=(255, 225, 130, 255))
        y += label_h
        for x, image in ((0, before), (before.width, after)):
            tile = checkerboard(image.size)
            tile.alpha_composite(image.convert("RGBA"))
            sheet.alpha_composite(tile, (x, y))
        y += row_h
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(path)


def assert_same_geometry(name: str, before: Image.Image, after: Image.Image) -> None:
    assert before.size == after.size, f"{name}: canvas changed {before.size} -> {after.size}"
    before_alpha = np.asarray(before.convert("RGBA"))[:, :, 3]
    after_alpha = np.asarray(after.convert("RGBA"))[:, :, 3]
    assert np.array_equal(before_alpha, after_alpha), f"{name}: alpha channel changed"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contact-dir", type=Path, default=Path("/tmp/hd2d2-sheets"))
    args = parser.parse_args()

    king_before = md5(KING)
    hero_master = single_subject(latest("media-generation-hero-slime-pink-*.png"))
    building_masters = split_sheet(latest("media-generation-buildings-sheet-*.png"))
    decor_masters = split_sheet(latest("media-generation-decor-sheet-*.png"))

    jobs: dict[str, tuple[Image.Image, Image.Image]] = {}

    current_pink = Image.open(IMG_DIR / "slime-pink.png").convert("RGBA")
    hero_rgba = conform_rgb(current_pink, hero_master)
    jobs["slime-pink.png"] = (current_pink, finish_slime(hero_rgba, current_pink))

    for colour, target_hue in SLIME_TARGETS.items():
        current = Image.open(IMG_DIR / f"slime-{colour}.png").convert("RGBA")
        # Preserve each shipped variant's geometry/alpha, but derive all RGB
        # gel detail from the single conformed hero.
        variant = hero_rgba.copy()
        variant[:, :, 3] = np.asarray(current)[:, :, 3]
        jobs[f"slime-{colour}.png"] = (
            current,
            finish_slime(palette_remap(variant, target_hue), current),
        )

    current_metal = Image.open(IMG_DIR / "slime-metal.png").convert("RGBA")
    metal = hero_rgba.copy()
    metal[:, :, 3] = np.asarray(current_metal)[:, :, 3]
    jobs["slime-metal.png"] = (current_metal, finish_slime(chrome_derivative(metal), current_metal))

    building_names = ["bld-bank.png", "bld-hospital.png", "bld-shop.png"]
    for name, master in zip(building_names, building_masters):
        current = Image.open(IMG_DIR / name).convert("RGBA")
        jobs[name] = (current, finish_sprite(conform_rgb(current, master), current))

    decor_names = ["decor-tree.png", "decor-rock.png", "decor-pond.png"]
    for name, master in zip(decor_names, decor_masters):
        current = Image.open(IMG_DIR / name).convert("RGBA")
        jobs[name] = (current, finish_sprite(conform_rgb(current, master), current))

    for name, (before, after) in jobs.items():
        assert_same_geometry(name, before, after)

    contact_sheet(
        [(name, jobs[f"slime-{name}.png"][0], jobs[f"slime-{name}.png"][1])
         for name in ["pink", *SLIME_TARGETS.keys(), "metal"]],
        args.contact_dir / "slimes-before-after.png",
    )
    contact_sheet(
        [(name, jobs[name][0], jobs[name][1]) for name in building_names],
        args.contact_dir / "buildings-before-after.png",
    )
    contact_sheet(
        [(name, jobs[name][0], jobs[name][1]) for name in decor_names],
        args.contact_dir / "decor-before-after.png",
    )

    for name, (_, after) in jobs.items():
        after.save(IMG_DIR / name)

    king_after = md5(KING)
    assert king_before == king_after == "cb91b0e33d2ecee4c4b34cae0dc13ccc", "king md5 guard failed"

    report = {
        "king_md5": king_after,
        "assertions": {
            name: {
                "size": list(before.size),
                "alpha_identical": True,
                "canvas_unchanged": True,
            }
            for name, (before, _) in jobs.items()
        },
        "contact_sheets": [
            str(args.contact_dir / "slimes-before-after.png"),
            str(args.contact_dir / "buildings-before-after.png"),
            str(args.contact_dir / "decor-before-after.png"),
        ],
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
