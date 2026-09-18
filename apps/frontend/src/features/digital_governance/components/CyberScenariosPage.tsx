"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  Lock,
  FileSignature,
  Cloud,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  RotateCcw,
  BookOpen,
  Award,
  ChevronRight,
  Clock,
  Building2,
  FileCheck2,
  Layers,
  Sparkles,
  Info
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { fetchApi } from "@/lib/api";
import confetti from "canvas-confetti";

interface ScenarioListItem {
  id: string;
  title: string;
  domain: string;
  ministry: string;
  statutory_framework: string[];
  difficulty: string;
  estimated_minutes: number;
  summary: string;
  objectives_count: number;
}

interface ScenarioOption {
  option_id: string;
  text: string;
  is_optimal: boolean;
  is_terminal: boolean;
  consequence_summary: string;
  statutory_rationale: string;
  next_question_id?: string;
  compliance_delta: number;
}

interface ScenarioQuestion {
  id: string;
  scenario_id: string;
  stage_title: string;
  prompt: string;
  context_update?: string;
  options: ScenarioOption[];
  governance_pillar: string;
}

interface DecisionNodeLog {
  step: number;
  stage_title: string;
  question_prompt: string;
  selected_option_id: string;
  selected_option_text: string;
  is_optimal: boolean;
  consequence_summary: string;
  statutory_rationale: string;
  score_after_decision: number;
}

interface ScenarioSummary {
  session_id: string;
  scenario_id: string;
  scenario_title: string;
  domain: string;
  ministry: string;
  total_steps: number;
  optimal_steps: number;
  procedural_compliance_score: number;
  resolved_satisfactorily: boolean;
  decision_trail: DecisionNodeLog[];
  key_regulatory_takeaways: string[];
}

const DOMAIN_ICONS: Record<string, any> = {
  "Cybersecurity": ShieldAlert,
  "Data Privacy": Lock,
  "Digital Signatures": FileSignature,
  "Government Cloud": Cloud,
  "Digital Public Infrastructure": Cpu,
};

