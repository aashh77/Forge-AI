# Backend Datastore Justification

**Chosen:** PostgreSQL

## Justification
The chosen full‑stack REST API architecture requires a relational database to store products, cart items, and user sessions. PostgreSQL offers robust ACID compliance, advanced query capabilities, and is the default database for Prisma. It can be run locally via Docker or a native installation, ensuring the developer’s localhost can host the service without external paid infrastructure.

## CTQ (Critical To Quality)
- What type of database is required for the architecture?
- Why is PostgreSQL suitable for this use case?
- How does PostgreSQL integrate with Prisma and Express?
- What are the local deployment options for PostgreSQL?

## Alternatives Considered
- **SQLite** — rejected because SQLite is file‑based and would simplify local development, but it lacks certain PostgreSQL features (e.g., advanced concurrency, full JSON support, and robust replication) that the architecture may need for future scaling and complex queries.
- **MySQL** — rejected because MySQL is a viable relational database, but the project’s ORM (Prisma) defaults to PostgreSQL for many advanced features, and the chosen stack already presumes PostgreSQL.
