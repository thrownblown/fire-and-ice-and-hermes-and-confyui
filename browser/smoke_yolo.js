// jsdom smoke test for the yolo view (skill: local-file-spa).
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const dom = new JSDOM(html, { runScripts: 'outside-only', url: 'http://x/browser/index.html?view=yolo' });
const win = dom.window;

// stub media + scroll before eval
win.Element.prototype.scrollIntoView = function () {};
win.HTMLMediaElement.prototype.load = function () {};
win.HTMLMediaElement.prototype.play = function () { return Promise.resolve(); };

// real baked data first
for (const f of ['shot-browser-data.js', 'setups-data.js', 'sweep-data.js', 'yolo-data.js', 'project-data.js', 'voice-data.js']) {
  const p = path.join(__dirname, f);
  if (fs.existsSync(p)) win.eval(fs.readFileSync(p, 'utf8'));
}
for (const f of ['../refs/refs-data.js', '../runs/testruns-data.js']) {
  const p = path.join(__dirname, f);
  if (fs.existsSync(p)) win.eval(fs.readFileSync(p, 'utf8'));
}

// then the inline script
const inline = html.match(/<script>([\s\S]*)<\/script>/)[1];
win.eval(inline);

const detail = win.document.getElementById('detail').innerHTML;
const list = win.document.getElementById('list').innerHTML;
const checks = {
  'tab count set': win.document.getElementById('nYolo').textContent.length > 0,
  'list has items': list.includes('item'),
  'VIDEO badge in list': list.includes('VIDEO'),
  'detail has video tag': detail.includes('<video'),
  'detail has prompt': detail.includes('Prompt (verbatim'),
  'detail has refs section': detail.includes('Refs consumed'),
  'sheet img present': detail.includes('refs/characters/'),
  'prompt text present': detail.includes('subject_definitions'),
  'deep link kept view': win.location.search.includes('yolo'),
};
let bad = 0;
for (const [k, v] of Object.entries(checks)) {
  console.log((v ? 'PASS' : 'FAIL'), k);
  if (!v) bad++;
}
if (bad) { console.log('\n--- detail head ---\n', detail.slice(0, 600)); process.exit(1); }
console.log('ALL SMOKE CHECKS PASS');
