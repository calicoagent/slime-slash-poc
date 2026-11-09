# ISW Transplant — Asset Manifest

Everything below was copied **byte-identical** (md5-verified against source) from
Handler's Isekai Slime World (`~/workspace/isekai-slime-world-ref/client-phaser/public/`)
on 2026-11-09. Source repo untouched. Total copied: ~58 MB.
Reference sheets: `contact-plates.png` (all plates), `contact-npcs.png` (all 18 NPC front frames).

Key geometry contract (from ISW `docs/maps/ALPHA-FIELDS.md` + `src/world/plates.ts`):
the world is a **2:1 diamond isometric** grid — one cell is **96×48 px** on screen
(`TILE_WIDTH=96`, `TILE_HEIGHT=48`). A plate is a single painted image whose terrain
diamond is 2:1, top corner touching the image top; the client scales the plate so one
painted cell = 96×48. Plate placement formula (`platePlacement` in `plates.ts`):
`tw = plateW * 2 / (zoneW + zoneH)`, `th = min(tw/2, plateH * 2 / (zoneW + zoneH))`,
`scale = 96 / tw`, cell (0,0) centre sits at plate pixel `(zoneH * tw/2, th/2)`.
Every ISW zone below is **24×24 cells** unless noted. Painted margin around the
diamond (forest, cliffs, backdrop) is part of the plate and is left as painted.

---

## 1. Plates → `plates/`

All plates are **complete painted ground scenes** in the isometric presentation
(diamond terrain + painted environment border: surrounding forest, cliff skirts,
backdrop) — not tileable textures, and not the flat editor previews in
`docs/maps/*.flat.png` (those are 640×640 renders; the production files below are
distinct, higher-resolution paintings of the same maps).

| File | Pixels | KB | Zone | Reads as |
|---|---|---|---|---|
| `alderwake.png` | 1536×864 | 2609 | **Alderwake — the town** (`town: true`) | Stone-walled town ground: cobble crossroads, the Wake stream running through under arched stone bridges, spring pond. Buildings are props, not painted here. Town grown around a living Alder Bell tree. |
| `alderwake.water.png` | 1536×864 | 23 | Alderwake water mask | RGBA **alpha mask** (white RGB, feathered alpha, 1.6% coverage) tracing the painted stream/pond shoreline — used by the water effect (§4), not a picture. |
| `alderwake_approach.png` | 1536×864 | 2395 | Alderwake Approach | Grass field with dirt track and cobble apron — the field before the town's west wall/gate. Pairs only with Alderwake. |
| `landing_glade.png` | 1740×904 | 2388 | Landing Glade (Alpha start) | Meadow clearing, pond at NW, glowing blue spawn circle on the grass, dirt path leaving SE. |
| `landing_glade.water.png` | 1740×904 | 35 | Landing Glade water mask | RGBA alpha mask (white RGB, feathered, 2.9% coverage) over the pond. |
| `forest_path_1.png` | 1536×864 | 2319 | Forest Path 1 | Grass plateau, single winding dirt path (the L1–2 chain, part 1). |
| `forest_path_2.png` | 1536×864 | 2361 | Forest Path 2 | Stream crossing: river runs full height, 3-cell plank bridge, waterfall over the south cliff lip. |
| `forest_path_3.png` | 1536×864 | 2423 | Forest Path 3 | Path junction in deep forest, small violet pond nook at E edge. Grand Rabbit guards this map in ISW. |
| `lakeside_camp.png` | 1536×864 | 2351 | Lakeside Camp | Big lake filling the middle (sandy shore), camp clearing + fire pit SW of the lake, path in from S. Home of the camp NPCs (§3). |
| `southwest_grove.png` | 1672×941 | 2192 | Southwest Grove | Sunlit grove, violet stone ritual circle on the grass, crossing dirt tracks. |
| `redbracken_hollow.png` | 1536×864 | 2335 | Redbracken Hollow (draft zone) | Autumn hollow: orange bracken, a patch of red growth around a stone, crossroads. |
| `witherbriar_moor.png` | 1536×864 | 2425 | Witherbriar Moor (draft zone) | Bleak moor, dead trees, mist, one small dark pond. |
| `brimstone_verge.png` | 1536×864 | 2275 | Brimstone Verge (draft zone) | Volcanic verge: scorched earth, lava-glow cracks, steaming turquoise pool at N. |
| `cinderfell.png` | 1536×864 | 2201 | Cinderfell (draft zone) | Ash-grey waste, a chasm cut at SW, glowing ember patch. |

