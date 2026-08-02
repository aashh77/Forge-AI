# QA Report

## Edge Cases Considered
- POST /cart/add missing quantity
- POST /cart/add invalid productId
- GET /cart when empty after clear

## Fuzz Payloads
```json
[
  {
    "path": "/cart/add",
    "method": "POST",
    "body": {
      "productId": "!!!",
      "quantity": "many"
    }
  },
  {
    "path": "/cart/add",
    "method": "POST",
    "body": {
      "productId": 12345,
      "quantity": -5
    }
  },
  {
    "path": "/cart/add",
    "method": "POST",
    "body": {
      "productId": null,
      "quantity": 1
    }
  },
  {
    "path": "/catalogue",
    "method": "GET",
    "body": null
  },
  {
    "path": "/cart",
    "method": "GET",
    "body": null
  }
]
```
