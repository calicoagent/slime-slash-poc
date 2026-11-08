#!/usr/bin/env python3
"""Deterministic HD-2D detail pass for Slime Slash sprites.

The pass bakes richer light, rim, specular and material texture into the PNG
assets.  It deliberately preserves every canvas size and every alpha value:
only RGB detail inside the existing silhouette is changed.  The final RGB
image for each sprite is posterised to at most 64 colours with no dithering,
keeping the hard-edged pixel-art read.

slime-king.png is intentionally absent from TARGETS.  Handler has ruled that
asset byte-identical; this script never opens it.
"""

from __future__ import annotations

import argparse
import math
import zlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


REPO_ROOT = Path(__file__).resolve().parents[2]
TAU = math.tau

SLIMES = (
    "slime-blue.png",
    "slime-green.png",
    "slime-metal.png",
    "slime-mint.png",
    "slime-orange.png",
    "slime-pink.png",
    "slime-purple.png",
    "slime-yellow.png",
)
BUILDINGS = ("bld-bank.png", "bld-hospital.png", "bld-shop.png")
DECOR = (
    "decor-grass.png",
    "decor-pond.png",
    "decor-rock.png",
    "decor-tree.png",
    "tile-grass.png",
)
WEAPONS = (
    "dagger.png",
    "great.png",
    "hammer.png",
    "katana.png",
    "pick.png",
    "spear.png",
    "sword.png",
)

TARGETS = (
    *(("img", name) for name in SLIMES),
    *(("img", name) for name in BUILDINGS),
    *(("img", name) for name in DECOR),
    *(("weapons", name) for name in WEAPONS),
)

FACE_BAND = (120, 215)  # Runtime faces are drawn over these slime rows.


def clamp01(values: np.ndarray) -> np.ndarray:
    return np.clip(values, 0.0, 1.0)


