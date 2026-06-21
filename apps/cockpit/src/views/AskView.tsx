import { useState } from "react";
import { ask } from "@synapse/client";
import type { Citation } from "@synapse/contracts-ts";
import {
  PageHeader,
  SegmentedControl,
  Badge,
  ChatBubble,
  CitationCard,
  Eyebrow,
  Button,
  Kbd,
  Icon,
  GlowAccent,
} from "@synapse/ui-kit";

export function AskView() {
  const [mode, setMode] = useState("Ask");
  const [input, setInput] = useState("");
  const [question, setQuestion] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string | null>(null);
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);

  async function send() {
    const q = input.trim();
    if (!q || loading) return;
    setQuestion(q);
    setInput("");
    setLoading(true);
    setError(null);
    const started = performance.now();
    try {
      const res = await ask(q, 8);
      setAnswer(res.answer);
      setCitations(res.citations);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setAnswer(null);
      setCitations([]);
    } finally {
      setElapsedMs(Math.round(performance.now() - started));
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  }

  const retrieval: {
    left: string;
    right: string;
    divider?: boolean;
    accent?: boolean;
    ok?: boolean;
  }[] = [
    { left: "lexical · BM25 (floor)", right: "vault scan" },
    { left: "vector · sqlite-vec", right: "off" },
    { left: "merge · RRF", right: "—", divider: true },
    { left: "rerank · bge-base", right: "off", accent: true },
    {
      left: "extractive · no LLM",
      right: elapsedMs != null ? `${elapsedMs}ms` : "idle",
      divider: true,
      ok: elapsedMs != null,
    },
  ];

  return (
    <div className="view view__split">
      <GlowAccent style={{ top: 0, left: 200 }} width={380} opacity={0.45} />

      {/* main column */}
      <div className="view__main">
        <PageHeader
          eyebrow="reason_ask · hybrid RAG + rerank"
          title="Ask"
          actions={
            <>
              <SegmentedControl
                options={["Ask", "Multi-step", "Extractive"]}
                value={mode}
                onChange={setMode}
              />
              <Badge tone="neutral">extractive · no LLM</Badge>
            </>
          }
        />

        <div style={{ height: 20 }} />

        {question && <ChatBubble role="user">{question}</ChatBubble>}

        {question && <div style={{ height: 18 }} />}

        <ChatBubble
          role="agent"
          footer={
            error
              ? "request failed · is the kernel running? (bun run dev:api)"
              : answer
                ? `grounded · ${citations.length} citation${citations.length === 1 ? "" : "s"} · never fabricates (§1.10)`
                : "ask a question and I'll answer from your vault — grounded, with citations"
          }
        >
          {loading ? (
            <p style={{ margin: 0, color: "var(--syn-text-secondary)" }}>
              Retrieving from your vault…
            </p>
          ) : error ? (
            <p style={{ margin: 0, color: "var(--syn-danger)" }}>{error}</p>
          ) : answer ? (
            answer.split("\n\n").map((para, i) => (
              <p key={i} style={{ marginTop: i === 0 ? 0 : undefined, marginBottom: 0 }}>
                {para}
              </p>
            ))
          ) : (
            <p style={{ margin: 0, color: "var(--syn-text-fainter)" }}>
              e.g. “How does simulated annealing differ from a genetic algorithm, and when would
              you pick each?”
            </p>
          )}
        </ChatBubble>

        <div className="grow" />

        {/* input bar */}
        <div
          style={{
            marginTop: 20,
            display: "flex",
            gap: 10,
            alignItems: "center",
            background: "var(--syn-surface-sunken)",
            border: "1px solid rgba(130,160,205,.14)",
            borderRadius: 8,
            padding: "11px 13px",
          }}
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask your vault…"
            style={{
              flex: 1,
              background: "transparent",
              border: "none",
              outline: "none",
              fontSize: 13.5,
              color: "var(--syn-text-primary)",
              fontFamily: "inherit",
            }}
          />
          <Kbd>⌘↵</Kbd>
          <Button variant="primary" onClick={() => void send()} disabled={loading || !input.trim()}>
            SEND <Icon name="send" size={13} strokeWidth={2} />
          </Button>
        </div>
      </div>

      {/* citations rail */}
      <div className="view__aside" style={{ width: 346 }}>
        <div className="row--between">
          <Eyebrow>Citations · {citations.length}</Eyebrow>
          <span className="meta">→ source chunks</span>
        </div>

        {citations.length === 0 && !loading && (
          <span className="meta" style={{ color: "var(--syn-text-fainter)" }}>
            No citations yet.
          </span>
        )}

        {citations.map((c, i) => (
          <CitationCard
            key={`${c.source}-${i}`}
            index={i + 1}
            source={c.source}
            quote={c.snippet}
            score={c.score}
          />
        ))}

        <div
          style={{
            background: "var(--syn-surface-sunken)",
            border: "1px solid var(--syn-divider)",
            borderRadius: "var(--syn-radius-md)",
            padding: 13,
            marginTop: 3,
          }}
        >
          <Eyebrow>Retrieval</Eyebrow>
          <div style={{ display: "flex", flexDirection: "column", gap: 7, marginTop: 10 }}>
            {retrieval.map((r) => (
              <div
                key={r.left}
                className="row--between meta"
                style={
                  r.divider
                    ? { paddingTop: 6, borderTop: "1px solid var(--syn-border-subtle)" }
                    : undefined
                }
              >
                <span style={r.accent ? { color: "var(--syn-accent)" } : undefined}>{r.left}</span>
                <span style={{ color: r.ok ? "var(--syn-success)" : "var(--syn-text-secondary)" }}>
                  {r.right}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
