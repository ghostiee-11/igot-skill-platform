"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, FileUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { ErrorNotice } from "@/components/shared/ErrorNotice";
import { fetchApi, uploadApi } from "@/lib/api";
import type { Quiz, QuizSummary } from "@/lib/types/competency";

const ACCEPTED = ".pdf,.pptx,.docx,.txt,.md,.vtt,.srt";
const MIN_TEXT = 200;
const DIFFICULTIES = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
];

export default function QuizHubPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"upload" | "paste">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [title, setTitle] = useState("");
  const [count, setCount] = useState("10");
  const [difficulty, setDifficulty] = useState("intermediate");
  const [formError, setFormError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [quizzes, setQuizzes] = useState<QuizSummary[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);

  useEffect(() => {
    fetchApi<QuizSummary[]>("/quiz")
      .then(setQuizzes)
      .catch((e: Error) => setListError(e.message));
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);
    if (mode === "upload" && !file) return setFormError("Choose a file to upload.");
    if (mode === "paste" && text.trim().length < MIN_TEXT) {
      return setFormError(`Paste at least ${MIN_TEXT} characters of learning material.`);
    }

    const formData = new FormData();
    if (mode === "upload" && file) formData.append("file", file);
    if (mode === "paste") formData.append("text", text);
    formData.append("title", title);
    formData.append("num_questions", count);
    formData.append("difficulty", difficulty);

    setGenerating(true);
    try {
      const quiz = await uploadApi<Quiz>("/quiz/generate", formData);
      router.push(`/quiz/${quiz.id}`);
    } catch (e) {
      setFormError((e as Error).message);
      setGenerating(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-7xl space-y-10 px-4 py-8 sm:px-6 lg:px-8">
      <header className="space-y-2">
        <p className="text-sm font-medium text-[#1E3A8A]">Assessment workspace</p>
        <h1 className="text-3xl font-bold text-balance text-slate-900">Quizzes from your learning material</h1>
        <p className="max-w-2xl text-pretty text-slate-600">
          Upload a document, presentation, or video transcript and get multiple-choice questions with explanations and instant feedback.
        </p>
      </header>

      <div className="grid gap-8 lg:grid-cols-5">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-balance">Create a quiz</CardTitle>
            <CardDescription>PDF, PowerPoint, Word, text, or VTT/SRT transcripts up to 20 MB.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-5" noValidate>
              <Tabs value={mode} onValueChange={(v) => setMode(v as "upload" | "paste")}>
                <TabsList className="w-full">
                  <TabsTrigger value="upload" className="flex-1">Upload file</TabsTrigger>
                  <TabsTrigger value="paste" className="flex-1">Paste text</TabsTrigger>
                </TabsList>
                <TabsContent value="upload" className="space-y-2">
                  <Label htmlFor="quiz-file">Learning material</Label>
                  <input
                    id="quiz-file"
                    type="file"
                    accept={ACCEPTED}
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                    aria-describedby={formError ? "quiz-form-error" : undefined}
                    className="block w-full text-sm text-slate-700 file:mr-3 file:h-10 file:rounded-lg file:border-0 file:bg-slate-100 file:px-4 file:text-sm file:font-medium file:text-slate-800 hover:file:bg-slate-200"
                  />
                  {file && <p className="truncate text-xs text-slate-500">{file.name}</p>}
                </TabsContent>
                <TabsContent value="paste" className="space-y-2">
                  <Label htmlFor="quiz-text">Learning material</Label>
                  <Textarea
                    id="quiz-text"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Paste lecture notes, a chapter, or a transcript"
                    className="min-h-40"
                    aria-describedby={formError ? "quiz-form-error" : undefined}
                  />
                  <p className="text-xs text-slate-500 tabular-nums">{text.trim().length} characters</p>
                </TabsContent>
              </Tabs>

              <div className="space-y-2">
                <Label htmlFor="quiz-title">Title (optional)</Label>
                <Input id="quiz-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. CPI compilation basics" />
              </div>

              <div className="space-y-2">
                <Label htmlFor="quiz-count">Number of questions</Label>
                <Select value={count} onValueChange={setCount}>
                  <SelectTrigger id="quiz-count">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {["5", "10", "15", "20"].map((n) => (
                      <SelectItem key={n} value={n}>{n} questions</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <fieldset className="space-y-2">
                <legend className="text-sm font-medium text-slate-800">Difficulty</legend>
                <RadioGroup value={difficulty} onValueChange={setDifficulty} className="flex flex-wrap gap-4">
                  {DIFFICULTIES.map((d) => (
                    <div key={d.value} className="flex items-center gap-2">
                      <RadioGroupItem id={`difficulty-${d.value}`} value={d.value} />
                      <Label htmlFor={`difficulty-${d.value}`} className="font-normal">{d.label}</Label>
                    </div>
                  ))}
                </RadioGroup>
              </fieldset>

              {formError && (
                <p id="quiz-form-error" role="alert" className="text-sm text-red-600">{formError}</p>
              )}

              <Button type="submit" className="w-full" disabled={generating}>
                <FileUp className="size-4" aria-hidden="true" />
                {generating ? "Generating questions..." : "Generate quiz"}
              </Button>
              {generating && (
                <p className="text-center text-xs text-slate-500" role="status">
                  Reading your material and writing questions. This can take up to a minute.
                </p>
              )}
            </form>
          </CardContent>
        </Card>

        <section aria-labelledby="quiz-list-heading" className="space-y-4 lg:col-span-3">
          <h2 id="quiz-list-heading" className="text-xl font-semibold text-balance text-slate-900">Available quizzes</h2>
          {listError && <ErrorNotice message={listError} />}
          {!quizzes && !listError && (
            <div className="space-y-3" aria-busy="true">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-24 w-full" />
              ))}
            </div>
          )}
          {quizzes?.length === 0 && (
            <Card>
              <CardContent className="pt-6 text-pretty text-slate-600">
                No quizzes yet. Upload learning material to create the first one.
              </CardContent>
            </Card>
          )}
          <ul className="space-y-3">
            {quizzes?.map((q) => (
              <li key={q.id}>
                <Card>
                  <CardContent className="flex flex-col gap-3 pt-6 sm:flex-row sm:items-center sm:justify-between">
                    <div className="min-w-0 space-y-1">
                      <p className="truncate font-medium text-slate-900">{q.title}</p>
                      <p className="truncate text-sm text-slate-500">
                        {q.question_count} questions · {q.source_name}
                        {q.creator_name ? ` · by ${q.creator_name}` : ""}
                      </p>
                      <div className="flex flex-wrap gap-2 pt-1">
                        <Badge variant="outline" className="capitalize">{q.difficulty}</Badge>
                        {q.best_score !== null && (
                          <Badge variant="secondary" className="tabular-nums">Best score {q.best_score}%</Badge>
                        )}
                      </div>
                    </div>
                    <ButtonLink href={`/quiz/${q.id}`} size="sm" className="shrink-0">
                      {q.best_score !== null ? "Retake" : "Take quiz"}
                      <ArrowRight className="size-4" aria-hidden="true" />
                    </ButtonLink>
                  </CardContent>
                </Card>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
