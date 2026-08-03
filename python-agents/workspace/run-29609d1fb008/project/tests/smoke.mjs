const base = process.env.TEST_BASE_URL || 'http://localhost:3000';
const timeout = AbortSignal.timeout(5000);
await fetch(`${base}/`, { signal: timeout });
console.log('PASS');