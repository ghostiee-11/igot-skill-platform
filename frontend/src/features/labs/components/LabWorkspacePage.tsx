"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Circle,
  Download,
  Loader2,
  Play,
  Plus,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  XCircle,
} from "lucide-react";
import confetti from "canvas-confetti";
import { Button } from "@/components/ui/button";
import { Markdown } from "@/components/shared/Markdown";
import { fetchApi } from "@/lib/api";
import type { CellExecutionResult, LabDetail, LabExecutionResult, NotebookCell } from "@/lib/types/labs";
import { NotebookCellView } from "@/features/labs/components/NotebookCellView";
import { LabAssistantPanel } from "@/features/labs/components/LabAssistantPanel";

const PythonEditor = dynamic(() => import("@/features/labs/components/PythonEditor"), { ssr: false });

// The check cell runs a sample test while practising; it is never part of the graded submission.
const CHECK_CELL_ID = "cell-code-test";
const SAVE_DELAY_MS = 600;

type SidebarTab = "instructions" | "tests";

function storageKey(labId: string) {
  return `igot-lab-notebook-${labId}`;
}

function humanizeTestName(name: string) {
  const text = name.replace(/^test_/, "").replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function errorText(err: unknown) {
  return err instanceof Error && err.message ? err.message : "Something went wrong. Try again.";
}

function starterCells(lab: LabDetail): NotebookCell[] {
  return [
    {
      id: "cell-intro",
      type: "markdown",
      content: `## ${lab.title}\n\n${lab.objective}\n\nWrite your solution in the next cell and run it with **Shift + Enter**. Use the check cell at the end to try a sample test, then select **Submit for grading**.`,
    },
    {
      id: "cell-solution",
      type: "code",
      content: lab.starter_code || "# Write your Python code here\n",
      execution_count: null,
      status: "idle",
      output: null,
    },
    {
      id: "cell-check-intro",
      type: "markdown",
      content: "### Check your work\nThis cell runs one of the graded tests against the code above. It is not included when you submit.",
    },
    {
      id: CHECK_CELL_ID,
      type: "code",
      content: lab.test_cases?.[0]?.test_code ?? "# No sample test is available for this lab.\n",
      execution_count: null,
      status: "idle",
      output: null,
    },
  ];
}

function loadSavedCells(labId: string): NotebookCell[] | null {
  try {
    const raw = window.localStorage.getItem(storageKey(labId));
    if (!raw) return null;
    const saved = JSON.parse(raw) as Pick<NotebookCell, "id" | "type" | "content">[];
    if (!Array.isArray(saved) || saved.length === 0) return null;
    return saved.map((c) => ({ ...c, execution_count: null, status: "idle", output: null }));
  } catch {
    return null;
  }
}

export default function LabWorkspacePage() {
  const { labId } = useParams<{ labId: string }>();
  const [lab, setLab] = useState<LabDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [cells, setCells] = useState<NotebookCell[]>([]);
  const [activeIndex, setActiveIndex] = useState(1);
  const [runningAll, setRunningAll] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [testResult, setTestResult] = useState<LabExecutionResult | null>(null);
  const [notice, setNotice] = useState<{ tone: "error" | "info"; text: string } | null>(null);
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>("instructions");
  const [confirmReset, setConfirmReset] = useState(false);
  const [saveState, setSaveState] = useState<"saved" | "saving">("saved");
  const [instructionsCollapsed, setInstructionsCollapsed] = useState(false);
  const [assistantOpen, setAssistantOpen] = useState(false);

  const cellsRef = useRef<NotebookCell[]>([]);
  const counterRef = useRef(1);
  const hydratedRef = useRef(false);

  useEffect(() => {
    cellsRef.current = cells;
  }, [cells]);

  useEffect(() => {
    if (!labId) return;
    fetchApi<LabDetail>(`/technical-courses/labs/${labId}`)
      .then((data) => {
        setLab(data);
        setCells(loadSavedCells(labId) ?? starterCells(data));
        hydratedRef.current = true;
      })
      .catch((err) => setLoadError(errorText(err)));
  }, [labId]);

  // Autosave the notebook in this browser so a reload does not lose work.
  useEffect(() => {
    if (!hydratedRef.current || !labId) return;
    setSaveState("saving");
    const id = window.setTimeout(() => {
      try {
        window.localStorage.setItem(storageKey(labId), JSON.stringify(cells.map(({ id, type, content }) => ({ id, type, content }))));
      } catch {
        // Storage can be unavailable (private mode); the notebook still works for this visit.
      }
      setSaveState("saved");
    }, SAVE_DELAY_MS);
    return () => window.clearTimeout(id);
  }, [cells, labId]);

  const patchCell = useCallback((id: string, patch: Partial<NotebookCell>) => {
    setCells((prev) => prev.map((c) => (c.id === id ? { ...c, ...patch } : c)));
  }, []);

  const runCell = useCallback(
    async (index: number) => {
      const current = cellsRef.current;
      const cell = current[index];
      if (!cell || cell.type !== "code") return;
      // The sandbox is stateless, so earlier code cells are sent as context, like re-running a kernel.
      const contextCode = current
        .slice(0, index)
        .filter((c) => c.type === "code" && c.id !== CHECK_CELL_ID)
        .map((c) => c.content)
        .join("\n\n");
      const count = counterRef.current++;
      patchCell(cell.id, { status: "running" });
      try {
        const res = await fetchApi<CellExecutionResult>("/technical-courses/sandbox/execute-code", {
          method: "POST",
          body: JSON.stringify({ code: cell.content, context_code: contextCode }),
        });
        const output = res.success
          ? (res.output ?? res.stdout ?? "")
          : [res.stdout, res.stderr].filter(Boolean).join("\n") || res.output || "The cell failed to run.";
        patchCell(cell.id, {
          status: res.success ? "success" : "error",
          execution_count: count,
          output,
          duration_ms: res.execution_time_ms,
        });
      } catch (err) {
        patchCell(cell.id, { status: "error", execution_count: count, output: errorText(err) });
      }
    },
    [patchCell],
  );

  const runAll = async () => {
    setRunningAll(true);
    for (let i = 0; i < cellsRef.current.length; i++) {
      if (cellsRef.current[i].type === "code") await runCell(i);
    }
    setRunningAll(false);
  };

  const addCell = (type: "code" | "markdown", afterIndex: number) => {
    const cell: NotebookCell = {
      id: `cell-${Date.now()}`,
      type,
      content: type === "code" ? "" : "",
      execution_count: null,
      status: "idle",
      output: null,
    };
    setCells((prev) => [...prev.slice(0, afterIndex + 1), cell, ...prev.slice(afterIndex + 1)]);
    setActiveIndex(afterIndex + 1);
  };

  const moveCell = (index: number, direction: "up" | "down") => {
    const target = direction === "up" ? index - 1 : index + 1;
    setCells((prev) => {
      if (target < 0 || target >= prev.length) return prev;
      const next = [...prev];
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
    setActiveIndex(target);
  };

  const deleteCell = (index: number) => {
    setCells((prev) => (prev.length <= 1 ? prev : prev.filter((_, i) => i !== index)));
    setActiveIndex((i) => Math.max(0, Math.min(i, cellsRef.current.length - 2)));
  };

  const resetNotebook = () => {
    if (!lab) return;
    setCells(starterCells(lab));
    setTestResult(null);
    setConfirmReset(false);
    setActiveIndex(1);
    setNotice({ tone: "info", text: "The notebook was reset to the starter code." });
  };

  const submit = async () => {
    if (!lab) return;
    setSubmitting(true);
    setSidebarTab("tests");
    setNotice(null);
    const code = cellsRef.current
      .filter((c) => c.type === "code" && c.id !== CHECK_CELL_ID)
      .map((c) => c.content)
      .join("\n\n");
    try {
      const res = await fetchApi<LabExecutionResult>(`/technical-courses/labs/${lab.id}/execute`, {
        method: "POST",
        body: JSON.stringify({ code }),
      });
      setTestResult(res);
      if (res.all_passed) confetti({ particleCount: 80, spread: 70, origin: { y: 0.6 } });
    } catch (err) {
      setNotice({ tone: "error", text: `Grading failed: ${errorText(err)}` });
    } finally {
      setSubmitting(false);
    }
  };

  const downloadNotebook = async () => {
    if (!lab) return;
    try {
      const res = await fetchApi<{ filename: string; content: string; mime_type: string }>("/technical-courses/notebook/export", {
        method: "POST",
        body: JSON.stringify({
          title: lab.title,
          format: "ipynb",
          cells: cellsRef.current.map((c) => ({ type: c.type, content: c.content, execution_count: c.execution_count || null })),
        }),
      });
      const url = URL.createObjectURL(new Blob([res.content], { type: res.mime_type }));
      const link = document.createElement("a");
      link.href = url;
      link.download = res.filename;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setNotice({ tone: "error", text: `Download failed: ${errorText(err)}` });
    }
  };

  if (loadError) {
    return (
      <div className="mx-auto flex min-h-[70vh] max-w-md flex-col items-center justify-center px-4 text-center">
        <AlertCircle className="size-10 text-rose-600" aria-hidden="true" />
        <h1 className="mt-3 text-lg font-semibold text-slate-900">This lab could not be loaded</h1>
        <p className="mt-1 text-sm text-pretty text-slate-600">{loadError}</p>
        <Link href="/labs" className="mt-4 text-sm font-medium text-[#1E3A8A] hover:underline">
          Back to labs
        </Link>
      </div>
    );
  }

  if (!lab) {
    return (
      <div className="flex min-h-[70vh] items-center justify-center gap-2 text-sm text-slate-500" role="status">
        <Loader2 className="size-4 animate-spin" aria-hidden="true" />
        Starting your notebook...
      </div>
    );
  }

  const busy = runningAll || submitting || cells.some((c) => c.status === "running");
  const tests = lab.test_cases ?? [];
  const resultsByName = new Map((testResult?.test_results ?? []).map((r) => [r.name, r]));
  const assistantCode = cells
    .filter((cell) => cell.type === "code" && cell.id !== CHECK_CELL_ID)
    .map((cell) => cell.content)
    .join("\n\n");
  const activeOutput = cells[activeIndex]?.output;

  return (
    <div className="flex flex-col bg-slate-50 lg:h-[calc(100vh-65px)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 bg-white px-4 py-2.5">
        <div className="flex min-w-0 items-center gap-3">
          <Link href="/labs" className="inline-flex shrink-0 items-center gap-1 text-sm font-medium text-slate-500 hover:text-slate-900">
            <ArrowLeft className="size-4" aria-hidden="true" />
            Labs
          </Link>
          <span className="h-6 w-px shrink-0 bg-slate-200" aria-hidden="true" />
          <div className="min-w-0">
            <h1 className="truncate text-sm font-semibold text-slate-900">{lab.title}</h1>
            <p className="text-xs text-slate-500">
              Python 3.11 · <span className="capitalize">{lab.difficulty}</span> · {tests.length || lab.test_cases_count || 0} graded tests
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 px-2.5 py-1 text-xs text-slate-600" role="status">
            <span className={`size-2 rounded-full ${busy ? "animate-pulse bg-[#fab219]" : "bg-[#0ca30c]"}`} aria-hidden="true" />
            {busy ? "Kernel busy" : "Kernel idle"}
          </span>
          <span className="hidden text-xs text-slate-400 sm:inline">{saveState === "saving" ? "Saving..." : "Saved in this browser"}</span>
          <Button variant="outline" size="sm" onClick={() => void runAll()} disabled={busy}>
            <Play className="size-3.5" aria-hidden="true" />
            Run all
          </Button>
          {confirmReset ? (
            <span className="flex items-center gap-1.5 text-xs text-slate-600">
              Reset to starter code?
              <Button variant="outline" size="sm" onClick={() => setConfirmReset(false)}>
                Cancel
              </Button>
              <Button variant="danger" size="sm" onClick={resetNotebook}>
                Reset
              </Button>
            </span>
          ) : (
            <Button variant="ghost" size="sm" onClick={() => setConfirmReset(true)} disabled={busy}>
              <RotateCcw className="size-3.5" aria-hidden="true" />
              Reset
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={() => void downloadNotebook()}>
            <Download className="size-3.5" aria-hidden="true" />
            .ipynb
          </Button>
          <Button size="sm" onClick={() => void submit()} disabled={submitting}>
            {submitting ? <Loader2 className="size-3.5 animate-spin" aria-hidden="true" /> : <ShieldCheck className="size-3.5" aria-hidden="true" />}
            {submitting ? "Grading..." : "Submit for grading"}
          </Button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
        <div
          className={`relative shrink-0 transition-[width] duration-200 ease-out ${
            instructionsCollapsed ? "lg:w-0" : "lg:w-[24rem] xl:w-[27rem]"
          }`}
        >
          <aside
            className={`flex min-h-0 flex-col border-b border-slate-200 bg-white transition-opacity duration-150 lg:absolute lg:inset-0 lg:h-full lg:w-full lg:border-b-0 lg:border-r ${
              instructionsCollapsed ? "lg:pointer-events-none lg:opacity-0" : "lg:opacity-100"
            }`}
          >
          <div role="tablist" aria-label="Lab panels" className="flex shrink-0 border-b border-slate-200 px-2">
            {(
              [
                ["instructions", "Instructions"],
                ["tests", "Graded tests"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                role="tab"
                type="button"
                aria-selected={sidebarTab === key}
                onClick={() => setSidebarTab(key)}
                className={`-mb-px inline-flex items-center gap-2 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors ${
                  sidebarTab === key ? "border-[#1E3A8A] text-[#1E3A8A]" : "border-transparent text-slate-500 hover:text-slate-900"
                }`}
              >
                {label}
                {key === "tests" && testResult && (
                  <span
                    className={`rounded-full px-1.5 py-0.5 text-[11px] font-semibold tabular-nums ${
                      testResult.all_passed ? "bg-[#0ca30c]/10 text-[#0a6e0a]" : "bg-[#ec835a]/15 text-[#9a3f1a]"
                    }`}
                  >
                    {testResult.passed_tests_count}/{testResult.total_tests_count}
                  </span>
                )}
              </button>
            ))}
          </div>

          <div className="max-h-[45vh] min-h-0 flex-1 overflow-y-auto p-5 lg:max-h-none">
            {sidebarTab === "instructions" ? (
              <div className="space-y-5">
                <p className="text-sm text-pretty text-slate-700">{lab.objective}</p>
                {lab.instructions && (
                  <Markdown
                    content={lab.instructions}
                    className="prose prose-sm prose-slate max-w-none prose-headings:text-balance prose-headings:text-slate-900 prose-h3:mb-2 prose-h3:mt-4 prose-code:before:content-none prose-code:after:content-none prose-code:rounded prose-code:bg-slate-100 prose-code:px-1"
                  />
                )}
                {lab.constraints && lab.constraints.length > 0 && (
                  <section>
                    <h2 className="text-sm font-semibold text-slate-900">Requirements</h2>
                    <ul className="mt-2 space-y-1.5 text-sm text-slate-700">
                      {lab.constraints.map((c, i) => (
                        <li key={i} className="flex gap-2">
                          <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-slate-400" aria-hidden="true" />
                          <span className="text-pretty">{c}</span>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}
                {lab.solution?.reference_code && (
                  <details className="group rounded-xl border border-slate-200">
                    <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-slate-700 marker:content-none">
                      Reference solution
                      <span className="block text-xs font-normal text-slate-500">Try the lab yourself before opening this.</span>
                    </summary>
                    <div className="border-t border-slate-200 p-3">
                      <div className="overflow-hidden rounded-md border border-slate-200 bg-slate-50/70">
                        <PythonEditor value={lab.solution.reference_code} label="Reference solution" readOnly />
                      </div>
                      {lab.solution.explanation && <p className="mt-2 text-xs text-pretty text-slate-600">{lab.solution.explanation}</p>}
                    </div>
                  </details>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                {testResult ? (
                  <div
                    className={`rounded-xl border p-4 ${
                      testResult.all_passed ? "border-[#0ca30c]/30 bg-[#0ca30c]/5" : "border-[#ec835a]/40 bg-[#ec835a]/5"
                    }`}
                    role="status"
                  >
                    <p className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                      {testResult.all_passed ? (
                        <CheckCircle2 className="size-5 text-[#0ca30c]" aria-hidden="true" />
                      ) : (
                        <AlertCircle className="size-5 text-[#ec835a]" aria-hidden="true" />
                      )}
                      {testResult.all_passed
                        ? "All tests passed"
                        : `${testResult.passed_tests_count} of ${testResult.total_tests_count} tests passed`}
                    </p>
                    {testResult.feedback && <p className="mt-1 text-sm text-pretty text-slate-600">{testResult.feedback}</p>}
                    <p className="mt-1 text-xs tabular-nums text-slate-500">Graded in {Math.round(testResult.execution_time_ms)} ms</p>
                  </div>
                ) : (
                  <p className="text-sm text-pretty text-slate-600">
                    Your code is checked against these tests when you submit. Submit as often as you like.
                  </p>
                )}

                <ul className="space-y-2">
                  {(tests.length ? tests.map((t) => ({ name: t.name, description: t.description })) : testResult?.test_results.map((r) => ({ name: r.name, description: undefined })) ?? []).map((test) => {
                    const result = resultsByName.get(test.name);
                    return (
                      <li key={test.name} className="rounded-xl border border-slate-200 p-3">
                        <div className="flex items-start gap-2.5">
                          {!result ? (
                            <Circle className="mt-0.5 size-4 shrink-0 text-slate-300" aria-hidden="true" />
                          ) : result.passed ? (
                            <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-[#0ca30c]" aria-hidden="true" />
                          ) : (
                            <XCircle className="mt-0.5 size-4 shrink-0 text-rose-600" aria-hidden="true" />
                          )}
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium text-slate-900">
                              {humanizeTestName(test.name)}
                              <span className="sr-only">{!result ? ", not run" : result.passed ? ", passed" : ", failed"}</span>
                            </p>
                            {test.description && <p className="text-xs text-pretty text-slate-500">{test.description}</p>}
                            {result && !result.passed && result.error && (
                              <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap rounded-md bg-rose-50 p-2 font-mono text-[12px] text-rose-800">
                                {result.error}
                              </pre>
                            )}
                          </div>
                        </div>
                      </li>
                    );
                  })}
                </ul>

                {testResult?.stderr && !testResult.all_passed && (
                  <details className="rounded-xl border border-slate-200">
                    <summary className="cursor-pointer px-4 py-2.5 text-sm font-medium text-slate-700">Error output</summary>
                    <pre className="max-h-60 overflow-auto whitespace-pre-wrap border-t border-slate-200 p-3 font-mono text-[12px] text-rose-800">
                      {testResult.stderr}
                    </pre>
                  </details>
                )}

                <Button className="w-full" onClick={() => void submit()} disabled={submitting}>
                  {submitting ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : <ShieldCheck className="size-4" aria-hidden="true" />}
                  {submitting ? "Grading..." : testResult ? "Submit again" : "Submit for grading"}
                </Button>
              </div>
            )}
          </div>
          </aside>
          <button
            type="button"
            onClick={() => setInstructionsCollapsed((collapsed) => !collapsed)}
            aria-label={instructionsCollapsed ? "Show lab instructions" : "Hide lab instructions"}
            aria-expanded={!instructionsCollapsed}
            className="absolute right-0 top-3 z-30 hidden size-7 translate-x-1/2 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-500 shadow-sm transition-colors hover:border-[#1E3A8A]/40 hover:text-[#1E3A8A] lg:inline-flex"
          >
            {instructionsCollapsed ? <ChevronRight className="size-3.5" aria-hidden="true" /> : <ChevronLeft className="size-3.5" aria-hidden="true" />}
          </button>
        </div>

        <main className="relative min-h-0 flex-1 overflow-y-auto" aria-label="Notebook">
          <div className="sticky top-0 z-20 flex items-center gap-1 border-b border-slate-200 bg-white/95 px-4 py-1.5 backdrop-blur">
            <Button variant="ghost" size="sm" onClick={() => addCell("code", activeIndex)}>
              <Plus className="size-3.5" aria-hidden="true" />
              Code
            </Button>
            <Button variant="ghost" size="sm" onClick={() => addCell("markdown", activeIndex)}>
              <Plus className="size-3.5" aria-hidden="true" />
              Text
            </Button>
            <span className="mx-1 h-5 w-px bg-slate-200" aria-hidden="true" />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => void runCell(activeIndex)}
              disabled={cells[activeIndex]?.type !== "code" || cells[activeIndex]?.status === "running"}
            >
              <Play className="size-3.5" aria-hidden="true" />
              Run cell
            </Button>
            <span className="ml-auto hidden text-xs text-slate-400 md:inline">Shift + Enter runs the selected cell</span>
          </div>

          {notice && (
            <div
              role={notice.tone === "error" ? "alert" : "status"}
              className={`mx-auto mt-4 flex max-w-4xl items-start gap-2 rounded-lg border px-3 py-2 text-sm ${
                notice.tone === "error" ? "border-rose-200 bg-rose-50 text-rose-800" : "border-blue-200 bg-blue-50 text-[#1E3A8A]"
              }`}
            >
              <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
              <p className="flex-1 text-pretty">{notice.text}</p>
              <button type="button" onClick={() => setNotice(null)} className="text-xs font-medium underline">
                Dismiss
              </button>
            </div>
          )}

          <div className="mx-auto max-w-4xl space-y-4 px-2 py-6 sm:px-4">
            {cells.map((cell, index) => (
              <NotebookCellView
                key={cell.id}
                cell={cell}
                index={index}
                active={index === activeIndex}
                canMoveUp={index > 0}
                canMoveDown={index < cells.length - 1}
                onActivate={() => setActiveIndex(index)}
                onChange={(content) => patchCell(cell.id, { content })}
                onRun={() => {
                  void runCell(index);
                  setActiveIndex(Math.min(index + 1, cells.length - 1));
                }}
                onMove={(direction) => moveCell(index, direction)}
                onDelete={() => deleteCell(index)}
              />
            ))}
            <div className="flex justify-center gap-2 pl-14">
              <Button variant="outline" size="sm" onClick={() => addCell("code", cells.length - 1)}>
                <Plus className="size-3.5" aria-hidden="true" />
                Code cell
              </Button>
              <Button variant="outline" size="sm" onClick={() => addCell("markdown", cells.length - 1)}>
                <Plus className="size-3.5" aria-hidden="true" />
                Text cell
              </Button>
            </div>
          </div>
        </main>

        {assistantOpen && (
          <LabAssistantPanel
            labId={lab.id}
            labTitle={lab.title}
            currentCode={assistantCode}
            activeOutput={activeOutput}
            onClose={() => setAssistantOpen(false)}
          />
        )}

        <button
          type="button"
          onClick={() => setAssistantOpen((open) => !open)}
          aria-label={assistantOpen ? "Close lab guide" : "Open lab guide"}
          aria-expanded={assistantOpen}
          aria-controls="lab-assistant-panel"
          title={assistantOpen ? "Close lab guide" : "Open lab guide"}
          className="fixed bottom-5 left-1/2 z-40 inline-flex size-11 -translate-x-1/2 items-center justify-center rounded-full bg-gradient-to-br from-[#1E3A8A] to-[#0D9488] text-white shadow-lg ring-4 ring-white/80 transition hover:scale-105 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-200 max-lg:data-[state=open]:hidden"
          data-state={assistantOpen ? "open" : "closed"}
        >
          <Sparkles className="size-5" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}
