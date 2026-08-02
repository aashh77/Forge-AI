import { AbortSignal } from 'node:abort-controller';

const base = process.env.TEST_BASE_URL || 'http://localhost:3000';
const timeout = 5000;

async function fetchWithTimeout(url, options = {}) {
  const signal = AbortSignal.timeout(timeout);
  return fetch(url, { ...options, signal });
}

const fuzzPayloads = [
  { path: '/cart/add', method: 'POST', body: { productId: '!!!', quantity: 'many' } },
  { path: '/cart/add', method: 'POST', body: { productId: 12345, quantity: -5 } },
  { path: '/cart/add', method: 'POST', body: { productId: null, quantity: 1 } },
  { path: '/catalogue', method: 'GET', body: null },
  { path: '/cart', method: 'GET', body: null }
];

(async () => {
  for (const p of fuzzPayloads) {
    const url = `${base}${p.path}`;
    const options = {
      method: p.method,
      headers: { 'Content-Type': 'application/json' }
    };
    if (p.body !== null && p.body !== undefined) {
      options.body = JSON.stringify(p.body);
    }
    try {
      const res = await fetchWithTimeout(url, options);
      console.log(`Fuzz ${p.method} ${p.path} -> ${res.status}`);
    } catch (e) {
      console.log(`Fuzz ${p.method} ${p.path} -> error: ${e.message}`);
    }
  }
})();