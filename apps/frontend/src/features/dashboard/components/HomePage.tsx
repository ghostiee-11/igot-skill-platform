"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Compass,
  PlayCircle,
  Clock,
  Flame,
  Target,
  BookOpen,
  Award,
  ArrowRight,
  TrendingUp,
  History,
  Calendar,
  CheckCircle2,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  Building2,
  Star,
  UserCheck,
  Zap,
  BarChart2,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthContext";
import { useI18n } from "@/lib/i18n";
import { CoursePreview } from "@/lib/types";

export default function HomePage() {
  const router = useRouter();
  const { user } = useAuth();
  const { t, language } = useI18n();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi("/dashboard/summary")
      .then((res) => setData(res))
      .catch((err) => console.error("Error loading dashboard summary:", err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center bg-[#F8FAFC]">
        <div className="flex flex-col items-center gap-3">
          <div className="h-9 w-9 rounded-full border-[3px] border-slate-200 border-t-[#1E3A8A] animate-spin" />
          <p className="text-xs text-slate-500 font-medium">Loading Karmayogi dashboard...</p>
        </div>
      </div>
    );
  }

  const learner = data?.learner || {
    full_name: user?.full_name || "Official",
    designation: "Senior Statistical Officer",
    department: "MoSPI",
  };

  const continueCourse = data?.continue_learning;
  const todaysGoals = data?.todays_goals || { target_minutes: 30, achieved_minutes: 20, percent: 66 };
  const streak = data?.learning_streak || { streak_days: 6 };
  const progressStats = data?.my_learning_progress || { in_progress_count: 1, completed_count: 0, overall_progress_percent: 66.7, hours_learned: 2.8 };
  const competencies = data?.competencies?.top_skills || [];
  const recommendedCourses: CoursePreview[] = data?.recommended_courses || [];
  const trendingCourses: CoursePreview[] = data?.trending_courses || [];
  const recentlyExplored = data?.recently_explored || [];
  const futurePlanned = data?.future_planned || [];

  const getCourseTitle = (id: number, fallback: string) => {
    const key = `course.${id}.title`;
    const translated = t(key);
    return translated !== key ? translated : fallback;
  };

  const getCourseOrg = (org: string) => {
    const key = `org.${org}`;
    const translated = t(key);
    return translated !== key ? translated : org;
  };

  const getDifficultyStyle = (difficulty: string) => {
    switch ((difficulty || "").toLowerCase()) {
      case "beginner":     return "border-l-[#059669]";
      case "intermediate": return "border-l-[#1E3A8A]";
      case "advanced":     return "border-l-amber-500";
      default:             return "border-l-slate-300";
    }
  };

  const getInitials = (name: string) =>
    name.split(" ").map(n => n[0]).slice(0, 2).join("").toUpperCase();

  return (
    <div className="min-h-[calc(100vh-68px)] flex flex-col bg-[#F8FAFC] w-full text-slate-900">

      {/* ══════════════════════════════════════════════
          Welcome Header — Dark Navy Gradient
          ══════════════════════════════════════════════ */}
      <section className="hero-gradient relative overflow-hidden">
        {/* Subtle mesh overlay */}
        <div className="absolute inset-0 hero-mesh opacity-60" />
        {/* Glow orbs */}
        <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full bg-teal-500/10 blur-[60px] pointer-events-none" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-10 w-full">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              {/* Avatar with gradient ring */}
              <div className="relative shrink-0">
                <div className="h-14 w-14 rounded-full p-[2px] navy-teal-gradient shadow-lg">
                  <div className="h-full w-full rounded-full bg-[#0C1B3D] text-white flex items-center justify-center font-extrabold text-lg">
                    {getInitials(learner.full_name)}
                  </div>
                </div>
                {/* Online indicator */}
                <span className="absolute bottom-0.5 right-0.5 h-3.5 w-3.5 rounded-full bg-emerald-400 border-2 border-[#0C1B3D]" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Building2 className="h-3.5 w-3.5 text-white/50" />
                  <span className="text-[11px] font-bold text-white/50 uppercase tracking-widest">{t("home.eyebrow")}</span>
                </div>
                <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white leading-tight">
                  {t("home.welcome")}, {learner.full_name}
                </h1>
                <p className="text-xs text-white/60 mt-1 font-medium">
                  {learner.designation} • {learner.department} • {t("home.trainingRecord")}
                </p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 sm:gap-3 w-full sm:w-auto">
              <a href="/discover" className="w-full sm:w-auto">
                <Button size="sm"
                  className="w-full sm:w-auto h-10 px-5 rounded-xl bg-white hover:bg-slate-50 text-[#1E3A8A] text-xs font-bold shadow-sm transition-all cursor-pointer border-0 hover:scale-105 flex items-center justify-center gap-2">
                  <Compass className="h-4 w-4" />
                  {t("home.browseCatalogue")}
                </Button>
              </a>
              <a href="/my-learning" className="w-full sm:w-auto">
                <Button variant="outline" size="sm"
                  className="w-full sm:w-auto h-10 px-5 rounded-xl glass-light text-white border-white/30 hover:bg-white/20 text-xs font-semibold transition-all cursor-pointer flex items-center justify-center gap-2">
                  <BookOpen className="h-4 w-4 text-teal-300" />
                  {t("home.myLearningBtn")}
                </Button>
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════════════════════════════════
          Dashboard Workspace
          ══════════════════════════════════════════════ */}
      <section className="py-8 sm:py-10 flex-1 w-full">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-7">

          {/* Row 1: Continue Learning + Goals + Streak */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

            {/* Continue Learning */}
            <Card className="lg:col-span-2 border-slate-200 bg-white shadow-sm rounded-2xl overflow-hidden card-hover-lift border-l-4 border-l-[#1E3A8A]">
              <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <PlayCircle className="h-4 w-4 text-[#1E3A8A]" />
                    {t("home.continueLearning")}
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-500 mt-0.5">
                    {t("home.activeCoursework")}
                  </CardDescription>
                </div>
                {continueCourse && (
                  <span className="text-[11px] font-bold text-teal-700 bg-teal-50 px-2.5 py-0.5 rounded-full border border-teal-200">
                    {t("home.inProgress")}
                  </span>
                )}
              </CardHeader>
              <CardContent className="p-6">
                {continueCourse ? (
                  <div className="space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <h3 className="text-base font-bold text-slate-900">
                          {getCourseTitle(continueCourse.course_id, continueCourse.course_title)}
                        </h3>
                        <p className="text-xs text-slate-400 font-medium mt-0.5">
                          {continueCourse.current_module} • {continueCourse.current_lesson}
                        </p>
                      </div>
                      <a href={`/learn/${continueCourse.course_id}`}>
                        <Button size="sm"
                          className="navy-teal-gradient text-white text-xs font-bold rounded-xl h-9 px-4 gap-1.5 shadow-sm cursor-pointer border-0 hover:opacity-90 transition-opacity">
                          <PlayCircle className="h-3.5 w-3.5" />
                          {t("home.resumeCourse")}
                        </Button>
                      </a>
                    </div>
                    <div className="space-y-1.5 pt-2">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-slate-500">{t("home.courseCompletion")}</span>
                        <span className="text-[#1E3A8A]">{continueCourse.progress_percent}%</span>
                      </div>
                      <div className="relative h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="absolute inset-y-0 left-0 rounded-full navy-teal-gradient transition-all duration-700"
                          style={{ width: `${continueCourse.progress_percent}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="py-8 text-center space-y-3">
                    <p className="text-xs text-slate-400">{t("home.noCourseInProgress")}</p>
                    <a href="/discover">
                      <Button size="sm" variant="outline"
                        className="text-xs rounded-xl border-slate-300 text-[#1E3A8A] hover:bg-slate-50 cursor-pointer">
                        {t("home.exploreEnroll")} <ArrowRight className="h-3.5 w-3.5 ml-1" />
                      </Button>
                    </a>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Goals + Streak column */}
            <div className="space-y-5">
              {/* Today's Goals */}
              <Card className="border-slate-200 bg-white shadow-sm rounded-2xl overflow-hidden card-hover-lift border-l-4 border-l-[#0D9488]">
                <CardContent className="p-5">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="h-8 w-8 rounded-xl bg-[#0D9488] flex items-center justify-center">
                        <Target className="h-4 w-4 text-white" />
                      </div>
                      <h4 className="text-xs font-bold text-slate-900">{t("home.todaysGoals")}</h4>
                    </div>
                    <span className="text-xs font-bold text-slate-900">
                      {todaysGoals.achieved_minutes} / {todaysGoals.target_minutes}m
                    </span>
                  </div>
                  <div className="relative h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="absolute inset-y-0 left-0 rounded-full bg-[#0D9488] transition-all duration-700"
                      style={{ width: `${todaysGoals.percent}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-2 flex items-center gap-1.5 font-medium">
                    {todaysGoals.achieved_minutes >= todaysGoals.target_minutes ? (
                      <><CheckCircle2 className="h-3.5 w-3.5 text-[#0D9488]" /><span>{t("home.dailyGoalAchieved")}</span></>
                    ) : (
                      <span>{t("home.minutesRemaining").replace("{minutes}", (todaysGoals.target_minutes - todaysGoals.achieved_minutes).toString())}</span>
                    )}
                  </p>
                </CardContent>
              </Card>

              {/* Learning Streak */}
              <Card className="border-slate-200 shadow-sm rounded-2xl overflow-hidden card-hover-lift"
                style={{ background: streak.streak_days >= 3 ? "linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)" : "white" }}>
                <CardContent className="p-5 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-amber-500 flex items-center justify-center shadow-sm">
                      <Flame className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">{t("home.learningStreak")}</h4>
                      <p className="text-xs text-slate-500 font-medium">{t("home.activeDailyEngagement")}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-3xl font-black text-amber-600">{streak.streak_days}</span>
                    <p className="text-[10px] text-amber-500 uppercase font-bold">{t("home.days")}</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Row 2: Recommended Courses */}
          <div>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
                  <div className="h-6 w-6 rounded-lg navy-teal-gradient flex items-center justify-center">
                    <Sparkles className="h-3.5 w-3.5 text-white" />
                  </div>
                  {t("home.recommended")}
                </h2>
                <p className="text-xs text-slate-400 mt-0.5">{t("home.recommendedSubtitle")}</p>
              </div>
              <a href="/discover" className="text-xs font-bold text-[#1E3A8A] hover:underline flex items-center gap-1 cursor-pointer">
                {t("home.viewAll")} <ChevronRight className="h-3.5 w-3.5" />
              </a>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              {recommendedCourses.map((c) => (
                <Card key={c.id}
                  className={`border-slate-200 bg-white flex flex-col justify-between card-hover-lift rounded-2xl overflow-hidden border-l-4 ${getDifficultyStyle(c.difficulty)}`}>
                  <div className="p-4">
                    <div className="flex items-center justify-between gap-2 mb-2.5">
                      <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1">
                        <Clock className="h-3 w-3" />{c.duration_hours}h
                      </span>
                    </div>
                    <h4 className="font-bold text-slate-900 text-sm line-clamp-2 mb-1.5 hover:text-[#1E3A8A] transition-colors">
                      {getCourseTitle(c.id, c.title)}
                    </h4>
                    <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">{c.overview}</p>
                  </div>
                  <div className="p-4 pt-3 flex items-center justify-between border-t border-slate-100 bg-slate-50/50 text-xs">
                    <span className="text-slate-400 font-medium truncate max-w-[120px]">{getCourseOrg(c.organization)}</span>
                    <a href={`/courses/${c.id}`} className="font-bold text-[#1E3A8A] hover:underline flex items-center gap-0.5 cursor-pointer">
                      {t("home.inspectCourse")} →
                    </a>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Row 3: Trending + Future Planned */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Trending Courses */}
            <Card className="border-slate-200 bg-white shadow-sm rounded-2xl overflow-hidden card-hover-lift">
              <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <div className="h-6 w-6 rounded-lg bg-[#059669] flex items-center justify-center">
                      <TrendingUp className="h-3.5 w-3.5 text-white" />
                    </div>
                    {t("home.trending")}
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-400 mt-0.5">{t("home.trendingSubtitle")}</CardDescription>
                </div>
              </CardHeader>
              <CardContent className="p-4 space-y-2">
                {trendingCourses.slice(0, 3).map((tc) => (
                  <a key={tc.id} href={`/courses/${tc.id}`}
                    className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 border border-slate-100 hover:border-[#1E3A8A]/30 transition-all block cursor-pointer group">
                    <div className="space-y-0.5">
                      <h5 className="text-xs font-bold text-slate-900 group-hover:text-[#1E3A8A] transition-colors">
                        {getCourseTitle(tc.id, tc.title)}
                      </h5>
                      <p className="text-[11px] text-slate-400">
                        {getCourseOrg(tc.organization)} • {tc.enrolled_count} {t("home.civilServantsEnrolled")}
                      </p>
                    </div>
                    <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-[#1E3A8A] shrink-0 transition-colors" />
                  </a>
                ))}
              </CardContent>
            </Card>

            {/* Future Planned */}
            <Card className="border-slate-200 bg-white shadow-sm rounded-2xl overflow-hidden card-hover-lift">
              <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    <div className="h-6 w-6 rounded-lg bg-[#1E3A8A] flex items-center justify-center">
                      <Calendar className="h-3.5 w-3.5 text-white" />
                    </div>
                    {t("home.futurePlanned")}
                  </CardTitle>
                  <CardDescription className="text-xs text-slate-400 mt-0.5">{t("home.futurePlannedSubtitle")}</CardDescription>
                </div>
              </CardHeader>
              <CardContent className="p-4 space-y-2">
                {futurePlanned.length > 0 ? (
                  futurePlanned.map((fc: any) => (
                    <div key={fc.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100 text-xs">
                      <div>
                        <h5 className="font-bold text-slate-900">{fc.course_title}</h5>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          {t("home.target")} {fc.planned_for} • {t("home.scheduledBy")}{" "}
                          {fc.source === "admin" ? t("home.departmentAdmin") : t("home.self")}
                        </p>
                      </div>
                      <a href={`/courses/${fc.course_id}`}>
                        <Button variant="outline" size="sm"
                          className="h-7 text-xs rounded-lg border-slate-300 text-slate-600 hover:bg-white cursor-pointer">
                          {t("home.viewSyllabus")}
                        </Button>
                      </a>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 py-6 text-center font-medium">{t("home.noFutureCourses")}</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Row 4: Learning Stats + Competencies */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* My Progress */}
            <Card className="border-slate-200 bg-white shadow-sm rounded-2xl overflow-hidden card-hover-lift">
              <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <div className="h-6 w-6 rounded-lg bg-[#1E3A8A] flex items-center justify-center">
                    <BookOpen className="h-3.5 w-3.5 text-white" />
                  </div>
                  {t("home.myProgress")}
                </CardTitle>
                <a href="/my-learning" className="text-xs font-bold text-[#1E3A8A] hover:underline cursor-pointer">
                  {t("home.fullRecord")} →
                </a>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                    <p className="text-2xl font-extrabold text-slate-900">{progressStats.in_progress_count}</p>
                    <p className="text-[11px] text-slate-400 font-semibold mt-1">{t("home.inProgress")}</p>
                  </div>
                  <div className="p-4 rounded-2xl bg-teal-50 border border-teal-100">
                    <p className="text-2xl font-extrabold text-[#0D9488]">{progressStats.completed_count}</p>
                    <p className="text-[11px] text-[#0D9488] font-semibold mt-1">{t("home.completed")}</p>
                  </div>
                  <div className="p-4 rounded-2xl bg-blue-50 border border-blue-100">
                    <p className="text-2xl font-extrabold text-[#1E3A8A]">{progressStats.hours_learned}h</p>
                    <p className="text-[11px] text-[#1E3A8A] font-semibold mt-1">{t("home.learningHours")}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Competencies */}
            <Card className="border-slate-200 bg-white shadow-sm rounded-2xl overflow-hidden card-hover-lift">
              <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <div className="h-6 w-6 rounded-lg bg-amber-500 flex items-center justify-center">
                    <Award className="h-3.5 w-3.5 text-white" />
                  </div>
                  {t("home.competencies")}
                </CardTitle>
                <a href="/competency" className="text-xs font-bold text-[#1E3A8A] hover:underline cursor-pointer">
                  {t("home.competencyRadar")} →
                </a>
              </CardHeader>
              <CardContent className="p-6">
                {competencies.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {competencies.map((skill: any) => (
                      <span key={skill.id}
                        className="text-xs font-semibold py-1.5 px-3 rounded-full bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1.5">
                        <CheckCircle2 className="h-3.5 w-3.5 text-amber-500" />
                        {skill.name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 text-slate-400 text-xs font-medium">
                    {t("home.completeAssessmentsMsg")}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Row 5: Recently Explored */}
          {recentlyExplored.length > 0 && (
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                <History className="h-4 w-4 text-slate-300" />
                {t("home.recentlyExplored")}
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {recentlyExplored.map((re: any) => (
                  <a key={re.id} href={`/courses/${re.id}`}
                    className="p-4 rounded-2xl border border-slate-200 bg-white hover:border-[#1E3A8A]/40 hover:shadow-sm card-hover-lift block cursor-pointer">
                    <h5 className="text-xs font-bold text-slate-900 truncate hover:text-[#1E3A8A] transition-colors">
                      {getCourseTitle(re.id, re.title)}
                    </h5>
                    <p className="text-[11px] text-slate-400 mt-1">{getCourseOrg(re.organization)} • {re.difficulty}</p>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Trust Ribbon */}
          <div className="pt-5 pb-2 border-t border-slate-200/80 flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-medium">
              <CheckCircle2 className="h-3.5 w-3.5 text-[#059669]" />
              {t("discover.trustTag1")}
            </span>
            <span className="flex items-center gap-1.5 font-medium">
              <ShieldCheck className="h-3.5 w-3.5 text-[#1E3A8A]" />
              {t("discover.trustTag2")}
            </span>
            <span className="flex items-center gap-1.5 font-medium">
              <Award className="h-3.5 w-3.5 text-amber-500" />
              {t("discover.trustTag3")}
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
