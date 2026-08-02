import { agentApi, AgentApiError } from "@/lib/agentApi";

export const dynamic = "force-dynamic";

export async function POST(req: Request) {
  let body: { text?: string; source_lang?: string; target_lang?: string };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Invalid JSON body" }, { status: 400 });
  }
  const text = (body.text || "").trim();
  if (!text) {
    return Response.json({ error: "text is required" }, { status: 400 });
  }
  try {
    const result = await agentApi.translate(text, body.source_lang || "hi", body.target_lang || "en");
    return Response.json(result);
  } catch (err) {
    const status = err instanceof AgentApiError ? err.status : 502;
    return Response.json({ error: (err as Error).message }, { status });
  }
}
