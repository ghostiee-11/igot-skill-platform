import React, { Suspense } from "react";
import { Metadata } from "next";
import StatisticalExamPage from "@/features/statistical/components/StatisticalExamPage";

export const metadata: Metadata = {
  title: "Adaptive Statistical Examination | iGot Karmayogi",
  description: "Computerized Adaptive Testing (CAT) dynamic item-branching examination for statistical competencies and indices."
};

export default function StatisticalExamRoute() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[70vh] bg-slate-50 flex flex-col items-center justify-center text-slate-900">
          <div className="w-10 h-10 border-4 border-[#1E3A8A] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-slate-500 text-sm font-medium">Loading Adaptive Statistical Testing Engine...</p>
        </div>
      }
    >
      <StatisticalExamPage />
    </Suspense>
  );
}
