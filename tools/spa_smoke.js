/* Headless smoke test for the FNI shot browser.
 *
 * The browser tool cannot drive 127.0.0.1, so this is the runtime verification path:
 *   1. extract every INLINE <script> from browser/index.html and syntax-check it;
 *   2. eval those plus the real browser/*data.js files inside a vm context with a minimal
 *      DOM stub (getElementById returns inert elements, history.pushState rewrites
 *      location.search so the URL-state router still works);
 *   3. drive the router to the views that were just added and assert the rendered HTML
 *      contains their markers.
 *
 *   node tools/spa_smoke.js
 */
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const B = 'E:/FNI/browser/';
const html = fs.readFileSync(B + 'index.html', 'utf8');

// ---- 1. inline scripts -------------------------------------------------------------------
const inline = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
console.log('inline <script> blocks:', inline.length, inline.map(s => s.length).join(', '));
const code = inline.join('\n;\n');
try {
  new vm.Script(code, { filename: 'inline.js' });
  console.log('PASS  syntax check (vm.Script)');
} catch (e) {
  console.log('FAIL  syntax:', e.message);
  process.exit(1);
}

// ---- 2. DOM stub -------------------------------------------------------------------------
function el(id) {
  const e = {
    id, className: '', textContent: '', innerHTML: '', value: '', placeholder: '',
    style: {}, children: [], onclick: null, oninput: null, onkeydown: null, dataset: {},
    clientWidth: 800, clientHeight: 600, scrollTop: 0,
    appendChild(c) { this.children.push(c); return c; },
    removeChild(c) { return c; },
    setAttribute() {}, getAttribute() { return null; }, removeAttribute() {},
    addEventListener() {}, removeEventListener() {}, focus() {}, blur() {},
    scrollIntoView() {}, insertBefore(c) { return c; },
    querySelector() { return null; }, querySelectorAll() { return []; },
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
  };
  return e;
}
const els = {};
const getEl = id => (els[id] = els[id] || el(id));

const loc = { search: '?view=shots', pathname: '/browser/index.html', href: 'http://x/browser/index.html', hash: '' };
const search = new URLSearchParams('view=shots');
const history = {
  pushState(_s, _t, url) { if (url && url.indexOf('?') >= 0) { search.delete('view'); new URLSearchParams(url.split('?')[1]).forEach((v, k) => { search.delete(k); search.set(k, v); }); loc.search = '?' + search.toString(); } },
  replaceState(_s, _t, url) { this.pushState(null, null, url); },
  back() {}, forward() {},
};

const ctx = {
  console,
  URLSearchParams,
  setTimeout, clearTimeout, setInterval, clearInterval,
  document: {
    getElementById: getEl,
    createElement: () => el('_new'),
    querySelectorAll: () => [],
    querySelector: () => null,
    addEventListener() {},
    body: el('body'),
    documentElement: el('html'),
    activeElement: null,
  },
  location: loc,
  history,
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  navigator: { userAgent: 'node' },
  addEventListener() {}, removeEventListener() {},
};
ctx.window = ctx;
ctx.globalThis = ctx;
vm.createContext(ctx);

// ---- 3. load the real data + the app -----------------------------------------------------
for (const f of ['shot-browser-data.js', 'project-data.js', 'setups-data.js', 'sweep-data.js',
                 'testruns-data.js', 'voice-data.js', 'yolo-data.js', 'yolo2-data.js']) {
  const p = B + f;
  if (!fs.existsSync(p)) { console.log('  (missing data file, skipped):', f); continue; }
  try {
    vm.runInContext(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''), ctx, { filename: f });
  } catch (e) {
    console.log('FAIL  loading', f, e.message);
    process.exit(1);
  }
}
console.log('PASS  data files loaded (incl. yolo2-data.js)');

try {
  vm.runInContext(code, ctx, { filename: 'inline.js' });
  console.log('PASS  app evaluated under the stub (no ReferenceError)');
} catch (e) {
  console.log('FAIL  app eval:', e.message);
  process.exit(1);
}

// ---- 4. boot each view FROM ITS URL (that is how the SPA actually starts) ----------------
const DATA = ['shot-browser-data.js', 'project-data.js', 'setups-data.js', 'sweep-data.js',
              'voice-data.js', 'yolo-data.js', 'yolo2-data.js'];
const DATA_EXTRA = [['E:/FNI/runs/testruns-data.js', 'runs/testruns-data.js']];

function bootWith(query) {
  const c = Object.assign({}, ctx);
  c.document = Object.assign({}, ctx.document);
  c.location = { search: query, pathname: '/browser/index.html', href: 'http://x/browser/index.html', hash: '' };
  c.history = { pushState(_s, _t, url) {
      if (url && url.indexOf('?') >= 0) c.location.search = '?' + url.split('?')[1];
    }, replaceState(_s, _t, url) { if (url && url.indexOf('?') >= 0) c.location.search = '?' + url.split('?')[1]; }, back() {}, forward() {} };
  const box = {};                                  // this boot's elements
  c.document.getElementById = id => (box[id] = box[id] || el(id));
  c.window = c; c.globalThis = c;
  vm.createContext(c);
  for (const f of DATA) {
    const p = B + f;
    if (fs.existsSync(p)) vm.runInContext(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''), c, { filename: f });
  }
  for (const [p, name] of DATA_EXTRA) {
    if (fs.existsSync(p)) vm.runInContext(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''), c, { filename: name });
  }
  vm.runInContext(code, c, { filename: 'inline.js' });
  return ((box.detail || {}).innerHTML || '') + '\n' + ((box.list || {}).innerHTML || '');
}

const checks = [
  ['?view=yolo2&yolo=G01-c01', 'Render passes'],
  ['?view=yolo2&yolo=G01-c01', 'VLM read'],
  ['?view=yolo', 'yolo'],
  ['?view=shots', ''],
  ['?view=setups', ''],
  ['?view=tests', ''],
];
let bad = 0;
for (const [q, want] of checks) {
  let out = '';
  try {
    out = bootWith(q);
  } catch (e) {
    console.log('FAIL  boot ' + q + ' threw: ' + e.message);
    bad++;
    continue;
  }
  const hit = !want || out.indexOf(want) >= 0;
  console.log((hit ? 'PASS  ' : 'FAIL  ') + q + ' renders ' + out.length + ' chars' +
              (want ? (hit ? ' and contains "' + want + '"' : ' but LACKS "' + want + '"') : ''));
  if (!hit) bad++;
}
console.log(bad ? 'SUMMARY: ' + bad + ' failure(s)' : 'SUMMARY: all checks passed');
