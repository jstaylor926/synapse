import { PageHeader, Card, Tag, Eyebrow } from "@synapse/ui-kit";

interface TreeNode {
  label: string;
  depth: number;
  badge?: { text: string; tone: "purple" | "neutral" };
  active?: boolean;
}

const TREE: TreeNode[] = [
  { label: "📁 vault", depth: 0 },
  { label: "courses", depth: 1 },
  { label: "assignments", depth: 1 },
  { label: "topics", depth: 1 },
  { label: "▾ tasks", depth: 1, badge: { text: "system", tone: "purple" } },
  { label: "a2-t1.md", depth: 2 },
  { label: "a2-t2.md", depth: 2 },
  { label: "a2-t3.md", depth: 2, active: true },
  { label: "a2-t4.md", depth: 2 },
  { label: "resources", depth: 1 },
  { label: "blocks", depth: 1 },
  { label: "cards", depth: 1 },
  { label: "notes", depth: 1, badge: { text: "human", tone: "neutral" } },
];

/* One frontmatter line: key in muted, value tinted by role. */
const FRONTMATTER: { k: string; v: string; color?: string }[] = [
  { k: "type", v: "task", color: "var(--syn-text-secondary)" },
  { k: "id", v: "a2-t3", color: "var(--syn-text-secondary)" },
  { k: "assignment", v: '"[[cs7641-a2]]"', color: "var(--syn-purple-text)" },
  { k: "topic", v: '["[[topics/randomized-optimization]]"]', color: "var(--syn-purple-text)" },
  { k: "resources", v: '["[[resources/lecture-07]]", "[[notes/sa-vs-ga]]"]', color: "var(--syn-accent)" },
  { k: "estimate", v: "45m", color: "var(--syn-amber)" },
  { k: "scheduled", v: "2026-06-22T18:00", color: "var(--syn-amber)" },
  { k: "status", v: "todo", color: "var(--syn-accent)" },
];

const EDGES: { from: string; to: string; color: string }[] = [
  { from: "assignment →", to: "cs7641-a2", color: "var(--syn-purple-text)" },
  { from: "topic →", to: "randomized-optimization", color: "var(--syn-purple-text)" },
  { from: "resources →", to: "lecture-07 · sa-vs-ga", color: "var(--syn-accent)" },
  { from: "binding →", to: "study_flashcards", color: "var(--syn-success)" },
  { from: "doc_id →", to: "kb:abc123", color: "var(--syn-accent)" },
];

