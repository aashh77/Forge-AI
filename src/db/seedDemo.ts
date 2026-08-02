import { DEMO_PROMPT, DEMO_RUN_ID } from "@/lib/constants";
import { db } from "@/db";
import { forgeRuns } from "@/db/schema";
import { eq } from "drizzle-orm";
import demoState from "./demo-state.json";

export async function seedDemoRun(): Promise<void> {
  try {
    const existing = await db.select().from(forgeRuns).where(eq(forgeRuns.id, DEMO_RUN_ID)).limit(1);
    if (existing.length > 0) return;

    const state = demoState as Record<string, unknown>;
    await db.insert(forgeRuns).values({
      id: DEMO_RUN_ID,
      name: DEMO_PROMPT,
      prompt: DEMO_PROMPT,
      status: "completed",
      state,
      createdAt: new Date((state.created_at as number) * 1000),
      updatedAt: new Date((state.updated_at as number) * 1000),
    });
  } catch {
    // Non-fatal: the demo run is a convenience, not a requirement for the app to work.
  }
}
