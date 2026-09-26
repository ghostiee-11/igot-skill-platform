"use client";

import React from "react";
import Link from "next/link";
import {
  Building2,
  ShieldCheck,
  Award,
  BookOpen,
  Compass,
  ArrowRight,
  CheckCircle2,
  BarChart3,
  FileCheck2,
  Sparkles,
  GraduationCap,
  Users,
  Target,
  FileText,
  Landmark,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import { useAuth } from "@/lib/auth/AuthContext";

export default function AboutPage() {
  const { t } = useI18n();
  const { user } = useAuth();

  const stakeholders = [
    {
      name: "Ministry of Statistics & Programme Implementation (MoSPI)",
      code: "MoSPI",
      role: "Nodal Ministry",
      desc: "Apex ministry steering India's official statistical system, census planning, sample surveys, and macro-economic index compilation.",
    },
    {
      name: "Capacity Building Commission (CBC)",
      code: "CBC",
      role: "Standards Authority",
      desc: "Constitutional custodian of Mission Karmayogi, standardizing civil service competencies and role-based training across all ministries.",
    },
    {
      name: "National Statistical Systems Training Academy (NSSTA)",
      code: "NSSTA",
      role: "Core Faculty",
      desc: "Premier training institution in Greater Noida conducting foundational, in-service, and international training for the Indian Statistical Service (ISS).",
    },
    {
      name: "National Sample Survey Office (NSSO)",
      code: "NSSO",
      role: "Survey Cadre",
      desc: "Conducts multi-subject socio-economic surveys, periodic labor force surveys, and agricultural statistics across all states and UTs.",
    },
    {
      name: "Central Statistics Office (CSO)",
      code: "CSO",
      role: "Compilation Wing",
      desc: "Compiles National Accounts, Consumer Price Index (CPI), Index of Industrial Production (IIP), and national statistical standards.",
    },
    {
      name: "Institute of Secretariat Training & Management (ISTM)",
      code: "ISTM / DoPT",
      role: "Administrative Partner",
      desc: "Accredited partner delivering foundational administrative law, PFMS fiscal procedures, and central civil services conduct rules.",
    },
  ];

  const competencyPillars = [
    {
      icon: BarChart3,
      title: t("about.pillar1Title"),
      desc: t("about.pillar1Desc"),
      detail: "Deep methodologies covering multi-stage stratified sampling, Laspeyres index formulation, non-sampling error controls, and CAPI field validation.",
    },
    {
      icon: FileCheck2,
      title: t("about.pillar2Title"),
      desc: t("about.pillar2Desc"),
      detail: "Standardized national examinations with a strict 70% threshold, generating cryptographically verified SHA-256 digital certificates linked to personnel records.",
    },
    {
      icon: Sparkles,
      title: t("about.pillar3Title"),
      desc: t("about.pillar3Desc"),
      detail: "24/7 cited cadre assistant offering instant clarity on survey round schedules, central circulars, field concepts, and technical definitions.",
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
                  {t("about.cardOrg")} • {t("about.cardSub")}
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-slate-900 tracking-tight">
                {t("about.title")}
              </h1>
              <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
                {t("about.desc")}
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
                    Dashboard <ArrowRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* 2. Main Content Canvas */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-12">
        {/* Core Pillars Grid */}
        <section>
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Foundational Capacity Building Pillars
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Three pillars ensuring data integrity, institutional excellence, and modern service delivery
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {competencyPillars.map((pillar, idx) => {
              const Icon = pillar.icon;
              return (
                <Card key={idx} className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden flex flex-col justify-between">
                  <CardHeader className="pb-3">
                    <div className="h-10 w-10 rounded-xl bg-blue-50 text-[#1E3A8A] flex items-center justify-center mb-3">
                      <Icon className="h-5 w-5" />
                    </div>
                    <CardTitle className="text-base font-bold text-slate-900">
                      {pillar.title}
                    </CardTitle>
                    <CardDescription className="text-xs text-slate-600 mt-1 leading-relaxed">
                      {pillar.desc}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <p className="text-xs text-slate-500 border-t border-slate-100 pt-3 leading-relaxed">
                      {pillar.detail}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </section>

        {/* Transition from Rule-Based to Role-Based Learning */}
        <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-2xs">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-6 space-y-4">
              <div className="inline-flex items-center gap-1.5 text-[11px] font-bold text-[#1E3A8A] bg-blue-50 px-2.5 py-1 rounded-md border border-blue-200">
                <Target className="h-3.5 w-3.5" />
                Paradigm Shift: Rule to Role
              </div>
              <h3 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
                Empowering India's Cadre with Competency-Led Learning
              </h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Under Mission Karmayogi, civil servant capacity building shifts from episodic, career-milestone refresher courses to continuous, anytime-anywhere competency mastery. Every module directly connects to official duties, CAPI digital workflows, and verifiable service credentials.
              </p>
              <div className="space-y-2 pt-2 text-xs text-slate-700">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Standardized NSS sample survey and CPI price indices curriculums</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Alignment with the United Nations National Quality Assurance Framework (UN-NQAF)</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Automatic credential verification linked to Central Personnel Service Records</span>
                </div>
              </div>
            </div>

            <div className="lg:col-span-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <div className="text-[10px] font-bold text-slate-400 uppercase">Legacy Model</div>
                <h4 className="text-xs font-bold text-slate-800">Rule-Based Procedures</h4>
                <ul className="text-[11px] text-slate-500 space-y-1.5 list-disc pl-4">
                  <li>Procedural memorization</li>
                  <li>Occasional episodic training</li>
                  <li>Paper certificates without digital verification</li>
                  <li>One-size-fits-all curricula</li>
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 space-y-2">
                <div className="text-[10px] font-bold text-[#1E3A8A] uppercase">Mission Karmayogi</div>
                <h4 className="text-xs font-bold text-[#1E3A8A]">Role-Based Competencies</h4>
                <ul className="text-[11px] text-slate-700 space-y-1.5 list-disc pl-4">
                  <li>Direct functional mastery for field duties</li>
                  <li>Continuous learning on demand</li>
                  <li>Cryptographic SHA-256 digital credentials</li>
                  <li>Personalized cadre recommendations</li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* Institutional Stakeholders */}
        <section>
          <div className="mb-6">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Institutional Governance & Accreditations
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Governed under the leadership of premier central statistical bodies and capacity building authorities
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {stakeholders.map((s, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#1E3A8A] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      {s.role}
                    </span>
                    <span className="text-xs font-bold text-slate-400 font-mono">{s.code}</span>
                  </div>
                  <h3 className="text-xs font-bold text-slate-900 mt-2">{s.name}</h3>
                  <p className="text-xs text-slate-600 mt-1.5 leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Verifiable Credentials Banner */}
        <section className="hero-gradient rounded-2xl p-8 border border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-6 shadow-xs">
          <div className="space-y-2 max-w-xl">
            <div className="flex items-center gap-2 text-amber-700 text-xs font-bold uppercase tracking-wider">
              <ShieldCheck className="h-4 w-4" />
              Verified Digital Credential Standard
            </div>
            <h3 className="text-xl sm:text-2xl font-bold tracking-tight">
              70% Passing Threshold for National Accreditation
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Every course completion on iGOT Karmayogi requires passing standardized assessments evaluated by National Faculty Panels. Earned credentials include cryptographic verification hashes permanently recognized in central civil service personnel records.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 shrink-0">
            <Link href="/discover">
              <Button className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold px-5 shadow-xs cursor-pointer">
                Explore Accredited Courses
              </Button>
            </Link>
            <Link href="/help">
              <Button variant="outline" className="border-slate-300 bg-white text-slate-700 hover:bg-slate-50 text-xs font-semibold px-5 cursor-pointer">
                Credential Verification FAQ
              </Button>
            </Link>
          </div>
        </section>
      </div>
    </div>
  );
}
