# Backend Datastore Justification

**Chosen:** JSON-file store

## Justification
A JSON-file store keeps all cart and catalogue data on the developer’s local machine, eliminating the need for any external paid or networked infrastructure. It’s simple to set up, fully file‑based, and works out of the box on a localhost environment.

## CTQ (Critical To Quality)
- Data persistence across browser sessions
- Concurrent read/write safety
- Schema flexibility for cart items

## Alternatives Considered
- **SQLite** — rejected because SQLite is file‑based but adds a heavier dependency and is overkill for a simple cart; a plain JSON file is lighter and easier to manage for this use case.
- **In‑memory store (e.g., Map or Redis‑like in‑memory DB)** — rejected because Data would be lost on page reload or server restart, defeating persistence requirements.
