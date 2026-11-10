// basics-gate/run.cjs — the Slime Slash pre-ship VISUAL BASICS GATE.
// See BASICS_GATE.md (repo root) for the rules this enforces and why.
// Boots the game fresh-save at portrait 390x844 + desktop 1920x1080
// (stubbed-import Playwright, pattern after the gauntlet harnesses),
// captures the frame battery, runs the automated checks, writes
// report.json + contact-sheet.png to
//   ~/workspace/gauntlet-archive/basics-gate/<timestamp>/
// and exits NONZERO if any check FAILs. No build ships on a red gate.
//
// Env: GATE_REPO — repo to test (default: this repo). Used to
// regression-test the gate itself against older builds.
const http = require('http'), fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const { chromium } = require(path.join(__dirname, '..', 'store-harness', 'node_modules', 'playwright-core'));
const REPO = process.env.GATE_REPO || path.resolve(__dirname, '..', '..');
const STAMP = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const OUT = path.join(process.env.HOME, 'workspace', 'gauntlet-archive', 'basics-gate', STAMP);
fs.mkdirSync(path.join(OUT, 'tmp'), { recursive: true });
process.env.TMPDIR = path.join(OUT, 'tmp');           // hermetic: no /tmp fills
const ZUSTAND = fs.readFileSync('/home/hatch/Projects/lucky-wall/node_modules/zustand/esm/vanilla.mjs');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.json': 'application/json', '.mp3': 'audio/mpeg', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.mp4': 'video/mp4' };

/* ---- thresholds (calibrated 2026-11-10 against v0.6.6 and the
   v0.6.0/v0.6.5 failures they exist to catch; see report of the
   calibration run in BASICS_GATE.md) ---- */
const SWORD_MIN_REACH_PX = 60;      // rest-state blade length, game px (geometry)
const SWORD_BLADE_MIN = 0.45;       // rendered-blade fraction along grip->tip in the rest frame (v0.6.5 drew only a pommel dot: ~0; fixed build: ~1)
const TREE_MEDIAN_TOL = 0.05;       // matched-tree MEDIAN dip delta vs baseline (shadowed builds measured -0.083/-0.109; shadowless ~0)
const TREE_GROSS_TOL = 0.12;        // any single tree dropping further is a gross local shadow, median or not
const TREE_MIN_MATCHED = 2;         // baseline trees that must be sampled for the frame half to pass
/* crowd ground visibility = WHOLE-frame ground-palette fraction (see
   pixels.py for why whole-frame, not a central region). Verdict on the
   MEAN of the arrival sample and the fully-converged (dense) sample,
   with a per-sample minimum guard. Measured 2026-11-10: healthy builds
   portrait .46-.55, desktop .578-.587 across runs; the archived v0.6.0
   carpet frame reads .213 whole-frame. Floors sit between the regimes
   with margin on both sides. */
const CROWD_P_MEAN = 0.40, CROWD_P_MIN = 0.36;   // portrait mean/min ground fraction
const CROWD_D_MEAN = 0.50, CROWD_D_MIN = 0.46;   // desktop mean/min ground fraction
const HUD_MAX_OVERLAP_PX = 4;       // per-dimension overlap allowed between HUD clusters

const STUB = `
export const selfId = 'aaaa-self';
export function joinRoom(){
  window.__sent = {}; window.__bytes = {};
  return { onPeerJoin(f){ window.__pj = f; }, onPeerLeave(f){ window.__pl = f; },
    makeAction(t){ return [ (d)=>{ return Promise.resolve(); }, (f)=>{ (window.__on = window.__on || {})[t] = f; } ]; } };
}`;

