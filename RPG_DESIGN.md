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

- **Prologue — "The Grass Forgets."** Elder Mirra tests the Blade: slay 8
  slimes, return. Prophecy told. Rewards: 100c, 1 SP.
- **Ch.1 — "Sigil of the Meadow."** Shrine east of town. Guardian: **VERDANT
  WARDEN** (armoured tank-class). Sigil I + relic **Warden's Pauldron**.
- **Ch.2 — "Sigil of the Grove."** Shrine in the Grove. Guardian: **THORN
  REGENT** (king-class, summons darts). Sigil II + relic **Thorn Crown**.
- **Ch.3 — "Sigil of the Wilds."** Shrine deep in the Wilds. Guardian:
  **ROTBLOOM COLOSSUS** (splitter colossus). Sigil III + relic **Rotbloom
  Heart**.
- **Ch.4 — "The Root of Rot."** The Elder sets the Sigils; the Emperor wakes
  as the **CHAOS EMPEROR** (finale form: denser patterns, +25% HP scale).
  Kill him → ending: the Tree blooms (golden bloom ambience in the world from
  then on for that player), ending cards + credits, `storyComplete`. Postgame:
  free play; the Elder offers **New Cycle+** (story resets, guardians/finale
  scale +50% per cycle, progress/items kept).

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
- **Guardians**: boss-class world entities riding the existing boss machinery
  (boss bar with their name, orb patterns at reduced density per guardian,
  king-class movement for Regent, splitter death for Colossus, tank bulk for
  Warden). HP scales gently with player level. Kill credited to the killer's
  quest via the existing kill attribution. Solo must fully work.
- **Relics**: equip up to 2 in the INVENTORY tab; effects fold into `recalc()`
  like soul gems: Pauldron −10% contact damage taken; Thorn Crown +8% crit;
  Rotbloom Heart +1.5 HP/s regen; Sprout Charm +8% coins; Emperor's Eye
  (+10% XP) drops from the Chaos Emperor for Cycle+ runs.
- **Ending bloom**: when `story.complete`, world rendering adds golden
  speckles + drifting petals (local ambience from progress state).

## Out of scope

No new zones/biomes, no party members, no turn-based anything, no voice, no
new netcode channels (reuse pos/wrld/boss/kill patterns). No paid anything.
