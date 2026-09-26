"use client";

import React from "react";
import Link from "next/link";
import {
  FlaskConical,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface LabLauncherBannerProps {
  title?: string;
  labId?: string | number;
  description?: string;
}

export function LabLauncherBanner({
  title = "Interactive Practice Lab",
  labId = "1001",
  description = "A Jupyter notebook backed by an isolated Python 3.11 sandbox, with automatic test grading.",
}: LabLauncherBannerProps) {
  return (
    <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-2xl">
          <div className="mb-2 inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.14em] text-[#0D9488]">
            <FlaskConical className="h-4 w-4" /> Technical practice
          </div>
          <h3 className="text-xl font-semibold text-slate-950">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            {description}
          </p>
        </div>

        <Link href={`/labs/${labId}`} target="_blank" rel="noopener noreferrer">
          <Button
            size="sm"
            className="h-10 rounded-xl bg-[#1E3A8A] px-5 text-xs font-semibold text-white hover:bg-[#173274]"
          >
            Open lab <ArrowRight className="ml-1 h-3.5 w-3.5" />
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-2 border-t border-slate-100 pt-4 text-sm text-slate-600 sm:grid-cols-3">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-[#0D9488]" />
          <span>Run code in cells</span>
        </div>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-[#0D9488]" />
          <span>Check your work</span>
        </div>
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-[#0D9488]" />
          <span>Submit when ready</span>
        </div>
      </div>
    </div>
  );
}

export default LabLauncherBanner;