export default function CyberScenariosPage() {
  const [scenarios, setScenarios] = useState<ScenarioListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDomain, setSelectedDomain] = useState<string>("All");

  // Active Session State
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<any | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<ScenarioQuestion | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [lastDecisionResult, setLastDecisionResult] = useState<any | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [summary, setSummary] = useState<ScenarioSummary | null>(null);

  useEffect(() => {
    fetchApi<ScenarioListItem[]>("/digital-governance/scenarios")
      .then((data) => setScenarios(data))
      .catch((err) => console.error("Error loading scenarios:", err))
      .finally(() => setLoading(false));
  }, []);

  const domains = ["All", "Cybersecurity", "Data Privacy", "Digital Signatures", "Government Cloud", "Digital Public Infrastructure"];

  const filteredScenarios = selectedDomain === "All"
    ? scenarios
    : scenarios.filter((s) => s.domain === selectedDomain);

  const handleStartScenario = async (scenarioId: string) => {
    setLoading(true);
    setLastDecisionResult(null);
    setSelectedOptionId(null);
    setSummary(null);

    try {
      const res = await fetchApi("/digital-governance/scenarios/session/start", {
        method: "POST",
        body: JSON.stringify({ scenario_id: scenarioId }),
      });
      setActiveSessionId(res.session_id);
      setSessionData(res);
      setCurrentQuestion(res.current_question);
    } catch (err: any) {
      alert("Error starting scenario session: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitDecision = async () => {
    if (!activeSessionId || !selectedOptionId) return;
    setSubmitting(true);

    try {
      const res = await fetchApi(`/digital-governance/scenarios/session/${activeSessionId}/answer`, {
        method: "POST",
        body: JSON.stringify({ option_id: selectedOptionId }),
      });

      setLastDecisionResult(res);

      if (res.is_terminal && res.session_summary) {
        setSummary(res.session_summary);
        if (res.session_summary.resolved_satisfactorily) {
          confetti({ particleCount: 90, spread: 60, origin: { y: 0.6 } });
        }
      }
    } catch (err: any) {
      alert("Failed to submit decision: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleAdvanceToNext = () => {
    if (lastDecisionResult?.next_question) {
      setCurrentQuestion(lastDecisionResult.next_question);
      setLastDecisionResult(null);
      setSelectedOptionId(null);
    }
  };

  const handleResetSession = () => {
    setActiveSessionId(null);
    setSessionData(null);
    setCurrentQuestion(null);
    setSelectedOptionId(null);
    setLastDecisionResult(null);
    setSummary(null);
  };

  if (loading && !activeSessionId) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-4 border-slate-200 border-t-[#1E3A8A] animate-spin" />
      </div>
    );
  }

  // ── VIEW 3: FINAL EXECUTIVE DEBRIEF REPORT ─────────────────────────────────
  if (summary) {
    const DomainIcon = DOMAIN_ICONS[summary.domain] || ShieldAlert;
    return (
      <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">
        <Card className="border-slate-200 bg-white shadow-md overflow-hidden">
          <div
            className={`p-8 text-center border-b ${
              summary.resolved_satisfactorily
                ? "bg-gradient-to-b from-emerald-50 to-white border-emerald-100"
                : "bg-gradient-to-b from-rose-50 to-white border-rose-100"
            }`}
          >
            <div
              className={`h-16 w-16 rounded-full mx-auto flex items-center justify-center mb-4 ${
                summary.resolved_satisfactorily
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-rose-100 text-rose-700"
              }`}
            >
              {summary.resolved_satisfactorily ? (
                <CheckCircle2 className="h-10 w-10" />
              ) : (
                <AlertTriangle className="h-10 w-10" />
              )}
            </div>

            <Badge variant={summary.resolved_satisfactorily ? "success" : "default"} className="mb-2">
              {summary.resolved_satisfactorily ? "Statutory Compliance Achieved" : "Procedural Deficiencies Noted"}
            </Badge>

            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
              Executive Incident Debrief
            </h1>
            <p className="text-xs text-slate-500 mt-1 max-w-lg mx-auto">
              {summary.scenario_title}
            </p>

            <div className="mt-6 flex justify-center items-center gap-6">
              <div className="text-center">
                <p className="text-3xl font-extrabold text-slate-900">{summary.procedural_compliance_score}%</p>
                <p className="text-[11px] text-slate-500 uppercase font-semibold">Compliance Score</p>
              </div>
              <div className="h-10 w-px bg-slate-200" />
              <div className="text-center">
                <p className="text-3xl font-extrabold text-slate-900">
                  {summary.optimal_steps} / {summary.total_steps}
                </p>
                <p className="text-[11px] text-slate-500 uppercase font-semibold">Optimal Checkpoints</p>
              </div>
              <div className="h-10 w-px bg-slate-200" />
              <div className="text-center">
                <p className="text-sm font-bold text-slate-900 truncate max-w-[140px]">{summary.domain}</p>
                <p className="text-[11px] text-slate-500 uppercase font-semibold">Pillar</p>
              </div>
            </div>

            <div className="mt-8 flex justify-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={handleResetSession}
                className="text-xs font-semibold rounded-xl"
              >
                <RotateCcw className="h-3.5 w-3.5 mr-1" /> Choose Another Scenario
              </Button>
              <Button
                size="sm"
                onClick={() => handleStartScenario(summary.scenario_id)}
                className="navy-teal-gradient hover:opacity-95 text-white text-xs font-semibold px-5 shadow-xs rounded-xl"
              >
                Retake Simulation
              </Button>
            </div>
          </div>

          {/* Decision Trail Breakdown */}
          <CardContent className="p-6 sm:p-8 space-y-6">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <FileCheck2 className="h-4 w-4 text-[#1E3A8A]" />
              Audited Decision Trail & Statutory Compliance Log
            </h3>

            <div className="space-y-4">
              {summary.decision_trail.map((node) => (
                <div
                  key={node.step}
                  className={`p-4 rounded-xl border text-xs leading-relaxed ${
                    node.is_optimal
                      ? "bg-emerald-50/40 border-emerald-200"
                      : "bg-amber-50/40 border-amber-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide">
                        Checkpoint {node.step}: {node.stage_title}
                      </span>
                      <p className="font-semibold text-slate-900 mt-0.5">{node.question_prompt}</p>
                    </div>
                    <Badge variant={node.is_optimal ? "success" : "warning"} className="shrink-0">
                      {node.is_optimal ? "Optimal Action" : "Sub-Optimal Action"}
                    </Badge>
                  </div>

                  <div className="space-y-1.5 text-slate-700 bg-white/70 p-3 rounded-lg border border-slate-200/60 mt-2">
                    <p>
                      <span className="font-bold text-slate-900">Your Action:</span> {node.selected_option_text}
                    </p>
                    <p className="text-slate-600">
                      <span className="font-bold text-slate-900">Operational Consequence:</span> {node.consequence_summary}
                    </p>
                    <p className="text-[11px] text-slate-500 italic pt-1 border-t border-slate-100">
                      <span className="font-semibold text-slate-700">Statutory Rationale:</span> {node.statutory_rationale}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Regulatory Takeaways */}
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2 text-xs">
              <h4 className="font-bold text-slate-900 uppercase tracking-wide flex items-center gap-1.5">
                <Info className="h-3.5 w-3.5 text-[#1E3A8A]" /> Key Regulatory Takeaways
              </h4>
              <ul className="list-disc pl-5 space-y-1 text-slate-600">
                {summary.key_regulatory_takeaways.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── VIEW 2: ACTIVE SCENARIO SIMULATION RUNNER ──────────────────────────────
  if (activeSessionId && currentQuestion) {
    const DomainIcon = DOMAIN_ICONS[sessionData.domain] || ShieldAlert;
    const isAnswered = lastDecisionResult !== null;

    return (
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {/* Top Status Bar */}
        <div className="flex items-center justify-between gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="secondary" className="text-[10px] font-semibold text-[#1E3A8A] bg-blue-50 border-blue-200">
                <DomainIcon className="h-3 w-3 mr-1 inline" />
                {sessionData.domain}
              </Badge>
              <span className="text-[11px] text-slate-400">•</span>
              <span className="text-[11px] text-slate-500 font-medium truncate">{sessionData.ministry}</span>
            </div>
            <h2 className="text-sm font-bold text-slate-900 truncate">
              {sessionData.scenario_title}
            </h2>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <div className="text-right">
              <div className="text-[10px] uppercase font-bold text-slate-400">Compliance</div>
              <div className="text-sm font-extrabold text-slate-900">
                {lastDecisionResult ? lastDecisionResult.compliance_score : sessionData.compliance_score}%
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={handleResetSession} className="text-xs">
              Exit
            </Button>
          </div>
        </div>

        {/* Active Stage & Question Card */}
        <Card className="border-slate-200 bg-white shadow-sm overflow-hidden">
          <CardHeader className="bg-slate-50/50 border-b border-slate-100 pb-4">
            <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span className="font-bold text-[#1E3A8A] uppercase tracking-wider">
                {currentQuestion.stage_title}
              </span>
              <span>Step {sessionData.step_number || 1}</span>
            </div>
            <CardTitle className="text-base font-bold text-slate-900 leading-snug">
              {currentQuestion.prompt}
            </CardTitle>
          </CardHeader>

          <CardContent className="p-6 space-y-5">
            {/* Context update banner if present */}
            {currentQuestion.context_update && (
              <div className="p-3.5 rounded-lg bg-amber-50/70 border border-amber-200 text-xs text-amber-900 flex items-start gap-2.5">
                <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Incident Progression Update: </span>
                  {currentQuestion.context_update}
                </div>
              </div>
            )}

            {/* Decision Choices */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide">
                Select Your Operational Action:
              </h4>

              {currentQuestion.options.map((opt, idx) => {
                const isSelected = selectedOptionId === opt.option_id;
                const isAnswerSubmitted = isAnswered;
                const isChosenAnswer = isAnswerSubmitted && lastDecisionResult.selected_option.option_id === opt.option_id;

                let borderClass = "border-slate-200 hover:border-blue-300 bg-white";
                if (isSelected && !isAnswerSubmitted) {
                  borderClass = "border-[#1E3A8A] bg-blue-50/40 ring-1 ring-[#1E3A8A]";
                } else if (isChosenAnswer) {
                  borderClass = opt.is_optimal
                    ? "border-emerald-500 bg-emerald-50/60 ring-1 ring-emerald-500"
                    : "border-amber-500 bg-amber-50/60 ring-1 ring-amber-500";
                }

                return (
                  <button
                    key={opt.option_id}
                    type="button"
                    disabled={isAnswerSubmitted}
                    onClick={() => setSelectedOptionId(opt.option_id)}
                    className={`w-full p-4 rounded-xl border text-left text-xs font-medium transition-all flex items-start gap-3 cursor-pointer disabled:cursor-default ${borderClass}`}
                  >
                    <span
                      className={`h-5 w-5 rounded-full text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5 ${
                        isSelected
                          ? "bg-[#1E3A8A] text-white"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <span className="text-slate-800 leading-relaxed">{opt.text}</span>
                  </button>
                );
              })}
            </div>

            {/* Consequence & Statutory Rationale Callout after decision is submitted */}
            {isAnswered && (
              <div
                className={`p-4 rounded-xl border text-xs leading-relaxed space-y-2 animate-in fade-in duration-200 ${
                  lastDecisionResult.selected_option.is_optimal
                    ? "bg-emerald-50/80 border-emerald-300 text-emerald-950"
                    : "bg-amber-50/80 border-amber-300 text-amber-950"
                }`}
              >
                <div className="flex items-center gap-2 font-bold text-sm">
                  {lastDecisionResult.selected_option.is_optimal ? (
                    <>
                      <CheckCircle2 className="h-4 w-4 text-emerald-700" /> Optimal Action Executed
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-4 w-4 text-amber-700" /> Procedural Risk / Sub-Optimal Action
                    </>
                  )}
                </div>

                <p>
                  <span className="font-semibold">Immediate Operational Impact: </span>
                  {lastDecisionResult.selected_option.consequence_summary}
                </p>

                <p className="pt-2 border-t border-slate-300/60 text-[11px] text-slate-700">
                  <span className="font-bold text-slate-900">Statutory Rationale: </span>
                  {lastDecisionResult.selected_option.statutory_rationale}
                </p>
              </div>
            )}
          </CardContent>

          <CardFooter className="flex items-center justify-between border-t border-slate-100 p-4 bg-slate-50/30">
            <Button variant="outline" size="sm" onClick={handleResetSession} className="text-xs rounded-xl">
              Abort Simulation
            </Button>

            {!isAnswered ? (
              <Button
                size="sm"
                disabled={!selectedOptionId || submitting}
                onClick={handleSubmitDecision}
                className="navy-teal-gradient hover:opacity-95 text-white text-xs font-semibold px-6 shadow-xs cursor-pointer disabled:opacity-50 rounded-xl"
              >
                {submitting ? "Evaluating..." : "Commit Operational Action"}
              </Button>
            ) : lastDecisionResult.is_terminal ? (
              <Button
                size="sm"
                onClick={() => setSummary(lastDecisionResult.session_summary)}
                className="navy-teal-gradient hover:opacity-95 text-white text-xs font-semibold px-6 shadow-xs cursor-pointer rounded-xl"
              >
                View Final Executive Debrief <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={handleAdvanceToNext}
                className="navy-teal-gradient hover:opacity-95 text-white text-xs font-semibold px-6 shadow-xs cursor-pointer rounded-xl"
              >
                Advance to Next Stage <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            )}
          </CardFooter>
        </Card>
      </div>
    );
  }

  // ── VIEW 1: SCENARIO SELECTION DIRECTORY ──────────────────────────────────
  return (
    <div className="min-h-[calc(100vh-65px)] bg-slate-50 flex flex-col w-full">
      {/* Header Banner - Full Edge-to-Edge */}
      <section className="hero-gradient text-white py-10 sm:py-12 relative overflow-hidden shadow-md border-b border-blue-900/40 w-full">
        <div className="hero-mesh" />
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4">
          <div className="flex items-center gap-2 text-xs font-bold text-teal-300 uppercase tracking-wider">
            <Building2 className="h-4 w-4" />
            <span>National e-Governance Division (NeGD) & CERT-In Accredited</span>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Digital Governance Incident Tabletop Simulations
              </h1>
              <p className="text-xs sm:text-sm text-white/80 mt-1 max-w-2xl leading-relaxed">
                Multi-stage branching operational exercises designed for Indian civil servants. Make high-stakes
                decisions under statutory mandates including the IT Act 2000, CERT-In 6-hour directions, DPDP Act 2023,
                CCA PKI rules, and MeghRaj Cloud sovereignty frameworks.
              </p>
            </div>
            <Link href="/courses">
              <Button size="sm" className="glass-light hover:bg-white/20 border border-white/20 text-white font-semibold text-xs shrink-0 rounded-xl">
                <BookOpen className="h-3.5 w-3.5 mr-1 text-teal-300" /> View Official Curriculum
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Main Content: Filter & Scenarios */}
      <div className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full space-y-8">

      {/* Domain Filter Pills Card */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center gap-2">
        <span className="text-xs font-bold text-slate-500 mr-1 uppercase tracking-wide">Pillars:</span>
        {domains.map((dom) => {
          const isSelected = selectedDomain === dom;
          return (
            <button
              key={dom}
              type="button"
              onClick={() => setSelectedDomain(dom)}
              className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                isSelected
                  ? "navy-teal-gradient text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {dom}
            </button>
          );
        })}
      </div>

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredScenarios.map((scenario) => {
          const Icon = DOMAIN_ICONS[scenario.domain] || ShieldAlert;
          return (
            <Card
              key={scenario.id}
              className="border-slate-200 bg-white shadow-xs hover:shadow-md transition-shadow flex flex-col justify-between overflow-hidden"
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <Badge variant="secondary" className="text-[10px] font-semibold text-[#1E3A8A] bg-blue-50 border-blue-200">
                    <Icon className="h-3 w-3 mr-1 inline" />
                    {scenario.domain}
                  </Badge>
                  <span className="text-[11px] text-slate-500 font-medium flex items-center gap-1">
                    <Clock className="h-3 w-3" /> {scenario.estimated_minutes} mins
                  </span>
                </div>
                <CardTitle className="text-base font-bold text-slate-900 leading-snug line-clamp-2">
                  {scenario.title}
                </CardTitle>
                <p className="text-[11px] font-semibold text-slate-500 mt-1 truncate">
                  {scenario.ministry}
                </p>
              </CardHeader>

              <CardContent className="space-y-3 pb-4">
                <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                  {scenario.summary}
                </p>

                <div className="pt-2 border-t border-slate-100 space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                    Statutory Framework:
                  </span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {scenario.statutory_framework.slice(0, 2).map((st, i) => (
                      <span key={i} className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                        {st}
                      </span>
                    ))}
                  </div>
                </div>
              </CardContent>

              <CardFooter className="border-t border-slate-100 pt-3 bg-slate-50/50">
                <Button
                  onClick={() => handleStartScenario(scenario.id)}
                  className="w-full navy-teal-gradient hover:opacity-95 text-white text-xs font-semibold shadow-xs cursor-pointer rounded-xl"
                >
                  Launch Tabletop Simulation <ArrowRight className="h-3.5 w-3.5 ml-1" />
                </Button>
              </CardFooter>
            </Card>
          );
        })}
      </div>
    </div>
  </div>
  );
}
