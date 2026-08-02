# QA Report

## Edge Cases Considered
- GET /nonexistent returns 404
- POST /burst with empty body returns 400

## Fuzz Payloads
```json
[
  {
    "path": "/burst",
    "method": "POST",
    "body": {
      "action": "burst"
    }
  },
  {
    "path": "/burst",
    "method": "POST",
    "body": {
      "foo": "bar"
    }
  },
  {
    "path": "/burst",
    "method": "POST",
    "body": {
      "x": null
    }
  },
  {
    "path": "/burst",
    "method": "POST",
    "body": {
      "y": "string"
    }
  },
  {
    "path": "/nonexistent",
    "method": "GET"
  }
]
```
