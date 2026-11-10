# BASICS GATE — the pre-ship visual basics check

Handler, 2026-11-10: *"Shadow broken. Trees don't need shadow. Tree shouldn't be on the road. These I should not have to tell you. Create a system so I don't have to."*

This gate is that system. It boots the real game, plays it to the places
where basics break, measures the basics with numbers, and refuses to
call the build good until every one of them passes.

## THE SHIP RULE

**No build is pushed or reported to Handler without a green gate run.**
A red gate means the build does not ship — the defect gets fixed in the
game, never argued around in the gate. On top of the automated run, the
main agent reads the run's `contact-sheet.png` personally, by eye,
before reporting: the sheet is the portrait/desktop battery (title,
altar rest, sword crop, crowd, town, grove), and the eye pass covers
what numbers can't — ground reading as a finished, textured place
rather than flat discs, scale reading right, nothing looking pasted-on.

## The rules (Handler's terms, accumulated from his corrections)

a. **The sword is VISIBLE** — at rest and in motion, at phone and
   desktop sizes. (v0.6.0–v0.6.4 shipped a sword that rendered
   zero-length for five versions while probes said it was fine.)
b. **Trees cast NO shadow.** Other shadows sit anchored at their
   object's base, never detached. (Handler, 2026-11-10: tree shadows
   removed entirely — do not re-add them.)
c. **No game-placed prop stands on a road/path or in water.** Props
   belong on natural ground. Story-fixed set pieces are exempt and
   reported, not failed.
d. **Name plates and ELITE tags render fully on-screen** — never
   clipped by the frame edge. (The cut-off METAL tag was the original
   complaint.)
e. **HUD clusters never overlap or clip at 390×844.** Anything not
   needed during a fight lives in the menu or in toasts, not on the HUD.
f. **In a full musou crowd the ground stays visible** — no carpet of
   slimes wall-to-wall. (The v0.6.0 transplant failure.)
g. **Scale sanity:** slimes vs NPCs vs trees read correctly at the
   current zoom — covered by the sword/crowd numbers plus the
   contact-sheet eye pass.
h. **The title screen is a static picture** — composed art, inert
   input until PLAY. The world must not run behind the menu.
i. **Zero page errors. Always.**

## How to run

```
node tools/basics-gate/run.cjs        # from the repo root, ~90 seconds
```

- Boots the game fresh-save (localStorage save wiped) at PORTRAIT
  390×844 (DSF 2) and DESKTOP 1920×1080, stubbed-import Playwright,
  hermetic TMPDIR under the output dir (the pattern from the gauntlet
  harnesses — Chromium never touches the small `/tmp` tmpfs).
- Battery per viewport: title → PLAY → altar clearing at rest (sword
  probe + sword crop) → glade crowd walked in (+ a fully-converged
  "dense" crowd sample) → town (+ NPC proximity plates) → grove, two
  viewpoints.
- Writes `report.json` (per-check PASS/FAIL + every measured value),
  the full frame battery, and `contact-sheet.png` to
  `~/workspace/gauntlet-archive/basics-gate/<timestamp>/`.
- Prints one line per check. **Exit 0 = GREEN, 1 = RED, 2 = harness
  failure.**
- `GATE_REPO=/path/to/tree node tools/basics-gate/run.cjs` runs the
  gate against another checkout — used to regression-test the gate
  itself against old builds (see calibration below). Needs
  `tools/store-harness`'s playwright-core, the zustand bytes the
  harness reads from the lucky-wall checkout, and python3 + PIL.

## What each check measures

| check | how | pass bar |
|---|---|---|
| page-errors | pageerror + console-error listeners, whole battery | 0 |
| sword-visible-at-rest | geometry probe (reach px) AND rendered-blade fraction: pixels sampled along grip→tip in the rest frame, matched against the measured blade steel (~(163,177,192), blue > red) | reach ≥ 60 px and rendered fraction ≥ 0.45, both viewports |
| trees-no-shadow | (1) source assertion: `drawTree`/`drawDeadTree` bodies contain no `.ellipse(` call and no `rgba(38,32,40` shadow fill; (2) frame probe: per-tree vertical luminance dip under the trunk vs 30 px further down-screen, compared per-tree against `tools/basics-gate/tree-baseline.json` | source clean; ≥ 2 baseline trees sampled, median delta ≥ −0.05, no tree below −0.12 |
| props-off-road-and-water | live probe over the game's real `PROPS` + its persistent road/water grids in every zone, AND `tools/prop_audit.py` (full-res plate discs) parsed for its scattered-prop verdict | 0 violations in both |
| hud-no-overlap@390x844 | bounding-rect intersections among the visible LEAF controls (coin, vitals, quest card, the 3 item buttons, MENU, rack tab, rack, minimap, pause) | no intersection > 4 px in both dimensions |
| labels-on-screen | every canvas fillText/strokeText is recorded with its transform; watched plates (player name, current-zone NPC names, ELITE / METAL / emperor / guardian tags) are reconstructed to screen rects | every plate that intersects the viewport is fully contained by it |
| crowd-ground-visible | whole-frame fraction of pixels matching the plate ground palette families (grass/path/water), mean of the arrival and fully-converged samples | portrait mean ≥ 0.40 (each ≥ 0.36); desktop mean ≥ 0.50 (each ≥ 0.46) |

