# Slime Slash — RPG layer design ("The Verdance Cycle")

Handler's order (2026-11-08): full RPG elements, an epic story in the spirit of
Final Fantasy I–III. Director: Raphael M. This doc is the design authority for
the RPG builders; the game's standing rulings (GAME UI, no emoji, no
hit-stop/shake/frame-skip, observable store, Emperor-only boss toasts) all hold.

## The hook

In Slime Slash the player **is a sword** — players render as blades, there is
no swordsman. The story makes that literal: you are the **Verdant Blade**, a
living sword grown from the World Tree, and the prophecy's "blade carried by
no hand". Other players are the **Scattered Steel** — sister blades from the
same fallen branches. Multiplayer is diegetic.

## Premise

A thousand years ago the World Tree **Verdia** sickened. Its heart shattered
into three **Verdant Sigils** (Meadow, Grove, Wilds) and the slimes — once the
Tree's gardeners — turned feral as the **Rot** spread from beneath the world.
The Rot crowned the Tree's old guardian and made him the **Slime Emperor**.
The last town keeps the prophecy: *when the grass forgets its colour, a blade
carried by no hand shall gather the Sigils and cut the Rot at its root.*

## Chapters

The arc was extended to FF1 scale (2026-11-09): nine beats, FOUR guardian
"fiends", a mid-story twist, and a loop-reveal ending. Two talk beats sit
between the Sigil hunts — they are required only in sequence; progress past
their slot implies them done (see Migration).

- **Prologue — "The Grass Forgets."** Elder Mirra tests the Blade: slay 8
  slimes, return. Prophecy told. Rewards: 100c, 1 SP.
- **Ch.I — "Sigil of the Meadow."** Shrine east of town. Guardian: **VERDANT
  WARDEN** (armoured tank-class). Sigil I + relic **Warden's Pauldron**.
- **Ch.II — "The Thornwick Bell"** *(talk beat)*. Elder Mirra sends the Blade
  to Thornwick to ask the **Hermit** what the Rot *is*. His dedicated quest
  set tells of the First Garden and a guardian who "took the sickness into
  himself so the Tree would not scream" — he does not name the Emperor
  plainly. Return to the Elder. Rewards: 200c, 1 SP.
- **Ch.III — "Sigil of the Grove."** Shrine in the Grove. Guardian: **THORN
  REGENT** (king-class, summons darts). Sigil II + relic **Thorn Crown**.
- **Ch.IV — "What the Scout Saw"** *(talk beat)*. At Rotwatch, **Scout Vex**
  reports: he followed the Emperor at night and saw him at the **Root
  Shrine** on Wilds' far shore, "standing guard over something buried — like
  a dog over a grave." This beat **opens the Root Shrine** (before it, the
  shrine is inert stones and its Herald cannot be summoned). No return trip.
  Rewards: 300c, 1 SP.
- **Ch.V — "Sigil of the Wilds."** Shrine deep in the Wilds. Guardian:
  **ROTBLOOM COLOSSUS** (splitter colossus). Sigil III + relic **Rotbloom
  Heart**.
- **Ch.VI — "The Fourth Sigil."** Guardian #4: the **ROOT HERALD** at the
  Root Shrine (king-bodied; runtime antler crown of roots + tattered banner
  cape; kit: aimed bursts + rings + splitter summons; HP 3000). He drops
  **no Sigil** — on his fall the **TRUTH sequence** plays (3 chapter cards):
  the Emperor was Verdia's guardian; the Rot is the Tree's grief for a cut
  made long ago; the cut was a **blade** — the Verdant Blade has ended this
  Cycle before, and the Tree shattered its own heart to forget. The Herald
  drops the way open instead: `story.heraldDone`. Relic: the **Verdant Eye**
  ("Emperor's Eye", +10% XP) — if already owned, coin instead.
- **Ch.VII — "The Root of Rot."** The finale gate is now **Sigils ≥ 3 AND
  `heraldDone`**. The Elder sets the Sigils (her finale briefing acknowledges
  the Herald's truth); the Emperor wakes as the **CHAOS EMPEROR** (finale
  form: denser patterns, +25% HP scale). Kill him → ending: the Tree blooms
  (golden bloom ambience in the world from then on for that player), ending
  cards — including the **loop-reveal card** before the credits (Elder: "You
  have planted this garden before, Blade. This time — try to remember.") —
  and `storyComplete`. Postgame: free play; the Elder offers **New Cycle+**
  (story resets — `heraldDone` included, so the Herald re-locks with the
  chain — guardians/finale scale +50% per cycle, progress/items kept).

## Save migration (FF1 arc)

`progress.story.heraldDone` is the arc's only new field (optional, defaults
false). Saves written before the arc lack the key entirely — its **absence**
is the old-save marker (new saves always write it). Applied once, in
`loadProgress`:

