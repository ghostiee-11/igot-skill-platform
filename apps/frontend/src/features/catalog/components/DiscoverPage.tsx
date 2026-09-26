"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import {
  Search,
  Filter,
  ArrowUpDown,
  BookOpen,
  Building2,
  Clock,
  Sparkles,
  ChevronRight,
  History,
  TrendingUp,
  X,
  RotateCcw,
  Star,
  UserCheck,
  Award,
  ShieldCheck,
  CheckCircle2,
  Zap,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { fetchApi } from "@/lib/api";
import { CoursePreview } from "@/lib/types";
import { useI18n } from "@/lib/i18n";
import { DOMAIN_ACCENT_CLASS, domainForCategory } from "@/features/competency/domains";

/** Accent stripe follows the course's competency domain */
const getCategoryAccent = (category: string): string => {
  const domain = domainForCategory(category);
  return domain ? DOMAIN_ACCENT_CLASS[domain] : "bg-slate-300";
};

const getDifficultyDot = (diff: string) => {
  switch ((diff || "").toLowerCase()) {
    case "beginner":     return "bg-[#059669]";
    case "intermediate": return "bg-amber-500";
    case "advanced":     return "bg-red-500";
    default:             return "bg-slate-400";
  }
};

function DiscoverContent() {
  const { t, language } = useI18n();
  const searchParams = useSearchParams();

  const [query, setQuery]         = useState(searchParams?.get("q") || "");
  const [category, setCategory]   = useState(searchParams?.get("category") || "all");
  const [difficulty, setDifficulty] = useState("all");
  const [source, setSource]       = useState(searchParams?.get("source") || "all");
  const [sort, setSort]           = useState("popular");

  const [courses, setCourses]               = useState<CoursePreview[]>([]);
  const [categories, setCategories]         = useState<string[]>([]);
  const [trendingSearches, setTrendingSearches] = useState<string[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [loading, setLoading]               = useState(true);

  const fetchCourses = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (query)                      params.append("q", query);
    if (category && category !== "all")     params.append("category", category);
    if (difficulty && difficulty !== "all") params.append("difficulty", difficulty);
    if (source && source !== "all")         params.append("source", source);
    if (sort)                       params.append("sort", sort);

    fetchApi<{
      courses: CoursePreview[];
      categories: string[];
      trending_searches: string[];
      user_recent_searches: string[];
    }>(`/discover/courses?${params.toString()}`)
      .then((res) => {
        setCourses(res.courses);
        setCategories(res.categories);
        setTrendingSearches(res.trending_searches);
        setRecentSearches(res.user_recent_searches);
      })
      .catch((err) => console.error("Error fetching discover courses:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchCourses(); }, [category, difficulty, source, sort]);

  const handleSearchSubmit = (e: React.FormEvent) => { e.preventDefault(); fetchCourses(); };
  const handleResetFilters = () => {
    setQuery(""); setCategory("all"); setDifficulty("all"); setSource("all"); setSort("popular");
  };

  const hasActiveFilters = query !== "" || category !== "all" || difficulty !== "all" || source !== "all" || sort !== "popular";

  const getCourseTitle = (course: CoursePreview) => {
    const key = `course.${course.id}.title`;
    const t2 = t(key);
    return t2 !== key ? t2 : course.title;
  };
  const getCourseOverview = (course: CoursePreview) => {
    const key = `course.${course.id}.overview`;
    const t2 = t(key);
    return t2 !== key ? t2 : course.overview;
  };
  const getCourseOrg = (course: CoursePreview) => {
    const key = `org.${course.organization}`;
    const t2 = t(key);
    return t2 !== key ? t2 : course.organization;
  };
  const getCategoryLabel = (cat: string) => {
    const key = `category.${cat}`;
    const t2 = t(key);
    return t2 !== key ? t2 : cat;
  };
  const getTopicLabel = (topic: string) => {
    const key = `topic.${topic}`;
    const t2 = t(key);
    return t2 !== key ? t2 : topic;
  };
  const getDifficultyLabel = (diff: string) => {
    switch (diff.toLowerCase()) {
      case "beginner":     return t("discover.beginner");
      case "intermediate": return t("discover.intermediate");
      case "advanced":     return t("discover.advanced");
      default:             return diff;
    }
  };

  return (
    <div className="min-h-[calc(100vh-68px)] flex flex-col bg-[#F8FAFC] w-full text-slate-900">

      {/* ═══════════════════════════════════════════
          Header — Dark Navy Gradient + Search
          ═══════════════════════════════════════════ */}
      <section className="hero-gradient relative overflow-hidden py-10 sm:py-14">
        {/* Mesh + glow */}
        <div className="absolute inset-0 hero-mesh opacity-50" />
        <div className="absolute -top-20 -right-20 w-80 h-80 rounded-full bg-teal-500/15 blur-[80px] pointer-events-none" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          {/* Eyebrow */}
          <div className="flex items-center gap-2 mb-4">
            <div className="glass-light rounded-full px-3 py-1.5 flex items-center gap-2">
              <Building2 className="h-3.5 w-3.5 text-teal-300" />
              <span className="text-[11px] font-bold text-white/70 uppercase tracking-widest">
                {t("discover.eyebrow")}
              </span>
            </div>
          </div>

          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-tight">
            {t("discover.title")}
          </h1>
          <p className="mt-3 text-sm sm:text-base text-white/60 max-w-3xl leading-relaxed">
            {t("discover.subtitle")}
          </p>

          {/* Search Bar — glassmorphic */}
          <form onSubmit={handleSearchSubmit} className="mt-7 flex flex-col sm:flex-row gap-2.5 max-w-3xl">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/50" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t("discover.searchPlaceholder")}
                className="w-full pl-11 pr-10 h-12 text-sm rounded-xl glass-light text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-teal-400/50 transition-all"
              />
              {query && (
                <button type="button" onClick={() => setQuery("")}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/50 hover:text-white cursor-pointer">
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>
            <Button type="submit"
              className="h-12 px-7 navy-teal-gradient text-white text-sm font-bold rounded-xl shadow-lg border-0 flex items-center justify-center gap-2 cursor-pointer hover:opacity-90 transition-opacity">
              <Search className="h-4 w-4" />
              {t("discover.searchBtn")}
            </Button>
          </form>

          {/* Trending searches */}
          <div className="mt-5 flex flex-wrap items-center gap-2 text-xs">
            <span className="text-white/50 flex items-center gap-1.5 font-semibold">
              <TrendingUp className="h-3.5 w-3.5 text-amber-400" />
              {t("discover.trending")}
            </span>
            {trendingSearches.map((ts) => (
              <button key={ts}
                onClick={() => { setQuery(ts); setCategory("all"); }}
                className="px-3 py-1 rounded-full glass-card text-white/70 hover:text-white text-[11px] font-medium cursor-pointer transition-all hover:scale-105">
                {getTopicLabel(ts)}
              </button>
            ))}
            {recentSearches.length > 0 && (
              <div className="w-full flex flex-wrap items-center gap-2 mt-2 text-xs text-white/40">
                <span className="flex items-center gap-1 font-semibold">
                  <History className="h-3.5 w-3.5 text-white/30" />
                  {t("discover.recent")}
                </span>
                {recentSearches.map((rs, idx) => (
                  <button key={idx} onClick={() => setQuery(rs)}
                    className="text-teal-300 hover:underline font-semibold cursor-pointer">{rs}</button>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════
          Catalogue Workspace
          ═══════════════════════════════════════════ */}
      <section className="py-8 sm:py-10 flex-1 w-full">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">

          {/* Category tabs */}
          <div className="-mx-4 px-4 sm:mx-0 sm:px-0 flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none text-xs touch-pan-x">
            {[
              { key: "all",     label: t("discover.all") },
              { key: "popular", label: t("discover.popular") },
              { key: "new",     label: t("discover.new") },
              ...categories.map(c => ({ key: c, label: getCategoryLabel(c) })),
            ].map((tab) => (
              <button key={tab.key}
                onClick={() => setCategory(tab.key)}
                className={`relative px-3.5 sm:px-4 py-2 rounded-xl font-semibold transition-all cursor-pointer whitespace-nowrap border shrink-0 ${
                  category === tab.key
                    ? "navy-teal-gradient text-white border-transparent shadow-sm"
                    : "bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:border-slate-300"
                }`}>
                {tab.label}
              </button>
            ))}
          </div>

          {/* Filter ribbon */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-3.5 sm:gap-4 p-4 rounded-2xl bg-white border border-slate-200 shadow-sm text-xs">
            <div className="flex items-center justify-between sm:justify-start gap-3 w-full md:w-auto">
              <span className="font-bold text-slate-900 text-sm">
                {courses.length === 1
                  ? t("discover.showingSingle")
                  : t("discover.showingMultiple").replace("{count}", courses.length.toString())}
              </span>
              {hasActiveFilters && (
                <button onClick={handleResetFilters}
                  className="flex items-center gap-1 text-[11px] text-[#1E3A8A] hover:underline font-bold cursor-pointer">
                  <RotateCcw className="h-3 w-3" />
                  {t("discover.resetFilters")}
                </button>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-2.5 sm:gap-3 w-full md:w-auto">
              <div className="flex items-center gap-1.5 flex-1 sm:flex-none">
                <Filter className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <select value={source} onChange={(e) => setSource(e.target.value)}
                  className="w-full sm:w-auto rounded-lg border border-slate-200 px-2.5 py-1.5 bg-white text-slate-700 text-xs font-semibold focus:outline-none focus:border-[#1E3A8A] cursor-pointer">
                  <option value="all">{t("discover.allProviders")}</option>
                  <option value="internal">{t("discover.mospiInternal")}</option>
                  <option value="external">{t("discover.externalAccredited")}</option>
                </select>
              </div>
              <div className="flex items-center gap-1.5 flex-1 sm:flex-none">
                <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}
                  className="w-full sm:w-auto rounded-lg border border-slate-200 px-2.5 py-1.5 bg-white text-slate-700 text-xs font-semibold focus:outline-none focus:border-[#1E3A8A] cursor-pointer">
                  <option value="all">{t("discover.allDifficulties")}</option>
                  <option value="beginner">{t("discover.beginner")}</option>
                  <option value="intermediate">{t("discover.intermediate")}</option>
                  <option value="advanced">{t("discover.advanced")}</option>
                </select>
              </div>
              <div className="flex items-center gap-1.5 border-t sm:border-t-0 sm:border-l border-slate-200 pt-2 sm:pt-0 sm:pl-3 w-full sm:w-auto">
                <ArrowUpDown className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span className="text-slate-400 font-semibold">{t("discover.sort")}:</span>
                <select value={sort} onChange={(e) => setSort(e.target.value)}
                  className="flex-1 sm:flex-none rounded-lg border border-slate-200 px-2.5 py-1.5 bg-white text-slate-700 text-xs font-semibold focus:outline-none focus:border-[#1E3A8A] cursor-pointer">
                  <option value="popular">{t("discover.sortPopular")}</option>
                  <option value="rating">{t("discover.sortRating")}</option>
                  <option value="new">{t("discover.sortNew")}</option>
                  <option value="duration">{t("discover.sortDuration")}</option>
                </select>
              </div>
            </div>
          </div>

          {/* Courses Grid */}
          {loading ? (
            <div className="py-24 text-center">
              <div className="h-9 w-9 rounded-full border-[3px] border-slate-200 border-t-[#1E3A8A] animate-spin mx-auto mb-3" />
              <p className="text-xs text-slate-400 font-medium">{t("discover.updating")}</p>
            </div>
          ) : courses.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {courses.map((course) => (
                <div key={course.id}
                  className="bg-white rounded-2xl border border-slate-200 overflow-hidden flex flex-col card-hover-lift shadow-sm group">
                  {/* Category accent stripe */}
                  <div className={`h-1 w-full ${getCategoryAccent(course.category)}`} />

                  <div className="p-6 flex flex-col flex-1">
                    {/* Top metadata */}
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className="flex items-center gap-1 text-xs text-slate-400 font-medium">
                        <Clock className="h-3.5 w-3.5 text-slate-300" />
                        {course.duration_hours} {t("discover.hours")}
                      </span>
                    </div>

                    {/* Title */}
                    <h3 className="text-base font-bold text-slate-900 leading-snug mb-2 line-clamp-2 group-hover:text-[#1E3A8A] transition-colors">
                      {getCourseTitle(course)}
                    </h3>

                    {/* Overview */}
                    <p className="text-xs text-slate-500 line-clamp-3 mb-4 leading-relaxed flex-1">
                      {getCourseOverview(course)}
                    </p>

                    {/* Metadata */}
                    <div className="space-y-1.5 text-xs text-slate-400 pt-3 border-t border-slate-100">
                      <div className="flex items-center justify-between">
                        <span>{t("discover.accreditedBody")}</span>
                        <span className="font-semibold text-slate-700 text-right truncate max-w-[160px]">
                          {getCourseOrg(course)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>{t("discover.targetDifficulty")}</span>
                        <span className="flex items-center gap-1.5 font-semibold text-slate-700">
                          <span className={`h-2 w-2 rounded-full ${getDifficultyDot(course.difficulty)}`} />
                          {getDifficultyLabel(course.difficulty)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span>{t("discover.modules")}</span>
                        <span className="font-semibold text-slate-700">{course.modules_count} {t("discover.units")}</span>
                      </div>
                    </div>
                  </div>

                  {/* Card Footer */}
                  <div className="px-6 py-4 border-t border-slate-100 bg-slate-50/60 flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs text-slate-500">
                      <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-500" />
                      <span className="font-bold text-slate-800">{course.rating}</span>
                      <span className="text-slate-300">•</span>
                      <span>{course.enrolled_count} {t("discover.enrolled")}</span>
                    </div>
                    <a href={`/courses/${course.id}`}>
                      <Button size="sm"
                        className="navy-teal-gradient text-white text-xs font-bold rounded-xl h-8 px-4 border-0 shadow-sm cursor-pointer hover:opacity-90 transition-opacity flex items-center gap-1">
                        {t("discover.viewCourse")}
                        <ChevronRight className="h-3.5 w-3.5" />
                      </Button>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-20 text-center bg-white rounded-2xl border border-slate-200 max-w-xl mx-auto p-8 shadow-sm">
              <BookOpen className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-base font-bold text-slate-900">{t("discover.noCoursesFound")}</h3>
              <p className="text-xs text-slate-400 mt-2 max-w-md mx-auto leading-relaxed">
                {t("discover.noCoursesDesc")}
              </p>
              <Button variant="outline" size="sm" onClick={handleResetFilters}
                className="mt-5 text-xs rounded-xl border-slate-300 text-[#1E3A8A] hover:bg-slate-50 cursor-pointer">
                <RotateCcw className="h-3.5 w-3.5 mr-1.5" />
                {t("discover.resetFilters")}
              </Button>
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

export default function DiscoverPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[70vh] flex items-center justify-center bg-[#F8FAFC]">
          <div className="h-9 w-9 rounded-full border-[3px] border-slate-200 border-t-[#1E3A8A] animate-spin" />
        </div>
      }
    >
      <DiscoverContent />
    </Suspense>
  );
}
