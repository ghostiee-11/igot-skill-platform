"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Award,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  User,
  GraduationCap,
  Briefcase,
  Layers,
  Sparkles,
  ShieldCheck,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { useAuth } from "@/lib/auth/AuthContext";
import { fetchApi } from "@/lib/api";

export default function OnboardingWizardPage() {
  const router = useRouter();
  const { user, updateUser } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    phone: "",
    bio: "",
    education: "M.Sc. Statistics",
    work_experience_years: 5,
    prior_training: "Foundation Training at NSSTA",
    designation: "Senior Statistical Officer (SSO)",
    department: "Ministry of Statistics & Programme Implementation (MoSPI)",
    job_role: "Price Indices Compilation and Sample Field Audits",
    current_assignment: "Revision of Consumer Price Index (CPI) weights",
    areas_of_interest: ["Sample Survey Design", "Inflation Metrics", "Data Governance"],
    language_pref: "en",
    appearance_pref: "light",
  });

  useEffect(() => {
    if (!user) {
      router.push("/login");
      return;
    }
  }, [user, router]);

  const toggleInterest = (interest: string) => {
    setFormData((prev) => {
      const exists = prev.areas_of_interest.includes(interest);
      return {
        ...prev,
        areas_of_interest: exists
          ? prev.areas_of_interest.filter((i) => i !== interest)
          : [...prev.areas_of_interest, interest],
      };
    });
  };

  const handleSaveProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      await fetchApi("/onboarding/save", {
        method: "POST",
        body: JSON.stringify(formData),
      });

      updateUser({ onboarding_completed: true });
      router.push("/home");
    } catch (err: any) {
      setError(err.message || "Failed to save profile. Please try again.");
      setLoading(false);
    }
  };

  const stepsList = [
    { num: 1, title: "Profile Setup", icon: Sparkles },
    { num: 2, title: "Personal Info", icon: User },
    { num: 3, title: "Education & Workex", icon: GraduationCap },
    { num: 4, title: "Designation & Role", icon: Briefcase },
    { num: 5, title: "Assignments & Interests", icon: Layers },
  ];

  return (
    <div className="min-h-[90vh] bg-slate-50 py-10 px-4 sm:px-6 lg:px-8 flex flex-col items-center justify-center">
      <div className="max-w-2xl w-full space-y-8">
        {/* Wizard Header */}
        <div className="text-center">
          <div className="inline-flex h-12 w-12 rounded-xl bg-[#1E3A8A] text-white items-center justify-center mb-3 shadow-sm">
            <Award className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Civil Servant Onboarding
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Configure your official role to curate relevant statistical training modules
          </p>
        </div>

        {/* Step Progress Bar (Miro vertical subflow translated into clear numbered steps) */}
        <div className="flex items-center justify-between px-2">
          {stepsList.map((s, idx) => {
            const isCompleted = step > s.num;
            const isCurrent = step === s.num;
            const Icon = s.icon;
            return (
              <React.Fragment key={s.num}>
                <div className="flex flex-col items-center">
                  <div
                    className={`h-9 w-9 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                      isCompleted
                        ? "bg-emerald-600 text-white"
                        : isCurrent
                        ? "bg-[#1E3A8A] text-white ring-4 ring-blue-100"
                        : "bg-slate-200 text-slate-500"
                    }`}
                  >
                    {isCompleted ? <CheckCircle2 className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                  </div>
                  <span
                    className={`text-[10px] mt-1.5 font-medium hidden sm:block ${
                      isCurrent ? "text-slate-900 font-bold" : "text-slate-500"
                    }`}
                  >
                    {s.title}
                  </span>
                </div>
                {idx < stepsList.length - 1 && (
                  <div
                    className={`flex-1 h-0.5 mx-2 transition-colors ${
                      step > s.num ? "bg-emerald-600" : "bg-slate-200"
                    }`}
                  />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Wizard Card */}
        <Card className="border-slate-200 shadow-sm bg-white overflow-hidden">
          {/* Step 1: Profile Setup Intro */}
          {step === 1 && (
            <div>
              <CardHeader className="text-center pb-4">
                <CardTitle className="text-xl font-bold text-slate-900">
                  Welcome to Mission Karmayogi, {user?.full_name || "Officer"}!
                </CardTitle>
                <CardDescription className="text-xs max-w-md mx-auto mt-2 leading-relaxed">
                  As part of the Official Statistical System of India, your customized competency roadmap will adapt to your ministry, cadre seniority, and technical assignments.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 pt-2">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex items-start gap-3">
                    <ShieldCheck className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">Accredited Competency Framework</h4>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Aligned with the Capacity Building Commission (CBC) guidelines and UN-NQAF statistical standards.
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">Automated Training Record</h4>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Your assessment certificates and learning streaks directly update your institutional profile.
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-end pt-4 border-t border-slate-100">
                <Button onClick={() => setStep(2)} className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs px-6 cursor-pointer">
                  Begin Step 2: Personal Info <ArrowRight className="h-3.5 w-3.5 ml-1" />
                </Button>
              </CardFooter>
            </div>
          )}

          {/* Step 2: Personal Info */}
          {step === 2 && (
            <div>
              <CardHeader>
                <CardTitle className="text-lg font-bold text-slate-900">Step 2: Personal & Contact Details</CardTitle>
                <CardDescription className="text-xs">
                  Verify contact coordinates for certification records and official notices
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Contact Phone / WhatsApp Number
                  </label>
                  <Input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+91 98765 43210"
                    className="text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Official Bio / Summary
                  </label>
                  <textarea
                    rows={3}
                    value={formData.bio}
                    onChange={(e) => setFormData({ ...formData, bio: e.target.value })}
                    placeholder="Briefly state your statistical expertise or administrative cadre role..."
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900"
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-between pt-4 border-t border-slate-100">
                <Button variant="outline" size="sm" onClick={() => setStep(1)} className="text-xs">
                  <ArrowLeft className="h-3.5 w-3.5 mr-1" /> Previous
                </Button>
                <Button size="sm" onClick={() => setStep(3)} className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs px-5 cursor-pointer">
                  Next: Education & Workex <ArrowRight className="h-3.5 w-3.5 ml-1" />
                </Button>
              </CardFooter>
            </div>
          )}

          {/* Step 3: Education / Workex / Previous Training */}
          {step === 3 && (
            <div>
              <CardHeader>
                <CardTitle className="text-lg font-bold text-slate-900">Step 3: Education & Public Service Record</CardTitle>
                <CardDescription className="text-xs">
                  Academic qualifications and prior civil service foundational training
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Highest Educational Qualification
                  </label>
                  <Input
                    type="text"
                    value={formData.education}
                    onChange={(e) => setFormData({ ...formData, education: e.target.value })}
                    placeholder="e.g. M.Stat (ISI Kolkata) or M.A. Economics"
                    className="text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Years in Public Service / Administration
                  </label>
                  <Input
                    type="number"
                    min={0}
                    max={45}
                    value={formData.work_experience_years}
                    onChange={(e) => setFormData({ ...formData, work_experience_years: parseInt(e.target.value) || 0 })}
                    className="text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Prior Training Institutes Attended
                  </label>
                  <Input
                    type="text"
                    value={formData.prior_training}
                    onChange={(e) => setFormData({ ...formData, prior_training: e.target.value })}
                    placeholder="e.g. LBSNAA Mussoorie, NSSTA Greater Noida, ISTM Delhi"
                    className="text-xs"
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-between pt-4 border-t border-slate-100">
                <Button variant="outline" size="sm" onClick={() => setStep(2)} className="text-xs">
                  <ArrowLeft className="h-3.5 w-3.5 mr-1" /> Previous
                </Button>
                <Button size="sm" onClick={() => setStep(4)} className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs px-5 cursor-pointer">
                  Next: Designation & Cadre <ArrowRight className="h-3.5 w-3.5 ml-1" />
                </Button>
              </CardFooter>
            </div>
          )}

          {/* Step 4: Designation / Department / Job Role */}
          {step === 4 && (
            <div>
              <CardHeader>
                <CardTitle className="text-lg font-bold text-slate-900">Step 4: Designation & Ministry Details</CardTitle>
                <CardDescription className="text-xs">
                  Your current organizational placement and functional duties
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Official Designation
                  </label>
                  <Input
                    type="text"
                    value={formData.designation}
                    onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
                    placeholder="e.g. Senior Statistical Officer / Assistant Director / Inspector"
                    className="text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Department / Ministry
                  </label>
                  <select
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 p-2 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-900 bg-white"
                  >
                    <option value="Ministry of Statistics & Programme Implementation (MoSPI)">
                      Ministry of Statistics & Programme Implementation (MoSPI)
                    </option>
                    <option value="National Sample Survey Office (NSSO)">
                      National Sample Survey Office (NSSO)
                    </option>
                    <option value="Central Statistics Office (CSO)">
                      Central Statistics Office (CSO)
                    </option>
                    <option value="Department of Personnel & Training (DoPT)">
                      Department of Personnel & Training (DoPT)
                    </option>
                    <option value="Other Central Ministry / State Directorate">
                      Other Central Ministry / State Directorate
                    </option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Primary Functional Job Role
                  </label>
                  <Input
                    type="text"
                    value={formData.job_role}
                    onChange={(e) => setFormData({ ...formData, job_role: e.target.value })}
                    placeholder="e.g. Field Survey Audits / Price Index Compilation / Policy Analysis"
                    className="text-xs"
                  />
                </div>
              </CardContent>
              <CardFooter className="flex justify-between pt-4 border-t border-slate-100">
                <Button variant="outline" size="sm" onClick={() => setStep(3)} className="text-xs">
                  <ArrowLeft className="h-3.5 w-3.5 mr-1" /> Previous
                </Button>
                <Button size="sm" onClick={() => setStep(5)} className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs px-5 cursor-pointer">
                  Next: Interests & Assignments <ArrowRight className="h-3.5 w-3.5 ml-1" />
                </Button>
              </CardFooter>
            </div>
          )}

          {/* Step 5: Current Assignment / Areas of Interest -> Save Profile */}
          {step === 5 && (
            <div>
              <CardHeader>
                <CardTitle className="text-lg font-bold text-slate-900">Step 5: Current Assignment & Learning Interests</CardTitle>
                <CardDescription className="text-xs">
                  Highlight focus disciplines to tailor suggested courses on your dashboard
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {error && (
                  <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                    {error}
                  </div>
                )}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Current Active Assignment / Project
                  </label>
                  <Input
                    type="text"
                    value={formData.current_assignment}
                    onChange={(e) => setFormData({ ...formData, current_assignment: e.target.value })}
                    placeholder="e.g. All-India Household Consumption Expenditure Survey 2026"
                    className="text-xs"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-2">
                    Select Areas of Technical Interest
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {[
                      "Sample Survey Design",
                      "Inflation Metrics & CPI",
                      "National Accounts & GDP",
                      "Data Governance & UN-NQAF",
                      "Public Financial Management (PFMS)",
                      "Python & Data Science",
                      "CAPI Digital Field Operations",
                      "Administrative Law",
                    ].map((interest) => {
                      const selected = formData.areas_of_interest.includes(interest);
                      return (
                        <button
                          key={interest}
                          type="button"
                          onClick={() => toggleInterest(interest)}
                          className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors cursor-pointer inline-flex items-center gap-1 ${
                            selected
                              ? "bg-[#1E3A8A] text-white border-[#1E3A8A]"
                              : "bg-slate-50 text-slate-700 border-slate-300 hover:bg-slate-100"
                          }`}
                        >
                          <span>{interest}</span>
                          {selected && <Check className="h-3 w-3" />}
                        </button>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between pt-4 border-t border-slate-100">
                <Button variant="outline" size="sm" onClick={() => setStep(4)} className="text-xs">
                  <ArrowLeft className="h-3.5 w-3.5 mr-1" /> Previous
                </Button>
                <Button
                  size="sm"
                  onClick={handleSaveProfile}
                  disabled={loading}
                  className="bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs px-6 shadow-sm"
                >
                  {loading ? "Saving Profile..." : "Save Profile & Enter Dashboard"}
                </Button>
              </CardFooter>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
