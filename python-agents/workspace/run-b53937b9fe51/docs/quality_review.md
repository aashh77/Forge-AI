# Code Quality Review

**Score:** 35/100

## Summary
The current codebase is incomplete and lacks critical components such as a backend server, API routes, and a finished front‑end. There is duplicated data, inconsistent identifiers, and missing error handling, security, and persistence. Additionally, project documentation, linting, testing, and packaging are absent. A comprehensive rewrite is required to bring the project to a functional, maintainable state.

## Issues
- **[MAJOR] server.js** — Missing server implementation. The package.json references a server.js file as the main entry point, but no such file exists, preventing the application from running.
  Recommendation: Create a server.js file that sets up an Express server, serves static files from the public directory, and provides API endpoints for retrieving the catalogue and managing the cart.
- **[MAJOR] server.js** — Missing API routes for cart operations. There are no endpoints to add items to the cart, retrieve the cart contents, or clear the cart.
  Recommendation: Implement RESTful routes such as POST /cart/add, GET /cart, and DELETE /cart/clear, with proper request validation and error handling.
- **[MAJOR] server.js** — No error handling or input validation in the backend. This can lead to unhandled exceptions and security vulnerabilities.
  Recommendation: Add middleware for error handling, validate request bodies (e.g., using Joi or express-validator), and sanitize inputs to prevent injection attacks.
- **[MAJOR] server.js** — No security measures such as CORS configuration, rate limiting, or helmet usage.
  Recommendation: Use the cors package to restrict origins, add helmet for HTTP headers, and consider express-rate-limit to mitigate abuse.
- **[MODERATE] public/app.js** — Duplicate data between data.json and the coffees array in app.js. This leads to maintenance overhead and potential inconsistencies.
  Recommendation: Remove the hardcoded coffees array and fetch the catalogue from the backend (e.g., GET /catalogue) to keep a single source of truth.
- **[MODERATE] public/app.js** — Inconsistent ID types: data.json uses string IDs like "coffee1", while app.js uses numeric IDs.
  Recommendation: Standardize IDs to be strings or numbers across the entire codebase and update all references accordingly.
- **[MODERATE] public/app.js** — Front‑end code is incomplete and truncated. Event listeners for adding to cart, rendering the catalogue, and updating the cart count are missing.
  Recommendation: Finish the implementation: render the catalogue items, attach click handlers to add-to-cart buttons, update the cart count, and persist the cart in localStorage or via API.
- **[MINOR] public/app.js** — Hardcoded image URLs from picsum.photos. These may change or become unavailable, breaking the UI.
  Recommendation: Use a stable image source or host images locally; consider adding fallback images.
- **[MINOR] public/app.js** — No persistence of cart state. The cart is stored only in memory and will be lost on page reload.
  Recommendation: Persist the cart in localStorage or send it to the backend to maintain state across sessions.
- **[MINOR] public/app.js** — Missing CSS and responsive design. The UI will not look good on different screen sizes.
  Recommendation: Add a CSS file or use a framework like Bootstrap to style the catalogue and cart elements responsively.
- **[MINOR] public/app.js** — No accessibility features (e.g., ARIA labels, keyboard navigation).
  Recommendation: Add appropriate ARIA attributes and ensure interactive elements are keyboard‑accessible.
- **[MINOR] package.json** — Missing scripts for linting, testing, and building.
  Recommendation: Add scripts such as "lint": "eslint .", "test": "vitest", and a build step if using a bundler.
- **[MINOR] README.md** — No README file to explain project setup, usage, and contribution guidelines.
  Recommendation: Create a README.md with installation steps, API documentation, and contribution instructions.
- **[MINOR] .gitignore** — No .gitignore file. This may expose node_modules, logs, and other unnecessary files to the repository.
  Recommendation: Add a standard .gitignore for Node.js projects.
- **[MINOR] LICENSE** — No license specified. The code's usage rights are unclear.
  Recommendation: Add an MIT or similar license file.
