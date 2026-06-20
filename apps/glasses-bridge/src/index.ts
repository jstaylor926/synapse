/**
 * @synapse/glasses-bridge — adapts the kernel's FastAPI REST edge into the
 * compact "spec_view" payloads the AR glasses (G2) consume.
 *
 * It owns no business logic: it queries `synapse_engine.api_server` and reshapes
 * responses for the glasses' constrained display. Run with `bun run dev`.
 */

import type { SearchHit } from "@synapse/contracts-ts";

const KERNEL_API = process.env.SYNAPSE_API_BASE ?? "http://127.0.0.1:8765";
const PORT = Number(process.env.GLASSES_BRIDGE_PORT ?? 4317);

/** Reshape a rich SearchHit into a minimal card for the glasses display. */
function toSpecView(hit: SearchHit) {
  return { title: hit.title, body: hit.snippet };
}

const server = Bun.serve({
  port: PORT,
  async fetch(req) {
    const url = new URL(req.url);

    if (url.pathname === "/healthz") {
      return Response.json({ status: "ok", kernel: KERNEL_API });
    }

    if (url.pathname === "/spec_view/search") {
      const q = url.searchParams.get("q") ?? "";
      const upstream = new URL(`${KERNEL_API}/kb/search`);
      upstream.searchParams.set("q", q);
      const res = await fetch(upstream);
      const { hits } = (await res.json()) as { hits: SearchHit[] };
      return Response.json({ cards: hits.map(toSpecView) });
    }

    return new Response("Not found", { status: 404 });
  },
});

console.log(`[glasses-bridge] listening on http://localhost:${server.port} -> ${KERNEL_API}`);
