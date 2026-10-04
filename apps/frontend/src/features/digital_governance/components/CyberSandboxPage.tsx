"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  ShieldAlert,
  Terminal,
  Cpu,
  Flag,
  Key,
  RefreshCw,
  Play,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Lock,
  Unlock,
  Clock,
  ChevronRight,
  Layers,
  Award,
  Maximize2,
  Minimize2,
  FileText,
  HelpCircle,
  Radio,
  Server,
  Send,
  BookOpen,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { fetchApi } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

interface ChallengeSummary {
  id: string;
  title: string;
  category: string;
  difficulty: string;
  points: number;
  duration_minutes: number;
  is_flagship: boolean;
  solved: boolean;
  competency_id: string;
  tags: string[];
  mitre_techniques: string[];
  objectives: string[];
}

interface Hint {
  id: number;
  penalty: number;
  unlocked: boolean;
  content?: string;
}

interface ActiveSessionData {
  session_id: string;
  challenge_id: string;
  title: string;
  category: string;
  difficulty: string;
  points: number;
  expires_at: string;
  remaining_seconds: number;
  status: string;
  assigned_port: number;
  marimo_url: string;
  hints: Hint[];
  scenario_md: string;
  objectives: string[];
  solved: boolean;
}

interface CompetencyRadar {
  soc_investigation: number;
  phishing_analysis: number;
  cloud_security: number;
  dpi_security: number;
  digital_forensics: number;
  total_score: number;
  solved_challenges_count: number;
}

