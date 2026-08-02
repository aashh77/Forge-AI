import { agentApi, AgentApiError } from "@/lib/agentApi";

export const dynamic = "force-dynamic";

export async function POST(_req: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  try {
    const result = await agentApi.stop(runId);
    return Response.json(result);
  } catch (err) {
    const status = err instanceof AgentApiError ? err.status : 502;
    return Response.json({ error: (err as Error).message }, { status });
  }
}
