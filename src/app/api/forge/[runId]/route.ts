import { db } from "@/db";
import { forgeRuns } from "@/db/schema";
import { DEMO_RUN_ID } from "@/lib/constants";
import { agentApi, AgentApiError } from "@/lib/agentApi";
import type { RunState } from "@/lib/types";
import { eq } from "drizzle-orm";

export const dynamic = "force-dynamic";

function runName(prompt: string): string {
  const first = prompt.split(/[.!?\n]/).find((s) => s.trim().length > 0) || prompt;
  const cleaned = first.trim();
  return cleaned.length > 70 ? `${cleaned.slice(0, 67)}...` : cleaned;
}

export async function GET(_req: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  try {
    // Refresh live deployment status from the engine before returning state.
    try {
      await agentApi.deploymentStatus(runId);
    } catch {
      // Non-fatal: engine may be offline.
    }
    const run = (await agentApi.getRun(runId)) as RunState;
    // Mirror the full run state into Postgres so history and project reloads
    // work even if the Python engine is restarted.
    db.update(forgeRuns)
      .set({
        name: runName(run.prompt),
        status: run.status,
        state: run as unknown as Record<string, unknown>,
        updatedAt: new Date(),
      })
      .where(eq(forgeRuns.id, runId))
      .catch(() => {});
    return Response.json(run);
  } catch (err) {
    const status = err instanceof AgentApiError ? err.status : 502;
    // Fall back to the mirrored copy in Postgres so pinned/historical runs
    // can still be reviewed when the agent engine is offline.
    try {
      const row = await db.select().from(forgeRuns).where(eq(forgeRuns.id, runId)).limit(1);
      if (row.length && row[0].state) {
        return Response.json(row[0].state);
      }
    } catch {
      // Ignore DB fallback errors and return the original engine error below.
    }
    return Response.json({ error: (err as Error).message }, { status });
  }
}

export async function PATCH(req: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  let body: { name?: string };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  if (!body.name || !body.name.trim()) {
    return Response.json({ error: "name is required" }, { status: 400 });
  }
  try {
    await db
      .update(forgeRuns)
      .set({ name: body.name.trim(), updatedAt: new Date() })
      .where(eq(forgeRuns.id, runId));
    return Response.json({ ok: true });
  } catch (err) {
    return Response.json({ error: (err as Error).message }, { status: 500 });
  }
}

export async function DELETE(_req: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  if (runId === DEMO_RUN_ID) {
    return Response.json(
      { error: "The demo project is pinned and cannot be deleted." },
      { status: 403 },
    );
  }
  try {
    await db.delete(forgeRuns).where(eq(forgeRuns.id, runId));
    return Response.json({ ok: true });
  } catch (err) {
    return Response.json({ error: (err as Error).message }, { status: 500 });
  }
}
