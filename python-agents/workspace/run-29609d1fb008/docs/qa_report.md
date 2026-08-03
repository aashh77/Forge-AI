# QA Report

## Edge Cases Considered
- /
- /?query=1
- /nonexistent
- 

## Fuzz Payloads
```json
[
  {
    "path": "/",
    "method": "GET",
    "body": {}
  },
  {
    "path": "/?q=abc",
    "method": "GET",
    "body": {}
  },
  {
    "path": "/nonexistent",
    "method": "GET",
    "body": {}
  },
  {
    "path": "/",
    "method": "POST",
    "body": {
      "foo": "bar"
    }
  },
  {
    "path": "/",
    "method": "PUT",
    "body": {
      "a": 1
    }
  }
]
```
