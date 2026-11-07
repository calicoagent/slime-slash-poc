# Slime Slash — review notes (Raphael C, 2026-11-07)

Scope: full read of `index.html` at `906ebae` (4,987 lines; module script
lines 812–4985), then fixes as separate local commits on `master`. Not
pushed. Assets untouched (`git diff 906ebae..HEAD -- assets` is empty).

## 1. What changed (7 commits, `index.html` only, +158 / −62)

| Commit | Kind | Change |
|---|---|---|
| `0b868dc` | PERF | No network serialise without peers; hit/kill/mine broadcasts coalesced to ONE world payload per frame |
| `577089b` | FIX  | `notify()` cap loop froze the tab (infinite loop) when the oldest toast was mid-fade |
| `b9c75fb` | PERF | View-cull slimes in the entity pass; per-frame boss memo; floats set `ctx.font` only on change |
| `4c82e9b` | FIX  | Host splash now kills what it takes to ≤0 HP; one XP grant can level more than once; stale "UNLOCKED: weapon" toast removed |
| `abdb70d` | FIX  | Sphere unlock, DEPOSIT/WITHDRAW and bounty payout save on the event; save on `pagehide` / `visibilitychange→hidden` |
| `dc5548f` | FIX  | Prune host `hitClaimsAt`; title-screen slimes no longer leak into the world; Esc closes bank/shop; Keen Eye text corrected |
| `3558c73` | PERF | HUD writes only on change; weapon-XP bar patched in place instead of a 7-card rack rebuild on every kill |

### Findings behind each change

1. **Tab freeze in `notify()` (likely part of the iPhone "crash").**
   `dismissToast(el, true)` returned early for a toast already fading
   (`_gone`, still in the DOM for its 240 ms exit). `notify()` loops
   `while (children > 4) dismissToast(lastElementChild, true)`, so with 4
   toasts up, the oldest auto-dismissing and a 5th arriving inside that
   240 ms, nothing was removed and the loop spun forever. That's routine
   mid-fight (streak, combo, level, SP and Emperor toasts). Reproduced
   headlessly on `906ebae`: the evaluate never returns (5 s timeout); after
   the fix it returns in 3 ms with 4 toasts. It also hung my first perf
   harness run on the base build: renderer pegged at 100% for 4.5 min.
2. **Solo host serialised the whole world on every hit.** Trystero 0.21.6
   `send()` does `JSON.stringify` + `encodeBytes` + chunking *before*
   iterating peers (`room.js` send, read from the CDN source). Each
   `hostApplyHit` / `hostKill` / `hostMine` also called `worldPayload()`
   (every slime through `toFixed`) synchronously, so one splash swing
   built N full payloads in one frame. Measured solo in a 12 s fight:
   **138–152 payloads, ~0.86–0.95 MB serialised, for zero peers → 0 after.**
   With peers it's now ≤1 world payload per frame plus the 220 ms heartbeat.
3. **Every slime in the world was drawn every frame**, along with a
   face-fade test against every occluder. The world is 6×6 u and a phone
   view is ~1.8×1 u. Culling uses a generous box (`r*4 + .3u`) that
   covers hop lift, HP bar, ELITE tag, motes and the Emperor's aura and
   name plate, so the visible frame is identical.
4. **Splash zombies.** Host-side Greatsword/Warhammer splash reduced
   neighbour HP but never called `hostKill`. Test: 4 ring slimes at 1 HP,
   one Warhammer hit. Before: 4 left alive at ≤0 HP. After: 0, credited
   to the hitter.
5. **XP overflow parked.** `gainXp` used `if`, not `while`. A scaled
   Emperor at Lv 38 pays ~15.8k XP against 3.8k per level. Test (3.5
   levels of XP at Lv 38): before 38→39 with 16,705 XP parked; after
   38→43 with 624 left. Each level still pays its own SP and +10 HP.
6. **Saves lost by the 906ebae throttle.** Unlocks, bank moves and bounty
   SP used to ride the every-call HUD save; after the 2.5 s throttle they
   saved nothing until the next tick. Now saved on the event, plus on
   `pagehide` / `hidden`. Test: coins set to 777,777, then `pagehide`.
   Before: disk still 5,400. After: 777,777.
7. **Unbounded host map.** `hitClaimsAt` kept one key per (player,
   slime/rock) for the whole host reign. It's now pruned (entries >1 s
   old, every 5 s, once >600).
8. **Title slimes leaked.** The 9 `amb*` title slimes stayed in the map
   after PLAY, so `electHost`'s `slimes.size===0` 50-slime seed never ran.
9. **DOM churn per kill.** `gainWxp` rebuilt the whole rack (img nodes +
   a forced layout in `syncRackUI`) on every kill and every mined chunk.
   `refreshHUD` re-wrote ~15 values and re-parsed the scoreboard
   `innerHTML` several times a frame in fights. Cooldown overlays wrote
   style every frame even when idle.

## 2. Validation

- `node --check` on the extracted module with the Trystero import stubbed:
  **OK, 4,268 lines** (helper: extract `<script type="module">`, replace
  the CDN import with a stub, `node --check`).