export default function CyberSandboxPage() {
  const searchParams = useSearchParams();
  const courseId = searchParams.get("courseId") || "4";
  const [challenges, setChallenges] = useState<ChallengeSummary[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [activeSession, setActiveSession] = useState<ActiveSessionData | null>(
    null,
  );
  const [loading, setLoading] = useState<boolean>(true);
  const [startingSession, setStartingSession] = useState<boolean>(false);
  const [startError, setStartError] = useState<string | null>(null);
  const [flagInput, setFlagInput] = useState<string>("");
  const [submittingFlag, setSubmittingFlag] = useState<boolean>(false);
  const [flagMessage, setFlagMessage] = useState<{
    text: string;
    success: boolean;
  } | null>(null);
  const [competencies, setCompetencies] = useState<CompetencyRadar>({
    soc_investigation: 0,
    phishing_analysis: 0,
    cloud_security: 0,
    dpi_security: 0,
    digital_forensics: 0,
    total_score: 0,
    solved_challenges_count: 0,
  });

  // Console UI
  const [fullscreen, setFullscreen] = useState<boolean>(false);
  const [iframeKey, setIframeKey] = useState<number>(0);
  const [unlockingHintId, setUnlockingHintId] = useState<number | null>(null);
  const [remainingSecs, setRemainingSecs] = useState<number>(0);

  // Fetch Catalog & Competencies
  const fetchChallenges = async () => {
    try {
      const res = await fetch(
        `${API_BASE}/digital-governance/sandbox/challenges`,
      );
      if (res.ok) {
        const data = await res.json();
        setChallenges(data);
      } else {
        // Fallback default challenges for preview
        setChallenges([
          {
            id: "01-soc-auth-investigation",
            title: "INCIDENT 0101: Operation NightShift",
            category: "SOC Investigation",
            difficulty: "Beginner",
            points: 100,
            duration_minutes: 45,
            is_flagship: false,
            solved: false,
            competency_id: "soc_investigation",
            tags: [
              "soc",
              "authentication",
              "brute-force",
              "event-4625",
              "cert-in",
            ],
            mitre_techniques: ["T1110.001", "T1078.002"],
            objectives: [
              "Isolate external brute-force spikes in auth_events.json",
              "Discover compromised off-hours user account",
              "Trace Living-off-the-Land command to recover flag",
            ],
          },
          {
            id: "03-compromised-linux-server",
            title: "INCIDENT 0303: Operation Shakti (Linux Server IR)",
            category: "Incident Response / Linux Forensics",
            difficulty: "Intermediate",
            points: 130,
            duration_minutes: 45,
            is_flagship: false,
            solved: false,
            competency_id: "digital_forensics",
            tags: [
              "linux",
              "crontab",
              "sudoers",
              "persistence",
              "reverse-shell",
            ],
            mitre_techniques: ["T1053.003", "T1548.003", "T1059.004"],
            objectives: [
              "Inspect auth.log for privilege escalation and unauthorized sudo usage",
              "Audit crontab and cron.d scheduled jobs for hidden backdoor timers",
              "De-obfuscate reverse shell script to extract incident flag",
            ],
          },
          {
            id: "04-vulnerable-web-app",
            title: "INCIDENT 0404: Operation Suraksha (Citizen DB SQLi)",
            category: "Web Application Security / Data Privacy",
            difficulty: "Intermediate",
            points: 140,
            duration_minutes: 45,
            is_flagship: false,
            solved: false,
            competency_id: "data_privacy",
            tags: ["web", "sqli", "union-select", "dpdp-act", "aadhaar-leak"],
            mitre_techniques: ["T1190", "T1005", "T1565"],
            objectives: [
              "Identify SQL injection entry point on welfare directory search",
              "Craft UNION SELECT payload to probe hidden database schemas",
              "Extract unredacted citizen subsidy records to recover incident flag",
            ],
          },
          {
            id: "05-threat-hunting-lotl",
            title: "INCIDENT 0505: Operation Garuda (Threat Hunting)",
            category: "Threat Hunting / Cyber Defense",
            difficulty: "Advanced",
            points: 160,
            duration_minutes: 50,
            is_flagship: false,
            solved: false,
            competency_id: "soc_investigation",
            tags: [
              "lotl",
              "threat-hunting",
              "sysmon",
              "entropy",
              "dns-tunneling",
            ],
            mitre_techniques: ["T1036.005", "T1071.004", "T1059.001"],
            objectives: [
              "Detect process masquerading in Sysmon process tree events",
              "Calculate Shannon entropy on subdomains in DNS query logs",
              "Reconstruct exfiltrated Base64 data stream to recover flag",
            ],
          },
          {
            id: "06-pki-token-dispute",
            title: "INCIDENT 0606: Operation Mudra (PKI & GeM Defense)",
            category: "Digital Signatures / PKI",
            difficulty: "Intermediate",
            points: 140,
            duration_minutes: 45,
            is_flagship: false,
            solved: false,
            competency_id: "digital_forensics",
            tags: ["pki", "digital-signatures", "gem", "dsc", "ocsp", "crl"],
            mitre_techniques: ["T1588.003", "T1552.004"],
            objectives: [
              "Audit Class 3 DSC certificate revocation list (CRL) timestamps",
              "Correlate GeM tender submission timestamp against CA revocation",
              "Establish non-repudiation under IT Act 2000 Section 3 & 3A",
            ],
          },
          {
            id: "07-meghraj-cloud-audit",
            title: "INCIDENT 0707: Operation Megh (Sovereign Cloud Audit)",
            category: "Government Cloud / MeghRaj",
            difficulty: "Intermediate",
            points: 125,
            duration_minutes: 45,
            is_flagship: false,
            solved: false,
            competency_id: "cloud_security",
            tags: ["cloud", "meghraj", "stqc", "data-localization", "s3"],
            mitre_techniques: ["T1530", "T1048"],
            objectives: [
              "Inspect cloud_audit_events.json for non-MeghRaj foreign deployment",
              "Identify leaking citizen bucket across international borders",
              "Extract STQC remediation flag",
            ],
          },
        ]);
      }
    } catch (e) {
      console.warn("API unavailable, loading local fallback challenges:", e);
    } finally {
      setLoading(false);
    }
  };

  const fetchCompetencies = async () => {
    try {
      setCompetencies(await fetchApi<CompetencyRadar>("/digital-governance/sandbox/competencies"));
    } catch (e) {
      // ignore
    }
  };

  useEffect(() => {
    fetchChallenges();
    fetchCompetencies();
  }, []);

  // Timer Tick
  useEffect(() => {
    if (!activeSession || remainingSecs <= 0) return;
    const interval = setInterval(() => {
      setRemainingSecs((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [activeSession, remainingSecs]);

  // Start Session
  const handleStartSession = async (chalId: string) => {
    setStartingSession(true);
    setStartError(null);
    setFlagMessage(null);
    setFlagInput("");
    try {
      const sess = await fetchApi<ActiveSessionData>("/digital-governance/sandbox/session/start", {
        method: "POST",
        body: JSON.stringify({ challenge_id: chalId, duration_minutes: 45 }),
      });
      setActiveSession(sess);
      setRemainingSecs(sess.remaining_seconds || 2700);
    } catch (e) {
      console.error("Start session error:", e);
      setStartError(e instanceof Error ? e.message : "The analyst console could not be started.");
    } finally {
      setStartingSession(false);
    }
  };

  // Stop Session
  const handleStopSession = async () => {
    if (!activeSession) return;
    try {
      await fetchApi(`/digital-governance/sandbox/session/${activeSession.session_id}/stop`, { method: "POST" });
    } catch (e) {
      // ignore
    }
    setActiveSession(null);
    setRemainingSecs(0);
  };

  // Submit Flag
  const handleSubmitFlag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!flagInput.trim() || !activeSession) return;
    setSubmittingFlag(true);
    setFlagMessage(null);

    try {
      const data = await fetchApi<{message:string;correct:boolean}>("/digital-governance/sandbox/session/submit-flag", {
        method: "POST",
        body: JSON.stringify({ session_id: activeSession.session_id, challenge_id: activeSession.challenge_id, flag: flagInput.trim() }),
      });
      setFlagMessage({ text: data.message, success: data.correct });
      if (data.correct) {
        setActiveSession({ ...activeSession, solved: true });
        fetchCompetencies();
        setChallenges((items) => items.map((item) => item.id === activeSession.challenge_id ? { ...item, solved: true } : item));
      }
    } catch (e) {
      setFlagMessage({
        text: e instanceof Error ? e.message : "Error submitting flag. Please try again.",
        success: false,
      });
    } finally {
      setSubmittingFlag(false);
    }
  };

  const CHALLENGE_HINTS_CATALOG: Record<string, Record<number, string>> = {
    "01-soc-auth-investigation": {
      1: "Filter authentication events where event_id is 4625 (logon failure) and aggregate count by ip_address to identify the brute-force source.",
      2: "Once you locate the attacker IP, filter for the subsequent successful logon (event_id 4624) to find the compromised account name, then inspect the Event 4688 command line.",
    },
    "03-compromised-linux-server": {
      1: "Inspect the deploy user's command history in Step 1 (.bash_history) for curl or base64 decoding commands.",
      2: "Inspect Step 3 (/etc/cron.d). Check the file configured to run periodically and find where the persistence payload is placed.",
    },
    "04-vulnerable-web-app": {
      1: "Test input with `'`. Observe if SQLite syntax errors leak database structure.",
      2: "Determine column count with UNION SELECT. Try `' UNION SELECT 1, 2, 3, 4 --` until no column count error occurs.",
      3: "Query sqlite_master schema: `' UNION SELECT 1, name, sql, 4 FROM sqlite_master WHERE type='table' --` to discover secret vault tables.",
    },
    "05-threat-hunting-lotl": {
      1: "Genuine Windows svchost.exe only runs from C:\\Windows\\System32. Check parent process and command line for anomalous paths.",
      2: "Adjust the Shannon Entropy slider to 4.0 or above in Step 2. High entropy DNS queries often indicate C2 exfiltration or base64 data tunneling.",
    },
    "06-pki-token-dispute": {
      1: "Compare the submission timestamp in gem_tender_submission.json against the DSC CRL revocation timestamp in dsc_revocation_list.json.",
      2: "Under Section 3A of the IT Act, a digital signature created after the certificate revocation timestamp is legally null and void.",
    },
    "07-meghraj-cloud-audit": {
      1: "Filter cloud_audit_events.json for records where 'region' does not equal 'ap-south-1' (MeghRaj Sovereign Cloud Mumbai).",
      2: "Inspect the 'response_elements' in the non-compliant region event to uncover the replicated bucket name and storage tier.",
    },
  };

  // Unlock Hint
  const handleUnlockHint = async (hintId: number) => {
    if (!activeSession) return;
    setUnlockingHintId(hintId);
    try {
      const data = await fetchApi<{content:string;remaining_points:number}>("/digital-governance/sandbox/session/unlock-hint", {
        method: "POST",
        body: JSON.stringify({ session_id: activeSession.session_id, challenge_id: activeSession.challenge_id, hint_id: hintId }),
      });
      setActiveSession({
        ...activeSession,
        points: data.remaining_points,
        hints: activeSession.hints.map((h) =>
          h.id === hintId
            ? { ...h, unlocked: true, content: data.content }
            : h,
        ),
      });
    } catch (e) {
      setStartError(e instanceof Error ? e.message : "Could not unlock hint.");
    } finally {
      setUnlockingHintId(null);
    }
  };

  // Format seconds to mm:ss
  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  // Filter challenges across modules and domains
  const filteredChallenges = challenges.filter((c) => {
    if (selectedCategory === "All") return true;
    if (selectedCategory === "SOC")
      return c.category.includes("SOC") || c.tags.includes("soc");
    if (selectedCategory === "Linux IR")
      return c.category.includes("Linux") || c.category.includes("Forensics");
    if (selectedCategory === "Web")
      return c.category.includes("Web") || c.category.includes("Privacy");
    if (selectedCategory === "PKI")
      return c.category.includes("PKI") || c.category.includes("Signature");
    if (selectedCategory === "Cloud")
      return c.category.includes("Cloud") || c.category.includes("MeghRaj");
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50 pb-16 text-slate-900">
      <div className="hero-gradient relative overflow-hidden px-4 py-12 text-white sm:px-6 lg:px-8">
        <div className="absolute inset-0 hero-mesh opacity-40 pointer-events-none" />
        <div className="relative z-10 max-w-7xl mx-auto">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-teal-200">
                <Terminal className="h-3.5 w-3.5 text-teal-300" />
                <span>
                  Digital governance · practical investigation
                </span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
                Cyber Defense &amp; Tabletop Sandboxes
              </h1>
              <p className="mt-2 text-white/80 max-w-2xl text-sm sm:text-base leading-relaxed font-normal">
                Investigate real-world critical infrastructure incidents in
                isolated Python Marimo environments. Analyze forensic logs,
                verify cryptographic signatures, mitigate supply chain breaches,
                and submit verifiable flags.
              </p>
            </div>

            {/* Quick Actions & Score Overview */}
            <div className="flex flex-col sm:flex-row gap-3">
              {courseId && (
                <Link
                  href={`/courses/${courseId}`}
                  className="flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-bold px-5 py-2.5 rounded-xl transition-all text-xs shadow-md"
                >
                  <BookOpen className="h-4 w-4 text-white" />
                  Return to Course Player
                </Link>
              )}
              <Link
                href={`/digital-governance/scenarios${courseId ? `?courseId=${courseId}` : ""}`}
                className="flex items-center justify-center gap-2 glass-light hover:bg-white/20 border border-white/20 text-white font-bold px-5 py-2.5 rounded-xl transition-all text-xs"
              >
                <Layers className="h-4 w-4 text-teal-300" />
                Crisis Scenarios
              </Link>
            </div>
          </div>

          {/* Competency Radar Strip */}
          <div className="mt-6 pt-6 border-t border-blue-800/60 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
            <div className="bg-blue-950/50 border border-blue-800 rounded-lg p-3">
              <div className="text-slate-400 font-medium">Total CTF Score</div>
              <div className="text-xl font-bold text-amber-400 mt-1 flex items-baseline gap-1">
                {competencies.total_score}{" "}
                <span className="text-[10px] text-slate-400">pts</span>
              </div>
            </div>
            <div className="bg-blue-950/50 border border-blue-800 rounded-lg p-3">
              <div className="text-slate-400 font-medium">Solved Incidents</div>
              <div className="text-xl font-bold text-emerald-400 mt-1">
                {competencies.solved_challenges_count}
              </div>
            </div>
            <div className="bg-blue-950/50 border border-blue-800 rounded-lg p-3">
              <div className="text-slate-400 font-medium">SOC Triage</div>
              <div className="text-base font-bold text-white mt-1">
                {competencies.soc_investigation} pts
              </div>
            </div>
            <div className="bg-blue-950/50 border border-blue-800 rounded-lg p-3">
              <div className="text-slate-400 font-medium">Phishing DFIR</div>
              <div className="text-base font-bold text-white mt-1">
                {competencies.phishing_analysis} pts
              </div>
            </div>
            <div className="bg-blue-950/50 border border-blue-800 rounded-lg p-3">
              <div className="text-slate-400 font-medium">Cloud / MeghRaj</div>
              <div className="text-base font-bold text-white mt-1">
                {competencies.cloud_security} pts
              </div>
            </div>
            <div className="bg-blue-950/50 border border-blue-800 rounded-lg p-3">
              <div className="text-slate-400 font-medium">DPI & API Setu</div>
              <div className="text-base font-bold text-white mt-1">
                {competencies.dpi_security} pts
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* LEFT: Challenge Drawer & Catalog (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-bold text-[#1E3A8A] flex items-center gap-2">
                  <Server className="h-4 w-4 text-amber-500" />
                  Investigation Modules
                </h2>
                <span className="text-xs text-slate-500 font-medium bg-slate-100 px-2 py-0.5 rounded">
                  {filteredChallenges.length} Available
                </span>
              </div>

              {/* Category Filter Pills */}
              <div className="flex flex-wrap gap-1.5 mb-4 pb-2 border-b border-slate-100">
                {["All", "SOC", "Linux IR", "Web", "PKI", "Cloud"].map(
                  (cat) => (
                    <button
                      key={cat}
                      onClick={() => setSelectedCategory(cat)}
                      className={`text-xs px-2.5 py-1 rounded-md font-medium transition-colors ${
                        selectedCategory === cat
                          ? "bg-[#1E3A8A] text-white shadow-sm"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                    >
                      {cat}
                    </button>
                  ),
                )}
              </div>

              {/* Challenge List */}
              <div className="space-y-3 max-h-[700px] overflow-y-auto pr-1">
                {filteredChallenges.map((chal) => {
                  const isCurrent = activeSession?.challenge_id === chal.id;
                  return (
                    <div
                      key={chal.id}
                      className={`p-3.5 rounded-lg border transition-all ${
                        isCurrent
                          ? "bg-blue-50/70 border-[#1E3A8A] ring-1 ring-[#1E3A8A]"
                          : "bg-white border-slate-200 hover:border-blue-300 hover:bg-slate-50/50"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-1.5 mb-1">
                            <span className="bg-slate-100 text-slate-700 text-[10px] font-semibold px-1.5 py-0.2 rounded">
                              {chal.category}
                            </span>
                            <span
                              className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                                chal.difficulty === "Beginner"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : chal.difficulty === "Intermediate"
                                    ? "bg-amber-100 text-amber-800"
                                    : "bg-rose-100 text-rose-800"
                              }`}
                            >
                              {chal.difficulty}
                            </span>
                          </div>
                          <h3 className="font-bold text-sm text-slate-900 leading-snug">
                            {chal.title}
                          </h3>
                        </div>

                        <div className="text-right">
                          <span className="font-extrabold text-sm text-[#1E3A8A]">
                            {chal.points} pts
                          </span>
                          {chal.solved && (
                            <div className="flex items-center justify-end text-[10px] font-bold text-emerald-600 gap-0.5 mt-0.5">
                              <CheckCircle2 className="h-3 w-3" /> Solved
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Tags & MITRE */}
                      <div className="flex flex-wrap gap-1 mt-2">
                        {chal.tags.slice(0, 3).map((t, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded"
                          >
                            #{t}
                          </span>
                        ))}
                      </div>

                      {/* Action */}
                      <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
                        <span className="text-slate-500 flex items-center gap-1 text-[11px]">
                          <Clock className="h-3 w-3" /> {chal.duration_minutes}m
                          TTL
                        </span>

                        {isCurrent ? (
                          <span className="inline-flex items-center gap-1 font-bold text-[#1E3A8A] bg-blue-100/80 px-2 py-1 rounded text-xs">
                            <Radio className="h-3 w-3 text-emerald-500 animate-pulse" />
                            Live Active
                          </span>
                        ) : (
                          <button
                            onClick={() => handleStartSession(chal.id)}
                            disabled={startingSession}
                            className="inline-flex items-center gap-1 bg-[#1E3A8A] hover:bg-blue-900 text-white px-2.5 py-1 rounded font-semibold transition-colors text-xs"
                          >
                            <Play className="h-3 w-3 fill-current" />
                            Launch Environment
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
              {startError && (
                <div role="alert" className="mt-3 flex items-start gap-2 rounded-xl border border-rose-300 bg-rose-50 p-3 text-xs text-rose-900">
                  <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden="true" />
                  <p className="text-pretty">{startError}</p>
                </div>
              )}
            </div>
          </div>

          {/* RIGHT: Active Incident Stage & Marimo Workspace (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {activeSession ? (
              <div className="space-y-4">
                {/* Active Session Header Bar */}
                <div className="bg-[#1E3A8A] text-white p-4 rounded-xl shadow-md border border-blue-900 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-ping" />
                      <span className="text-xs uppercase font-bold tracking-wider text-amber-300">
                        Active Incident Range
                      </span>
                      <span className="text-xs bg-blue-950 px-2 py-0.5 rounded text-slate-300 font-mono">
                        Port {activeSession.assigned_port}
                      </span>
                    </div>
                    <h2 className="text-lg font-bold text-white mt-1">
                      {activeSession.title}
                    </h2>
                  </div>

                  {/* Timer & Controls */}
                  <div className="flex items-center gap-3">
                    <div className="bg-blue-950/80 border border-blue-800 rounded-lg px-3 py-1.5 text-center">
                      <div className="text-[10px] text-slate-300 font-semibold uppercase">
                        TTL Countdown
                      </div>
                      <div className="text-base font-mono font-bold text-amber-400 flex items-center justify-center gap-1">
                        <Clock className="h-3.5 w-3.5" />
                        {formatTime(remainingSecs)}
                      </div>
                    </div>

                    <button
                      onClick={handleStopSession}
                      className="text-xs bg-red-900/80 hover:bg-red-800 text-red-200 border border-red-700 px-3 py-1.5 rounded-lg font-medium transition-colors"
                    >
                      Terminate
                    </button>
                  </div>
                </div>

                {/* Objectives Checklist & Briefing */}
                <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                  <h3 className="font-bold text-sm text-[#1E3A8A] flex items-center gap-1.5 mb-2">
                    <ShieldAlert className="h-4 w-4 text-amber-500" />
                    Investigation Objectives
                  </h3>
                  <ul className="space-y-1.5 text-xs text-slate-700">
                    {activeSession.objectives.map((obj, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0 mt-0.5" />
                        <span>{obj}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Interactive Marimo Analyst Console / Embed */}
                <div
                  className={`bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs ${fullscreen ? "fixed inset-4 z-50 flex flex-col" : ""}`}
                >
                  <div className="bg-slate-50 text-slate-700 px-4 py-2.5 text-xs font-mono flex items-center justify-between border-b border-slate-200">
                    <div className="flex items-center gap-2">
                      <Terminal className="h-3.5 w-3.5 text-emerald-400" />
                      <span>
                        Marimo Analyst Console — {activeSession.marimo_url}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <a
                        href={activeSession.marimo_url}
                        target="_blank"
                        rel="noreferrer"
                        className="hover:text-[#1E3A8A] flex items-center gap-1 text-[11px] bg-white border border-slate-200 px-2 py-0.5 rounded transition-colors"
                      >
                        <ExternalLink className="h-3 w-3" /> New Window
                      </a>
                      <button
                        onClick={() => setIframeKey((k) => k + 1)}
                        title="Reload Console Frame"
                        className="hover:text-[#1E3A8A] p-1 rounded transition-colors text-slate-500"
                      >
                        <RefreshCw className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => setFullscreen(!fullscreen)}
                        className="hover:text-[#1E3A8A] p-1 rounded transition-colors"
                      >
                        {fullscreen ? (
                          <Minimize2 className="h-3.5 w-3.5" />
                        ) : (
                          <Maximize2 className="h-3.5 w-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Embedded Iframe */}
                  <div
                    className={`w-full bg-slate-100 relative ${fullscreen ? "flex-1" : "h-[460px]"}`}
                  >
                    <iframe
                      key={iframeKey}
                      src={activeSession.marimo_url}
                      className="w-full h-full border-0"
                      title="Marimo Interactive Sandbox"
                      sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                    />

                    {/* Iframe badge */}
                    <div className="absolute bottom-2 right-2 bg-white/90 border border-slate-200 text-slate-600 text-[10px] px-2 py-1 rounded backdrop-blur pointer-events-none">
                      Interactive Analysis Console • Port{" "}
                      {activeSession.assigned_port}
                    </div>
                  </div>
                </div>

                {/* CTF Flag Submission Bar */}
                <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-bold text-sm text-[#1E3A8A] flex items-center gap-1.5">
                      <Flag className="h-4 w-4 text-rose-500" />
                      Submit Incident Flag
                    </h3>
                    <span className="text-xs font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
                      Reward: {activeSession.points} pts
                    </span>
                  </div>

                  <form onSubmit={handleSubmitFlag} className="flex gap-2">
                    <div className="relative flex-1">
                      <input
                        type="text"
                        value={flagInput}
                        onChange={(e) => setFlagInput(e.target.value)}
                        placeholder="FLAG{sha256_or_incident_token_here}"
                        className="w-full font-mono text-xs border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-[#1E3A8A] focus:outline-none"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={submittingFlag || !flagInput.trim()}
                      className="bg-[#1E3A8A] hover:bg-blue-900 text-white text-xs font-bold px-4 py-2 rounded-lg flex items-center gap-1.5 transition-colors disabled:opacity-50"
                    >
                      {submittingFlag ? (
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <Send className="h-3.5 w-3.5" />
                      )}
                      Verify Flag
                    </button>
                  </form>

                  {/* Flag Feedback Notification */}
                  {flagMessage && (
                    <div
                      className={`mt-3 p-2.5 rounded-lg text-xs font-medium flex items-center gap-2 ${
                        flagMessage.success
                          ? "bg-emerald-50 text-emerald-900 border border-emerald-300"
                          : "bg-rose-50 text-rose-900 border border-rose-300"
                      }`}
                    >
                      {flagMessage.success ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
                      )}
                      <span>{flagMessage.text}</span>
                    </div>
                  )}
                </div>

                {/* Locked Hints Accordion */}
                <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                  <h3 className="font-bold text-sm text-slate-800 flex items-center gap-1.5 mb-3">
                    <Key className="h-4 w-4 text-amber-500" />
                    Tiered Investigation Hints (CTFd Locked)
                  </h3>

                  <div className="space-y-2">
                    {activeSession.hints.map((h) => (
                      <div
                        key={h.id}
                        className={`p-3 rounded-lg border text-xs ${
                          h.unlocked
                            ? "bg-amber-50/50 border-amber-200 text-slate-800"
                            : "bg-slate-50 border-slate-200 text-slate-600"
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold flex items-center gap-1.5">
                            {h.unlocked ? (
                              <Unlock className="h-3.5 w-3.5 text-amber-600" />
                            ) : (
                              <Lock className="h-3.5 w-3.5 text-slate-500" />
                            )}
                            Hint #{h.id}
                          </span>

                          {!h.unlocked ? (
                            <button
                              onClick={() => handleUnlockHint(h.id)}
                              disabled={unlockingHintId === h.id}
                              className="bg-amber-100 hover:bg-amber-200 text-amber-900 font-bold px-2 py-1 rounded text-[11px] border border-amber-300 transition-colors"
                            >
                              Unlock (-{h.penalty} pts)
                            </button>
                          ) : (
                            <span className="text-[10px] text-amber-800 font-bold bg-amber-100 px-1.5 py-0.5 rounded">
                              Unlocked
                            </span>
                          )}
                        </div>

                        {h.unlocked && h.content && (
                          <div className="mt-2 text-slate-700 leading-relaxed font-sans pt-2 border-t border-amber-200/60">
                            {h.content}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              /* No Active Session Empty State */
              <div className="bg-white rounded-xl border border-slate-200 p-8 shadow-sm text-center space-y-4">
                <div className="h-16 w-16 bg-blue-50 text-[#1E3A8A] rounded-2xl flex items-center justify-center mx-auto border border-blue-200">
                  <Terminal className="h-8 w-8 text-[#1E3A8A]" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">
                  Select an Investigation Challenge
                </h3>
                <p className="text-slate-600 text-xs sm:text-sm max-w-md mx-auto leading-relaxed">
                  Select an incident from the left panel to launch your
                  interactive Marimo analysis workbench.
                </p>

                <div className="pt-2 flex justify-center gap-3">
                  <button
                    onClick={() =>
                      handleStartSession("01-soc-auth-investigation")
                    }
                    disabled={startingSession}
                    className="bg-[#1E3A8A] hover:bg-blue-900 text-white text-xs font-bold px-4 py-2.5 rounded-lg flex items-center gap-2 shadow-sm transition-all"
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    {startingSession ? "Starting workbench…" : "Launch Incident Module 1"}
                  </button>
                </div>
                {startError && <p role="alert" className="text-sm text-rose-700">{startError}</p>}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
