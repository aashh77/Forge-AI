import { agentApi, AgentApiError } from "@/lib/agentApi";

export const dynamic = "force-dynamic";

export async function POST(req: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  let body: { agent?: string; question?: string };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  if (!body.agent || !body.question) {
    return Response.json({ error: "agent and question are required" }, { status: 400 });
  }
  try {
    const result = await agentApi.chat(runId, body.agent, body.question);
    return Response.json(result);
  } catch (err) {
    const status = err instanceof AgentApiError ? err.status : 502;
    return Response.json({ error: (err as Error).message }, { status });
  }
}
