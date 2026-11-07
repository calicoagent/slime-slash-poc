# Slime Slash: central zustand store (Raphael C, 2026-11-08)

Handler's order: "Move state to central zustand store properly seperate world and player progress."
Base: `b232d21` (No cap). Local commits on `master`, not pushed. Assets untouched
(`git diff b232d21..HEAD -- assets` is empty). No gameplay, balance, UI or visual change.

| Commit | Change |
|---|---|
| `a7842d3` | zustand 5.1.0 vanilla import (pinned, jsdelivr); store with the **world** slice |
| `4d70eb9` | **session** slice (player body, HP/MP, combo, input, camera, FX, UI state, clocks) |
| `11b44ba` | **progress** slice: the save, immutable, written only through store actions; persist/load in the store |
| `f01adbb` | `tools/store-harness/`: headless harness, fixtures, `check-module.sh` |
| this one | these notes |

## 1. Store design

```js
import { createStore } from 'https://cdn.jsdelivr.net/npm/zustand@5.1.0/vanilla/+esm';
const store = createStore((set, get) => ({ world, session, progress, ...actions }));
const world = store.getState().world;      // stable slice
const ses   = store.getState().session;    // stable slice
const me    = ses.player;                  // the local player's live body
const prog  = () => store.getState().progress;   // read fresh, every time
const act   = /* the store's action functions only */;
```

| Slice | Owner / lifetime | Writes | Persisted | Synced |
|---|---|---|---|---|
| `world` | shared, ephemeral, host-authoritative | netcode + host sim, in place | never | yes, through the unchanged world payload |
| `session` | this tab, ephemeral | frame loop / input / UI, in place | never | never (pos payload unchanged) |
| `progress` | this player, durable | store actions only, `set()` with a new object | yes, `slimeslash-save-v1` | no (name/level/weapon are read into the pos payload as before) |

**How writes work, per slice.** The order said "writes via store actions/setState" and also
"no new object allocations in hot paths". Both can't hold for every write, because slime
positions, HP/MP regen, the slash trail and the pointer change every frame and an immutable
`set()` allocates a new root object each time. So I split it this way:

- **progress** is fully immutable. Every write is a named action (`patchProgress`,
  `addCoins`, `setWxp`, `addGem`, `payCost`, `addItem`, `ownWeapon`, `unlockNode`,
  `addToGemBag`, `markHint`, `bountyStep`, `resetProgress`). Each one `set()`s a new
  progress object and copies nested objects, arrays and Sets on write. Progress changes on
  discrete events (kill, buy, unlock, level), not per frame.
- **world** and **session** are stable objects: created once, never replaced. Code reads
  and writes their fields and entity records in place (`world.slimes`, `me.hp`,
  `ses.combo`). Zero allocations, no subscriptions. The store is still the only place those
  facts live; nothing reads them through a copy.

Nothing subscribes to the store at runtime (the harness's FREEZE check is the only
subscriber).

**Persist boundary.** `persistProgress`, `loadProgress`, `hasSave` and `clearSave` are the
only localStorage access for the save. The key and the JSON shape are unchanged, field order
included. `saveGame()` is now `act.persistProgress()`. Its call sites didn't change: event
saves, the 2.5 s HUD throttle, and `pagehide` / `visibilitychange→hidden`. zustand's
`persist` middleware is deliberately not used because it writes on every `set()`, which
would mean a localStorage write per kill. HP/MP live in `session` and never reach the save
(measured: `hpInSave: false`).

**What stays outside the store:** handles and caches only. That's the canvas size
(`W/H/DPR`), the audio context `AC`, images and tint caches, DOM updater lists
(`shopUpdaters`, `menuInvUpdaters`), DOM write-memos (`setText`'s `el._t`,
`updateDmgFlash._a`, `updateInteract._pr`) and the per-frame boss memo `_bossT/_bossS`.
No module-level `let` holds game state any more.

## 2. Where the old state holders went

