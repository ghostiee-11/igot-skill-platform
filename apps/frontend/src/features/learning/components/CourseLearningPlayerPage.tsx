"use client";

import React, { useEffect, useRef, useState, Suspense } from "react";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  CheckCircle2,
  Circle,
  PlayCircle,
  ChevronLeft,
  ChevronRight,
  Video,
  FileText,
  FlaskConical,
  Award,
  AlertCircle,
  Sparkles,
  HelpCircle,
  BookOpen,
  Brain,
  ShieldAlert,
  Scale,
  ArrowRight,
  Terminal,
  BarChart3,
  Mic,
  FileCheck2,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { fetchApi } from "@/lib/api";
import { CurrentLesson, ModuleSummary } from "@/lib/types";
import { useI18n } from "@/lib/i18n";
import confetti from "canvas-confetti";
import { LessonVideo } from "@/features/learning/components/LessonVideo";
import { LessonMarkdown } from "@/features/learning/components/LessonMarkdown";

function LearningPlayerContent() {
  const { courseId } = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { t } = useI18n();

  const lessonQueryId = searchParams?.get("lessonId");
  const pathname = usePathname();
  const mainRef = useRef<HTMLElement>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const [courseMeta, setCourseMeta] = useState<any>(null);
  const [modulesTree, setModulesTree] = useState<ModuleSummary[]>([]);
  const [currentLesson, setCurrentLesson] = useState<CurrentLesson | null>(null);
  const [loading, setLoading] = useState(true);
  const [mobileSyllabusOpen, setMobileSyllabusOpen] = useState(false);

  // In-lesson Activity Practice state
  const [selectedActivityOption, setSelectedActivityOption] = useState<number | null>(null);
  const [activityFeedback, setActivityFeedback] = useState<{
    is_correct: boolean;
    explanation: string;
  } | null>(null);
  const [activityChecking, setActivityChecking] = useState(false);

  const loadPlayerData = (targetLessonId?: number | string | null) => {
    setLoading(true);
    const url = targetLessonId
      ? `/learning/course/${courseId}/player?lesson_id=${targetLessonId}`
      : `/learning/course/${courseId}/player`;

    fetchApi(url)
      .then((data) => {
        setCourseMeta(data.course);
        setModulesTree(data.modules_tree);
        setCurrentLesson(data.current_lesson);
        // Reset activity state for new lesson
        setSelectedActivityOption(null);
        setActivityFeedback(null);
      })
      .catch((err) => console.error("Error loading learning player:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (courseId) {
      loadPlayerData(lessonQueryId);
    }
  }, [courseId, lessonQueryId]);

  // Keep the lesson in the URL so reload, back/forward and shared links land on the same lesson.
  const handleSelectLesson = (lessonId: number) => {
    setMobileSyllabusOpen(false);
    setActionError(null);
    router.push(`${pathname}?lessonId=${lessonId}`);
  };

  useEffect(() => {
    window.scrollTo({ top: 0 });
    mainRef.current?.scrollTo({ top: 0 });
  }, [currentLesson?.id]);

  const handleValidateActivity = async () => {
    if (!currentLesson || selectedActivityOption === null) return;
    setActivityChecking(true);
    try {
      const res = await fetchApi(`/learning/lesson/${currentLesson.id}/activity`, {
        method: "POST",
        body: JSON.stringify({ selected_option: selectedActivityOption }),
      });

      setActivityFeedback(res);
      if (res.is_correct) {
        confetti({
          particleCount: 50,
          spread: 60,
          origin: { y: 0.8 },
        });
      }
    } catch (err: any) {
      setActionError("Your practice answer could not be checked. Try again.");
    } finally {
      setActivityChecking(false);
    }
  };

  const handleCompleteAndNext = async () => {
    if (!currentLesson) return;
    try {
      const res = await fetchApi(`/learning/lesson/${currentLesson.id}/complete`, {
        method: "POST",
      });

      // If course is finished or this is the last lesson, transition to Assess
      if (currentLesson.is_last_lesson || res.is_course_finished) {
        if (courseMeta?.assessment_id) {
          router.push(`/assess/${courseMeta.assessment_id}`);
        } else {
          router.push(`/progress`);
        }
      } else if (currentLesson.next_lesson_id) {
        handleSelectLesson(currentLesson.next_lesson_id);
      }
    } catch (err: any) {
      setActionError("Lesson progress could not be saved. Check your connection and try again.");
    }
  };

  if (loading && !currentLesson) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center bg-[#F8FAFC]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 rounded-full border-[3px] border-slate-200 border-t-[#1E3A8A] animate-spin" />
          <p className="text-xs text-slate-500 font-medium">Loading course player...</p>
        </div>
      </div>
    );
  }

  if (!currentLesson) {
    return (
      <div className="p-12 text-center bg-[#F8FAFC] min-h-[60vh] flex flex-col items-center justify-center">
        <BookOpen className="h-10 w-10 text-slate-400 mb-3" />
        <h3 className="text-base font-bold text-slate-800">Lesson content unavailable</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          This course unit is being calibrated. Return to the course syllabus to continue.
        </p>
        <Link href={`/courses/${courseId}`} className="mt-4">
          <Button size="sm" variant="outline" className="text-xs rounded-xl">
            <ChevronLeft className="h-3.5 w-3.5 mr-1" /> Back to Course
          </Button>
        </Link>
      </div>
    );
  }

  const courseIdNum = Number(courseId);
  const courseTitleLower = (courseMeta?.title || "").toLowerCase();
  const isBehaviouralCourse = courseIdNum === 1 || courseTitleLower.includes("conduct") || courseTitleLower.includes("ethics") || courseTitleLower.includes("behavioural");
  const isStatisticalCourse = courseIdNum === 2 || courseTitleLower.includes("price") || courseTitleLower.includes("cpi") || courseTitleLower.includes("statistical");
  const isTechnicalCourse = courseIdNum === 3 || courseTitleLower.includes("python") || courseTitleLower.includes("data cleaning") || courseTitleLower.includes("technical") || currentLesson.content_type === "lab";
  const isDigitalGovCourse = courseIdNum === 4 || courseTitleLower.includes("digital governance") || courseTitleLower.includes("cyber");

  return (
    <div className="flex flex-col lg:flex-row min-h-[calc(100vh-65px)] bg-[#F8FAFC]">
      {/* Mobile Syllabus Toggle Bar */}
      <div className="lg:hidden bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between shadow-2xs">
        <div className="flex items-center gap-2 min-w-0">
          <BookOpen className="h-4 w-4 text-[#1E3A8A] shrink-0" />
          <span className="text-xs font-bold text-slate-900 truncate">
            {currentLesson.module_title}: {currentLesson.title}
          </span>
        </div>
        <button
          onClick={() => setMobileSyllabusOpen(!mobileSyllabusOpen)}
          className="text-xs font-bold text-[#1E3A8A] hover:text-[#172554] flex items-center gap-1 shrink-0 ml-2 px-2.5 py-1 rounded-lg bg-blue-50/80 border border-blue-200/80 cursor-pointer transition-colors"
        >
          {mobileSyllabusOpen ? "Hide Syllabus" : "View Syllabus"}
          <ChevronRight className={`h-3.5 w-3.5 transition-transform duration-200 ${mobileSyllabusOpen ? "rotate-90" : ""}`} />
        </button>
      </div>

      {/* Collapsible Left Course Syllabus Sidebar */}
      <aside className={`${mobileSyllabusOpen ? "flex" : "hidden"} lg:flex w-full lg:w-80 border-r border-slate-200 bg-white flex-col shrink-0 transition-all duration-300`}>
        <div className="p-4 border-b border-slate-200 bg-slate-50/70">
          <Link
            href={`/courses/${courseId}`}
            className="text-[11px] font-semibold text-slate-500 hover:text-slate-900 flex items-center gap-1 mb-2.5 transition-colors"
          >
            <ChevronLeft className="h-3.5 w-3.5" /> Back to Course Overview
          </Link>
          <h2 className="text-sm font-bold text-slate-900 line-clamp-2">
            {courseMeta?.title}
          </h2>
          <div className="mt-3 space-y-1.5">
            <div className="flex justify-between text-[11px] font-bold text-slate-600">
              <span>Overall Progress</span>
              <span className="text-[#1E3A8A]">{courseMeta?.progress_percent || 0}%</span>
            </div>
            <div className="relative h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="absolute inset-y-0 left-0 rounded-full navy-teal-gradient transition-all duration-500"
                style={{ width: `${courseMeta?.progress_percent || 0}%` }}
              />
            </div>
          </div>
        </div>

        {/* Modules & Lessons Tree */}
        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          {modulesTree.map((mod, modIdx) => (
            <div key={mod.id} className="space-y-1.5">
              <div className="flex items-center justify-between px-2 text-xs font-bold text-slate-700">
                <span className="truncate">
                  {modIdx + 1}. {mod.title}
                </span>
                <span className="text-[10px] text-slate-400 font-normal">
                  {mod.completed_lessons}/{mod.total_lessons}
                </span>
              </div>

              <div className="space-y-1">
                {mod.lessons.map((l) => {
                  const isCurrent = l.id === currentLesson.id;
                  return (
                    <button
                      key={l.id}
                      onClick={() => handleSelectLesson(l.id)}
                      className={`w-full flex items-center justify-between p-2.5 rounded-xl text-left text-xs transition-all cursor-pointer ${
                        isCurrent
                          ? "bg-[#1E3A8A] text-white font-bold shadow-sm"
                          : l.completed
                          ? "text-slate-700 hover:bg-slate-100 bg-slate-50/80 font-medium"
                          : "text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      <div className="flex items-center gap-2.5 truncate">
                        {l.completed ? (
                          <CheckCircle2
                            className={`h-4 w-4 shrink-0 ${
                              isCurrent ? "text-teal-300" : "text-emerald-600"
                            }`}
                          />
                        ) : (
                          <Circle
                            className={`h-4 w-4 shrink-0 ${
                              isCurrent ? "text-white/60" : "text-slate-300"
                            }`}
                          />
                        )}
                        <span className="truncate">{l.title}</span>
                      </div>
                      <span
                        className={`text-[10px] ml-2 ${
                          isCurrent ? "text-white/80" : "text-slate-400"
                        }`}
                      >
                        {l.duration_minutes}m
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Final Assessment Shortcut Link */}
          {courseMeta?.assessment_id && (
            <div className="pt-4 border-t border-slate-100">
              <Link
                href={`/assess/${courseMeta.assessment_id}`}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-blue-50/70 border border-blue-200 text-[#1E3A8A] hover:bg-blue-100/70 text-xs font-bold transition-colors shadow-2xs"
              >
                <span className="flex items-center gap-2">
                  <Award className="h-4 w-4 text-[#1E3A8A]" />
                  Official Certification Exam
                </span>
                <ChevronRight className="h-4 w-4 text-[#1E3A8A]" />
              </Link>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Stage */}
      <main
        ref={mainRef}
        aria-busy={loading}
        className={`flex-1 flex flex-col overflow-y-auto transition-opacity ${loading ? "opacity-50 pointer-events-none" : ""}`}
      >
        {/* Lesson Header */}
        <div className="px-4 sm:px-8 py-4 bg-white border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
          <div>
            <span className="text-[11px] font-bold text-[#0D9488] uppercase tracking-wider">
              {currentLesson.module_title}
            </span>
            <h1 className="text-lg sm:text-xl font-extrabold text-slate-900 mt-0.5">
              {currentLesson.title}
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs capitalize font-semibold">
              {currentLesson.content_type} {"\u2022"} {currentLesson.duration_minutes} min
            </Badge>
            {currentLesson.completed && (
              <Badge variant="success" className="text-xs inline-flex items-center gap-1 font-bold">
                <CheckCircle2 className="h-3 w-3" /> Completed
              </Badge>
            )}
          </div>
        </div>

        {/* Lesson Body Content */}
        <div className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-8 space-y-6 sm:space-y-8">
          {/* ════════════════════════════════════════════════════════════════
              PRIMARY: ACTUAL SCRAPED VIDEO PLAYER / SEGMENT
              ════════════════════════════════════════════════════════════════ */}
          <div className="space-y-6">
            {/* Video Player or Verified Fallback */}
            <LessonVideo
              title={currentLesson.title}
              videoMapping={currentLesson.video_mapping}
              videoUrl={currentLesson.video_url}
              startTime={currentLesson.video_start_time}
              endTime={currentLesson.video_end_time}
              sourceVideoTitle={currentLesson.source_video_title}
              topic={currentLesson.topic}
              learningObjective={currentLesson.learning_objective}
              durationMinutes={currentLesson.duration_minutes}
              isCompleted={currentLesson.completed}
              onComplete={() => {
                confetti({ particleCount: 40, spread: 60, origin: { y: 0.7 } });
              }}
            />

            {/* Lesson Objectives & Syllabus Brief */}
            <Card className="border-slate-200/90 bg-white shadow-sm rounded-2xl overflow-hidden">
              <CardHeader className="pb-3 border-b border-slate-100 bg-slate-50/50">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <BookOpen className="h-4 w-4 text-[#1E3A8A]" />
                    <CardTitle className="text-sm font-bold text-slate-900">
                      Lesson Objectives & Syllabus Alignment
                    </CardTitle>
                  </div>
                  {currentLesson.topic && (
                    <Badge variant="outline" className="text-[11px] font-semibold text-teal-700 bg-teal-50 border-teal-200">
                      {currentLesson.topic}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="p-5 sm:p-6 space-y-3.5 text-xs leading-relaxed text-slate-700">
                {currentLesson.learning_objective ? (
                  <div className="p-3.5 rounded-xl bg-blue-50/60 border border-blue-100/90 space-y-1">
                    <div className="flex items-center gap-1.5 font-bold text-[#1E3A8A] text-xs">
                      <Sparkles className="h-3.5 w-3.5" />
                      Key Learning Objective:
                    </div>
                    <p className="text-slate-800 font-medium pl-5 text-[12px]">
                      {currentLesson.learning_objective}
                    </p>
                  </div>
                ) : (
                  <p className="text-slate-600">
                    This unit provides official capacity-building training from the {courseMeta?.organization || "Ministry"} covering core operational standards, statutory guidelines, and practical execution frameworks.
                  </p>
                )}

                {/* Collapsible Supplementary Reading & Notes */}
                {currentLesson.content && (
                  <details className="mt-4 pt-3 border-t border-slate-100 group cursor-pointer">
                    <summary className="text-xs font-bold text-[#1E3A8A] group-open:text-slate-900 flex items-center justify-between py-1 transition-colors select-none">
                      <span className="flex items-center gap-1.5">
                        <FileText className="h-3.5 w-3.5 text-[#0D9488]" />
                        View Structured Reading Notes & Code Reference
                      </span>
                      <span className="text-[11px] font-normal text-slate-400 group-open:hidden">
                        Click to expand
                      </span>
                    </summary>
                    <div className="mt-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
                      <LessonMarkdown content={currentLesson.content} title={currentLesson.title} />
                    </div>
                  </details>
                )}
              </CardContent>
            </Card>
          </div>

          {/* IN-LESSON PRACTICE / CONCEPT CHECK ACTIVITY */}
          {currentLesson.activity && currentLesson.activity.has_activity && (
            <Card className="border-blue-200 bg-blue-50/40 shadow-sm rounded-2xl overflow-hidden">
              <CardHeader className="pb-3 border-b border-blue-100 bg-white/60">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-[#1E3A8A]" />
                  <CardTitle className="text-sm font-bold text-slate-900">
                    {t("learn.practice") || "In-Lesson Concept Check"}
                  </CardTitle>
                </div>
                <p className="text-xs text-slate-600">
                  Verify your conceptual understanding before continuing to the hands-on activity.
                </p>
              </CardHeader>
              <CardContent className="p-5 sm:p-6 space-y-4">
                <p className="text-sm font-bold text-slate-900">
                  {currentLesson.activity.question}
                </p>

                <div className="space-y-2.5">
                  {currentLesson.activity.options.map((opt, idx) => {
                    const isSelected = selectedActivityOption === idx;
                    return (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => {
                          setSelectedActivityOption(idx);
                          setActivityFeedback(null);
                        }}
                        className={`w-full p-3.5 rounded-xl border text-left text-xs font-semibold transition-all cursor-pointer flex items-center gap-3 ${
                          isSelected
                            ? "bg-[#1E3A8A] text-white border-[#1E3A8A] shadow-sm"
                            : "bg-white text-slate-800 border-slate-200 hover:bg-slate-50 hover:border-slate-300"
                        }`}
                      >
                        <span
                          className={`h-5 w-5 rounded-full text-[10px] font-bold flex items-center justify-center shrink-0 ${
                            isSelected
                              ? "bg-teal-500 text-white"
                              : "bg-slate-100 text-slate-600"
                          }`}
                        >
                          {String.fromCharCode(65 + idx)}
                        </span>
                        <span>{opt}</span>
                      </button>
                    );
                  })}
                </div>

                {/* Validation Feedback */}
                {activityFeedback && (
                  <div
                    className={`p-3.5 rounded-xl text-xs flex items-start gap-2.5 ${
                      activityFeedback.is_correct
                        ? "bg-emerald-100/80 border border-emerald-300 text-emerald-950"
                        : "bg-rose-100/80 border border-rose-300 text-rose-950"
                    }`}
                  >
                    {activityFeedback.is_correct ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-700 shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-rose-700 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className="font-bold">
                        {activityFeedback.is_correct ? "Correct Concept Application!" : "Review Required"}
                      </p>
                      <p className="mt-0.5 text-[11px] leading-relaxed">
                        {activityFeedback.explanation}
                      </p>
                    </div>
                  </div>
                )}

                <div className="flex justify-end pt-2">
                  <Button
                    size="sm"
                    onClick={handleValidateActivity}
                    disabled={selectedActivityOption === null || activityChecking}
                    className="navy-teal-gradient hover:opacity-95 text-white text-xs font-bold rounded-xl h-9 px-5 shadow-sm"
                  >
                    {activityChecking ? "Checking..." : t("learn.checkAnswer") || "Check Answer"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* ════════════════════════════════════════════════════════════════
              DOMAIN-SPECIFIC IN-FLOW ACTIVITY LAUNCHER
              ════════════════════════════════════════════════════════════════ */}
          {/* 1. TECHNICAL: Hands-on Python Lab */}
          {isTechnicalCourse && (
            <Card className="border-emerald-200 bg-gradient-to-br from-emerald-50/60 via-white to-white shadow-sm rounded-2xl overflow-hidden border-l-4 border-l-emerald-600">
              <CardHeader className="pb-3 border-b border-emerald-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FlaskConical className="h-4 w-4 text-emerald-700" />
                    <span className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                      Executable Python Lab & Sandbox
                    </span>
                  </div>
                  <span className="text-[10px] font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200">
                    Pytest Autograder
                  </span>
                </div>
                <CardTitle className="text-base font-bold text-slate-900 mt-1">
                  {currentLesson.content_type === "lab"
                    ? currentLesson.title
                    : "Interactive Python Coding Lab: Data Wrangling on Microdata"}
                </CardTitle>
                <p className="text-xs text-slate-600 mt-0.5">
                  Write, execute, and debug Python routines in an isolated 3.11 sandbox environment with real-time test assertions and code feedback.
                </p>
              </CardHeader>
              <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1 text-xs text-slate-600">
                  <div className="flex items-center gap-2 font-medium">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Run vectorized calculations in live Python kernel</span>
                  </div>
                  <div className="flex items-center gap-2 font-medium">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Instant grading against automated test suites</span>
                  </div>
                </div>
                {(() => {
                  const topicLower = (currentLesson.topic || "").toLowerCase();
                  let labTarget = "python-pandas-transform-001";
                  if (topicLower.includes("pydantic") || topicLower.includes("validation")) {
                    labTarget = "python-debugging-pfms-001";
                  } else if (topicLower.includes("viz") || topicLower.includes("chart")) {
                    labTarget = "python-data-viz-001";
                  }
                  return (
                    <a href={`/labs/${labTarget}?courseId=${courseId}`}>
                      <Button
                        size="sm"
                        className="h-10 px-5 rounded-xl bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-xs shadow-sm flex items-center gap-1.5 cursor-pointer transition-all"
                      >
                        <Terminal className="h-3.5 w-3.5" />
                        Launch Lab Workspace <ArrowRight className="h-3.5 w-3.5 ml-1" />
                      </Button>
                    </a>
                  );
                })()}
              </CardContent>
            </Card>
          )}

          {/* 2. STATISTICAL: Adaptive Exam & Formula Interpretation */}
          {isStatisticalCourse && (
            <Card className="border-indigo-200 bg-gradient-to-br from-indigo-50/60 via-white to-white shadow-sm rounded-2xl overflow-hidden border-l-4 border-l-indigo-600">
              <CardHeader className="pb-3 border-b border-indigo-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="h-4 w-4 text-indigo-700" />
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-800">
                      Statistical Mastery Activity
                    </span>
                  </div>
                  <span className="text-[10px] font-bold bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full border border-indigo-200">
                    Adaptive Engine
                  </span>
                </div>
                <CardTitle className="text-base font-bold text-slate-900 mt-1">
                  Statistical Data Interpretation & CPI Assessment
                </CardTitle>
                <p className="text-xs text-slate-600 mt-0.5">
                  Calculate elementary price relatives, evaluate modified Laspeyres weightings, and interpret official MoSPI chart visualisations.
                </p>
              </CardHeader>
              <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="space-y-1 text-xs text-slate-600">
                  <div className="flex items-center gap-2 font-medium">
                    <BarChart3 className="h-3.5 w-3.5 text-indigo-600" />
                    <span>Real-time dynamic price index calculation</span>
                  </div>
                  <div className="flex items-center gap-2 font-medium">
                    <CheckCircle2 className="h-3.5 w-3.5 text-indigo-600" />
                    <span>Instant skill mastery calibration</span>
                  </div>
                </div>
                <a href={`/statistical/exam?courseId=${courseId}`}>
                  <Button
                    size="sm"
                    className="h-10 px-5 rounded-xl bg-indigo-700 hover:bg-indigo-800 text-white font-bold text-xs shadow-sm flex items-center gap-1.5 cursor-pointer transition-all"
                  >
                    <Brain className="h-3.5 w-3.5" />
                    Start Statistical Assessment <ArrowRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </a>
              </CardContent>
            </Card>
          )}

          {/* 3. DIGITAL GOVERNANCE: DFIR Sandbox & Tabletop Crisis Scenario */}
          {isDigitalGovCourse && (
            <Card className="border-sky-200 bg-gradient-to-br from-sky-50/60 via-white to-white shadow-sm rounded-2xl overflow-hidden border-l-4 border-l-[#1E3A8A]">
              <CardHeader className="pb-3 border-b border-sky-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-[#1E3A8A]" />
                    <span className="text-xs font-bold uppercase tracking-wider text-[#1E3A8A]">
                      Cyber Defense & Crisis Scenario Activity
                    </span>
                  </div>
                  <span className="text-[10px] font-bold bg-sky-100 text-[#1E3A8A] px-2 py-0.5 rounded-full border border-sky-200">
                    CERT-In Workbench
                  </span>
                </div>
                <CardTitle className="text-base font-bold text-slate-900 mt-1">
                  National Cyber Defense Workbench & Incident Injects
                </CardTitle>
                <p className="text-xs text-slate-600 mt-0.5">
                  Investigate telemetry logs, triage unauthorized intrusion attempts, and practice 6-hour statutory CERT-In breach reporting.
                </p>
              </CardHeader>
              <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex flex-col gap-2 w-full sm:w-auto">
                  <a href={`/digital-governance/sandbox?courseId=${courseId}`}>
                    <Button
                      size="sm"
                      className="w-full sm:w-auto h-10 px-5 rounded-xl bg-[#1E3A8A] hover:bg-[#172554] text-white font-bold text-xs shadow-sm flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      <Terminal className="h-3.5 w-3.5" />
                      Open DFIR Cyber Sandbox
                    </Button>
                  </a>
                  <a href={`/digital-governance/scenarios?courseId=${courseId}`}>
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full sm:w-auto h-10 px-5 rounded-xl border-slate-300 text-slate-700 hover:bg-slate-50 font-bold text-xs shadow-2xs flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      <Scale className="h-3.5 w-3.5 text-amber-600" />
                      Tabletop Crisis Simulation
                    </Button>
                  </a>
                </div>
              </CardContent>
            </Card>
          )}

          {/* 4. BEHAVIOURAL: Conduct Case Study & AI Oral Board */}
          {isBehaviouralCourse && (
            <Card className="border-teal-200 bg-gradient-to-br from-teal-50/60 via-white to-white shadow-sm rounded-2xl overflow-hidden border-l-4 border-l-[#0D9488]">
              <CardHeader className="pb-3 border-b border-teal-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Scale className="h-4 w-4 text-[#0D9488]" />
                    <span className="text-xs font-bold uppercase tracking-wider text-[#0D9488]">
                      Administrative Ethics & Oral Defense Activity
                    </span>
                  </div>
                  <span className="text-[10px] font-bold bg-teal-100 text-teal-800 px-2 py-0.5 rounded-full border border-teal-200">
                    Live Board
                  </span>
                </div>
                <CardTitle className="text-base font-bold text-slate-900 mt-1">
                  Administrative Conduct Inquiries & Oral Defense Board
                </CardTitle>
                <p className="text-xs text-slate-600 mt-0.5">
                  Resolve branching Rule 14 disciplinary dilemmas or take part in an interactive AI civil service oral examination.
                </p>
              </CardHeader>
              <CardContent className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex flex-col gap-2 w-full sm:w-auto">
                  <a href={`/behavioural/cases?courseId=${courseId}`}>
                    <Button
                      size="sm"
                      className="w-full sm:w-auto h-10 px-5 rounded-xl bg-[#0D9488] hover:bg-teal-700 text-white font-bold text-xs shadow-sm flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      <FileCheck2 className="h-3.5 w-3.5" />
                      Launch Case Scenario Inquiry
                    </Button>
                  </a>
                  <a href={`/behavioural/interview?courseId=${courseId}`}>
                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full sm:w-auto h-10 px-5 rounded-xl border-teal-300 bg-teal-50/50 text-[#0D9488] hover:bg-teal-100/50 font-bold text-xs shadow-2xs flex items-center justify-center gap-1.5 cursor-pointer"
                    >
                      <Mic className="h-3.5 w-3.5 text-[#0D9488]" />
                      AI Oral Defense Board
                    </Button>
                  </a>
                </div>
              </CardContent>
            </Card>
          )}

          {actionError && (
            <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-300 bg-rose-50 p-3 text-xs text-rose-900">
              <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
              <p className="text-pretty">{actionError}</p>
            </div>
          )}

          {/* Navigation Controls Bar */}
          <div className="pt-6 border-t border-slate-200 flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              disabled={!currentLesson.prev_lesson_id}
              onClick={() => {
                if (currentLesson.prev_lesson_id) {
                  handleSelectLesson(currentLesson.prev_lesson_id);
                }
              }}
              className="text-xs rounded-xl h-10 px-4 font-semibold border-slate-300 cursor-pointer"
            >
              <ChevronLeft className="h-4 w-4 mr-1" /> {t("learn.previous") || "Previous Unit"}
            </Button>

            <Button
              size="sm"
              onClick={handleCompleteAndNext}
              className="navy-teal-gradient hover:opacity-95 text-white text-xs font-bold px-6 h-10 cursor-pointer rounded-xl shadow-sm"
            >
              {currentLesson.is_last_lesson
                ? t("learn.takeAssessment") || "Take Official Assessment"
                : t("learn.markCompleted") || "Mark Complete & Continue"}
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
}

export default function CourseLearningPlayerPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[80vh] flex items-center justify-center bg-[#F8FAFC]">
          <div className="h-8 w-8 rounded-full border-4 border-slate-200 border-t-[#1E3A8A] animate-spin" />
        </div>
      }
    >
      <LearningPlayerContent />
    </Suspense>
  );
}
