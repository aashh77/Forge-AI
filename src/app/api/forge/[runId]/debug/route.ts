import { agentApi, AgentApiError } from "@/lib/agentApi";

export const dynamic = "force-dynamic";

export async function POST(req: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  let body: { question?: string };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  if (!body.question) {
    return Response.json({ error: "question is required" }, { status: 400 });
  }
  try {
    const result = await agentApi.debug(runId, body.question);
    return Response.json(result);
  } catch (err) {
    const status = err instanceof AgentApiError ? err.status : 502;
    return Response.json({ error: (err as Error).message }, { status });
  }
}
