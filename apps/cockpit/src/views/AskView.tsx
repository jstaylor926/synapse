import { useState } from "react";
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

const CITATIONS = [
  {
    index: 1,
    source: "lecture-07.pdf · p.12",
    quote:
      "…temperature T controls the Metropolis acceptance of uphill moves; as T→0 the walk becomes greedy hill-climbing…",
    score: 0.91,
  },
  {
    index: 2,
    source: "notes/sa-vs-ga.md",
    quote:
      "GA keeps a population; crossover recombines partial solutions, mutation adds diversity — implicit parallel search over schemata.",
    score: 0.88,
  },
  {
    index: 3,
    source: "lecture-08.pdf · p.3",
    quote:
      "Choosing an optimizer: cost of evaluation, ruggedness, and whether the representation recombines meaningfully.",
    score: 0.74,
  },
];

const RETRIEVAL = [
  { left: "vector · sqlite-vec", right: "top-K 40" },
  { left: "lexical · FTS5 / BM25", right: "top-K 40" },
  { left: "merge · RRF", right: "→ 50", divider: true },
  { left: "rerank · bge-base", right: "50 → 5", accent: true },
  { left: "inline · bounded · timeout", right: "1.41s", divider: true, ok: true },
];

export function AskView() {
  const [mode, setMode] = useState("Ask");

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
              <Badge tone="success">claude-sonnet · litellm</Badge>
            </>
          }
        />

        <div style={{ height: 20 }} />

        <ChatBubble role="user">
          How does simulated annealing differ from a genetic algorithm for randomized optimization,
          and when would you pick each?
        </ChatBubble>

        <div style={{ height: 18 }} />

        <ChatBubble
          role="agent"
          footer="grounded · 3 citations · never fabricates (§1.10)"
        >
          <p style={{ margin: 0 }}>
            Simulated annealing is a <strong style={{ color: "#fff" }}>single-solution</strong>{" "}
            search: it perturbs one candidate and accepts worse moves with a probability set by a
            falling temperature schedule, so early exploration gives way to late exploitation.
          </p>
          <p style={{ marginBottom: 0 }}>
            A genetic algorithm instead evolves a <strong style={{ color: "#fff" }}>population</strong>,
            recombining high-fitness individuals via crossover and mutation — letting it cover several
            basins at once. Prefer SA when evaluations are cheap and the landscape is rugged but
            locally smooth; prefer a GA when structure recombines well.
          </p>
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
          <span style={{ fontSize: 13.5, color: "var(--syn-text-fainter)", flex: 1 }}>
            Ask your vault…
          </span>
          <Kbd>⌘↵</Kbd>
          <Button variant="primary">
            SEND <Icon name="send" size={13} strokeWidth={2} />
          </Button>
        </div>
      </div>

      {/* citations rail */}
      <div className="view__aside" style={{ width: 346 }}>
        <div className="row--between">
          <Eyebrow>Citations · 3</Eyebrow>
          <span className="meta">→ source chunks</span>
        </div>

        {CITATIONS.map((c) => (
          <CitationCard key={c.index} {...c} />
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
            {RETRIEVAL.map((r) => (
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
