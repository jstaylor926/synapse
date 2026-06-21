import { useState } from "react";
import { codeAssist } from "@synapse/client";
import type { Citation } from "@synapse/contracts-ts";
import {
  PageHeader,
  Badge,
  ChatBubble,
  CitationCard,
  Eyebrow,
  Button,
  Kbd,
  Icon,
  GlowAccent,
} from "@synapse/ui-kit";
import { CodeEditor } from "../components/CodeEditor";
import { splitAnswer } from "../lib/parseAnswer";

export function CodeBuddyView() {
  const [code, setCode] = useState("");
  const [input, setInput] = useState("");
  const [question, setQuestion] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string | null>(null);
  const [mode, setMode] = useState<string>("extractive");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function send() {
    const q = input.trim();
    if (!q || loading) return;
    // Embed the scratch editor's code in the question so the contract stays ReasonAsk.
    const codeBlock = code.trim() ? `\n\nMy current code:\n\`\`\`python\n${code}\n\`\`\`` : "";
    setQuestion(q);
    setInput("");
    setLoading(true);
    setError(null);
    try {
      const res = await codeAssist(q + codeBlock, 8);
      setAnswer(res.answer);
      setMode(res.mode);
      setCitations(res.citations);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setAnswer(null);
      setCitations([]);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  }

  const isGenerative = mode === "generative";

  return (
    <div className="view view__split">
      <GlowAccent style={{ top: 0, left: 240 }} width={380} opacity={0.42} />

      <div className="view__main">
        <PageHeader
          eyebrow="code_assist · grounded in ingested code + docs"
          title="Code Buddy"
          description="Paste your assignment code, ask about it, and get an editable reference back. It reasons, never executes."
          actions={<Badge dot={false}>no-exec · advice only</Badge>}
        />

        <div style={{ height: 16 }} />

        {/* Scratch / paste workspace */}
        <Eyebrow>Your code · paste &amp; edit</Eyebrow>
        <div style={{ height: 8 }} />
        <CodeEditor
          value={code}
          onChange={setCode}
          language="python"
          editable
          filename="scratch.py · editable"
          placeholder="# Paste your assignment code here, then ask about it below…"
          minHeight="150px"
        />

        <div style={{ height: 16 }} />

        {/* Question input */}
        <div
          style={{
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
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask about your code — e.g. why does my SA loop converge too fast?"
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

        <div style={{ height: 18 }} />

        {question && <ChatBubble role="user">{question}</ChatBubble>}
        {question && <div style={{ height: 18 }} />}

        <ChatBubble
          role="agent"
          name="CODE BUDDY"
          footer={
            error
              ? "request failed · is the kernel running? (bun run dev:api)"
              : answer
                ? `${isGenerative ? "generated" : "extractive floor"} · ${citations.length} citation${citations.length === 1 ? "" : "s"} · never runs your code`
                : "paste code above and ask — grounded in your ingested code + docs"
          }
        >
          {loading ? (
            <p style={{ margin: 0, color: "var(--syn-text-secondary)" }}>
              Reasoning over your code + vault… (first call warms the model)
            </p>
          ) : error ? (
            <p style={{ margin: 0, color: "var(--syn-danger)" }}>{error}</p>
          ) : answer ? (
            splitAnswer(answer).map((seg, i) =>
              seg.kind === "code" ? (
                <div key={i} style={{ margin: "12px 0" }}>
                  <CodeEditor
                    value={seg.text}
                    language={seg.lang}
                    editable
                    filename={`${seg.lang} · reference · editable`}
                  />
                </div>
              ) : (
                seg.text.split("\n\n").map((para, j) => (
                  <p key={`${i}-${j}`} style={{ marginTop: i === 0 && j === 0 ? 0 : undefined, marginBottom: 0 }}>
                    {para}
                  </p>
                ))
              ),
            )
          ) : (
            <p style={{ margin: 0, color: "var(--syn-text-fainter)" }}>
              e.g. “My A2 simulated-annealing loop converges too fast — what's wrong with my accept rule?”
            </p>
          )}
        </ChatBubble>
      </div>

      {/* Right rail: grounding + mode */}
      <div className="view__aside" style={{ width: 330 }}>
        <div className="row--between">
          <Eyebrow>Grounding · {citations.length}</Eyebrow>
          <Badge tone={isGenerative ? "success" : "neutral"}>
            {isGenerative ? "GENERATIVE" : "extractive"}
          </Badge>
        </div>

        {citations.length === 0 && !loading && (
          <span className="meta" style={{ color: "var(--syn-text-fainter)" }}>
            No grounding yet — ask a question.
          </span>
        )}

        {citations.map((c, i) => (
          <CitationCard key={`${c.source}-${i}`} index={i + 1} source={c.source} quote={c.snippet} score={c.score} />
        ))}

        {/* Saving snippets writes the vault → deferred until the gatekeeper lands (M0). */}
        <div className="row--between" style={{ marginTop: 4 }}>
          <Eyebrow>Saved snippets</Eyebrow>
          <span className="meta">soon · needs gatekeeper</span>
        </div>
        <div
          style={{
            background: "var(--syn-surface-sunken)",
            border: "1px solid var(--syn-divider)",
            borderRadius: "var(--syn-radius-md)",
            padding: 13,
            opacity: 0.55,
          }}
        >
          <div className="meta">
            Saving snippets back to the vault needs the single-writer gatekeeper (a future step).
            Edit + copy work today.
          </div>
        </div>
      </div>
    </div>
  );
}
