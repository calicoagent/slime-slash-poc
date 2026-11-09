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

---

## 6. GUI — ISW's interface kit → `gui/`

*Prep pass 2026-11-09, for the GUI transplant builder. Everything below is
sourced from the shipped code, not from the debug screenshots — read the
⚠ screenshot caveat before trusting any picture.*

### 6.0 Where ISW's GUI actually lives

ISW's game GUI is **not** image-based. There are no panel PNGs, no 9-slice
frames, no button sprites, and **no bundled font files anywhere in the repo**
(verified: zero `.woff/.ttf/.otf` outside `node_modules`). The whole look is
one CSS kit + a DOM placement layer:

| Layer | Source (in the ISW repo) | What it is |
|---|---|---|
| **The kit** | `packages/isw-ui/` | ~40 DOM components (`panel.ts`, `vitals.ts`, `gauge.ts`, `menubar.ts`, `hotbar.ts`, `minimap.ts`, `npc-balloon.ts`, `speech-balloon.ts`, `thought-bubble.ts`, `shop-window.ts`, `bag-window.ts`, `chat-panel.ts`, `battle.ts`, `defeat.ts`, `skilltree.ts`…) styled by **one 6,917-line stylesheet, `src/ui.css`** — every colour, bevel and shadow below is a token in it. |
| **Placement** | `client-phaser/src/hud/*.css` | Thin per-slot CSS that only *positions* kit components over the Phaser canvas (`hud.css`, `hotbar.css`, `bubble.css`, `quest-tracker.css`, `toast.css`, `bag.css`…). |
| **Page tokens** | `client-phaser/src/style.css` | Page-level `:root` vars (same values as the kit's) + the login/title screen. |
| **Icons** | `packages/isw-ui/src/assets/icons/` (425 PNGs) + `src/sprites.ts` | Cut pixel-art sprites, mapped id → file by `sprites.ts`. Items all draw from one "keys" sheet (`key_000`–`key_099`) so every inventory object is a distinct picture. |
| **In-world text** | Phaser `add.text` (`client-phaser/src/world/actors.ts`, `src/game/world.ts`) | Canvas nameplates/banners — the only canvas-drawn UI; everything else is DOM. |

Copied into `assets/isw/gui/` (byte-identical, md5-verified — see
`gui/checksums.md5`, 447 files, 6.0 MB):

- `gui/icons/` — all **425** kit icon PNGs (pixel art, ~64 px tall, RGBA;
  weapons/armour/items/skills/eggs/UI glyphs; includes the 100 `key_*` item
  icons).
- `gui/assets/` — `eggs/egg_000/001/031/063.png` + `rebirth-egg-blue.png`
  (the only non-icon kit images; window decoration art).
- `gui/cursors/sword.png` — ISW's sword mouse cursor (2,370 B; the same
  file §5 noted in `public/cursors/`).
- `gui/reference/` — 5 screenshots, see §6.6 for what each one really shows.
- `gui/source/` — the spec sources for the builder: `isw-ui-ui.css` (the
  kit stylesheet, complete), `isw-ui-sprites.ts` (icon id table),
  `isw-ui-panel.ts`, `isw-ui-npc-balloon.ts`, `client-style.css`, and the
  client placement CSS (`hud.css`, `hotbar.css`, `bubble.css`,
  `quest-tracker.css`, `toast.css`, `bag.css`).

**Fonts:** nothing to copy. The kit's stack is system fonts only —
`"Noto Sans", "Noto Sans JP", "Noto Sans Thai", "Hiragino Sans", "Thonburi",
sans-serif` — with two deliberate exceptions: **Georgia, serif** for NPC
dialogue text, shop titles and key-cap chips, and **ui-monospace** for coin
counts and numeric chips. `font-synthesis: none`.

### 6.1 The look in one paragraph

