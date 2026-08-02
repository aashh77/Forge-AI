# Backend Implementation Summary

## Routes
- `GET /api/health` — Health check returning status ok
- `GET /api/catalogue` — Return list of coffee items
- `POST /api/cart/add` — Add an item to the cart
- `GET /api/cart` — Retrieve current cart contents
- `DELETE /api/cart/remove` — Remove an item from the cart
- `POST /api/cart/clear` — Clear all items from the cart

## Business Logic
The backend uses a simple JSON file (data.json) to persist catalogue and cart data. On each request the file is read into memory, modified, and written back. Catalogue items are static and served via GET /api/catalogue. Cart operations (add, view, remove, clear) manipulate an array of items stored under the "cart" key. The server exposes a health endpoint, serves static files from the public folder, and listens on the configured port. This setup allows a local coffee catalogue web page to add items to a cart and view the cart without external dependencies.