const EXPOSE = `
;(function(){
window.__drv = null;
window.__drive = (wps) => { window.__drv = { wps, i: 0, last: performance.now() }; };
window.__stopDrive = () => { window.__drv = null; };
(function drvLoop(){
  requestAnimationFrame(drvLoop);
  const d = window.__drv; if (!d) return;
  const now = performance.now();
  const wp = d.wps[d.i]; if (!wp){ window.__drv = null; return; }
  let tx = wp.x, ty = wp.y;
  const a = SP(me.x, me.y), ax = a[0], ay = a[1];
  const b = SP(tx, ty), bx = b[0], by = b[1];
  const distPx = Math.hypot(bx - ax, by - ay);
  const dtS = Math.min(.1, Math.max(.001, (now - d.last) / 1000)); d.last = now;
  if (distPx <= (wp.arrivePx || 3)){ d.i++; return; }
  const stepPx = Math.min(distPx, wp.pxs * dtS);
  const f = stepPx / distPx;
  pushPtrSample(me.x + (tx - me.x) * f, me.y + (ty - me.y) * f, now);
})();
/* canvas text recorder: every fillText/strokeText on the game canvas,
   with the live transform + measured width — the label on-screen check
   reconstructs screen rects from these. SP returns a shared array;
   getTransform() returns a fresh DOMMatrix, so this is safe. */
window.__texts = [];
(function(){
  const ft = ctx.fillText.bind(ctx), st = ctx.strokeText.bind(ctx);
  const rec = (kind, txt, x, y) => { try {
    const tr = ctx.getTransform();
    window.__texts.push({ k: kind, t: String(txt), x, y, w: ctx.measureText(String(txt)).width,
      font: ctx.font, align: ctx.textAlign, base: ctx.textBaseline,
      a: tr.a, b: tr.b, c: tr.c, d: tr.d, e: tr.e, f: tr.f });
    if (window.__texts.length > 6000) window.__texts.splice(0, 3000);
  } catch(e){} };
  ctx.fillText = (t, x, y, m) => { rec('fill', t, x, y); return ft(t, x, y, m); };
  ctx.strokeText = (t, x, y, m) => { rec('stroke', t, x, y); return st(t, x, y, m); };
})();
window.__G = {
  probe: () => ({ version: GAME_VERSION, zone: ses.myZone, started: ses.started }),
  census: () => { let n = 0; for (const s of world.slimes.values()) if (s.zone === ses.myZone) n++; return n; },
  mePos: () => ({ x: +me.x.toFixed(2), y: +me.y.toFixed(2) }),
  meScreen: () => { const p = SP(me.x, me.y).slice(); return { x: p[0], y: p[1] }; },
  interact: () => interactPressed(),
  god: () => { const keep = () => { me.invulnUntil = performance.now() + 5000; requestAnimationFrame(keep); }; keep(); },
  teleport: (x, y) => { me.x = x; me.y = y; me.px = x; me.py = y; ses.cam.x = x; ses.cam.y = y; pinPtr(x, y, performance.now()); },
  travel: (z, x, y) => { doZoneTravel(z, x, y, ZONES_DEF[z].name); return ses.myZone; },
  townPos: () => ({ x: TOWN.x, y: TOWN.y }),
  swordProbe: () => { const bl = bladeAt(performance.now()); const g = SP(me.x, me.y).slice();
    const tp = SP(me.x + Math.cos(bl.ang) * myReach() * (1 + bl.ext), me.y + Math.sin(bl.ang) * myReach() * (1 + bl.ext)).slice();
    return { reach: myReach(), ang: bl.ang, reachPx: Math.hypot(tp[0] - g[0], tp[1] - g[1]), liveF: ses.liveF, weapon: myWeapon().id,
      grip: { x: g[0], y: g[1] }, tip: { x: tp[0], y: tp[1] } }; },
  propsReady: () => ZONE_IDS.every(z => PROPS[z]),
  propsAudit: () => { const out = {};
    for (const z of ZONE_IDS){ const items = PROPS[z] || [];
      const onRoad = (x, y) => { if (typeof zonePath === 'undefined' || !zonePath[z]) return null;
        const bx = (x / ZONE_U * WATER_GRID_N) | 0, by = (y / ZONE_U * WATER_GRID_N) | 0;
        for (let oy = -1; oy <= 1; oy++) for (let ox = -1; ox <= 1; ox++){ const nx = bx + ox, ny = by + oy;
          if (nx < 0 || ny < 0 || nx >= WATER_GRID_N || ny >= WATER_GRID_N) continue;
          if (zonePath[z][ny * WATER_GRID_N + nx]) return true; } return false; };
      const scat = items.filter(i => i.t === 'tree' || i.t === 'rock');
      out[z] = { scattered: scat.length,
        onRoad: scat.filter(i => onRoad(i.x, i.y)).map(i => ({ t: i.t, x: +i.x.toFixed(2), y: +i.y.toFixed(2) })),
        onRoadCheckable: typeof zonePath !== 'undefined' && !!zonePath[z],
        inWater: scat.filter(i => waterAt(z, i.x, i.y)).map(i => ({ t: i.t, x: +i.x.toFixed(2), y: +i.y.toFixed(2) })) };
    } return out; },
  treesOnScreen: () => { const z = ses.myZone, u = 440 * ZK(), items = PROPS[z] || [];
    const vis = (p, m) => p[0] > -m && p[0] < W + m && p[1] > -m && p[1] < H + m;
    const trees = [], rocks = [], slimes = [];
    for (const d of items){ const p = SP(d.x, d.y).slice();
      if (d.t === 'tree' && vis(p, 60)){
        /* water under the strip footprint darkens it exactly like a
           shadow would — flag such trees so the pixel check skips them */
        let water = false;
        for (const dx of [-.4 * d.s, 0, .4 * d.s]) for (const dy of [.05, .25, .45])
          if (waterAt(z, d.x + dx, d.y + dy)) water = true;
        /* the sampled column (x +-.25*w, base..base+42) must be fully
           on-frame, or the pixel strips come back null */
        const w = .36 * u * d.s, base = p[1] + .03 * u;
        if (base + 42 >= H || p[0] - .25 * w <= 0 || p[0] + .25 * w >= W) continue;
        trees.push({ id: z + ' tree (' + d.x.toFixed(2) + ',' + d.y.toFixed(2) + ')', cx: p[0], cy: p[1], w, u, s: d.s, water });
      }
      if (d.t === 'rock' && vis(p, 60)) rocks.push({ x: p[0], y: p[1], r: .17 * u * d.s / 2 });
    }
    for (const s of world.slimes.values()){ if (s.zone !== z || s.dead) continue; const p = SP(s.x, s.y).slice();
      if (vis(p, 40)) slimes.push({ x: p[0], y: p[1], r: Math.max(8, typeof SLIME_SCALE === 'function' ? s.r * SLIME_SCALE() : s.r * 72 * ZK() * 2) }); }
    return { zone: z, trees, rocks, slimes, W, H }; },
  npcSpots: () => NPC_DEFS.filter(d => d.zone === ses.myZone).map(d => ({ name: d.name, x: d.x, y: d.y })),
  labelWatch: () => ({ names: [prog().name, ...NPC_DEFS.filter(d => d.zone === ses.myZone).map(d => d.name)],
    tags: ['ELITE', 'METAL', 'SLIME EMPEROR', 'CHAOS EMPEROR', ...Object.values(GUARDIANS).map(g => g.name)] }),
  canvasSize: () => ({ w: cv.width, h: cv.height }),
};
})();
</script>`;

