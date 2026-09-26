"use client";

import Link from "next/link";
import {
  AlertCircle,
  ArrowLeft,
  Award,
  CheckCircle2,
  Mic,
  Printer,
  RotateCcw,
  TrendingUp,
  Video,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import type { InterviewReportData } from "@/features/behavioural/interview-types";

const COMPETENCY_ORDER = [
  "Course Knowledge",
  "Leadership",
  "Communication",
  "Project Management",
  "Ethics",
  "Decision Making",
  "Change Management",
];

const BAND_STYLE: Record<string, string> = {
  Exemplary: "border-emerald-200 bg-emerald-50 text-emerald-800",
  Proficient: "border-blue-200 bg-blue-50 text-[#1E3A8A]",
  Developing: "border-amber-200 bg-amber-50 text-amber-800",
  "Needs Attention": "border-rose-200 bg-rose-50 text-rose-800",
};

function measured(value: number | null | undefined, unit = "") {
  return value === null || value === undefined ? "Not captured" : `${value}${unit}`;
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 py-2">
      <dt className="text-slate-600">{label}</dt>
      <dd className="text-right font-medium tabular-nums text-slate-900">{value}</dd>
    </div>
  );
}

function ListCard({ title, icon: Icon, tone, items }: { title: string; icon: LucideIcon; tone: string; items: string[] }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
      <h3 className={`flex items-center gap-1.5 text-sm font-semibold ${tone}`}>
        <Icon className="size-4" aria-hidden="true" />
        {title}
      </h3>
      <ul className="mt-2 list-disc space-y-1.5 pl-4 text-sm text-pretty text-slate-600">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export function InterviewReport({
  report,
  onRestart,
  backHref,
  backLabel,
}: {
  report: InterviewReportData;
  onRestart: () => void;
  backHref: string;
  backLabel: string;
}) {
  const scores = COMPETENCY_ORDER.map((name) => report.competency_scores[name]).filter(Boolean);
  const video = report.video_behavioural_observations;
  const speech = report.speech_analysis;
  const narratives = [
    ["Course understanding", report.course_understanding],
    ["Communication", report.communication_assessment],
    ["Decision making", report.decision_making_assessment],
    ["Consistency across answers", report.conversation_analysis],
  ].filter(([, text]) => Boolean(text));

  return (
    <div className="mt-6 space-y-5">
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-[#0D9488]">Oral board report</p>
            <h2 className="mt-1 text-xl font-bold text-balance text-slate-900">{report.course_title}</h2>
            <p className="mt-1 text-sm text-slate-600">
              {report.officer_name} · {report.total_turns} {report.total_turns === 1 ? "answer" : "answers"} ·{" "}
              {report.total_duration_formatted}
            </p>
          </div>
          <div className="sm:text-right">
            <p className="text-4xl font-bold tabular-nums text-slate-900">
              {Math.round(report.overall_score_percent)}
              <span className="text-lg font-medium text-slate-500">/100</span>
            </p>
            <span
              className={`mt-1 inline-block rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                BAND_STYLE[report.overall_rating_band] ?? BAND_STYLE.Proficient
              }`}
            >
              {report.overall_rating_band}
            </span>
          </div>
        </div>
        <p className="mt-4 text-sm leading-relaxed text-pretty text-slate-700">{report.overall_assessment}</p>
        {report.evaluation_method && <p className="mt-2 text-xs text-pretty text-slate-500">{report.evaluation_method}</p>}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs" aria-labelledby="competency-heading">
        <h3 id="competency-heading" className="flex items-center gap-2 text-sm font-semibold text-slate-900">
          <Award className="size-4 text-[#0D9488]" aria-hidden="true" />
          Competency scores
        </h3>
        <ul className="mt-4 space-y-5">
          {scores.map((s) => (
            <li key={s.competency_name}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-medium text-slate-900">{s.competency_name}</span>
                <span className="flex items-center gap-2">
                  <span className="text-sm font-semibold tabular-nums text-slate-900">{Math.round(s.score_percent)}</span>
                  <span
                    className={`rounded-full border px-2 py-0.5 text-[11px] font-semibold ${
                      BAND_STYLE[s.rating_band] ?? BAND_STYLE.Proficient
                    }`}
                  >
                    {s.rating_band}
                  </span>
                </span>
              </div>
              <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
                <div
                  className="h-full rounded-full bg-[#2a78d6]"
                  style={{ width: `${Math.max(2, Math.min(100, s.score_percent))}%` }}
                />
              </div>
              <p className="mt-1.5 text-xs text-pretty text-slate-600">
                <span className="font-semibold text-slate-700">Evidence: </span>
                {s.key_evidence}
              </p>
              <p className="mt-0.5 text-xs text-pretty text-slate-600">
                <span className="font-semibold text-slate-700">Next step: </span>
                {s.growth_opportunity}
              </p>
            </li>
          ))}
        </ul>
      </section>

      {narratives.length > 0 && (
        <section className="grid gap-4 md:grid-cols-2">
          {narratives.map(([title, text]) => (
            <div key={title} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
              <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-pretty text-slate-600">{text}</p>
            </div>
          ))}
        </section>
      )}

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs" aria-labelledby="signals-report-heading">
        <h3 id="signals-report-heading" className="text-sm font-semibold text-slate-900">
          Delivery signals
        </h3>
        <p className="mt-1 text-xs text-pretty text-slate-500">
          Measured in your browser during your answers. Anything that could not be measured, for example with the camera
          off or with typed answers, is marked as not captured.
        </p>
        <div className="mt-4 grid gap-6 md:grid-cols-2">
          <div>
            <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <Video className="size-3.5" aria-hidden="true" />
              Camera
            </h4>
            <dl className="mt-2 divide-y divide-slate-100 text-sm">
              <Row label="Face in frame" value={measured(video.face_presence_percent, "%")} />
              <Row label="Facing the camera" value={measured(video.gaze_alignment_percent, "%")} />
              <Row label="Head steadiness" value={measured(video.posture_stability_score, "/100")} />
              <Row label="Head movement" value={video.head_movement_observed} />
            </dl>
            <p className="mt-2 text-xs text-pretty text-slate-500">{video.observable_summary}</p>
          </div>
          <div>
            <h4 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
              <Mic className="size-3.5" aria-hidden="true" />
              Voice
            </h4>
            <dl className="mt-2 divide-y divide-slate-100 text-sm">
              <Row label="Speaking pace" value={speech.pace_assessment} />
              <Row label="Filler words" value={measured(speech.filler_word_count)} />
              <Row label="Pauses" value={speech.pauses_frequency} />
            </dl>
            <p className="mt-2 text-xs text-pretty text-slate-500">{speech.delivery_cadence}</p>
          </div>
        </div>
        {report.observable_signals_disclaimer && (
          <p className="mt-4 rounded-lg bg-slate-50 p-3 text-xs text-pretty text-slate-600">
            {report.observable_signals_disclaimer}
          </p>
        )}
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <ListCard title="Strengths" icon={CheckCircle2} tone="text-emerald-700" items={report.core_strengths} />
        <ListCard title="Areas to improve" icon={AlertCircle} tone="text-amber-700" items={report.areas_for_improvement} />
        <ListCard title="Recommended learning" icon={TrendingUp} tone="text-[#0D9488]" items={report.recommended_upskilling} />
      </section>

      <details className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
        <summary className="cursor-pointer text-sm font-semibold text-slate-900">
          Full transcript ({report.transcript.length} messages)
        </summary>
        <ol className="mt-3 space-y-3">
          {report.transcript.map((entry, i) => (
            <li key={i} className="rounded-xl bg-slate-50 p-3 text-sm">
              <p className="text-xs font-semibold text-slate-500">
                {entry.speaker === "AI Interviewer" ? "Board member" : entry.speaker}
              </p>
              <p className="mt-1 leading-relaxed text-pretty text-slate-800">{entry.content}</p>
              {entry.speaker !== "AI Interviewer" && entry.behavioral_tags.length > 0 && (
                <p className="mt-1 text-[11px] text-slate-500">Competencies shown: {entry.behavioral_tags.join(", ")}</p>
              )}
            </li>
          ))}
        </ol>
      </details>

      <div className="flex flex-wrap items-center justify-between gap-3 print:hidden">
        <Link href={backHref} className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-slate-900">
          <ArrowLeft className="size-4" aria-hidden="true" />
          {backLabel}
        </Link>
        <div className="flex gap-2">
          <Button variant="outline" onClick={onRestart}>
            <RotateCcw className="size-4" aria-hidden="true" />
            New interview
          </Button>
          <Button onClick={() => window.print()}>
            <Printer className="size-4" aria-hidden="true" />
            Print report
          </Button>
        </div>
      </div>
    </div>
  );
}
