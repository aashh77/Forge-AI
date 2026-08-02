/* Fallback fuzz test generated because LLM test generation failed or timed out. */
const BASE = (process.env.TEST_BASE_URL || "http://localhost:4100").replace(/\/$/, "");
const TIMEOUT_MS = 8000;
const PAYLOADS = [
  { path: "/api/health", method: "GET", body: null },
  { path: "/", method: "GET", body: null },
  { path: "/api/health", method: "POST", body: { fuzz: true } },
  { path: "/nonexistent-fuzz-path", method: "GET", body: null },
];

async function main() {
  for (const p of PAYLOADS) {
    const url = `${BASE}${p.path}`;
    try {
      const opts = { method: p.method, signal: AbortSignal.timeout(TIMEOUT_MS) };
      if (p.body !== null) opts.body = JSON.stringify(p.body);
      const res = await fetch(url, opts);
      console.log(`FUZZ ${p.method} ${p.path} -> ${res.status}`);
    } catch (err) {
      console.log(`FUZZ ${p.method} ${p.path} -> ERROR: ${err.message}`);
    }
  }
}

main();
