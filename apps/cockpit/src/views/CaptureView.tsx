import {
  PageHeader,
  Card,
  Tag,
  Badge,
  Eyebrow,
  Button,
  ProgressBar,
  Icon,
  GlowAccent,
} from "@synapse/ui-kit";

const SOURCES = [
  { key: "PDF", tool: "pdf_ingest", sub: "parse → md → KB", mode: "async" as const },
  { key: "WEB", tool: "web_ingest", sub: "trafilatura", mode: "sync" as const },
  { key: "AUDIO", tool: "audio_ingest", sub: "faster-whisper", mode: "async" as const },
  { key: "MAIL", tool: "mail_ingest", sub: "gmail.readonly", mode: "sync" as const },
  { key: "KB", tool: "kb_ingest", sub: "md / txt", mode: "auto" as const },
];

type RecentTone = "success" | "accent" | "neutral";
interface RecentIngest {
  name: string;
  meta: string;
  status: string;
  tone: RecentTone;
  progress?: number;
}

const RECENT: RecentIngest[] = [
  { name: "lecture-07.pdf", meta: "doc_id kb:abc123 · 14 chunks · native (pymupdf4llm)", status: "DONE", tone: "success" },
  { name: "cs7641-a2-spec.pdf", meta: "Docling · math/tables · 18/29 pages · job j-7f3a", status: "62%", tone: "accent", progress: 62 },
  { name: "lecture-recording.m4a", meta: "faster-whisper · 41:08 · job j-7f3b", status: "QUEUED", tone: "neutral" },
  { name: "Randomized Optimization — survey", meta: "web_ingest · trafilatura · doc_id kb:de91", status: "DONE", tone: "success" },
];

const ACTIVITY = [
  { id: "j-7f3a · docling", state: "running", color: "var(--syn-accent)", pulse: true },
  { id: "j-7f3b · whisper", state: "queued", color: "#3a4458", pulse: false },
  { id: "j-7e90 · reindex", state: "done", color: "var(--syn-success)", pulse: false },
  { id: "j-7c11 · ocrmypdf", state: "failed · retry", color: "var(--syn-danger)", pulse: false },
];

const MODE_TONE = { async: "danger", sync: "success", auto: "neutral" } as const;

export function CaptureView() {
  return (
    <div className="view">
      <PageHeader
        eyebrow="kb_ingest · pdf_ingest · web_ingest · audio_ingest · mail_ingest"
        title="Capture"
        description="Anything → clean markdown → KB. Vault is truth; the index is derived & rebuildable."
      />

      <div style={{ height: 18 }} />

      {/* drop zone */}
      <div
        style={{
          border: "1.5px dashed rgba(130,160,205,.26)",
          borderRadius: 9,
          background: "var(--syn-surface-sunken)",
          padding: 26,
          display: "flex",
          alignItems: "center",
          gap: 20,
          marginBottom: 16,
          position: "relative",
          overflow: "hidden",
        }}
      >
        <GlowAccent style={{ top: -40, right: 60 }} width={280} height={160} opacity={0.4} />
        <div
          style={{
            width: 52,
            height: 52,
            border: "1.5px solid var(--syn-accent-35)",
            borderRadius: 9,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "var(--syn-accent)",
            flex: "none",
          }}
        >
          <Icon name="capture" size={26} strokeWidth={1.6} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 16, fontWeight: 700 }}>
            Drop a file, paste a URL, or name a Gmail thread
          </div>
          <div className="meta" style={{ marginTop: 6 }}>
            router: pymupdf4llm (native · sync) → Docling (math / tables · queued)
          </div>
        </div>
        <div className="row">
          <Button variant="secondary" size="sm">browse</Button>
          <Button variant="primary" size="sm">paste</Button>
        </div>
      </div>

      {/* source tiles */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(5,1fr)", gap: 12, marginBottom: 18 }}>
        {SOURCES.map((s) => (
          <Card key={s.key}>
            <div className="row--between" style={{ marginBottom: 9 }}>
              <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 12, fontWeight: 700, color: "var(--syn-accent)" }}>
                {s.key}
              </span>
              <Tag tone={MODE_TONE[s.mode]}>{s.mode}</Tag>
            </div>
            <div className="meta">
              {s.tool}
              <br />
              <span style={{ color: "var(--syn-text-fainter)" }}>{s.sub}</span>
            </div>
          </Card>
        ))}
      </div>

      {/* recent + activity */}
      <div className="view__split">
        <div className="grow">
          <Eyebrow>Recent ingests</Eyebrow>
          <div className="stack" style={{ marginTop: 11 }}>
            {RECENT.map((r) => (
              <Card key={r.name} variant={r.tone === "accent" ? "active" : "default"} className="row" style={{ gap: 13 }}>
                <span
                  className={r.tone === "accent" ? "syn-dot syn-dot--accent syn-dot--pulse" : "syn-dot"}
                  style={{ width: 8, height: 8, background: r.tone === "success" ? "var(--syn-success)" : r.tone === "neutral" ? "#3a4458" : undefined }}
                />
                <div className="grow">
                  <div style={{ fontSize: 13.5, fontWeight: 700 }}>{r.name}</div>
                  <div className="meta" style={{ marginTop: 3 }}>{r.meta}</div>
                  {r.progress != null && (
                    <div style={{ marginTop: 7 }}>
                      <ProgressBar value={r.progress} tall />
                    </div>
                  )}
                </div>
                <Badge tone={r.tone === "neutral" ? "neutral" : r.tone} dot={false}>
                  {r.status}
                </Badge>
              </Card>
            ))}
          </div>
        </div>

        <div
          style={{
            width: 330,
            flex: "none",
            background: "var(--syn-surface-sunken)",
            border: "1px solid var(--syn-divider)",
            borderRadius: 8,
            padding: 14,
          }}
        >
          <div className="row--between" style={{ marginBottom: 12 }}>
            <Eyebrow>Activity · job_list</Eyebrow>
            <span className="meta">huey · sqlite</span>
          </div>
          <div className="stack" style={{ gap: 9 }}>
            {ACTIVITY.map((a) => (
              <div key={a.id} className="row" style={{ gap: 10 }}>
                <span
                  className={a.pulse ? "syn-dot syn-dot--pulse" : "syn-dot"}
                  style={{ width: 7, height: 7, background: a.color }}
                />
                <span className="grow" style={{ fontFamily: "var(--syn-font-mono)", fontSize: 11, color: "var(--syn-text-secondary)" }}>
                  {a.id}
                </span>
                <span style={{ fontFamily: "var(--syn-font-mono)", fontSize: 10, color: a.color }}>
                  {a.state}
                </span>
              </div>
            ))}
          </div>
          <div className="meta" style={{ marginTop: 13, paddingTop: 11, borderTop: "1px solid var(--syn-divider)" }}>
            one job_status protocol (§4.6)
            <br />idempotent · keyed on input hash
            <br />persistent · survives kernel restart
          </div>
        </div>
      </div>
    </div>
  );
}
