import type { CSSProperties } from "react";
import {
  PageHeader,
  Card,
  Tag,
  Badge,
  Stamp,
  Eyebrow,
  Divider,
  GlowAccent,
} from "@synapse/ui-kit";

interface AgendaItem {
  label: string;
  title: string;
  meta: string;
  tone: "accent" | "purple" | "neutral";
}

const AGENDA: AgendaItem[] = [
  { label: "NOW · 18:00", title: "a2-t3 — Drill RO flashcards", meta: "45m · study_flashcards · plan_run", tone: "accent" },
  { label: "NEXT · 18:45", title: "sr_review — 12 cards due", meta: "FSRS-6 · randomized-optimization", tone: "purple" },
  { label: "TONIGHT · FREE", title: "2h 10m open", meta: "gcal free/busy · read-only", tone: "neutral" },
];

interface PlannerTask {
  id: string;
  title: string;
  estimate: string;
  state: "done" | "doing" | "active" | "todo";
  topic?: string;
  resources: string;
  binding: string;
}

const TASKS: PlannerTask[] = [
  { id: "a2-t1", title: "Read L07 + notes", estimate: "30m", state: "done", topic: "randomized-optimization", resources: "lecture-07 · notes/sa-vs-ga", binding: "reason_ask" },
  { id: "a2-t2", title: "Implement SA vs GA", estimate: "90m", state: "doing", topic: "randomized-optimization", resources: "notes/sa-vs-ga", binding: "code_assist" },
  { id: "a2-t3", title: "Drill RO flashcards", estimate: "45m · now", state: "active", topic: "randomized-optimization", resources: "lecture-07 · notes/sa-vs-ga", binding: "study_flashcards { n: 15 }" },
  { id: "a2-t4", title: "Write-up draft", estimate: "60m", state: "todo", resources: "notes/sa-vs-ga · lecture-08", binding: "study_cheatsheet" },
];

const TONE_TEXT = { accent: "var(--syn-accent)", purple: "var(--syn-purple-text)", neutral: "var(--syn-text-fainter)" };

function TaskRow({ task }: { task: PlannerTask }) {
  const bulletStyle =
    task.state === "done"
      ? { border: "2px solid var(--syn-success)", background: "var(--syn-success)" }
      : task.state === "doing"
        ? { border: "2px solid var(--syn-success)", boxShadow: "inset 0 0 0 2px var(--syn-success)" }
        : task.state === "active"
          ? { border: "2px solid var(--syn-accent)" }
          : { border: "2px solid #3a4458" };

  return (
    <Card variant={task.state === "active" ? "active" : "default"}>
      <div className="row" style={{ gap: 9, marginBottom: 9 }}>
        <span style={{ width: 11, height: 11, borderRadius: "50%", flex: "none", ...bulletStyle }} />
        <span className="grow" style={{ fontSize: 13.5, fontWeight: 700, color: task.state === "todo" ? "var(--syn-text-secondary)" : undefined }}>
          {task.id} · {task.title}
        </span>
        <Tag tone={task.state === "active" ? "accent" : "neutral"}>{task.estimate}</Tag>
      </div>
      {task.topic && (
        <div style={{ marginBottom: 8 }}>
          <Tag tone="purple">[[{task.topic}]]</Tag>
        </div>
      )}
      <div className="meta">
        resources:{" "}
        {task.resources.split(" · ").map((r, i) => (
          <span key={r}>
            {i > 0 && " · "}
            <span style={{ color: "var(--syn-accent)" }}>{r}</span>
          </span>
        ))}
      </div>
      <div className="meta row" style={{ marginTop: 8, gap: 6 }}>
        <span style={{ color: task.state === "active" ? "var(--syn-accent)" : "var(--syn-text-fainter)" }}>
          binding ⛓
        </span>
        <span style={{ color: task.state === "active" ? "var(--syn-accent-text)" : "var(--syn-text-dimmer)" }}>
          {task.binding}
        </span>
      </div>
    </Card>
  );
}

