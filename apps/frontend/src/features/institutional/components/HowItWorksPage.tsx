"use client";

import React from "react";
import Link from "next/link";
import {
  Building2,
  UserCheck,
  GraduationCap,
  ClipboardCheck,
  Award,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  FileCheck2,
  Compass,
  PlayCircle,
  HelpCircle,
  Clock,
  Layers,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import { useAuth } from "@/lib/auth/AuthContext";

export default function HowItWorksPage() {
  const { t } = useI18n();
  const { user } = useAuth();

  const steps = [
    {
      num: 1,
      icon: UserCheck,
      badge: "Stage 01",
      title: t("howItWorks.step1Title"),
      shortDesc: t("howItWorks.step1Desc"),
      fullExplanation:
        "Every official authenticates using their official government credentials. Through our guided 5-step onboarding wizard, you declare your parent ministry (e.g., MoSPI, NSSO, CSO), designation seniority, prior training institutes (LBSNAA, NSSTA, ISTM), and specialized functional domains. This generates a tailored competency roadmap aligned with your exact duties.",
      highlights: [
        "Government email authentication (@mospi.gov.in / @nic.in)",
        "Automated cadre mapping (ISS, SSS, Subordinate)",
        "Pre-populated departmental training prerequisites",
      ],
    },
    {
      num: 2,
      icon: GraduationCap,
      badge: "Stage 02",
      title: t("howItWorks.step2Title"),
      shortDesc: t("howItWorks.step2Desc"),
      fullExplanation:
        "Access structured, accredited curriculum authored by premier training academies including NSSTA and ISTM. Curricula feature interactive video lectures, CAPI digital survey simulations, field schedule exercises, and regulatory documentation. In-lesson concept checks test your understanding as you progress.",
      highlights: [
        "Interactive NSSTA video lectures with faculty breakdowns",
        "Tablet-based CAPI data collection simulations",
        "Self-paced learning with offline synchronizable materials",
      ],
    },
    {
      num: 3,
      icon: ClipboardCheck,
      badge: "Stage 03",
      title: t("howItWorks.step3Title"),
      shortDesc: t("howItWorks.step3Desc"),
      fullExplanation:
        "Test your statistical and operational competence through timed national assessments. Questions rigorously evaluate conceptual understanding, sampling techniques, and official standards. Instant diagnostic scoring pinpoints exact areas of mastery and provides clear regulatory citations for any review needed.",
      highlights: [
        "Strict 70% passing threshold for accredited credentials",
        "Comprehensive question-by-question regulatory feedback",
        "Unlimited attempts permitted with best score retained",
      ],
    },
    {
      num: 4,
      icon: Award,
      badge: "Stage 04",
      title: t("howItWorks.step4Title"),
      shortDesc: t("howItWorks.step4Desc"),
      fullExplanation:
        "Upon achieving 70% or higher, the system instantly generates an official, cryptographically verifiable Certificate of Competency. Each credential features a unique certificate identifier, recipient details, and a SHA-256 verification hash permanently linked to your official civil service record.",
      highlights: [
        "Tamper-proof SHA-256 verification hash",
        "Printable and downloadable high-resolution certificate PDF",
        "Automatic sync with central ministry personnel training records",
      ],
    },
  ];

  const faqs = [
    {
      q: "Can I pause and resume a course at any time?",
      a: "Yes. All progress is automatically saved to your official learning ledger after each completed lesson or activity. You can resume seamlessly across devices.",
    },
    {
      q: "What happens if I score below the 70% passing threshold on an assessment?",
      a: "Under the capacity-building policy, unlimited re-attempts are permitted. The system provides detailed question analysis highlighting the regulatory concepts you need to review before re-taking.",
    },
    {
      q: "How does my department admin track my progress?",
      a: "Department Administrators have access to the Administrative Supervisory Console (/admin) which displays active enrollments, module completion rates, and acquired certifications across their cadre.",
    },
    {
      q: "Are credentials recognized across different central ministries?",
      a: "Yes. iGOT Karmayogi certifications are accredited under Capacity Building Commission (CBC) standards and recognized across all central ministries and state directorates.",
    },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* 1. Institutional White Header Banner */}
      <section className="bg-white border-b border-slate-200 py-8 sm:py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="max-w-3xl">
              <div className="flex items-center gap-2 mb-2">
                <Building2 className="h-4 w-4 text-[#1E3A8A]" />
                <span className="text-[11px] font-bold text-[#1E3A8A] uppercase tracking-wider">
                  Official Learning Methodology • Capacity Building Commission
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-slate-900 tracking-tight">
                {t("howItWorks.title")}
              </h1>
              <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
                {t("howItWorks.subtitle")}
              </p>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <Link href="/discover">
                <Button
                  size="sm"
                  className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold px-4 shadow-xs cursor-pointer"
                >
                  <Compass className="h-4 w-4 mr-1.5" /> {t("hero.explore")}
                </Button>
              </Link>
              {user && (
                <Link href="/home">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-semibold px-4 cursor-pointer"
                  >
                    My Dashboard <ArrowRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 2. Main Content Canvas */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
        {/* 4 Steps Detailed Breakdown */}
        <section className="space-y-6">
          <div className="mb-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Structured 4-Stage Capacity Building Path
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              From authentication to recognized national certification
            </p>
          </div>

          <div className="space-y-6">
            {steps.map((step) => {
              const Icon = step.icon;
              return (
                <Card
                  key={step.num}
                  className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden"
                >
                  <div className="p-6 sm:p-8">
                    <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-6">
                      <div className="flex items-start gap-4">
                        <div className="h-12 w-12 rounded-xl bg-blue-50 text-[#1E3A8A] flex items-center justify-center shrink-0 font-bold text-lg border border-blue-200">
                          {step.num}
                        </div>
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-[#1E3A8A] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                            {step.badge}
                          </span>
                          <h3 className="text-lg font-bold text-slate-900 mt-1">
                            {step.title}
                          </h3>
                          <p className="text-xs font-medium text-slate-500">
                            {step.shortDesc}
                          </p>
                        </div>
                      </div>

                      <div className="lg:w-7/12 space-y-4">
                        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                          {step.fullExplanation}
                        </p>
                        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 space-y-2">
                          <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wide block">
                            Key Standard Operations
                          </span>
                          <div className="space-y-1.5">
                            {step.highlights.map((h, i) => (
                              <div key={i} className="flex items-center gap-2 text-xs text-slate-600">
                                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                                <span>{h}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </section>

        {/* Process Guarantee & Standards Banner */}
        <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-2xs">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center divide-y md:divide-y-0 md:divide-x divide-slate-100">
            <div className="pt-4 md:pt-0 md:px-4 space-y-2">
              <div className="h-10 w-10 rounded-full bg-blue-50 text-[#1E3A8A] flex items-center justify-center mx-auto">
                <Clock className="h-5 w-5" />
              </div>
              <h4 className="text-sm font-bold text-slate-900">Self-Paced Continuity</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Resume active coursework anywhere, anytime. Progress syncs immediately to official personnel records.
              </p>
            </div>

            <div className="pt-4 md:pt-0 md:px-4 space-y-2">
              <div className="h-10 w-10 rounded-full bg-amber-50 text-amber-700 flex items-center justify-center mx-auto">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <h4 className="text-sm font-bold text-slate-900">70% Standard of Excellence</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Guarantees rigorous mastery of official statistics, sampling methodologies, and regulatory frameworks.
              </p>
            </div>

            <div className="pt-4 md:pt-0 md:px-4 space-y-2">
              <div className="h-10 w-10 rounded-full bg-emerald-50 text-emerald-700 flex items-center justify-center mx-auto">
                <FileCheck2 className="h-5 w-5" />
              </div>
              <h4 className="text-sm font-bold text-slate-900">Cryptographic Verification</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Tamper-proof digital credentials verified with SHA-256 hashes recognized across the civil services.
              </p>
            </div>
          </div>
        </section>

        {/* Frequently Asked Questions */}
        <section>
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Learning Process FAQ
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Clear answers to common questions regarding assessments, certification, and cadre tracking
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs space-y-2"
              >
                <div className="flex items-start gap-2.5">
                  <HelpCircle className="h-4 w-4 text-[#1E3A8A] shrink-0 mt-0.5" />
                  <h3 className="text-xs font-bold text-slate-900">{faq.q}</h3>
                </div>
                <p className="text-xs text-slate-600 pl-6.5 leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Closing Action Banner */}
        <section className="hero-gradient rounded-2xl p-8 border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-xs">
          <div className="space-y-1.5 max-w-xl">
            <h3 className="text-xl font-bold tracking-tight">
              Ready to begin your Karmayogi competency journey?
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Explore accredited foundational courses in National Sample Surveys, Consumer Price Index, and Public Financial Management today.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link href="/discover">
              <Button className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold px-5 shadow-xs cursor-pointer">
                Explore Course Catalogue
              </Button>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
