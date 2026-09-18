"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Building2,
  HelpCircle,
  Sparkles,
  Phone,
  Mail,
  Clock,
  MapPin,
  ShieldCheck,
  Award,
  Send,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  FileQuestion,
  MessageSquare,
  Compass,
  ArrowRight,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/lib/i18n";
import { useAuth } from "@/lib/auth/AuthContext";

export default function HelpPage() {
  const { t } = useI18n();
  const { user } = useAuth();

  const [expandedFaq, setExpandedFaq] = useState<number | null>(0);
  const [ticketForm, setTicketForm] = useState({
    name: user?.full_name || "",
    email: user?.email || "",
    department: "",
    category: "Technical Support",
    subject: "",
    message: "",
  });
  const [ticketSubmitted, setTicketSubmitted] = useState<string | null>(null);
  const [submittingTicket, setSubmittingTicket] = useState(false);

  const faqs = [
    {
      q: t("help.faq1Q"),
      a: "Every certificate issued on iGOT Karmayogi contains a verifiable, tamper-proof SHA-256 hash. Departmental administrators and vigilance officers can verify any credential by searching the certificate ID at the public registry or inspecting the encrypted digital signature.",
    },
    {
      q: t("help.faq2Q"),
      a: "All MoSPI and CBC accredited certifications require a minimum 70% passing score on the final timed evaluation. Learners who do not meet the threshold on their first attempt may retake the assessment with unlimited attempts permitted under Phase 0 guidelines.",
    },
    {
      q: "How do I update my ministry designation if transferred?",
      a: "You can update your designation, department, and active assignments at any time via your Official Profile (/profile). Updates immediately sync with your cadre's Administrative Supervisory Console.",
    },
    {
      q: "Are CAPI field survey operations supported offline?",
      a: "Yes. CAPI digital modules and handbook references can be pre-cached on Android tablets. Once a network connection is established, geo-tagged survey entries and validation checks automatically synchronize with central servers.",
    },
    {
      q: "How does my training record link to my Central Civil Service Service Book?",
      a: "Under the National Programme for Civil Services Capacity Building (NPCSCB), accredited module hours and certified competencies are transmitted to the Department of Personnel & Training (DoPT) digital repository for annual cadre reviews.",
    },
  ];

  const handleLaunchAiAssistant = () => {
    // Open the bottom AI assistant widget
    const aiWidgetButton = document.querySelector("#karmayogi-ai-assistant-toggle") as HTMLButtonElement | null;
    if (aiWidgetButton) {
      aiWidgetButton.click();
    } else {
      alert("AI Assistant ready: Use the floating blue Support Desk icon in the bottom-right corner.");
    }
  };

  const handleTicketSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingTicket(true);
    setTimeout(() => {
      const ticketId = `KARM-TKT-2026-${Math.floor(1000 + Math.random() * 9000)}`;
      setTicketSubmitted(ticketId);
      setSubmittingTicket(false);
    }, 1000);
  };

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
                  Central Assistance & Training Desk • Capacity Building Commission
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-slate-900 tracking-tight">
                {t("help.title")}
              </h1>
              <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
                {t("help.subtitle")}
              </p>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <Link href="/discover">
                <Button
                  size="sm"
                  className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold px-4 shadow-xs cursor-pointer"
                >
                  <Compass className="h-4 w-4 mr-1.5" /> {t("resources.browseCatalog")}
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
        {/* Support Channels 3 Cards Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1: 24/7 AI Assistant */}
          <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden flex flex-col justify-between">
            <CardHeader className="pb-3">
              <div className="h-10 w-10 rounded-xl bg-blue-50 text-[#1E3A8A] flex items-center justify-center mb-3">
                <Sparkles className="h-5 w-5" />
              </div>
              <CardTitle className="text-base font-bold text-slate-900">
                {t("help.aiTitle")}
              </CardTitle>
              <CardDescription className="text-xs text-slate-600 mt-1 leading-relaxed">
                {t("help.aiDesc")}
              </CardDescription>
            </CardHeader>
            <CardFooter className="pt-2 pb-5 border-t border-slate-100 flex flex-col items-start gap-3">
              <span className="text-[11px] text-slate-500">Available 24/7 • Direct citations</span>
              <Button
                size="sm"
                onClick={handleLaunchAiAssistant}
                className="w-full bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold cursor-pointer shadow-xs"
              >
                <Sparkles className="h-3.5 w-3.5 mr-1.5" /> {t("help.aiLaunch")}
              </Button>
            </CardFooter>
          </Card>

          {/* Card 2: Central Training Division Desk */}
          <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden flex flex-col justify-between">
            <CardHeader className="pb-3">
              <div className="h-10 w-10 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center mb-3">
                <Phone className="h-5 w-5" />
              </div>
              <CardTitle className="text-base font-bold text-slate-900">
                {t("help.deskTitle")}
              </CardTitle>
              <CardDescription className="text-xs text-slate-600 mt-1 leading-relaxed">
                {t("help.deskDesc")}
              </CardDescription>
            </CardHeader>
            <CardContent className="py-0 space-y-2 text-xs text-slate-600">
              <div className="flex items-center gap-2">
                <Clock className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span>{t("help.hours")}</span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span className="font-mono text-[11px]">training-desk@mospi.gov.in</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span>Sardar Patel Bhawan, Sansad Marg, New Delhi</span>
              </div>
            </CardContent>
            <CardFooter className="pt-3 pb-5 border-t border-slate-100">
              <span className="text-[11px] font-semibold text-slate-500">Tel: +91 11 2338 2145</span>
            </CardFooter>
          </Card>

          {/* Card 3: Nodal Cadre Coordination */}
          <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden flex flex-col justify-between">
            <CardHeader className="pb-3">
              <div className="h-10 w-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center mb-3">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <CardTitle className="text-base font-bold text-slate-900">
                Nodal Cadre Coordinators
              </CardTitle>
              <CardDescription className="text-xs text-slate-600 mt-1 leading-relaxed">
                Designated ISS and SSS cadre nodal officers in participating ministries for official batch nominations and clearance.
              </CardDescription>
            </CardHeader>
            <CardContent className="py-0 space-y-2 text-xs text-slate-600">
              <p className="text-slate-500">
                For department approvals, cadre seniority updates, or inter-ministerial transfers, consult your assigned department nodal officer.
              </p>
            </CardContent>
            <CardFooter className="pt-3 pb-5 border-t border-slate-100">
              <Link href="/profile" className="text-xs font-semibold text-[#1E3A8A] hover:underline">
                View Your Profile & Cadre Data →
              </Link>
            </CardFooter>
          </Card>
        </section>

        {/* Two-Column Grid: Left FAQ Accordion (7 cols) and Right Official Inquiry Form (5 cols) */}
        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: FAQs */}
          <div className="lg:col-span-7 space-y-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">
                {t("help.faqTitle")}
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Official rules regarding certification, scoring standards, and technical access
              </p>
            </div>

            <div className="space-y-3">
              {faqs.map((faq, idx) => {
                const isOpen = expandedFaq === idx;
                return (
                  <div
                    key={idx}
                    className="bg-white rounded-xl border border-slate-200 shadow-2xs overflow-hidden"
                  >
                    <button
                      type="button"
                      onClick={() => setExpandedFaq(isOpen ? null : idx)}
                      className="w-full p-4 text-left flex items-center justify-between gap-3 text-xs font-bold text-slate-900 hover:bg-slate-50/70 transition-colors cursor-pointer"
                    >
                      <span className="flex items-center gap-2">
                        <FileQuestion className="h-4 w-4 text-[#1E3A8A] shrink-0" />
                        {faq.q}
                      </span>
                      {isOpen ? (
                        <ChevronUp className="h-4 w-4 text-slate-400 shrink-0" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-slate-400 shrink-0" />
                      )}
                    </button>

                    {isOpen && (
                      <div className="px-4 pb-4 pt-1 text-xs text-slate-600 leading-relaxed border-t border-slate-100 bg-slate-50/40">
                        {faq.a}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Official Inquiry Ticket Form */}
          <div className="lg:col-span-5">
            <Card className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden">
              <CardHeader className="pb-3 border-b border-slate-100">
                <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-[#1E3A8A]" />
                  Submit Cadre Support Request
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Transmitted directly to the Central Training Division helpdesk
                </CardDescription>
              </CardHeader>

              <CardContent className="p-5 space-y-4">
                {ticketSubmitted ? (
                  <div className="py-6 text-center space-y-3">
                    <div className="h-12 w-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
                      <CheckCircle2 className="h-6 w-6" />
                    </div>
                    <h4 className="text-sm font-bold text-slate-900">Support Request Dispatched</h4>
                    <p className="text-xs text-slate-600">
                      Your ticket has been recorded with tracking ID:
                    </p>
                    <span className="inline-block px-3 py-1 rounded-md bg-slate-100 font-mono text-xs font-bold text-[#1E3A8A]">
                      {ticketSubmitted}
                    </span>
                    <p className="text-[11px] text-slate-500">
                      A training division representative will follow up via your official email.
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setTicketSubmitted(null)}
                      className="text-xs mt-2"
                    >
                      Submit Another Query
                    </Button>
                  </div>
                ) : (
                  <form onSubmit={handleTicketSubmit} className="space-y-3 text-xs">
                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Officer Name
                      </label>
                      <Input
                        required
                        value={ticketForm.name}
                        onChange={(e) => setTicketForm({ ...ticketForm, name: e.target.value })}
                        placeholder="Dr. S. K. Sharma"
                        className="text-xs"
                      />
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Government Email
                      </label>
                      <Input
                        type="email"
                        required
                        value={ticketForm.email}
                        onChange={(e) => setTicketForm({ ...ticketForm, email: e.target.value })}
                        placeholder="officer@mospi.gov.in"
                        className="text-xs"
                      />
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Ministry / Department
                      </label>
                      <Input
                        required
                        value={ticketForm.department}
                        onChange={(e) => setTicketForm({ ...ticketForm, department: e.target.value })}
                        placeholder="MoSPI / NSSO / CSO"
                        className="text-xs"
                      />
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Inquiry Category
                      </label>
                      <select
                        value={ticketForm.category}
                        onChange={(e) => setTicketForm({ ...ticketForm, category: e.target.value })}
                        className="w-full rounded-lg border border-slate-300 p-2 text-xs bg-white text-slate-900"
                      >
                        <option value="Course Enrollment & Access">Course Enrollment & Access</option>
                        <option value="Assessment & Scoring Review">Assessment & Scoring Review</option>
                        <option value="Certificate Hash Verification">Certificate Hash Verification</option>
                        <option value="CAPI Field Sync Issue">CAPI Field Sync Issue</option>
                        <option value="Cadre Designation Update">Cadre Designation Update</option>
                      </select>
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Subject
                      </label>
                      <Input
                        required
                        value={ticketForm.subject}
                        onChange={(e) => setTicketForm({ ...ticketForm, subject: e.target.value })}
                        placeholder="e.g. Assessment Retake Confirmation"
                        className="text-xs"
                      />
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Detailed Description
                      </label>
                      <textarea
                        required
                        rows={3}
                        value={ticketForm.message}
                        onChange={(e) => setTicketForm({ ...ticketForm, message: e.target.value })}
                        placeholder="Provide relevant course code, date of assessment, or specific question context..."
                        className="w-full rounded-lg border border-slate-300 p-2 text-xs focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]"
                      />
                    </div>

                    <Button
                      type="submit"
                      disabled={submittingTicket}
                      className="w-full bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold gap-1.5 shadow-xs cursor-pointer"
                    >
                      <Send className="h-3.5 w-3.5" />
                      {submittingTicket ? "Transmitting Query..." : "Submit Support Request"}
                    </Button>
                  </form>
                )}
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </div>
  );
}
