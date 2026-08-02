/* Fallback smoke test generated because LLM test generation failed or timed out. */
const BASE = (process.env.TEST_BASE_URL || "http://localhost:4100").replace(/\/$/, "");
const TIMEOUT_MS = 10000;
let failed = false;

async function check(name, method, path, expectStatus) {
  const url = `${BASE}${path}`;
  try {
    const res = await fetch(url, { method, signal: AbortSignal.timeout(TIMEOUT_MS) });
    const ok = expectStatus ? res.status === expectStatus : res.status < 500;
    console.log(`${ok ? "PASS" : "FAIL"}: ${method} ${path} -> ${res.status}`);
    if (!ok) failed = true;
  } catch (err) {
    console.log(`FAIL: ${method} ${path} -> ${err.message}`);
    failed = true;
  }
}

async function main() {
  await check("root", "GET", "/", null);
  await check("health", "GET", "/api/health", 200);
  if (failed) process.exitCode = 1;
}

main();
