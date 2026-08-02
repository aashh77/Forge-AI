# Agent Execution Plan

## Summary
Implemented a safe JSON parsing routine for the cart in app.js to eliminate crashes on initial load.

## Schedule

### step6 — frontend (patch)
- **Reason:** Prevent crash on first load due to null or malformed localStorage data.
- **Context:** Frontend cart handling
- **Instructions:** In public/app.js, replace the line that parses the cart from localStorage with a safe version:

```js
const cartData = localStorage.getItem(CART_KEY);
let cart = [];
try {
  cart = cartData ? JSON.parse(cartData) : [];
} catch (e) {
  console.warn('Invalid cart data in localStorage', e);
  cart = [];
}
```

This change ensures that if the stored value is null or contains invalid JSON, the application will not crash and will default to an empty cart.
- **Depends on:** step5

