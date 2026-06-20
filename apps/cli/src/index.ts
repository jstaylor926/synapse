#!/usr/bin/env bun
/**
 * @synapse/cli — a thin Bun CLI for interacting with the kernel over its REST edge.
 *
 * Usage:
 *   bun run src/index.ts health
 *   bun run src/index.ts search "spaced repetition"
 *
 * Once linked (`bun link`) it's available as `synapse <command>`.
 */

import type { SearchHit } from "@synapse/contracts-ts";

const API_BASE = process.env.SYNAPSE_API_BASE ?? "http://127.0.0.1:8765";

async function health(): Promise<void> {
  const res = await fetch(`${API_BASE}/health`);
  console.log(JSON.stringify(await res.json(), null, 2));
}

async function search(query: string): Promise<void> {
  const url = new URL(`${API_BASE}/kb/search`);
  url.searchParams.set("q", query);
  const res = await fetch(url);
  const { hits } = (await res.json()) as { hits: SearchHit[] };
  for (const hit of hits) {
    console.log(`${hit.score.toFixed(3)}  ${hit.title}  (${hit.path})`);
  }
}

function usage(): void {
  console.log(
    [
      "synapse — Synapse kernel CLI",
      "",
      "Commands:",
      "  health            Check that the kernel REST edge is reachable",
      "  search <query>    Hybrid search over the vault",
      "",
      `API base: ${API_BASE} (override with SYNAPSE_API_BASE)`,
    ].join("\n"),
  );
}

const [command, ...rest] = process.argv.slice(2);

switch (command) {
  case "health":
    await health();
    break;
  case "search":
    if (rest.length === 0) {
      console.error("error: search requires a query");
      process.exit(1);
    }
    await search(rest.join(" "));
    break;
  default:
    usage();
    if (command !== undefined && command !== "help") process.exit(1);
}
