import React, { Suspense } from "react";
import DiscoverPage from "@/features/catalog/components/DiscoverPage";

export default function Page() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[70vh] bg-slate-50 flex flex-col items-center justify-center text-slate-900">
          <div className="w-10 h-10 border-4 border-[#1E3A8A] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-slate-500 text-sm font-medium">Loading Course Catalog...</p>
        </div>
      }
    >
      <DiscoverPage />
    </Suspense>
  );
}