ISW's GUI is **dark slate-blue machined metal + one gold chrome reserved
for speech and commerce**. Panels are near-black blue-grey plates with a
1 px near-black edge, an 8 px radius, a lit top edge and a heavy soft drop
shadow; raised controls are bevelled (white 26 % top-left, black 66 %
bottom-right) with a top gloss sweep. Against that cool dark system, every
player-facing *voice* surface — speech balloons, NPC dialogue, the shop,
the hotbar, toasts, quest cards — switches to a warm **gold chrome**
(gradient `#fff4c8 → #e9c46a → #6b4712 → #e9c46a → #b8862b`) on a dark
brown-black `#1f170e`/`#120d07` ground with cream text `#eadfc6`. Slime
Slash today is the inverse temperature: cream parchment panels, thick
brown borders, bright flat chips. **A faithful port is a palette-and-chrome
swap of every surface, not a reskin of the parchment shapes** (see §6.7).

### 6.2 The two chrome systems (tokens, verbatim)

**System A — slate (structure: panels, vitals, minimap, menubar, tabs).**
Defined on `.isw-ui` in `ui.css`:

```
--ink: #101b25        page/void           --text:  #f1f1eb   body text
--surface: #17242f    panel base          --muted: #c5cdd1   secondary text
--edge: #839099       hairlines           --accent:#e3d5b8   cream-gold accent
--accent-ink: #1b252b text on accent      --error: #ffd0c5   --ok: #9be7a9
--isw-surface-top: #2e4356                raised-control top tone
--isw-radius: 8px                         THE radius, every window
--isw-title-strip: linear-gradient(180deg, #3d5a70, #1b2a37 82%)
--isw-inset-body:  linear-gradient(180deg, #111d28, #0b141d 88%)
--isw-frame (the one window shadow, everywhere):
  inset 0 1px 0 rgb(255 255 255 / 18%), inset 0 -2px 0 rgb(0 0 0 / 50%),
  0 18px 40px rgb(0 0 0 / 62%), 0 4px 10px rgb(0 0 0 / 48%)
--isw-bevel-light: inset 2px 2px 0 rgb(255 255 255 / 26%)
--isw-bevel-dark:  inset -2px -2px 0 rgb(0 0 0 / 66%)
--isw-gloss: linear-gradient(180deg, rgb(255 255 255 / 22%), transparent 46%)
--isw-well-floor: linear-gradient(180deg, #201c17, #070c11 58%, #03070b)
--isw-numeral-outline: 1 px #06101a outline on all four sides + soft drop
  (key numbers are weight 800, tabular-nums, and always carry this outline
  so they survive any fill underneath)
```

**System B — gold (voice: balloons, NPC dialogue, shop, hotbar, toasts,
quest tracker, gauge).** Defined per-component (`.isw-ui-say/-chat/-npcsay/
-shopwin`, `.isw-ui-hotbar`, `.isw-ui-gauge`, client `quest-tracker.css`):

```
--gold-hi #fff4c8   --gold #e9c46a   --gold-mid #b8862b   --gold-lo #6b4712
--ink #120d07       --txt #eadfc6    --dim #a89a7c        --line rgb(233 196 106 / .35)
--bub #1f170e       (balloon fill)   --bad #ff7a66        --good #9fe08a
--chrome:   linear-gradient(180deg, #fff4c8, #e9c46a 28%, #6b4712 50%, #e9c46a 72%, #b8862b)
--chrome-d: linear-gradient(160deg, #fff4c8, #e9c46a 35%, #6b4712 60%, #e9c46a 85%, #b8862b)
gauge fills: HP #d8453a→#ff8a70 · MP #3f7fe0→#8cc4ff · hunger #e0962e→#ffd07a
             XP #f3d27a · numerals #fff8e6
quest card: surface #17120c · text #eadfc6 · muted #b3a585 · edge #8a6a2c · good #7fd88a
```

**Type scale** (kit, cut for a 1600×900 stage; Slime Slash runs larger —
keep the *ratios*, not the px): window titles 10 px / body values 9 px /
labels-tags-timers 7 px / countdown numerals 13 px. Panel titles are
uppercase, weight 700, letter-spacing 0.1em. Every tap target is ≥44 px
regardless of glyph size (hit-slop pseudo-elements).