| Old save state | Migrates to | Why |
|---|---|---|
| `complete: true` (quest `postgame`) | untouched | the tale is done |
| quest `finale` (3 Sigils, old gate) | quest `herald`, step reset | they still owe the fourth guardian under the new gate |
| quest `wilds` | stays `wilds` | scout precedes wilds in the new chain, but a Blade mid-wilds is never sent backwards; the Root Shrine wakes for them via the three-Sigils leniency |
| quest `grove` | stays `grove` | bell is treated as done-in-passing |
| quest `meadow` / `prologue` | unchanged ids | the arc runs in full from here |

Root Shrine wake rule (`rootShrineAwake`): the `scout` beat is done, **or**
the Blade carries three Sigils, **or** `heraldDone`, **or** the Cycle is
complete. The talk beats are REQUIRED only in sequence for players who reach
them in sequence.

Side quest (any time after Prologue): **"Three Lost Sproutlings"** — the Child
in town; find 3 sproutling interactables hidden in the world, return. Reward:
relic **Sprout Charm**.

## NPCs (town, pixel figures, in-world speech bubbles)

- **Elder Mirra** (by the plaza) — story giver, all chapter quests.
- **Forge** (at the SHOP) — flavour, smithing hints.
- **Warden Pike** (at the INN) — lore, combat tips (rotates).
- **The Child** (wanders the plaza) — side quest giver.

Dialogue: bubble above the NPC's head, typewriter reveal, tap / interact key
advances; lines are data per NPC + quest state. Interact prompt chip like
buildings (B / tap).

## Systems

- **Quest engine** (data-driven): quests = { id, chapter, giver, objectives,
  dialogue, rewards }. Objective types: `talk`, `killCount`, `killKind`,
  `guardian`, `emperorFinale`, `interact` (sproutlings), `return`. Progress
  lives ONLY in the progress slice (`story: { quest, step, sigils, cycles,
  complete, relicsOwned, relicsEquipped, sprouts }`), additive save fields
  with defaults — old saves load unchanged.
- **Quest tracker**: one slim chunky card under the stat panel — current
  objective + n/m. Tap opens the STORY tab. Only the tracker + chapter cards
  are new HUD; everything else lives in the menu.
- **STORY tab** in the menu: chapter list (done = stamped, current = detail +
  objective text, future = "???"), and the prophecy text.
- **Chapter cards**: full-screen dark pixel plate at chapter starts and the
  ending — chapter numeral + title + 2–3 narration lines, tap to continue.
- **Shrines**: one per zone — stone ring + crystal (per-zone tint), interact
  when the quest points there summons the Guardian; after the Sigil, the
  crystal glows (world visual from world slice state + progress sigils).
  Plus the **Root Shrine** on Wilds' far shore: not a Sigil shrine — inert
  stones until woken (see `rootShrineAwake`), its own banner poles and
  rot-root dressing, ambient spawns suppressed around it like its sisters,
  and it joins shrine fast-travel once the Herald falls.
- **Guardians**: boss-class world entities riding the existing boss machinery
  (boss bar with their name, orb patterns at reduced density per guardian,
  king-class movement for Regent, splitter death for Colossus, tank bulk for
  Warden). HP scales gently with player level. Kill credited to the killer's
  quest via the existing kill attribution. Solo must fully work.
- **Relics**: equip up to 2 in the INVENTORY tab; effects fold into `recalc()`
  like soul gems: Pauldron −10% contact damage taken; Thorn Crown +8% crit;
  Rotbloom Heart +1.5 HP/s regen; Sprout Charm +8% coins; the Verdant Eye
  ("Emperor's Eye", +10% XP) drops from the **Root Herald** (Ch.VI); a quest
  relic already owned pays out in coin instead (guardian norms).
- **Ending bloom**: when `story.complete`, world rendering adds golden
  speckles + drifting petals (local ambience from progress state).

## Out of scope

No new zones/biomes, no party members, no turn-based anything, no voice, no
new netcode channels (reuse pos/wrld/boss/kill patterns). No paid anything.