| Old | New |
|---|---|
| `me` object (one bag of position + HP + economy + progression) | split: body/HP/MP/cooldowns → `ses.player` (`me`); level, xp, coins, kills, sp, spBuys, weapon, name, banked, items, purse, owned, gems, wxp, gemBag, sockets, spawnAt → `progress` |
| `slimes`, `slimeSeq`, `nodes`, `nodeSeq`, `nodeRespawnAt`, `peers`, `scores` | `world.*` |
| `isHost`, `hostId`, `lastWorldAt`, `room`, `send*` (7 channels), `joinedAt` | `world.*` |
| `bullets`, `spiralEmitters`, `pendingVolleys`, `pendingBursts` (boss orbs) | `world.*` |
| `bossSpawnAt`, `lastMetalAt`, `metalNoneNearSince`, `bossFireAt`, `bossPatternIdx`, `bossEnraged`, `bossFury`, `bossSummonAt` | `world.*` (host clocks/latches) |
| `hitClaimsAt`, `hostTick._prune` | `world.hitClaimsAt`, `world.hitPruneAt` |
| `worldTimer`, `worldDirty` | `world.*` |
| `unlocked`, `bounty`, `hintsSeen`, `muted`, `rackCollapsed` | `progress.*` |
| `started`, `startedAt`, `paused`, `cam`, `combo`, `comboUntil`, `dmgFlashAt`, `myTrail`, `myZone`, `nearBuilding`, `seenBosses` | `ses.*` |
| `particles`, `floats`, `popRings`, `dmgFloats`, `dmgCue`, `waves`, `meteors`, `shots` | `ses.*` |
| `pointerDown`, `lastClient`, `lastMoveT`, `uiPointer`, `downInfo` | `ses.*` |
| `menuTab`, `selNode`, `sphereCentered`, `sphereZoom`, `resetArmed`, `menuResetArmed`, `titleResetArmed`, `bubbleTimer`, `gemSeq`, `lastTingAt`, `lastPickToastAt` | `ses.*` |
| `S` (derived stats) | `ses.stats` (derived cache, rebuilt by `recalc`) |
| `lastT`, `posSendAcc`, `frame._mm`, `frame._b`, `refreshHUD._sv`, `localHitCheck._prune` | `ses.lastT`, `ses.posSendAcc`, `ses.minimapAt`, `ses.slowTickAt`, `ses.autoSaveAt`, `ses.hitPruneAt` |
| `saveGame` / `loadGame` bodies, `localStorage` calls in `resetRun` and the title RESET | store `persistProgress` / `loadProgress` / `clearSave` / `hasSave` |

The world and session renames used scope analysis (acorn + eslint-scope), so locals that
shadow a name were left alone (for example the `P` and `nodes` locals). The ~100 progress
writes were converted one by one, including writes through aliases: `gainWxp` and
`breakthroughWeapon` mutated the record returned by `wxpOf()`, and `socketGem` pushed into
the sockets array.

## 3. Validation

All of it ran on this Mac with Playwright 1.56.1 `headless_shell` at 390×844 @3x. Harness:
`tools/store-harness/harness.js`. It runs against both the pre-store build and this build
through one adapter.

- **(a) `node --check`** (`tools/store-harness/check-module.sh`, Trystero and zustand stubbed
  for this check only): **OK, 4,501 lines** (final tree; 4,492 before the store header comment).
- **(b) Boot with the REAL imports** (`boot` mode, nothing stubbed or routed): **0 page
  errors, 0 console errors**. jsdelivr served `zustand@5.1.0/vanilla/+esm` with 200, plus
  Trystero 0.21.6 and its secp256k1 dependency. The title screen was visible, PLAY hid it,
  the HUD showed, and the screenshot shows the world rendered with slimes spawned. The only
  console noise was 2–3 nostr relay WebSocket failures (`relay.current.fyi` DNS,
  `relay.damus.io` 503). Those relays are external and happen the same on the base build.
- **(c) Saves.** Handler-like Lv 38 fixture (26 Sphere nodes, 3 socketed gems, purse,
  bounty, inn respawn):
  - loaded then saved: **byte-identical** to what `b232d21` writes.
  - a 15-step scripted session (deposit, withdraw, buy items, potion, equip, 3.5-level XP
    grant, weapon XP, gem drop, unsocket, socket, buy SP, craft, 4 kills, King kill):
    **the save after every step is byte-identical** between base and store build. The only
    difference is the `Date.now()` part of soul-gem ids, which is wall clock. It matches
    after normalisation.
  - legacy fixture (no `owned`, the old `spin` hint, invalid gems, sockets pointing at
    missing gems, weapon Lv 99, a bogus node id, an unsafe name): base and store build
    migrate it to the **identical** save.
  - a save written by the store build: loaded and re-saved by the store build gives an
    **identical** string, and the old build loads it identically too.
  - `pagehide` writes progress changed since the last throttled save (777,777 on both).
    RESET SAVE removes the key and the next save matches base.
  - UI click-through (Sphere tab, zoom, 3 unlocks through `#ncBtn`, pause, sound, weapon
    keys, rack tab): saves identical base vs store build.
  - **FREEZE=1**, progress deep-frozen after every `set()`, so any leftover in-place write
    throws: func 53 commits, ui 14, perf fight 376, **0 errors**.