const server = http.createServer((req, res) => {
  const p = path.join(REPO, decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html');
  fs.readFile(p, (e, buf) => { if (e){ res.writeHead(404); res.end(); return; } res.writeHead(200, { 'content-type': MIME[path.extname(p)] || 'application/octet-stream' }); res.end(buf); });
});
let PORT;
const report = { when: new Date().toISOString(), repo: REPO, out: OUT, errors: [], frames: [], checks: {} };

async function basePage(browser, { w = 390, h = 844, dsf = 2 } = {}){
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: dsf, isMobile: w < 600, hasTouch: w < 600 });
  const page = await ctx.newPage();
  page.on('pageerror', e => report.errors.push(String(e).slice(0, 300)));
  page.on('console', m => { if (m.type() === 'error' && !/Failed to load resource|WebSocket|ERR_/.test(m.text())) report.errors.push('console: ' + m.text().slice(0, 300)); });
  await page.route('**/trystero@0.21.6/**', r => r.fulfill({ status: 200, contentType: 'text/javascript', body: STUB }));
  await page.route('**/zustand@5.1.0/**', r => r.fulfill({ status: 200, contentType: 'text/javascript', body: ZUSTAND }));
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  await page.route(`http://localhost:${PORT}/`, async r => {
    let html = fs.readFileSync(path.join(REPO, 'index.html'), 'utf8');
    html = html.replace('</script>', EXPOSE);
    html = html.replace('<script type="module">', `<script>localStorage.removeItem('slimeslash-save-v1');</script><script type="module">`);
    r.fulfill({ status: 200, contentType: 'text/html', body: html });
  });
  await page.goto(`http://localhost:${PORT}/`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__G, null, { timeout: 20000 });
  return { ctx, page };
}
const G = (page, fn, ...a) => page.evaluate(fn, ...a);
async function waitFor(page, fn, timeout = 15000, label = 'cond'){
  const t0 = Date.now();
  while (Date.now() - t0 < timeout){ if (await G(page, fn)) return true; await page.waitForTimeout(150); }
  throw new Error('timeout waiting: ' + label);
}
async function shot(page, name){
  await page.screenshot({ path: path.join(OUT, name + '.png') });
  report.frames.push(name + '.png');
}
async function captureTexts(page){
  await G(page, () => new Promise(res => { window.__texts.length = 0; requestAnimationFrame(() => requestAnimationFrame(() => res(1))); }));
  return G(page, () => window.__texts.slice());
}

/* ---------- label (name plate / ELITE tag) screen-rect check ---------- */
function textRect(e){
  if (Math.abs(e.b) > 0.02 || Math.abs(e.c) > 0.02) return null;      // rotated draw — not a plate
  const X = e.a * e.x + e.c * e.y + e.e, Y = e.b * e.x + e.d * e.y + e.f;
  const wDev = e.w * Math.abs(e.a);
  const fontPx = parseFloat((/([0-9.]+)px/.exec(e.font) || [0, 12])[1]);
  const fh = fontPx * Math.abs(e.d);
  let l, r, t, b;
  if (e.align === 'center'){ l = X - wDev / 2; r = X + wDev / 2; }
  else if (e.align === 'right' || e.align === 'end'){ l = X - wDev; r = X; }
  else { l = X; r = X + wDev; }
  if (e.base === 'middle'){ t = Y - fh / 2; b = Y + fh / 2; }
  else { t = Y - fh * 0.85; b = Y + fh * 0.25; }
  // plate-backed labels (NPC names, ELITE, boss plates): the drawn plate
  // is wider/taller than the glyph box — expand to the plate's true rect
  if (fontPx <= 8){ l -= 5 * Math.abs(e.a); r += 5 * Math.abs(e.a); t -= 3 * Math.abs(e.d); b += 3 * Math.abs(e.d); }
  else if (fontPx <= 11){ l -= 7 * Math.abs(e.a); r += 7 * Math.abs(e.a); t -= 3.5 * Math.abs(e.d); b += 3.5 * Math.abs(e.d); }
  return { l, t, r, b };
}
function checkLabels(captures){
  const violations = [], found = {};
  let checked = 0, offscreenIgnored = 0;
  for (const cap of captures){
    const watch = new Set([...cap.watch.names, ...cap.watch.tags]);
    const seen = new Set();
    for (const e of cap.texts){
      if (!watch.has(e.t) || seen.has(e.t + '@' + Math.round(e.x) + ',' + Math.round(e.y))) continue;
      seen.add(e.t + '@' + Math.round(e.x) + ',' + Math.round(e.y));
      const rc = textRect(e);
      if (!rc) continue;
      /* A plate belonging to an off-screen entity is drawn off-screen —
         it is not "rendered clipped", it is not rendered at all. The
         basics violation is a plate that INTERSECTS the viewport but is
         not fully contained by it (Handler's cut-off METAL tag). */
      const intersects = rc.r > 0 && rc.l < cap.canvas.w && rc.b > 0 && rc.t < cap.canvas.h;
      if (!intersects){ offscreenIgnored++; continue; }
      checked++;
      found[e.t] = (found[e.t] || 0) + 1;
      if (rc.l < -1 || rc.t < -1 || rc.r > cap.canvas.w + 1 || rc.b > cap.canvas.h + 1)
        violations.push({ frame: cap.frame, text: e.t, rect: { l: +rc.l.toFixed(1), t: +rc.t.toFixed(1), r: +rc.r.toFixed(1), b: +rc.b.toFixed(1) }, canvas: cap.canvas });
    }
  }
  return { pass: violations.length === 0, checked, found, violations, offscreenIgnored };
}

