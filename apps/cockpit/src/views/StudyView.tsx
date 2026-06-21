import { useState } from "react";
import {
  PageHeader,
  Card,
  Tag,
  Eyebrow,
  Button,
  Stepper,
  SegmentedControl,
  NewsprintCard,
  Icon,
} from "@synapse/ui-kit";

interface GeneratedCard {
  n: string;
  q: string;
  a: string;
  source: string;
  added: boolean;
}

const CARDS: GeneratedCard[] = [
  { n: "01", q: "What acceptance rule lets SA escape local optima?", a: "The Metropolis criterion — accept worse moves with probability e^(−ΔE/T).", source: "source · lecture-07 · p.12", added: true },
  { n: "02", q: "In a GA, what does crossover contribute that mutation does not?", a: "Recombination of partial solutions (schemata) from two parents — large, structured jumps.", source: "source · notes/sa-vs-ga", added: true },
  { n: "03", q: "Why is SA's memory footprint smaller than a GA's?", a: "SA holds one current solution; a GA maintains an entire population each generation.", source: "source · lecture-07 · p.14", added: false },
];

export function StudyView() {
  const [count, setCount] = useState(15);
  const [type, setType] = useState("Flashcards");

  return (
    <div className="view view__split" style={{ gap: 20 }}>
      {/* controls */}
      <div style={{ width: 322, flex: "none", display: "flex", flexDirection: "column", gap: 13 }}>
        <PageHeader
          eyebrow="study_flashcards · study_quiz · study_cheatsheet"
          title="Study"
        />

        <Card style={{ padding: 16, display: "flex", flexDirection: "column", gap: 15 }}>
          <div>
            <Eyebrow>Topic</Eyebrow>
            <div
              className="row--between"
              style={{
                marginTop: 7,
                background: "rgba(139,92,240,.1)",
                border: "1px solid rgba(139,92,240,.34)",
                borderRadius: 6,
                padding: "10px 12px",
              }}
            >
              <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 12, color: "#cdbef0" }}>
                randomized-optimization
              </span>
              <Icon name="chevron-down" size={13} strokeWidth={1.6} style={{ color: "var(--syn-purple-text)" }} />
            </div>
          </div>

          <div>
            <Eyebrow>Count</Eyebrow>
            <div style={{ marginTop: 7 }}>
              <Stepper value={count} onChange={setCount} min={1} max={50} />
            </div>
          </div>

          <div>
            <Eyebrow>Type</Eyebrow>
            <div style={{ marginTop: 7 }}>
              <SegmentedControl
                options={["Flashcards", "Quiz", "Cheatsheet"]}
                value={type}
                onChange={setType}
                block
              />
            </div>
          </div>

          <div>
            <Eyebrow>Scope · from KB</Eyebrow>
            <div className="row" style={{ marginTop: 7, flexWrap: "wrap", gap: 6 }}>
              <Tag tone="accent">lecture-07</Tag>
              <Tag tone="accent">notes/sa-vs-ga</Tag>
            </div>
          </div>

          <Button variant="primary" block>
            GENERATE <Icon name="plus" size={13} strokeWidth={2.2} />
          </Button>
          <div style={{ textAlign: "center" }} className="meta">
            grounded in KB · every card cites its source
          </div>
        </Card>
      </div>

      {/* output */}
      <div className="view__main">
        <div className="row--between" style={{ marginBottom: 13 }}>
          <Eyebrow>Output · {count} cards · source-cited</Eyebrow>
          <Tag tone="accent" style={{ padding: "6px 11px" }}>add all → sr_add</Tag>
        </div>

        <div className="stack" style={{ gap: 10 }}>
          {CARDS.map((c) => (
            <Card key={c.n} className="row" style={{ gap: 14, alignItems: "flex-start", padding: "14px 16px" }}>
              <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 11, color: "var(--syn-accent)", marginTop: 2 }}>
                {c.n}
              </span>
              <div className="grow">
                <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 5 }}>{c.q}</div>
                <div style={{ fontSize: 13, color: "var(--syn-text-dim)", lineHeight: 1.5 }}>{c.a}</div>
                <div className="meta" style={{ marginTop: 7 }}>{c.source}</div>
              </div>
              <span
                style={{
                  width: 20,
                  height: 20,
                  border: c.added ? "1.5px solid var(--syn-success)" : "1.5px solid rgba(130,160,205,.24)",
                  borderRadius: 4,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--syn-success)",
                  flex: "none",
                }}
              >
                {c.added && <Icon name="check" size={11} strokeWidth={2.4} />}
              </span>
            </Card>
          ))}
        </div>

        {/* cheatsheet peek on newsprint */}
        <div style={{ marginTop: 18 }}>
          <Eyebrow>study_cheatsheet · markdown preview</Eyebrow>
          <div style={{ marginTop: 11, maxWidth: 560 }}>
            <NewsprintCard title="Randomized Optimization — Cheat Sheet">
              <span style={{ color: "var(--syn-paper-red)", fontWeight: 700 }}># SA</span> — single
              solution · temp schedule · Metropolis accept
              <br />
              <span style={{ color: "var(--syn-paper-red)", fontWeight: 700 }}># GA</span> — population ·
              crossover + mutation · implicit parallelism
              <br />
              <span style={{ color: "var(--syn-paper-red)", fontWeight: 700 }}># MIMIC</span> — models
              structure · estimates distribution per iter
              <br />
              <span style={{ color: "var(--syn-paper-ink-soft)" }}>
                — pick SA: rugged + cheap evals · pick GA: recombinable structure
              </span>
            </NewsprintCard>
          </div>
        </div>
      </div>
    </div>
  );
}
