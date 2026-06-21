import { PageHeader, Badge, Tag, NewsprintCard, Icon } from "@synapse/ui-kit";

export function NotesView() {
  return (
    <div className="view" style={{ display: "flex", flexDirection: "column" }}>
      <PageHeader
        eyebrow="notes/ · human-owned · split study workspace"
        title="Notes"
        actions={
          <>
            <Badge tone="success">saved 18:04 · gatekeeper</Badge>
            <Badge dot={false}>append-only</Badge>
          </>
        }
      />

      <div style={{ height: 16 }} />

      {/* split workspace */}
      <div
        style={{
          flex: 1,
          display: "flex",
          border: "1px solid var(--syn-border)",
          borderRadius: 9,
          overflow: "hidden",
          minHeight: 640,
        }}
      >
        {/* LEFT — note editor */}
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", background: "var(--syn-bg-rail)", borderRight: "1px solid var(--syn-divider)" }}>
          <div style={{ height: 40, flex: "none", display: "flex", alignItems: "center", gap: 11, padding: "0 16px", borderBottom: "1px solid var(--syn-border-subtle)", background: "var(--syn-bg-chrome)" }}>
            <Icon name="notes" size={13} strokeWidth={1.5} style={{ color: "var(--syn-text-dimmer)" }} />
            <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 11.5, color: "var(--syn-text-secondary)", flex: 1 }}>
              notes/sa-vs-ga.md
            </span>
            <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 10, color: "var(--syn-text-fainter)" }}>214 words</span>
            <Tag tone="purple">→ a2-t2</Tag>
          </div>

          <div style={{ flex: 1, padding: "24px 28px", overflow: "auto" }}>
            <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-.01em", marginBottom: 18 }}>
              Simulated Annealing vs Genetic Algorithms
            </div>

            <div style={{ fontFamily: "var(--syn-font-mono)", fontSize: 12, color: "var(--syn-purple)", marginBottom: 8 }}>
              ## Core difference
            </div>
            <p style={{ fontSize: 14.5, lineHeight: 1.75, color: "var(--syn-text-body)", marginTop: 0, marginBottom: 16 }}>
              <strong style={{ color: "#fff" }}>SA</strong> walks a single solution and accepts worse
              moves on a falling temperature schedule — exploration early, exploitation late.{" "}
              <strong style={{ color: "#fff" }}>GA</strong> evolves a whole population, recombining good
              partial solutions via crossover.
            </p>

            <div style={{ fontFamily: "var(--syn-font-mono)", fontSize: 12, color: "var(--syn-purple)", marginBottom: 8 }}>
              ## Temperature
            </div>
            <p style={{ fontSize: 14.5, lineHeight: 1.75, color: "var(--syn-text-body)", marginTop: 0, marginBottom: 8 }}>
              The accept probability is the Metropolis rule →{" "}
              <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 13, color: "var(--syn-accent)", background: "var(--syn-accent-12)", padding: "1px 6px", borderRadius: 3 }}>
                exp(-ΔE / T)
              </span>
              . As T → 0 it collapses to greedy hill-climbing.
            </p>

            {/* callout / open question */}
            <div
              style={{
                background: "color-mix(in srgb, var(--syn-accent) 7%, var(--syn-surface))",
                borderLeft: "3px solid var(--syn-accent)",
                borderRadius: "0 6px 6px 0",
                padding: "12px 14px",
                margin: "18px 0",
              }}
            >
              <div style={{ fontFamily: "var(--syn-font-mono)", fontSize: 10, letterSpacing: ".1em", color: "var(--syn-accent)", marginBottom: 6 }}>
                Q · TODO
              </div>
              <div style={{ fontSize: 14, lineHeight: 1.6, color: "var(--syn-text-body)" }}>
                When does SA beat GA? → rugged landscape + cheap evals; GA wins when structure
                recombines well. <span style={{ color: "var(--syn-text-faint)" }}>Confirm against L08.</span>
              </div>
            </div>

            <div style={{ fontSize: 14.5, lineHeight: 1.75, color: "var(--syn-text-body)" }}>
              Links: <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 12.5, color: "var(--syn-purple-text)" }}>[[resources/lecture-07]]</span>{" "}
              · <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 12.5, color: "var(--syn-purple-text)" }}>[[topics/randomized-optimization]]</span>
              <span style={{ display: "inline-block", width: 2, height: 18, background: "var(--syn-accent)", marginLeft: 3, verticalAlign: -3, animation: "syn-caret 1.1s steps(1) infinite" }} />
            </div>
          </div>

          <div style={{ height: 42, flex: "none", display: "flex", alignItems: "center", gap: 4, padding: "0 14px", borderTop: "1px solid var(--syn-border-subtle)", background: "var(--syn-bg-chrome)" }}>
            {["B", "I", "</>", "•"].map((b) => (
              <span key={b} style={{ width: 28, height: 26, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, color: "var(--syn-text-dim)", borderRadius: 4 }}>
                {b}
              </span>
            ))}
            <span className="grow" />
            <span className="meta">plain text + markdown · ⌘S writes via gatekeeper</span>
          </div>
        </div>

        {/* RIGHT — source viewer */}
        <div style={{ flex: 1.15, minWidth: 0, display: "flex", flexDirection: "column", background: "var(--syn-bg-base)" }}>
          <div style={{ height: 40, flex: "none", display: "flex", alignItems: "stretch", padding: "0 8px", borderBottom: "1px solid var(--syn-divider)", background: "var(--syn-bg-chrome)" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 7, padding: "0 14px", fontFamily: "var(--syn-font-mono)", fontSize: 11, color: "var(--syn-accent-text)", borderBottom: "2px solid var(--syn-accent)" }}>
              <Tag tone="accent">pdf</Tag>lecture-07.pdf
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 7, padding: "0 14px", fontFamily: "var(--syn-font-mono)", fontSize: 11, color: "var(--syn-text-faint)" }}>
              <Tag tone="neutral">md</Tag>sa-vs-ga.md
            </span>
          </div>

          <div
            style={{
              flex: 1,
              overflow: "auto",
              padding: 22,
              display: "flex",
              justifyContent: "center",
              background: "repeating-linear-gradient(45deg,#090c13,#090c13 11px,#0a0e16 11px,#0a0e16 22px)",
            }}
          >
            <div style={{ width: 460, maxWidth: "100%", alignSelf: "flex-start" }}>
              <NewsprintCard title="§3 Simulated Annealing">
                <div style={{ fontSize: 13.5, lineHeight: 1.78, color: "var(--syn-paper-ink)", fontFamily: "var(--syn-font-sans)" }}>
                  Simulated annealing maintains a single candidate and proposes a local move at each
                  step. A move that improves fitness is always taken; a move that worsens it by ΔE is
                  accepted with probability governed by a temperature parameter T.
                  <div style={{ background: "#f4efe2", border: "1px solid #cdc4ab", borderRadius: 3, padding: "14px 16px", textAlign: "center", margin: "14px 0" }}>
                    <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 16, color: "#1d1810" }}>
                      P(accept) = exp( −ΔE / T )
                    </span>
                  </div>
                  High temperatures permit broad exploration; the cooling schedule lowers T over time.
                  In the limit T → 0, annealing degenerates to greedy hill-climbing.
                  <div style={{ marginTop: 22, paddingTop: 12, borderTop: "1px solid #cdc4ab", display: "flex", justifyContent: "space-between", fontFamily: "var(--syn-font-mono)", fontSize: 10, color: "#8a7f63" }}>
                    <span>lecture-07.pdf</span>
                    <span>12 / 28</span>
                  </div>
                </div>
              </NewsprintCard>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
