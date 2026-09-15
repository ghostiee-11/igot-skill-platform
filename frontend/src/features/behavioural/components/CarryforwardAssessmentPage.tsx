"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileText,
  ShieldAlert,
  GitBranch,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Scale,
  Building2,
  RotateCcw,
  Sparkles,
  ExternalLink,
  Clock,
  Layers,
  BookOpen,
  X,
} from "lucide-react";
import { fetchApi } from "@/lib/api";

interface GovernmentDocument {
  id: string;
  title: string;
  document_type: string;
  issuing_authority: string;
  document_number: string;
  statutory_reference: string;
  date_of_issue: string;
  full_text: string;
  key_stakeholders: string[];
  procedural_clauses: string[];
}

interface CarryforwardOption {
  option_id: string;
  text: string;
  is_optimal: boolean;
  is_satisfactory_terminal: boolean;
  consequence_summary: string;
  statutory_rationale: string;
  next_question_id?: string;
}

interface CarryforwardQuestion {
  id: string;
  case_id: string;
  stage_type: "root" | "carryforward_branch";
  prompt: string;
  context_update?: string;
  options: CarryforwardOption[];
  behavioral_competencies: string[];
}

interface CaseScenario {
  id: string;
  title: string;
  category: string;
  course_id?: number;
  course_title?: string;
  course_organization?: string;
  document_id: string;
  document_title: string;
  document_type: string;
  statutory_citations: string[];
  initial_context: string;
  root_question_id: string;
  questions: Record<string, CarryforwardQuestion>;
  learning_objectives: string[];
}

interface CourseCaseOverview {
  course_id: number;
  title: string;
  organization: string;
  category: string;
  overview: string;
  mapped_notices: string[];
  case_count: number;
}

interface DecisionNodeLog {
  question_id: string;
  stage_type: string;
  question_prompt: string;
  selected_option_id: string;
  selected_option_text: string;
  is_optimal: boolean;
  is_satisfactory_terminal: boolean;
  consequence_summary: string;
  statutory_rationale: string;
}

interface CompetencyResult {
  competency: string;
  score: number;
  level: string;
  description: string;
}

interface SessionSummary {
  session_id: string;
  case_id: string;
  case_title: string;
  document_title: string;
  document_type: string;
  total_steps: number;
  optimal_steps: number;
  procedural_compliance_score: number;
  resolved_satisfactorily: boolean;
  decision_trail: DecisionNodeLog[];
  competency_scores?: Record<string, number>;
  competency_results?: CompetencyResult[];
  strengths?: string[];
  weaknesses?: string[];
  recommended_upskilling?: string[];
  key_takeaways: string[];
}