**`town_of_beginning` has NO production plate.** It is ISW's 48×48 first town in
content/docs (renders: `docs/maps/town_of_beginning.flat.png` / `.iso.png`), but no
`town_of_beginning.png` exists in `public/plates/` — in the shipped client the town
function is served by **Alderwake**. Several NPC sheets are named for its NPCs
(the `hollow_*` set, §3) even though their plate never shipped.

Plate aspect: 1536×864 = 16:9 for ten plates; `landing_glade` 1740×904 ≈ 1.92:1;
`southwest_grove` 1672×941 ≈ 1.78:1. In every case the **terrain diamond inside is 2:1**.

---

## 2. Music + SFX → `media/`, `sfx/`

### Music (MP3, copied in `media/`)

| File | Duration | KB | Loopability |
|---|---|---|---|
| `title-theme.mp3` | 2:11 (130.99 s) | 4093 | Title theme; composed track, loop it whole or play once on the title screen. |
| `field-landing-glade.mp3` | 4:00 (240.02 s) | 7500 | Field BGM for Landing Glade in ISW — an authored zone loop (played looped in-game); the round 4:00 length is a loop-cut. |
| `field-lakeside-camp.mp3` | 4:00 (240.02 s) | 7502 | Field BGM for Lakeside Camp — same authored-loop treatment. |

That is the entire ISW music set: **one title theme + two field tracks** (no boss track
exists). Also copied from `media/` (not audio): `title-screen-1.mp4` (20.0 s) and
`title-screen-2.mp4` (10.0 s) — animated title backdrops; `loading-loop.mp4`/`.webm`
(6.7 s); `title.png`, `title-poster.jpg`, `og-card.png`, `discord-blurple.svg`.

### SFX (MP3, copied in `sfx/`)

| File | Duration | KB | Use in ISW |
|---|---|---|---|
| `hit.mp3` | 0.45 s | 4 | Combat hit |
| `miss.mp3` | 0.55 s | 6 | Combat miss |
| `critical-hit.mp3` | 2.14 s | 13 | Critical hit |
| `combat-defeat.mp3` | 3.00 s | 26 | Combat defeat |
| `level-up.mp3` | 2.06 s | 45 | Level up fanfare |
| `shop-buy-sell.mp3` | 1.49 s | 26 | Shop buy/sell |
| `tick.mp3` | 0.96 s | 8 | UI tick |

Also copied for the water effect: `fx/caustics.png` (256×256 tileable Worley caustics
texture, §4).

---

## 3. NPC sprites → `npcs/`

All 18 files are **spritesheets, 288×768 px, RGBA**, one per NPC, in the ISW "tamer
convention" (`src/world/npcSheets.ts`, `src/world/sprites.ts`):

- **Grid: 3 columns × 8 rows of 96×96 px frames** (24 frames).
- **Row order (top→bottom) is facing: N, NW, E, SE, S, SW, W, NE.** Row 4 = S = front.
- **Column 0 = stand pose**; columns 1–2 are the two walk steps (cycle 0‑1‑0‑2).
- **Front-facing idle = frame index 12** (row 4 × 3 + col 0), crop `(0, 384, 96, 96)`.
- Feet sit on pixel row 89 of the frame (origin Y ≈ 89/96 ≈ 0.927); the standing
  figure actually occupies ~76 px of the 96 px frame height.
