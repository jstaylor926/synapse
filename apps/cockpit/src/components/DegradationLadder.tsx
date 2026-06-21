/**
 * The "degradation ladder" card pinned to the bottom of the nav rail — a
 * status read-out of which models are live vs idle, plus the active vault.
 * Placeholder data; a later milestone wires this to the kernel's health probe.
 */

const ROWS = [
  { label: "fastembed · local", state: "up" },
  { label: "anthropic · litellm", state: "up" },
  { label: "ollama · idle", state: "idle" },
] as const;

export function DegradationLadder() {
  return (
    <div
      style={{
        padding: 12,
        background: "var(--syn-surface-input)",
        border: "1px solid var(--syn-border-subtle)",
        borderRadius: "var(--syn-radius-md)",
      }}
    >
      <div
        style={{
          fontFamily: "var(--syn-font-mono)",
          fontSize: 9.5,
          letterSpacing: "0.14em",
          color: "var(--syn-text-ghost)",
          marginBottom: 9,
        }}
      >
        DEGRADATION LADDER
      </div>
      {ROWS.map((row) => (
        <div key={row.label} style={{ display: "flex", alignItems: "center", gap: 7, marginBottom: 6 }}>
          <span
            className="syn-dot"
            style={{ background: row.state === "up" ? "var(--syn-success)" : "#3a4458" }}
          />
          <span
            style={{
              fontFamily: "var(--syn-font-mono)",
              fontSize: 10.5,
              color: row.state === "up" ? "var(--syn-text-dim)" : "var(--syn-text-fainter)",
            }}
          >
            {row.label}
          </span>
        </div>
      ))}
      <div
        style={{
          marginTop: 10,
          paddingTop: 9,
          borderTop: "1px solid var(--syn-border-subtle)",
          fontFamily: "var(--syn-font-mono)",
          fontSize: 10,
          color: "var(--syn-text-fainter)",
        }}
      >
        vault · cs7641 · 1,284 chunks
      </div>
    </div>
  );
}