export default function CarryforwardAssessmentPage() {
  const [activeTab, setActiveTab] = useState<"cases" | "generator" | "corpus">("cases");
  const [cases, setCases] = useState<CaseScenario[]>([]);
  const [corpus, setCorpus] = useState<GovernmentDocument[]>([]);
  const [courses, setCourses] = useState<CourseCaseOverview[]>([]);
  const [selectedCourseFilter, setSelectedCourseFilter] = useState<number | null>(null);
  const [selectedGenCourseId, setSelectedGenCourseId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCaseId, setSelectedCaseId] = useState<string>("");

  // Interactive Session State
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [activeCase, setActiveCase] = useState<CaseScenario | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState<CarryforwardQuestion | null>(null);
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastAnswerResult, setLastAnswerResult] = useState<any | null>(null);
  const [sessionCompleted, setSessionCompleted] = useState(false);
  const [summaryData, setSummaryData] = useState<SessionSummary | null>(null);
  const [trail, setTrail] = useState<DecisionNodeLog[]>([]);

  // Document Inspector Modal / Accordion
  const [inspectingDoc, setInspectingDoc] = useState<GovernmentDocument | null>(null);
  const [showDocModal, setShowDocModal] = useState(false);

  // Generator State
  const [genTitle, setGenTitle] = useState("");
  const [genType, setGenType] = useState("Notice");
  const [genAuthority, setGenAuthority] = useState("Department of Personnel & Training (DoPT)");
  const [genReference, setGenReference] = useState("CCS (Conduct) Rules, 1964");
  const [genText, setGenText] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [genError, setGenError] = useState<string | null>(null);

  // Load initial cases, corpus, and courses
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [casesData, corpusData, coursesData] = await Promise.all([
          fetchApi<CaseScenario[]>("/behavioural/cases"),
          fetchApi<GovernmentDocument[]>("/behavioural/corpus"),
          fetchApi<CourseCaseOverview[]>("/behavioural/courses")
        ]);
        setCases(casesData);
        setCorpus(corpusData);
        setCourses(coursesData);

        // Check if navigated from a course with ?courseId=X
        let initialCaseId = casesData.length > 0 ? casesData[0].id : "";
        if (typeof window !== "undefined") {
          const params = new URLSearchParams(window.location.search);
          const cId = params.get("courseId");
          if (cId) {
            const parsed = parseInt(cId, 10);
            if (!isNaN(parsed)) {
              setSelectedCourseFilter(parsed);
              setSelectedGenCourseId(parsed);
              const courseCases = casesData.filter((c) => c.course_id === parsed);
              if (courseCases.length > 0) {
                initialCaseId = courseCases[0].id;
              }
            }
          }
        }
        if (initialCaseId) {
          setSelectedCaseId(initialCaseId);
        }
      } catch (err) {
        console.error("Failed to load behavioural cases:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Start or reset an interactive session
  const startSession = async (caseIdToStart?: string, caseOverride?: CaseScenario) => {
    const targetCaseId = caseIdToStart || selectedCaseId;
    try {
      setLoading(true);
      setLastAnswerResult(null);
      setSessionCompleted(false);
      setSummaryData(null);
      setTrail([]);
      setSelectedOptionId(null);

      const res = await fetchApi<{
        session_id: string;
        case_id: string;
        case_title: string;
        document_title: string;
        document_type: string;
        initial_context: string;
        current_question: CarryforwardQuestion;
      }>("/behavioural/session/start", {
        method: "POST",
        body: JSON.stringify({ case_id: targetCaseId })
      });

      setSessionId(res.session_id);
      const matchedCase =
        caseOverride ||
        cases.find((c) => c.id === res.case_id) ||
        null;
      setActiveCase(matchedCase);
      setCurrentQuestion(res.current_question);
    } catch (err: any) {
      alert("Failed to start session: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Submit response to current MCQ
  const submitAnswer = async () => {
    if (!sessionId || !currentQuestion || !selectedOptionId) return;

    try {
      setIsSubmitting(true);
      const res = await fetchApi<{
        is_optimal: boolean;
        is_satisfactory_terminal: boolean;
        consequence_summary: string;
        statutory_rationale: string;
        carryforward_active: boolean;
        scenario_completed: boolean;
        session_completed: boolean;
        current_score: number;
        total_steps_taken: number;
        next_question?: CarryforwardQuestion;
        next_case_id?: string;
      }>(`/behavioural/session/${sessionId}/submit`, {
        method: "POST",
        body: JSON.stringify({
          question_id: currentQuestion.id,
          selected_option_id: selectedOptionId
        })
      });

      const selectedOpt = currentQuestion.options.find((o) => o.option_id === selectedOptionId);
      if (selectedOpt) {
        setTrail((prev) => [
          ...prev,
          {
            question_id: currentQuestion.id,
            stage_type: currentQuestion.stage_type,
            question_prompt: currentQuestion.prompt,
            selected_option_id: selectedOpt.option_id,
            selected_option_text: selectedOpt.text,
            is_optimal: selectedOpt.is_optimal,
            is_satisfactory_terminal: selectedOpt.is_satisfactory_terminal,
            consequence_summary: selectedOpt.consequence_summary,
            statutory_rationale: selectedOpt.statutory_rationale
          }
        ]);
      }

      setLastAnswerResult(res);
    } catch (err: any) {
      alert("Submission error: " + err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Move to next question or scenario
  const proceedToNextQuestion = async () => {
    if (!lastAnswerResult || !sessionId) return;
    if (lastAnswerResult.next_question && !lastAnswerResult.session_completed) {
      if (lastAnswerResult.next_case_id) {
        const nextCase = cases.find((c) => c.id === lastAnswerResult.next_case_id);
        if (nextCase) setActiveCase(nextCase);
      }
      setCurrentQuestion(lastAnswerResult.next_question);
      setSelectedOptionId(null);
      setLastAnswerResult(null);
      return;
    }
    if (lastAnswerResult.session_completed) {
      const sum = await fetchApi<SessionSummary>(`/behavioural/session/${sessionId}/summary`);
      setSummaryData(sum);
      setSessionCompleted(true);
    }
  };

  // Course Notice & Syllabus Pre-filler for Generation Studio
  const handleLoadCourseNotice = (courseId: number) => {
    const course = courses.find((c) => c.course_id === courseId);
    if (!course) return;
    setSelectedGenCourseId(courseId);

    // Look for matching document from corpus
    let matchedDoc = corpus.find(
      (d) => course.mapped_notices.some((mn) => d.title.toLowerCase().includes(mn.toLowerCase()))
    );

    if (matchedDoc) {
      setGenTitle(matchedDoc.title);
      setGenType(matchedDoc.document_type);
      setGenAuthority(matchedDoc.issuing_authority);
      setGenReference(matchedDoc.statutory_reference);
      setGenText(matchedDoc.full_text);
    } else {
      setGenTitle(`Operational Scrutiny Notice: ${course.title}`);
      setGenType("Notice");
      setGenAuthority(course.organization);
      setGenReference("GFR 2017 & Administrative Service Rules");
      setGenText(
        `GOVERNMENT OF INDIA\n${course.organization.toUpperCase()}\n\nADMINISTRATIVE COMPLIANCE & QUALITY SCRUTINY DIRECTIVE\n\nSubject: Procedural Adherence in ${course.title} Field Protocols.\n\n` +
        `1. During regular quality monitoring across zonal directorates, procedural variances and delays in submitting statutory returns have been observed.\n` +
        `2. All controlling officers are directed to enforce strict compliance with core technical methodologies and reporting timelines.\n` +
        `3. Any informal shortcuts or unverified deviations must be addressed with immediate remediation under administrative rules.`
      );
    }
  };

  // Custom Notice & Course-Anchored Case Generation
  const handleGenerateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!genText || genText.length < 50) {
      setGenError("Please paste at least 50 characters of government document text.");
      return;
    }
    try {
      setIsGenerating(true);
      setGenError(null);

      let newCase: CaseScenario;
      if (selectedGenCourseId) {
        newCase = await fetchApi<CaseScenario>(`/behavioural/courses/${selectedGenCourseId}/generate-case`, {
          method: "POST",
          body: JSON.stringify({
            course_id: selectedGenCourseId,
            custom_notice_text: genText
          })
        });
      } else {
        newCase = await fetchApi<CaseScenario>("/behavioural/cases/generate", {
          method: "POST",
          body: JSON.stringify({
            raw_text: genText,
            document_title: genTitle || "Government Notice",
            document_type: genType,
            issuing_authority: genAuthority,
            statutory_reference: genReference
          })
        });
      }

      setCases((prev) => [newCase, ...prev]);
      setSelectedCaseId(newCase.id);
      if (newCase.course_id) {
        setSelectedCourseFilter(newCase.course_id);
      }
      setActiveTab("cases");
      await startSession(newCase.id, newCase);
    } catch (err: any) {
      setGenError(err.message || "Failed to generate case from document.");
    } finally {
      setIsGenerating(false);
    }
  };

  const openDocumentInspector = (docId: string) => {
    const doc = corpus.find((d) => d.id === docId);
    if (doc) {
      setInspectingDoc(doc);
      setShowDocModal(true);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/60 pb-24 text-slate-800">
      {/* Header Banner */}
      <div className="border-b border-slate-200 bg-white shadow-xs">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 rounded-md bg-blue-50 px-2.5 py-1 text-xs font-semibold text-[#1E3A8A] ring-1 ring-blue-700/10">
                  <Scale className="h-3.5 w-3.5 text-[#1E3A8A]" />
                  Mission Karmayogi • Civil Services Capacity Building
                </span>
                <span className="inline-flex items-center gap-1 rounded-md bg-teal-50 px-2 py-0.5 text-xs font-semibold text-[#0D9488] ring-1 ring-teal-700/10">
                  <GitBranch className="h-3 w-3" />
                  Carryforward Adaptive Engine
                </span>
              </div>
              <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
                Practise better administrative decisions.
              </h1>
              <p className="mt-1 text-sm text-slate-600 max-w-3xl">
                Real administrative decisions derived from authentic Government Notices, Statutory Forms, and
                Departmental Proceedings. When an answer creates regulatory complications, it branches into consequential
                follow-up MCQs until the case reaches satisfactory resolution.
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Link
                href="/behavioural/interview"
                className="inline-flex items-center gap-2 rounded-lg bg-white border border-[#1E3A8A]/30 px-3.5 py-2 text-xs font-bold text-[#1E3A8A] shadow-xs hover:bg-blue-50/50 transition-all"
              >
                <Clock className="h-4 w-4 text-[#0D9488]" />
                Live interview
              </Link>
            </div>
          </div>

          {/* Tab Navigation */}
          <div className="mt-6 flex space-x-2 border-b border-slate-200">
            <button
              onClick={() => setActiveTab("cases")}
              className={`pb-3 px-3 text-sm font-semibold transition-all border-b-2 cursor-pointer ${
                activeTab === "cases"
                  ? "border-[#1E3A8A] text-[#1E3A8A]"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <span className="flex items-center gap-1.5">
                <Layers className="h-4 w-4" />
                Case practice
              </span>
            </button>
            <button
              onClick={() => setActiveTab("corpus")}
              className={`pb-3 px-3 text-sm font-semibold transition-all border-b-2 cursor-pointer ${
                activeTab === "corpus"
                  ? "border-[#1E3A8A] text-[#1E3A8A]"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <span className="flex items-center gap-1.5">
                <BookOpen className="h-4 w-4" />
                Sources
              </span>
            </button>
            <button
              onClick={() => setActiveTab("generator")}
              className={`pb-3 px-3 text-sm font-semibold transition-all border-b-2 cursor-pointer ${
                activeTab === "generator"
                  ? "border-[#1E3A8A] text-[#1E3A8A]"
                  : "border-transparent text-slate-500 hover:text-slate-700"
              }`}
            >
              <span className="flex items-center gap-1.5">
                <Sparkles className="h-4 w-4 text-[#0D9488]" />
                Create case
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {activeTab === "cases" && (
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
            {/* Left Sidebar: Case Scenario Selector */}
            <div className="lg:col-span-4 space-y-4">
              <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
                <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                  <h3 className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                    <Building2 className="h-4 w-4 text-[#1E3A8A]" />
                    Select Administrative Case
                  </h3>
                  <span className="text-xs text-slate-500">
                    {selectedCourseFilter ? cases.filter((c) => c.course_id === selectedCourseFilter).length : cases.length} of {cases.length}
                  </span>
                </div>

                {/* Course Curriculum Filter */}
                <div className="mt-3.5">
                  <label className="block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1">
                    Filter by Course Curriculum
                  </label>
                  <select
                    value={selectedCourseFilter ?? ""}
                    onChange={(e) => {
                      const val = e.target.value ? parseInt(e.target.value, 10) : null;
                      setSelectedCourseFilter(val);
                      const targetList = val ? cases.filter((c) => c.course_id === val) : cases;
                      if (targetList.length > 0) {
                        setSelectedCaseId(targetList[0].id);
                        startSession(targetList[0].id);
                      }
                    }}
                    className="w-full rounded-lg border border-slate-200 bg-slate-50/70 px-2.5 py-1.5 text-xs font-semibold text-slate-800 focus:border-[#1E3A8A] focus:outline-hidden cursor-pointer"
                  >
                    <option value="">All Courses & General Cases ({cases.length})</option>
                    {courses.map((course) => {
                      const count = cases.filter((c) => c.course_id === course.course_id).length;
                      return (
                        <option key={course.course_id} value={course.course_id}>
                          Course {course.course_id}: {course.title.length > 34 ? course.title.slice(0, 34) + "..." : course.title} ({count})
                        </option>
                      );
                    })}
                  </select>
                </div>

                <div className="mt-3 space-y-2.5">
                  {(selectedCourseFilter ? cases.filter((c) => c.course_id === selectedCourseFilter) : cases).map((c) => {
                    const isSelected = (activeCase && activeCase.id === c.id) || selectedCaseId === c.id;
                    return (
                      <button
                        key={c.id}
                        onClick={() => {
                          setSelectedCaseId(c.id);
                          startSession(c.id);
                        }}
                        className={`w-full text-left p-3.5 rounded-lg border transition-all cursor-pointer ${
                          isSelected
                            ? "border-[#1E3A8A] bg-blue-50/40 ring-1 ring-[#1E3A8A]/20"
                            : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="inline-block rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700">
                            {c.document_type}
                          </span>
                          <span className="text-[11px] font-semibold text-[#0D9488] flex items-center gap-1">
                            <GitBranch className="h-3 w-3" />
                            Multi-Stage
                          </span>
                        </div>
                        <h4 className="mt-1.5 text-sm font-bold text-slate-900 leading-snug">{c.title}</h4>
                        <p className="mt-1 text-xs text-slate-500 line-clamp-2">{c.category}</p>
                        {c.course_title && (
                          <div className="mt-2 pt-2 border-t border-slate-100 flex items-center gap-1.5 text-[11px] font-medium text-[#1E3A8A]">
                            <BookOpen className="h-3 w-3 shrink-0 text-[#0D9488]" />
                            <span className="truncate">{c.course_title}</span>
                          </div>
                        )}
                      </button>
                    );
                  })}
                  {(selectedCourseFilter && cases.filter((c) => c.course_id === selectedCourseFilter).length === 0) && (
                    <div className="p-4 rounded-lg bg-slate-50 border border-slate-200 text-center text-xs text-slate-500">
                      No cases generated yet for this course.
                      <button
                        onClick={() => {
                          setSelectedGenCourseId(selectedCourseFilter);
                          handleLoadCourseNotice(selectedCourseFilter);
                          setActiveTab("generator");
                        }}
                        className="mt-2 block w-full rounded bg-[#1E3A8A] text-white py-1.5 font-bold text-[11px] hover:opacity-90 transition-opacity"
                      >
                        Generate Case from Syllabus
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Official Source Document Quick Viewer */}
              {activeCase && (
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">Source Document</h4>
                    <button
                      onClick={() => openDocumentInspector(activeCase.document_id)}
                      className="text-xs font-bold text-[#1E3A8A] hover:underline flex items-center gap-1 cursor-pointer"
                    >
                      <ExternalLink className="h-3 w-3" />
                      View Gazette Sheet
                    </button>
                  </div>
                  <div className="mt-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
                    <p className="text-xs font-bold text-slate-900">{activeCase.document_title}</p>
                    <div className="mt-2 space-y-1">
                      {activeCase.statutory_citations.map((cite, i) => (
                        <span
                          key={i}
                          className="inline-block mr-1 mb-1 rounded bg-slate-200/80 px-2 py-0.5 text-[10px] font-medium text-slate-700"
                        >
                          {cite}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right Panel: Interactive MCQ & Carryforward Runner */}
            <div className="lg:col-span-8">
              {!sessionId ? (
                <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-xs">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-blue-50 text-[#1E3A8A]">
                    <Scale className="h-7 w-7" />
                  </div>
                  <h3 className="mt-4 text-lg font-bold text-slate-900">Ready to Begin Case Deliberation</h3>
                  <p className="mt-2 text-sm text-slate-600 max-w-md mx-auto">
                    Select an administrative case from the left panel to examine official evidence, exercise executive
                    judgment, and navigate consequential carryforward branches.
                  </p>
                  <button
                    onClick={() => startSession()}
                    className="mt-6 inline-flex items-center gap-2 rounded-lg bg-[#1E3A8A] px-5 py-2.5 text-sm font-bold text-white shadow-xs hover:bg-[#1E3A8A]/90 transition-all cursor-pointer"
                  >
                    <ArrowRight className="h-4 w-4" />
                    Commence Inquiry Session
                  </button>
                </div>
              ) : sessionCompleted && summaryData ? (
                /* Completed Session Summary View */
                <div className="space-y-6">
                  <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-5">
                      <div>
                        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700 border border-emerald-200">
                          Case Satisfactorily Resolved
                        </span>
                        <h2 className="mt-2 text-xl font-bold text-slate-900">{summaryData.case_title}</h2>
                        <p className="text-xs text-slate-500 mt-0.5">Based on: {summaryData.document_title}</p>
                      </div>

                      <div className="text-right">
                        <div className="text-2xl font-black text-[#1E3A8A]">
                          {summaryData.procedural_compliance_score}%
                        </div>
                        <div className="text-xs font-bold text-slate-500">Procedural Compliance</div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 my-6">
                      <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100 text-center">
                        <div className="text-lg font-bold text-slate-900">{summaryData.total_steps}</div>
                        <div className="text-xs text-slate-500">Total Decision Steps</div>
                      </div>
                      <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100 text-center">
                        <div className="text-lg font-bold text-emerald-600">{summaryData.optimal_steps}</div>
                        <div className="text-xs text-slate-500">Optimal Choices</div>
                      </div>
                      <div className="col-span-2 sm:col-span-1 p-3.5 rounded-lg bg-slate-50 border border-slate-100 text-center">
                        <div className="text-lg font-bold text-[#0D9488]">
                          {summaryData.total_steps > summaryData.optimal_steps ? "Cured in Branch" : "Direct Resolution"}
                        </div>
                        <div className="text-xs text-slate-500">Resolution Pathway</div>
                      </div>
                    </div>

                    {/* Competency Level Evaluation Results */}
                    {summaryData.competency_results && summaryData.competency_results.length > 0 && (
                      <div className="mt-6 pt-5 border-t border-slate-100">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-1.5">
                          <Scale className="h-4 w-4 text-[#1E3A8A]" />
                          Civil Service Competency-Level Performance
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                          {summaryData.competency_results.map((cr) => (
                            <div key={cr.competency} className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                              <div className="flex items-center justify-between">
                                <span className="font-bold text-xs text-slate-900">{cr.competency}</span>
                                <span
                                  className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                    cr.level === "Exemplary"
                                      ? "bg-emerald-100 text-emerald-800"
                                      : cr.level === "Proficient"
                                      ? "bg-blue-100 text-blue-800"
                                      : "bg-amber-100 text-amber-800"
                                  }`}
                                >
                                  {cr.level} ({cr.score}%)
                                </span>
                              </div>
                              <div className="mt-1.5 w-full bg-slate-200 h-1 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-[#1E3A8A]"
                                  style={{ width: `${cr.score}%` }}
                                />
                              </div>
                              <p className="mt-1.5 text-[10px] text-slate-500">{cr.description}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Strengths, Weaknesses & Recommended Upskilling */}
                    <div className="mt-6 pt-5 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-3 gap-4">
                      {summaryData.strengths && summaryData.strengths.length > 0 && (
                        <div className="p-3.5 rounded-lg bg-emerald-50/50 border border-emerald-200/80">
                          <h5 className="text-xs font-bold text-emerald-900 mb-2 flex items-center gap-1">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                            Demonstrated Strengths
                          </h5>
                          <ul className="space-y-1 text-xs text-emerald-800">
                            {summaryData.strengths.map((st, idx) => (
                              <li key={idx} className="flex items-start gap-1.5">
                                <span>•</span>
                                <span>{st}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {summaryData.weaknesses && summaryData.weaknesses.length > 0 && (
                        <div className="p-3.5 rounded-lg bg-amber-50/50 border border-amber-200/80">
                          <h5 className="text-xs font-bold text-amber-900 mb-2 flex items-center gap-1">
                            <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
                            Procedural Weaknesses
                          </h5>
                          <ul className="space-y-1 text-xs text-amber-800">
                            {summaryData.weaknesses.map((w, idx) => (
                              <li key={idx} className="flex items-start gap-1.5">
                                <span>•</span>
                                <span>{w}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {summaryData.recommended_upskilling && summaryData.recommended_upskilling.length > 0 && (
                        <div className="p-3.5 rounded-lg bg-blue-50/50 border border-blue-200/80">
                          <h5 className="text-xs font-bold text-[#1E3A8A] mb-2 flex items-center gap-1">
                            <BookOpen className="h-3.5 w-3.5 text-[#0D9488]" />
                            Recommended Upskilling Areas
                          </h5>
                          <ul className="space-y-1 text-xs text-blue-900">
                            {summaryData.recommended_upskilling.map((up, idx) => (
                              <li key={idx} className="flex items-start gap-1.5">
                                <span>•</span>
                                <span>{up}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    <div className="mt-5">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                        Key Administrative Takeaways
                      </h4>
                      <div className="space-y-1.5">
                        {summaryData.key_takeaways.map((takeaway, i) => (
                          <div key={i} className="flex items-start gap-2 text-xs text-slate-700">
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0 mt-0.5" />
                            <span>{takeaway}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Decision Trail Audit Table */}
                  <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
                    <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-[#1E3A8A]" />
                      Chronological Decision Audit Trail
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">
                      Inspection of each choice made and how follow-up branches were navigated:
                    </p>

                    <div className="mt-4 space-y-3">
                      {summaryData.decision_trail.map((node, i) => (
                        <div
                          key={i}
                          className={`p-4 rounded-xl border text-xs ${
                            node.is_optimal
                              ? "border-emerald-200 bg-emerald-50/30"
                              : "border-amber-200 bg-amber-50/30"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold uppercase tracking-wider text-[11px] text-slate-600">
                              Step {i + 1} • {node.stage_type === "root" ? "Root Scenario" : "Carryforward Consequence Branch"}
                            </span>
                            <span
                              className={`font-bold px-2 py-0.5 rounded text-[10px] ${
                                node.is_optimal
                                  ? "bg-emerald-100 text-emerald-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}
                            >
                              {node.is_optimal ? "Optimal Civil Service Action" : "Procedural Defect Triggered"}
                            </span>
                          </div>
                          <p className="font-semibold text-slate-900 mt-2 text-sm">{node.question_prompt}</p>
                          <div className="mt-2 p-2.5 rounded bg-white border border-slate-200">
                            <span className="font-bold text-[#1E3A8A]">Selected Option {node.selected_option_id}: </span>
                            {node.selected_option_text}
                          </div>
                          <div className="mt-2 text-slate-600">
                            <span className="font-semibold">Outcome: </span>
                            {node.consequence_summary}
                          </div>
                          <div className="mt-1 text-slate-500 italic">
                            <span className="font-semibold not-italic">Statutory Basis: </span>
                            {node.statutory_rationale}
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="mt-6 flex justify-end">
                      <button
                        onClick={() => startSession()}
                        className="inline-flex items-center gap-2 rounded-lg bg-[#1E3A8A] px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-[#1E3A8A]/90 transition-all cursor-pointer"
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                        Restart Inquiry
                      </button>
                    </div>
                  </div>
                </div>
              ) : currentQuestion ? (
                /* Active Question & MCQ View */
                <div className="space-y-6">
                  {trail.length > 0 && (
                    <div className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-xs">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                        Carryforward Progress Trail
                      </p>
                      <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
                        <span className="rounded-full bg-blue-50 px-2 py-0.5 font-semibold text-[#1E3A8A]">
                          Root Scenario
                        </span>
                        {trail.map((node, i) => (
                          <span key={`${node.question_id}-${i}`} className="flex items-center gap-1.5">
                            <ArrowRight className="h-3 w-3 text-slate-400" />
                            <span
                              className={`rounded-full px-2 py-0.5 font-semibold ${
                                node.is_optimal
                                  ? "bg-emerald-50 text-emerald-800"
                                  : "bg-amber-50 text-amber-800"
                              }`}
                            >
                              {node.stage_type === "root" ? "Branch Taken" : "Follow-up Remediation"} · {node.selected_option_id}
                            </span>
                          </span>
                        ))}
                        {lastAnswerResult?.is_satisfactory_terminal && (
                          <>
                            <ArrowRight className="h-3 w-3 text-slate-400" />
                            <span className="rounded-full bg-emerald-100 px-2 py-0.5 font-semibold text-emerald-800">
                              Satisfactorily Resolved
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                  )}
                  {/* Carryforward Status Indicator */}
                  <div
                    className={`rounded-xl border p-4 shadow-xs transition-all ${
                      currentQuestion.stage_type === "carryforward_branch"
                        ? "border-amber-300 bg-amber-50/70"
                        : "border-blue-200 bg-blue-50/40"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {currentQuestion.stage_type === "carryforward_branch" ? (
                          <ShieldAlert className="h-5 w-5 text-amber-600 animate-pulse" />
                        ) : (
                          <Scale className="h-5 w-5 text-[#1E3A8A]" />
                        )}
                        <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                          {currentQuestion.stage_type === "carryforward_branch"
                            ? "Carryforward Consequence Branch Active"
                            : "Primary Case Dilemma"}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        {currentQuestion.behavioral_competencies.map((comp, idx) => (
                          <span
                            key={idx}
                            className="rounded bg-white/80 px-2 py-0.5 text-[10px] font-bold text-slate-600 border border-slate-200"
                          >
                            {comp}
                          </span>
                        ))}
                      </div>
                    </div>

                    {currentQuestion.context_update && (
                      <p className="mt-2 text-xs text-slate-700 border-t border-amber-200/60 pt-2">
                        <span className="font-bold">Administrative Context Update: </span>
                        {currentQuestion.context_update}
                      </p>
                    )}
                  </div>

                  {/* Question Box */}
                  <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
                    <h2 className="text-base sm:text-lg font-bold text-slate-900 leading-relaxed">
                      {currentQuestion.prompt}
                    </h2>

                    {/* Options List */}
                    <div className="mt-6 space-y-3">
                      {currentQuestion.options.map((opt) => {
                        const isSelected = selectedOptionId === opt.option_id;
                        const isAnswered = lastAnswerResult !== null;
                        const isCorrect = opt.is_optimal;

                        let optionStyle = "border-slate-200 hover:border-[#1E3A8A]/50 hover:bg-slate-50";
                        if (isSelected && !isAnswered) {
                          optionStyle = "border-[#1E3A8A] bg-blue-50/50 ring-2 ring-[#1E3A8A]/20";
                        } else if (isAnswered) {
                          if (isCorrect) {
                            optionStyle = "border-emerald-400 bg-emerald-50/50 text-emerald-950 font-medium";
                          } else if (isSelected && !isCorrect) {
                            optionStyle = "border-amber-400 bg-amber-50/50 text-amber-950";
                          } else {
                            optionStyle = "border-slate-100 bg-slate-50/50 opacity-60";
                          }
                        }

                        return (
                          <div
                            key={opt.option_id}
                            onClick={() => !isAnswered && setSelectedOptionId(opt.option_id)}
                            className={`p-4 rounded-xl border transition-all cursor-pointer text-sm ${optionStyle}`}
                          >
                            <div className="flex items-start gap-3">
                              <span
                                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                                  isSelected
                                    ? "bg-[#1E3A8A] text-white"
                                    : "bg-slate-100 text-slate-700"
                                }`}
                              >
                                {opt.option_id}
                              </span>
                              <div className="flex-1">
                                <p className="leading-snug">{opt.text}</p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>

                    {/* Submit Action or Next Question Action */}
                    {!lastAnswerResult ? (
                      <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
                        <span className="text-xs text-slate-500">
                          Select the most procedurally defensible action according to civil service regulations.
                        </span>
                        <button
                          disabled={!selectedOptionId || isSubmitting}
                          onClick={submitAnswer}
                          className="inline-flex items-center gap-2 rounded-lg bg-[#1E3A8A] px-5 py-2.5 text-xs font-bold text-white shadow-xs hover:bg-[#1E3A8A]/90 disabled:opacity-40 transition-all cursor-pointer"
                        >
                          {isSubmitting ? "Evaluating..." : "Submit Procedural Decision"}
                          <ArrowRight className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    ) : (
                      /* Post-submission feedback banner */
                      <div className="mt-6 rounded-xl border p-4 text-xs space-y-3 bg-slate-50 border-slate-200">
                        <div className="flex items-center justify-between">
                          <span
                            className={`font-bold px-2.5 py-1 rounded text-xs inline-flex items-center gap-1.5 ${
                              lastAnswerResult.is_optimal
                                ? "bg-emerald-100 text-emerald-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {lastAnswerResult.is_optimal ? (
                              <>
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                Optimal Civil Service Choice
                              </>
                            ) : (
                              <>
                                <AlertTriangle className="h-3.5 w-3.5" />
                                Procedural Risk / Defect Incurred
                              </>
                            )}
                          </span>

                          <span className="text-slate-500 font-semibold">
                            Current Compliance: {lastAnswerResult.current_score}%
                          </span>
                        </div>

                        <div>
                          <p className="font-semibold text-slate-800">Consequence of Choice:</p>
                          <p className="text-slate-600 mt-0.5">{lastAnswerResult.consequence_summary}</p>
                        </div>

                        <div className="rounded bg-white p-2.5 border border-slate-200 text-slate-700">
                          <span className="font-bold text-[#1E3A8A]">Statutory Rationale: </span>
                          {lastAnswerResult.statutory_rationale}
                        </div>

                        {lastAnswerResult.carryforward_active ? (
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                            <span className="font-bold text-amber-800 flex items-center gap-1.5 text-xs">
                              <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
                              Next step: Consequential Carryforward Inquiry has been triggered.
                            </span>
                            <button
                              onClick={proceedToNextQuestion}
                              className="inline-flex items-center gap-1.5 rounded-xl bg-amber-600 px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-amber-700 transition-all cursor-pointer"
                            >
                              Address Follow-up Scenario
                              <ArrowRight className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        ) : (
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
                            <span className="font-bold text-emerald-800 flex items-center gap-1.5 text-xs">
                              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                              Case satisfactorily resolved under administrative due process!
                            </span>
                            <button
                              onClick={proceedToNextQuestion}
                              className="inline-flex items-center gap-1.5 rounded-xl navy-teal-gradient px-4 py-2 text-xs font-bold text-white shadow-sm hover:opacity-95 transition-all cursor-pointer"
                            >
                              {lastAnswerResult.session_completed ? "View Complete Assessment Summary" : "Advance to Next Case"}
                              <ArrowRight className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        )}

        {/* Tab 2: Government Document Corpus View */}
        {activeTab === "corpus" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900">Official Civil Service Document Repository</h2>
                <p className="text-xs text-slate-500">
                  Pre-seeded gazettes, office memorandums, circulars, and departmental inquiries:
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {corpus.map((doc) => (
                <div
                  key={doc.id}
                  className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="rounded bg-blue-50 px-2 py-0.5 text-[10px] font-bold uppercase text-[#1E3A8A]">
                        {doc.document_type}
                      </span>
                      <span className="text-[11px] text-slate-500 font-mono">{doc.date_of_issue}</span>
                    </div>
                    <h3 className="mt-2.5 text-base font-bold text-slate-900 leading-snug">{doc.title}</h3>
                    <p className="mt-1 text-xs text-slate-500">
                      <span className="font-semibold text-slate-700">Authority:</span> {doc.issuing_authority}
                    </p>
                    <p className="text-xs text-slate-500">
                      <span className="font-semibold text-slate-700">Ref:</span> {doc.document_number}
                    </p>

                    <div className="mt-3 p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs text-slate-700 font-mono">
                      {doc.statutory_reference}
                    </div>

                    <div className="mt-3">
                      <h4 className="text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                        Key Stakeholders
                      </h4>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {doc.key_stakeholders.map((s, idx) => (
                          <span key={idx} className="rounded bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                    <button
                      onClick={() => openDocumentInspector(doc.id)}
                      className="text-xs font-bold text-[#1E3A8A] hover:underline flex items-center gap-1 cursor-pointer"
                    >
                      <FileText className="h-3.5 w-3.5" />
                      Read Complete Instrument
                    </button>
                    <button
                      onClick={() => {
                        const matchedCase = cases.find((c) => c.document_id === doc.id);
                        if (matchedCase) {
                          setSelectedCaseId(matchedCase.id);
                          setActiveTab("cases");
                          startSession(matchedCase.id);
                        }
                      }}
                      className="rounded bg-slate-900 px-3 py-1.5 text-xs font-bold text-white hover:bg-slate-800 transition-all cursor-pointer"
                    >
                      Launch Case
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Custom Document Ingestion Studio */}
        {activeTab === "generator" && (
          <div className="max-w-3xl mx-auto rounded-2xl border border-slate-200 bg-white p-8 shadow-xs">
            <div className="flex items-center gap-2 text-[#0D9488]">
              <Sparkles className="h-5 w-5" />
              <span className="text-xs font-bold uppercase tracking-wider">AI Content Generation Pipeline</span>
            </div>
            <h2 className="mt-2 text-xl font-bold text-slate-900">
              Government Notice & Form Ingestion Studio
            </h2>
            <p className="mt-1 text-xs text-slate-600">
              Paste the text of any official notification, office memorandum, statutory form, or tribunal proceeding.
              The pipeline extracts the administrative conflict, identifies statutory references, and generates a
              multi-stage carryforward branching MCQ case.
            </p>

            <form onSubmit={handleGenerateCase} className="mt-6 space-y-4">
              {/* Course Anchoring Selector */}
              <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-4 space-y-2.5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <label className="block text-xs font-bold text-[#1E3A8A] uppercase tracking-wider">
                      Anchor Case to Database Course Curriculum (Optional)
                    </label>
                    <p className="text-[11px] text-slate-500">
                      Select an official course from the platform database to automatically inject its syllabus context and mapped statutory notices.
                    </p>
                  </div>
                  {selectedGenCourseId && (
                    <button
                      type="button"
                      onClick={() => handleLoadCourseNotice(selectedGenCourseId)}
                      className="shrink-0 px-3 py-1.5 rounded-lg bg-[#1E3A8A] text-white text-xs font-bold hover:bg-[#1E3A8A]/90 transition-all flex items-center gap-1.5 cursor-pointer shadow-2xs"
                    >
                      <Sparkles className="h-3.5 w-3.5 text-teal-300" />
                      Auto-Load Course Notice
                    </button>
                  )}
                </div>

                <select
                  value={selectedGenCourseId ?? ""}
                  onChange={(e) => {
                    const val = e.target.value ? parseInt(e.target.value, 10) : null;
                    setSelectedGenCourseId(val);
                    if (val) {
                      handleLoadCourseNotice(val);
                    }
                  }}
                  className="w-full rounded-lg border border-blue-200 bg-white px-3 py-2 text-xs font-medium text-slate-800 focus:border-[#1E3A8A] focus:outline-hidden cursor-pointer"
                >
                  <option value="">None (Independent General Government Scenario)</option>
                  {courses.map((c) => (
                    <option key={c.course_id} value={c.course_id}>
                      Course {c.course_id}: {c.title} — {c.organization}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700">Document Title</label>
                  <input
                    type="text"
                    required
                    value={genTitle}
                    onChange={(e) => setGenTitle(e.target.value)}
                    placeholder="e.g. O.M. on Timely Disposal of RTI First Appeals"
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-[#1E3A8A] focus:outline-hidden"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700">Document Instrument Type</label>
                  <select
                    value={genType}
                    onChange={(e) => setGenType(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-[#1E3A8A] focus:outline-hidden"
                  >
                    <option value="Notice">Official Notice / Office Memorandum</option>
                    <option value="Statutory Form">Statutory Form / Schedule</option>
                    <option value="Departmental Proceeding">Departmental Proceeding / Inquiry</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700">Issuing Ministry / Authority</label>
                  <input
                    type="text"
                    value={genAuthority}
                    onChange={(e) => setGenAuthority(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-[#1E3A8A] focus:outline-hidden"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700">Statutory Act / Rule Reference</label>
                  <input
                    type="text"
                    value={genReference}
                    onChange={(e) => setGenReference(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs focus:border-[#1E3A8A] focus:outline-hidden"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700">
                  Document Text (Notices, Clauses, Inquiries, or Articles of Charge)
                </label>
                <textarea
                  rows={8}
                  required
                  value={genText}
                  onChange={(e) => setGenText(e.target.value)}
                  placeholder="Paste the official notification, circular clauses, or inquiry text here..."
                  className="mt-1 w-full rounded-lg border border-slate-200 p-3 text-xs font-mono focus:border-[#1E3A8A] focus:outline-hidden"
                />
              </div>

              {genError && (
                <div className="p-3 rounded-lg bg-red-50 text-red-700 text-xs border border-red-200">
                  {genError}
                </div>
              )}

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#1E3A8A] px-5 py-2.5 text-xs font-bold text-white shadow-xs hover:bg-[#1E3A8A]/90 disabled:opacity-40 transition-all cursor-pointer"
                >
                  {isGenerating ? (
                    <>Generating Carryforward Decision Tree...</>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 text-[#0D9488]" />
                      Synthesize Carryforward Case Tree
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* Official Document Gazette Sheet Modal */}
      {showDocModal && inspectingDoc && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
          <div className="relative w-full max-w-2xl max-h-[85vh] rounded-2xl bg-white shadow-2xl border border-slate-300 flex flex-col">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50 rounded-t-2xl">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#1E3A8A] bg-blue-100/60 px-2 py-0.5 rounded">
                  {inspectingDoc.document_type}
                </span>
                <h3 className="mt-1 text-sm font-bold text-slate-900">{inspectingDoc.title}</h3>
              </div>
              <button
                onClick={() => setShowDocModal(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-200 hover:text-slate-700 transition-all cursor-pointer"
                aria-label="Close document modal"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 text-xs font-serif leading-relaxed text-slate-800">
              <div className="border border-slate-300 p-4 rounded-lg bg-amber-50/20 shadow-inner">
                <div className="text-center border-b border-slate-300 pb-2 mb-3">
                  <div className="font-bold text-slate-900 tracking-wider">GOVERNMENT OF INDIA</div>
                  <div className="text-[11px] text-slate-700">{inspectingDoc.issuing_authority}</div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">{inspectingDoc.document_number}</div>
                </div>

                <div className="whitespace-pre-line text-slate-800 text-xs font-mono leading-relaxed">
                  {inspectingDoc.full_text}
                </div>
              </div>
            </div>

            <div className="p-4 border-t border-slate-200 bg-slate-50 rounded-b-2xl flex justify-end">
              <button
                onClick={() => setShowDocModal(false)}
                className="rounded-lg bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800 cursor-pointer"
              >
                Close Document
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