export function PlannerView() {
  return (
    <div className="view">
      <GlowAccent style={{ top: -30, right: 120 }} width={340} opacity={0.5} />

      <PageHeader
        eyebrow="plan_breakdown → plan_schedule → plan_agenda"
        title="Planner"
        description="One ontology — a class assignment and a job application are the same shape: a deadline, source material, and tasks."
        actions={
          <>
            <Stamp>Due · 06·27</Stamp>
            <div style={{ display: "flex", flexDirection: "column", gap: 7, alignItems: "flex-end" }}>
              <Badge tone="accent">open · 4 tasks</Badge>
              <Badge tone="purple">scheduled · 5 blocks</Badge>
            </div>
          </>
        }
      />

      <div style={{ height: 18 }} />

      {/* agenda strip */}
      <div style={{ display: "flex", gap: 12, marginBottom: 18 }}>
        {AGENDA.map((a) => (
          <Card
            key={a.label}
            variant={a.tone === "neutral" ? "default" : "accent-edge"}
            style={{
              flex: 1,
              ...(a.tone === "purple"
                ? { borderColor: "rgba(139,92,240,.32)", borderLeftColor: "var(--syn-purple)" }
                : {}),
            }}
          >
            <div style={{ fontFamily: "var(--syn-font-mono)", fontSize: 10, letterSpacing: ".12em", color: TONE_TEXT[a.tone], marginBottom: 7 }}>
              {a.label}
            </div>
            <div style={{ fontSize: 14.5, fontWeight: 700 }}>{a.title}</div>
            <div className="meta" style={{ marginTop: 5 }}>{a.meta}</div>
          </Card>
        ))}
      </div>

      {/* two-column body */}
      <div className="view__split">
        {/* breakdown */}
        <div style={{ width: 368, flex: "none", display: "flex", flexDirection: "column", gap: 11 }}>
          <div className="row--between">
            <Eyebrow>Breakdown</Eyebrow>
            <span className="meta">plan_breakdown()</span>
          </div>

          <Card variant="sunken">
            <div className="row" style={{ gap: 8, marginBottom: 7 }}>
              <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 13, fontWeight: 700 }}>cs7641-a2</span>
              <Tag tone="accent">type: assignment</Tag>
            </div>
            <div className="meta">
              course: <span style={{ color: "var(--syn-purple-text)" }}>[[CS7641]]</span> · due:{" "}
              <span style={{ color: "var(--syn-danger-text)" }}>2026-06-27</span>
              <br />spec: <span style={{ color: "var(--syn-accent)" }}>[[resources/cs7641-a2-spec]]</span>
            </div>
          </Card>

          {TASKS.map((t) => (
            <TaskRow key={t.id} task={t} />
          ))}

          <Divider label="same ontology" />

          <Card variant="dashed-purple">
            <div className="row" style={{ gap: 8, marginBottom: 7 }}>
              <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 13, fontWeight: 700 }}>acme-frontend</span>
              <Tag tone="purple">type: assignment · job</Tag>
            </div>
            <div className="meta">
              apply-by: <span style={{ color: "var(--syn-danger-text)" }}>2026-06-24</span> · 3 tasks
            </div>
            <div className="meta" style={{ marginTop: 9, display: "flex", flexDirection: "column", gap: 6 }}>
              <span>tailor resume → <span style={{ color: "var(--syn-accent)" }}>study_cheatsheet</span></span>
              <span>research company → <span style={{ color: "var(--syn-accent)" }}>web_ingest · mail_ingest</span></span>
              <span>drill STAR → <span style={{ color: "var(--syn-purple-text)" }}>sr_add · sr_review</span></span>
            </div>
          </Card>
        </div>

        {/* schedule */}
        <div
          style={{
            flex: 1,
            minWidth: 0,
            background: "var(--syn-surface-sunken)",
            border: "1px solid var(--syn-border)",
            borderRadius: 8,
            padding: "16px 16px 18px",
          }}
        >
          <div className="row--between" style={{ marginBottom: 14 }}>
            <div>
              <Eyebrow>Schedule · plan_schedule</Eyebrow>
              <div style={{ fontSize: 15, fontWeight: 700, marginTop: 5 }}>
                Backward from the deadline, into free blocks
              </div>
            </div>
            <div className="row" style={{ gap: 13 }}>
              {[
                { c: "var(--syn-accent)", l: "study" },
                { c: "var(--syn-purple)", l: "review" },
                { c: "var(--syn-success)", l: "code" },
              ].map((x) => (
                <span key={x.l} className="row meta" style={{ gap: 5 }}>
                  <span style={{ width: 9, height: 9, borderRadius: 2, background: x.c }} />
                  {x.l}
                </span>
              ))}
            </div>
          </div>

          <WeekGrid />

          <div className="meta" style={{ marginTop: 13 }}>
            plan_sync_external() · calendar.readonly · never writes back · optional one-way .ics out
          </div>
        </div>
      </div>
    </div>
  );
}

/* A compact week grid. Blocks are absolutely positioned by (top, height) px. */
interface Block {
  top: number;
  height: number;
  time: string;
  title: string;
  tone: "accent" | "purple" | "code" | "busy" | "due";
}

