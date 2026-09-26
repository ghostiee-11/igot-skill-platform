"use client";

import React, { useEffect, useState } from "react";
import {
  User,
  ShieldCheck,
  Settings,
  Award,
  CheckCircle2,
  Save,
  Languages,
  Moon,
  Sun,
  Target,
  Briefcase,
  GraduationCap,
  Building2,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthContext";
import { useI18n } from "@/lib/i18n";

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const { language, setLanguage, t } = useI18n();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const [formData, setFormData] = useState({
    full_name: "",
    phone: "",
    bio: "",
    education: "",
    work_experience_years: 0,
    prior_training: "",
    designation: "",
    department: "",
    job_role: "",
    current_assignment: "",
    areas_of_interest: [] as string[],
    language_pref: "en",
    appearance_pref: "light",
    daily_goal_minutes: 30,
  });

  useEffect(() => {
    fetchApi("/profile/")
      .then((data) => {
        setFormData({
          full_name: data.full_name || "",
          phone: data.profile.phone || "",
          bio: data.profile.bio || "",
          education: data.profile.education || "",
          work_experience_years: data.profile.work_experience_years || 0,
          prior_training: data.profile.prior_training || "",
          designation: data.profile.designation || "",
          department: data.profile.department || "",
          job_role: data.profile.job_role || "",
          current_assignment: data.profile.current_assignment || "",
          areas_of_interest: data.profile.areas_of_interest || [],
          language_pref: data.profile.language_pref || "en",
          appearance_pref: data.profile.appearance_pref || "light",
          daily_goal_minutes: data.profile.daily_goal_minutes || 30,
        });
      })
      .catch((err) => console.error("Error loading profile:", err))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSavedSuccess(false);

    try {
      await fetchApi("/profile/", {
        method: "PUT",
        body: JSON.stringify(formData),
      });

      updateUser({ full_name: formData.full_name });
      setLanguage(formData.language_pref as "en" | "hi");
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      alert("Failed to update profile: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center bg-[#F8FAFC]">
        <div className="h-8 w-8 rounded-full border-3 border-slate-200 border-t-[#1E3A8A] animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* 1. Institutional White Header */}
      <section className="bg-white border-b border-slate-200 py-8 sm:py-10">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
            <div className="flex items-center gap-5">
              <div className="h-16 w-16 rounded-2xl bg-[#1E3A8A] text-white flex items-center justify-center text-2xl font-bold shadow-sm ring-4 ring-blue-50 shrink-0">
                {formData.full_name?.charAt(0) || "U"}
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <Building2 className="h-3.5 w-3.5 text-[#1E3A8A]" />
                  <span className="text-[11px] font-bold text-[#1E3A8A] uppercase tracking-wider">
                    {t("profile.eyebrow")}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-2.5">
                  <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
                    {formData.full_name || t("profile.title")}
                  </h1>
                  <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-0.5 rounded-md bg-blue-50 text-[#1E3A8A] border border-blue-200">
                    <ShieldCheck className="h-3 w-3 text-[#1E3A8A]" />
                    {user?.role ? `${user.role.toUpperCase()} • ${t("profile.verifiedOfficial")}` : t("profile.verifiedOfficial")}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {formData.designation ? `${formData.designation} • ${formData.department}` : t("profile.subtitle")}
                </p>
              </div>
            </div>

            {savedSuccess && (
              <div className="p-3 px-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold flex items-center gap-2 shrink-0">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                {t("profile.savedSuccess")}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* 2. Main Content Canvas */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        <form onSubmit={handleSave} className="space-y-6">
          {/* Section 1: Personal & Professional Info */}
          <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-[#1E3A8A]" />
                {t("profile.officialRole")}
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                {t("profile.officialRoleDesc")}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t("profile.fullName")}
                  </label>
                  <Input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t("profile.phone")}
                  </label>
                  <Input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t("profile.designation")}
                  </label>
                  <Input
                    type="text"
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                    className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t("profile.department")}
                  </label>
                  <Input
                    type="text"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t("profile.jobRole")}
                  </label>
                  <Input
                    type="text"
                    value={formData.job_role}
                    onChange={(e) => setFormData({ ...formData, job_role: e.target.value })}
                    className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t("profile.yearsInService")}
                  </label>
                  <Input
                    type="number"
                    value={formData.work_experience_years}
                    onChange={(e) => setFormData({ ...formData, work_experience_years: parseInt(e.target.value) || 0 })}
                    className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t("profile.currentAssignment")}
                </label>
                <Input
                  type="text"
                  value={formData.current_assignment}
                  onChange={(e) => setFormData({ ...formData, current_assignment: e.target.value })}
                  className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {t("profile.qualifications")}
                </label>
                <Input
                  type="text"
                  value={formData.education}
                  onChange={(e) => setFormData({ ...formData, education: e.target.value })}
                  className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                />
              </div>
            </CardContent>
          </Card>

          {/* Section 2: Settings & Preferences */}
          <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Settings className="h-4 w-4 text-[#1E3A8A]" />
                {t("profile.preferences")}
              </CardTitle>
              <CardDescription className="text-xs text-slate-500">
                {t("profile.preferencesDesc")}
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t("profile.interfaceLanguage")}
                  </label>
                  <select
                    value={formData.language_pref}
                    onChange={(e) => setFormData({ ...formData, language_pref: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 p-2 text-xs bg-white text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
                  >
                    <option value="en">English (Official Civil Services)</option>
                    <option value="hi">हिन्दी (राजभाषा)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t("profile.dailyGoal")}
                  </label>
                  <Input
                    type="number"
                    min={10}
                    max={180}
                    value={formData.daily_goal_minutes}
                    onChange={(e) => setFormData({ ...formData, daily_goal_minutes: parseInt(e.target.value) || 30 })}
                    className="text-xs border-slate-300 focus:border-[#1E3A8A]"
                  />
                </div>
              </div>
            </CardContent>

            <CardFooter className="flex justify-end border-t border-slate-100 pt-4 pb-4">
              <Button
                type="submit"
                disabled={saving}
                className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold px-6 shadow-xs cursor-pointer"
              >
                <Save className="h-3.5 w-3.5 mr-1.5" />
                {saving ? t("profile.saving") : t("profile.saveChanges")}
              </Button>
            </CardFooter>
          </Card>
        </form>
      </div>
    </div>
  );
}
