import {
  PageHeader,
  Card,
  Eyebrow,
  StatTile,
  Flashcard,
  RatingButtons,
  ProgressBar,
} from "@synapse/ui-kit";

const LOAD = [42, 64, 38, 80, 54, 30, 46]; // % heights, Fri→Thu
const LOAD_LABELS = ["F", "S", "S", "M", "T", "W", "T"];

export function ReviewView() {
  return (
    <div className="view view__split" style={{ gap: 20 }}>
      {/* stats column */}
      <div style={{ width: 286, flex: "none", display: "flex", flexDirection: "column", gap: 13 }}>
        <PageHeader eyebrow="sr_review · py-fsrs FSRS-6" title="Review" />

        <Card style={{ padding: 15 }}>
          <div className="meta" style={{ marginBottom: 4 }}>deck</div>
          <div style={{ fontSize: 13.5, fontWeight: 700, marginBottom: 14 }}>
            CS7641 / randomized-optimization
          </div>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 42, fontWeight: 900, lineHeight: 0.9, color: "var(--syn-accent)" }}>12</span>
            <span className="meta" style={{ paddingBottom: 6 }}>due today</span>
          </div>
          <div style={{ display: "flex", gap: 14, marginTop: 14, paddingTop: 13, borderTop: "1px solid var(--syn-divider)" }}>
            <StatTile value="0.90" label="retention" tone="success" />
            <StatTile value="84" label="deck size" />
            <StatTile value="7d" label="streak" tone="purple" />
          </div>
        </Card>

        <Card style={{ padding: 15 }}>
          <Eyebrow>Review load · sr_stats</Eyebrow>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height: 64, marginTop: 13 }}>
            {LOAD.map((h, i) => (
              <div
                key={i}
                style={{
                  flex: 1,
                  height: `${h}%`,
                  background: i === 3 ? "var(--syn-accent)" : "#2a3346",
                  borderRadius: 2,
                }}
              />
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontFamily: "var(--syn-font-mono)", fontSize: 9, color: "var(--syn-text-ghost)" }}>
            {LOAD_LABELS.map((l, i) => (
              <span key={i}>{l}</span>
            ))}
          </div>
        </Card>
      </div>

      {/* card column */}
      <div className="view__main">
        <div className="row--between" style={{ marginBottom: 14 }}>
          <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 11, letterSpacing: ".12em", color: "var(--syn-text-faint)" }}>
            CARD 3 / 12
          </span>
          <div className="grow" style={{ margin: "0 16px" }}>
            <ProgressBar value={25} />
          </div>
          <span className="meta">sr_review(card_id, rating)</span>
        </div>

        <Flashcard
          front={
            <>
              Simulated annealing — what is the role of the temperature parameter{" "}
              <span style={{ fontFamily: "var(--syn-font-mono)", color: "var(--syn-accent)" }}>T</span>, and
              what happens to the search as{" "}
              <span style={{ fontFamily: "var(--syn-font-mono)", color: "var(--syn-accent)" }}>T → 0</span>?
            </>
          }
          back={
            <>
              T sets the probability of accepting uphill (worse) moves via the Metropolis criterion.
              High T explores freely; as the schedule cools, that probability shrinks — and as{" "}
              <span style={{ fontFamily: "var(--syn-font-mono)", color: "var(--syn-accent)" }}>T → 0</span> SA
              degenerates to greedy hill-climbing.
            </>
          }
          source={
            <>
              source · <span style={{ color: "var(--syn-accent)" }}>resources/lecture-07.pdf · p.12</span>
            </>
          }
        />

        <div style={{ marginTop: 16 }}>
          <RatingButtons intervals={{ again: "< 1m", hard: "8m", good: "2d", easy: "5d" }} />
        </div>
        <div style={{ textAlign: "center", marginTop: 11 }} className="meta">
          next_due computed by FSRS-6 · stability &amp; difficulty updated per rating
        </div>
      </div>
    </div>
  );
}
