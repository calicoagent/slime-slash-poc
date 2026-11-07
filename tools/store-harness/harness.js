// Headless harness for the Slime Slash zustand store refactor.
// Works on BOTH the pre-refactor build and the store build (adapter below),
// so old/new can be compared on the same seeded scenario.
//
// usage: node harness.js <repoDir> <label> <mode> [fixture.json]   (npm i playwright-core@1.56 first)
//   boot   REAL imports (Trystero + zustand from the CDN, nothing stubbed):
//          zero page errors, title renders, PLAY enters the world.
//   perf   12 s Warhammer move-and-fight at 4x CPU throttle (Trystero stubbed
//          the same way as the 3558c73-era harness; zustand REAL).
//   func   save/load + scripted progress actions; prints the saves written.
//   ui     menu/Sphere/pause/sound/rack click-through, then the save it leaves.
//   reload loads the given fixture save, saves again (round-trip check).
// FREEZE=1 deep-freezes progress after every set(): any in-place progress write throws.
const http = require('http'), fs = require('fs'), path = require('path');
const { chromium } = require('playwright-core');

const [,, repoDir, label = 'run', mode = 'perf', fixtureArg] = process.argv;
const MIME = { '.html':'text/html', '.js':'text/javascript', '.png':'image/png', '.json':'application/json', '.mp3':'audio/mpeg', '.svg':'image/svg+xml', '.webp':'image/webp', '.mp4':'video/mp4' };
const server = http.createServer((req, res) => {
  const p = path.join(repoDir, decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html');
  fs.readFile(p, (e, buf) => { if (e){ res.writeHead(404); res.end(); return; } res.writeHead(200, { 'content-type': MIME[path.extname(p)] || 'application/octet-stream' }); res.end(buf); });
});

const STUB = `
export const selfId = 'aaaa-self';
export function joinRoom(){
  window.__sent = {}; window.__bytes = {};
  return {
    onPeerJoin(f){ window.__pj = f; }, onPeerLeave(f){ window.__pl = f; },
    makeAction(t){
      return [ (d)=>{ const s = JSON.stringify(d); new TextEncoder().encode(s);
                     window.__sent[t]=(window.__sent[t]||0)+1; window.__bytes[t]=(window.__bytes[t]||0)+s.length; return Promise.resolve(); },
               (f)=>{ (window.__on = window.__on || {})[t] = f; } ];
    } };
}`;
// Adapter: same API over the old module-level state and the new store.
const EXPOSE = `
;(()=>{ const __wp = worldPayload; window.__wpCalls = 0; worldPayload = function(){ window.__wpCalls++; return __wp(); };
const NEW = typeof store !== 'undefined';
window.__T = { NEW, me, spawnSlime, hostApplyHit, gainXp, saveGame, loadGame, equip, doHit, myDamage, onKillFx, buyItem, buySpherePoint,
  socketGem, unsocketGem, craftWeapon, resetRun, useItem, grantGem, gainWxp,
  store: NEW ? store : null,
  get prog(){ return NEW ? store.getState().progress : null; },
  get kills(){ const p = NEW && store.getState().progress; return p ? p.kills : me.kills; },
  get level(){ const p = NEW && store.getState().progress; return p ? p.level : me.level; },
  get slimes(){ return NEW ? store.getState().world.slimes : slimes; },
  get started(){ return NEW && typeof ses !== 'undefined' ? ses.started : started; } }; })();
</script>`;

const DEFAULT_FIXTURE = path.join(__dirname, 'fixture-handler.json');
const OUT = process.env.OUT || require('os').tmpdir();   // screenshots land here, never in the repo

(async () => {
  await new Promise(r => server.listen(0, r));
  const port = server.address().port;
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport:{ width:390, height:844 }, deviceScaleFactor:3 });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  const relayErrors = []; page.on('console', m => { if (m.type()!=='error' || /Failed to load resource/.test(m.text())) return; if (/^WebSocket connection to 'wss:/.test(m.text())) relayErrors.push(m.text()); else errors.push('console: ' + m.text()); });
  const cdnLoads = [];
  page.on('response', r => { if (/cdn\.jsdelivr\.net/.test(r.url())) cdnLoads.push(r.status() + ' ' + r.url()); });
  if (mode !== 'boot') await page.route('**/trystero@0.21.6/**', r => r.fulfill({ status:200, contentType:'text/javascript', body:STUB }));
  if (!process.env.FONTS && mode !== 'boot') await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
  if (mode !== 'boot') await page.route(`http://localhost:${port}/`, async r => {
    const html = fs.readFileSync(path.join(repoDir, 'index.html'), 'utf8');
    const i = html.lastIndexOf('</script>');
    r.fulfill({ status:200, contentType:'text/html', body: html.slice(0, i) + EXPOSE + html.slice(i + 9) });
  });
  const fixture = mode === 'boot' ? null : JSON.parse(fs.readFileSync(fixtureArg || DEFAULT_FIXTURE, 'utf8'));
  await page.addInitScript(save => {
    let a = 1234567; Math.random = () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
    if (save && !sessionStorage.getItem('__seeded')){ localStorage.setItem('slimeslash-save-v1', JSON.stringify(save)); sessionStorage.setItem('__seeded', '1'); }
  }, fixture);
  await page.goto(`http://localhost:${port}/`);
  const out = { label, mode, errors };

  if (mode === 'boot'){
    await page.waitForSelector('#playBtn', { state:'visible', timeout:20000 });
    await page.waitForTimeout(1500);
    out.titleVisible = await page.isVisible('#title');
    await page.screenshot({ path: path.join(OUT, label + '-title.png') });
    await page.click('#playBtn', { force:true });
    await page.waitForTimeout(4000);
    out.afterPlay = await page.evaluate(() => ({ titleHidden: document.querySelector('#title').classList.contains('hidden'),
      hudShown: !document.querySelector('#hud').classList.contains('hidden'),
      toast: [...document.querySelectorAll('#toasts > *')].map(e => e.textContent).slice(0, 3) }));
    await page.screenshot({ path: path.join(OUT, label + '-world.png') });
    out.cdnLoads = cdnLoads; out.relayWsErrors = relayErrors.length;
    console.log(JSON.stringify(out, null, 1));
    await browser.close(); server.close(); return;
  }

  await page.waitForFunction(() => window.__T);
  if (process.env.FREEZE) out.freeze = await page.evaluate(() => {
    // Instrumentation only: deep-freeze progress after every set(), so any
    // in-place write to progress throws (module code is strict mode).
    const T = window.__T; if (!T.NEW) return 'n/a';
    const deep = o => { if (!o || typeof o !== 'object' || Object.isFrozen(o)) return o;
      if (o instanceof Set || o instanceof Map){ for (const k of ['add','delete','clear','set']) if (o[k]) o[k] = () => { throw new TypeError('progress ' + o.constructor.name + '.' + k + ' mutated in place'); }; }
      Object.freeze(o); for (const v of Object.values(o)) deep(v); if (o instanceof Set) for (const v of o) deep(v); return o; };
    deep(T.store.getState().progress); window.__freezes = 0;
    T.store.subscribe(s => { deep(s.progress); window.__freezes++; });
    return 'on'; });
  const reseed = () => page.evaluate(() => { let a = 42; Math.random = () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; });
  const readSave = () => page.evaluate(() => localStorage.getItem('slimeslash-save-v1'));
  out.preload = await readSave();   // what is on disk before PLAY (the fixture as written)
  await page.click('#playBtn', { force:true });
  await page.waitForTimeout(800);

  if (mode === 'perf'){
    const cdp = await ctx.newCDPSession(page);
    await cdp.send('Performance.enable');
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: +(process.env.THROTTLE||4) });
    await page.evaluate(() => { window.__gaps = []; let last = performance.now(); const f = t => { window.__gaps.push(t - last); last = t; if (window.__rec) requestAnimationFrame(f); }; window.__rec = true; requestAnimationFrame(f);
      window.__T.equip(5); window.__kills0 = window.__T.kills; window.__wpCalls = 0; window.__sent = {}; window.__bytes = {};
      window.__ls = 0; const si = Storage.prototype.setItem; Storage.prototype.setItem = function(k, v){ window.__ls++; return si.call(this, k, v); }; });
    const m0 = Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(m => [m.name, m.value]));
    const t0 = Date.now();
    let i = 0;
    while (Date.now() - t0 < 12000){
      if (i % 12 === 0) await page.evaluate(() => { const T = window.__T; for (let k=0;k<6;k++) T.spawnSlime({ kind: k%3 ? 'mid' : 'big', x: T.me.x + (Math.random()-.5)*.2, y: T.me.y + (Math.random()-.5)*.2 }); });
      const a = i * .55, cx = 195 + Math.cos(a) * 110, cy = 420 + Math.sin(a * 1.3) * 160;
      await page.mouse.move(cx, cy, { steps: 3 });
      i++;
    }
    const m1 = Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(m => [m.name, m.value]));
    const r = await page.evaluate(() => { window.__rec = false; const g = window.__gaps.slice(5).sort((a,b)=>a-b); const q = p => +g[Math.floor(p*(g.length-1))].toFixed(1);
      return { frames:g.length, p50:q(.5), p95:q(.95), p99:q(.99), max:+g[g.length-1].toFixed(1), kills:window.__T.kills - window.__kills0,
               worldPayloadCalls:window.__wpCalls, sends:window.__sent, localStorageWrites:window.__ls, slimes:window.__T.slimes.size }; });
    await page.screenshot({ path: path.join(OUT, label + '-fight.png') });
    Object.assign(out, r, { wallMs: Date.now() - t0, taskSec: +(m1.TaskDuration - m0.TaskDuration).toFixed(2), scriptSec: +(m1.ScriptDuration - m0.ScriptDuration).toFixed(2), layoutSec: +(m1.LayoutDuration - m0.LayoutDuration).toFixed(3), heapMB: +(m1.JSHeapUsedSize/1048576).toFixed(1) });
    delete out.preload;
  }

  if (mode === 'func' || mode === 'reload'){
    // 1. load -> save with nothing changed: what the build writes for this fixture
    await page.evaluate(() => window.__T.saveGame());
    out.loadSave = await readSave();
  }
  if (mode === 'ui'){
    // click-through of the menus/panels/settings that write progress or session UI state
    const k = key => page.keyboard.press(key), w = ms => page.waitForTimeout(ms);
    await k('f'); await w(300);                       // Sphere tab (marks the sphere hint)
    out.sphereOpen = await page.evaluate(() => !document.querySelector('#forge').classList.contains('hidden'));
    for (const id of ['#szIn', '#szOut', '#szIn']) if (await page.$(id)) { await page.click(id, { force:true }); await w(80); }
    // select every available-looking node in turn and press the card button: unlocks what 4 SP can buy
    out.unlockClicks = await page.evaluate(() => { let c = 0; for (const d of [...document.querySelectorAll('#sphereNodes > *')]){ d.onclick && d.onclick(); const b = document.querySelector('#ncBtn'); if (b && !b.disabled){ b.click(); c++; } } return c; });
    await k('Escape'); await w(200);
    await k('Escape'); await w(200);                  // pause menu
    out.pauseOpen = await page.evaluate(() => !document.querySelector('#pauseMenu').classList.contains('hidden'));
    await page.click('#soundBtn', { force:true }); await w(100);
    out.soundLabel = await page.evaluate(() => document.querySelector('#soundBtn').textContent);
    await k('Escape'); await w(200);
    for (const key of ['1','2','6','2']){ await k(key); await w(120); }
    await page.click('#rackTab', { force:true }); await w(100);
    await page.evaluate(() => window.__T.saveGame());
    out.uiSave = await readSave();
  }
  if (mode === 'func'){
    // 2. a deterministic scripted session through the real UI handlers / functions
    await reseed();
    out.steps = await page.evaluate(() => {
      const T = window.__T, log = [], $ = s => document.querySelector(s);
      const snap = tag => { T.saveGame(); log.push([tag, localStorage.getItem('slimeslash-save-v1')]); };
      $('#depBtn').click(); snap('deposit');
      $('#wdBtn').click(); snap('withdraw');
      T.buyItem('potion'); T.buyItem('bomb'); snap('buyItems');
      T.me.hp = 10; T.useItem('potion'); snap('usePotion');
      T.equip(2); snap('equip2');
      T.gainXp(12000); snap('gainXp');
      T.gainWxp(2, 700); snap('gainWxp');
      T.grantGem(1, T.me.x, T.me.y); snap('grantGem');
      T.equip(1); T.unsocketGem('gB'); snap('unsocket');
      T.socketGem('gB'); snap('socket');
      T.buySpherePoint(); snap('buySP');
      T.craftWeapon(3); snap('craft3');
      // kill rewards through the real path (my kill: coins, kills, MP, weapon XP, bounty, gems, combo)
      for (let k = 0; k < 4; k++) T.onKillFx({ id:'x'+k, x:T.me.x, y:T.me.y, c:'#7ee787', by:T.me.id, coins:20, xp:34, kind:'mid', elite:false, r:.03 });
      snap('kills');
      T.onKillFx({ id:'kb', x:T.me.x, y:T.me.y, c:'#ffe066', by:T.me.id, coins:400, xp:800, kind:'king', elite:false, r:.06 }); snap('kingKill');
      return log;
    });
    out.hpInSave = /"(hp|mp|maxHp|maxMp)"/.test(await readSave());
    // 3. pagehide persists state changed since the last throttled save
    out.pagehide = await page.evaluate(() => { const T = window.__T;
      if (T.NEW && T.store.getState().patchProgress) T.store.getState().patchProgress({ coins: 777777 }); else T.me.coins = 777777;
      window.dispatchEvent(new Event('pagehide')); return JSON.parse(localStorage.getItem('slimeslash-save-v1')).coins; });
    // 4. RESET SAVE through the pause menu's reset path
    await reseed();
    out.afterReset = await page.evaluate(() => { const T = window.__T; T.resetRun(); const gone = localStorage.getItem('slimeslash-save-v1');
      T.saveGame(); return { removed: gone === null, save: localStorage.getItem('slimeslash-save-v1') }; });
  }
  if (process.env.FREEZE) out.freezes = await page.evaluate(() => window.__freezes);
  console.log(JSON.stringify(out));
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
