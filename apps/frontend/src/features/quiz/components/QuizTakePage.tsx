"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, CheckCircle2, RotateCcw, Trash2, XCircle } from "lucide-react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ErrorNotice } from "@/components/shared/ErrorNotice";
import { fetchApi } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { Quiz, QuizResult } from "@/lib/types/competency";

export default function QuizTakePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    fetchApi<Quiz>(`/quiz/${id}`)
      .then(setQuiz)
      .catch((e: Error) => setError(e.message));
  }, [id]);

  async function submit() {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const res = await fetchApi<QuizResult>(`/quiz/${id}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers }),
      });
      setResult(res);
      window.scrollTo({ top: 0 });
    } catch (e) {
      setSubmitError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  async function deleteQuiz() {
    setDeleteError(null);
    try {
      await fetchApi(`/quiz/${id}`, { method: "DELETE" });
      router.push("/quiz");
    } catch (e) {
      setDeleteError((e as Error).message);
    }
  }

  function retake() {
    setAnswers({});
    setResult(null);
  }

  if (error) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
        <ErrorNotice message={error} />
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="mx-auto w-full max-w-3xl space-y-4 px-4 py-8 sm:px-6" aria-busy="true">
        <Skeleton className="h-10 w-2/3" />
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-40 w-full" />
        ))}
      </div>
    );
  }

  const remaining = quiz.questions.length - Object.keys(answers).length;
  const resultById = new Map(result?.results.map((r) => [r.question_id, r]));

  const takeView = result ? (
    <div className="space-y-6">
      <Card>
        <CardContent className="flex flex-col gap-4 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-slate-600">Your score</p>
            <p className="text-4xl font-bold text-slate-900 tabular-nums">{result.score_percent}%</p>
            <p className="text-sm text-slate-600 tabular-nums">
              {result.correct_count} of {result.total_questions} correct · {result.band}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={retake}>
              <RotateCcw className="size-4" aria-hidden="true" />
              Retake quiz
            </Button>
            <ButtonLink href="/quiz">All quizzes</ButtonLink>
          </div>
        </CardContent>
        <CardContent className="space-y-3 border-t border-slate-100 pt-4">
          <p className="text-pretty text-slate-700">{result.feedback}</p>
          {result.concepts_to_review.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-slate-800">Concepts to review</p>
              <div className="flex flex-wrap gap-2">
                {result.concepts_to_review.map((c) => (
                  <Badge key={c} variant="warning">{c}</Badge>
                ))}
              </div>
              <ButtonLink href="/recommendations" variant="ghost" size="sm" className="-ml-3">
                Find courses on these concepts
              </ButtonLink>
            </div>
          )}
        </CardContent>
      </Card>

      <ol className="space-y-4">
        {quiz.questions.map((q, index) => {
          const r = resultById.get(q.id);
          return (
            <li key={q.id}>
              <Card>
                <CardHeader>
                  <p className="flex items-center gap-2 text-sm font-medium">
                    {r?.is_correct ? (
                      <span className="flex items-center gap-1 text-emerald-700">
                        <CheckCircle2 className="size-4" aria-hidden="true" /> Correct
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-red-700">
                        <XCircle className="size-4" aria-hidden="true" /> Incorrect
                      </span>
                    )}
                  </p>
                  <CardTitle className="text-base leading-snug text-pretty">
                    {index + 1}. {q.question}
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <ul className="space-y-2">
                    {q.options.map((option, i) => {
                      const isCorrect = r?.correct_index === i;
                      const isSelectedWrong = r?.selected_index === i && !r.is_correct;
                      return (
                        <li
                          key={i}
                          className={cn(
                            "flex items-start justify-between gap-3 rounded-lg border px-3 py-2 text-sm",
                            isCorrect && "border-emerald-300 bg-emerald-50 text-emerald-900",
                            isSelectedWrong && "border-red-300 bg-red-50 text-red-900",
                            !isCorrect && !isSelectedWrong && "border-slate-200 text-slate-700"
                          )}
                        >
                          <span className="text-pretty">{option}</span>
                          {isCorrect && <span className="shrink-0 text-xs font-medium">Correct answer</span>}
                          {isSelectedWrong && <span className="shrink-0 text-xs font-medium">Your answer</span>}
                        </li>
                      );
                    })}
                  </ul>
                  {r?.explanation && <p className="text-sm text-pretty text-slate-600">{r.explanation}</p>}
                </CardContent>
              </Card>
            </li>
          );
        })}
      </ol>
    </div>
  ) : (
    <div className="space-y-4">
      <ol className="space-y-4">
        {quiz.questions.map((q, index) => (
          <li key={q.id}>
            <Card>
              <CardContent className="pt-6">
                <fieldset className="space-y-3">
                  <legend className="mb-3 font-medium text-pretty text-slate-900">
                    {index + 1}. {q.question}
                  </legend>
                  <RadioGroup
                    value={answers[q.id] !== undefined ? String(answers[q.id]) : ""}
                    onValueChange={(v) => setAnswers((prev) => ({ ...prev, [q.id]: Number(v) }))}
                  >
                    {q.options.map((option, i) => (
                      <div key={i} className="flex items-start gap-3 rounded-lg border border-slate-200 px-3 py-2 has-[button[data-state=checked]]:border-[#1E3A8A] has-[button[data-state=checked]]:bg-blue-50">
                        <RadioGroupItem id={`q${q.id}-o${i}`} value={String(i)} className="mt-0.5" />
                        <Label htmlFor={`q${q.id}-o${i}`} className="flex-1 cursor-pointer font-normal text-pretty">{option}</Label>
                      </div>
                    ))}
                  </RadioGroup>
                </fieldset>
              </CardContent>
            </Card>
          </li>
        ))}
      </ol>

      <div className="flex flex-col items-start gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p id="submit-hint" className="text-sm text-slate-600 tabular-nums">
          {remaining > 0 ? `Answer all ${quiz.questions.length} questions to submit (${remaining} remaining).` : "All questions answered."}
        </p>
        <Button onClick={submit} disabled={remaining > 0 || submitting} aria-describedby="submit-hint">
          {submitting ? "Checking answers..." : "Submit answers"}
        </Button>
      </div>
      {submitError && <p role="alert" className="text-sm text-red-600">{submitError}</p>}
    </div>
  );

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-8 sm:px-6">
      <ButtonLink href="/quiz" variant="ghost" size="sm" className="-ml-3">
        <ArrowLeft className="size-4" aria-hidden="true" />
        All quizzes
      </ButtonLink>

      <header className="space-y-3">
        <h1 className="text-2xl font-bold text-balance text-slate-900 sm:text-3xl">{quiz.title}</h1>
        <p className="text-sm text-slate-600">
          {quiz.question_count} questions · {quiz.source_name}
          {quiz.creator_name ? ` · by ${quiz.creator_name}` : ""}
        </p>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline" className="capitalize">{quiz.difficulty}</Badge>
          {quiz.generator === "fallback" && (
            <Badge variant="secondary">Generated without AI (fill-in-the-blank)</Badge>
          )}
        </div>
      </header>

      {quiz.can_manage ? (
        <Tabs defaultValue="take">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <TabsList>
              <TabsTrigger value="take">Take quiz</TabsTrigger>
              <TabsTrigger value="key">Answer key</TabsTrigger>
            </TabsList>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="sm" className="text-red-700 hover:bg-red-50">
                  <Trash2 className="size-4" aria-hidden="true" />
                  Delete quiz
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete this quiz?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This permanently removes the quiz and every learner attempt. It cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={deleteQuiz}>Delete quiz</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
          {deleteError && <p role="alert" className="text-sm text-red-600">{deleteError}</p>}
          <TabsContent value="take">{takeView}</TabsContent>
          <TabsContent value="key" className="space-y-4">
            {quiz.questions.map((q, index) => (
              <Card key={q.id}>
                <CardHeader>
                  <CardTitle className="text-base leading-snug text-pretty">
                    {index + 1}. {q.question}
                  </CardTitle>
                  {q.concept && <CardDescription>Concept: {q.concept}</CardDescription>}
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <p className="text-slate-800">
                    <span className="font-medium">Answer: </span>
                    {q.correct_index !== undefined ? q.options[q.correct_index] : "Not available"}
                  </p>
                  {q.explanation && <p className="text-pretty text-slate-600">{q.explanation}</p>}
                </CardContent>
              </Card>
            ))}
          </TabsContent>
        </Tabs>
      ) : (
        takeView
      )}
    </div>
  );
}
