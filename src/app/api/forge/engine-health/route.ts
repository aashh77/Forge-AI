import { agentApi } from "@/lib/agentApi";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const health = await agentApi.health();
    return Response.json({ reachable: true, ...health });
  } catch (err) {
    return Response.json({ reachable: false, error: (err as Error).message }, { status: 200 });
  }
}