- Headless Chromium (Playwright 1.56.1, the cached `headless_shell-1194`)
  on this Mac, iPhone-sized 390×844 @3x, Trystero stubbed (stub does the
  same stringify+encode as the real send), seeded `Math.random`, a
  Handler-like save (Lv 38, 1,100 kills, 26 Sphere nodes, Sword Lv 20,
  Warhammer Lv 9, 3 socketed gems, purse, 20k banked).
  Scenario: 12 s Warhammer move-and-fight, slime clusters dropped under
  the sword every ~600 ms, **4× CPU throttle**.

  | build | JS script time | layout | frame-gap p95 / p99 / max | world payloads |
  |---|---|---|---|---|
  | base (906ebae + toast fix only, so it can finish) run 1 | 2.21 s | 0.123 s | 50.1 / 66.7 / 100.0 ms | 138 (859 KB) |
  | base run 2 | 2.18 s | 0.141 s | 66.6 / 66.8 / 100.1 ms | 152 (952 KB) |
  | after `b9c75fb` (net + cull) | 1.71 / 1.68 s | 0.16 / 0.15 s | 50.1 / 66.7 / 83.4 ms | 0 |
  | final `3558c73` | **1.56 s** | **0.089 s** | **50.0 / 50.1 / 66.7 ms** | **0** |

  Headless at 4× throttle is CPU-saturated (TaskDuration ≈ wall time in
  every run), so p50 stays 33 ms in all builds. These numbers show work
  removed, not iPhone FPS: canvas raster/GPU cost isn't captured.
- Functional checks (same harness, `func` mode), base vs final:
  save round-trip **identical** (level, kills, SP, coins, banked, owned,
  26 unlocks, weapon XP, gem bag, sockets, bounty, old `spin` hint key →
  `skill`); splash zombies 4 → 0; multi-level XP 38→39 vs 38→43;
  pagehide save 5,400 vs 777,777. Zero page errors in every run.
- Screenshot of the final build mid-fight (real fonts): HUD, rack card
  in-place "Lv 10!" gate pulse, item counts, toasts at the very top,
  combo badge all render.
- Rulings re-checked against the diff: no `shadowBlur`, no `ctx.filter`,
  no shake / hit-stop / frame skip, no emoji, no per-frame
  `localStorage` (7 new `saveGame()` calls, all on discrete events),
  King/Emperor sprite and every asset byte-identical, toasts unchanged
  (still Emperor-only boss toasts, top stack).

## 3. Recommended, NOT changed (balance / design calls for Handler)

1. **Host damage cap of 120 per claim.** This is the biggest balance
   finding. `hostApplyHit` clamps every claim (the host's own included)
   to 120. Measured pre-crit `myDamage()` on the Lv 38 fixture: Sword
   231, Warhammer 213, Katana 168, Dagger 93, Pickaxe 90. So at
   Handler's level the cap binds on most hits, crits (x1.75 / x2.2) are
   discarded entirely, weapon levels 10→50 (x2.35 → x5.55) add nothing
   past the cap, and the floating numbers ("440!") overstate what lands
   by 2–4x. The Emperor's HP scaling (x8.8 = 35,200 HP at Lv 38) assumes
   damage grows. Options: (a) scale the cap with the claimant's level
   (the host already gets `l` in the pos payload), e.g. `max(120, 12*level)`;
   (b) keep 120 but clamp the client's damage float to what the host will
   apply, so the numbers stop lying. Either one changes feel, so it's
   Handler's call.
2. **Double splash for Greatsword/Warhammer.** The client `doHit` already
   sends half-damage claims for neighbours (native weapon splash + tree
   nodes), and the host *also* applies the weapon's native splash on
   every claim it receives, including those secondary ones. Splash is
   effectively applied twice. Removing the host copy would weaken both
   weapons noticeably; balance call.
3. **Net trust.** `kill`, `boss` and `mined` events are accepted from any
   peer, not just `hostId`. The room id + appId are fixed and public
   (nostr relays), so any client could grant coins or fire bullet rings.
   Restricting these to `id === hostId` is a one-liner, but it interacts
   with host-migration races and partial-mesh split brains. I didn't
   change it while real-device peer discovery is unverified.
4. **Host migration loses boss latches.** `guard66` / `guard33`, enrage,
   fury and `bossSpawnAt` live only on the old host. A handover mid-fight
   re-fires ROYAL GUARD and restarts the spawn clock. Carry them in the
   payload's `b` block if handovers happen in practice.
5. **"Baloo 2" never loads.** Canvas text (signs, names, floating coins,
   ELITE/boss labels) asks for `"Baloo 2"`, but the page only loads
   Press Start 2P and VT323, so it falls back to the system sans (Helvetica
   bold on iPhone), which reads as website type. Either add Baloo 2 to
   the font link or move canvas text to VT323 / Press Start 2P. It's a
   visual change, so Handler's call.
6. **`debug.html` pins trystero 0.26** (`@trystero-p2p/nostr`, property-style
   `onPeerJoin`) while the game ships 0.21.6 (method-style). A debug page
   on a different major API can't confirm the game's discovery path.
7. **Combo badge vs item row (phone).** At 3-digit combos ("x135 ON FIRE")
   the badge sits flush on the items row and its pop animation pushes it
   over the count chips. The ruling says only toasts may cover UI, so it
   needs a few px more clearance or a narrower 3-digit layout.

## 4. Remaining risks

- **Real-device multiplayer peer discovery is still unverified.** Nothing
  here tests it; the harness stubs Trystero. Coalescing changes host
  broadcast timing by ≤1 frame, which isn't verified with real peers.
- **No on-device iPhone run.** Perf numbers are headless Chromium with CPU
  throttle; Safari's canvas raster and GPU cost, and Safari-specific font
  parsing, aren't measured. The toast freeze is proven in Chromium; the
  same loop logic is engine-independent.
- View culling relies on the `r*4 + .3u` margin covering every
  slime-attached visual. The largest (Emperor aura 1.8×1.3×.14 u ≈ .33 u,
  name plate at 1.45× baseR) fits inside the boss's .86 u margin. A future
  bigger effect drawn from `drawSlime` would need the margin rechecked.
- `setText` / `setStyle` cache values on the element. Any new code that
  writes those same HUD nodes directly would desync the cache. Use the
  setters for those nodes.