- **(d) Move-and-fight** (12 s Warhammer, slime clusters every ~600 ms, 4× CPU throttle,
  runs interleaved):

  | run | JS script | layout | frame gap p95 / p99 / max | world payloads |
  |---|---|---|---|---|
  | base 1 / 2 / 3 | 1.63 / 1.67 / 1.62 s | 0.100 / 0.093 / 0.107 s | 50 / 50–67 / 67–83 ms | 0 |
  | store 1 / 2 / 3 | 1.69 / 1.65 / 1.74 s | 0.100 / 0.102 / 0.089 s | 50 / 50–67 / 67–83 ms | 0 |
  | store, FREEZE | 1.72 s | 0.106 s | 50 / 50 / 67 ms | 0 |

  Mean script time is 1.64 s on base and 1.69 s on the store build (+3%). That's inside
  base's own run-to-run spread today (1.51–1.67 s over 6 base runs: 2 old-harness, 4 this harness) and in line with the
  3558c73-era 1.56 s. Frame gaps match. Headless at 4× is CPU-saturated, as in the earlier
  review. localStorage writes in the fight are event saves only (15–27, scaling with
  level-ups), with no per-frame writes, the same as base.
- **(e) grep proof:** `grep -n "localStorage\|SAVE_KEY" index.html` returns only the store
  block: the `SAVE_KEY` definition, `setItem` in `persistProgress`, `getItem` in
  `loadProgress` and `hasSave`, `removeItem` in `clearSave`, plus comments.
  `grep -c setItem` is 1.
- Rulings re-checked on the diff: no `shadowBlur`, `ctx.filter`, shake, hit-stop or frame
  skip added (the only "shake" lines are the existing rock `shakeT`, renamed). No emoji.
  Assets are byte-identical. The host hit path (no cap with finite-positive sanitisation,
  Metal exactly 1, Royal Guard rejection, `hitClaimsAt` pruning, payload coalescing) and the
  toast code changed only by renames.

Re-run: `cd tools/store-harness && npm i && node harness.js ../.. run <boot|perf|func|ui|reload> [fixture.json]`.
Pass a checkout of `b232d21` as the repo dir to get the base numbers.

## 4. Behaviour I had to touch

None changed. Two places needed care to stay the same:

1. **Load-time stats come from weapon 1.** The old `loadGame` ran `recalc()` before it
   restored the saved weapon, so the soul-gem stats folded into `S` (and `maxHp` through
   vitality) came from **weapon 1's** sockets. That lasts until the next recalc (level-up,
   unlock, or gem change). An atomic store load would have quietly "fixed" this. I kept it
   explicitly instead: `recalc(1)` in `loadGame`, with a comment. Bug for Handler, item 1
   below.
2. `ses.lastT` is stamped when the store is created rather than a few hundred lines later
   in module evaluation. That's a sub-millisecond difference in the first frame's `dt` and
   isn't observable.

## 5. Bugs found, not fixed (Handler's call)

1. **Soul-gem stats follow the wrong weapon.** `equip()` doesn't call `recalc()`, so after a
   weapon switch the stats still include the previous weapon's socketed gems until the next
   level-up, unlock or gem change. The same applies right after a load (weapon 1, above).
   With a vitality gem this also shifts `maxHp`. The fix is one `recalc()` in `equip()` and
   `recalc()` instead of `recalc(1)` in `loadGame`. It changes stats players feel, so I
   didn't apply it.
2. The earlier review's open items (double splash, net trust on `kill`/`boss`/`mined`, boss
   latches lost on host migration, Baloo 2 font, `debug.html` on Trystero 0.26) are
   unchanged. The store makes the migration fix easier: the latches all sit in `world` now.

## 6. Risks

- **The zustand CDN is a new runtime dependency.** If jsdelivr fails, the module doesn't
  load at all, the same failure mode as Trystero today. The version is pinned to 5.1.0. The
  served file is jsdelivr's Rollup bundle of `esm/vanilla.mjs` (about 40 lines, no
  dependencies).
- **The rule that `prog()` is always read fresh is a convention.** A reference held across
  a write sees stale progress. FREEZE catches in-place writes but not stale reads. Today
  every progress read is a direct `prog().x`.
- Real-device multiplayer is still unverified (the boot test reached the relays but found
  no peer), and there's still no iPhone run. Same as the previous review.
