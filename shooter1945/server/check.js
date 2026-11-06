// 정적 검사(CI): server.js 와 web/*.html 안의 <script> 가 문법 오류 없이 컴파일되는지 확인한다.
// 실행: node check.js [web 폴더]   (Docker 빌드 중에도 실행되어, 문법 오류가 있으면 이미지 빌드가 실패한다)
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const webDir = path.resolve(process.argv[2] || path.join(__dirname, '..', 'web'));
let failed = 0;
function compile(name, code) {
  try { new vm.Script(code, { filename: name }); console.log('OK   ' + name); }
  catch (e) { failed++; console.error('FAIL ' + name + ': ' + e.message); }
}

compile('server.js', fs.readFileSync(path.join(__dirname, 'server.js'), 'utf8').replace(/^#!.*/, ''));
for (const f of fs.readdirSync(webDir).filter(n => n.endsWith('.html'))) {
  const html = fs.readFileSync(path.join(webDir, f), 'utf8');
  const re = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/gi;
  let m, i = 0;
  while ((m = re.exec(html))) compile(`${f} <script #${++i}>`, m[1]);
  if (!i) console.log('--   ' + f + ' (인라인 스크립트 없음)');
}
if (failed) { console.error(failed + '개 파일에서 문법 오류'); process.exit(1); }
console.log('모든 검사 통과');
