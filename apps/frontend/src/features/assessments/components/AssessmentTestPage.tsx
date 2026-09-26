"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Award,
  Clock,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  RotateCcw,
  FileCheck2,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fetchApi } from "@/lib/api";
import { AssessmentDetail, CertificateItem } from "@/lib/types";
import { CertificateModal } from "@/components/certificate/CertificateModal";
import { useI18n } from "@/lib/i18n";
import confetti from "canvas-confetti";

function formatClock(totalSeconds: number) {
  return `${Math.floor(totalSeconds / 60)}:${String(totalSeconds % 60).padStart(2, "0")}`;
}

export default function AssessmentTestPage() {
  const { assessmentId } = useParams();
  const router = useRouter();
  const { t } = useI18n();

  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [testStarted, setTestStarted] = useState(false);
  const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
  const [userAnswers, setUserAnswers] = useState<Record<string, number>>({});
  const [submitting, setSubmitting] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [deadline, setDeadline] = useState<number | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [confirmingSubmit, setConfirmingSubmit] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Certificate modal state
  const [showCertModal, setShowCertModal] = useState(false);
  const [certificateData, setCertificateData] = useState<CertificateItem | null>(null);

  useEffect(() => {
    if (!assessmentId) return;
    fetchApi<AssessmentDetail>(`/assessments/${assessmentId}`)
      .then((data) => setAssessment(data))
      .catch((err) => console.error("Error loading assessment:", err))
      .finally(() => setLoading(false));
  }, [assessmentId]);

  useEffect(() => {
    if (!deadline || results) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [deadline, results]);

  const secondsLeft = deadline ? Math.max(0, Math.ceil((deadline - now) / 1000)) : null;

  // Time is up: submit whatever has been answered.
  useEffect(() => {
    if (secondsLeft === 0 && !results && !submitting) handleSubmit();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [secondsLeft]);

  const startTest = () => {
    if (!assessment) return;
    setDeadline(Date.now() + assessment.time_limit_minutes * 60_000);
    setNow(Date.now());
    setTestStarted(true);
  };

  const handleSelectOption = (questionId: number, optionIdx: number) => {
    setUserAnswers((prev) => ({
      ...prev,
      [String(questionId)]: optionIdx,
    }));
  };

  const handleSubmit = async () => {
    if (!assessment) return;
    setConfirmingSubmit(false);
    setSubmitError(null);
    setSubmitting(true);

    try {
      const data = await fetchApi(`/assessments/${assessment.id}/submit`, {
        method: "POST",
        body: JSON.stringify({ answers: userAnswers }),
      });

      setResults(data);

      if (data.passed) {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 },
        });

        // Prepare certificate data for instant preview
        setCertificateData({
          certificate_id: data.certificate_id,
          course_id: data.course_id,
          course_title: data.course_title,
          organization: data.organization,
          instructor: "National Faculty Panel",
          recipient_name: data.recipient_name,
          issued_date: new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }),
          score_percent: data.score_percent,
          verification_status: "Verified Official Credential",
          duration_hours: data.duration_hours,
        });
      }
    } catch (err: any) {
      setSubmitError(err?.message || "Your answers could not be submitted. Check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetake = () => {
    setUserAnswers({});
    setResults(null);
    setCurrentQuestionIdx(0);
    startTest();
  };

  if (loading) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-4 border-slate-200 border-t-amber-600 animate-spin" />
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className="p-12 text-center">
        <p className="text-sm text-slate-500">Assessment not found.</p>
      </div>
    );
  }

  // STAGE 3: RESULTS SCREEN (Per Miro: Results -> pass | fail -> Analytics)
  if (results) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12 space-y-6">
        <Card className="border-slate-200 bg-white shadow-md overflow-hidden">
          <div
            className={`p-8 text-center ${
              results.passed
                ? "bg-gradient-to-b from-emerald-50 to-white border-b border-emerald-100"
                : "bg-gradient-to-b from-rose-50 to-white border-b border-rose-100"
            }`}
          >
            <div
              className={`h-16 w-16 rounded-full mx-auto flex items-center justify-center mb-4 ${
                results.passed
                  ? "bg-emerald-100 text-emerald-700"
                  : "bg-rose-100 text-rose-700"
              }`}
            >
              {results.passed ? <CheckCircle2 className="h-10 w-10" /> : <XCircle className="h-10 w-10" />}
            </div>

            <Badge variant={results.passed ? "success" : "default"} className="mb-2">
              {results.passed ? "Examination Passed" : "Retake Permitted"}
            </Badge>

            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
              {results.passed ? t("assess.congratulations") : t("assess.tryAgain")}
            </h1>

            <p className="text-xs text-slate-500 mt-1">{assessment.title}</p>

            <div className="mt-6 flex justify-center items-center gap-6">
              <div className="text-center">
                <p className="text-3xl font-extrabold text-slate-900">{results.score_percent}%</p>
                <p className="text-[11px] text-slate-500 uppercase font-semibold">Your Score</p>
              </div>
              <div className="h-10 w-px bg-slate-200" />
              <div className="text-center">
                <p className="text-3xl font-extrabold text-slate-900">{results.pass_threshold_percent}%</p>
                <p className="text-[11px] text-slate-500 uppercase font-semibold">Pass Threshold</p>
              </div>
              <div className="h-10 w-px bg-slate-200" />
              <div className="text-center">
                <p className="text-3xl font-extrabold text-slate-900">
                  {results.correct_answers}/{results.total_questions}
                </p>
                <p className="text-[11px] text-slate-500 uppercase font-semibold">Questions Correct</p>
              </div>
            </div>

            <div className="mt-8 flex flex-wrap justify-center gap-3">
              {results.passed && (
                <Button
                  onClick={() => setShowCertModal(true)}
                  className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold shadow-xs cursor-pointer"
                >
                  <Award className="h-4 w-4 mr-1.5 text-amber-400" />
                  {t("assess.viewCertificate")}
                </Button>
              )}
              <Button
                variant="outline"
                onClick={handleRetake}
                className="text-xs text-slate-700"
              >
                <RotateCcw className="h-3.5 w-3.5 mr-1" />
                {t("assess.retake")}
              </Button>
              <a href="/progress">
                <Button variant="outline" className="text-xs">
                  View Full Analytics Record <ArrowRight className="h-3.5 w-3.5 ml-1" />
                </Button>
              </a>
            </div>
          </div>

          {/* Question Breakdown with Explanations */}
          <CardContent className="p-6 space-y-4">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Detailed Question Analysis
            </h3>

            <div className="space-y-3">
              {results.breakdown.map((item: any, idx: number) => (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border text-xs leading-relaxed ${
                    item.is_correct
                      ? "bg-emerald-50/40 border-emerald-200"
                      : "bg-rose-50/40 border-rose-200"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <p className="font-bold text-slate-900">
                      Q{idx + 1}: {item.question_text}
                    </p>
                    <Badge variant={item.is_correct ? "success" : "default"} className="inline-flex items-center gap-1">
                      {item.is_correct ? (
                        <>
                          <CheckCircle2 className="h-3 w-3" /> Correct
                        </>
                      ) : (
                        <>
                          <XCircle className="h-3 w-3" /> Incorrect
                        </>
                      )}
                    </Badge>
                  </div>

                  <div className="space-y-1 text-slate-600">
                    <p>
                      <span className="font-semibold">Your Answer:</span>{" "}
                      {item.selected_option !== null && item.options[item.selected_option]
                        ? item.options[item.selected_option]
                        : "No answer chosen"}
                    </p>
                    {!item.is_correct && (
                      <p className="text-emerald-800 font-semibold">
                        Correct Answer: {item.options[item.correct_option]}
                      </p>
                    )}
                  </div>

                  {item.explanation && (
                    <p className="mt-2 pt-2 border-t border-slate-200/60 text-[11px] text-slate-500 italic">
                      Regulatory context: {item.explanation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Certificate Modal Popup */}
        <CertificateModal
          certificate={certificateData}
          open={showCertModal}
          onClose={() => setShowCertModal(false)}
        />
      </div>
    );
  }

  // STAGE 1: INSTRUCTIONS SCREEN (Per Miro: Instructions)
  if (!testStarted) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 space-y-6">
        <Card className="border-slate-200 bg-white shadow-sm">
          <CardHeader className="text-center pb-4 border-b border-slate-100">
            <div className="inline-flex h-12 w-12 rounded-full bg-amber-50 border border-amber-300 text-amber-700 items-center justify-center mx-auto mb-2">
              <Award className="h-6 w-6" />
            </div>
            <CardTitle className="text-xl font-bold text-slate-900">
              {assessment.title}
            </CardTitle>
            <CardDescription className="text-xs">
              Accredited by {assessment.organization} • Official Competency Evaluation
            </CardDescription>
          </CardHeader>

          <CardContent className="p-6 space-y-5 text-xs text-slate-600 leading-relaxed">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 grid grid-cols-3 gap-3 text-center">
              <div>
                <p className="text-slate-400 text-[10px] uppercase font-bold">Total Questions</p>
                <p className="text-base font-bold text-slate-900">{assessment.total_questions} MCQs</p>
              </div>
              <div>
                <p className="text-slate-400 text-[10px] uppercase font-bold">Time Limit</p>
                <p className="text-base font-bold text-slate-900">{assessment.time_limit_minutes} Mins</p>
              </div>
              <div>
                <p className="text-slate-400 text-[10px] uppercase font-bold">Pass Standard</p>
                <p className="text-base font-bold text-emerald-700">{assessment.pass_threshold_percent}%</p>
              </div>
            </div>

            <div className="space-y-2">
              <h4 className="font-bold text-slate-900">Examination Instructions:</h4>
              <ul className="list-disc pl-5 space-y-1.5 text-slate-600">
                <li>Questions test conceptual rigor, sampling methods, and official standards.</li>
                <li>Each question has one uniquely correct option. Unanswered questions are marked incorrect.</li>
                <li>The timer starts when you begin. Your answers are submitted automatically when time runs out.</li>
                <li>You may review and change your selected answers prior to final submission.</li>
                <li>Under Phase 0 policy, unlimited attempts are permitted, and your best verified score is preserved on your official profile.</li>
              </ul>
            </div>

            {assessment.last_attempt && (
              <div className="p-3 bg-amber-50/60 border border-amber-200 rounded-lg text-[11px] text-amber-900 flex items-center justify-between">
                <span>Previous Attempt: {assessment.last_attempt.score_percent}% ({assessment.last_attempt.passed ? "Passed" : "Not Met"})</span>
                <span className="text-slate-500">{assessment.last_attempt.submitted_at}</span>
              </div>
            )}
          </CardContent>

          <CardFooter className="flex justify-between border-t border-slate-100 pt-4">
            <a href={`/courses/${assessment.course_id}`}>
              <Button variant="outline" size="sm" className="text-xs">
                Back to Course
              </Button>
            </a>
            <Button
              size="sm"
              onClick={startTest}
              className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold px-6 shadow-xs cursor-pointer"
            >
              {t("assess.startAssessment")} <ArrowRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  // STAGE 2: QUESTIONS TEST RUNNER (Per Miro: Questions -> Submit)
  const question = assessment.questions[currentQuestionIdx];
  const isLastQuestion = currentQuestionIdx === assessment.questions.length - 1;
  const answeredCount = Object.keys(userAnswers).length;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* Test Top Bar */}
      <div className="flex items-center justify-between gap-3 bg-white p-3.5 sm:p-4 rounded-xl border border-slate-200 shadow-xs">
        <div className="min-w-0 flex-1">
          <h3 className="text-xs font-bold text-slate-900 truncate max-w-[180px] sm:max-w-md">
            {assessment.title}
          </h3>
          <p className="text-[10px] sm:text-[11px] text-slate-500">
            Question {currentQuestionIdx + 1} of {assessment.questions.length} • {answeredCount} answered
          </p>
        </div>
        <div
          role="timer"
          aria-label="Time remaining"
          className={`flex items-center gap-1.5 sm:gap-2 text-[11px] sm:text-xs font-semibold px-2.5 sm:px-3 py-1 rounded-lg shrink-0 ${
            secondsLeft !== null && secondsLeft <= 60 ? "bg-rose-50 text-rose-700" : "bg-slate-100 text-slate-700"
          }`}
        >
          <Clock className="h-3.5 w-3.5 text-amber-600 shrink-0" aria-hidden="true" />
          <span className="tabular-nums">{formatClock(secondsLeft ?? assessment.time_limit_minutes * 60)}</span>
        </div>
      </div>

      {/* Active Question Card */}
      <Card className="border-slate-200 bg-white shadow-xs">
        <CardHeader className="pb-4">
          <span className="text-[11px] font-bold text-amber-700 uppercase tracking-wide">
            Question {currentQuestionIdx + 1}
          </span>
          <CardTitle className="text-base font-bold text-slate-900 mt-1 leading-snug">
            {question.text}
          </CardTitle>
        </CardHeader>

        <CardContent className="space-y-2.5">
          {question.options.map((opt, optIdx) => {
            const isSelected = userAnswers[String(question.id)] === optIdx;
            return (
              <button
                key={optIdx}
                type="button"
                onClick={() => handleSelectOption(question.id, optIdx)}
                className={`w-full p-3.5 rounded-xl border text-left text-xs font-medium transition-all cursor-pointer flex items-center gap-3 ${
                  isSelected
                    ? "bg-[#1E3A8A] text-white border-[#1E3A8A] shadow-xs"
                    : "bg-white text-slate-800 border-slate-200 hover:bg-slate-50"
                }`}
              >
                <span
                  className={`h-5 w-5 rounded-full text-[10px] font-bold flex items-center justify-center shrink-0 ${
                    isSelected ? "bg-amber-500 text-slate-950" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {String.fromCharCode(65 + optIdx)}
                </span>
                <span>{opt}</span>
              </button>
            );
          })}
        </CardContent>

        {/* Navigation & Submit Footer */}
        <CardFooter className="flex items-center justify-between border-t border-slate-100 pt-4">
          <Button
            variant="outline"
            size="sm"
            disabled={currentQuestionIdx === 0}
            onClick={() => setCurrentQuestionIdx((p) => p - 1)}
            className="text-xs"
          >
            Previous
          </Button>

          <div className="flex gap-2">
            {!isLastQuestion ? (
              <Button
                size="sm"
                onClick={() => setCurrentQuestionIdx((p) => p + 1)}
                className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs px-5 cursor-pointer"
              >
                Next Question <ArrowRight className="h-3.5 w-3.5 ml-1" />
              </Button>
            ) : (
              <Button
                size="sm"
                onClick={() =>
                  answeredCount < assessment.questions.length && !confirmingSubmit
                    ? setConfirmingSubmit(true)
                    : handleSubmit()
                }
                disabled={submitting}
                className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold px-6 shadow-xs"
              >
                {submitting ? "Grading..." : t("assess.submit")}
              </Button>
            )}
          </div>
        </CardFooter>
      </Card>

      {confirmingSubmit && (
        <div role="alertdialog" aria-live="polite" className="flex flex-col gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4 text-xs text-amber-950 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-pretty">
            {assessment.questions.length - answeredCount} of {assessment.questions.length} questions are unanswered and will be marked incorrect.
          </p>
          <div className="flex shrink-0 gap-2">
            <Button variant="outline" size="sm" className="text-xs" onClick={() => setConfirmingSubmit(false)}>
              Review answers
            </Button>
            <Button size="sm" className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs" onClick={handleSubmit} disabled={submitting}>
              Submit anyway
            </Button>
          </div>
        </div>
      )}

      {submitError && (
        <div role="alert" className="flex items-start gap-2 rounded-xl border border-rose-300 bg-rose-50 p-4 text-xs text-rose-900">
          <AlertCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
          <p className="text-pretty">{submitError}</p>
        </div>
      )}

      {/* Question Quick Jump Grid */}
      <div className="flex flex-wrap items-center gap-2 p-3 bg-white rounded-xl border border-slate-200 text-xs">
        <span className="text-slate-400 font-semibold mr-1">Questions:</span>
        {assessment.questions.map((q, idx) => {
          const isAnswered = userAnswers[String(q.id)] !== undefined;
          const isCurrent = idx === currentQuestionIdx;
          return (
            <button
              key={q.id}
              onClick={() => setCurrentQuestionIdx(idx)}
              className={`h-7 w-7 rounded-lg text-xs font-bold transition-colors cursor-pointer ${
                isCurrent
                  ? "bg-[#1E3A8A] text-white ring-2 ring-blue-300"
                  : isAnswered
                  ? "bg-emerald-100 text-emerald-800"
                  : "bg-slate-100 text-slate-600 hover:bg-slate-200"
              }`}
            >
              {idx + 1}
            </button>
          );
        })}
      </div>
    </div>
  );
}
