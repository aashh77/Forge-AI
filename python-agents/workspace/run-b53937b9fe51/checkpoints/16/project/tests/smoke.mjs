import { AbortSignal } from 'node:abort-controller';

const base = process.env.TEST_BASE_URL || 'http://localhost:3000';
const timeout = 5000;

async function fetchWithTimeout(url, options = {}) {
  const signal = AbortSignal.timeout(timeout);
  return fetch(url, { ...options, signal });
}

async function assert(condition, message) {
  if (!condition) {
    console.error(`FAIL: ${message}`);
    process.exitCode = 1;
  } else {
    console.log(`PASS: ${message}`);
  }
}

(async () => {
  // 1. GET /catalogue
  let res = await fetchWithTimeout(`${base}/catalogue`);
  await assert(res.ok, 'GET /catalogue returns 200');
  let catalogue = await res.json();
  await assert(Array.isArray(catalogue), 'Catalogue is an array');

  // 2. POST /cart/add with valid product
  const product = catalogue[0];
  const addBody = { productId: product.id, quantity: 1 };
  res = await fetchWithTimeout(`${base}/cart/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(addBody),
  });
  await assert(res.ok, 'POST /cart/add with valid product returns 200');

  // 3. GET /cart contains the item
  res = await fetchWithTimeout(`${base}/cart`);
  await assert(res.ok, 'GET /cart returns 200');
  let cart = await res.json();
  const added = cart.items?.find(i => i.productId === product.id);
  await assert(added, 'Cart contains added product');

  // Edge case 1: POST /cart/add missing quantity
  const badBody1 = { productId: product.id };
  res = await fetchWithTimeout(`${base}/cart/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(badBody1),
  });
  await assert(!res.ok, 'POST /cart/add missing quantity returns error');

  // Edge case 2: POST /cart/add invalid productId
  const badBody2 = { productId: 'nonexistent', quantity: 1 };
  res = await fetchWithTimeout(`${base}/cart/add`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(badBody2),
  });
  await assert(!res.ok, 'POST /cart/add invalid productId returns error');

  // Edge case 3: GET /cart when empty (clear cart first)
  // Assuming an endpoint to clear cart for testing
  await fetchWithTimeout(`${base}/cart/clear`, { method: 'POST' });
  res = await fetchWithTimeout(`${base}/cart`);
  await assert(res.ok, 'GET /cart after clear returns 200');
  cart = await res.json();
  await assert(Array.isArray(cart.items) && cart.items.length === 0, 'Cart is empty after clear');
})();