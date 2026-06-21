import { useCallback, useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { oneDark } from "@codemirror/theme-one-dark";

/**
 * IDE-style code surface (CodeMirror 6) reusing the `syn-code` window chrome.
 * `editable` toggles between the scratch/paste input (editable) and a read-only
 * render of the assistant's code. It never executes — display + edit + copy only.
 */
export interface CodeEditorProps {
  value: string;
  onChange?: (value: string) => void;
  /** Language for syntax highlighting. Only python is wired today; others fall back to plain. */
  language?: string;
  /** Editable (the paste area) vs read-only (assistant output). */
  editable?: boolean;
  /** Window-chrome label; defaults to the language tag. */
  filename?: string;
  placeholder?: string;
  minHeight?: string;
}

function languageExtensions(language: string) {
  switch (language) {
    case "python":
    case "py":
      return [python()];
    default:
      return [];
  }
}

export function CodeEditor({
  value,
  onChange,
  language = "python",
  editable = true,
  filename,
  placeholder,
  minHeight = "72px",
}: CodeEditorProps) {
  const [copied, setCopied] = useState(false);

  const copy = useCallback(() => {
    void navigator.clipboard?.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    });
  }, [value]);

  return (
    <div className="syn-code">
      <div className="syn-code__head">
        <span className="syn-code__dots">
          <span className="syn-code__dot" />
          <span className="syn-code__dot" />
        </span>
        <span className="syn-code__name">{filename ?? `${language}${editable ? " · editable" : ""}`}</span>
        <button
          type="button"
          className="syn-kbd"
          onClick={copy}
          style={{ cursor: "pointer", background: "none", border: "none" }}
        >
          {copied ? "copied" : "copy"}
        </button>
      </div>
      <CodeMirror
        value={value}
        onChange={onChange}
        editable={editable}
        readOnly={!editable}
        theme={oneDark}
        extensions={languageExtensions(language)}
        placeholder={placeholder}
        minHeight={minHeight}
        basicSetup={{
          lineNumbers: true,
          foldGutter: false,
          highlightActiveLine: editable,
          highlightActiveLineGutter: editable,
        }}
      />
    </div>
  );
}
