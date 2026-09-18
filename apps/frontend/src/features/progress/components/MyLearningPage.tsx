"use client";

import React, { useEffect, useState } from "react";
import {
  BookOpen,
  Award,
  PlayCircle,
  CheckCircle2,
  Calendar,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Building2,
  Clock,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CertificateModal } from "@/components/certificate/CertificateModal";
import { fetchApi } from "@/lib/api";
import { CertificateItem } from "@/lib/types";
import { useAuth } from "@/lib/auth/AuthContext";
import { useI18n } from "@/lib/i18n";

export default function MyLearningPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [activeTab, setActiveTab] = useState<"in_progress" | "completed" | "skills" | "planned">("in_progress");
  const [profileData, setProfileData] = useState<any>(null);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Certificate Modal
  const [selectedCert, setSelectedCert] = useState<CertificateItem | null>(null);
  const [certModalOpen, setCertModalOpen] = useState(false);

  useEffect(() => {
    Promise.all([
      fetchApi("/profile/"),
      fetchApi("/dashboard/summary"),
    ])
      .then(([prof, dash]) => {
        setProfileData(prof);
        setDashboardData(dash);
      })
      .catch((err) => console.error("Error loading learning data:", err))
      .finally(() => setLoading(false));
  }, []);

  const openCertificate = (cert: CertificateItem) => {
    setSelectedCert(cert);
    setCertModalOpen(true);
  };

  if (loading) {
    return (
      <div className="min-h-[75vh] flex items-center justify-center bg-[#F8FAFC]">
        <div className="h-8 w-8 rounded-full border-3 border-slate-200 border-t-[#1E3A8A] animate-spin" />
      </div>
    );
  }

  const continueCourse = dashboardData?.continue_learning;
  const certificates: CertificateItem[] = profileData?.certificates || [];
  const skills = profileData?.skills || [];
  const plannedCourses = dashboardData?.future_planned || [];
  const progressStats = dashboardData?.my_learning_progress || { in_progress_count: 1, completed_count: 0 };

  return (
    <div className="min-h-[calc(100vh-68px)] flex flex-col bg-[#F8FAFC] w-full text-slate-900">
      {/* 1. Official Institutional Header - Clean White */}
      <section className="bg-white border-b border-slate-200 py-8 sm:py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#1E3A8A] mb-2">
            <Building2 className="h-4 w-4 text-[#1E3A8A]" />
            <span>{t("learning.eyebrow")}</span>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-tight">
                {t("learning.title")}
              </h1>
              <p className="text-xs sm:text-sm text-slate-600 mt-1 font-medium max-w-2xl leading-relaxed">
                {t("learning.subtitle")}
              </p>
            </div>

            <div className="flex items-center gap-3 text-center">
              <div className="px-4 py-2.5 bg-slate-50 rounded-lg border border-slate-200/80 min-w-[90px]">
                <p className="text-xl font-bold text-slate-900">{progressStats.in_progress_count}</p>
                <p className="text-[10px] text-slate-500 uppercase font-semibold">{t("home.inProgress")}</p>
              </div>
              <div className="px-4 py-2.5 bg-emerald-50 rounded-lg border border-emerald-200/80 min-w-[90px]">
                <p className="text-xl font-bold text-emerald-800">{progressStats.completed_count}</p>
                <p className="text-[10px] text-emerald-700 uppercase font-semibold">{t("home.completed")}</p>
              </div>
              <div className="px-4 py-2.5 bg-blue-50 rounded-lg border border-blue-200/80 min-w-[90px]">
                <p className="text-xl font-bold text-[#1E3A8A]">{skills.length}</p>
                <p className="text-[10px] text-slate-600 uppercase font-semibold">{t("home.competencies")}</p>
              </div>
            </div>
          </div>

          {/* Tab Navigation Ribbon */}
          <div className="mt-8 flex border-b border-slate-200 gap-6 text-xs font-semibold overflow-x-auto scrollbar-none">
            <button
              onClick={() => setActiveTab("in_progress")}
              className={`pb-3 transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === "in_progress"
                  ? "border-b-2 border-[#1E3A8A] text-[#1E3A8A] font-bold"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              <PlayCircle className="h-4 w-4" />
              {t("learning.tabInProgress")} ({progressStats.in_progress_count})
            </button>

            <button
              onClick={() => setActiveTab("completed")}
              className={`pb-3 transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === "completed"
                  ? "border-b-2 border-[#1E3A8A] text-[#1E3A8A] font-bold"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              <Award className="h-4 w-4" />
              {t("learning.tabCompleted")} ({certificates.length})
            </button>

            <button
              onClick={() => setActiveTab("skills")}
              className={`pb-3 transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === "skills"
                  ? "border-b-2 border-[#1E3A8A] text-[#1E3A8A] font-bold"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              <Sparkles className="h-4 w-4" />
              {t("learning.tabSkills")} ({skills.length})
            </button>

            <button
              onClick={() => setActiveTab("planned")}
              className={`pb-3 transition-all cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
                activeTab === "planned"
                  ? "border-b-2 border-[#1E3A8A] text-[#1E3A8A] font-bold"
                  : "text-slate-500 hover:text-slate-900"
              }`}
            >
              <Calendar className="h-4 w-4" />
              {t("learning.tabPlanned")} ({plannedCourses.length})
            </button>
          </div>
        </div>
      </section>

      {/* 2. Main Content Canvas */}
      <section className="py-8 sm:py-10 flex-1 w-full">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          {/* Tab 1: In Progress Courses */}
          {activeTab === "in_progress" && (
            <div className="space-y-4">
              {continueCourse ? (
                <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
                  <CardContent className="p-6">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1">
                        <span className="text-[11px] font-semibold text-[#1E3A8A] bg-blue-50 px-2.5 py-0.5 rounded-md border border-blue-200/80 mb-1 inline-block">
                          {t("home.inProgress")}
                        </span>
                        <h3 className="text-base sm:text-lg font-bold text-slate-900">
                          {continueCourse.course_title}
                        </h3>
                        <p className="text-xs text-slate-500">
                          {continueCourse.current_module} • {continueCourse.current_lesson}
                        </p>
                      </div>
                      <a href={`/learn/${continueCourse.course_id}`}>
                        <Button
                          size="sm"
                          className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-medium px-5 h-9 rounded-lg shadow-2xs transition-colors cursor-pointer border border-[#1E3A8A]"
                        >
                          {t("learning.resume")} <ArrowRight className="h-3.5 w-3.5 ml-1" />
                        </Button>
                      </a>
                    </div>

                    <div className="mt-5 space-y-1.5 pt-4 border-t border-slate-100">
                      <div className="flex justify-between text-xs font-bold text-slate-700">
                        <span>{t("home.courseCompletion")}: {continueCourse.progress_percent}%</span>
                        <span className="font-normal text-slate-500">{continueCourse.organization}</span>
                      </div>
                      <Progress value={continueCourse.progress_percent} indicatorClassName="bg-[#1E3A8A]" />
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <div className="py-16 text-center bg-white rounded-xl border border-slate-200 shadow-2xs p-8 max-w-lg mx-auto">
                  <BookOpen className="h-10 w-10 text-slate-400 mx-auto mb-3" />
                  <h3 className="text-sm font-bold text-slate-900">{t("home.noCourseInProgress")}</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    Explore the national statistical catalogue and enroll in foundational training.
                  </p>
                  <a href="/discover">
                    <Button
                      size="sm"
                      className="mt-4 bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-medium rounded-lg h-8 px-4"
                    >
                      {t("home.browseCatalogue")}
                    </Button>
                  </a>
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Completed Courses & Verified Certificates */}
          {activeTab === "completed" && (
            <div className="space-y-4">
              {certificates.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {certificates.map((cert) => (
                    <Card
                      key={cert.certificate_id}
                      className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden flex flex-col justify-between"
                    >
                      <CardHeader className="pb-3 border-b border-slate-100">
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded">
                            {t("home.completed")}
                          </span>
                          <span className="text-[11px] font-mono text-slate-400">{cert.certificate_id}</span>
                        </div>
                        <CardTitle className="text-base font-bold text-slate-900">
                          {cert.course_title}
                        </CardTitle>
                        <CardDescription className="text-xs text-slate-500">
                          {cert.organization} • {cert.issued_date}
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="p-5 flex items-center justify-between">
                        <div>
                          <span className="text-xs text-slate-500 block">Assessment Score</span>
                          <span className="text-base font-extrabold text-emerald-800">{cert.score_percent}%</span>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => openCertificate(cert)}
                          className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-medium rounded-lg gap-1.5 h-8 px-3.5 shadow-2xs cursor-pointer border border-[#1E3A8A]"
                        >
                          <Award className="h-4 w-4" /> {t("learning.viewCertificate")}
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="py-16 text-center bg-white rounded-xl border border-slate-200 shadow-2xs p-8 max-w-lg mx-auto">
                  <Award className="h-10 w-10 text-slate-400 mx-auto mb-3" />
                  <h3 className="text-sm font-bold text-slate-900">{t("learning.noCompleted")}</h3>
                </div>
              )}
            </div>
          )}

          {/* Tab 3: Acquired Competencies */}
          {activeTab === "skills" && (
            <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
              <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle className="text-base font-bold text-slate-900">
                  {t("learning.tabSkills")}
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Demonstrated proficiencies earned through completed official assessments
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                {skills.length > 0 ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                    {skills.map((s: any) => (
                      <div
                        key={s.id}
                        className="p-4 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5"
                      >
                        <span className="text-[10px] font-semibold text-[#1E3A8A] bg-blue-50 border border-blue-200/70 px-2 py-0.5 rounded">
                          {s.category}
                        </span>
                        <h4 className="text-xs font-bold text-slate-900">{s.name}</h4>
                        <p className="text-[11px] text-slate-500">
                          Earned via {s.source_course}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 text-center py-8">
                    {t("learning.noSkills")}
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Tab 4: Planned Courses */}
          {activeTab === "planned" && (
            <div className="space-y-4">
              {plannedCourses.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {plannedCourses.map((pc: any) => (
                    <Card key={pc.id} className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
                      <CardContent className="p-5 flex items-center justify-between">
                        <div>
                          <span className="text-[10px] font-medium text-slate-500 mb-1 block">
                            {t("home.target")} {pc.planned_for}
                          </span>
                          <h4 className="text-sm font-bold text-slate-900">{pc.course_title}</h4>
                          <p className="text-xs text-slate-500 mt-0.5">{pc.organization} • {pc.duration_hours}h</p>
                        </div>
                        <a href={`/courses/${pc.course_id}`}>
                          <Button
                            variant="outline"
                            size="sm"
                            className="text-xs rounded-md border-slate-300 text-slate-700 hover:bg-slate-50 cursor-pointer"
                          >
                            {t("home.viewSyllabus")}
                          </Button>
                        </a>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="py-16 text-center bg-white rounded-xl border border-slate-200 shadow-2xs p-8 max-w-lg mx-auto">
                  <Calendar className="h-10 w-10 text-slate-400 mx-auto mb-3" />
                  <h3 className="text-sm font-bold text-slate-900">{t("learning.noPlanned")}</h3>
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Certificate Modal */}
      <CertificateModal
        certificate={selectedCert}
        open={certModalOpen}
        onClose={() => setCertModalOpen(false)}
      />
    </div>
  );
}
