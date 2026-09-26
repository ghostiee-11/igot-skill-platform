import CyberSandboxPage from "@/features/digital_governance/components/CyberSandboxPage";

export const metadata = {
  title: "Cyber Defense Sandbox & Incident Response Range | iGot Karmayogi",
  description:
    "Interactive CTF and incident response range for Indian civil servants. Analyze authentic telemetry in isolated Marimo sandboxes, investigate MITRE ATT&CK techniques, and verify critical infrastructure flags.",
};

export default function Page() {
  return <CyberSandboxPage />;
}
