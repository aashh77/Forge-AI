import { agentApi, AgentApiError } from "@/lib/agentApi";

export const dynamic = "force-dynamic";

export async function POST(req: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  let body: { checkpoint_id?: string };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  if (!body.checkpoint_id) {
    return Response.json({ error: "checkpoint_id is required" }, { status: 400 });
  }
  try {
    const result = await agentApi.rollback(runId, body.checkpoint_id);
    return Response.json(result);
  } catch (err) {
    const status = err instanceof AgentApiError ? err.status : 502;
    return Response.json({ error: (err as Error).message }, { status });
  }
}
