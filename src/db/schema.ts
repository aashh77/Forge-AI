import { jsonb, pgTable, text, timestamp } from "drizzle-orm/pg-core";

// Primary history table for Forge AI runs. The Python agent engine remains the
// source of truth while a run is active, but the whole run state is mirrored
// here on every poll so the dashboard can list and reload previous projects
// from Postgres alone.
export const forgeRuns = pgTable("forge_runs", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  prompt: text("prompt").notNull(),
  status: text("status").notNull().default("pending"),
  state: jsonb("state").$type<Record<string, unknown>>(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});
