import { randomUUID } from "crypto";
import { db } from "@/db";
import { forgeRuns } from "@/db/schema";
import { seedDemoRun } from "@/db/seedDemo";
import { DEMO_RUN_ID } from "@/lib/constants";
import { agentApi, AgentApiError } from "@/lib/agentApi";
import { desc, eq } from "drizzle-orm";

export const dynamic = "force-dynamic";

function runName(prompt: string): string {
  const first = prompt.split(/[.!?\n]/).find((s) => s.trim().length > 0) || prompt;
  const cleaned = first.trim();
  return cleaned.length > 70 ? `${cleaned.slice(0, 67)}...` : cleaned;
}

export async function GET() {
  try {
    await seedDemoRun();
    const rows = await db.select().from(forgeRuns).orderBy(desc(forgeRuns.createdAt)).limit(50);

    // Keep the pinned demo run first regardless of creation date.
    const demoRow = rows.find((r) => r.id === DEMO_RUN_ID);
    const otherRows = rows.filter((r) => r.id !== DEMO_RUN_ID);
    const orderedRows = demoRow ? [demoRow, ...otherRows] : rows;

    const runs = orderedRows.map((r) => ({
      id: r.id,
      name: r.name,
      prompt: r.prompt,
      status: r.status,
      created_at: Math.floor(new Date(r.createdAt).getTime() / 1000),
      updated_at: Math.floor(new Date(r.updatedAt).getTime() / 1000),
    }));
    return Response.json({ runs });
  } catch (err) {
    return Response.json({ runs: [], error: (err as Error).message }, { status: 200 });
  }
}

export async function POST(req: Request) {
  let body: { prompt?: string };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  const prompt = (body.prompt || "").trim();
  if (!prompt) {
    return Response.json({ error: "prompt is required" }, { status: 400 });
  }

  const runId = `run-${randomUUID().replace(/-/g, "").slice(0, 12)}`;
  const name = runName(prompt);

  try {
    await agentApi.createRun(prompt, runId);
  } catch (err) {
    const status = err instanceof AgentApiError ? err.status : 502;
    return Response.json({ error: (err as Error).message }, { status });
  }

  try {
    await db.insert(forgeRuns).values({ id: runId, name, prompt, status: "running" });
  } catch {
    // Non-fatal: the agent engine is the source of truth for run state.
  }

  return Response.json({ run_id: runId });
}

export async function PUT(req: Request) {
  let body: { run_id?: string; name?: string; status?: string; state?: unknown };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  if (!body.run_id) {
    return Response.json({ error: "run_id is required" }, { status: 400 });
  }
  try {
    await db
      .update(forgeRuns)
      .set({
        name: body.name,
        status: body.status,
        state: body.state as Record<string, unknown> | undefined,
        updatedAt: new Date(),
      })
      .where(eq(forgeRuns.id, body.run_id));
    return Response.json({ ok: true });
  } catch (err) {
    return Response.json({ error: (err as Error).message }, { status: 500 });
  }
}
