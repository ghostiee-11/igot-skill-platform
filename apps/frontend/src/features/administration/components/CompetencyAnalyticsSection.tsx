"use client";

import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ButtonLink } from "@/components/ui/button-link";
import { ErrorNotice } from "@/components/shared/ErrorNotice";
import { fetchApi } from "@/lib/api";
import type { DomainCode } from "@/lib/types/competency";
import { DOMAINS, DOMAIN_ORDER } from "@/features/competency/domains";
import { CHART, ChartLegend, ChartTable, ChartTooltip, axisTick } from "@/features/analytics/chart-kit";

interface Analytics {
  profiled_learners: number;
  average_scores: { domain_code: DomainCode; domain_name: string; average_score: number }[];
  gap_distribution: { domain_code: DomainCode; on_target: number; minor_gap: number; major_gap: number }[];
  gap_trend: ({ date: string } & Partial<Record<DomainCode, number>>)[];
  projections: { domain_code: DomainCode; current_gap: number | null; projected_gap_30d: number | null }[];
  training_effectiveness: {
    quizzes_generated: number;
    quiz_attempts: number;
    average_quiz_score: number | null;
    assessment_attempts: number;
    assessment_pass_rate: number | null;
    enrollments_completed: number;
    enrollments_in_progress: number;
  };
  top_recommended_courses: { course_id: number; title: string; recommended_to: number }[];
}

// Color follows the domain, never its rank: fixed slot per domain.
const DOMAIN_COLOR: Record<DomainCode, string> = {
  statistical: CHART.series[0],
  technical: CHART.series[1],
  digital_governance: CHART.series[2],
  behavioural: CHART.series[3],
};

const STATUS_SERIES = [
  { key: "on_target", label: "On target", color: CHART.status.good },
  { key: "minor_gap", label: "Minor gap (up to 1 level)", color: CHART.status.warning },
  { key: "major_gap", label: "Major gap (over 1 level)", color: CHART.status.serious },
] as const;

const shortDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
const formatGap = (value: number | null) => (value === null ? "No data" : value.toFixed(2));
const officials = (count: number) => `${count} ${count === 1 ? "official" : "officials"}`;

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="space-y-1 pt-6">
        <p className="text-sm text-slate-600">{label}</p>
        <p className="text-2xl font-semibold text-slate-900">{value}</p>
      </CardContent>
    </Card>
  );
}

