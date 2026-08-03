const base = process.env.TEST_BASE_URL || 'http://localhost:3000';
const timeout = AbortSignal.timeout(5000);
const tests = [
  { path: '/', method: 'GET' },
  { path: '/?q=abc', method: 'GET' },
  { path: '/nonexistent', method: 'GET' },
  { path: '/', method: 'POST', body: { foo: 'bar' } },
  { path: '/', method: 'PUT', body: { a: 1 } }
];
for (const t of tests) {
  const url = `${base}${t.path}`;
  const options = { method: t.method, signal: timeout };
  if (t.body) {
    options.headers = { 'Content-Type': 'application/json' };
    options.body = JSON.stringify(t.body);
  }
  await fetch(url, options);
}
console.log('PASS');