/* ---------- HUD cluster overlap (DOM, main world) ---------- */
async function hudRects(page){
  return page.evaluate(() => {
    /* LEAF controls only. Containers (#rackDock, #items) are wide
       transparent boxes whose rects cross other clusters without any
       visible element touching — container intersections are reported
       as a note, never a failure. */
    const ids = ['#coinBadge', '#lvlBadge', '#questCard', '#itemPotion', '#itemBomb', '#itemShield', '#menuBtn', '#rackTab', '#rack', '#minimap', '#pauseBtn'];
    const containers = ['#rackDock', '#items'];
    const info = ['#peerBadge', '#boardBadge', '#shareBtn'];
    const grab = (id) => { const el = document.querySelector(id); if (!el) return null;
      const r = el.getBoundingClientRect(), cs = getComputedStyle(el);
      return { id, x: r.x, y: r.y, w: r.width, h: r.height, visible: r.width > 0 && r.height > 0 && cs.display !== 'none' && cs.visibility !== 'hidden' }; };
    return { clusters: ids.map(grab), containers: containers.map(grab), info: info.map(grab) };
  });
}
function overlaps(list){
  const vis = list.filter(c => c && c.visible);
  const out = [];
  for (let i = 0; i < vis.length; i++) for (let j = i + 1; j < vis.length; j++){
    const a = vis[i], b = vis[j];
    const ow = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
    const oh = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
    if (ow > HUD_MAX_OVERLAP_PX && oh > HUD_MAX_OVERLAP_PX) out.push({ a: a.id, b: b.id, overlapW: +ow.toFixed(1), overlapH: +oh.toFixed(1) });
  }
  return out;
}
function hudCheck(h){
  const intersections = overlaps(h.clusters);
  return { pass: intersections.length === 0, clusters: h.clusters, info: h.info, intersections,
    containerNote: { rects: h.containers, intersections: overlaps([...h.containers, ...h.clusters]),
      note: 'container boxes (#rackDock/#items) are transparent layout boxes; their intersections are listed for information only — the FAIL set is the visible leaf controls above.' },
    excludedByDesign: ['#interactPrompt (transient)', '#bossBar (fight-only)', '#chapterCard (story overlay)', '#toaster (transient toasts)', '#comboBadge (transient)', 'coach chip (canvas, transient)'] };
}

