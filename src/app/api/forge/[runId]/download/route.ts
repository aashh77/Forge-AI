import { DEMO_RUN_ID } from "@/lib/constants";
import { agentApi } from "@/lib/agentApi";
import { readFileSync } from "fs";
import { join } from "path";

export const dynamic = "force-dynamic";

export async function GET(_req: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;

  if (runId === DEMO_RUN_ID) {
    const zipPath = join(process.cwd(), "python-agents", "workspace", runId, "forge-ai-run-demo.zip");
    try {
      const buffer = readFileSync(zipPath);
      return new Response(buffer, {
        status: 200,
        headers: {
          "Content-Type": "application/zip",
          "Content-Disposition": `attachment; filename="forge-ai-${runId}.zip"`,
        },
      });
    } catch {
      return Response.json({ error: "Demo archive not found on disk." }, { status: 404 });
    }
  }

  let upstream: Response;
  try {
    upstream = await fetch(agentApi.downloadUrl(runId), { cache: "no-store" });
  } catch {
    return Response.json({ error: "Cannot reach the Forge AI agent engine to download the archive." }, { status: 503 });
  }
  if (!upstream.ok || !upstream.body) {
    return Response.json({ error: `Agent engine returned ${upstream.status}` }, { status: upstream.status || 502 });
  }
  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename="forge-ai-${runId}.zip"`,
    },
  });
}
