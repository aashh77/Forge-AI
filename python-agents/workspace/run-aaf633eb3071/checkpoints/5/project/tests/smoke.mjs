#!/usr/bin/env node
const base = process.env.TEST_BASE_URL || 'http://localhost:3000';
let failCount = 0;

async function testHello() {
  try {
    const res = await fetch(base, {signal: AbortSignal.timeout(5000)});
    if (res.status !== 200) {
      console.log(`FAIL: GET / returned status ${res.status}`);
      failCount++;
      return;
    }
    const text = await res.text();
    if (!text.includes('Hello World')) {
      console.log('FAIL: GET / does not contain "Hello World"');
      failCount++;
      return;
    }
    console.log('PASS: GET / contains Hello World');
  } catch (e) {
    console.log(`FAIL: GET / threw ${e}`);
    failCount++;
  }
}

async function testNotFound() {
  try {
    const res = await fetch(`${base}/nonexistent`, {signal: AbortSignal.timeout(5000)});
    if (res.status !== 404) {
      console.log(`FAIL: GET /nonexistent returned status ${res.status}`);
      failCount++;
      return;
    }
    console.log('PASS: GET /nonexistent returned 404');
  } catch (e) {
    console.log(`FAIL: GET /nonexistent threw ${e}`);
    failCount++;
  }
}

async function testBurstEmptyBody() {
  try {
    const res = await fetch(`${base}/burst`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({}),
      signal: AbortSignal.timeout(5000),
    });
    if (res.status !== 400 && res.status !== 200) {
      console.log(`FAIL: POST /burst with empty body returned status ${res.status}`);
      failCount++;
      return;
    }
    console.log(`PASS: POST /burst with empty body returned status ${res.status}`);
  } catch (e) {
    console.log(`FAIL: POST /burst with empty body threw ${e}`);
    failCount++;
  }
}

(async () => {
  await testHello();
  await testNotFound();
  await testBurstEmptyBody();
  if (failCount > 0) {
    process.exitCode = 1;
  }
})();