export function VaultView() {
  return (
    <div className="view" style={{ display: "flex", flexDirection: "column" }}>
      <PageHeader
        eyebrow="vault-as-truth · single-writer gatekeeper · Obsidian-native"
        title="Vault"
      />

      <div style={{ height: 16 }} />

      <div style={{ flex: 1, display: "flex", border: "1px solid var(--syn-border)", borderRadius: 9, overflow: "hidden", minHeight: 0 }}>
        {/* tree */}
        <div style={{ width: 236, flex: "none", background: "var(--syn-bg-chrome)", borderRight: "1px solid var(--syn-divider)", padding: "13px 10px", fontFamily: "var(--syn-font-mono)", fontSize: 11.5 }}>
          {TREE.map((n) => (
            <div
              key={n.label}
              style={{
                padding: `${n.depth >= 2 ? 3 : 4}px 6px ${n.depth >= 2 ? 3 : 4}px ${6 + n.depth * 14}px`,
                color: n.active ? "var(--syn-accent-text)" : n.depth === 0 ? "var(--syn-text-dimmer)" : n.active ? undefined : "var(--syn-text-faint)",
                background: n.active ? "var(--syn-accent-12)" : undefined,
                borderRadius: n.active ? 3 : undefined,
                borderLeft: n.active ? "2px solid var(--syn-accent)" : undefined,
                display: "flex",
                alignItems: "center",
                gap: 6,
              }}
            >
              {n.label}
              {n.badge && (
                <span
                  style={{
                    fontSize: 8.5,
                    color: n.badge.tone === "purple" ? "var(--syn-purple-text)" : "var(--syn-text-dim)",
                    border: `1px solid ${n.badge.tone === "purple" ? "rgba(139,92,240,.4)" : "rgba(130,160,205,.24)"}`,
                    padding: "0 4px",
                    borderRadius: 3,
                  }}
                >
                  {n.badge.text}
                </span>
              )}
            </div>
          ))}
        </div>

        {/* frontmatter editor */}
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", background: "var(--syn-bg-base)" }}>
          <div style={{ height: 42, flex: "none", display: "flex", alignItems: "center", gap: 12, padding: "0 16px", borderBottom: "1px solid var(--syn-divider)", background: "var(--syn-bg-chrome)" }}>
            <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 12, color: "var(--syn-text-secondary)" }}>
              tasks/a2-t3.md
            </span>
            <span className="grow" />
            <Tag tone="purple">OPEN IN OBSIDIAN</Tag>
          </div>
          <div style={{ flex: 1, padding: "18px 22px", fontFamily: "var(--syn-font-mono)", fontSize: 12.5, lineHeight: 1.95, overflow: "auto" }}>
            <div style={{ color: "var(--syn-text-disabled)" }}>---</div>
            {FRONTMATTER.map((f) => (
              <div key={f.k}>
                <span style={{ color: "var(--syn-text-faint)" }}>{f.k}:</span>{" "}
                <span style={{ color: f.color }}>{f.v}</span>
              </div>
            ))}
            <div style={{ color: "var(--syn-text-disabled)" }}>---</div>
            <div style={{ marginTop: 8, color: "var(--syn-text-body)" }}>
              - [ ] Drill RO flashcards <span style={{ color: "var(--syn-amber)" }}>📅 2026-06-22</span>{" "}
              <span style={{ color: "var(--syn-danger-text)" }}>⏫</span>
            </div>
          </div>
        </div>

        {/* meta */}
        <div style={{ width: 300, flex: "none", background: "var(--syn-bg-chrome)", borderLeft: "1px solid var(--syn-divider)", padding: 15, display: "flex", flexDirection: "column", gap: 13, overflow: "auto" }}>
          <Card variant="dashed-purple" style={{ borderStyle: "solid", background: "rgba(139,92,240,.07)", borderColor: "rgba(139,92,240,.28)" }}>
            <div className="row" style={{ gap: 7, marginBottom: 10 }}>
              <span className="syn-dot syn-dot--purple" style={{ width: 7, height: 7 }} />
              <Eyebrow style={{ color: "var(--syn-purple-text)" }}>Gatekeeper</Eyebrow>
            </div>
            <div className="meta" style={{ color: "var(--syn-text-dim)", display: "flex", flexDirection: "column", gap: 7 }}>
              <span>single-threaded write queue</span>
              <span>atomic · temp → fsync → rename</span>
              <span>last write <span style={{ color: "var(--syn-success)" }}>18:02 · ok</span></span>
              <span style={{ color: "var(--syn-text-faint)" }}>optimistic-concurrency · mtime+hash guarded vs Obsidian</span>
            </div>
          </Card>

          <Card>
            <Eyebrow>Ownership</Eyebrow>
            <div className="row" style={{ gap: 8, marginTop: 10, marginBottom: 7 }}>
              <Tag tone="purple">tasks/</Tag>
              <span className="meta" style={{ color: "var(--syn-text-dim)" }}>system-owned · generated</span>
            </div>
            <div className="row" style={{ gap: 8 }}>
              <Tag tone="neutral">notes/</Tag>
              <span className="meta">human-owned · append-only</span>
            </div>
          </Card>

          <Card>
            <Eyebrow>Edges · wikilinks</Eyebrow>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 11, fontFamily: "var(--syn-font-mono)", fontSize: 10.5, lineHeight: 1.4 }}>
              {EDGES.map((e) => (
                <div key={e.from} style={e.from === "doc_id →" ? { paddingTop: 7, borderTop: "1px solid var(--syn-divider)" } : undefined}>
                  <span style={{ color: "var(--syn-text-faint)" }}>{e.from}</span>{" "}
                  <span style={{ color: e.color }}>{e.to}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