Design notes worth knowing before "fixing" a number:

- The sword check samples RENDERED pixels because the v0.6.5 bug was
  invisible to geometry: `SP()` returns a shared array, the draw code
  aliased grip to tip, and the probe read full reach while nothing was
  drawn. Any future probe-only check is suspect by default.
- The tree frame probe compares each tree against ITS OWN baseline
  because the painted plates are biased: ground under a grove tree
  reads up to ~13% darker than 30 px further down with no shadow
  anywhere. Lateral reference strips were abandoned — neighbouring
  canopies (~440 px wide on desktop) contaminate them completely.
  Re-baseline only on a build verified good by eye (instructions are
  inside `tree-baseline.json`).
- The crowd statistic is whole-frame on purpose: the pack converges on
  the player, so a central region is the noisiest sample possible.
- HUD containers (`#rackDock`, `#items`) are transparent layout boxes
  whose rects cross other clusters without anything visible touching;
  their intersections are recorded in the report as a note, never a
  failure. Transients are excluded by design (list in report.json):
  interact prompt, boss bar, chapter card, toaster, combo badge,
  coach chip.

## Calibration (the gate tested against the builds that broke)

| build | sword | trees | crowd | labels |
|---|---|---|---|---|
| v0.6.7 (current) | PASS (rendered 0.80) | PASS (source clean, median Δ ≈ 0) | PASS (0.52–0.55 / 0.61–0.63) | PASS — plus forced-edge harness 63/63 cases, 0 violations (see first catch) |
| v0.6.6 | PASS (rendered 0.80–0.83) | PASS (source clean, median Δ ≈ 0) | PASS (0.46–0.54 / 0.55–0.62) | FAIL intermittently — fixed in v0.6.7 |
| v0.6.5 | PASS — v0.6.5 IS the sword fix | FAIL (source dirty; median Δ −0.083) | PASS | FAIL |
| v0.6.4 | FAIL (rendered 0.02–0.07) | FAIL (source dirty; median Δ −0.109) | PASS | FAIL |
| v0.6.0 transplant | FAIL (rendered 0) | FAIL (source dirty) | FAIL (0.22 / 0.13 — the carpet) | FAIL |

Calibration runs live in the same archive (`2026-11-10T06-30-46`,
`06-33-11`, `06-35-05`); the first green run on v0.6.6 is
`2026-11-10T06-42-25`.

## First catch — FIXED in v0.6.7 (2026-11-10)

**ELITE name plates clipped at the screen edge.** Plates were drawn
centred on their entity with no viewport clamping, so an elite at the
frame edge got its tag cut — measured overhangs up to ~20 CSS px past
the portrait right edge (visible bottom-right of
`2026-11-10T06-13-03/crowd-portrait.png`). Intermittent per run (it
needs an elite at the edge during the capture window): violations in
4 of 10 gate runs on v0.6.6, and on every old build tested.

Fixed in v0.6.7: every entity plate/tag draw — the ELITE tag, the
Emperor and guardian plates, NPC name plates, and the player/peer
names in drawSword — now clamps its centre through `plateC()` so the
whole rect stays inside the canvas with a 4 px margin; the plate
slides along the edge and stays attached to its entity instead of
being cut. Verified DETERMINISTICALLY, not by sampling luck: a
forced-edge harness (`~/workspace/gauntlet-archive/plate-clamp/
edge-test.cjs`) drives every plate type onto every screen edge at
both viewports (entities placed via the game's own screenToZone
inverse, rects reconstructed with this gate's own textRect) —
63/63 cases counted, 128 violations on v0.6.6 → 0 on v0.6.7, zero
page errors. The sampling check above stays as the always-on
tripwire; a green labels line in one run still does not by itself
clear an intermittent plate defect.

## Stated limitations

- **Labels is a sampling check.** It can only catch a clipped plate
  that occurs during the capture windows. It proves presence, never
  absence — see the known defect above.
- **Props live probe is coarse**: the game's persistent grids are
  48×48 over a zone (3×3 neighbourhood test). The python audit is the
  fine-grained half but MIRRORS the generator; the two must agree, and
  the live probe over the real runtime `PROPS` is the anchor. Hand-
  placed set pieces on roads (treasure grave; hermit tent + campfire)
  are report-only by design — they are authored, not scattered.
- **Tree frame check needs baseline overlap** (≥ 2 of the baselined
  trees sampled). If plates or prop placement change, trees move and
  the baseline must be re-measured on a verified-good build.
- **Title stillness (h), sword in motion, and scale feel (g)** are
  covered by the contact-sheet eye pass, not by dedicated numbers:
  the battery captures the title frame frozen and the crowd frames
  mid-fight for exactly that read.
- **HUD check runs at 390×844 in the altar state.** Desktop rects and
  menu-open states are not gated (desktop frames are on the sheet for
  the eye pass).
- The gate runs the game under the gauntlet's stubbed networking
  (Trystero stub, real zustand bytes). Multiplayer behaviour is out of
  scope — it remains unverified on real devices regardless of the gate.
