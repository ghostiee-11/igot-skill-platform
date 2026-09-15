"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import {
  Compass,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  BarChart3,
  FileCheck2,
  Sparkles,
  UserCheck,
  GraduationCap,
  ClipboardCheck,
  Award,
  HelpCircle,
  FileText,
  Download,
  PhoneCall,
  Mail,
  CheckCircle2,
  Clock,
  Building2,
  Shield,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth/AuthContext";
import { useI18n } from "@/lib/i18n";
import { useRouter } from "next/navigation";

export default function EntryLandingPage() {
  const { user } = useAuth();
  const router = useRouter();
  const { t, language } = useI18n();

  const heroSlides = useMemo(
    () => [
      {
        src: "/karmayogi.jpg",
        alt: language === "hi" ? "मिशन कर्मयोगी राष्ट्रीय क्षमता निर्माण" : "Mission Karmayogi civil service capacity building session",
        title: t("hero.slide1"),
      },
      {
        src: "/government-meeting.jpg",
        alt: language === "hi" ? "प्रशासनिक संवर्ग समीक्षा एवं नीति समन्वय" : "Government administrative cadre review and collaborative meeting",
        title: t("hero.slide2"),
      },
      {
        src: "/ai-daksh.jpg",
        alt: language === "hi" ? "एआई-दक्ष आधिकारिक सांख्यिकी एवं विश्लेषणात्मक उपकरण" : "AI-Daksh civil service intelligence and analytical tools",
        title: t("hero.slide3"),
      },
    ],
    [t, language]
  );

  const [currentSlide, setCurrentSlide] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (user) router.push("/home");
  }, [user, router]);

  useEffect(() => {
    if (typeof window !== "undefined" && window.location.hash) {
      const id = window.location.hash.replace("#", "");
      const el = document.getElementById(id);
      if (el) {
        const timer = setTimeout(() => {
          const header = document.querySelector("header");
          const headerHeight = header ? Math.round(header.getBoundingClientRect().height) : 68;
          const targetTop = Math.round(el.getBoundingClientRect().top + window.scrollY - headerHeight);
          window.scrollTo({ top: Math.max(0, targetTop), behavior: "smooth" });
        }, 120);
        return () => clearTimeout(timer);
      }
    }
  }, []);

  useEffect(() => {
    if (isPaused) return;
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % heroSlides.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [isPaused, heroSlides.length]);

  const handlePrev = useCallback(() => {
    setCurrentSlide((prev) => (prev - 1 + heroSlides.length) % heroSlides.length);
  }, [heroSlides.length]);

  const handleNext = useCallback(() => {
    setCurrentSlide((prev) => (prev + 1) % heroSlides.length);
  }, [heroSlides.length]);

  return (
    <div className="flex flex-col w-full text-slate-900">

      {/* ════════════════════════════════════════════════
          1. HERO — Dark Navy Gradient with Mesh Grid
          ════════════════════════════════════════════════ */}
      <section
        id="hero"
        className="landing-hero scroll-mt-16 sm:scroll-mt-[68px] min-h-0 lg:min-h-[calc(100vh-68px)] flex flex-col justify-center hero-gradient hero-mesh py-8 sm:py-16 relative overflow-hidden"
      >
        {/* Radial glow orb — top-left */}
        <div className="absolute -top-24 -left-24 w-[280px] sm:w-[480px] h-[280px] sm:h-[480px] max-w-full rounded-full bg-[#1E3A8A]/30 blur-[100px] pointer-events-none" />
        {/* Radial glow orb — bottom-right */}
        <div className="absolute -bottom-24 -right-12 w-[240px] sm:w-[360px] h-[240px] sm:h-[360px] max-w-full rounded-full bg-[#0D9488]/20 blur-[80px] pointer-events-none" />

        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full relative z-10">
          {/* Two-Column Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">

            {/* Left Column */}
            <div className="lg:col-span-7 flex flex-col justify-start text-left animate-fade-in-up">
              {/* Eyebrow */}
              <div className="flex items-center gap-2 mb-4 sm:mb-5">
                <div className="flex items-center gap-2 glass-light rounded-full px-3 py-1.5">
                  <Building2 className="h-3.5 w-3.5 text-teal-300" />
                  <span className="text-[10px] sm:text-[11px] font-bold text-white/80 uppercase tracking-widest">
                    MoSPI • Capacity Building Commission
                  </span>
                </div>
              </div>

              {/* Headline */}
              <h1 className="text-2xl sm:text-4xl lg:text-[44px] font-extrabold tracking-tight text-white leading-[1.15] sm:leading-[1.1]">
                {t("hero.title")}
              </h1>

              {/* Subtitle */}
              <p className="mt-4 sm:mt-5 text-sm sm:text-lg text-white/70 font-normal leading-relaxed max-w-xl animate-fade-in-up-delay-1">
                {t("hero.subtitle")}
              </p>

              {/* CTAs */}
              <div className="mt-6 sm:mt-8 flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-3.5 animate-fade-in-up-delay-2">
                <a href="/login" className="w-full sm:w-auto">
                  <Button
                    size="lg"
                    className="w-full sm:w-auto h-12 px-7 rounded-xl bg-white hover:bg-slate-50 text-[#1E3A8A] font-bold text-sm shadow-lg transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer border-0 hover:scale-105"
                  >
                    {t("hero.signIn")} <ArrowRight className="h-4 w-4" />
                  </Button>
                </a>
                <a href="/discover" className="w-full sm:w-auto">
                  <Button
                    size="lg"
                    className="w-full sm:w-auto h-12 px-7 rounded-xl glass-light hover:bg-white/20 text-white font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2 cursor-pointer border border-white/30 hover:border-white/50"
                  >
                    <Compass className="h-4 w-4 text-teal-300" /> {t("hero.explore")}
                  </Button>
                </a>
              </div>

              {/* Trust badges */}
              <div className="mt-6 sm:mt-8 pt-4 sm:pt-5 border-t border-white/10 flex flex-wrap items-center gap-x-5 sm:gap-x-6 gap-y-2 animate-fade-in-up-delay-3">
                <span className="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs text-white/60 font-medium">
                  <CheckCircle2 className="h-3.5 sm:h-4 w-3.5 sm:w-4 text-teal-400 shrink-0" /> {t("hero.badgeMospi")}
                </span>
                <span className="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs text-white/60 font-medium">
                  <Shield className="h-3.5 sm:h-4 w-3.5 sm:w-4 text-amber-400 shrink-0" /> {t("hero.badgeCbc")}
                </span>
                <span className="flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs text-white/60 font-medium">
                  <Award className="h-3.5 sm:h-4 w-3.5 sm:w-4 text-teal-400 shrink-0" /> {t("hero.badgeIso")}
                </span>
              </div>
            </div>

            {/* Right Column: Carousel */}
            <div className="lg:col-span-5 w-full flex flex-col items-end animate-fade-in-up-delay-1">
              <div className="w-full">
                <div
                  className="keep-on-dark relative w-full h-[200px] xs:h-[230px] sm:h-[270px] rounded-2xl overflow-hidden group"
                  style={{ boxShadow: "0 25px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.1)" }}
                  onMouseEnter={() => setIsPaused(true)}
                  onMouseLeave={() => setIsPaused(false)}
                >
                  {heroSlides.map((slide, idx) => (
                    <div
                      key={slide.src}
                      className={`absolute inset-0 flex items-center justify-center transition-opacity duration-700 ease-in-out ${
                        idx === currentSlide ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
                      }`}
                    >
                      <img
                        src={slide.src}
                        alt={slide.alt}
                        className="w-full h-full object-cover block select-none"
                        loading={idx === 0 ? "eager" : "lazy"}
                      />
                      {/* Slide gradient overlay */}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
                      {/* Slide title */}
                      <div className="absolute bottom-3 left-4 right-4">
                        <p className="text-white text-xs font-semibold drop-shadow-md line-clamp-1">
                          {slide.title}
                        </p>
                      </div>
                    </div>
                  ))}

                  {/* Prev/Next */}
                  <button type="button" onClick={handlePrev} aria-label="Previous slide"
                    className="absolute left-3 top-1/2 -translate-y-1/2 z-20 h-8 w-8 rounded-full glass-light text-white flex items-center justify-center transition-all opacity-0 group-hover:opacity-100 cursor-pointer hover:bg-white/20">
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <button type="button" onClick={handleNext} aria-label="Next slide"
                    className="absolute right-3 top-1/2 -translate-y-1/2 z-20 h-8 w-8 rounded-full glass-light text-white flex items-center justify-center transition-all opacity-0 group-hover:opacity-100 cursor-pointer hover:bg-white/20">
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>

                {/* Dot controls */}
                <div className="mt-3 flex items-center justify-center gap-1.5">
                  {heroSlides.map((_, idx) => (
                    <button
                      key={idx} type="button"
                      onClick={() => setCurrentSlide(idx)}
                      aria-label={`Slide ${idx + 1}`}
                      className={`transition-all duration-300 rounded-full cursor-pointer ${
                        idx === currentSlide ? "w-5 h-1.5 bg-teal-400" : "w-1.5 h-1.5 bg-white/30 hover:bg-white/50"
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* ── Statistics Bar (frosted glass inside hero) ── */}
          <div className="mt-12 sm:mt-14">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
              {[
                { num: t("stats.trainedCount"), label: t("stats.trainedLabel"), sub: t("stats.trainedSub"), accent: "text-teal-400" },
                { num: t("stats.modulesCount"), label: t("stats.modulesLabel"), sub: t("stats.modulesSub"), accent: "text-amber-400" },
                { num: t("stats.qualityCount"), label: t("stats.qualityLabel"), sub: t("stats.qualitySub"), accent: "text-teal-400" },
                { num: t("stats.certCount"), label: t("stats.certLabel"), sub: t("stats.certSub"), accent: "text-amber-400" },
              ].map((s, i) => (
                <div key={i} className="glass-card rounded-xl px-4 py-4 sm:px-5 sm:py-5">
                  <p className={`text-2xl sm:text-3xl font-extrabold tracking-tight ${s.accent}`}>{s.num}</p>
                  <p className="text-xs sm:text-sm font-semibold text-white/90 mt-0.5">{s.label}</p>
                  <p className="text-[11px] text-white/45 mt-0.5">{s.sub}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════
          2. ABOUT — Warm White → Slate Gradient
          ════════════════════════════════════════════════ */}
      <section
        id="about"
        className="scroll-mt-16 sm:scroll-mt-[68px] min-h-0 lg:min-h-[calc(100vh-68px)] flex flex-col justify-center bg-gradient-to-b from-white to-slate-50 border-b border-slate-200 py-12 sm:py-16"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-14 items-center">

            {/* Left: Institutional Card with left accent */}
            <div className="lg:col-span-5">
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                {/* Colored top stripe */}
                <div className="h-1 w-full navy-teal-gradient" />
                <div className="p-6">
                  <div className="flex items-center gap-3 mb-5">
                    <div className="h-10 w-10 rounded-xl navy-teal-gradient flex items-center justify-center shadow-sm">
                      <Building2 className="h-5 w-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-slate-900">{t("about.cardOrg")}</h3>
                      <p className="text-xs text-slate-500">{t("about.cardSub")}</p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {[
                      { title: t("about.item1Title"), desc: t("about.item1Desc"), color: "border-l-[#1E3A8A] bg-blue-50/60" },
                      { title: t("about.item2Title"), desc: t("about.item2Desc"), color: "border-l-[#0D9488] bg-teal-50/60" },
                      { title: t("about.item3Title"), desc: t("about.item3Desc"), color: "border-l-amber-500 bg-amber-50/40" },
                    ].map((item, i) => (
                      <div key={i} className={`pl-4 pr-3 py-3 rounded-r-lg border-l-2 ${item.color}`}>
                        <span className="font-semibold text-slate-900 block text-xs">{item.title}</span>
                        <span className="text-slate-500 mt-0.5 block text-[11px] leading-relaxed">{item.desc}</span>
                      </div>
                    ))}
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                    <span className="font-mono">MoSPI • CSO • NSSO • NSSTA</span>
                    <span className="font-medium text-slate-600 text-[11px]">{t("hero.badgeIso")}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Pillars */}
            <div className="lg:col-span-7">
              <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
                {t("about.title")}
              </h2>
              <p className="mt-4 text-slate-600 text-sm sm:text-base leading-relaxed">
                {t("about.desc")}
              </p>

              <div className="mt-8 space-y-4">
                {[
                  {
                    icon: BarChart3,
                    title: t("about.pillar1Title"),
                    desc: t("about.pillar1Desc"),
                    bg: "bg-[#1E3A8A]",
                    border: "border-blue-200/60",
                    ring: "ring-1 ring-blue-100",
                  },
                  {
                    icon: FileCheck2,
                    title: t("about.pillar2Title"),
                    desc: t("about.pillar2Desc"),
                    bg: "bg-[#0D9488]",
                    border: "border-teal-200/60",
                    ring: "ring-1 ring-teal-100",
                  },
                  {
                    icon: Sparkles,
                    title: t("about.pillar3Title"),
                    desc: t("about.pillar3Desc"),
                    bg: "bg-[#B45309]",
                    border: "border-amber-200/60",
                    ring: "ring-1 ring-amber-100",
                  },
                ].map((p, i) => {
                  const Icon = p.icon;
                  return (
                    <div key={i} className={`flex items-start gap-4 p-4 rounded-xl border bg-white card-hover-lift ${p.border} ${p.ring}`}>
                      <div className={`h-10 w-10 rounded-xl ${p.bg} flex items-center justify-center shrink-0`}>
                        <Icon className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-900">{p.title}</h3>
                        <p className="text-xs text-slate-600 mt-1 leading-relaxed">{p.desc}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════
          3. HOW IT WORKS — Timeline Steps
          ════════════════════════════════════════════════ */}
      <section
        id="how-it-works"
        className="scroll-mt-16 sm:scroll-mt-[68px] min-h-0 lg:min-h-[calc(100vh-68px)] flex flex-col justify-center bg-white border-b border-slate-200 py-12 sm:py-16"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {t("howItWorks.title")}
            </h2>
            <p className="mt-3 text-slate-500 text-sm sm:text-base leading-relaxed">
              {t("howItWorks.subtitle")}
            </p>
          </div>

          {/* Desktop: Horizontal timeline with connecting line */}
          <div className="hidden md:block relative">
            {/* Connecting gradient line */}
            <div className="absolute top-9 left-[12.5%] right-[12.5%] h-0.5 bg-gradient-to-r from-[#1E3A8A] via-[#0D9488] to-[#EAB308]" />

            <div className="grid grid-cols-4 gap-6">
              {[
                { num: "01", icon: UserCheck,       title: t("howItWorks.step1Title"), desc: t("howItWorks.step1Desc"), ring: "ring-[#1E3A8A]", bg: "bg-[#1E3A8A]",  numColor: "text-[#1E3A8A]" },
                { num: "02", icon: GraduationCap,   title: t("howItWorks.step2Title"), desc: t("howItWorks.step2Desc"), ring: "ring-[#0D9488]", bg: "bg-[#0D9488]",  numColor: "text-[#0D9488]" },
                { num: "03", icon: ClipboardCheck,  title: t("howItWorks.step3Title"), desc: t("howItWorks.step3Desc"), ring: "ring-amber-500",  bg: "bg-amber-500",  numColor: "text-amber-600" },
                { num: "04", icon: Award,            title: t("howItWorks.step4Title"), desc: t("howItWorks.step4Desc"), ring: "ring-[#B45309]", bg: "bg-[#B45309]",  numColor: "text-[#B45309]" },
              ].map((step, i) => {
                const Icon = step.icon;
                return (
                  <div key={i} className="flex flex-col items-center text-center group">
                    {/* Step icon circle */}
                    <div className={`relative z-10 h-[72px] w-[72px] rounded-full ${step.bg} flex items-center justify-center shadow-md ring-4 ring-white mb-5 group-hover:scale-105 transition-transform duration-200`}>
                      <Icon className="h-8 w-8 text-white" />
                    </div>
                    <span className={`text-[10px] font-black uppercase tracking-widest ${step.numColor} mb-1.5`}>{step.num}</span>
                    <h3 className="font-bold text-slate-900 text-sm mb-2">{step.title}</h3>
                    <p className="text-xs text-slate-500 leading-relaxed">{step.desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Mobile: Vertical stacked */}
          <div className="md:hidden space-y-5">
            {[
              { num: "01", icon: UserCheck,       title: t("howItWorks.step1Title"), desc: t("howItWorks.step1Desc"), bg: "bg-[#1E3A8A]" },
              { num: "02", icon: GraduationCap,   title: t("howItWorks.step2Title"), desc: t("howItWorks.step2Desc"), bg: "bg-[#0D9488]" },
              { num: "03", icon: ClipboardCheck,  title: t("howItWorks.step3Title"), desc: t("howItWorks.step3Desc"), bg: "bg-amber-500" },
              { num: "04", icon: Award,            title: t("howItWorks.step4Title"), desc: t("howItWorks.step4Desc"), bg: "bg-[#B45309]" },
            ].map((step, i) => {
              const Icon = step.icon;
              return (
                <div key={i} className="flex items-start gap-4 p-5 rounded-2xl border border-slate-200 bg-white card-hover-lift">
                  <div className={`h-12 w-12 rounded-xl ${step.bg} flex items-center justify-center shrink-0`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">{step.num}</span>
                    <h3 className="font-bold text-slate-900 text-sm mt-0.5">{step.title}</h3>
                    <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{step.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════
          4. RESOURCES — Cadre Library
          ════════════════════════════════════════════════ */}
      <section
        id="resources"
        className="scroll-mt-16 sm:scroll-mt-[68px] min-h-0 lg:min-h-[calc(100vh-68px)] flex flex-col justify-center bg-slate-50 border-b border-slate-200 py-12 sm:py-16"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-10">
            <div>
              <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
                {t("resources.title")}
              </h2>
              <p className="mt-2 text-slate-500 text-sm max-w-xl leading-relaxed">
                {t("resources.subtitle")}
              </p>
            </div>
            <a href="/discover" className="mt-4 md:mt-0">
              <Button
                variant="outline"
                size="sm"
                className="border-[#1E3A8A] text-[#1E3A8A] hover:bg-[#1E3A8A] hover:text-white rounded-lg text-xs font-semibold cursor-pointer transition-all duration-200"
              >
                {t("resources.browseCatalog")} <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
              </Button>
            </a>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {[
              { tag: t("resources.doc1Tag"), title: t("resources.doc1Title"), desc: t("resources.doc1Desc"), size: "4.2 MB", accentColor: "bg-[#1E3A8A]", iconColor: "text-white bg-[#1E3A8A]" },
              { tag: t("resources.doc2Tag"), title: t("resources.doc2Title"), desc: t("resources.doc2Desc"), size: "3.8 MB", accentColor: "bg-[#0D9488]", iconColor: "text-white bg-[#0D9488]" },
              { tag: t("resources.doc3Tag"), title: t("resources.doc3Title"), desc: t("resources.doc3Desc"), size: "2.6 MB", accentColor: "bg-[#B45309]", iconColor: "text-white bg-[#B45309]" },
              { tag: t("resources.doc4Tag"), title: t("resources.doc4Title"), desc: t("resources.doc4Desc"), size: "5.1 MB", accentColor: "bg-amber-500", iconColor: "text-white bg-amber-500" },
            ].map((doc, i) => (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 overflow-hidden flex flex-col card-hover-lift shadow-sm">
                {/* Top color stripe */}
                <div className={`h-1 w-full ${doc.accentColor}`} />
                <div className="p-5 flex flex-col flex-1">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      {doc.tag}
                    </span>
                    <div className={`h-7 w-7 rounded-lg flex items-center justify-center ${doc.iconColor}`}>
                      <FileText className="h-3.5 w-3.5" />
                    </div>
                  </div>
                  <h3 className="font-bold text-slate-900 text-sm leading-snug flex-1">{doc.title}</h3>
                  <p className="text-xs text-slate-500 mt-2 leading-relaxed line-clamp-3">{doc.desc}</p>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-400 text-[11px]">PDF • {doc.size}</span>
                    <a href="/discover" className="font-semibold text-[#1E3A8A] hover:underline flex items-center gap-1 cursor-pointer">
                      <Download className="h-3.5 w-3.5" /> {t("resources.access")}
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════════
          5. HELP — Support Channels + Closing CTA
          ════════════════════════════════════════════════ */}
      <section
        id="help"
        className="scroll-mt-16 sm:scroll-mt-[68px] min-h-0 lg:min-h-[calc(100vh-68px)] flex flex-col justify-between bg-white pt-12 pb-0"
      >
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full flex-1 flex flex-col justify-center py-4">
          <div className="text-center max-w-2xl mx-auto mb-10">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {t("help.title")}
            </h2>
            <p className="mt-3 text-slate-500 text-sm leading-relaxed">
              {t("help.subtitle")}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Card 1: AI Copilot */}
            <div className="rounded-2xl border border-slate-200 bg-gradient-to-b from-blue-50/80 to-white overflow-hidden flex flex-col card-hover-lift shadow-sm">
              <div className="h-1 w-full bg-[#1E3A8A]" />
              <div className="p-5 flex-1 flex flex-col">
                <div className="h-10 w-10 rounded-xl navy-teal-gradient flex items-center justify-center mb-4">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
                <h3 className="font-bold text-slate-900 text-sm">{t("help.aiTitle")}</h3>
                <p className="text-xs text-slate-500 mt-2 leading-relaxed flex-1">{t("help.aiDesc")}</p>
                <div className="mt-5 pt-3 border-t border-slate-200/70">
                  <a href="/login" className="inline-flex items-center text-xs font-bold text-[#1E3A8A] hover:underline">
                    <Zap className="mr-1.5 h-3.5 w-3.5 text-teal-500" /> {t("help.aiLaunch")} <ArrowRight className="ml-1 h-3 w-3" />
                  </a>
                </div>
              </div>
            </div>

            {/* Card 2: Training Desk */}
            <div className="rounded-2xl border border-slate-200 bg-gradient-to-b from-teal-50/60 to-white overflow-hidden flex flex-col card-hover-lift shadow-sm">
              <div className="h-1 w-full bg-[#0D9488]" />
              <div className="p-5 flex-1 flex flex-col">
                <div className="h-10 w-10 rounded-xl bg-[#0D9488] flex items-center justify-center mb-4">
                  <PhoneCall className="h-5 w-5 text-white" />
                </div>
                <h3 className="font-bold text-slate-900 text-sm">{t("help.deskTitle")}</h3>
                <p className="text-xs text-slate-500 mt-2 leading-relaxed">{t("help.deskDesc")}</p>
                <div className="mt-3 space-y-1.5 text-xs text-slate-600">
                  <p className="flex items-center gap-2"><Mail className="h-3.5 w-3.5 text-slate-400" /> support-karmayogi@gov.in</p>
                  <p className="flex items-center gap-2"><PhoneCall className="h-3.5 w-3.5 text-slate-400" /> 1800-11-KARM</p>
                </div>
                <div className="mt-5 pt-3 border-t border-slate-200/70 flex items-center text-xs text-slate-400">
                  <Clock className="h-3.5 w-3.5 mr-1.5 text-slate-300" /> {t("help.hours")}
                </div>
              </div>
            </div>

            {/* Card 3: FAQs */}
            <div className="rounded-2xl border border-slate-200 bg-gradient-to-b from-amber-50/50 to-white overflow-hidden flex flex-col card-hover-lift shadow-sm">
              <div className="h-1 w-full bg-[#B45309]" />
              <div className="p-5 flex-1 flex flex-col">
                <div className="h-10 w-10 rounded-xl bg-[#B45309] flex items-center justify-center mb-4">
                  <HelpCircle className="h-5 w-5 text-white" />
                </div>
                <h3 className="font-bold text-slate-900 text-sm">{t("help.faqTitle")}</h3>
                <div className="mt-3 space-y-2.5 text-xs flex-1">
                  <div className="p-2.5 bg-white rounded-lg border border-slate-100">
                    <p className="font-semibold text-slate-800">{t("help.faq1Q")}</p>
                    <p className="text-slate-400 mt-0.5 text-[11px]">{t("help.faq1A")}</p>
                  </div>
                  <div className="p-2.5 bg-white rounded-lg border border-slate-100">
                    <p className="font-semibold text-slate-800">{t("help.faq2Q")}</p>
                    <p className="text-slate-400 mt-0.5 text-[11px]">{t("help.faq2A")}</p>
                  </div>
                </div>
                <div className="mt-5 pt-3 border-t border-slate-200/70">
                  <a href="/login" className="inline-flex items-center text-xs font-bold text-[#B45309] hover:underline">
                    {t("help.knowledgeBase")} <ArrowRight className="ml-1 h-3 w-3" />
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Closing CTA — Navy Gradient ── */}
        <div className="hero-gradient text-white py-8 border-t border-white/10 w-full mt-auto relative overflow-hidden">
          <div className="absolute inset-0 hero-mesh opacity-40" />
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-5">
              <div>
                <h3 className="text-base sm:text-xl font-extrabold text-white">
                  {t("cta.readyTitle")}
                </h3>
                <p className="text-xs text-white/60 mt-1 max-w-xl">{t("cta.readyDesc")}</p>
              </div>
              <div className="flex flex-wrap items-center gap-3 shrink-0">
                <a href="/login">
                  <Button variant="outline" size="sm"
                    className="rounded-xl text-white border-white/30 hover:bg-white/10 px-5 py-2.5 text-xs font-semibold cursor-pointer">
                    {t("hero.signIn")}
                  </Button>
                </a>
                <a href="/register">
                  <Button size="sm"
                    className="rounded-xl bg-[#EAB308] hover:bg-[#CA8A04] text-slate-950 font-extrabold px-5 py-2.5 text-xs cursor-pointer border-0 transition-all hover:scale-105 shadow-lg">
                    {t("cta.register")}
                  </Button>
                </a>
              </div>
            </div>

            {/* Legal Strip */}
            <div className="mt-5 pt-4 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-white/35">
              <p>{t("cta.copyright")}</p>
              <div className="flex items-center gap-4 text-white/35">
                <a href="/discover" className="hover:text-white/70 transition-colors">{t("cta.privacy")}</a>
                <span>•</span>
                <a href="/discover" className="hover:text-white/70 transition-colors">{t("cta.terms")}</a>
                <span>•</span>
                <a href="/discover" className="hover:text-white/70 transition-colors">{t("cta.dataGov")}</a>
                <span>•</span>
                <Link href="/#help" className="hover:text-white/70 transition-colors">{t("cta.helpdesk")}</Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
