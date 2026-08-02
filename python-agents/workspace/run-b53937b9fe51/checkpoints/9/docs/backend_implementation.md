# Backend Implementation Summary

## Routes
- `GET /api/health` — Health check endpoint returning status ok
- `GET /api/products` — Retrieve list of coffee products
- `POST /api/auth/register` — Register a new user and return JWT
- `POST /api/auth/login` — Authenticate user and return JWT
- `POST /api/cart/add` — Add a product to the authenticated user's cart
- `GET /api/cart` — Retrieve the authenticated user's cart items with product details

## Business Logic
The backend provides a secure REST API for a coffee catalogue. Users can register and login to receive a JWT. Authenticated routes allow adding products to a cart and retrieving the cart. Products, users, and cart items are persisted in PostgreSQL via Prisma. The API serves static files from the public folder and includes a health check endpoint.