export default function CompetencyAnalyticsSection() {
  const [data, setData] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchApi<Analytics>("/admin/competency-analytics")
      .then(setData)
      .catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <ErrorNotice message={error} />;

  if (!data) {
    return (
      <div className="space-y-4" aria-busy="true">
        <Skeleton className="h-7 w-72" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  const effectiveness = data.training_effectiveness;
  const scoreRows = DOMAIN_ORDER.map((code) => ({
    code,
    domain: DOMAINS[code].shortLabel,
    score: data.average_scores.find((s) => s.domain_code === code)?.average_score ?? 0,
  }));
  const distributionRows = DOMAIN_ORDER.map((code) => {
    const row = data.gap_distribution.find((d) => d.domain_code === code);
    return {
      code,
      domain: DOMAINS[code].shortLabel,
      on_target: row?.on_target ?? 0,
      minor_gap: row?.minor_gap ?? 0,
      major_gap: row?.major_gap ?? 0,
    };
  });
  const lastTrendIndex = data.gap_trend.length - 1;

  return (
    <section aria-labelledby="workforce-analytics-heading" className="space-y-6">
      <div className="space-y-1">
        <h2 id="workforce-analytics-heading" className="text-xl font-semibold text-balance text-slate-900">
          Workforce competency intelligence
        </h2>
        <p className="text-sm text-pretty text-slate-600">
          Organisation-wide competency levels, gaps, training effectiveness, and projected capacity-building needs.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatTile label="Officials with a competency profile" value={data.profiled_learners.toLocaleString()} />
        <StatTile label="AI quizzes generated" value={effectiveness.quizzes_generated.toLocaleString()} />
        <StatTile label="Average quiz score" value={effectiveness.average_quiz_score === null ? "No attempts" : `${effectiveness.average_quiz_score}%`} />
        <StatTile label="Assessment pass rate" value={effectiveness.assessment_pass_rate === null ? "No attempts" : `${effectiveness.assessment_pass_rate}%`} />
      </div>

      {data.profiled_learners === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-start gap-3 pt-6">
            <p className="text-pretty text-slate-600">
              No official has run a competency gap analysis yet. Organisation charts appear once analyses exist.
            </p>
            <ButtonLink href="/competency" size="sm">Open competency profile</ButtonLink>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base text-balance">Average competency score by domain</CardTitle>
                <CardDescription>Mean score across profiled officials, out of 100.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={scoreRows} margin={{ top: 20, right: 8, bottom: 0, left: -16 }}>
                      <CartesianGrid vertical={false} stroke={CHART.grid} />
                      <XAxis dataKey="domain" interval={0} tick={axisTick} tickLine={false} axisLine={{ stroke: CHART.axis }} />
                      <YAxis domain={[0, 100]} tick={axisTick} tickLine={false} axisLine={false} />
                      <Tooltip cursor={{ fill: "#f1f5f9" }} content={<ChartTooltip format={(v) => v.toFixed(1)} />} />
                      <Bar dataKey="score" name="Average score" fill={CHART.series[0]} maxBarSize={24} radius={[4, 4, 0, 0]}>
                        <LabelList dataKey="score" position="top" fill={CHART.secondaryInk} fontSize={12} />
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <ChartTable
                  caption="Average competency score by domain"
                  columns={["Domain", "Average score"]}
                  rows={scoreRows.map((d) => [DOMAINS[d.code].label, d.score.toFixed(1)])}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base text-balance">Gap distribution by domain</CardTitle>
                <CardDescription>Officials grouped by their latest gap against role target.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <ChartLegend items={STATUS_SERIES.map((s) => ({ label: s.label, color: s.color }))} />
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={distributionRows} margin={{ top: 8, right: 8, bottom: 0, left: -16 }}>
                      <CartesianGrid vertical={false} stroke={CHART.grid} />
                      <XAxis dataKey="domain" interval={0} tick={axisTick} tickLine={false} axisLine={{ stroke: CHART.axis }} />
                      <YAxis allowDecimals={false} tick={axisTick} tickLine={false} axisLine={false} />
                      <Tooltip cursor={{ fill: "#f1f5f9" }} content={<ChartTooltip />} />
                      {STATUS_SERIES.map((s, i) => (
                        <Bar
                          key={s.key}
                          dataKey={s.key}
                          name={s.label}
                          stackId="gap"
                          fill={s.color}
                          stroke={CHART.surface}
                          strokeWidth={2}
                          maxBarSize={24}
                          radius={i === STATUS_SERIES.length - 1 ? [4, 4, 0, 0] : 0}
                        />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <ChartTable
                  caption="Officials by gap status and domain"
                  columns={["Domain", ...STATUS_SERIES.map((s) => s.label)]}
                  rows={distributionRows.map((d) => [DOMAINS[d.code].label, d.on_target, d.minor_gap, d.major_gap])}
                />
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base text-balance">Average gap over the last 30 days</CardTitle>
              <CardDescription>Levels below role target, averaged per day across all analyses. Lower is better.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <ChartLegend items={DOMAIN_ORDER.map((code) => ({ label: DOMAINS[code].label, color: DOMAIN_COLOR[code], shape: "line" as const }))} />
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.gap_trend} margin={{ top: 8, right: 24, bottom: 0, left: -16 }}>
                    <CartesianGrid vertical={false} stroke={CHART.grid} />
                    <XAxis dataKey="date" tickFormatter={shortDate} tick={axisTick} tickLine={false} axisLine={{ stroke: CHART.axis }} />
                    <YAxis tick={axisTick} tickLine={false} axisLine={false} />
                    <Tooltip
                      cursor={{ stroke: CHART.axis, strokeWidth: 1 }}
                      labelFormatter={(value) => shortDate(String(value))}
                      content={<ChartTooltip shape="line" format={(v) => v.toFixed(2)} />}
                    />
                    {DOMAIN_ORDER.map((code) => (
                      <Line
                        key={code}
                        type="monotone"
                        dataKey={code}
                        name={DOMAINS[code].label}
                        stroke={DOMAIN_COLOR[code]}
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        dot={data.gap_trend.length === 1 ? { r: 4, stroke: CHART.surface, strokeWidth: 2, fill: DOMAIN_COLOR[code] } : false}
                        activeDot={{ r: 5, stroke: CHART.surface, strokeWidth: 2 }}
                        connectNulls
                        isAnimationActive={false}
                      >
                        <LabelList
                          dataKey={code}
                          content={({ x, y, index, value }) =>
                            index === lastTrendIndex && typeof value === "number" ? (
                              <text x={Number(x) + 6} y={Number(y)} dy={4} fill={CHART.secondaryInk} fontSize={12}>
                                {value.toFixed(1)}
                              </text>
                            ) : null
                          }
                        />
                      </Line>
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <ChartTable
                caption="Average gap per domain by day"
                columns={["Date", ...DOMAIN_ORDER.map((code) => DOMAINS[code].label)]}
                rows={data.gap_trend.map((point) => [
                  shortDate(point.date),
                  ...DOMAIN_ORDER.map((code) => (point[code] === undefined ? "No data" : point[code]!.toFixed(2))),
                ])}
              />
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base text-balance">Projected capacity-building needs</CardTitle>
                <CardDescription>Average gap today and a 30-day projection from the recent trend.</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full border-collapse text-left text-sm">
                  <thead>
                    <tr>
                      <th scope="col" className="border-b border-slate-200 py-2 pr-4 font-medium text-slate-700">Domain</th>
                      <th scope="col" className="border-b border-slate-200 py-2 pr-4 font-medium text-slate-700">Current gap</th>
                      <th scope="col" className="border-b border-slate-200 py-2 pr-4 font-medium text-slate-700">Projected in 30 days</th>
                    </tr>
                  </thead>
                  <tbody>
                    {DOMAIN_ORDER.map((code) => {
                      const p = data.projections.find((row) => row.domain_code === code);
                      const widening = p?.current_gap != null && p.projected_gap_30d != null && p.projected_gap_30d > p.current_gap;
                      return (
                        <tr key={code}>
                          <th scope="row" className="border-b border-slate-100 py-2 pr-4 font-normal text-slate-700">{DOMAINS[code].label}</th>
                          <td className="border-b border-slate-100 py-2 pr-4 text-slate-900 tabular-nums">{formatGap(p?.current_gap ?? null)}</td>
                          <td className="border-b border-slate-100 py-2 pr-4 text-slate-900 tabular-nums">
                            {formatGap(p?.projected_gap_30d ?? null)}
                            {widening && <span className="ml-2 text-xs font-medium text-amber-800">Widening</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base text-balance">Most-recommended courses</CardTitle>
                <CardDescription>Emerging demand: the courses matched to competency gaps for the most officials.</CardDescription>
              </CardHeader>
              <CardContent>
                {data.top_recommended_courses.length === 0 ? (
                  <p className="text-sm text-slate-600">No recommendations generated yet.</p>
                ) : (
                  <ol className="space-y-2">
                    {data.top_recommended_courses.map((course) => (
                      <li key={course.course_id} className="flex items-center justify-between gap-4 text-sm">
                        <span className="truncate text-slate-800">{course.title}</span>
                        <span className="shrink-0 text-slate-600 tabular-nums">{officials(course.recommended_to)}</span>
                      </li>
                    ))}
                  </ol>
                )}
                <p className="mt-4 text-xs text-slate-500 tabular-nums">
                  Enrolments: {effectiveness.enrollments_completed} completed, {effectiveness.enrollments_in_progress} in progress
                </p>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </section>
  );
}
