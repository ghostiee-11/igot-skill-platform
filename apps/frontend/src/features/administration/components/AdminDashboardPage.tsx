"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ShieldAlert,
  ShieldCheck,
  Users,
  BookOpen,
  Award,
  TrendingUp,
  UserPlus,
  PlusCircle,
  AlertTriangle,
  CheckCircle2,
  Check,
  Search,
  Building2,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { fetchApi } from "@/lib/api";
import CompetencyAnalyticsSection from "@/features/administration/components/CompetencyAnalyticsSection";
import { useAuth } from "@/lib/auth/AuthContext";
import { useI18n } from "@/lib/i18n";

export default function AdminDashboardPage() {
  const router = useRouter();
  const { user, isAdmin, isLoading } = useAuth();
  const { t } = useI18n();

  const [adminData, setAdminData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Course Assignment Modal state
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);
  const [assignSuccess, setAssignSuccess] = useState<string | null>(null);
  const [assigning, setAssigning] = useState(false);

  // New Course Modal state
  const [courseModalOpen, setCourseModalOpen] = useState(false);
  const [newCourse, setNewCourse] = useState({
    title: "",
    overview: "",
    instructor: "",
    organization: "MoSPI / NSSTA",
    duration_hours: 5.0,
    difficulty: "intermediate",
    category: "Sample Surveys",
    source: "internal",
  });
  const [creatingCourse, setCreatingCourse] = useState(false);

  const loadAdminData = () => {
    setLoading(true);
    fetchApi("/admin/overview")
      .then((data) => setAdminData(data))
      .catch((err) => console.error("Error loading admin data:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (!isLoading) {
      if (!user || user.role !== "admin") {
        router.push("/home");
        return;
      }
      loadAdminData();
    }
  }, [user, isAdmin, isLoading, router]);

  const handleAssignCourse = async () => {
    if (!selectedUserId || !selectedCourseId) return;
    setAssigning(true);
    try {
      const res = await fetchApi("/admin/assign-course", {
        method: "POST",
        body: JSON.stringify({
          user_id: selectedUserId,
          course_id: selectedCourseId,
        }),
      });

      setAssignSuccess(res.message);
      loadAdminData();
      setTimeout(() => {
        setAssignSuccess(null);
        setAssignModalOpen(false);
      }, 2000);
    } catch (err: any) {
      alert("Failed to assign course: " + err.message);
    } finally {
      setAssigning(false);
    }
  };

  const handleCreateCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingCourse(true);
    try {
      await fetchApi("/admin/courses", {
        method: "POST",
        body: JSON.stringify(newCourse),
      });

      setCourseModalOpen(false);
      loadAdminData();
      alert("Course created successfully in catalogue!");
    } catch (err: any) {
      alert("Error creating course: " + err.message);
    } finally {
      setCreatingCourse(false);
    }
  };

  if (loading || !adminData) {
    return (
      <div className="min-h-[75vh] flex items-center justify-center bg-[#F8FAFC]">
        <div className="h-8 w-8 rounded-full border-3 border-slate-200 border-t-[#1E3A8A] animate-spin" />
      </div>
    );
  }

  const summary = adminData.summary || {};
  const usersList = adminData.users || [];
  const courseAnalytics = adminData.course_analytics || [];
  const strugglingQuestions = adminData.struggling_questions || [];

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* 1. Institutional White Header Banner */}
      <section className="bg-white border-b border-slate-200 py-8 sm:py-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <Building2 className="h-3.5 w-3.5 text-[#1E3A8A]" />
                <span className="text-[11px] font-bold text-[#1E3A8A] uppercase tracking-wider">
                  {t("admin.eyebrow")}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
                  <ShieldAlert className="h-7 w-7 text-[#1E3A8A]" />
                  {t("admin.title")}
                </h1>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-md bg-blue-50 text-[#1E3A8A] border border-blue-200">
                  <ShieldCheck className="h-3 w-3 text-[#1E3A8A]" />
                  {t("admin.authorityBadge")}
                </span>
              </div>
              <p className="text-xs sm:text-sm text-slate-500 mt-1">
                {t("admin.subtitle")}
              </p>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <Button
                size="sm"
                onClick={() => setCourseModalOpen(true)}
                className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold gap-1.5 px-4 shadow-xs cursor-pointer"
              >
                <PlusCircle className="h-4 w-4" /> {t("admin.addNewCourse")}
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* 2. Main Content Canvas */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <CompetencyAnalyticsSection />
        {/* Aggregate Metrics Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
          <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
            <CardContent className="p-5 flex items-center gap-3.5">
              <div className="h-11 w-11 rounded-xl bg-blue-50 text-[#1E3A8A] flex items-center justify-center">
                <Users className="h-6 w-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{summary.total_users}</p>
                <p className="text-[11px] text-slate-500 font-medium">{t("admin.registeredOfficials")}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
            <CardContent className="p-5 flex items-center gap-3.5">
              <div className="h-11 w-11 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
                <BookOpen className="h-6 w-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{summary.total_courses}</p>
                <p className="text-[11px] text-slate-500 font-medium">{t("admin.activeCurricula")}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
            <CardContent className="p-5 flex items-center gap-3.5">
              <div className="h-11 w-11 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                <Award className="h-6 w-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{summary.completion_rate_percent}%</p>
                <p className="text-[11px] text-slate-500 font-medium">{t("admin.completionRate")}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
            <CardContent className="p-5 flex items-center gap-3.5">
              <div className="h-11 w-11 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center">
                <TrendingUp className="h-6 w-6" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{summary.overall_pass_rate_percent}%</p>
                <p className="text-[11px] text-slate-500 font-medium">{t("admin.passRate")}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Row 2: User Management & Course Assignment Table */}
        <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
          <CardHeader className="border-b border-slate-100 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Users className="h-4 w-4 text-[#1E3A8A]" />
                {t("admin.cadreManagement")}
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                {t("admin.cadreManagementDesc")}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="p-0 overflow-x-auto max-h-[36rem] overflow-y-auto">
            <table className="w-full text-left text-xs">
              <thead className="sticky top-0 z-10 bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="px-6 py-3">{t("admin.colOfficial")}</th>
                  <th className="px-6 py-3">{t("admin.colDeptRole")}</th>
                  <th className="px-6 py-3">{t("admin.colOnboarded")}</th>
                  <th className="px-6 py-3">{t("admin.colEnrolled")}</th>
                  <th className="px-6 py-3 text-right">{t("admin.colActions")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {usersList.map((u: any) => (
                  <tr key={u.id} className="hover:bg-slate-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <p className="font-bold text-slate-900">{u.full_name}</p>
                      <p className="text-[11px] text-slate-400">{u.email}</p>
                    </td>
                    <td className="px-6 py-4">
                      <p className="font-semibold text-slate-800">{u.designation}</p>
                      <p className="text-[11px] text-slate-500 truncate max-w-xs">{u.department}</p>
                    </td>
                    <td className="px-6 py-4">
                      {u.onboarding_completed ? (
                        <Badge variant="success" className="text-[10px] inline-flex items-center gap-1">
                          <CheckCircle2 className="h-3 w-3" /> {t("admin.completed")}
                        </Badge>
                      ) : (
                        <Badge variant="secondary" className="text-[10px]">{t("admin.pending")}</Badge>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        {u.courses.length > 0 ? (
                          u.courses.map((uc: any, idx: number) => (
                            <div key={idx} className="flex items-center gap-2 text-[11px]">
                              <span className="font-medium text-slate-800 truncate max-w-[180px]">
                                {uc.title}
                              </span>
                              <span className="text-slate-400">({uc.progress_percent}%)</span>
                            </div>
                          ))
                        ) : (
                          <span className="text-slate-400 text-[11px]">{t("admin.noActiveCourses")}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setSelectedUserId(u.id);
                          setSelectedCourseId(courseAnalytics[0]?.id || 1);
                          setAssignModalOpen(true);
                        }}
                        className="text-xs h-8 border-slate-300 text-[#1E3A8A] hover:bg-slate-50 cursor-pointer"
                      >
                        {t("admin.assignCourse")}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        {/* Row 3: Question Difficulty Analysis */}
        <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
          <CardHeader className="border-b border-slate-100 p-6">
            <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              {t("admin.questionAnalytics")}
            </CardTitle>
            <CardDescription className="text-xs text-slate-500">
              {t("admin.questionAnalyticsDesc")}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            {strugglingQuestions.length > 0 && (
              <p className="mb-3 text-xs text-slate-500 tabular-nums">
                The {Math.min(10, strugglingQuestions.length)} questions with the lowest cadre accuracy, out of {strugglingQuestions.length} analysed.
              </p>
            )}
            <div className="space-y-3">
              {strugglingQuestions.slice(0, 10).map((sq: any) => (
                <div
                  key={sq.question_id}
                  className="p-4 rounded-xl border border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                >
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                      {sq.assessment_title}
                    </span>
                    <p className="font-semibold text-slate-900 mt-0.5">{sq.question_text}</p>
                  </div>
                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-right">
                      <span className="text-sm font-bold text-slate-900">{sq.accuracy_percent}%</span>
                      <span className="text-[10px] text-slate-500 block">Cadre Accuracy</span>
                    </div>
                    <Badge
                      variant={sq.accuracy_percent < 50 ? "default" : "secondary"}
                      className="text-[10px]"
                    >
                      {sq.difficulty_tag}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Assignment Modal */}
        <Dialog open={assignModalOpen} onOpenChange={setAssignModalOpen}>
          <DialogContent className="max-w-md p-6 bg-white">
            <DialogHeader>
              <DialogTitle>Assign Course to Official</DialogTitle>
              <DialogDescription className="text-xs text-slate-500">
                Assign accredited training to an officer. The course will automatically appear in their active learning queue.
              </DialogDescription>
            </DialogHeader>

            {assignSuccess ? (
              <div className="py-6 text-center text-xs font-semibold text-emerald-800 space-y-2">
                <CheckCircle2 className="h-8 w-8 text-emerald-600 mx-auto" />
                <p>{assignSuccess}</p>
              </div>
            ) : (
              <div className="space-y-4 pt-2 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Select Official</label>
                  <select
                    value={selectedUserId || ""}
                    onChange={(e) => setSelectedUserId(parseInt(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 p-2 text-xs bg-white text-slate-900"
                  >
                    {usersList.map((u: any) => (
                      <option key={u.id} value={u.id}>
                        {u.full_name} ({u.designation || u.email})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Select Training Course</label>
                  <select
                    value={selectedCourseId || ""}
                    onChange={(e) => setSelectedCourseId(parseInt(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 p-2 text-xs bg-white text-slate-900"
                  >
                    {courseAnalytics.map((c: any) => (
                      <option key={c.id} value={c.id}>
                        {c.title} ({c.organization})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex justify-end gap-2 pt-4 border-t border-slate-100">
                  <Button variant="outline" size="sm" onClick={() => setAssignModalOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleAssignCourse}
                    disabled={assigning}
                    className="bg-[#1E3A8A] hover:bg-[#172554] text-white cursor-pointer"
                  >
                    {assigning ? "Assigning..." : "Confirm Assignment"}
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* New Course Modal */}
        <Dialog open={courseModalOpen} onOpenChange={setCourseModalOpen}>
          <DialogContent className="max-w-lg p-6 bg-white">
            <DialogHeader>
              <DialogTitle>Create New Course Curriculum</DialogTitle>
              <DialogDescription className="text-xs text-slate-500">
                Add a new course to the iGOT Karmayogi national statistical catalogue
              </DialogDescription>
            </DialogHeader>

            <form onSubmit={handleCreateCourse} className="space-y-3 pt-2 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Course Title</label>
                <Input
                  required
                  value={newCourse.title}
                  onChange={(e) => setNewCourse({ ...newCourse, title: e.target.value })}
                  placeholder="e.g. Sustainable Development Goals (SDG) Statistical Indicators"
                  className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Overview Description</label>
                <textarea
                  required
                  rows={2}
                  value={newCourse.overview}
                  onChange={(e) => setNewCourse({ ...newCourse, overview: e.target.value })}
                  placeholder="Comprehensive guide on SDG indicator tracking..."
                  className="w-full rounded-lg border border-slate-300 p-2 text-xs focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Instructor / Faculty</label>
                  <Input
                    required
                    value={newCourse.instructor}
                    onChange={(e) => setNewCourse({ ...newCourse, instructor: e.target.value })}
                    placeholder="Dr. S. K. Roy"
                    className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Accredited Body</label>
                  <Input
                    required
                    value={newCourse.organization}
                    onChange={(e) => setNewCourse({ ...newCourse, organization: e.target.value })}
                    className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Duration (Hours)</label>
                  <Input
                    type="number"
                    step="0.5"
                    value={newCourse.duration_hours}
                    onChange={(e) => setNewCourse({ ...newCourse, duration_hours: parseFloat(e.target.value) || 4 })}
                    className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Provider Source</label>
                  <select
                    value={newCourse.source}
                    onChange={(e) => setNewCourse({ ...newCourse, source: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 p-2 text-xs bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
                  >
                    <option value="internal">Internal MoSPI</option>
                    <option value="external">External (ISTM/DoPT)</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t border-slate-100">
                <Button variant="outline" size="sm" type="button" onClick={() => setCourseModalOpen(false)}>
                  Cancel
                </Button>
                <Button size="sm" type="submit" disabled={creatingCourse} className="bg-[#1E3A8A] hover:bg-[#172554] text-white cursor-pointer">
                  {creatingCourse ? "Publishing..." : "Publish Course to Catalogue"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
