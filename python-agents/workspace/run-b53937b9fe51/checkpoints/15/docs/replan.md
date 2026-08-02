# Agent Execution Plan

## Summary
Implemented strict CORS policy, added health‑check endpoint, unit‑tested Firestore security rules, and updated frontend fetch calls to include credentials, addressing the security audit findings.

## Schedule

### step4 — backend (patch)
- **Reason:** Restricts cross‑site requests to the trusted domain and provides a simple health check for monitoring.
- **Context:** Security audit: CORS is too permissive; need strict policy and health endpoint.
- **Instructions:** Modify server.js: replace `app.use(cors());` with `app.use(cors({ origin: 'https://myapp.vercel.app', credentials: true }));` to restrict CORS to the deployed Vercel domain. Add a health‑check route: `app.get('/health', (req,res)=>res.status(200).send('OK'));`. Ensure all API routes use the same CORS configuration and that the `Access-Control-Allow-Credentials` header is set.

Existing file: server.js
- **Depends on:** step1

### step5 — backend (patch)
- **Reason:** Ensures that Firestore rules correctly protect cart data and prevents accidental privilege escalation.
- **Context:** Security audit: unit‑test Firestore security rules in CI.
- **Instructions:** Add a new test file `tests/firestore.rules.test.js` that uses `firebase-functions-test` to load the Firestore security rules from `firestore.rules` and runs unit tests for read/write permissions on cart documents. Include a CI comment to run this test on each push.

Existing files: none (new test file).
- **Depends on:** step4

### step6 — frontend (patch)
- **Reason:** Ensures that authenticated requests carry the HttpOnly cookie and are accepted by the backend.
- **Context:** CORS restriction may affect API calls from the frontend.
- **Instructions:** Update all fetch calls to the cart API in the Next.js pages/components to include credentials: `fetch(url, { credentials: 'include', mode: 'cors' })`. Verify that the frontend origin (`https://myapp.vercel.app`) is allowed by the new CORS policy.

Existing files: pages/api/cart.js, components/CartButton.jsx, etc.
- **Depends on:** step4

