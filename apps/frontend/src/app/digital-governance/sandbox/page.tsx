import React, { Suspense } from "react";
import CyberSandboxPage from "@/features/digital_governance/components/CyberSandboxPage";

export const metadata = {
  title: "Cyber Defense Sandbox & Incident Response Range | iGot Karmayogi",
  description:
    "Interactive CTF and incident response range for Indian civil servants. Analyze authentic telemetry in isolated Marimo sandboxes, investigate MITRE ATT&CK techniques, and verify critical infrastructure flags.",
};

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[70vh] bg-slate-50 flex flex-col items-center justify-center text-slate-900">
          <div className="w-10 h-10 border-4 border-[#1E3A8A] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-slate-500 text-sm font-medium">Loading Cyber Defense Sandbox...</p>
        </div>
      }
    >
      <CyberSandboxPage />
    </Suspense>
  );
}