/* ---------- tree shadow: source assertion ---------- */
function fnBody(src, name){
  const i = src.indexOf('function ' + name + '(');
  if (i < 0) return null;
  let j = src.indexOf('{', i), depth = 0;
  for (let k = j; k < src.length; k++){
    if (src[k] === '{') depth++;
    else if (src[k] === '}'){ depth--; if (depth === 0) return src.slice(j, k + 1); }
  }
  return null;
}
function treeSourceCheck(){
  const src = fs.readFileSync(path.join(REPO, 'index.html'), 'utf8');
  const out = {};
  for (const fn of ['drawTree', 'drawDeadTree']){
    const body = fnBody(src, fn);
    out[fn] = body === null ? { found: false } : {
      found: true,
      ellipseCall: /\.ellipse\s*\(/.test(body),
      shadowFill: /rgba\(38,32,40/.test(body),
    };
    out[fn].pass = !!out[fn].found && !out[fn].ellipseCall && !out[fn].shadowFill;
  }
  return { pass: out.drawTree.pass && out.drawDeadTree.pass, functions: out };
}

/* ---------- prop audit (python ground truth) ---------- */
function runPropAudit(){
  const script = path.join(REPO, 'tools', 'prop_audit.py');
  if (!fs.existsSync(script)) return { ran: false, reason: 'tools/prop_audit.py not present in this tree' };
  let txt;
  try { txt = execFileSync('python3', [script], { cwd: REPO, timeout: 300000 }).toString(); }
  catch (e){ return { ran: false, reason: 'prop_audit.py failed: ' + String(e.message).slice(0, 200) }; }
  const after = {}; let totalChecked = 0;
  for (const m of txt.matchAll(/^([a-z]+)\s+checked=\s*(\d+).*after: on-road=(\d+) in-water=(\d+)/gm))
    after[m[1]] = { checked: +m[2], onRoad: +m[3], inWater: +m[4] };
  const total = /TOTAL\s+checked=(\d+)/.exec(txt); if (total) totalChecked = +total[1];
  const hp = txt.split('HAND-PLACED SET PIECES')[1] || '';
  const setOnRoad = {};
  for (const m of hp.matchAll(/!!\s+([a-z]+)\s+(\S+)\s+\([\d.]+,[\d.]+\)\s+sits on road/g)){
    setOnRoad[m[1]] = setOnRoad[m[1]] || []; setOnRoad[m[1]].push(m[2]);
  }
  const scattered = {}; let scatRoad = 0, scatWater = 0;
  for (const z of Object.keys(after)){
    const sp = (setOnRoad[z] || []).length;
    scattered[z] = { onRoad: after[z].onRoad - sp, inWater: after[z].inWater, setPiecesOnRoad: setOnRoad[z] || [] };
    scatRoad += scattered[z].onRoad; scatWater += scattered[z].inWater;
  }
  return { ran: true, totalChecked, after, scattered, scatteredOnRoad: scatRoad, scatteredInWater: scatWater,
    mirrorCaveat: 'prop_audit.py MIRRORS the game generator and verifies against full-res plate discs; the live probe in this gate reads the game\'s actual PROPS + its persistent block grids. The two must agree.' };
}

/* ---------- one viewport's battery ---------- */
async function runViewport(browser, cfg){
  const tag = cfg.w < 600 ? 'portrait' : 'desktop';
  const data = { tag, sword: null, labelCaptures: [], treeScenes: [], hud: null, crops: [] };
  const { ctx, page } = await basePage(browser, cfg);
  await page.waitForTimeout(4500);                                   // title diorama settles (frozen ~2.6s)
  await shot(page, 'title-' + tag);
  await page.evaluate(() => document.querySelector('#playBtn').click());
  await page.waitForTimeout(700);
  for (let i = 0; i < 4; i++){ await G(page, () => window.__G.interact()); await page.waitForTimeout(180); }
  await G(page, () => window.__G.god());
  await waitFor(page, () => window.__G.propsReady(), 25000, 'props ready').catch(() => {});
  await waitFor(page, () => window.__G.census() >= 300, 20000, 'glade stocked').catch(() => {});
  // altar clearing, at rest — sword probe + frame + crop anchor
  await G(page, () => window.__drive([{ x: 10.3, y: 7.3, pxs: 200 }]));
  await waitFor(page, () => { const m = window.__G.mePos(); return Math.hypot(m.x - 10.3, m.y - 7.3) < .4; }, 20000, 'altar arrival').catch(() => {});
  await G(page, () => window.__stopDrive());
  await page.waitForTimeout(1200);
  data.sword = await G(page, () => window.__G.swordProbe());
  await shot(page, 'altar-rest-' + tag);
  const meScr = await G(page, () => window.__G.meScreen());
  data.crops.push({ src: path.join(OUT, 'altar-rest-' + tag + '.png'), out: path.join(OUT, 'sword-crop-' + tag + '.png'),
    cx: meScr.x * cfg.dsf, cy: meScr.y * cfg.dsf, w: 640, h: 520 });
  if (tag === 'portrait') data.hud = await hudRects(page);
  // glade crowd — walked in, labels captured on the living frame
  await G(page, () => window.__drive([{ x: 3.2, y: 10.5, pxs: 200 }]));
  await waitFor(page, () => { const m = window.__G.mePos(); return Math.hypot(m.x - 3.2, m.y - 10.5) < .4; }, 25000, 'crowd arrival').catch(() => {});
  await G(page, () => window.__stopDrive());
  await page.waitForTimeout(600);
  data.labelCaptures.push({ frame: 'crowd-' + tag, texts: await captureTexts(page), watch: await G(page, () => window.__G.labelWatch()), canvas: await G(page, () => window.__G.canvasSize()) });
  await shot(page, 'crowd-' + tag);
  await page.waitForTimeout(4000);                                   // stress: let the pack fully converge on the player
  await shot(page, 'crowd-dense-' + tag);
  data.treeScenes.push({ frame: 'crowd-' + tag, dsf: cfg.dsf, player: await G(page, () => window.__G.meScreen()), ...(await G(page, () => window.__G.treesOnScreen())) });
  // town — NPC plates need proximity: visit an NPC after the wide shot
  const tp = await G(page, () => window.__G.townPos());
  await G(page, (p) => window.__G.travel('town', p.x, p.y + .1), tp);
  await waitFor(page, () => window.__G.probe().zone === 'town', 10000, 'in town').catch(() => {});
  await page.waitForTimeout(1800);
  await shot(page, 'town-' + tag);
  data.treeScenes.push({ frame: 'town-' + tag, dsf: cfg.dsf, player: await G(page, () => window.__G.meScreen()), ...(await G(page, () => window.__G.treesOnScreen())) });
  const npcs = await G(page, () => window.__G.npcSpots());
  if (npcs.length){
    await G(page, (n) => window.__G.teleport(n.x + .35, n.y + .35), npcs[0]);
    await page.waitForTimeout(600);
    data.labelCaptures.push({ frame: 'town-npc-' + tag, texts: await captureTexts(page), watch: await G(page, () => window.__G.labelWatch()), canvas: await G(page, () => window.__G.canvasSize()) });
    await shot(page, 'town-npc-' + tag);
  }
  // grove — two viewpoints: clean-tree yield from one view is marginal
  await G(page, () => window.__G.travel('grove', 7.2, 7.2));
  await waitFor(page, () => window.__G.probe().zone === 'grove', 10000, 'in grove').catch(() => {});
  await page.waitForTimeout(2500);
  await shot(page, 'grove-' + tag);
  data.treeScenes.push({ frame: 'grove-' + tag, dsf: cfg.dsf, player: await G(page, () => window.__G.meScreen()), ...(await G(page, () => window.__G.treesOnScreen())) });
  await G(page, () => window.__G.teleport(11.4, 11.6));
  await page.waitForTimeout(700);                                    // sample before the local slimes wander into the columns
  await shot(page, 'grove2-' + tag);
  data.treeScenes.push({ frame: 'grove2-' + tag, dsf: cfg.dsf, player: await G(page, () => window.__G.meScreen()), ...(await G(page, () => window.__G.treesOnScreen())) });
  data.props = await G(page, () => window.__G.propsAudit());
  data.version = (await G(page, () => window.__G.probe())).version;
  await ctx.close();
  return data;
}

/* ---------- main ---------- */
(async () => {
  await new Promise(r => server.listen(0, r));
  PORT = server.address().port;
  const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
  const P = await runViewport(browser, { w: 390, h: 844, dsf: 2 });
  const D = await runViewport(browser, { w: 1920, h: 1080, dsf: 1 });
  await browser.close();
  server.close();
  report.version = P.version || D.version;

  /* checks */
  const C = report.checks;
  C.pageErrors = { pass: report.errors.length === 0, count: report.errors.length, errors: [...new Set(report.errors)] };
  C.sword = { pass: [P, D].every(v => v.sword && v.sword.reachPx >= SWORD_MIN_REACH_PX),
    minReachPx: SWORD_MIN_REACH_PX,
    portrait: P.sword, desktop: D.sword };
  // props: live probe (real PROPS + persistent grids) AND python ground truth
  const liveBad = [];
  for (const v of [P, D]) if (v.props) for (const z of Object.keys(v.props)){
    for (const p of v.props[z].onRoad) liveBad.push({ viewport: v.tag, zone: z, kind: 'road', ...p });
    for (const p of v.props[z].inWater) liveBad.push({ viewport: v.tag, zone: z, kind: 'water', ...p });
  }
  const audit = runPropAudit();
  C.props = { pass: liveBad.length === 0 && audit.ran && audit.scatteredOnRoad === 0 && audit.scatteredInWater === 0,
    liveViolations: liveBad, live: P.props || D.props, audit };
  C.hud = hudCheck(P.hud);
  C.hud.desktopInfo = D.hud ? hudCheck(D.hud) : null;
  C.labels = checkLabels([...P.labelCaptures, ...D.labelCaptures]);

  /* pixel work: tree strips (first scene yielding >=3 valid trees),
     crowd ground fraction, sword crops, contact sheet */
  const runPixels = (jobsObj, suffix) => {
    const jp = path.join(OUT, 'pixel-jobs' + suffix + '.json');
    fs.writeFileSync(jp, JSON.stringify(jobsObj, null, 2));
    return JSON.parse(execFileSync('python3', [path.join(__dirname, 'pixels.py'), jp], { timeout: 300000 }).toString());
  };
  const scenes = [...P.treeScenes, ...D.treeScenes];
  const order = ['town', 'grove', 'grove2', 'crowd'];
  scenes.sort((a, b) => order.indexOf(a.frame.split('-')[0]) - order.indexOf(b.frame.split('-')[0]));
  let treeFrame = { sceneUsed: null, trees: null, pass: false };
  const pooled = [];
  for (const s of scenes){
    /* the sampled column is narrow (x +- .25*w, y base..base+42):
       exclude only what intersects THAT column */
    const box = (t) => ({ x0: t.cx - .25 * t.w, x1: t.cx + .25 * t.w, y0: t.cy + .03 * t.u, y1: t.cy + .03 * t.u + 42 });
    const reasons = {};
    const clean = s.trees.filter(t => {
      const why = (r) => { reasons[r] = (reasons[r] || 0) + 1; return false; };
      if (t.water) return why('water');                // strip footprint over water reads dark — not a shadow
      const b = box(t);
      if (s.rocks.some(r => r.x + r.r > b.x0 && r.x - r.r < b.x1 && r.y + r.r > b.y0 && r.y - r.r < b.y1)) return why('rock');
      if (s.slimes && s.slimes.some(sl => sl.x + sl.r > b.x0 - 6 && sl.x - sl.r < b.x1 + 6 && sl.y + sl.r > b.y0 - 6 && sl.y - sl.r < b.y1 + 6)) return why('slime');
      if (s.player && s.player.x > b.x0 - 30 && s.player.x < b.x1 + 30 && s.player.y > b.y0 - 30 && s.player.y < b.y1 + 30) return why('player');
      /* another tree's canopy/trunk falling into the sampled column */
      for (const o of s.trees){ if (o === t) continue;
        const oTop = o.cy + .03 * o.u - o.w * 1.14, oBot = o.cy + .03 * o.u;
        if (o.cx + o.w / 2 > b.x0 && o.cx - o.w / 2 < b.x1 && oBot > b.y0 && oTop < b.y1) return why('tree-overlap'); }
      return true;
    });
    treeFrame.sceneAttempts = [...(treeFrame.sceneAttempts || []), { frame: s.frame, candidates: s.trees.length, clean: clean.length, excluded: reasons }];
    if (!clean.length) continue;
    /* clean trees are scarce per view (iso trees are huge) — POOL the
       valid per-tree dips across every scene; the dip is a within-
       column ratio, comparable across frames and viewports */
    let res = null;
    try { res = runPixels({ trees: { frame: path.join(OUT, s.frame + '.png'), dsf: s.dsf, trees: clean.slice(0, 8) } }, '-trees-' + s.frame); } catch (e){ report.pixelError = String(e.message).slice(0, 300); }
    const valid = res && res.trees ? res.trees.filter(t => t.dip !== null) : [];
    for (const t of valid) pooled.push({ frame: s.frame, ...t });
    treeFrame.pooledFrom = [...(treeFrame.pooledFrom || []), { frame: s.frame, clean: clean.length, valid: valid.length }];
    if (pooled.length >= 6) break;
  }
  if (pooled.length >= 1){
    const dips = pooled.map(t => t.dip).sort((a, b) => a - b);
    treeFrame.trees = pooled;
    treeFrame.minDip = dips[0];
    treeFrame.medianDip = dips[Math.floor(dips.length / 2)];
    /* per-tree baseline verdict: the dip is plate-biased per tree, so
       compare each sampled tree against its own baseline from the
       verified shadowless build (tree-baseline.json beside this file) */
    let baseline = {};
    try { baseline = JSON.parse(fs.readFileSync(path.join(__dirname, 'tree-baseline.json'), 'utf8')).trees || {}; } catch (e){}
    const matched = pooled.filter(t => baseline[t.id] !== undefined)
      .map(t => ({ id: t.id, dip: t.dip, baseline: baseline[t.id], delta: +(t.dip - baseline[t.id]).toFixed(4) }));
    const deltas = matched.map(m => m.delta).sort((a, b) => a - b);
    const medianDelta = deltas.length ? deltas[Math.floor(deltas.length / 2)] : null;
    treeFrame.baseline = { matched, medianDelta, minDelta: deltas.length ? deltas[0] : null,
      medianTol: TREE_MEDIAN_TOL, grossTol: TREE_GROSS_TOL };
    treeFrame.pass = matched.length >= TREE_MIN_MATCHED && medianDelta >= -TREE_MEDIAN_TOL && deltas[0] >= -TREE_GROSS_TOL;
  }
  C.trees = { source: treeSourceCheck(), frame: treeFrame, pass: false };
  C.trees.pass = C.trees.source.pass && treeFrame.pass;

  const carpetPath = path.join(process.env.HOME, 'workspace', 'gauntlet-archive', 'transplant', '30-glade-altar-clean.png');
  const jobs = { crops: [...P.crops, ...D.crops],
    sword: { portrait: { frame: path.join(OUT, 'altar-rest-portrait.png'), dsf: 2, grip: P.sword.grip, tip: P.sword.tip },
             desktop: { frame: path.join(OUT, 'altar-rest-desktop.png'), dsf: 1, grip: D.sword.grip, tip: D.sword.tip } },
    crowd: { portrait: path.join(OUT, 'crowd-portrait.png'), desktop: path.join(OUT, 'crowd-desktop.png'),
      densePortrait: path.join(OUT, 'crowd-dense-portrait.png'), denseDesktop: path.join(OUT, 'crowd-dense-desktop.png'),
      carpet: fs.existsSync(carpetPath) ? carpetPath : null },
    montage: { out: path.join(OUT, 'contact-sheet.png'), cols: 3, cellW: 620,
      items: ['title-portrait', 'altar-rest-portrait', 'sword-crop-portrait', 'crowd-portrait', 'town-portrait', 'grove-portrait', 'title-desktop', 'crowd-desktop', 'town-desktop']
        .map(n => ({ path: path.join(OUT, n + '.png'), label: n })) } };
  let px = {};
  try { px = runPixels(jobs, ''); } catch (e){ report.pixelError = String(e.message).slice(0, 300); }

  /* sword: the geometry probe alone is blind to draw-path bugs (on
     v0.6.5 it read full reach while the blade rendered zero-length) —
     the pass requires the RENDERED blade in the rest frame too. */
  C.sword.rendered = px.sword || null;
  C.sword.bladeMin = SWORD_BLADE_MIN;
  C.sword.pass = C.sword.pass && !!(px.sword && px.sword.portrait && px.sword.desktop &&
    px.sword.portrait.bladeFraction >= SWORD_BLADE_MIN && px.sword.desktop.bladeFraction >= SWORD_BLADE_MIN);

  const crowd = px.crowd || {};
  const cMean = (a, b) => (a && b) ? +(((a.fraction + b.fraction) / 2)).toFixed(4) : null;
  const crowdMeans = { portrait: cMean(crowd.portrait, crowd.densePortrait), desktop: cMean(crowd.desktop, crowd.denseDesktop) };
  C.crowd = { floors: { portraitMean: CROWD_P_MEAN, portraitMin: CROWD_P_MIN, desktopMean: CROWD_D_MEAN, desktopMin: CROWD_D_MIN },
    portrait: crowd.portrait || null, desktop: crowd.desktop || null,
    densePortrait: crowd.densePortrait || null, denseDesktop: crowd.denseDesktop || null,
    means: crowdMeans, carpetReference: crowd.carpet || null,
    pass: !!(crowdMeans.portrait !== null && crowdMeans.desktop !== null &&
      crowdMeans.portrait >= CROWD_P_MEAN && Math.min(crowd.portrait.fraction, crowd.densePortrait.fraction) >= CROWD_P_MIN &&
      crowdMeans.desktop >= CROWD_D_MEAN && Math.min(crowd.desktop.fraction, crowd.denseDesktop.fraction) >= CROWD_D_MIN) };

  report.contactSheet = fs.existsSync(path.join(OUT, 'contact-sheet.png')) ? 'contact-sheet.png' : null;
  fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(report, null, 2));

  const line = (name, c, extra) => console.log((c.pass ? 'PASS' : 'FAIL') + '  ' + name + (extra ? '  — ' + extra : ''));
  line('page-errors', C.pageErrors, C.pageErrors.count + ' errors');
  line('sword-visible-at-rest', C.sword, 'reachPx portrait=' + (P.sword && P.sword.reachPx.toFixed(1)) + ' desktop=' + (D.sword && D.sword.reachPx.toFixed(1)) + ' (min ' + SWORD_MIN_REACH_PX + '), rendered blade fraction portrait=' + (px.sword && px.sword.portrait && px.sword.portrait.bladeFraction) + ' desktop=' + (px.sword && px.sword.desktop && px.sword.desktop.bladeFraction) + ' (min ' + SWORD_BLADE_MIN + ')');
  line('trees-no-shadow', C.trees, 'source ' + (C.trees.source.pass ? 'clean' : 'DIRTY') + ', frame: pooled ' + (treeFrame.trees ? treeFrame.trees.length : 0) + ' trees, baseline-matched ' + (treeFrame.baseline ? treeFrame.baseline.matched.length : 0) + ', median delta ' + (treeFrame.baseline ? treeFrame.baseline.medianDelta : 'n/a') + ', min delta ' + (treeFrame.baseline ? treeFrame.baseline.minDelta : 'n/a') + ' (tols -' + TREE_MEDIAN_TOL + '/-' + TREE_GROSS_TOL + ')');
  line('props-off-road-and-water', C.props, 'live violations=' + liveBad.length + ', audit scattered on-road=' + (audit.ran ? audit.scatteredOnRoad : 'n/a') + ' in-water=' + (audit.ran ? audit.scatteredInWater : 'n/a'));
  line('hud-no-overlap@390x844', C.hud, C.hud.intersections.length + ' leaf intersections');
  line('labels-on-screen', C.labels, C.labels.checked + ' plates checked, ' + C.labels.violations.length + ' violations');
  line('crowd-ground-visible', C.crowd, 'ground-fraction mean portrait=' + crowdMeans.portrait + ' desktop=' + crowdMeans.desktop + ' (samples p ' + (crowd.portrait && crowd.portrait.fraction) + '/' + (crowd.densePortrait && crowd.densePortrait.fraction) + ', d ' + (crowd.desktop && crowd.desktop.fraction) + '/' + (crowd.denseDesktop && crowd.denseDesktop.fraction) + '; v0.6.0 carpet ref=' + (crowd.carpet && crowd.carpet.fraction) + ')');
  const fails = Object.values(C).filter(c => !c.pass).length;
  console.log(fails === 0 ? 'GATE: GREEN — all checks pass' : 'GATE: RED — ' + fails + ' check(s) failed');
  console.log('artefacts: ' + OUT);
  process.exit(fails === 0 ? 0 : 1);
})().catch(e => { console.error('GATE HARNESS FAIL', e); process.exit(2); });
