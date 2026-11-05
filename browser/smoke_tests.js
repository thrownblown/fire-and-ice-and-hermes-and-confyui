// jsdom smoke test for the Tests tab: does each clip render its VERBATIM PROMPT beside the video?
// Alex's standing ask ("the page must show the prompt next to the video"), so this asserts it and
// also asserts the prompt is the take's OWN text — not a neighbouring take's.
//   node browser/smoke_tests.js
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const dom = new JSDOM(html, { runScripts: 'outside-only', url: 'http://x/browser/index.html?view=tests&run=T0017' });
const win = dom.window;

win.Element.prototype.scrollIntoView = function () {};
win.HTMLMediaElement.prototype.load = function () {};
win.HTMLMediaElement.prototype.play = function () { return Promise.resolve(); };

for (const f of ['shot-browser-data.js', 'setups-data.js', 'sweep-data.js', 'yolo-data.js', 'project-data.js', 'voice-data.js']) {
  const p = path.join(__dirname, f);
  if (fs.existsSync(p)) win.eval(fs.readFileSync(p, 'utf8'));
}
for (const f of ['../refs/refs-data.js', '../runs/testruns-data.js']) {
  const p = path.join(__dirname, f);
  if (fs.existsSync(p)) win.eval(fs.readFileSync(p, 'utf8'));
}

const inline = html.match(/<script>([\s\S]*)<\/script>/)[1];
win.eval(inline);

const detail = win.document.getElementById('detail');
const d = detail ? detail.innerHTML : '';
const prompts = detail ? detail.querySelectorAll('.rc-prompt pre').length : 0;

const checks = [
  ['tests view rendered something', d.length > 500],
  ['T0017 heading present', d.includes('T0017')],
  ['at least one clip prompt rendered in a <pre>', prompts >= 1],
  ['prompt panel carries provenance', /prompt · <span class="mono">/.test(d) || d.includes('prompt ·')],
  ['c01 prompt text is present', d.includes('You have done well, my son.')],
  ['c01 prompt names both subjects', d.includes('&lt;Subject 1&gt; is JULIANA') && d.includes('&lt;Subject 2&gt; is NEKRON')],
  ['c01 prompt keeps all three shots', d.includes('[Shot 3]')],
  ['provenance points at the take graph', d.includes('graphs/S03-c01_audioOnly_t01.json')],
  ['the per-shot presence clause is NOT in T0017 take 1 (it was a later experiment)',
    !d.includes('On screen in this shot')],
];

let pass = 0;
for (const [name, ok] of checks) {
  console.log((ok ? 'PASS  ' : 'FAIL  ') + name);
  if (ok) pass++;
}
console.log(`\n${pass}/${checks.length} checks passed · ${prompts} prompt panel(s) rendered`);
process.exit(pass === checks.length ? 0 : 1);
