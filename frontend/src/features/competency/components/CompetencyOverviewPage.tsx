"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, FileQuestion, RefreshCw } from "lucide-react";
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorNotice } from "@/components/shared/ErrorNotice";
import { fetchApi } from "@/lib/api";
import type { DomainGap } from "@/lib/types/competency";
import { DOMAINS, DOMAIN_ACCENT_CLASS, DOMAIN_ORDER, LEVEL_MAX, levelLabel } from "@/features/competency/domains";
import { DomainNav, GapChip, LevelBar, LevelLegend, StatTile } from "@/features/competency/components/CompetencyUI";
import { CHART, ChartLegend, ChartTable, ChartTooltip, axisTick } from "@/features/analytics/chart-kit";

export default function CompetencyOverviewPage() {
  const [gaps, setGaps] = useState<DomainGap[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    fetchApi<DomainGap[]>("/competency/gaps")
      .then(setGaps)
      .catch((e: Error) => {
        if (e.message.toLowerCase().includes("no gap analysis")) setGaps([]);
        else setError(e.message);
      });
  }, []);

  async function runAnalysis() {
    setAnalyzing(true);
    setError(null);
    try {
      const res = await fetchApi<{ gaps: DomainGap[] }>("/competency/analyze", { method: "POST" });
      setGaps(res.gaps);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setAnalyzing(false);
    }
  }

  const byCode = new Map((gaps ?? []).map((g) => [g.domain_code, g]));
  const analysed = DOMAIN_ORDER.map((code) => byCode.get(code)).filter((g): g is DomainGap => Boolean(g));
  const hasAnalysis = analysed.length > 0;
  const lastRun = gaps?.[0]?.generated_at;
  const average = hasAnalysis ? analysed.reduce((sum, g) => sum + g.current_level, 0) / analysed.length : 0;
  const atTarget = analysed.filter((g) => g.gap <= 0).length;
  const largest = [...analysed].sort((a, b) => b.gap - a.gap)[0];
  const chartData = DOMAIN_ORDER.map((code) => ({
    domain: DOMAINS[code].shortLabel,
    current: Number((byCode.get(code)?.current_level ?? 0).toFixed(1)),
    target: byCode.get(code)?.target_level ?? 0,
  }));

  return (
    <div className="mx-auto w-full max-w-7xl space-y-6 px-4 py-8 sm:px-6 lg:px-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-[#0D9488]">Skill intelligence</p>
          <h1 className="text-3xl font-bold text-balance text-slate-900">Competency profile</h1>
          <p className="max-w-2xl text-pretty text-slate-600">
            Your level in each competency domain of the Official Statistical System, compared with the level expected for
            your role. Built from your assessments, labs, quizzes and simulations.
          </p>
        </div>
        <div className="flex flex-col items-start gap-1.5 sm:items-end">
          <Button onClick={runAnalysis} disabled={analyzing}>
            <RefreshCw className={`size-4 ${analyzing ? "animate-spin" : ""}`} aria-hidden="true" />
            {analyzing ? "Analysing..." : hasAnalysis ? "Re-run analysis" : "Run gap analysis"}
          </Button>
          {lastRun && (
            <p className="text-xs text-slate-500">
              Last analysed{" "}
              {new Date(lastRun).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}
            </p>
          )}
        </div>
      </header>

      <DomainNav active="overview" />

      {error && <ErrorNotice message={error} />}

      {!gaps && !error && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-busy="true">
          {DOMAIN_ORDER.map((code) => (
            <Skeleton key={code} className="h-52 w-full rounded-2xl" />
          ))}
        </div>
      )}

      {gaps && !hasAnalysis && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
          <h2 className="text-lg font-semibold text-balance text-slate-900">No gap analysis yet</h2>
          <p className="mt-1 max-w-xl text-pretty text-slate-600">
            Run your first analysis to see where you stand in all four domains and get courses matched to your gaps.
          </p>
          <Button onClick={runAnalysis} disabled={analyzing} className="mt-4">
            {analyzing ? "Analysing..." : "Run gap analysis"}
          </Button>
        </section>
      )}

      {hasAnalysis && (
        <>
          <dl className="grid gap-3 sm:grid-cols-3">
            <StatTile
              label="Average level"
              value={
                <>
                  {average.toFixed(1)}
                  <span className="text-sm font-normal text-slate-500">/{LEVEL_MAX}</span>
                </>
              }
              detail={levelLabel(average)}
            />
            <StatTile label="Domains at target" value={`${atTarget} of ${analysed.length}`} detail="Domains where you meet your role target" />
            <StatTile
              label="Largest gap"
              value={largest && largest.gap > 0 ? DOMAINS[largest.domain_code].shortLabel : "None"}
              detail={largest && largest.gap > 0 ? `${largest.gap.toFixed(1)} levels below target` : "All role targets met"}
            />
          </dl>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {DOMAIN_ORDER.map((code) => {
              const meta = DOMAINS[code];
              const gap = byCode.get(code);
              const Icon = meta.icon;
              const current = gap?.current_level ?? 0;
              return (
                <Link
                  key={code}
                  href={`/competency/${code}`}
                  aria-label={`${meta.label}: level ${current.toFixed(1)} of ${LEVEL_MAX}. Open domain`}
                  className="group flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xs transition hover:border-[#1E3A8A]/40 hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A]"
                >
                  <span className={`h-1 ${DOMAIN_ACCENT_CLASS[code]}`} aria-hidden="true" />
                  <div className="flex flex-1 flex-col p-5">
                    <div className="flex items-center gap-2 text-slate-700">
                      <Icon className="size-5" aria-hidden="true" />
                      <h2 className="text-sm font-semibold text-balance">{meta.label}</h2>
                    </div>
                    <p className="mt-3 text-3xl font-semibold tabular-nums text-slate-900">
                      {current.toFixed(1)}
                      <span className="text-base font-normal text-slate-500">/{LEVEL_MAX}</span>
                    </p>
                    <p className="text-sm text-slate-600 tabular-nums">
                      {levelLabel(current)}
                      {gap ? ` · target ${gap.target_level.toFixed(1)}` : ""}
                    </p>
                    <div className="mt-3">
                      <LevelBar level={current} target={gap?.target_level} label={meta.label} />
                    </div>
                    <div className="mt-3">
                      <GapChip gap={gap?.gap} />
                    </div>
                    <span className="mt-auto inline-flex items-center gap-1 pt-4 text-sm font-medium text-[#1E3A8A]">
                      Open domain
                      <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
                    </span>
                  </div>
                </Link>
              );
            })}
          </div>
          <LevelLegend />

          <div className="grid gap-4 lg:grid-cols-3">
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs lg:col-span-2" aria-labelledby="chart-heading">
              <h2 id="chart-heading" className="text-base font-semibold text-balance text-slate-900">
                Current level vs role target
              </h2>
              <p className="text-sm text-slate-500">Levels run from 0 (not yet assessed) to 5 (expert).</p>
              <div className="mt-4 space-y-4">
                <ChartLegend
                  items={[
                    { label: "Your current level", color: CHART.series[0] },
                    { label: "Target for your role", color: CHART.neutral },
                  ]}
                />
                <div className="h-72 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData} barGap={2} margin={{ top: 20, right: 8, bottom: 0, left: -16 }}>
                      <CartesianGrid vertical={false} stroke={CHART.grid} />
                      <XAxis dataKey="domain" tick={axisTick} tickLine={false} axisLine={{ stroke: CHART.axis }} />
                      <YAxis domain={[0, LEVEL_MAX]} ticks={[0, 1, 2, 3, 4, 5]} tick={axisTick} tickLine={false} axisLine={false} />
                      <Tooltip cursor={{ fill: "#f1f5f9" }} content={<ChartTooltip format={(v) => v.toFixed(1)} />} />
                      <Bar dataKey="current" name="Current level" fill={CHART.series[0]} maxBarSize={28} radius={[4, 4, 0, 0]}>
                        <LabelList dataKey="current" position="top" fill={CHART.secondaryInk} fontSize={12} />
                      </Bar>
                      <Bar dataKey="target" name="Role target" fill={CHART.neutral} maxBarSize={28} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <ChartTable
                  caption="Current level and role target by competency domain"
                  columns={["Domain", "Current level", "Target", "Gap"]}
                  rows={DOMAIN_ORDER.map((code) => {
                    const g = byCode.get(code);
                    return [DOMAINS[code].label, (g?.current_level ?? 0).toFixed(1), (g?.target_level ?? 0).toFixed(1), (g?.gap ?? 0).toFixed(1)];
                  })}
                />
                <p className="text-xs text-pretty text-slate-500">Targets use a default role-tier framework until your department configures its own.</p>
              </div>
            </section>

            <div className="space-y-4">
              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
                <span className="flex size-9 items-center justify-center rounded-lg bg-blue-50 text-[#1E3A8A]">
                  <BookOpen className="size-4" aria-hidden="true" />
                </span>
                <h2 className="mt-3 text-base font-semibold text-balance text-slate-900">Recommended learning</h2>
                <p className="mt-1 text-sm text-pretty text-slate-600">Courses from the iGOT Karmayogi catalogue ranked for your weakest domains.</p>
                <ButtonLink href="/recommendations" className="mt-4 w-full">
                  See recommendations
                </ButtonLink>
              </section>
              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
                <span className="flex size-9 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                  <FileQuestion className="size-4" aria-hidden="true" />
                </span>
                <h2 className="mt-3 text-base font-semibold text-balance text-slate-900">Test your understanding</h2>
                <p className="mt-1 text-sm text-pretty text-slate-600">Turn any study material into a quiz with instant feedback.</p>
                <ButtonLink href="/quiz" variant="outline" className="mt-4 w-full">
                  Create a quiz
                </ButtonLink>
              </section>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
