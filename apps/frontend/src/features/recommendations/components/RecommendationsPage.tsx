"use client";

import { useEffect, useState } from "react";
import { ArrowRight, Check, RefreshCw, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ErrorNotice } from "@/components/shared/ErrorNotice";
import { fetchApi } from "@/lib/api";
import type { Recommendation, RecommendationStatus } from "@/lib/types/competency";

const TABS: { value: RecommendationStatus; label: string }[] = [
  { value: "pending", label: "Recommended" },
  { value: "enrolled", label: "Enrolled" },
  { value: "dismissed", label: "Dismissed" },
];

export default function RecommendationsPage() {
  const [recs, setRecs] = useState<Recommendation[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [rowErrors, setRowErrors] = useState<Record<number, string>>({});
  const [busyId, setBusyId] = useState<number | null>(null);

  function load() {
    return fetchApi<Recommendation[]>("/recommendations")
      .then(setRecs)
      .catch((e: Error) => setError(e.message));
  }

  useEffect(() => {
    load();
  }, []);

  async function generate() {
    setGenerating(true);
    setError(null);
    try {
      await fetchApi("/recommendations/generate", { method: "POST" });
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setGenerating(false);
    }
  }

  async function updateStatus(id: number, status: RecommendationStatus) {
    setBusyId(id);
    setRowErrors((prev) => ({ ...prev, [id]: "" }));
    try {
      const updated = await fetchApi<Recommendation>(`/recommendations/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      setRecs((prev) => prev?.map((r) => (r.id === id ? updated : r)) ?? null);
    } catch (e) {
      setRowErrors((prev) => ({ ...prev, [id]: (e as Error).message }));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="mx-auto w-full max-w-5xl space-y-8 px-4 py-8 sm:px-6 lg:px-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-[#1E3A8A]">Personalised learning path</p>
          <h1 className="text-3xl font-bold text-balance text-slate-900">Recommended courses</h1>
          <p className="max-w-2xl text-pretty text-slate-600">
            Courses from the iGOT Karmayogi catalogue ranked against your latest competency gaps, with the reason each one helps.
          </p>
        </div>
        <div className="flex flex-col items-start gap-2 sm:items-end">
          <Button onClick={generate} disabled={generating}>
            <RefreshCw className="size-4" aria-hidden="true" />
            {generating ? "Finding courses..." : "Refresh recommendations"}
          </Button>
          {generating && <p className="text-xs text-slate-500" role="status">This can take up to a minute.</p>}
        </div>
      </header>

      {error && <ErrorNotice message={error} />}

      {!recs && !error && (
        <div className="space-y-4" aria-busy="true">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      )}

      {recs && (
        <Tabs defaultValue="pending">
          <TabsList>
            {TABS.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value}>
                {tab.label}
                <span className="text-slate-500 tabular-nums">{recs.filter((r) => r.status === tab.value).length}</span>
              </TabsTrigger>
            ))}
          </TabsList>

          {TABS.map((tab) => {
            const items = recs.filter((r) => r.status === tab.value);
            return (
              <TabsContent key={tab.value} value={tab.value} className="space-y-4">
                {items.length === 0 && (
                  <Card>
                    <CardContent className="flex flex-col items-start gap-3 pt-6">
                      <p className="text-pretty text-slate-600">
                        {tab.value === "pending"
                          ? "No open recommendations. Refresh to rank courses against your current gaps."
                          : `No ${tab.label.toLowerCase()} courses yet.`}
                      </p>
                      {tab.value === "pending" && (
                        <Button onClick={generate} disabled={generating} size="sm">Refresh recommendations</Button>
                      )}
                    </CardContent>
                  </Card>
                )}
                {items.map((rec) => (
                  <Card key={rec.id}>
                    <CardHeader>
                      <CardTitle className="text-lg text-balance">{rec.course_title ?? "Course"}</CardTitle>
                      <CardDescription className="text-pretty text-slate-600">{rec.reason}</CardDescription>
                    </CardHeader>
                    <CardContent className="flex flex-wrap items-center gap-2">
                      {rec.course_id && (
                        <ButtonLink href={`/courses/${rec.course_id}`} variant={rec.status === "enrolled" ? "default" : "outline"} size="sm">
                          {rec.status === "enrolled" ? "Continue course" : "View course"}
                          <ArrowRight className="size-4" aria-hidden="true" />
                        </ButtonLink>
                      )}
                      {rec.status === "pending" && (
                        <>
                          <Button size="sm" onClick={() => updateStatus(rec.id, "enrolled")} disabled={busyId === rec.id}>
                            <Check className="size-4" aria-hidden="true" />
                            Enroll
                          </Button>
                          <Button size="sm" variant="ghost" onClick={() => updateStatus(rec.id, "dismissed")} disabled={busyId === rec.id}>
                            <X className="size-4" aria-hidden="true" />
                            Dismiss
                          </Button>
                        </>
                      )}
                      {rec.status === "dismissed" && (
                        <Button size="sm" variant="ghost" onClick={() => updateStatus(rec.id, "pending")} disabled={busyId === rec.id}>
                          Restore
                        </Button>
                      )}
                      {rowErrors[rec.id] && (
                        <p role="alert" className="w-full text-sm text-red-600">{rowErrors[rec.id]}</p>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </TabsContent>
            );
          })}
        </Tabs>
      )}
    </div>
  );
}
