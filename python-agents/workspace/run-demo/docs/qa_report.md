# QA Report

## Edge Cases Considered
- Root URL returns a successful response.
- Health endpoint responds with HTTP 200 and JSON `{ status: "ok" }`.
- Static assets (CSS and JS) are served with correct MIME types.
- Page is readable on a 320px-wide viewport.
- JavaScript enhancement fails gracefully when scripts are blocked.

## Fuzz Payloads
```json
[
  { "path": "/", "method": "GET", "body": null },
  { "path": "/api/health", "method": "GET", "body": null },
  { "path": "/styles.css", "method": "GET", "body": null },
  { "path": "/app.js", "method": "GET", "body": null },
  { "path": "/nonexistent", "method": "GET", "body": null }
]
```
