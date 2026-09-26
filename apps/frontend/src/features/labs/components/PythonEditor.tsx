"use client";

import { useEffect, useMemo, useRef } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { githubLight } from "@uiw/codemirror-theme-github";
import { Prec } from "@codemirror/state";
import { EditorView, keymap } from "@codemirror/view";

const editorTheme = EditorView.theme({
  "&": { fontSize: "13px", backgroundColor: "transparent" },
  "&.cm-focused": { outline: "none" },
  ".cm-gutters": { backgroundColor: "transparent", border: "none", color: "#94a3b8" },
  ".cm-content": {
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
    padding: "10px 0",
  },
  ".cm-line": { paddingRight: "12px" },
});

export default function PythonEditor({
  value,
  onChange,
  onRun,
  onFocus,
  label,
  readOnly = false,
}: {
  value: string;
  onChange?: (value: string) => void;
  onRun?: () => void;
  onFocus?: () => void;
  label: string;
  readOnly?: boolean;
}) {
  const onRunRef = useRef(onRun);
  useEffect(() => {
    onRunRef.current = onRun;
  });

  const extensions = useMemo(
    () => [
      python(),
      editorTheme,
      EditorView.lineWrapping,
      EditorView.contentAttributes.of({ "aria-label": label }),
      // Jupyter shortcuts: Shift+Enter or Ctrl/Cmd+Enter runs the cell.
      Prec.highest(
        keymap.of([
          { key: "Shift-Enter", run: () => (onRunRef.current?.(), true) },
          { key: "Mod-Enter", run: () => (onRunRef.current?.(), true) },
        ]),
      ),
    ],
    [label],
  );

  return (
    <CodeMirror
      value={value}
      onChange={onChange}
      onFocus={onFocus}
      extensions={extensions}
      theme={githubLight}
      editable={!readOnly}
      readOnly={readOnly}
      basicSetup={{
        foldGutter: false,
        highlightActiveLine: false,
        highlightActiveLineGutter: false,
        autocompletion: !readOnly,
      }}
    />
  );
}