- All are **human** chibi pixel characters (Slime Slash's NPCs are animal folk;
  names, dialogue and roles stay Slime Slash's — these are body/appearance swaps).
  `contact-npcs.png` shows frame 12 of every sheet.

| Sheet | ISW identity (content/npcs.json) | Appearance (front frame) |
|---|---|---|
| `hollow_lorekeeper` | Old Renn — lorekeeper, Town of Beginning | Bald elder, long white beard, blue robe, holding a staff. The classic sage. |
| `camp_lorekeeper` | Old Garrow — lorekeeper, Lakeside Camp | Bald old man, grey side-hair, stern, green cloak, arms crossed. |
| `meadow_lorekeeper` | Wren of the Long Grass — lorekeeper, Meadow | Young blonde in a hooded green cloak, holding a vine-wrapped staff. |
| `camp_smith` | Smith Brannoc — smith (shop), Lakeside Camp | Big bald bearded man, headband, anvil emblem on his shirt, work apron. Unmistakably the smith. |
| `hollow_trainer` | Bran — trainer (gym), Town of Beginning | Bald muscular man, red headband, red martial-arts gi. Fighter/guard energy. |
| `barrows_trainer` | Kesh — trainer, Stone Barrows | Stern older woman, topknot, pauldrons, arms crossed. |
| `meadow_trainer` | Odile — trainer, Meadow | Blonde ponytailed girl, yellow top and shorts. Youngest-looking sheet. |
| `wake_trainer` | Wren — trainer, Alderwake | Young brown-haired fighter, green vest and sash. |
| `swamp_trainer` | Marsh — trainer, Swamp | Conical straw hat, green wraps — a field/ranger fighter. |
| `deeps_trainer` | Ordal — trainer, Mire Deeps | Long grey hair and beard, dark robe, bandaged arm. Recluse look. |
| `hollow_merchant` | Peddler Miri — shop, Town of Beginning | Young woman, orange headscarf, apron over a green dress. Shopkeeper. |
| `camp_merchant` | Pedlar Hobb — shop, Lakeside Camp | Red beanie, beard, heavy coat and satchel. Travelling pedlar. |
| `meadow_merchant` | Cartwright Odo — shop, Meadow | Flat cap, moustache, vest and shirt. |
| `barrows_merchant` | Quarry-Wife Sella — shop, Stone Barrows | Grey-haired older woman in brown work apron/overalls. |
| `swamp_merchant` | Fenwick the Waterlogged — shop, Swamp | Wide blue rain hat and raincoat. |
| `deeps_merchant` | Lantern-Keeper Ilva — shop, Mire Deeps | Hooded purple robe, white hair, **holding a lit lantern**. |
| `hollow_stable` | Keeper Bex — stable, Town of Beginning | Straw hat, red hair, apron, holding a lead rope. Keeper of a rest house. |
| `town_ticket_post` | Training Ticket Post — a **prop, not a person** | Wooden ticket post with a bell on top and a glowing ticket slot. |

### Proposed mapping onto Slime Slash's 8 roles

| Slime Slash role | ISW sheet | Why |
|---|---|---|
| **Elder Mirra** (lorekeeper) | `hollow_lorekeeper` (Old Renn) | The one true elder-sage: white beard, robe, staff. Carries prophecy/briefings visually. Alt: `camp_lorekeeper` (sterner, staff-less). |
| **Forge** (smith) | `camp_smith` (Brannoc) | Only smith in the set; anvil emblem, apron, forge build. Exact match. |
| **Warden Pike** (guard / trainer type) | `hollow_trainer` (Bran) | Martial trainer with a guard-captain stance. Alt: `barrows_trainer` (pauldrons, arms crossed). |
| **Tansy** (shopkeep, Thornwick shop) | `hollow_merchant` (Miri) | Aproned shopkeeper, warmest merchant read. |
| **Bramble** (innkeeper, Thornwick inn) | `hollow_stable` (Keeper Bex) | A "keeper" of lodgings-by-another-name: hat, apron, host energy. Alt: `barrows_merchant`. |
| **Scout Vex** (scout, Rotwatch) | `swamp_trainer` (Marsh) | Conical hat + field wraps read as a ranger/scout on patrol. Alt: `camp_merchant` (travelling pedlar with pack). |
| **The Hermit** (shore hermit) | `deeps_trainer` (Ordal) | Grey-bearded robed recluse. Alt: `deeps_merchant` (Ilva — hooded, lantern-lit, very hermit-mood). |
| **Child** | **⚠ NO GOOD MATCH** | All 18 sheets are adults. Least-bad is `meadow_trainer` (Odile — young, small, cheerful), but she reads as a young teen trainer, not a child. Flagged: either accept Odile as an older "Child", keep Slime Slash's current mouse-child sprite for this one role, or commission a new sheet. |

Unused sheets after this mapping: `camp_lorekeeper`, `meadow_lorekeeper`,
`camp_merchant`, `meadow_merchant`, `barrows_merchant`, `barrows_trainer`,
`swamp_merchant`, `wake_trainer`, `deeps_merchant` (alt-Hermit), and
`town_ticket_post` (a prop — usable as bank/ticket signage dressing, not a person).

---

## 4. Water — how ISW does it (for the canvas reimplementation)

Source: `client-phaser/src/world/atmosphere/shimmer.ts` + `caustics.ts` +
`src/protocol/Water.ts`. There is **no shader and no animated water tiles**: the water
surface is already painted in the plate; the effect is **light on top of the painting**,
in three layers, all clipped to the water region. Water region = terrain cells marked
`'w'` (flowing) or `'~'` (still) in the zone data — the mask is the union of those
cells' flat 2:1 diamonds, **or**, where one exists, the plate's soft alpha mask
(`plates/<zone>.water.png` — only Alderwake and Landing Glade have one; feathered
shoreline, use it when present, diamond-union otherwise).

**Layer 1 — highlight sheet (shimmer.ts).** A 256×256 soft-noise texture (48 blurred
white blobs, alpha 0.06–0.16, hash-seeded so it's identical every load) tiled over the
whole zone, blend **ADD**, tinted with the water tint (default `#cfe9ff`), at alpha
0.08–0.15 scaled by the zone's `sparkle` (0–1). It **drifts**: 14 px/s × `speed`
(default 0.5, range 0–2) on X, half that on Y, so it slides rather than travelling
along the projection diagonal. Canvas equivalent: an offscreen 256 tile, drawn
tiled with `globalCompositeOperation='lighter'`, offset by `(t*14*speed, t*7*speed)`,
clipped to the water mask.

**Layer 2 — sparkles (shimmer.ts).** Up to **60 additive glints** alive at once: 2–3 px
soft white dots (a 3 px radial dot texture), tint = water tint, alpha peaking 0.95
with a fade-in/fade-out over a **700–1600 ms** life, no motion — a glint appears,
brightens, dies. Birth position is **uniform inside a random water cell's diamond**
(affine map of the unit square: `x = cx + (u+v−1)*48`, `y = cy + (u−v)*24` for a
96×48 cell). `sparkle` scales the *rate* (calm pond = few glints), never the
brightness. Canvas equivalent: a small particle pool with the same numbers.

**Layer 3 — caustics (caustics.ts, STILL water `'~'` only).** Two layers of one
256×256 **tileable Worley-noise texture** (`fx/caustics.png` — copied to `fx/`),
each tiled, additive, scrolled **along the isometric axes** (not screen axes) at
different scales, speeds and directions (base scroll ≈ 12 px/s at speed 1). Two
interfering layers are what make it read as caustics instead of scrolling wallpaper.
Flowing water gets layers 1–2 only.

**Depth/occlusion:** both shimmer layers sit just above the ground plate
(depth ground+2 sheet, ground+3 sparkles) and **below actors and props** — a tree
between camera and pond occludes the glints on it. In canvas: draw water FX right
after the plate, before entities, inside the mask clip.

**Per-zone authoring (`Water` in zones.json):** `sparkle` 0.55–0.75 on the shipped
zones, `speed` 0.4–0.6, tints `#cfe9ff` / `#bfe0f2`. `sparkle: 0` = off, and off
means the module builds nothing at all.

**Assets the transplant needs for water:** the two `.water.png` masks (in `plates/`),
`fx/caustics.png` (copied), plus two tiny procedural textures it can generate at
runtime exactly as ISW does (3 px sparkle dot; 256 px blob-noise sheet).

---

## 5. Props & other sprites (inventoried, NOT copied)

- **`public/props/props.png` + `props.json`** — the shared prop atlas: a single
  640×4555 RGBA sheet (3.9 MB) with **54 named frames** in TexturePacker-style JSON
  (normalised anchors, recommended tile width 96): trees (`tree-oak`, `tree-wide`,
  `tree-young`, `tree-split`), bushes, rocks (`rock-standing`, `rock-mossy`),
  `stone-rune`, `lamp-wood`, `signpost`, `log-fallen`, buildings for Alderwake, etc.
  ⚠ A per-zone prop set also exists in the source repo at `assets/map-props/`
  (e.g. `alderwake/buildings.png`, `town-walls.png`, `small.png`) — Handler's earlier
  port (`tools/isw/port_env.py`) drew from this family. Neither was copied in this
  pass; copy on demand when the transplant places props.
- **`public/sprites/` (non-NPC)** — 16 monster spritesheets, all 1120 px wide
  (280×280 frames, 4 cols × 6–8 rows): `bramble_boar`, `briarback_tortoise`,
  `dust_mite`, `ember_wisp`, `gloom_moth`, `grand_rabbit`, `heather_adder`,
  `hollow_owl`, `kindle_bat`, `meadow_hopper`, `mossfang_wolf`, `peat_toad`,
  `puffbun`, `scald_beetle`, `sulphur_ram`, `thicket_sprout`, `bracken_heap`;
  the player **tamer** sheets in the same 288×768 / 3×8 convention (`tamer.png`,
  `tamer_sit.png`, `tamer_fish.png` at 336×896); and `vending_machine_128.png`
  (128×128 single image — the sprite the ticket post's sibling NPC uses).
- **`public/assets/slimes/`** — 6 cat-slime variant folders (BabyBlueCatSlime,
  BlackCatSlime, BrownCatSlime, DemonicCatSlime, Rainbow, WhiteCatSlime) — ISW's
  slime art lives here, not in `sprites/`.
- **`public/fx/`** — `caustics.png` (copied, §4) and `combat/` (`crit-bursts.png`,
  `digits.png` + `digits.json` — floating damage digits atlas; relevant if the
  transplant wants ISW's damage numbers too).
- **`public/cursors/sword.png`** — ISW's sword cursor. Noted; not copied.

---

*Checksums: md5 of every copied file was compared against its source after copying —
all identical. The `.water.png` masks and `fx/caustics.png` included.*
