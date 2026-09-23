"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  AlertCircle,
  ArrowLeft,
  Brain,
  Camera,
  CameraOff,
  Clock,
  Loader2,
  Mic,
  MicOff,
  Play,
  Send,
  ShieldCheck,
  Square,
  Volume2,
  VolumeX,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ApiError, fetchApi } from "@/lib/api";
import { useAuth } from "@/lib/auth/AuthContext";
import { useInterviewMedia } from "@/features/behavioural/hooks/useInterviewMedia";
import { countFillers, useSpeechCapture } from "@/features/behavioural/hooks/useSpeechCapture";
import { useBrowserVoice } from "@/features/behavioural/hooks/useBrowserVoice";
import { InterviewReport } from "@/features/behavioural/components/InterviewReport";
import type {
  BehaviouralCourse,
  InterviewReportData,
  InterviewStartResponse,
  InterviewTurnResponse,
} from "@/features/behavioural/interview-types";

const TOTAL_QUESTIONS = 6;
const DURATIONS = [25, 30, 35];

type Stage = "setup" | "room" | "concluding" | "report";

interface ChatMessage {
  role: "board" | "officer";
  text: string;
  tags?: string[];
  note?: string | null;
  source?: string;
}

function errorMessage(err: unknown, fallback: string) {
  if (err instanceof ApiError && err.status === 404) {
    return "This interview session is no longer available on the server, which can happen after a restart. Start a new interview.";
  }
  return err instanceof Error && err.message ? err.message : fallback;
}

function formatClock(totalSeconds: number) {
  return `${Math.floor(totalSeconds / 60)}:${String(totalSeconds % 60).padStart(2, "0")}`;
}

function percentOrStatus(value: number | null, live: boolean) {
  if (value !== null) return `${value}%`;
  return live ? "Measuring..." : "Not captured";
}

function SignalRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2">
      <dt className="text-slate-600">{label}</dt>
      <dd className="font-semibold tabular-nums text-slate-900">{value}</dd>
    </div>
  );
}

function IconToggle({
  on,
  onClick,
  disabled,
  onLabel,
  offLabel,
  OnIcon,
  OffIcon,
}: {
  on: boolean;
  onClick: () => void;
  disabled?: boolean;
  onLabel: string;
  offLabel: string;
  OnIcon: LucideIcon;
  OffIcon: LucideIcon;
}) {
  const Icon = on ? OnIcon : OffIcon;
  const label = on ? onLabel : offLabel;
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={on}
      aria-label={label}
      title={label}
      className={`inline-flex size-9 items-center justify-center rounded-lg transition-colors disabled:opacity-40 ${
        on ? "bg-white/15 text-white hover:bg-white/25" : "bg-rose-600 text-white hover:bg-rose-500"
      }`}
    >
      <Icon className="size-4" aria-hidden="true" />
    </button>
  );
}

