#!/usr/bin/env bun
/**
 * claude-hud — Claude Code hook → G2 heads-up display.
 *
 * Wired into .claude/settings.local.json on several hook events. Each invocation
 * receives the hook's JSON payload on stdin (see the Claude Code hooks docs) and
 * pushes one concise line to the relay (src/relay.ts), tagged source="claude",
 * so the glasses mirror what Claude is doing hands-free.
 *
 * Invoked as: `bun claude-hud.ts <event>` where <event> is stop | posttooluse |
 * notification | prompt. The event is also read from the payload's
 * `hook_event_name` as a fallback.
 *
 * Design rules for a hook: be fast, never block Claude, never crash the session.
 * Every failure path swallows its error and exits 0.
 */

const RELAY = process.env.HUD_RELAY_URL ?? "http://localhost:4318";
const MAX = 600; // keep HUD lines short

async function readStdin(): Promise<string> {
  try {
    const chunks: Uint8Array[] = [];
    for await (const c of Bun.stdin.stream()) chunks.push(c);
    return Buffer.concat(chunks).toString("utf8");
  } catch {
    return "";
  }
}

async function push(text: string): Promise<void> {
  const trimmed = text.trim();
  if (!trimmed) return;
  try {
    await fetch(`${RELAY}/push`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: trimmed.slice(0, MAX), source: "claude" }),
      signal: AbortSignal.timeout(1200),
    });
  } catch {
    /* relay down — ignore */
  }
}

/** Pull the last assistant text turn out of a Claude Code transcript (JSONL). */
function lastAssistantText(transcriptPath: string): string {
  try {
    const raw = require("node:fs").readFileSync(transcriptPath, "utf8") as string;
    const lines = raw.split("\n").filter(Boolean);
    for (let i = lines.length - 1; i >= 0; i--) {
      let rec: any;
      try {
        rec = JSON.parse(lines[i]!);
      } catch {
        continue;
      }
      if (rec?.type !== "assistant") continue;
      const content = rec.message?.content;
      if (Array.isArray(content)) {
        const text = content
          .filter((b: any) => b?.type === "text")
          .map((b: any) => b.text)
          .join("\n")
          .trim();
        if (text) return text;
      }
    }
  } catch {
    /* unreadable transcript — ignore */
  }
  return "";
}

/** One-line summary of a tool call: "Edit foo.ts", "Bash: npm test", … */
function summarizeTool(name: string, input: any): string {
  if (!name) return "tool";
  const i = input ?? {};
  switch (name) {
    case "Bash":
      return `Bash: ${String(i.command ?? "").split("\n")[0]}`;
    case "Read":
    case "Edit":
    case "Write":
    case "NotebookEdit":
      return `${name} ${basename(i.file_path ?? i.notebook_path ?? "")}`;
    case "Grep":
      return `Grep /${i.pattern ?? ""}/`;
    case "Glob":
      return `Glob ${i.pattern ?? ""}`;
    case "Task":
      return `Task: ${i.description ?? ""}`;
    default:
      return name;
  }
}

const basename = (p: string) => (p ? String(p).split("/").pop() ?? p : "");

async function main() {
  const raw = await readStdin();
  let payload: any = {};
  try {
    payload = raw ? JSON.parse(raw) : {};
  } catch {
    payload = {};
  }
  const event = (process.argv[2] ?? payload.hook_event_name ?? "").toLowerCase();

  switch (event) {
    case "stop":
    case "subagentstop": {
      const text = lastAssistantText(payload.transcript_path ?? "");
      if (text) await push(`✓ ${text}`);
      break;
    }
    case "posttooluse": {
      await push(`⚙ ${summarizeTool(payload.tool_name, payload.tool_input)}`);
      break;
    }
    case "notification": {
      await push(`🔔 ${payload.message ?? "notification"}`);
      break;
    }
    case "userpromptsubmit":
    case "prompt": {
      await push(`▶ ${payload.prompt ?? ""}`);
      break;
    }
    default:
      break;
  }
  // Always succeed: a hook must not break the Claude Code session.
  process.exit(0);
}

main();