### 6.3 Component anatomy (what to rebuild, exactly)

- **Panel / window** (`panel.ts` + `.isw-ui-panel`): `section` = header bar
  + optional tab strip + body + optional footer. Bar: title-strip gradient,
  padding 7×9 px, holds a 28×25 px **icon socket** (dark inset well,
  `--isw-inset-well`, accent glyph) at left, the uppercase title, and a
  27×24 px **close button** at right (steel gradient `#46607a→#1c2b38`,
  bevelled; **hover turns it red** `#d9776a→#8f2418` with a red glow).
  Body is the inset gradient over base `#16232e`; the whole window wears
  the 1 px `rgb(6 11 16 / 92%)` edge + `--isw-frame`. **Tabs** fuse with
  the body: the active tab's background *is* the body's first tone, its
  bottom border is removed, and a 2 px accent inset line caps it.
- **Buttons, three kinds.** (1) *Menubar tile*: 44×44 px, radius 3 px,
  `--isw-surface-top → #152430`, shared bevel; hover lifts 1 px and tints
  the edge; **active = cream gradient `#f0e3c9→#d8c49b` with dark icon +
  accent glow ring**. (2) *Gold button* `.isw-ui-gbtn` (dialogue choices,
  shop actions): the chrome gradient as background, ink text, weight 800,
  radius 4 px, min-height 32 px; `--ghost` variant = translucent black +
  gold text + gold-mid inset ring; disabled = grayscale(1) brightness(.6);
  may embed a **key-cap chip** (`.isw-ui-gbtn__k`: black chip, gold-hi
  Georgia glyph — this is ISW's key-prompt language). (3) *Panel close*,
  above.
- **Vitals** (`.isw-ui-vitals`): a slate panel holding a **circular
  portrait socket** — 56×56 px, the sprite frame pixelated inside a
  recessed dark well, ringed by the accent colour (`0 0 0 2px --accent`),
  with a **cream level pill overlapping the socket's bottom edge**; beside
  it the name (title tier) and stacked bars (min-width 232 px).
- **Gauge** (`.isw-ui-gauge`, the signature piece): a 128×128 px SVG dial —
  rotating sheen, the player's slime sprite centred, HP/MP/XP arcs in the
  gauge fills, command-point orbs; numerals `#fff8e6`. In the shipped HUD
  this dial *is* the top-left stat cluster (the vitals panel is the
  character-window form of the same data).
- **Hotbar** (`.isw-ui-hotbar`): a row of 46×46 px slots with **no bar
  behind them** — each slot is a dark radial socket (`#2b2217 → #120d08`)
  ringed by the gold chrome painted into a 2 px transparent border
  (border-box chrome / padding-box socket). Empty slots keep the ring at
  70 % opacity. Key number sits outside the slot's corner; the name plate
  pops above the slot.
- **Minimap** (`.isw-ui-minimap`): 254 px slate panel, dark glass gradient,
  a header row (zone name in accent, uppercase, 0.12em tracking + a status
  chip — green `--ok` pill for safe zones), the map canvas below.
- **Quest tracker** (client `quest-tracker.css`, kit-adjacent): a 232 px
  card in the *gold* system — surface `#17120c`, 1 px edge `#8a6a2c`,
  radius 8 px, title + objective lines in cream/muted; the card body is
  one button (opens the quest log), its right 44 px edge is a second
  button (collapse toggle) split by a divider.
- **Toasts** (client `toast.css`, toastify-js reskinned — the library's own
  CSS is never imported): a fixed **top-centre** column, width
  min(420 px, 100vw − 32 px); each toast a dark plate `rgb(14 11 8 / .92)`,
  radius 6 px, ring `0 0 0 1px #000, 0 0 0 2px rgb(233 196 106 / .45)`;
  a sticky/action toast upgrades to the full gold ring. 180 ms in, 400 ms
  fade. Click-through except the toasts themselves.
- **Speech balloon** (`.isw-ui-say`, player chat): zero-size anchor at the
  head; the balloon is dark `#1f170e` with a **2 px gold-chrome border**
  (border-box gradient trick), radius 15 px, black outer ring, tail drawn
  in chrome under the box; text 13 px system-ui, max 3 lines, 188 px max
  width; life is a 4 s pop-in/hold/fade animation.
- **NPC dialogue balloon** (`.isw-ui-npcsay`, the dialogue box): anchored
  at the NPC's head, grows upward: fill `#1f170e` at 95 %, a flat **2 px
  gold ring** (`box-shadow: 0 0 0 2px --gold`) instead of the chrome
  gradient, radius 10 px, gold triangle tail; inside — speaker name in
  gold (800, 12 px, system-ui), the line in **Georgia serif 14 px/1.45**
  cream, then a divider and a row of **choice chips** (gold buttons with
  key-caps). Max width 384 px. (In the client it layers: NPC dialogue
  z 30 over HUD, shop z 31 over dialogue — `client-style.css`.)
- **Thought bubble** (`.isw-ui-thought`): SVG cloud + two dots over an
  actor's head carrying one pixel icon — ISW's ambient status/prompt
  language (wants, refusals, interaction hints), with pop-in/out and a
  2.6 s float loop. This is the closest ISW analogue to a floating
  interact prompt.
- **Shop window** (`.isw-ui-shopwin`, "Ragnarok classic" per its own
  comment): 748×442 px centred window, near-black brown `rgba(14,11,8,.9)`,
  a **triple gold ring** frame (`#000 / gold-lo / gold / gold-lo` box-shadow
  steps) with gold corner brackets; header = shopkeeper mini-portrait in a
  gold-ringed circle + Georgia title + underline tabs (active tab gets a
  gold underline + glow wash) + coin readout right (monospace, coin icon);
  body = two inset panes (stock | cart) with hairline gold dividers,
  zebra rows, selected row = gold wash + 2 px gold left bar; item detail
  strip with a chrome-ringed 52 px icon slot and green/red stat deltas;
  gold buttons to act. Bank/inn in ISW ride the same window family
  (`bag-window.ts`, `vending-window.ts` share the gold tokens).
- **Battle plates** (`.isw-ui-battle`): slate panels; the enemy gets a
  64×64 px inset-well portrait plate + name at title tier; command verbs
  are bevelled slate chips with icon + cost. There is **no boss HP bar**
  in ISW — battles are panel-based, not bar-based.
- **Nameplates** (canvas, `actors.ts` LABEL_STYLE): 12 px, colour
  `#f4f4ee`, **3 px stroke `#101014`**, centred origin above the sprite —
  plain outlined text, no pill or background. Zone banners likewise plain
  canvas text top-left. Combat floaters (miss/damage) are canvas text +
  the `public/fx/combat/digits.png` atlas (§5).
- **Cursor**: `gui/cursors/sword.png` — a small pixel sword; ISW sets it
  as the world cursor (Slime Slash's blade-at-pointer makes this mostly
  a menu/title-screen concern).

### 6.4 HUD layout (the shipped arrangement)

From `ui.css .isw-ui-hud` + client `hud.css` (16 px corner insets
everywhere; the HUD root is click-through except its slots):

- **Top-left column:** the gauge dial (128 px) → effect/buff chips at
  y 188 → the menubar (44 px gold-chrome tiles, vertical) at y 244.
  (Character-window form: the vitals panel sits here instead.)
- **Top-right column:** online count → invite egg (46 px) → **quest
  tracker card under it at top 124 px, right 12 px**; the kit minimap
  belongs to this corner in the HUD spec (kit mock: 254 px panel).
- **Bottom-centre:** the hotbar (12 slots in the client, 46 px each).
- **Bottom-left:** the "Nearby" chat log panel (gold frame family).
- **Bottom-right:** fishing/minigame window slot.
- **Top-centre:** the toast column; zone name is a plain canvas banner.
- **Phone rules** (client `hotbar.css`/`quest-tracker.css`): ≤900 px wide
  or ≤500 px tall, the hotbar **stands up as a right-edge column** showing
  only keys 1–6, and the quest card slides under the top-right row, left
  of the hotbar column. Slime Slash is portrait-first — this rule matters
  more than the desktop one.
- **Layering** is document order, not z-index (only dialogue z 30 / shop
  z 31 / defeat lift break the rule): world canvas → HUD → NPC dialogue →
  shop/windows → account panels; toasts paint over HUD corners but never
  over a modal being answered.

### 6.5 Palette quick reference (sampled from the kit tokens)

| Role | Hex | Role | Hex |
|---|---|---|---|
| Slate ink / void | `#101b25` | Gold hi | `#fff4c8` |
| Panel body base | `#16232e` | Gold | `#e9c46a` |
| Inset body top→foot | `#111d28 → #0b141d` | Gold mid | `#b8862b` |
| Title strip top→foot | `#3d5a70 → #1b2a37` | Gold lo | `#6b4712` |
| Raised control top | `#2e4356` | Cream text (gold sys.) | `#eadfc6` |
| Body text (slate sys.) | `#f1f1eb` | Balloon brown-black | `#1f170e` |
| Muted text | `#c5cdd1` | Ink on gold | `#120d07` |
| Accent cream | `#e3d5b8` | HP / MP fills | `#d8453a` / `#3f7fe0` |
| Hairline edge | `#839099` | XP fill / numerals | `#f3d27a` / `#fff8e6` |
| Near-black edge | `rgb(6 11 16 / 92%)` | Error / OK | `#ffd0c5` / `#9be7a9` |

### 6.6 Reference screenshots (`gui/reference/`) — read this first

⚠ **The `docs/e2e/fishing-webgui/` screenshots are the DEBUG web client**,
a pre-kit diagnostic page (flat dark boxes, monospace, light-grey legacy
windows). They prove *layout and stacking*, never the shipped look. The
shipped look is defined by `gui/source/isw-ui-ui.css` + the design mock
below. Files copied:

| File | What it shows | Trust it for |
|---|---|---|
| `game-screen-preview.png` | The design mock for the Phaser game screen: vitals stack top-left with circular portrait medallions, circular minimap top-right under a zone title, chat panel bottom-left, hotbar + command pips bottom-centre, icon menubar bottom-right — in an ornate gold-trim variant of the chrome | **Composition and corner layout.** Its heavy gold filigree is the mock's flourish; the shipped kit renders the same arrangement in the flatter slate bevel + gold chrome of §6.2. |
| `windows-and-menubar.png` | Debug client with Status/Items/Care windows stacked, right-edge vertical menu (Status/Foes/Items/Skills/Equip/Care), minimap top-right, F-key hotbar bottom-right, chat bottom-left | Window stacking behaviour, right-edge menu placement, hotbar key labels. **Not** colours. |
| `battle-commands.png` | Debug client mid-battle: Commands panel (command points, verb buttons, tamer skills, items) bottom-right | Battle panel *contents* only. |
| `debug-webgui-layout.png` | The debug client's full side-panel layout | Layout archaeology only. |
| `login-card.png` | The page login card (style.css tokens) | The slate page palette on a bare page. |

Not copied (in the source repo if the builder wants them): `hud-mocks/`
(`slime-hud.html` — the gauge/HUD variant mock the kit gauge descends
from; `fishing-bag.html`, `interaction-bubble.html`) and
`client-phaser/src/ui-lab/` (`game-screen`, `shop-npc` lab pages + CSS) —
static mock pages, open them in a browser from the ISW repo for pixel
truth on the kit components.

### 6.7 ISW's GUI vs Slime Slash's — honest assessment

What defines ISW's look, against Slime Slash's current parchment-and-brown
game UI (cream panels, thick brown borders, hard offset shadows, bright
flat chips, pixel display font):

1. **Temperature inverts.** ISW is cool-dark (slate blue-black) with gold
   as a scarce warm accent; Slime Slash is warm-light (cream/brown) with
   colour everywhere. Nothing in ISW is parchment, and nothing is
   light-surfaced except the active menubar tile and the level pill —
   both read as *lit* because everything around them is dark.
2. **Edges are machined, not drawn.** ISW's borders are 1 px near-black +
   layered inset light/shadow (bevels, gloss, well shadows) — the "frame"
   is light behaviour, not a thick outline. Slime Slash's chunky brown
   outlines and offset shadows have no counterpart; keeping them under
   ISW colours would not read as ISW.
3. **Two chromes, assigned by meaning.** Slate = structure (windows,
   vitals, minimap, menus); gold = voice (speech, dialogue, shop, quest,
   toasts, hotbar). Slime Slash currently uses one parchment treatment
   for everything, so the port is also an *assignment* exercise (§6.8).
4. **Icons are art, text is quiet.** ISW spends its visual budget on the
   425 cut pixel icons and the gauge medallion; its type is small,
   uppercase-tracked, system sans (serif only where an NPC "speaks").
   Slime Slash's big pixel-font titles are a different voice — the port
   keeps game-feel through icons, the dial and the chrome, not type size.
5. **The world stays uncovered.** ISW's HUD is four corner clusters +
   bottom-centre bar over a vignetted world (`--isw-hud__atmosphere`:
   radial + linear dark falloff at the edges "so the world holds the
   HUD"). Panels open centred and modal-ish; nothing docks full-height.

**What a faithful port must therefore change in Slime Slash:**
(a) DOM/CSS HUD: adopt the kit tokens wholesale (both systems), rebuild
every panel on the panel anatomy (title strip + icon socket + red-hover
close + fused tabs), restyle the rack/hotbar as chrome-ring sockets, the
quest card as the gold tracker card, toasts as the top-centre dark-plate
column, menus as slate panels with gold where they "speak".
(b) Canvas-drawn elements: nameplates → ISW's plain outlined text
(12 px, `#f4f4ee`, 3 px `#101014` stroke — close to current, drop any
pill backing); dialogue → the npcsay balloon anatomy (DOM, gold ring,
Georgia line, gold choice chips with key-caps) replacing the parchment
comic bubble; interact prompts → gold key-cap chips / thought-bubble
language instead of the wide yellow bar; boss bar → no ISW analogue,
build it as a battle enemy plate (inset portrait socket + slate panel +
gauge-fill bar) — see flags in §6.8.
(c) The title screen: ISW's is full-bleed art + a left-side slate login
card over a darkened atmosphere gradient; Slime Slash's frozen diorama
stays, but its furniture (logo plate, name field, PLAY) should sit in a
slate panel with a gold primary button, not parchment.
(d) Scale discipline: the kit's px sizes assume a 1600×900 stage and
44 px targets; Slime Slash is portrait-phone-first — scale the kit up
(the client’s own phone rules in §6.4 are the precedent), keep ratios.

### 6.8 Surface mapping — Slime Slash surface → ISW element

| Slime Slash surface | Adopt | Notes / flags |
|---|---|---|
| Title screen | Page/title treatment (`client-style.css`): full-bleed art, dark atmosphere gradient, slate panel furniture; PLAY = gold `.isw-ui-gbtn` | Keep Slime Slash's frozen-diorama backdrop (Handler ruling); only the furniture changes chrome. |
| HUD stat panel (HP/MP/XP, level, coins) | `.isw-ui-vitals` panel, or the `.isw-ui-gauge` dial as the cluster | Dial is the signature; vitals panel is the safer portrait fit. Bars take gauge fills; numbers get the numeral outline. |
| Peer badge / connection state | Minimap header status chip (`.isw-ui-minimap__chip`) pattern | ⚠ No direct analogue — ISW shows an online *count* top-right; reuse the chip styling for the peer count/state. |
| Quest card | Quest tracker card (gold system, `quest-tracker.css`) | Near 1:1: title + objective, body opens log, right-edge collapse toggle. |
| Interact prompt ("E — …") | `.isw-ui-gbtn__k` key-cap chip + label; ambient hints → `.isw-ui-thought` bubble | The wide yellow bar dies; prompt = dark chip, gold key-cap, cream text, anchored per current prompt rules. |
| Weapon rack | `.isw-ui-hotbar` chrome-ring sockets in a slate tray (panel anatomy) | Weapon icons already exist as game art; selected weapon = active-tile cream treatment from the menubar. |
| Skill button | Hotbar slot + menubar active tile language | Cooldown numeral = kit countdown tier (13 px) over the socket. |
| Main menu + tabs (INVENTORY/SPHERE/GEMS/STORY/MAP/MORE) | `.isw-ui-panel` with fused tab strip | Tabs already exist in both games; ISW's active-tab fusion + accent cap is the tell. |
| SPHERE tab (Sphere Grid) | Kit `skilltree.ts` component family | ISW has a real skill-tree UI — closest analogue in the whole port; mine it for node/link styling. |
| Shop panel | `.isw-ui-shopwin` (gold triple-ring window) | Direct port: stock/cart panes map to buy list + owned; coin readout, detail strip, gold buttons all transfer. |
| Bank panel | Shop-window family (`bag-window`/`vending-window` gold tokens) | ⚠ No bank in ISW; the gold window family is the assigned chrome (it is a "speaking" commerce surface). |
| Inn panel | NPC dialogue balloon → choice chips (`.isw-ui-npcsay`) | ISW rests are NPC interactions, not windows: SLEEP / SLEEP & SAVE become dialogue choice chips at the innkeeper. |
| Dialogue bubbles | `.isw-ui-npcsay` balloon (DOM) | Replaces the canvas comic bubble: gold ring, Georgia line, name in gold, choices as gold chips. Typewriter pacing is Slime Slash's to keep. |
| Toasts | Client toast system (`toast.css`): top-centre dark plates, gold ring for action toasts | Replaces the Sonner stack styling; stacking/queue logic may stay. |
| Pause menu | Slate `.isw-ui-panel`, centred; game-menu pattern (client `hud.css` game menu: gold-chrome buttons on dark plate) | Segmented settings rows come from the game menu. |
| Chapter cards | ⚠ **No ISW analogue** | ISW has no full-screen story cards (its banners are plain canvas text). Keep the card format; dress it in slate panel + Georgia serif line + gold rule so it belongs to the family. |
| Boss bar | ⚠ **No ISW analogue** (no boss HP bar exists) | Build from battle parts: `.isw-ui-battle__enemy` plate (inset portrait socket) + slate panel + gauge HP fill; keep Slime Slash's top placement and Emperor-only toast rule. |
| Minimap + frame | `.isw-ui-minimap` panel (slate, zone header + status chip) | Zone-name header maps to the current zone/graph node; the MAP tab becomes a slate panel holding the zone graph. |
| Nameplates (NPC/peer/slime tags) | Canvas LABEL_STYLE: 12 px `#f4f4ee`, 3 px `#101014` stroke, no backing | Canvas-side change only; ELITE/boss tags take gold text as the accent exception. |
| Damage/heal floaters | Canvas text + ISW digits atlas (`public/fx/combat/digits.png`, §5 — not copied) | Optional; copy the atlas on demand if the builder wants ISW's numerals. |
| Cursor | `gui/cursors/sword.png` | Menus/title; in-world the blade is the cursor already. |
| Item/gem/ore icons in menus | Kit icon set (`gui/icons/`, id table in `gui/source/isw-ui-sprites.ts`) | Supplements Slime Slash's own generated icon set (§ items work); ISW's `key_*` sheet is the "every object distinct" precedent. |

*End of §6. The kit stylesheet in `gui/source/isw-ui-ui.css` is the
authority for every value above; where this section and the CSS disagree,
the CSS wins.*