export default function LiveInterviewPage() {
  const { user } = useAuth();
  const media = useInterviewMedia();
  const [draft, setDraft] = useState("");
  const voice = useBrowserVoice();
  const speech = useSpeechCapture(setDraft);

  const [stage, setStage] = useState<Stage>("setup");
  const [courses, setCourses] = useState<BehaviouralCourse[]>([]);
  const [coursesLoading, setCoursesLoading] = useState(true);
  const [courseId, setCourseId] = useState<number | null>(null);
  const [courseFromUrl, setCourseFromUrl] = useState<number | null>(null);
  const [officerName, setOfficerName] = useState("");
  const [duration, setDuration] = useState(30);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [phaseName, setPhaseName] = useState("");
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [voiceOn, setVoiceOn] = useState(true);
  const [elapsed, setElapsed] = useState(0);
  const [lastPace, setLastPace] = useState<number | null>(null);
  const [confirmEnd, setConfirmEnd] = useState(false);
  const [report, setReport] = useState<InterviewReportData | null>(null);

  const startedAtRef = useRef(0);
  const threadRef = useRef<HTMLDivElement>(null);
  const speechHandoffRef = useRef(0);

  useEffect(() => {
    const param = Number(new URLSearchParams(window.location.search).get("courseId"));
    const fromUrl = Number.isInteger(param) && param > 0 ? param : null;
    setCourseFromUrl(fromUrl);
    fetchApi<BehaviouralCourse[]>("/behavioural/courses?behavioural_only=true")
      .then((list) => {
        setCourses(list);
        setCourseId(fromUrl && list.some((c) => c.course_id === fromUrl) ? fromUrl : (list[0]?.course_id ?? null));
      })
      .catch(() => setError("Behavioural courses could not be loaded. Check that the backend is running."))
      .finally(() => setCoursesLoading(false));
  }, []);

  useEffect(() => {
    if (user?.full_name) setOfficerName((current) => current || user.full_name);
  }, [user]);

  useEffect(() => {
    if (stage !== "room") return;
    const id = window.setInterval(() => setElapsed(Math.floor((Date.now() - startedAtRef.current) / 1000)), 1000);
    return () => window.clearInterval(id);
  }, [stage]);

  useEffect(() => {
    const thread = threadRef.current;
    if (thread) thread.scrollTop = thread.scrollHeight;
  }, [messages, submitting]);

  const speak = async (text: string, force = false) => {
    // Stop dictation so the interviewer's voice is not transcribed as the answer.
    speech.stop();
    speechHandoffRef.current += 1;
    if (voiceOn || force) await voice.speak(text);
  };

  const conclude = async () => {
    if (!sessionId) return;
    speechHandoffRef.current += 1;
    speech.stop();
    media.stop();
    setConfirmEnd(false);
    setError(null);
    setStage("concluding");
    try {
      const result = await fetchApi<InterviewReportData>(`/behavioural/interview/${sessionId}/end`, { method: "POST" });
      setReport(result);
      setStage("report");
    } catch (err) {
      setError(errorMessage(err, "The assessment report could not be generated."));
    }
  };

  const handleStart = async () => {
    if (!courseId) return;
    setError(null);
    setStarting(true);
    try {
      // The interview still runs if camera access is declined; video signals are simply not captured.
      await media.start();
      const res = await fetchApi<InterviewStartResponse>("/behavioural/interview/start", {
        method: "POST",
        body: JSON.stringify({
          course_id: courseId,
          officer_name: officerName.trim() || "Officer",
          target_duration_minutes: duration,
        }),
      });
      setSessionId(res.session_id);
      setMessages([{ role: "board", text: res.initial_ai_question }]);
      setPhaseName(res.current_phase);
      setDraft("");
      setLastPace(null);
      setReport(null);
      startedAtRef.current = Date.now();
      setElapsed(0);
      media.resetTurn();
      setStage("room");
      void speak(res.initial_ai_question);
    } catch (err) {
      media.stop();
      setError(errorMessage(err, "The interview could not be started."));
    } finally {
      setStarting(false);
    }
  };

  const handleSubmit = async () => {
    if (!sessionId || submitting) return;
    speechHandoffRef.current += 1;
    voice.stop();
    // Wait for the last recorded clip to be transcribed before sending.
    const answer = (speech.listening || speech.busy ? await speech.finish() : draft).trim();
    if (!answer) return;

    const dictatedWords = speech.takeDictatedWords();
    const turn = media.takeTurnMetrics();
    const words = answer.split(/\s+/).length;
    const spoken = dictatedWords >= words / 2;
    const pace =
      spoken && turn.speaking_seconds !== null && turn.speaking_seconds >= 5
        ? Math.round(Math.min(260, Math.max(40, dictatedWords / (turn.speaking_seconds / 60))))
        : null;

    setSubmitting(true);
    setError(null);
    setMessages((current) => [...current, { role: "officer", text: answer }]);
    setDraft("");
    try {
      const res = await fetchApi<InterviewTurnResponse>("/behavioural/interview/turn", {
        method: "POST",
        body: JSON.stringify({
          session_id: sessionId,
          officer_response: answer,
          elapsed_seconds: Math.floor((Date.now() - startedAtRef.current) / 1000),
          input_mode: spoken ? "voice" : "typed",
          speaking_pace_wpm: pace,
          speaking_seconds: spoken ? turn.speaking_seconds : null,
          filler_words_count: spoken ? countFillers(answer) : null,
          pauses_count: spoken ? turn.pauses_count : null,
          face_presence_percent: turn.face_presence_percent,
          eye_contact_percent: turn.eye_contact_percent,
          posture_stability_score: turn.posture_stability_score,
          head_movement_rate: turn.head_movement_rate,
        }),
      });
      if (pace !== null) setLastPace(pace);
      setMessages((current) => {
        const next = [...current];
        const last = next[next.length - 1];
        next[next.length - 1] = { ...last, tags: res.detected_competencies, note: res.acknowledgement_note };
        return [...next, { role: "board", text: res.ai_question, source: res.ai_provider }];
      });
      setPhaseName(res.phase_name);
      void speak(res.ai_question);
      if (res.is_final_turn) await conclude();
    } catch (err) {
      setMessages((current) => current.slice(0, -1));
      setDraft(answer);
      setError(errorMessage(err, "Your answer could not be sent. Try again."));
    } finally {
      setSubmitting(false);
    }
  };

  const restart = () => {
    speechHandoffRef.current += 1;
    media.stop();
    speech.stop();
    voice.stop();
    setStage("setup");
    setSessionId(null);
    setMessages([]);
    setReport(null);
    setError(null);
  };

  const backHref = courseFromUrl ? `/courses/${courseFromUrl}` : "/competency/behavioural";
  const backLabel = courseFromUrl ? "Back to course" : "Behavioural competencies";
  const selectedCourse = courses.find((c) => c.course_id === courseId);
  const answered = messages.filter((m) => m.role === "officer").length;
  const draftWords = draft.trim() ? draft.trim().split(/\s+/).length : 0;
  const live = media.status === "live";

  const cameraMessage =
    media.status === "denied"
      ? "Camera access was blocked, so video signals are not captured. You can still answer."
      : media.status === "unavailable"
        ? "No camera is available, so video signals are not captured."
        : live
          ? "Camera is off."
          : "Camera is off.";

  const faceLabel =
    media.analyser === "loading"
      ? "Loading face analysis"
      : media.analyser === "unavailable"
        ? "Face analysis unavailable"
        : media.faceVisible === null
          ? "Starting analysis"
          : !media.faceVisible
            ? "Face not detected"
            : media.facingCamera === false
              ? "Face in frame, looking away"
              : "Face in frame";

  return (
    <div className="min-h-[calc(100vh-65px)] bg-slate-50">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Link
            href={backHref}
            onClick={() => media.stop()}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900"
          >
            <ArrowLeft className="size-3.5" aria-hidden="true" />
            {backLabel}
          </Link>

          {stage === "room" &&
            (confirmEnd ? (
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="text-slate-600">
                  End now and score {answered} {answered === 1 ? "answer" : "answers"}?
                </span>
                <Button size="sm" variant="outline" onClick={() => setConfirmEnd(false)}>
                  Keep going
                </Button>
                <Button size="sm" variant="danger" onClick={() => void conclude()}>
                  End interview
                </Button>
              </div>
            ) : (
              <Button size="sm" variant="outline" onClick={() => setConfirmEnd(true)} disabled={submitting}>
                <Square className="size-3.5" aria-hidden="true" />
                End interview
              </Button>
            ))}
        </div>

        <header className="hero-gradient relative left-1/2 mt-3 w-screen -translate-x-1/2 overflow-hidden px-4 py-12 text-white sm:px-6 sm:py-16 lg:px-8">
          <div className="hero-mesh pointer-events-none absolute inset-0 opacity-40" aria-hidden="true" />
          <div className="relative mx-auto max-w-7xl">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-teal-200">Behavioural &amp; managerial competencies</p>
          <h1 className="mt-2 text-3xl font-bold text-balance sm:text-4xl">Oral Board Interview</h1>
          <p className="mt-3 max-w-3xl text-sm text-pretty leading-relaxed text-white/75 sm:text-base">
            {stage === "setup"
              ? "Practise a structured spoken response, receive evidence-led feedback, and build confidence for a real interview board."
              : selectedCourse?.title}
          </p>
          </div>
        </header>

        {error && stage !== "concluding" && (
          <div role="alert" className="mt-4 flex items-start gap-2 rounded-xl border border-rose-300 bg-rose-50 p-3 text-sm text-rose-900">
            <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" />
            <p className="text-pretty">{error}</p>
          </div>
        )}

        {stage === "setup" && (
          <div className="mt-6 grid gap-6 lg:grid-cols-5">
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs lg:col-span-3">
              <h2 className="text-base font-semibold text-slate-900">Set up your interview</h2>
              <div className="mt-5 space-y-5">
                <div>
                  <label htmlFor="interview-course" className="block text-xs font-semibold text-slate-700">
                    Course
                  </label>
                  <select
                    id="interview-course"
                    value={courseId ?? ""}
                    onChange={(e) => setCourseId(Number(e.target.value))}
                    disabled={coursesLoading || courses.length === 0}
                    className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 focus:border-[#1E3A8A] focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]/20"
                  >
                    {coursesLoading && <option value="">Loading behavioural courses...</option>}
                    {courses.map((c) => (
                      <option key={c.course_id} value={c.course_id}>
                        {c.title}
                      </option>
                    ))}
                  </select>
                  {selectedCourse?.overview && (
                    <p className="mt-1.5 text-xs text-pretty text-slate-500">{selectedCourse.overview}</p>
                  )}
                </div>

                <div className="grid gap-5 sm:grid-cols-2">
                  <div>
                    <label htmlFor="interview-name" className="block text-xs font-semibold text-slate-700">
                      Your name
                    </label>
                    <input
                      id="interview-name"
                      value={officerName}
                      onChange={(e) => setOfficerName(e.target.value)}
                      autoComplete="name"
                      className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 focus:border-[#1E3A8A] focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]/20"
                    />
                  </div>
                  <fieldset>
                    <legend className="block text-xs font-semibold text-slate-700">Planned length</legend>
                    <div className="mt-1.5 grid grid-cols-3 gap-2">
                      {DURATIONS.map((d) => (
                        <label
                          key={d}
                          className={`cursor-pointer rounded-lg border px-2 py-2.5 text-center text-sm font-medium transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-[#1E3A8A]/30 ${
                            duration === d
                              ? "border-[#1E3A8A] bg-blue-50 text-[#1E3A8A]"
                              : "border-slate-300 text-slate-700 hover:bg-slate-50"
                          }`}
                        >
                          <input
                            type="radio"
                            name="interview-duration"
                            value={d}
                            checked={duration === d}
                            onChange={() => setDuration(d)}
                            className="sr-only"
                          />
                          {d} min
                        </label>
                      ))}
                    </div>
                  </fieldset>
                </div>

                <Button size="lg" className="w-full" onClick={() => void handleStart()} disabled={starting || !courseId}>
                  {starting ? (
                    <Loader2 className="size-4 animate-spin" aria-hidden="true" />
                  ) : (
                    <Play className="size-4" aria-hidden="true" />
                  )}
                  {starting
                    ? media.status === "requesting"
                      ? "Waiting for camera and microphone permission..."
                      : "Starting interview..."
                    : "Start interview"}
                </Button>
                <p className="text-xs text-pretty text-slate-500">
                  Your browser will ask for camera and microphone access. If you decline, the interview still runs and you
                  can type your answers.
                </p>
              </div>
            </section>

            <aside className="space-y-4 lg:col-span-2">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
                <h2 className="text-sm font-semibold text-slate-900">How it works</h2>
                <ol className="mt-3 space-y-3 text-sm text-slate-600">
                  {[
                    `The board asks ${TOTAL_QUESTIONS} questions, moving from the course itself to planning, leadership, ethics, change and judgement.`,
                    "Answer aloud with dictation or type. The board member responds to what you actually said.",
                    "At the end you get scores for seven competencies with evidence taken from your answers.",
                  ].map((step, i) => (
                    <li key={i} className="flex gap-3">
                      <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-[#1E3A8A] text-xs font-semibold text-white">
                        {i + 1}
                      </span>
                      <span className="text-pretty">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
              <div className="rounded-2xl border border-blue-100 bg-blue-50/60 p-5">
                <h2 className="flex items-center gap-1.5 text-sm font-semibold text-[#1E3A8A]">
                  <ShieldCheck className="size-4" aria-hidden="true" />
                  Privacy
                </h2>
                <ul className="mt-2 list-disc space-y-1.5 pl-4 text-xs text-pretty text-slate-700">
                  <li>Video is analysed in your browser and never uploaded. Only summary numbers are sent.</li>
                  <li>Use Chrome or Edge for browser speech recognition and the board member&apos;s spoken questions.</li>
                  <li>Signals describe observable delivery only and are not used to judge emotion or character.</li>
                  <li>Camera and microphone switch off when the interview ends or you leave this page.</li>
                </ul>
              </div>
            </aside>
          </div>
        )}

        {stage === "room" && (
          <div className="mt-6 grid gap-5 lg:grid-cols-12">
            <div className="space-y-4 lg:col-span-5">
              <div className="relative aspect-video overflow-hidden rounded-2xl bg-slate-900 shadow-sm">
                {live && media.cameraOn ? (
                  <video
                    ref={media.attachVideo}
                    autoPlay
                    playsInline
                    muted
                    aria-label="Your camera preview"
                    className="size-full -scale-x-100 object-cover"
                  />
                ) : (
                  <div className="flex size-full flex-col items-center justify-center gap-2 p-6 text-center text-slate-400">
                    <CameraOff className="size-10" aria-hidden="true" />
                    <p className="text-sm text-pretty">{cameraMessage}</p>
                  </div>
                )}

                <div className="absolute left-3 top-3 flex flex-wrap gap-2">
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-black/60 px-2.5 py-1 text-[11px] font-medium text-white">
                    <span className={`size-2 rounded-full ${live ? "bg-emerald-400" : "bg-slate-400"}`} aria-hidden="true" />
                    {live ? "Live" : "Offline"}
                  </span>
                  {live && media.cameraOn && (
                    <span className="rounded-full bg-black/60 px-2.5 py-1 text-[11px] font-medium text-white">{faceLabel}</span>
                  )}
                </div>

                <div className="absolute inset-x-3 bottom-3 flex items-center justify-between gap-2 rounded-xl bg-black/60 p-2">
                  <div className="flex gap-1.5">
                    <IconToggle
                      on={media.cameraOn}
                      disabled={!live}
                      onClick={media.toggleCamera}
                      onLabel="Turn camera off"
                      offLabel="Turn camera on"
                      OnIcon={Camera}
                      OffIcon={CameraOff}
                    />
                    <IconToggle
                      on={media.micOn}
                      disabled={!live}
                      onClick={() => {
                        if (!media.toggleMic()) speech.stop();
                      }}
                      onLabel="Mute microphone"
                      offLabel="Unmute microphone"
                      OnIcon={Mic}
                      OffIcon={MicOff}
                    />
                    <IconToggle
                      on={voiceOn}
                      onClick={() => {
                        if (voiceOn) voice.stop();
                        setVoiceOn(!voiceOn);
                      }}
                      onLabel="Mute interviewer voice"
                      offLabel="Unmute interviewer voice"
                      OnIcon={Volume2}
                      OffIcon={VolumeX}
                    />
                  </div>
                  <div className="flex h-5 items-end gap-0.5" aria-hidden="true">
                    {Array.from({ length: 10 }, (_, i) => (
                      <span
                        key={i}
                        className={`w-1 rounded-sm ${media.audioLevel > i * 6 ? "bg-emerald-400" : "bg-white/20"}`}
                        style={{ height: `${6 + i * 1.4}px` }}
                      />
                    ))}
                  </div>
                </div>
              </div>

              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs" aria-labelledby="signals-heading">
                <div className="flex items-baseline justify-between gap-2">
                  <h2 id="signals-heading" className="text-sm font-semibold text-slate-900">
                    Live delivery signals
                  </h2>
                  <span className="text-[11px] text-slate-500">Measured in your browser</span>
                </div>
                <dl className="mt-2 divide-y divide-slate-100 text-sm">
                  <SignalRow
                    label="Face in frame"
                    value={percentOrStatus(media.session.face_presence_percent, live && media.analyser === "ready")}
                  />
                  <SignalRow
                    label="Facing the camera"
                    value={percentOrStatus(media.session.eye_contact_percent, live && media.analyser === "ready")}
                  />
                  <SignalRow
                    label="Head steadiness"
                    value={
                      media.session.posture_stability_score !== null
                        ? `${media.session.posture_stability_score}/100`
                        : live && media.analyser === "ready"
                          ? "Measuring..."
                          : "Not captured"
                    }
                  />
                  <SignalRow label="Speaking pace (last answer)" value={lastPace === null ? "Spoken answers only" : `${lastPace} words/min`} />
                  <SignalRow label="Filler words (this answer)" value={String(countFillers(draft))} />
                </dl>
                {media.analyser === "unavailable" && (
                  <p className="mt-2 text-xs text-amber-700">
                    Face analysis could not load in this browser, so camera signals are not captured.
                  </p>
                )}
              </section>
            </div>

            <div className="flex flex-col gap-4 lg:col-span-7">
              <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-xs">
                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  <span className="font-semibold text-slate-900">
                    Question {Math.min(answered + 1, TOTAL_QUESTIONS)} of {TOTAL_QUESTIONS}
                  </span>
                  <span className="font-medium text-[#0D9488]">{phaseName}</span>
                  <span className="inline-flex items-center gap-1 tabular-nums text-slate-600">
                    <Clock className="size-3.5" aria-hidden="true" />
                    {formatClock(elapsed)} / {duration}:00
                  </span>
                </div>
                <div
                  className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-100"
                  role="progressbar"
                  aria-label="Questions answered"
                  aria-valuemin={0}
                  aria-valuemax={TOTAL_QUESTIONS}
                  aria-valuenow={answered}
                >
                  <div className="h-full rounded-full bg-[#1E3A8A] transition-all" style={{ width: `${(answered / TOTAL_QUESTIONS) * 100}%` }} />
                </div>
                {elapsed > duration * 60 && (
                  <p className="mt-2 text-xs text-amber-700">You are past the planned {duration} minutes. Keep your answers focused.</p>
                )}
              </section>

              <section className="flex flex-col rounded-2xl border border-slate-200 bg-white shadow-xs" aria-label="Interview conversation">
                <div ref={threadRef} className="h-[22rem] space-y-4 overflow-y-auto p-4 sm:h-[26rem]" aria-live="polite">
                  {messages.map((m, i) =>
                    m.role === "board" ? (
                      <div key={i} className="flex gap-3">
                        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-[#1E3A8A] text-white">
                          <Brain className="size-4" aria-hidden="true" />
                        </div>
                        <div className="max-w-[85%]">
                          <p className="text-[11px] font-semibold text-slate-500">
                            Board member{m.source === "groq" ? " · Groq AI" : m.source === "deterministic-fallback" ? " · fallback question" : ""}
                          </p>
                          <div className="mt-1 rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-3 text-sm leading-relaxed text-pretty text-slate-900">
                            {m.text}
                          </div>
                          {i === messages.length - 1 && (
                            <button
                              type="button"
                              onClick={() => speak(m.text, true)}
                              className="mt-1 text-[11px] font-semibold text-[#1E3A8A] hover:underline"
                            >
                              Replay
                            </button>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div key={i} className="flex flex-col items-end">
                        <p className="text-[11px] font-semibold text-slate-500">You</p>
                        <div className="mt-1 max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-tr-sm bg-[#1E3A8A] px-4 py-3 text-sm leading-relaxed text-pretty text-white">
                          {m.text}
                        </div>
                        {m.tags && m.tags.length > 0 && (
                          <div className="mt-1.5 flex max-w-[85%] flex-wrap justify-end gap-1">
                            {m.tags.map((tag) => (
                              <span key={tag} className="rounded-md border border-teal-200 bg-teal-50 px-1.5 py-0.5 text-[10px] font-medium text-teal-800">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                        {m.note && <p className="mt-1 max-w-[85%] text-right text-[11px] text-pretty text-slate-500">{m.note}</p>}
                      </div>
                    ),
                  )}
                  {submitting && (
                    <p className="flex items-center gap-2 text-xs text-slate-500">
                      <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
                      The board member is considering your answer...
                    </p>
                  )}
                </div>

                <div className="border-t border-slate-200 p-4">
                  <label htmlFor="interview-answer" className="sr-only">
                    Your answer
                  </label>
                  <textarea
                    id="interview-answer"
                    rows={4}
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                        e.preventDefault();
                        void handleSubmit();
                      }
                    }}
                    disabled={submitting}
                    placeholder={speech.listening ? "Listening... speak your answer" : "Type your answer, or dictate it"}
                    className="w-full resize-y rounded-xl border border-slate-300 bg-white p-3 text-sm leading-relaxed text-slate-900 focus:border-[#1E3A8A] focus:outline-none focus:ring-2 focus:ring-[#1E3A8A]/20 disabled:bg-slate-50"
                  />
                  {speech.error && <p className="mt-1 text-xs text-amber-700">{speech.error}</p>}
                  <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      {speech.supported ? (
                        <Button
                          type="button"
                          size="sm"
                          variant={speech.listening ? "danger" : "outline"}
                          onClick={() => (speech.listening ? speech.stop() : void speech.start(draft))}
                          disabled={submitting || speech.starting || speech.busy || (live && !media.micOn)}
                        >
                          {speech.starting ? (
                            <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
                          ) : speech.listening ? (
                            <MicOff className="size-3.5" aria-hidden="true" />
                          ) : (
                            <Mic className="size-3.5" aria-hidden="true" />
                          )}
                          {speech.starting ? "Starting mic..." : speech.listening ? "Stop dictation" : "Dictate answer"}
                        </Button>
                      ) : (
                        <span className="text-xs text-slate-500">Dictation is not supported in this browser. Type your answer.</span>
                      )}
                      <span className="text-xs tabular-nums text-slate-500">{draftWords} words</span>
                      {speech.busy && (
                        <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                          <Loader2 className="size-3 animate-spin" aria-hidden="true" />
                          Transcribing...
                        </span>
                      )}
                    </div>
                    <Button
                      type="button"
                      size="sm"
                      onClick={() => void handleSubmit()}
                      disabled={submitting || (!draft.trim() && !speech.listening && !speech.busy)}
                    >
                      <Send className="size-3.5" aria-hidden="true" />
                      Send answer
                    </Button>
                  </div>
                  <p className="mt-1.5 text-[11px] text-slate-400">Press Ctrl or Cmd + Enter to send.</p>
                </div>
              </section>
            </div>
          </div>
        )}

        {stage === "concluding" && (
          <div className="mx-auto mt-10 max-w-lg rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-xs">
            {error ? (
              <>
                <AlertCircle className="mx-auto size-8 text-rose-600" aria-hidden="true" />
                <p className="mt-3 text-sm text-pretty text-slate-700">{error}</p>
                <div className="mt-4 flex justify-center gap-2">
                  <Button variant="outline" onClick={restart}>
                    Start over
                  </Button>
                  <Button onClick={() => void conclude()}>Try again</Button>
                </div>
              </>
            ) : (
              <>
                <Loader2 className="mx-auto size-8 animate-spin text-[#1E3A8A]" aria-hidden="true" />
                <h2 className="mt-3 text-base font-semibold text-slate-900">Preparing your assessment</h2>
                <p className="mt-1 text-sm text-pretty text-slate-600">
                  The board is reviewing your {answered} {answered === 1 ? "answer" : "answers"}. This usually takes under a minute.
                </p>
              </>
            )}
          </div>
        )}

        {stage === "report" && report && (
          <InterviewReport report={report} onRestart={restart} backHref={backHref} backLabel={backLabel} />
        )}
      </div>
    </div>
  );
}
