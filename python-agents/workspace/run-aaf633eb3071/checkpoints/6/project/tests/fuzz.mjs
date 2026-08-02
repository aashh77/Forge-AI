#!/usr/bin/env node
const base = process.env.TEST_BASE_URL || 'http://localhost:3000';
const fuzzPayloads = [
  {path: '/burst', method: 'POST', body: {action: 'burst'}},
  {path: '/burst', method: 'POST', body: {foo: 'bar'}},
  {path: '/burst', method: 'POST', body: {x: null}},
  {path: '/burst', method: 'POST', body: {y: 'string'}},
  {path: '/nonexistent', method: 'GET'},
];

(async () => {
  for (const payload of fuzzPayloads) {
    const url = base + payload.path;
    const options = {
      method: payload.method,
      headers: {'Content-Type': 'application/json'},
      signal: AbortSignal.timeout(5000),
    };
    if (payload.body !== undefined) {
      options.body = JSON.stringify(payload.body);
    }
    try {
      const res = await fetch(url, options);
      console.log(`FUZZ: ${payload.method} ${payload.path} -> ${res.status}`);
    } catch (e) {
      console.log(`FUZZ: ${payload.method} ${payload.path} -> error ${e}`);
    }
  }
})();