def smoothstep(edge0: float, edge1: float, values: np.ndarray) -> np.ndarray:
    t = clamp01((values - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def luminance(rgb: np.ndarray) -> np.ndarray:
    return (
        rgb[..., 0] * 0.2126
        + rgb[..., 1] * 0.7152
        + rgb[..., 2] * 0.0722
    )


def saturation(rgb: np.ndarray) -> np.ndarray:
    peak = np.max(rgb, axis=2)
    valley = np.min(rgb, axis=2)
    return np.divide(
        peak - valley,
        peak,
        out=np.zeros_like(peak),
        where=peak > 1.0e-6,
    )


def blend_to(
    rgb: np.ndarray, colour: tuple[float, float, float], amount: np.ndarray
) -> np.ndarray:
    target = np.array(colour, dtype=np.float64)
    return rgb * (1.0 - amount[..., None]) + target * amount[..., None]


def scale_rgb(rgb: np.ndarray, factor: np.ndarray) -> np.ndarray:
    return rgb * factor[..., None]


def adjust_saturation(rgb: np.ndarray, factor: np.ndarray | float) -> np.ndarray:
    grey = luminance(rgb)[..., None]
    if np.isscalar(factor):
        return clamp01(grey + (rgb - grey) * float(factor))
    return clamp01(grey + (rgb - grey) * factor[..., None])


def hash01(
    x: np.ndarray,
    y: np.ndarray,
    seed: int,
    cell_x: int = 1,
    cell_y: int = 1,
) -> np.ndarray:
    """Stable splitmix-style hash in [0, 1), independent of Python's hash()."""

    xx = (x // cell_x).astype(np.uint64)
    yy = (y // cell_y).astype(np.uint64)
    z = xx * np.uint64(0xA24BAED4963EE407)
    z ^= yy * np.uint64(0x9FB21C651E98DF25)
    z ^= np.uint64(seed + 0x9E3779B97F4A7C15)
    z ^= z >> np.uint64(30)
    z *= np.uint64(0xBF58476D1CE4E5B9)
    z ^= z >> np.uint64(27)
    z *= np.uint64(0x94D049BB133111EB)
    z ^= z >> np.uint64(31)
    return (z >> np.uint64(32)).astype(np.float64) / 4294967296.0


def hash_scalar(number: int, seed: int) -> float:
    z = (number + 1) * 0xA24BAED4963EE407
    z ^= seed + 0x9E3779B97F4A7C15
    z ^= z >> 30
    z = (z * 0xBF58476D1CE4E5B9) & ((1 << 64) - 1)
    z ^= z >> 27
    z = (z * 0x94D049BB133111EB) & ((1 << 64) - 1)
    z ^= z >> 31
    return ((z >> 32) & 0xFFFFFFFF) / 4294967296.0


def erosion_depth(alpha: np.ndarray, max_depth: int = 6) -> np.ndarray:
    """Approximate inward distance from the nonzero-alpha silhouette."""

    visible = (alpha > 0).astype(np.uint8) * 255
    depth = np.zeros(alpha.shape, dtype=np.uint8)
    current = visible
    height, width = alpha.shape

    for step in range(1, max_depth + 1):
        padded = np.zeros((height + 2, width + 2), dtype=np.uint8)
        padded[1:-1, 1:-1] = current
        eroded = Image.fromarray(padded, mode="L").filter(ImageFilter.MinFilter(3))
        current = np.asarray(eroded)[1:-1, 1:-1]
        depth[current > 0] = step
        if not np.any(current):
            break
    return depth


def geometry(alpha: np.ndarray) -> dict[str, np.ndarray]:
    height, width = alpha.shape
    y, x = np.mgrid[0:height, 0:width]
    visible = alpha > 0
    rows = np.where(np.any(visible, axis=1))[0]
    cols = np.where(np.any(visible, axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        raise ValueError("sprite has no visible pixels")

    top, bottom = int(rows[0]), int(rows[-1])
    left, right = int(cols[0]), int(cols[-1])
    nx = (x - left) / max(1, right - left)
    ny = (y - top) / max(1, bottom - top)

    # Pad before blurring so canvas-edge sprites get the same alpha falloff
    # as sprites floating in transparent space.
    mask = visible.astype(np.uint8) * 255
    padded = np.zeros((height + 32, width + 32), dtype=np.uint8)
    padded[16:-16, 16:-16] = mask
    blurred = Image.fromarray(padded, mode="L").filter(ImageFilter.GaussianBlur(0.9))
    alpha_field = np.asarray(blurred)[16:-16, 16:-16].astype(np.float64) / 255.0
    grad_y, grad_x = np.gradient(alpha_field)
    magnitude = np.hypot(grad_x, grad_y)
    # Alpha gradient points inward.  Negating its dot product with the
    # upper-left light direction identifies edges facing that light.
    rim_light = clamp01((0.62 * grad_x + 0.78 * grad_y) / (magnitude + 1.0e-6))
    rim_dark = clamp01((-0.62 * grad_x - 0.78 * grad_y) / (magnitude + 1.0e-6))
    rim_light[magnitude < 0.01] = 0.0
    rim_dark[magnitude < 0.01] = 0.0

    return {
        "alpha": alpha,
        "x": x,
        "y": y,
        "nx": nx,
        "ny": ny,
        "visible": visible,
        "opaque": alpha >= 200,
        "depth": erosion_depth(alpha),
        "rim_light": rim_light,
        "rim_dark": rim_dark,
    }


def tone_and_light(
    rgb: np.ndarray,
    ctx: dict[str, np.ndarray],
    *,
    contrast: float,
    saturation_factor: float,
    top: float = 0.0,
    bottom: float = 0.0,
    left: float = 0.0,
    right: float = 0.0,
    rim_amount: float = 0.0,
) -> np.ndarray:
    lum = luminance(rgb)
    curved = clamp01(lum + 2.0 * contrast * lum * (1.0 - lum) * (lum - 0.5))
    ratio = np.divide(curved, lum, out=np.ones_like(lum), where=lum > 1.0e-4)
    rgb = clamp01(rgb * ratio[..., None])
    rgb = adjust_saturation(rgb, saturation_factor)

    light = (
        1.0
        + top * (1.0 - ctx["ny"])
        + left * (1.0 - ctx["nx"])
        - bottom * ctx["ny"]
        - right * ctx["nx"]
    )
    rgb = clamp01(scale_rgb(rgb, light))

    if rim_amount:
        edge = ctx["depth"] <= 1
        fade = np.where(ctx["depth"] == 0, 1.0, 0.42)
        lit = edge * ctx["rim_light"] * fade * rim_amount
        rgb = blend_to(rgb, (1.0, 0.94, 0.80), clamp01(lit))
        dark = edge * ctx["rim_dark"] * fade * 0.16
        rgb = scale_rgb(rgb, 1.0 - dark)
    return clamp01(rgb)


def add_highpass(
    rgb: np.ndarray,
    ctx: dict[str, np.ndarray],
    *,
    radius: float,
    amount: float,
    minimum_depth: int,
    extra_mask: np.ndarray | None = None,
) -> np.ndarray:
    grey = Image.fromarray(
        np.rint(luminance(rgb) * 255.0).astype(np.uint8), mode="L"
    )
    blurred = np.asarray(grey.filter(ImageFilter.GaussianBlur(radius))).astype(
        np.float64
    ) / 255.0
    detail = luminance(rgb) - blurred
    mask = ctx["opaque"] & (ctx["depth"] >= minimum_depth)
    if extra_mask is not None:
        mask &= extra_mask
    factor = np.where(mask, 1.0 + detail * amount, 1.0)
    return clamp01(scale_rgb(rgb, factor))


def add_cluster_texture(
    rgb: np.ndarray,
    ctx: dict[str, np.ndarray],
    mask: np.ndarray,
    *,
    seed: int,
    amplitude: float,
    cell: int = 4,
) -> np.ndarray:
    coarse = hash01(ctx["x"], ctx["y"], seed, cell, cell)
    fine = hash01(ctx["x"], ctx["y"], seed + 101, max(2, cell // 2), max(2, cell // 2))
    noise = coarse * 0.68 + fine * 0.32
    factor = np.where(mask, 1.0 + (noise - 0.5) * 2.0 * amplitude, 1.0)
    return clamp01(scale_rgb(rgb, factor))


def ellipse_field(
    ctx: dict[str, np.ndarray],
    centre_x: float,
    centre_y: float,
    radius_x: float,
    radius_y: float,
) -> np.ndarray:
    distance = ((ctx["nx"] - centre_x) / radius_x) ** 2 + (
        (ctx["ny"] - centre_y) / radius_y
    ) ** 2
    return clamp01(1.0 - distance)


def stepped(field: np.ndarray, steps: int = 4) -> np.ndarray:
    return np.floor(clamp01(field) * steps) / steps


def clean_texture_mask(
    rgb: np.ndarray, ctx: dict[str, np.ndarray], *, minimum_depth: int = 2
) -> np.ndarray:
    lum = luminance(rgb)
    return (
        ctx["opaque"]
        & (ctx["depth"] >= minimum_depth)
        & (lum >= 0.14)
        & (lum <= 0.90)
    )


def smooth_face_band(rgb: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Regularise the slime face band to smooth shading only.

    Runtime faces are drawn over rows 120-215, so that band must carry no
    speckle, sparkle or dither-like grain.  Replace it with an alpha-weighted
    local average (wide horizontally, narrow vertically): broad gel bands and
    the vertical light falloff survive, per-pixel texture does not.
    """

    height, width = alpha.shape
    y0, y1 = FACE_BAND[0], min(FACE_BAND[1], height - 1)
    if y1 < y0:
        return rgb
    weights = (alpha.astype(np.float64) / 255.0)[..., None]
    stacked = np.concatenate((rgb * weights, weights), axis=2)
    integral = np.zeros((height + 1, width + 1, 4), dtype=np.float64)
    integral[1:, 1:, :] = np.cumsum(np.cumsum(stacked, axis=0), axis=1)

    rows = np.arange(y0, y1 + 1)
    cols = np.arange(width)
    top = np.clip(rows - 3, 0, height)
    bottom = np.clip(rows + 4, 0, height)
    left = np.clip(cols - 12, 0, width)
    right = np.clip(cols + 13, 0, width)
    tt, ll = np.meshgrid(top, left, indexing="ij")
    bb, rr = np.meshgrid(bottom, right, indexing="ij")
    sums = (
        integral[bb, rr]
        - integral[tt, rr]
        - integral[bb, ll]
        + integral[tt, ll]
    )
    weight_sum = sums[..., 3]
    smoothed = np.divide(
        sums[..., :3],
        weight_sum[..., None],
        out=np.zeros_like(sums[..., :3]),
        where=weight_sum[..., None] > 0.05,
    )
    band = rgb[y0 : y1 + 1].copy()
    usable = (alpha[y0 : y1 + 1] > 0) & (weight_sum > 0.05)
    band[usable] = smoothed[usable]
    # Keep the baked specular core crisp: near-white highlight pixels keep
    # their pre-smoothing values instead of melting into the band.
    specular_core = luminance(band) > 0.92
    band[specular_core] = rgb[y0 : y1 + 1][specular_core]
    rgb = rgb.copy()
    rgb[y0 : y1 + 1] = band
    return rgb


def enhance_slime(
    rgb: np.ndarray, ctx: dict[str, np.ndarray], name: str, seed: int
) -> np.ndarray:
    is_metal = name == "slime-metal.png"
    rgb = tone_and_light(
        rgb,
        ctx,
        contrast=0.38 if is_metal else 0.30,
        saturation_factor=0.88 if is_metal else 1.10,
        top=0.13 if is_metal else 0.10,
        bottom=0.16 if is_metal else 0.13,
        left=0.045,
        right=0.035,
        rim_amount=0.38 if is_metal else 0.24,
    )
    rgb = add_highpass(rgb, ctx, radius=2.0, amount=0.10, minimum_depth=3)

    face_band = (ctx["y"] >= FACE_BAND[0]) & (ctx["y"] <= FACE_BAND[1])

    if is_metal:
        # Broad, smooth chrome bands.  In the face band this remains only a
        # luminance wave: no sparkle, speckle or specular is added there.
        phase = ctx["ny"] * 3.6 + 0.18 * np.sin(ctx["nx"] * np.pi)
        band = 0.5 + 0.5 * np.cos(phase * TAU)
        rgb = scale_rgb(rgb, 1.0 + (band - 0.5) * 0.15)

        fraction = phase - np.floor(phase)
        circular_distance = np.minimum(
            np.abs(fraction - 0.24), 1.0 - np.abs(fraction - 0.24)
        )
        strip = 1.0 - smoothstep(0.025, 0.13, circular_distance)
        strip_mask = ctx["visible"] & ~face_band
        rgb = blend_to(rgb, (0.96, 0.99, 1.0), strip * 0.13 * strip_mask)

        fraction2 = phase - np.floor(phase)
        circular_distance2 = np.minimum(
            np.abs(fraction2 - 0.67), 1.0 - np.abs(fraction2 - 0.67)
        )
        strip2 = 1.0 - smoothstep(0.02, 0.10, circular_distance2)
        rgb = blend_to(rgb, (1.0, 1.0, 1.0), strip2 * 0.09 * strip_mask)
    else:
        highlight = stepped(ellipse_field(ctx, 0.28, 0.31, 0.21, 0.125))
        highlight_mask = ctx["visible"] & ~face_band
        rgb = blend_to(rgb, (1.0, 1.0, 1.0), highlight * 0.16 * highlight_mask)

    # Gel belly: a smooth lower-body shade and a very slight saturation lift.
    belly = smoothstep(0.60, 1.0, ctx["ny"])
    rgb = scale_rgb(rgb, 1.0 - 0.12 * belly)
    rgb = adjust_saturation(rgb, 1.0 + 0.035 * belly)

    if not is_metal:
        top_sheen = 1.0 - smoothstep(0.04, 0.38, ctx["ny"])
        rgb = scale_rgb(rgb, 1.0 + 0.045 * top_sheen)

        # Sparse gel sparkles and pores, hard-excluded from the face band.
        texture_mask = clean_texture_mask(rgb, ctx, minimum_depth=3) & ~face_band
        rgb = add_cluster_texture(
            rgb, ctx, texture_mask, seed=seed + 11, amplitude=0.022, cell=3
        )
        sparkle_roll = hash01(ctx["x"], ctx["y"], seed + 23)
        sparkles = texture_mask & (sparkle_roll > 0.9962)
        rgb = blend_to(rgb, (1.0, 1.0, 1.0), sparkles * 0.20)
        pores = texture_mask & (sparkle_roll < 0.0035)
        rgb = scale_rgb(rgb, np.where(pores, 0.94, 1.0))

    # The face band is regularised last among the colour operations so no
    # earlier texture step can leave grain under the runtime-drawn faces.
    rgb = smooth_face_band(rgb, ctx["alpha"])

    # Contact occlusion where the body meets the ground.
    contact = (ctx["depth"] <= 2) & (ctx["ny"] > 0.72)
    rgb = scale_rgb(rgb, np.where(contact, 0.94, 1.0))
    return clamp01(rgb)


def semantic_masks(rgb: np.ndarray) -> dict[str, np.ndarray]:
    red, green, blue = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = luminance(rgb)
    sat = saturation(rgb)
    return {
        "red": red,
        "green": green,
        "blue": blue,
        "lum": lum,
        "sat": sat,
        "brown": (red > 0.18)
        & (red > green * 1.07)
        & (green > blue * 1.02)
        & (lum < 0.76),
        "gold": (red > 0.45)
        & (green > 0.27)
        & (blue < 0.36)
        & (red > blue * 1.40),
        "cream": (red > 0.58)
        & (green > 0.43)
        & (blue > 0.24)
        & (sat < 0.40),
        "green_plant": (green > red * 1.04)
        & (green > blue * 1.02)
        & (green > 0.18),
        "water": (blue > red * 1.13) & (blue > green * 0.92) & (blue > 0.25),
        "metal": (sat < 0.40) & (lum > 0.22) & (lum < 0.98),
        "dark": lum < 0.16,
    }


def enhance_building(
    rgb: np.ndarray,
    source: np.ndarray,
    ctx: dict[str, np.ndarray],
    name: str,
    seed: int,
) -> np.ndarray:
    rgb = tone_and_light(
        rgb,
        ctx,
        contrast=0.25,
        saturation_factor=1.10,
        top=0.07,
        bottom=0.10,
        left=0.03,
        right=0.03,
        rim_amount=0.17,
    )
    rgb = add_highpass(rgb, ctx, radius=2.0, amount=0.13, minimum_depth=3)
    masks = semantic_masks(source)
    x, y, ny = ctx["x"], ctx["y"], ctx["ny"]

    if name == "bld-shop.png":
        awning = ctx["visible"] & (ny < 0.43)
        scallops = 1.0 + 0.025 * np.sin((x / 15.0) * TAU + y / 22.0)
        rgb = scale_rgb(rgb, np.where(awning, scallops, 1.0))
        awning_bottom = awning & (ny > 0.35)
        rgb = scale_rgb(rgb, np.where(awning_bottom, 0.94, 1.0))
    else:
        roof = masks["brown"] & (ny < 0.53)
        shingle_row = (y + ((x // 18) % 2) * 3) // 7
        shingle_factor = np.where(shingle_row % 2 == 0, 1.035, 0.955)
        rgb = scale_rgb(rgb, np.where(roof, shingle_factor, 1.0))
        seams = roof & ((x % 18) < 2) & ((y % 7) != 0)
        rgb = scale_rgb(rgb, np.where(seams, 0.96, 1.0))

    roof_area = masks["brown"] & (ny < 0.53) & (name != "bld-shop.png")
    wood = masks["brown"] & ~roof_area
    rgb = add_cluster_texture(
        rgb, ctx, wood & ctx["opaque"], seed=seed + 31, amplitude=0.055, cell=7
    )
    row_grain = hash01(x, y, seed + 37, cell_x=10000, cell_y=3)
    rgb = scale_rgb(
        rgb,
        np.where(wood, 1.0 + (row_grain - 0.5) * 0.055, 1.0),
    )

    # Very quiet masonry joints and plaster variation on pale walls.
    walls = masks["cream"] & ctx["opaque"] & (ctx["depth"] >= 1)
    rgb = add_cluster_texture(
        rgb, ctx, walls, seed=seed + 41, amplitude=0.018, cell=5
    )
    joints = walls & (((x % 32) < 2) | ((y % 22) < 2))
    rgb = scale_rgb(rgb, np.where(joints, 0.965, 1.0))

    warm_glow = (
        ctx["visible"]
        & (ny > 0.42)  # windows and stall goods only, never signs or coins
        & (masks["red"] > 0.48)
        & (masks["green"] > 0.38)
        & (masks["blue"] < 0.30)
        & (masks["sat"] > 0.20)
    )
    rgb = blend_to(rgb, (1.0, 0.74, 0.28), warm_glow * 0.17)
    rgb = scale_rgb(rgb, np.where(warm_glow, 1.07, 1.0))

    cool_glow = (
        ctx["visible"]
        & (masks["blue"] > 0.36)
        & (masks["blue"] > masks["red"] * 1.07)
        & (masks["green"] > masks["red"])
    )
    rgb = blend_to(rgb, (0.82, 0.91, 1.0), cool_glow * 0.13)
    rgb = blend_to(rgb, (1.0, 0.88, 0.66), cool_glow * 0.045)

    saturated_details = ctx["visible"] & (masks["sat"] > 0.30) & ~masks["dark"]
    rgb = adjust_saturation(
        rgb, np.where(saturated_details, 1.13, 1.0)
    )

    texture_mask = clean_texture_mask(rgb, ctx) & (masks["sat"] < 0.30)
    rgb = add_cluster_texture(
        rgb, ctx, texture_mask, seed=seed + 53, amplitude=0.020, cell=4
    )
    return clamp01(rgb)


def enhance_decor(
    rgb: np.ndarray,
    source: np.ndarray,
    ctx: dict[str, np.ndarray],
    name: str,
    seed: int,
) -> np.ndarray:
    masks = semantic_masks(source)
    x, y, ny = ctx["x"], ctx["y"], ctx["ny"]

    if name == "decor-tree.png":
        rgb = tone_and_light(
            rgb,
            ctx,
            contrast=0.27,
            saturation_factor=1.13,
            top=0.09,
            bottom=0.11,
            left=0.04,
            right=0.035,
            rim_amount=0.20,
        )
        canopy = masks["green_plant"] & ctx["opaque"] & (ny < 0.84)
        rgb = add_cluster_texture(
            rgb, ctx, canopy, seed=seed + 61, amplitude=0.105, cell=7
        )
        rgb = add_cluster_texture(
            rgb, ctx, canopy, seed=seed + 67, amplitude=0.045, cell=3
        )
        cluster = hash01(x, y, seed + 71, 10, 10)
        lit_clusters = canopy & (cluster > 0.70) & (ny < 0.62)
        rgb = blend_to(rgb, (0.88, 1.0, 0.76), lit_clusters * 0.075)
        dark_clusters = canopy & (cluster < 0.29)
        rgb = scale_rgb(rgb, np.where(dark_clusters, 0.93, 1.0))
        lower_canopy = canopy & (ny > 0.58)
        rgb = scale_rgb(
            rgb, 1.0 - 0.075 * smoothstep(0.58, 0.88, ny) * lower_canopy
        )
        trunk = masks["brown"] & (ny >= 0.76)
        rgb = add_cluster_texture(
            rgb, ctx, trunk, seed=seed + 73, amplitude=0.06, cell=3
        )
        return clamp01(rgb)

    if name == "decor-rock.png":
        rgb = tone_and_light(
            rgb,
            ctx,
            contrast=0.30,
            saturation_factor=1.05,
            top=0.08,
            bottom=0.11,
            left=0.04,
            right=0.03,
            rim_amount=0.22,
        )
        rgb = add_highpass(rgb, ctx, radius=3.0, amount=0.22, minimum_depth=2)
        facet_band = np.floor((ctx["nx"] * 0.82 + ny * 1.08) * 5.0).astype(int)
        factors = np.array(
            [0.975 + 0.05 * hash_scalar(band, seed + 83) for band in range(-2, 12)]
        )
        facet_factor = factors[np.clip(facet_band + 2, 0, len(factors) - 1)]
        facet_mask = ctx["visible"] & (masks["lum"] > 0.18) & (masks["lum"] < 0.92)
        rgb = scale_rgb(rgb, np.where(facet_mask, facet_factor, 1.0))
        rgb = add_cluster_texture(
            rgb,
            ctx,
            clean_texture_mask(rgb, ctx, minimum_depth=2),
            seed=seed + 89,
            amplitude=0.026,
            cell=3,
        )
        return clamp01(rgb)

    if name == "decor-pond.png":
        rgb = tone_and_light(
            rgb,
            ctx,
            contrast=0.27,
            saturation_factor=1.13,
            top=0.07,
            bottom=0.09,
            left=0.035,
            right=0.03,
            rim_amount=0.16,
        )
        water = masks["water"] & ctx["visible"]
        centred_x = (ctx["nx"] - 0.50) * 2.0
        centred_y = (ny - 0.48) * 2.0
        radial = np.sqrt(centred_x**2 + centred_y**2)
        rgb = scale_rgb(
            rgb, np.where(water, 1.0 - 0.085 * smoothstep(0.52, 1.05, radial), 1.0)
        )
        sheen = stepped(ellipse_field(ctx, 0.36, 0.33, 0.37, 0.27), 4)
        rgb = blend_to(rgb, (0.86, 0.95, 1.0), sheen * 0.09 * water)

        cell_roll = hash01(x, y, seed + 97, 7, 3)
        dash = (
            water
            & (ctx["depth"] >= 3)
            & (cell_roll > 0.90)
            & ((x % 7) < 3)
            & ((y % 3) == 1)
        )
        rgb = blend_to(rgb, (1.0, 1.0, 1.0), dash * 0.30)

        shore = ctx["visible"] & ~water
        rgb = add_cluster_texture(
            rgb, ctx, shore & ctx["opaque"], seed=seed + 103, amplitude=0.038, cell=3
        )
        rgb = add_cluster_texture(
            rgb,
            ctx,
            clean_texture_mask(rgb, ctx, minimum_depth=3) & water,
            seed=seed + 107,
            amplitude=0.018,
            cell=5,
        )
        return clamp01(rgb)

    if name == "decor-grass.png":
        rgb = tone_and_light(
            rgb,
            ctx,
            contrast=0.28,
            saturation_factor=1.14,
            top=0.09,
            bottom=0.10,
            left=0.03,
            right=0.03,
            rim_amount=0.22,
        )
        green = masks["green_plant"] & ctx["opaque"]
        rgb = add_cluster_texture(
            rgb, ctx, green, seed=seed + 113, amplitude=0.052, cell=3
        )
        tips = green & (ctx["depth"] <= 1) & (ctx["rim_light"] > 0.18)
        rgb = blend_to(rgb, (0.86, 1.0, 0.62), tips * 0.14)
        bases = green & (ny > 0.62)
        rgb = scale_rgb(rgb, np.where(bases, 0.91, 1.0))
        soil = ctx["visible"] & ~masks["green_plant"] & (ny > 0.62)
        rgb = add_cluster_texture(
            rgb, ctx, soil, seed=seed + 127, amplitude=0.045, cell=3
        )
        return clamp01(rgb)

    raise ValueError(f"unhandled decor sprite: {name}")


def enhance_tile(
    rgb: np.ndarray, ctx: dict[str, np.ndarray], seed: int
) -> np.ndarray:
    # A pointwise grade preserves the source tile's seams.  Added detail uses
    # coordinates modulo the 256 px tile, arranged as a 64 x 64 toroidal grid
    # of 4 px cells, so the pattern repeats cleanly at every edge.
    rgb = tone_and_light(rgb, ctx, contrast=0.23, saturation_factor=1.11)
    x, y = ctx["x"], ctx["y"]
    cell_x = (x // 4) % 64
    cell_y = (y // 4) % 64
    cell_roll = hash01(cell_x, cell_y, seed + 131)
    rgb = add_cluster_texture(
        rgb, ctx, ctx["visible"], seed=seed + 137, amplitude=0.020, cell=4
    )

    local_x = x % 4
    local_y = y % 4
    blade_shape = ((local_x == 1) & (local_y >= 1)) | (
        (local_x == 2) & (local_y == 0)
    )
    bright_blades = (cell_roll > 0.875) & blade_shape
    rgb = blend_to(rgb, (0.82, 1.0, 0.58), bright_blades * 0.15)
    dark_specks = (cell_roll < 0.085) & (local_x == 2) & (local_y == 2)
    rgb = scale_rgb(rgb, np.where(dark_specks, 0.94, 1.0))
    return clamp01(rgb)


def enhance_weapon(
    rgb: np.ndarray,
    source: np.ndarray,
    ctx: dict[str, np.ndarray],
    seed: int,
) -> np.ndarray:
    rgb = tone_and_light(
        rgb,
        ctx,
        contrast=0.29,
        saturation_factor=1.09,
        top=0.065,
        bottom=0.085,
        left=0.025,
        right=0.025,
        rim_amount=0.15,
    )
    rgb = add_highpass(rgb, ctx, radius=2.0, amount=0.11, minimum_depth=2)
    masks = semantic_masks(source)
    x, y = ctx["x"], ctx["y"]

    gold = masks["gold"] & ctx["visible"]
    metal = masks["metal"] & ctx["visible"] & ~gold
    wood = masks["brown"] & ctx["visible"] & ~gold

    # Steel gets a top-to-bottom sheen before its explicit cut edge is laid in.
    steel_sheen = 1.0 + 0.105 * (1.0 - ctx["ny"]) - 0.075 * ctx["ny"]
    rgb = scale_rgb(rgb, np.where(metal, steel_sheen, 1.0))

    upper_edge = metal & (ctx["depth"] <= 1) & (ctx["rim_light"] > 0.20)
    edge_amount = np.where(ctx["depth"] == 0, 0.40, 0.22) * ctx["rim_light"]
    rgb = blend_to(rgb, (0.93, 0.98, 1.0), upper_edge * edge_amount)
    inner_edge = metal & (ctx["depth"] == 1) & (ctx["rim_light"] > 0.42)
    rgb = blend_to(rgb, (0.88, 0.95, 1.0), inner_edge * 0.15)
    lower_edge = metal & (ctx["depth"] <= 1) & (ctx["rim_dark"] > 0.25)
    rgb = scale_rgb(rgb, np.where(lower_edge, 0.89, 1.0))

    scratch_mask = (
        metal
        & (ctx["depth"] >= 1)
        & (masks["lum"] > 0.28)
        & (masks["lum"] < 0.92)
    )
    scratch_cells = hash01(x, y, seed + 139, 8, 2)
    bright_scratches = (
        scratch_mask & (scratch_cells > 0.965) & ((x % 8) < 3) & ((y % 2) == 0)
    )
    rgb = blend_to(rgb, (1.0, 1.0, 1.0), bright_scratches * 0.10)
    dark_scratches = scratch_mask & (hash01(x, y, seed + 149) < 0.006)
    rgb = scale_rgb(rgb, np.where(dark_scratches, 0.94, 1.0))

    rgb = adjust_saturation(rgb, np.where(gold, 1.17, 1.0))
    gold_edge = gold & (ctx["depth"] <= 1) & (ctx["rim_light"] > 0.15)
    rgb = blend_to(rgb, (1.0, 0.96, 0.76), gold_edge * 0.24 * ctx["rim_light"])
    gold_specular = stepped(ellipse_field(ctx, 0.46, 0.34, 0.34, 0.30), 4)
    rgb = blend_to(rgb, (1.0, 0.98, 0.84), gold * gold_specular * 0.045)

    rgb = add_cluster_texture(
        rgb, ctx, wood & ctx["opaque"], seed=seed + 151, amplitude=0.065, cell=7
    )
    grain_rows = hash01(x, y, seed + 157, cell_x=10000, cell_y=3)
    rgb = scale_rgb(rgb, np.where(wood, 1.0 + (grain_rows - 0.5) * 0.06, 1.0))

    saturated_parts = ctx["visible"] & (masks["sat"] >= 0.40) & ~gold
    rgb = adjust_saturation(rgb, np.where(saturated_parts, 1.10, 1.0))

    texture_mask = clean_texture_mask(rgb, ctx) & ~metal & ~gold
    rgb = add_cluster_texture(
        rgb, ctx, texture_mask, seed=seed + 163, amplitude=0.020, cell=4
    )
    return clamp01(rgb)


def quantise_to_palette(rgb: np.ndarray, alpha: np.ndarray) -> Image.Image:
    rgb8 = np.rint(clamp01(rgb) * 255.0).astype(np.uint8)
    rgb8[alpha == 0] = 0
    rgb_image = Image.fromarray(rgb8, mode="RGB")
    paletted = rgb_image.quantize(
        colors=64,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    )
    rgba = np.dstack((np.asarray(paletted.convert("RGB")), alpha))
    rgba[alpha == 0] = (0, 0, 0, 0)
    return Image.fromarray(rgba, mode="RGBA")


def visible_rgb_palette_size(image: Image.Image) -> int:
    rgba = np.asarray(image.convert("RGBA"))
    visible = rgba[rgba[..., 3] > 0][:, :3]
    if visible.size == 0:
        return 0
    return int(np.unique(visible, axis=0).shape[0])


def enhance_file(root: Path, folder: str, name: str) -> tuple[str, tuple[int, int], int]:
    path = root / "assets" / folder / name
    with Image.open(path) as opened:
        original = opened.convert("RGBA")
    original_array = np.asarray(original).copy()
    alpha = original_array[..., 3].copy()
    source = original_array[..., :3].astype(np.float64) / 255.0
    rgb = source.copy()
    ctx = geometry(alpha)
    ctx["seed"] = zlib.crc32(name.encode("utf-8"))
    seed = int(ctx["seed"])

    if name in SLIMES:
        rgb = enhance_slime(rgb, ctx, name, seed)
    elif name in BUILDINGS:
        rgb = enhance_building(rgb, source, ctx, name, seed)
    elif name == "tile-grass.png":
        rgb = enhance_tile(rgb, ctx, seed)
    elif name in DECOR:
        rgb = enhance_decor(rgb, source, ctx, name, seed)
    elif name in WEAPONS:
        rgb = enhance_weapon(rgb, source, ctx, seed)
    else:
        raise ValueError(f"no enhancement family for {name}")

    enhanced = quantise_to_palette(rgb, alpha)

    # Internal invariants: a failure here should stop the batch, not ship a
    # sprite that has drifted from its rig, anchors or silhouette.
    result = np.asarray(enhanced)
    if enhanced.size != original.size:
        raise AssertionError(f"{name}: canvas changed from {original.size} to {enhanced.size}")
    if not np.array_equal(result[..., 3], alpha):
        raise AssertionError(f"{name}: alpha channel changed")

    enhanced.save(path)
    return name, enhanced.size, visible_rgb_palette_size(enhanced)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=REPO_ROOT,
        help="repository root (defaults to the root containing this script)",
    )
    parser.add_argument(
        "--only",
        action="append",
        choices=[name for _, name in TARGETS],
        help="enhance only the named sprite (may be repeated)",
    )
    args = parser.parse_args()

    selected = [
        (folder, name)
        for folder, name in TARGETS
        if args.only is None or name in args.only
    ]
    for folder, name in selected:
        sprite, size, palette = enhance_file(args.root, folder, name)
        print(f"{sprite}: {size[0]}x{size[1]}, visible RGB palette={palette}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
