"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { ArrowDown, ArrowUp, CheckCircle2, Loader2, Pencil, Play, Trash2, XCircle } from "lucide-react";
import { Markdown } from "@/components/shared/Markdown";
import type { NotebookCell } from "@/lib/types/labs";

// CodeMirror touches the DOM, so the editor only renders in the browser.
const PythonEditor = dynamic(() => import("@/features/labs/components/PythonEditor"), {
  ssr: false,
  loading: () => <div className="h-20 animate-pulse rounded-md bg-slate-100" />,
});

function IconButton({
  label,
  onClick,
  disabled,
  children,
  tone = "default",
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
  tone?: "default" | "danger" | "run";
}) {
  const tones = {
    default: "text-slate-500 hover:bg-slate-100 hover:text-slate-900",
    danger: "text-slate-500 hover:bg-rose-50 hover:text-rose-700",
    run: "text-[#1E3A8A] hover:bg-blue-50",
  };
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      disabled={disabled}
      onClick={(e) => {
        e.stopPropagation();
        onClick();
      }}
      className={`inline-flex size-7 items-center justify-center rounded-md transition-colors disabled:pointer-events-none disabled:opacity-30 ${tones[tone]}`}
    >
      {children}
    </button>
  );
}

export function NotebookCellView({
  cell,
  index,
  active,
  canMoveUp,
  canMoveDown,
  onActivate,
  onChange,
  onRun,
  onMove,
  onDelete,
}: {
  cell: NotebookCell;
  index: number;
  active: boolean;
  canMoveUp: boolean;
  canMoveDown: boolean;
  onActivate: () => void;
  onChange: (content: string) => void;
  onRun: () => void;
  onMove: (direction: "up" | "down") => void;
  onDelete: () => void;
}) {
  const [editingMarkdown, setEditingMarkdown] = useState(cell.type === "markdown" && !cell.content.trim());
  const running = cell.status === "running";
  const prompt = cell.type === "code" ? `[${running ? "*" : (cell.execution_count ?? " ")}]:` : "";

  return (
    <div className="group flex gap-2" onClick={onActivate}>
      <div className="w-12 shrink-0 select-none pt-3 text-right font-mono text-xs text-slate-400" aria-hidden="true">
        {prompt}
      </div>
      <div
        className={`relative min-w-0 flex-1 rounded-lg border-l-4 transition-colors ${
          active ? "border-l-[#2a78d6] bg-white shadow-xs ring-1 ring-slate-200" : "border-l-transparent hover:bg-white/60"
        }`}
      >
        <div
          className={`absolute -top-3 right-2 z-10 flex items-center gap-0.5 rounded-lg border border-slate-200 bg-white px-1 shadow-xs transition-opacity ${
            active ? "opacity-100" : "opacity-0 group-hover:opacity-100 focus-within:opacity-100"
          }`}
        >
          {cell.type === "code" ? (
            <IconButton label={`Run cell ${index + 1}`} onClick={onRun} disabled={running} tone="run">
              <Play className="size-3.5" aria-hidden="true" />
            </IconButton>
          ) : (
            <IconButton label={editingMarkdown ? "Preview text" : "Edit text"} onClick={() => setEditingMarkdown(!editingMarkdown)}>
              <Pencil className="size-3.5" aria-hidden="true" />
            </IconButton>
          )}
          <IconButton label="Move cell up" onClick={() => onMove("up")} disabled={!canMoveUp}>
            <ArrowUp className="size-3.5" aria-hidden="true" />
          </IconButton>
          <IconButton label="Move cell down" onClick={() => onMove("down")} disabled={!canMoveDown}>
            <ArrowDown className="size-3.5" aria-hidden="true" />
          </IconButton>
          <IconButton label="Delete cell" onClick={onDelete} tone="danger">
            <Trash2 className="size-3.5" aria-hidden="true" />
          </IconButton>
        </div>

        {cell.type === "code" ? (
          <div className="m-2 overflow-hidden rounded-md border border-slate-200 bg-slate-50/70">
            <PythonEditor
              value={cell.content}
              onChange={onChange}
              onRun={onRun}
              onFocus={onActivate}
              label={`Code cell ${index + 1}`}
            />
          </div>
        ) : editingMarkdown ? (
          <textarea
            value={cell.content}
            onChange={(e) => onChange(e.target.value)}
            onFocus={onActivate}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.shiftKey || e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setEditingMarkdown(false);
              }
            }}
            aria-label={`Text cell ${index + 1}, markdown`}
            rows={Math.max(3, cell.content.split("\n").length)}
            className="m-2 block w-[calc(100%-1rem)] resize-y rounded-md border border-slate-200 bg-slate-50/70 p-3 font-mono text-[13px] leading-relaxed text-slate-800 focus:border-[#2a78d6] focus:outline-none"
            placeholder="Write notes in markdown. Shift + Enter to preview."
          />
        ) : (
          <div onDoubleClick={() => setEditingMarkdown(true)} className="px-4 py-3" title="Double-click to edit">
            <Markdown
              content={cell.content || "_Empty text cell. Double-click to edit._"}
              className="prose prose-sm prose-slate max-w-none prose-headings:mb-2 prose-headings:mt-1 prose-headings:text-balance prose-p:my-1.5 prose-p:text-pretty prose-code:before:content-none prose-code:after:content-none prose-code:rounded prose-code:bg-slate-100 prose-code:px-1"
            />
          </div>
        )}

        {cell.type === "code" && running && (
          <p className="flex items-center gap-1.5 px-4 pb-3 text-xs text-slate-500" role="status">
            <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
            Running in the Python sandbox...
          </p>
        )}

        {cell.type === "code" && !running && cell.output !== null && cell.output !== undefined && (
          <div
            className={`mx-2 mb-2 rounded-md border px-3 py-2 ${
              cell.status === "error" ? "border-rose-200 bg-rose-50" : "border-slate-100 bg-white"
            }`}
          >
            <pre
              className={`max-h-80 overflow-auto whitespace-pre-wrap break-words font-mono text-[13px] leading-relaxed ${
                cell.status === "error" ? "text-rose-800" : "text-slate-800"
              }`}
            >
              {cell.output || "Cell ran with no output."}
            </pre>
            <p className="mt-1.5 flex items-center gap-1 text-[11px] text-slate-500">
              {cell.status === "error" ? (
                <XCircle className="size-3 text-rose-600" aria-hidden="true" />
              ) : (
                <CheckCircle2 className="size-3 text-[#0ca30c]" aria-hidden="true" />
              )}
              {cell.status === "error" ? "Error" : "Done"}
              {cell.duration_ms !== undefined && <span className="tabular-nums"> · {Math.round(cell.duration_ms)} ms</span>}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
