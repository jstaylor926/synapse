import {
  PageHeader,
  Badge,
  ChatBubble,
  CodeBlock,
  SaveToKbButton,
  Card,
  Tag,
  Eyebrow,
  Button,
  Kbd,
  Icon,
  GlowAccent,
} from "@synapse/ui-kit";

const SA_REFERENCE = `from math import exp;  from random import random

def simulated_annealing(problem, schedule, max_iters=1000):
    state = best = problem.random_state()
    for t in range(max_iters):
        T   = schedule(t)            # cooling: T → 0
        nxt = problem.neighbor(state)
        dE  = problem.fitness(nxt) - problem.fitness(state)
        if dE > 0 or random() < exp(dE / T):   # accept
            state = nxt
        if problem.fitness(state) > problem.fitness(best):
            best = state
    return best`;

const GROUNDING = [
  { type: "py", tone: "success" as const, name: "mlrose/algorithms.py", note: "tree-sitter" },
  { type: "py", tone: "success" as const, name: "a2/sa.py · a2/ga.py", note: "your repo" },
  { type: "pdf", tone: "accent" as const, name: "lecture-07.pdf · p.12", note: "kb:abc123" },
];

export function CodeBuddyView() {
  return (
    <div className="view view__split">
      <GlowAccent style={{ top: 0, left: 240 }} width={380} opacity={0.42} />

      <div className="view__main">
        <PageHeader
          eyebrow="code_assist · grounded in ingested code + docs"
          title="Code Buddy"
          description="Discuss assignment code and pull snippets. It reasons, never executes — anything useful gets saved back to the vault."
          actions={<Badge dot={false}>no-exec · advice only</Badge>}
        />

        <div style={{ height: 20 }} />

        <ChatBubble role="user">
          My A2 simulated-annealing loop converges too fast. Here's my accept rule — what's wrong, and
          can you give me a clean reference?
        </ChatBubble>

        <div style={{ height: 18 }} />

        <ChatBubble
          role="agent"
          name="CODE BUDDY"
          footer="grounded · advice only, never runs your code"
        >
          <p style={{ marginTop: 0 }}>
            You're accepting uphill moves with <code style={{ color: "#ff9aa0" }}>dE &lt; 0</code> —
            that flips the Metropolis test, so worse moves win and the walk never settles. It should
            accept <strong style={{ color: "#fff" }}>better</strong> moves outright and worse ones only
            with probability <code style={{ color: "var(--syn-accent-text)" }}>e^(dE/T)</code>:
          </p>
          <CodeBlock
            filename="sa_reference.py · python"
            actions={
              <>
                <span className="syn-kbd">copy</span>
                <SaveToKbButton />
              </>
            }
          >
            {SA_REFERENCE}
          </CodeBlock>
        </ChatBubble>

        <div className="grow" />

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
          <span className="syn-kbd">&gt;_</span>
          <span style={{ fontSize: 13.5, color: "var(--syn-text-fainter)", flex: 1 }}>
            Paste code or ask about your assignment…
          </span>
          <Kbd>⌘↵</Kbd>
          <Button variant="primary">
            SEND <Icon name="send" size={13} strokeWidth={2} />
          </Button>
        </div>
      </div>

      <div className="view__aside" style={{ width: 330 }}>
        <Eyebrow>Grounding · ingested code</Eyebrow>
        <Card style={{ display: "flex", flexDirection: "column", gap: 9 }}>
          {GROUNDING.map((g) => (
            <div key={g.name} className="row">
              <Tag tone={g.tone}>{g.type}</Tag>
              <span className="grow" style={{ fontFamily: "var(--syn-font-mono)", fontSize: 11, color: "var(--syn-text-secondary)" }}>
                {g.name}
              </span>
              <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 9.5, color: "var(--syn-text-fainter)" }}>
                {g.note}
              </span>
            </div>
          ))}
        </Card>

        <div className="row--between" style={{ marginTop: 4 }}>
          <Eyebrow>Saved snippets</Eyebrow>
          <span className="meta">→ vault · kb</span>
        </div>
        {[
          { name: "sa_reference.py", path: "resources/snippets/sa-ref · kb:9d2f", bind: "a2-t2" },
          { name: "ga_crossover.py", path: "resources/snippets/ga-xover · kb:7b10", bind: "a2-t2" },
        ].map((s) => (
          <Card key={s.name}>
            <div className="row" style={{ marginBottom: 6 }}>
              <Icon name="check" size={12} strokeWidth={2} style={{ color: "var(--syn-success)" }} />
              <span style={{ fontSize: 13, fontWeight: 700, flex: 1 }}>{s.name}</span>
            </div>
            <div className="meta">
              {s.path}
              <br />→ bound to <span style={{ color: "var(--syn-purple-text)" }}>{s.bind}</span>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
