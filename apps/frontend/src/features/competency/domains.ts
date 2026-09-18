import type { ComponentType } from "react";
import { BarChart3, Code, ShieldCheck, Users } from "lucide-react";
import type { DomainCode } from "@/lib/types/competency";

export interface DomainMeta {
  code: DomainCode;
  label: string;
  shortLabel: string; // fits a chart axis tick without collisions
  description: string;
  icon: ComponentType<{ className?: string; "aria-hidden"?: boolean | "true" | "false" }>;
  practice: { label: string; href: string }[];
}

export const LEVEL_MAX = 5;

export const DOMAIN_ORDER: DomainCode[] = ["statistical", "technical", "digital_governance", "behavioural"];

export const DOMAINS: Record<DomainCode, DomainMeta> = {
  statistical: {
    code: "statistical",
    label: "Statistical",
    shortLabel: "Statistical",
    description:
      "Survey design, sampling, national accounts, price, labour, agricultural and industrial statistics, SDG indicators, metadata standards and data quality frameworks.",
    icon: BarChart3,
    practice: [{ label: "Adaptive statistics exam", href: "/statistical" }],
  },
  technical: {
    code: "technical",
    label: "Technical",
    shortLabel: "Technical",
    description:
      "Python, R, SQL, Stata, SPSS, SAS, GIS, data visualization, AI and machine learning, cloud computing, APIs and open data.",
    icon: Code,
    practice: [{ label: "Hands-on virtual labs", href: "/labs" }],
  },
  digital_governance: {
    code: "digital_governance",
    label: "Digital Governance",
    shortLabel: "Digital Gov.",
    description:
      "Cybersecurity, data privacy, digital signatures, government cloud and digital public infrastructure.",
    icon: ShieldCheck,
    practice: [
      { label: "Cyber defense sandbox", href: "/digital-governance/sandbox" },
      { label: "Governance scenarios", href: "/digital-governance/scenarios" },
    ],
  },
  behavioural: {
    code: "behavioural",
    label: "Behavioural & Managerial",
    shortLabel: "Behavioural",
    description:
      "Leadership, communication, project management, ethics, decision making, situational awareness, accountability and change management.",
    icon: Users,
    practice: [
      { label: "AI oral board interview", href: "/behavioural/interview" },
      { label: "Case-based decision simulations", href: "/behavioural/cases" },
    ],
  },
};

export function isDomainCode(value: string): value is DomainCode {
  return (DOMAIN_ORDER as string[]).includes(value);
}

// Mirrors DOMAIN_CATEGORIES in backend/app/agents/igot/client.py.
const DOMAIN_CATEGORIES: Record<DomainCode, string[]> = {
  statistical: ["statistical", "sample surveys", "price statistics", "national accounts", "official statistics"],
  technical: ["technical", "data science", "programming", "cloud computing", "ai/ml"],
  digital_governance: ["digital governance", "data governance", "cybersecurity"],
  behavioural: ["behavioural", "public administration", "leadership", "management"],
};

export function domainForCategory(category?: string | null): DomainCode | null {
  const normalized = (category ?? "").trim().toLowerCase();
  return DOMAIN_ORDER.find((code) => DOMAIN_CATEGORIES[code].includes(normalized)) ?? null;
}

// Same hues as the chart palette, so a domain reads as one color across the product.
export const DOMAIN_ACCENT_CLASS: Record<DomainCode, string> = {
  statistical: "bg-[#2a78d6]",
  technical: "bg-[#eb6834]",
  digital_governance: "bg-[#1baf7a]",
  behavioural: "bg-[#eda100]",
};

export type GapTone = "good" | "warning" | "serious";

export function gapStatus(gap: number | null | undefined): { label: string; tone: GapTone } | null {
  if (gap === null || gap === undefined) return null;
  if (gap <= 0) return { label: "Target met", tone: "good" };
  if (gap <= 1) return { label: "Close to target", tone: "warning" };
  return { label: "Priority gap", tone: "serious" };
}

export const PRACTICE_DESCRIPTIONS: Record<string, string> = {
  "/statistical": "An adaptive exam that adjusts to each answer",
  "/labs": "Hands-on notebooks with automatic test checks",
  "/digital-governance/sandbox": "Investigate simulated cyber incidents",
  "/digital-governance/scenarios": "Work through governance crisis decisions",
  "/behavioural/interview": "A spoken interview with an AI board member",
  "/behavioural/cases": "Decisions based on real government notices",
};

export function levelLabel(level: number): string {
  if (level >= 4.5) return "Expert";
  if (level >= 3.5) return "Advanced";
  if (level >= 2.5) return "Proficient";
  if (level >= 1.5) return "Developing";
  if (level > 0) return "Foundational";
  return "Not yet assessed";
}
