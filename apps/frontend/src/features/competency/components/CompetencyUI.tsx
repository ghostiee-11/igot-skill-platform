import Link from "next/link";
import { AlertCircle, AlertTriangle, CheckCircle2 } from "lucide-react";
import type { DomainCode } from "@/lib/types/competency";
import { DOMAINS, DOMAIN_ACCENT_CLASS, DOMAIN_ORDER, LEVEL_MAX, gapStatus, type GapTone } from "@/features/competency/domains";

const TONE_STYLE: Record<GapTone, { className: string; Icon: typeof CheckCircle2 }> = {
  good: { className: "border-[#0ca30c]/30 bg-[#0ca30c]/10 text-[#0a6e0a]", Icon: CheckCircle2 },
  warning: { className: "border-[#fab219]/50 bg-[#fab219]/15 text-[#7a5200]", Icon: AlertTriangle },
  serious: { className: "border-[#ec835a]/50 bg-[#ec835a]/15 text-[#9a3f1a]", Icon: AlertCircle },
};

export function GapChip({ gap }: { gap: number | null | undefined }) {
  const status = gapStatus(gap);
  if (!status) return null;
  const { className, Icon } = TONE_STYLE[status.tone];
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 text-xs font-medium ${className}`}>
      <Icon className="size-3.5" aria-hidden="true" />
      {status.label}
    </span>
  );
}

/** Level on the 0-5 scale as a bar, with a dark tick where the role target sits. */
export function LevelBar({ level, target, label }: { level: number; target?: number | null; label: string }) {
  const percent = Math.max(0, Math.min(100, (level / LEVEL_MAX) * 100));
  const targetPercent = target === null || target === undefined ? null : Math.max(0, Math.min(100, (target / LEVEL_MAX) * 100));
  return (
    <div
      role="img"
      aria-label={`${label}: level ${level.toFixed(1)} of ${LEVEL_MAX}${target != null ? `, role target ${target.toFixed(1)}` : ""}`}
      className="relative h-2 w-full rounded-full bg-slate-100"
    >
      <div className="h-full rounded-full bg-[#2a78d6]" style={{ width: `${percent}%` }} />
      {targetPercent !== null && (
        <span
          aria-hidden="true"
          className="absolute -top-1 h-4 w-0.5 rounded-full bg-slate-800"
          style={{ left: `calc(${targetPercent}% - 1px)` }}
        />
      )}
    </div>
  );
}

export function LevelLegend() {
  return (
    <div className="flex items-center gap-4 text-xs text-slate-500">
      <span className="inline-flex items-center gap-1.5">
        <span className="h-2 w-4 rounded-full bg-[#2a78d6]" aria-hidden="true" />
        Your level
      </span>
      <span className="inline-flex items-center gap-1.5">
        <span className="h-3 w-0.5 rounded-full bg-slate-800" aria-hidden="true" />
        Role target
      </span>
    </div>
  );
}

export function DomainNav({ active }: { active: DomainCode | "overview" }) {
  const items = [
    { key: "overview", href: "/competency", label: "Overview", accent: null as string | null },
    ...DOMAIN_ORDER.map((code) => ({
      key: code,
      href: `/competency/${code}`,
      label: DOMAINS[code].label,
      accent: DOMAIN_ACCENT_CLASS[code],
    })),
  ];
  return (
    <nav aria-label="Competency domains" className="overflow-x-auto">
      <ul className="flex min-w-max gap-1 border-b border-slate-200">
        {items.map((item) => {
          const isActive = item.key === active;
          return (
            <li key={item.key}>
              <Link
                href={item.href}
                aria-current={isActive ? "page" : undefined}
                className={`-mb-px inline-flex items-center gap-2 border-b-2 px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1E3A8A] ${
                  isActive ? "border-[#1E3A8A] text-[#1E3A8A]" : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-900"
                }`}
              >
                {item.accent && <span className={`size-2 rounded-full ${item.accent}`} aria-hidden="true" />}
                {item.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}

export function StatTile({ label, value, detail }: { label: string; value: React.ReactNode; detail?: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3">
      <dt className="text-xs font-medium text-slate-500">{label}</dt>
      <dd className="mt-1 text-2xl font-semibold tabular-nums text-slate-900">{value}</dd>
      {detail && <dd className="mt-1 text-xs text-slate-600">{detail}</dd>}
    </div>
  );
}