const DAYS: { label: string; due?: boolean; blocks: Block[] }[] = [
  { label: "MON 22", blocks: [{ top: 140, height: 50, time: "18:00 · 45m", title: "a2-t3 · RO cards", tone: "accent" }] },
  { label: "TUE 23", blocks: [
    { top: 0, height: 64, time: "16:00 · seminar", title: "gcal · busy", tone: "busy" },
    { top: 210, height: 64, time: "19:00 · 60m", title: "a2-t1 · Read L07", tone: "accent" },
  ] },
  { label: "WED 24", blocks: [{ top: 175, height: 50, time: "18:30 · 45m", title: "sr_review · 12", tone: "purple" }] },
  { label: "THU 25", blocks: [
    { top: 140, height: 64, time: "18:00 · gym", title: "gcal · busy", tone: "busy" },
    { top: 280, height: 100, time: "20:00 · 90m", title: "a2-t2 · Code SA/GA", tone: "code" },
  ] },
  { label: "FRI 26", blocks: [{ top: 70, height: 64, time: "17:00 · 60m", title: "a2-t4 · Write-up", tone: "accent" }] },
  { label: "SAT 27", due: true, blocks: [{ top: 0, height: 34, time: "09:00 · submit A2", title: "", tone: "due" }] },
];

const BLOCK_STYLE: Record<Block["tone"], CSSProperties> = {
  accent: { background: "color-mix(in srgb, var(--syn-accent) 16%, #0d1320)", border: "1px solid var(--syn-accent-35)", borderLeft: "3px solid var(--syn-accent)", color: "var(--syn-accent)" },
  purple: { background: "rgba(139,92,240,.15)", border: "1px solid rgba(139,92,240,.4)", borderLeft: "3px solid var(--syn-purple)", color: "var(--syn-purple-text)" },
  code: { background: "rgba(95,229,114,.13)", border: "1px solid rgba(95,229,114,.38)", borderLeft: "3px solid var(--syn-success)", color: "#8fe89a" },
  busy: { background: "repeating-linear-gradient(45deg,#141a26,#141a26 6px,#10151f 6px,#10151f 12px)", border: "1px dashed rgba(130,160,205,.22)", color: "#6b7686" },
  due: { background: "rgba(255,77,87,.13)", border: "1px solid rgba(255,77,87,.4)", borderLeft: "3px solid var(--syn-danger)", color: "var(--syn-danger-text)" },
};

function WeekGrid() {
  return (
    <div style={{ display: "flex", gap: 0, marginTop: 14 }}>
      {/* time axis */}
      <div style={{ width: 40, flex: "none", paddingTop: 30 }}>
        {["16:00", "17:00", "18:00", "19:00", "20:00", "21:00"].map((t) => (
          <div key={t} style={{ height: 70, fontFamily: "var(--syn-font-mono)", fontSize: 9.5, color: "var(--syn-text-ghost)", textAlign: "right", paddingRight: 7 }}>
            {t}
          </div>
        ))}
      </div>
      {/* day columns */}
      <div style={{ flex: 1, display: "grid", gridTemplateColumns: "repeat(6,1fr)", gap: 6 }}>
        {DAYS.map((d) => (
          <div key={d.label}>
            <div style={{ height: 24, display: "flex", alignItems: "center", justifyContent: "center" }}>
              {d.due ? (
                <span style={{ fontFamily: "var(--syn-font-display)", fontSize: 10, color: "var(--syn-danger)", border: "1px solid var(--syn-danger)", borderRadius: 2, padding: "1px 5px", letterSpacing: ".04em" }}>
                  {d.label} · DUE
                </span>
              ) : (
                <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 10.5, color: "var(--syn-text-dim)", letterSpacing: ".04em" }}>
                  {d.label}
                </span>
              )}
            </div>
            <div
              style={{
                position: "relative",
                height: 420,
                border: d.due ? "1px solid rgba(255,77,87,.22)" : "1px solid var(--syn-border-subtle)",
                borderRadius: 4,
                background: "var(--syn-surface-cal)",
                backgroundImage:
                  "repeating-linear-gradient(to bottom,transparent 0,transparent 69px,rgba(130,160,205,.06) 69px,rgba(130,160,205,.06) 70px)",
              }}
            >
              {d.blocks.map((b, i) => (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    left: 4,
                    right: 4,
                    top: b.top,
                    height: b.height,
                    borderRadius: 3,
                    padding: "5px 7px",
                    overflow: "hidden",
                    ...BLOCK_STYLE[b.tone],
                  }}
                >
                  <div style={{ fontFamily: "var(--syn-font-mono)", fontSize: 9 }}>{b.time}</div>
                  {b.title && (
                    <div style={{ fontSize: 11, fontWeight: 700, lineHeight: 1.2, marginTop: 2, color: "var(--syn-text)" }}>
                      {b.title}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
