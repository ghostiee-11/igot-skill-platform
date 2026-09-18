"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  PlayCircle,
  Clock,
  Video,
  FileText,
  FlaskConical,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  Star,
  Building2,
  BookOpen,
  Scale,
  Sparkles,
  Brain,
  Play,
  Award,
  Code2,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { fetchApi } from "@/lib/api";
import { CourseDetail } from "@/lib/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { useI18n } from "@/lib/i18n";

export default function CourseDetailPage() {
  const { courseId } = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const { t } = useI18n();

  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);
  const [expandedModules, setExpandedModules] = useState<
    Record<number, boolean>
  >({});

  useEffect(() => {
    if (!courseId) return;
    fetchApi<CourseDetail>(`/courses/${courseId}`)
      .then((data) => {
        setCourse(data);
        if (data.modules && data.modules.length > 0) {
          setExpandedModules({ [data.modules[0].id]: true });
        }
      })
      .catch((err) => console.error("Error loading course details:", err))
      .finally(() => setLoading(false));
  }, [courseId]);

  const toggleModule = (modId: number) => {
    setExpandedModules((prev) => ({
      ...prev,
      [modId]: !prev[modId],
    }));
  };

  const handleEnrollOrResume = async () => {
    if (!user) {
      router.push("/login");
      return;
    }

    if (course?.enrollment) {
      router.push(`/learn/${course.id}`);
      return;
    }

    setEnrolling(true);
    try {
      await fetchApi(`/courses/${courseId}/enroll`, {
        method: "POST",
      });
      router.push(`/learn/${courseId}`);
    } catch (err: any) {
      alert(err.message || "Failed to enroll in course");
      setEnrolling(false);
    }
  };

  // Helper for localized course text
  const getCourseTitle = () => {
    if (!course) return "";
    const key = `course.${course.id}.title`;
    const translated = t(key);
    return translated !== key ? translated : course.title;
  };

  const getCourseOverview = () => {
    if (!course) return "";
    const key = `course.${course.id}.overview`;
    const translated = t(key);
    return translated !== key ? translated : course.overview;
  };

  const getCourseOrg = () => {
    if (!course) return "";
    const key = `org.${course.organization}`;
    const translated = t(key);
    return translated !== key ? translated : course.organization;
  };

  const getDifficultyLabel = (diff: string) => {
    switch (diff.toLowerCase()) {
      case "beginner":
        return t("discover.beginner");
      case "intermediate":
        return t("discover.intermediate");
      case "advanced":
        return t("discover.advanced");
      default:
        return diff;
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center bg-[#F8FAFC]">
        <div className="h-8 w-8 rounded-full border-3 border-slate-200 border-t-[#1E3A8A] animate-spin" />
      </div>
    );
  }

  if (!course) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4 bg-[#F8FAFC]">
        <BookOpen className="h-12 w-12 text-slate-400 mb-3" />
        <h2 className="text-xl font-bold text-slate-900">
          {t("course.notFound")}
        </h2>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          {t("course.notFoundDesc")}
        </p>
        <a href="/discover">
          <Button
            variant="outline"
            size="sm"
            className="mt-5 text-xs rounded-lg border-slate-300 text-[#1E3A8A] hover:bg-slate-50 cursor-pointer"
          >
            {t("course.backToCatalogue")}
          </Button>
        </a>
      </div>
    );
  }

  const isEnrolled = !!course.enrollment;
  const progressPct = course.enrollment?.progress_percent || 0;
  const courseIdNum = Number(course.id);
  const isBehaviouralCourse = courseIdNum === 1 || course.category?.toLowerCase() === "behavioural";
  const isStatisticalCourse = courseIdNum === 2 || course.category?.toLowerCase() === "statistical" || course.category?.toLowerCase().includes("price");
  const isTechnicalCourse = courseIdNum === 3 || course.category?.toLowerCase() === "technical" || course.category?.toLowerCase().includes("data science");
  const isDigitalGovCourse = courseIdNum === 4 || course.category?.toLowerCase() === "digital governance" || course.category?.toLowerCase().includes("public administration");

  return (
    <div className="min-h-[calc(100vh-68px)] flex flex-col bg-[#F8FAFC] w-full text-slate-900">
      {/* 1. Institutional Course Header */}
      <section className="bg-white border-b border-slate-200 py-8 sm:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          {/* Eyebrow & Badges */}
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className="text-xs font-medium text-slate-600">
              {t(`category.${course.category}`) !==
              `category.${course.category}`
                ? t(`category.${course.category}`)
                : course.category}
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs font-medium text-slate-600">
              {getDifficultyLabel(course.difficulty)}
            </span>
            {isBehaviouralCourse && (
              <>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-md border bg-teal-50 text-[#0D9488] border-teal-200/80 flex items-center gap-1">
                  <Sparkles className="h-3 w-3 text-[#0D9488]" />
                  Oral Board & Case Inquiries
                </span>
              </>
            )}
            {isStatisticalCourse && (
              <>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-md border bg-indigo-50 text-[#4338CA] border-indigo-200/80 flex items-center gap-1">
                  <Brain className="h-3 w-3 text-[#4338CA]" />
                  Adaptive Exam Engine
                </span>
              </>
            )}
            {isTechnicalCourse && (
              <>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-md border bg-emerald-50 text-emerald-800 border-emerald-200/80 flex items-center gap-1">
                  <FlaskConical className="h-3 w-3 text-emerald-700" />
                  Hands-on Labs
                </span>
              </>
            )}
            {isDigitalGovCourse && (
              <>
                <span className="text-xs text-slate-400">•</span>
                <span className="text-[11px] font-semibold px-2.5 py-0.5 rounded-md border bg-sky-50 text-sky-800 border-sky-200/80 flex items-center gap-1">
                  <ShieldCheck className="h-3 w-3 text-sky-700" />
                  Cyber Defense Sandbox
                </span>
              </>
            )}
          </div>

          {/* Title */}
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight max-w-4xl">
            {getCourseTitle()}
          </h1>

          {/* Overview */}
          <p className="mt-3 text-sm sm:text-base text-slate-600 max-w-4xl leading-relaxed">
            {getCourseOverview()}
          </p>

          {/* Instructor & Accreditation Info Strip */}
          <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4 py-4 border-y border-slate-100 text-xs">
            <div>
              <span className="text-slate-400 block font-medium">
                {t("course.instructor")}
              </span>
              <span className="font-bold text-slate-900 mt-0.5 block">
                {course.instructor}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block font-medium">
                {t("course.organization")}
              </span>
              <span className="font-bold text-slate-900 mt-0.5 block">
                {getCourseOrg()}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block font-medium">
                {t("course.duration")}
              </span>
              <span className="font-bold text-slate-900 mt-0.5 block flex items-center gap-1">
                <Clock className="h-3.5 w-3.5 text-slate-400" />
                {course.duration_hours} {t("course.learningHours")}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block font-medium">
                {t("course.officialRating")}
              </span>
              <span className="font-bold text-slate-900 mt-0.5 flex items-center gap-1.5">
                <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-500" />
                <span>{course.rating}</span>
                <span className="text-slate-400 font-normal">
                  ({course.enrolled_count} {t("course.enrolled")})
                </span>
              </span>
            </div>
          </div>

          {/* Start / Resume Action CTA */}
          <div className="mt-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Button
                onClick={handleEnrollOrResume}
                disabled={enrolling}
                size="lg"
                className="navy-teal-gradient text-white font-bold shadow-md rounded-xl px-8 h-12 text-sm border-0 transition-all cursor-pointer hover:opacity-90 hover:scale-105"
              >
                {enrolling ? (
                  t("course.enrolling")
                ) : isEnrolled ? (
                  <>
                    <Play className="h-4 w-4 fill-white mr-2" />
                    {t("course.resumeCourse")}
                  </>
                ) : (
                  <>
                    <BookOpen className="h-4 w-4 mr-2" />
                    {t("course.enrollNow")}
                  </>
                )}
              </Button>

              {isEnrolled && (
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-3 py-1.5 rounded-lg border border-emerald-200">
                  {progressPct}% {t("course.completed")}
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {course.assessment_id && (
                <a href={`/assess/${course.assessment_id}`}>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs rounded-xl border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400 cursor-pointer"
                  >
                    {t("course.takeAssessment")} <ArrowRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </a>
              )}
              {isBehaviouralCourse && (
                <a href={`/behavioural/interview?courseId=${course.id}`}>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs rounded-xl border-teal-300 bg-teal-50/60 text-[#0D9488] hover:bg-teal-100/60 cursor-pointer flex items-center gap-1.5 font-semibold"
                  >
                    <Video className="h-3.5 w-3.5 text-[#0D9488]" />
                    AI Oral Board
                  </Button>
                </a>
              )}
              {isStatisticalCourse && (
                <a href={`/statistical/exam?courseId=${course.id}`}>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs rounded-xl border-indigo-300 bg-indigo-50/60 text-[#4338CA] hover:bg-indigo-100/60 cursor-pointer flex items-center gap-1.5 font-semibold"
                  >
                    <Brain className="h-3.5 w-3.5 text-[#4338CA]" />
                    Adaptive Statistical Exam
                  </Button>
                </a>
              )}
              {isTechnicalCourse && (
                <a href="/labs">
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs rounded-xl border-emerald-300 bg-emerald-50/60 text-emerald-800 hover:bg-emerald-100/60 cursor-pointer flex items-center gap-1.5 font-semibold"
                  >
                    <FlaskConical className="h-3.5 w-3.5 text-emerald-700" />
                    Hands-on Lab Workspace
                  </Button>
                </a>
              )}
              {isDigitalGovCourse && (
                <>
                  <a href="/digital-governance/sandbox">
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs rounded-xl border-blue-300 bg-blue-50/60 text-[#1E3A8A] hover:bg-blue-100/60 cursor-pointer flex items-center gap-1.5 font-semibold"
                    >
                      <ShieldAlert className="h-3.5 w-3.5 text-[#1E3A8A]" />
                      Cyber Defense Sandbox
                    </Button>
                  </a>
                  <a href="/digital-governance/scenarios">
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-xs rounded-xl border-amber-300 bg-amber-50/60 text-amber-800 hover:bg-amber-100/60 cursor-pointer flex items-center gap-1.5 font-semibold"
                    >
                      <Scale className="h-3.5 w-3.5 text-amber-700" />
                      Tabletop Scenarios
                    </Button>
                  </a>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 2. Syllabus & Materials Section */}
      <section className="py-8 sm:py-10 flex-1 w-full">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Main Column: Expandable Syllabus */}
            <div className="lg:col-span-2 space-y-6">
              <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
                <CardHeader className="border-b border-slate-100 pb-4">
                  <CardTitle className="text-base font-bold text-slate-900">
                    {t("course.syllabus")}
                  </CardTitle>
                  <p className="text-xs text-slate-500">
                    {course.modules.length} {t("discover.units")} •{" "}
                    {course.counts.readings +
                      course.counts.videos +
                      course.counts.labs}{" "}
                    {t("course.learningHours")}
                  </p>
                </CardHeader>
                <CardContent className="p-4 space-y-3">
                  {course.modules.map((mod, idx) => {
                    const isExpanded = expandedModules[mod.id];
                    return (
                      <div
                        key={mod.id}
                        className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-2xs"
                      >
                        <button
                          onClick={() => toggleModule(mod.id)}
                          className="w-full flex items-center justify-between p-4 bg-slate-50/70 hover:bg-slate-100/70 transition-colors text-left cursor-pointer"
                        >
                          <div className="flex items-center gap-3">
                            <span className="h-6 w-6 rounded-full bg-[#1E3A8A]/10 text-[#1E3A8A] font-bold text-xs flex items-center justify-center">
                              {idx + 1}
                            </span>
                            <div>
                              <h4 className="text-xs sm:text-sm font-bold text-slate-900">
                                {mod.title}
                              </h4>
                              {mod.description && (
                                <p className="text-[11px] text-slate-500 mt-0.5">
                                  {mod.lessons.length} {t("course.lessons")} • {mod.description}
                                </p>
                              )}
                            </div>
                          </div>
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-slate-400 shrink-0" />
                          )}
                        </button>

                        {isExpanded && mod.lessons && (
                          <div className="p-2 divide-y divide-slate-100 bg-white">
                            {mod.lessons.map((lesson) => (
                              <div
                                key={lesson.id}
                                className="flex items-center justify-between py-2.5 px-3 hover:bg-slate-50 rounded-lg text-xs group"
                              >
                                <div className="flex items-center gap-2.5">
                                  {lesson.content_type === "reading" && (
                                    <FileText className="h-3.5 w-3.5 text-blue-600" />
                                  )}
                                  {lesson.content_type === "video" && (
                                    <Video className="h-3.5 w-3.5 text-amber-600" />
                                  )}
                                  {lesson.content_type === "lab" && (
                                    <FlaskConical className="h-3.5 w-3.5 text-indigo-600" />
                                  )}
                                  <span className="text-slate-700 font-medium group-hover:text-[#1E3A8A] transition-colors">
                                    {lesson.title}
                                  </span>
                                </div>
                                <div className="flex items-center gap-3 text-slate-500">
                                  {lesson.has_activity && (
                                    <span className="text-[10px] bg-slate-100 text-slate-700 font-medium px-2 py-0.5 rounded border border-slate-200">
                                      {t("course.includesPractice")}
                                    </span>
                                  )}
                                  <span className="text-slate-400 text-[11px]">
                                    {lesson.duration_minutes}m
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </CardContent>
              </Card>

              {/* Specialized Hands-On Labs & Crisis Simulations for Digital Governance */}
              {(course.category?.toLowerCase().includes("digital governance") ||
                course.category?.toLowerCase().includes("cyber") ||
                course.title?.toLowerCase().includes("digital governance")) && (
                <Card className="border-slate-200 bg-gradient-to-br from-white to-blue-50/50 shadow-sm rounded-xl overflow-hidden border-l-4 border-l-[#1E3A8A]">
                  <CardHeader className="border-b border-slate-100 pb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="p-1.5 rounded-lg bg-[#1E3A8A] text-white">
                        <ShieldAlert className="h-4 w-4" />
                      </div>
                      <div>
                        <CardTitle className="text-sm font-bold text-slate-900">
                          Practical DFIR Labs & Crisis Workbenches
                        </CardTitle>
                        <p className="text-[11px] text-slate-500">
                          Interactive investigation consoles and CERT-In crisis
                          response simulations for this competency
                        </p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <a
                        href="/digital-governance/sandbox"
                        className="p-3.5 rounded-xl bg-white border border-slate-200 hover:border-[#1E3A8A] hover:shadow-md transition-all group block"
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-100">
                            8 Live DFIR Labs
                          </span>
                          <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#1E3A8A] transition-colors" />
                        </div>
                        <h5 className="text-xs font-bold text-slate-900 group-hover:text-[#1E3A8A] transition-colors">
                          Cyber Defense Sandbox
                        </h5>
                        <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                          Analyze auth logs, deobfuscate phishing payloads, and
                          audit cloud infrastructure in an interactive Marimo
                          console.
                        </p>
                      </a>

                      <a
                        href="/digital-governance/scenarios"
                        className="p-3.5 rounded-xl bg-white border border-slate-200 hover:border-[#1E3A8A] hover:shadow-md transition-all group block"
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-100">
                            National Incident Injects
                          </span>
                          <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#1E3A8A] transition-colors" />
                        </div>
                        <h5 className="text-xs font-bold text-slate-900 group-hover:text-[#1E3A8A] transition-colors">
                          Tabletop Crisis Simulation
                        </h5>
                        <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                          Practice real-time crisis decision making, 6-hour
                          CERT-In breach reporting, and DPDP Act 2023
                          compliance.
                        </p>
                      </a>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Sidebar Column: Materials Breakdown & Skills Gained */}
            <div className="space-y-6">
              {/* Materials Breakdown */}
              <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
                <CardHeader className="pb-3 border-b border-slate-100">
                  <CardTitle className="text-xs sm:text-sm font-bold text-slate-900">
                    {t("course.materialsIncluded")}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4 space-y-2.5 text-xs text-slate-600">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-blue-600" />
                      {t("course.readings")}
                    </span>
                    <span className="font-bold text-slate-900">
                      {course.counts.readings}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Video className="h-4 w-4 text-amber-600" />
                      {t("course.videos")}
                    </span>
                    <span className="font-bold text-slate-900">{course.counts.videos}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <FlaskConical className="h-4 w-4 text-indigo-600" />
                      {t("course.practicalLabs")}
                    </span>
                    <span className="font-bold text-slate-900">
                      {course.counts.labs}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-slate-600">
                      <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
                      {t("course.mcqTest")}
                    </span>
                    <span className="font-bold text-slate-900">
                      {course.counts.assessments}
                    </span>
                  </div>
                  <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                    <span className="flex items-center gap-2">
                      <Award className="h-4 w-4 text-[#0D9488]" />
                      {t("course.officialCertificate")}
                    </span>
                    <span className="font-bold text-emerald-600">{t("course.accredited")}</span>
                  </div>
                </CardContent>
              </Card>

              {/* Skills Gained */}
              <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
                <CardHeader className="pb-3 border-b border-slate-100">
                  <CardTitle className="text-xs sm:text-sm font-bold text-slate-900">
                    {t("course.skillsGained")}
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-4">
                  <div className="flex flex-wrap gap-2">
                    {(course.skills_gained || []).map((skill: string, idx: number) => (
                      <span
                        key={idx}
                        className="text-[11px] font-medium bg-amber-50 text-amber-900 border border-amber-200/80 px-2.5 py-1 rounded-md flex items-center gap-1.5"
                      >
                        <CheckCircle2 className="h-3 w-3 text-amber-600" />
                        {skill}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* 1. Behavioural Competency Pipeline - Course 1 */}
              {isBehaviouralCourse && (
                <Card className="border-blue-200 bg-gradient-to-br from-blue-50/60 to-slate-50 shadow-2xs rounded-xl overflow-hidden border">
                  <CardHeader className="pb-2.5 border-b border-blue-100/80 bg-white/70">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs sm:text-sm font-bold text-[#1E3A8A] flex items-center gap-1.5">
                        <Sparkles className="h-4 w-4 text-[#0D9488]" />
                        Behavioural Competency Pipeline
                      </CardTitle>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-[#1E3A8A]">
                        Live Multimodal
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 space-y-3 text-xs">
                    <p className="text-slate-600 leading-relaxed text-[11px]">
                      Evaluate practical civil service decision-making, ethical judgement, leadership, and oral defense grounded in statutory conduct rules.
                    </p>
                    <div className="space-y-2 pt-1">
                      <a
                        href={`/behavioural/cases?courseId=${course.id}`}
                        className="w-full flex items-center justify-between p-2.5 rounded-lg bg-white border border-slate-200 hover:border-[#1E3A8A] hover:shadow-xs transition-all font-semibold text-slate-800 text-xs group"
                      >
                        <span className="flex items-center gap-2">
                          <Scale className="h-3.5 w-3.5 text-[#1E3A8A]" />
                          Solve Case Inquiries (Consequential MCQs)
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#1E3A8A] group-hover:translate-x-0.5 transition-all" />
                      </a>
                      <a
                        href={`/behavioural/interview?courseId=${course.id}`}
                        className="w-full flex items-center justify-between p-2.5 rounded-lg bg-white border border-slate-200 hover:border-[#1E3A8A] hover:shadow-xs transition-all font-semibold text-slate-800 text-xs group"
                      >
                        <span className="flex items-center gap-2">
                          <Video className="h-3.5 w-3.5 text-[#0D9488]" />
                          Launch AI Live Interview
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#1E3A8A] group-hover:translate-x-0.5 transition-all" />
                      </a>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 2. Statistical Competency Engine - Course 2 */}
              {isStatisticalCourse && (
                <Card className="border-indigo-200 bg-gradient-to-br from-indigo-50/60 to-slate-50 shadow-2xs rounded-xl overflow-hidden border">
                  <CardHeader className="pb-2.5 border-b border-indigo-100/80 bg-white/70">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs sm:text-sm font-bold text-[#312E81] flex items-center gap-1.5">
                        <Brain className="h-4 w-4 text-[#4338CA]" />
                        Statistical Competency Engine
                      </CardTitle>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-100 text-[#4338CA]">
                        Adaptive Branching
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 space-y-3 text-xs">
                    <p className="text-slate-600 leading-relaxed text-[11px]">
                      Engage with parameterized inflation calculation problems, modified Laspeyres aggregation, Jevons geometric means, and real-time mastery tracking.
                    </p>
                    <div className="space-y-2 pt-1">
                      <a
                        href={`/statistical/exam?courseId=${course.id}`}
                        className="w-full flex items-center justify-between p-2.5 rounded-lg bg-white border border-slate-200 hover:border-[#4338CA] hover:shadow-xs transition-all font-semibold text-slate-800 text-xs group"
                      >
                        <span className="flex items-center gap-2">
                          <Brain className="h-3.5 w-3.5 text-[#4338CA]" />
                          Take Adaptive Statistical Exam
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-[#4338CA] group-hover:translate-x-0.5 transition-all" />
                      </a>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 3. Technical Competency Pipeline - Course 3 */}
              {isTechnicalCourse && (
                <Card className="border-emerald-200 bg-gradient-to-br from-emerald-50/60 to-slate-50 shadow-2xs rounded-xl overflow-hidden border">
                  <CardHeader className="pb-2.5 border-b border-emerald-100/80 bg-white/70">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs sm:text-sm font-bold text-emerald-900 flex items-center gap-1.5">
                        <FlaskConical className="h-4 w-4 text-emerald-700" />
                        Technical Competency Pipeline
                      </CardTitle>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                        Interactive Labs
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 space-y-3 text-xs">
                    <p className="text-slate-600 leading-relaxed text-[11px]">
                      Execute vectorized Python data cleaning scripts, Pandas microdata wrangling, and automated validation pipelines in an interactive Jupyter &amp; Marimo sandbox.
                    </p>
                    <div className="space-y-2 pt-1">
                      <a
                        href="/labs/1002"
                        className="w-full flex items-center justify-between p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 hover:border-emerald-700 hover:shadow-xs transition-all font-semibold text-emerald-900 text-xs group"
                      >
                        <span className="flex items-center gap-2">
                          <FlaskConical className="h-3.5 w-3.5 text-emerald-700" />
                          Launch Pandas Pipeline Lab (#1002)
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-emerald-700 group-hover:translate-x-0.5 transition-all" />
                      </a>
                      <a
                        href="/labs?tag=pandas"
                        className="w-full flex items-center justify-between p-2.5 rounded-lg bg-white border border-slate-200 hover:border-slate-400 hover:shadow-xs transition-all font-semibold text-slate-700 text-xs group"
                      >
                        <span className="flex items-center gap-2">
                          <Code2 className="h-3.5 w-3.5 text-slate-500" />
                          Browse All Technical Labs
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-slate-700 group-hover:translate-x-0.5 transition-all" />
                      </a>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 4. Digital Governance Sandbox - Course 4 */}
              {isDigitalGovCourse && (
                <Card className="border-sky-200 bg-gradient-to-br from-sky-50/60 to-slate-50 shadow-2xs rounded-xl overflow-hidden border">
                  <CardHeader className="pb-2.5 border-b border-sky-100/80 bg-white/70">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-xs sm:text-sm font-bold text-sky-950 flex items-center gap-1.5">
                        <ShieldCheck className="h-4 w-4 text-sky-700" />
                        Digital Governance Sandbox
                      </CardTitle>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-sky-100 text-sky-800">
                        Cyber Sandbox
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="p-4 space-y-3 text-xs">
                    <p className="text-slate-600 leading-relaxed text-[11px]">
                      Simulate critical public financial management workflows, CERT-In compliance incident responses, and treasury controls under active attack scenarios.
                    </p>
                    <div className="space-y-2 pt-1">
                      <a
                        href={`/digital-governance/sandbox?courseId=${course.id}`}
                        className="w-full flex items-center justify-between p-2.5 rounded-lg bg-white border border-slate-200 hover:border-sky-700 hover:shadow-xs transition-all font-semibold text-slate-800 text-xs group"
                      >
                        <span className="flex items-center gap-2">
                          <ShieldCheck className="h-3.5 w-3.5 text-sky-700" />
                          Launch Cyber Defense Sandbox
                        </span>
                        <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-sky-700 group-hover:translate-x-0.5 transition-all" />
                      </a>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
