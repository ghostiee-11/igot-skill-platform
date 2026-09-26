"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowRight, Clock, FileQuestion, Sparkles } from "lucide-react";
import { ButtonLink } from "@/components/ui/button-link";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorNotice } from "@/components/shared/ErrorNotice";
import { fetchApi } from "@/lib/api";
import type { DomainCourse, DomainDetail } from "@/lib/types/competency";
import {
  DOMAINS,
  DOMAIN_ACCENT_CLASS,
  LEVEL_MAX,
  PRACTICE_DESCRIPTIONS,
  isDomainCode,
  levelLabel,
} from "@/features/competency/domains";
import { DomainNav, GapChip, LevelBar, LevelLegend, StatTile } from "@/features/competency/components/CompetencyUI";

const EVIDENCE_LABELS: Record<string, string> = {
  self_declared: "Self-declared",
  assessment: "From assessments",
  inferred: "Inferred",
};

function CourseCard({ course }: { course: DomainCourse }) {
  return (
    <Link
      href={`/courses/${course.id}`}
      className="group flex flex-col rounded-2xl border border-slate-200 bg-white p-5 shadow-xs transition hover:border-[#1E3A8A]/40 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A]"
    >
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-500">
        {course.recommended && (
          <span className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-2 py-0.5 font-medium text-[#1E3A8A]">
            <Sparkles className="size-3" aria-hidden="true" />
            Recommended
          </span>
        )}
        <span className="capitalize">{course.difficulty}</span>
        <span aria-hidden="true">·</span>
        <span className="inline-flex items-center gap-1 tabular-nums">
          <Clock className="size-3.5" aria-hidden="true" />
          {course.duration_hours} h
        </span>
      </div>
      <h4 className="mt-2 text-base font-semibold text-balance text-slate-900 group-hover:text-[#1E3A8A]">{course.title}</h4>
      <p className="mt-1.5 line-clamp-3 text-sm text-pretty text-slate-600">{course.reason ?? course.overview}</p>
      <span className="mt-auto inline-flex items-center gap-1 pt-4 text-sm font-medium text-[#1E3A8A]">
        View course
        <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
      </span>
    </Link>
  );
}

export default function CompetencyDomainPage() {
  const params = useParams<{ domain: string }>();
  const code = params.domain;
  const [detail, setDetail] = useState<DomainDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isDomainCode(code)) return;
    setDetail(null);
    setError(null);
    fetchApi<DomainDetail>(`/competency/domains/${code}`)
      .then(setDetail)
      .catch((e: Error) => setError(e.message));
  }, [code]);

  if (!isDomainCode(code)) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-16 text-center sm:px-6">
        <h1 className="text-2xl font-bold text-balance text-slate-900">Competency domain not found</h1>
        <p className="mt-2 text-pretty text-slate-600">The four domains are Statistical, Technical, Digital Governance and Behavioural.</p>
        <ButtonLink href="/competency" className="mt-6">
          Back to competency profile
        </ButtonLink>
      </div>
    );
  }

  const meta = DOMAINS[code];
  const Icon = meta.icon;
  const analysed = detail?.current_level !== null && detail?.current_level !== undefined;
  const target = analysed ? detail!.target_level : null;
  const competencies = detail?.competencies ?? [];
  const belowTarget = target !== null ? competencies.filter((c) => c.level < target).length : 0;
  const focus =
    target !== null && competencies.length
      ? [...competencies].sort((a, b) => a.level - b.level)[0]
      : null;
  const recommended = (detail?.courses ?? []).filter((c) => c.recommended);
  const others = (detail?.courses ?? []).filter((c) => !c.recommended);

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <DomainNav active={code} />

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs">
        <div className={`h-1 ${DOMAIN_ACCENT_CLASS[code]}`} aria-hidden="true" />
        <div className="grid gap-6 p-6 lg:grid-cols-[minmax(0,1fr)_28rem] lg:items-center">
          <div className="flex gap-4">
            <span className="flex size-12 shrink-0 items-center justify-center rounded-xl bg-slate-100 text-slate-700">
              <Icon className="size-6" aria-hidden="true" />
            </span>
            <div>
              <p className="text-sm font-medium text-slate-500">Competency domain</p>
              <h1 className="text-2xl font-bold text-balance text-slate-900 sm:text-3xl">{meta.label}</h1>
              <p className="mt-2 max-w-2xl text-pretty text-slate-600">{meta.description}</p>
            </div>
          </div>

          {!detail && !error && <Skeleton className="h-24 w-full" />}
          {detail && analysed && (
            <dl className="grid grid-cols-3 gap-3">
              <StatTile
                label="Your level"
                value={
                  <>
                    {detail.current_level!.toFixed(1)}
                    <span className="text-sm font-normal text-slate-500">/{LEVEL_MAX}</span>
                  </>
                }
                detail={levelLabel(detail.current_level!)}
              />
              <StatTile label="Role target" value={detail.target_level!.toFixed(1)} detail={levelLabel(detail.target_level!)} />
              <StatTile
                label="Gap"
                value={Math.max(0, detail.gap!).toFixed(1)}
                detail={<GapChip gap={detail.gap} />}
              />
            </dl>
          )}
          {detail && !analysed && (
            <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
              <p className="text-sm text-pretty text-slate-600">
                Run a gap analysis to compare your level in this domain with the target for your role.
              </p>
              <ButtonLink href="/competency" size="sm" className="mt-3">
                Run gap analysis
              </ButtonLink>
            </div>
          )}
        </div>
      </section>

      {error && <ErrorNotice message={error} />}

      <div className="grid gap-6 lg:grid-cols-3">
        <section aria-labelledby="competencies-heading" className="rounded-2xl border border-slate-200 bg-white shadow-xs lg:col-span-2">
          <div className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4">
            <div>
              <h2 id="competencies-heading" className="text-base font-semibold text-slate-900">
                Competencies
              </h2>
              {detail && (
                <p className="text-sm text-slate-500">
                  {target !== null
                    ? `${belowTarget} of ${competencies.length} below your role target`
                    : `${competencies.length} competencies in this domain`}
                </p>
              )}
            </div>
            <LevelLegend />
          </div>
          <ul className="divide-y divide-slate-100">
            {!detail &&
              !error &&
              Array.from({ length: 5 }).map((_, i) => (
                <li key={i} className="px-5 py-4">
                  <Skeleton className="h-9 w-full" />
                </li>
              ))}
            {competencies.map((c) => (
              <li key={c.code} className="grid gap-2 px-5 py-4 sm:grid-cols-[minmax(0,1fr)_12rem_2.5rem] sm:items-center sm:gap-5">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium text-slate-900">{c.name}</p>
                    {target !== null && <GapChip gap={target - c.level} />}
                  </div>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {levelLabel(c.level)}
                    {c.evidence_source ? ` · ${EVIDENCE_LABELS[c.evidence_source] ?? c.evidence_source}` : ""}
                  </p>
                </div>
                <LevelBar level={c.level} target={target} label={c.name} />
                <p className="text-sm font-semibold tabular-nums text-slate-900 sm:text-right">{c.level.toFixed(1)}</p>
              </li>
            ))}
          </ul>
        </section>

        <aside className="space-y-4">
          {focus && target !== null && focus.level < target && (
            <section className="rounded-2xl border border-[#ec835a]/40 bg-[#ec835a]/5 p-5">
              <h2 className="text-sm font-semibold text-slate-900">Focus next</h2>
              <p className="mt-1 text-sm text-pretty text-slate-700">
                <span className="font-semibold">{focus.name}</span> is your lowest competency here at{" "}
                <span className="tabular-nums">{focus.level.toFixed(1)}</span>, against a role target of{" "}
                <span className="tabular-nums">{target.toFixed(1)}</span>.
              </p>
              {recommended[0] && (
                <ButtonLink href={`/courses/${recommended[0].id}`} size="sm" className="mt-3">
                  Start {recommended[0].title.length > 32 ? "recommended course" : recommended[0].title}
                  <ArrowRight className="size-4" aria-hidden="true" />
                </ButtonLink>
              )}
            </section>
          )}

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs" aria-labelledby="practice-heading">
            <h2 id="practice-heading" className="text-sm font-semibold text-slate-900">
              Practise this domain
            </h2>
            <ul className="mt-3 space-y-2">
              {[...meta.practice, { label: "Quiz yourself on your own material", href: "/quiz" }].map((p) => (
                <li key={p.href}>
                  <Link
                    href={p.href}
                    className="group flex items-center gap-3 rounded-xl border border-slate-200 p-3 transition hover:border-[#1E3A8A]/40 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A]"
                  >
                    <span className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                      {p.href === "/quiz" ? <FileQuestion className="size-4" aria-hidden="true" /> : <Icon className="size-4" aria-hidden="true" />}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-medium text-slate-900">{p.label}</span>
                      <span className="block text-xs text-pretty text-slate-500">
                        {PRACTICE_DESCRIPTIONS[p.href] ?? "Generate questions from any document you upload"}
                      </span>
                    </span>
                    <ArrowRight className="size-4 shrink-0 text-slate-400 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
                  </Link>
                </li>
              ))}
            </ul>
          </section>
        </aside>
      </div>

      <section aria-labelledby="courses-heading" className="space-y-4">
        <div className="flex items-end justify-between gap-4">
          <h2 id="courses-heading" className="text-xl font-semibold text-balance text-slate-900">
            Courses in this domain
          </h2>
          <ButtonLink href="/recommendations" variant="ghost" size="sm">
            All recommendations
            <ArrowRight className="size-4" aria-hidden="true" />
          </ButtonLink>
        </div>

        {!detail && !error && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-48 w-full rounded-2xl" />
            ))}
          </div>
        )}

        {detail && detail.courses.length === 0 && (
          <div className="rounded-2xl border border-slate-200 bg-white p-6 text-sm text-slate-600">
            No courses are mapped to this domain yet.{" "}
            <Link href="/courses" className="font-medium text-[#1E3A8A] hover:underline">
              Browse the full catalogue
            </Link>
          </div>
        )}

        {recommended.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">Recommended for you</h3>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {recommended.map((course) => (
                <CourseCard key={course.id} course={course} />
              ))}
            </div>
          </div>
        )}

        {others.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-slate-700">{recommended.length ? "More in this domain" : "All courses"}</h3>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {others.map((course) => (
                <CourseCard key={course.id} course={course} />
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
