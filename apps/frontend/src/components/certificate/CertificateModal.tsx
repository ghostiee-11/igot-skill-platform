"use client";

import React, { useRef } from "react";
import { Award, CheckCircle2, Download, Printer, ShieldCheck, X } from "lucide-react";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { CertificateItem } from "@/lib/types";

interface CertificateModalProps {
  certificate: CertificateItem | null;
  open: boolean;
  onClose: () => void;
}

export function CertificateModal({ certificate, open, onClose }: CertificateModalProps) {
  const printRef = useRef<HTMLDivElement>(null);

  if (!certificate) return null;

  const handlePrint = () => {
    window.print();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl p-0 overflow-hidden bg-slate-50" onClose={onClose}>
        {/* Certificate Canvas Area */}
        <div
          ref={printRef}
          className="relative p-4 sm:p-10 bg-white border-4 sm:border-8 border-slate-900 shadow-2xl m-2 sm:m-4 rounded-xl text-center"
        >
          {/* Subtle Guilloche Inner Border */}
          <div className="absolute inset-2 sm:inset-3 border-2 border-amber-600/40 rounded-lg pointer-events-none" />
          <div className="absolute inset-3 sm:inset-4 border border-slate-300 rounded-md pointer-events-none" />

          {/* Header & National Emblem Styling */}
          <div className="flex flex-col items-center mb-5 sm:mb-6">
            <div className="h-12 w-12 sm:h-14 sm:w-14 rounded-full bg-amber-50 border-2 border-amber-600 flex items-center justify-center mb-2.5 sm:mb-3">
              <Award className="h-6 w-6 sm:h-8 sm:w-8 text-amber-700" />
            </div>
            <h4 className="text-[10px] sm:text-xs font-bold uppercase tracking-widest text-slate-500 max-w-md">
              Government of India • Ministry of Personnel, Public Grievances and Pensions
            </h4>
            <h2 className="text-xl sm:text-2xl font-serif font-bold text-slate-900 mt-1 tracking-tight">
              Mission Karmayogi • National Programme for Civil Services Capacity Building
            </h2>
            <div className="w-20 sm:w-24 h-0.5 bg-amber-600 my-2.5 sm:my-3" />
            <p className="text-[10px] sm:text-xs font-semibold text-slate-600 uppercase tracking-widest">
              Official Certificate of Competency Mastery
            </p>
          </div>

          {/* Recipient Details */}
          <p className="text-xs sm:text-sm text-slate-500 italic mb-1.5 sm:mb-2">This is to officially certify that</p>
          <h1 className="text-2xl sm:text-3xl font-serif font-extrabold text-slate-900 underline decoration-amber-600/60 decoration-2 underline-offset-8 mb-3 sm:mb-4">
            {certificate.recipient_name}
          </h1>

          <p className="text-xs sm:text-sm text-slate-600 max-w-xl mx-auto mb-3 sm:mb-4 leading-relaxed">
            has successfully completed the prescribed curriculum and demonstrated professional competency in
          </p>

          <div className="bg-slate-50 border border-slate-200 rounded-xl py-2.5 sm:py-3 px-4 sm:px-6 max-w-xl mx-auto mb-5 sm:mb-6">
            <h3 className="text-base sm:text-xl font-bold text-slate-900">{certificate.course_title}</h3>
            <p className="text-[11px] sm:text-xs text-slate-500 mt-1 font-medium">
              Accredited by {certificate.organization} • Instructor: {certificate.instructor}
            </p>
          </div>

          {/* Competency & Grade Badge */}
          <div className="flex flex-col sm:flex-row justify-center items-stretch sm:items-center gap-3 sm:gap-6 mb-6 sm:mb-8 text-left">
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-2 flex items-center gap-3">
              <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
              <div>
                <p className="text-[10px] uppercase font-bold text-emerald-800">Assessment Score</p>
                <p className="text-sm font-extrabold text-emerald-900">{certificate.score_percent}% (Passed)</p>
              </div>
            </div>

            <div className="bg-slate-100 border border-slate-200 rounded-lg px-4 py-2 flex items-center gap-3">
              <ShieldCheck className="h-5 w-5 text-slate-700 shrink-0" />
              <div>
                <p className="text-[10px] uppercase font-bold text-slate-700">Official Status</p>
                <p className="text-sm font-extrabold text-slate-900">Verified Credential</p>
              </div>
            </div>
          </div>

          {/* Signatures & Issue Date */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-0 items-end pt-5 sm:pt-6 border-t border-slate-200 text-xs text-slate-600">
            <div>
              <p className="font-semibold text-slate-800">{certificate.issued_date}</p>
              <p className="text-[10px] text-slate-400">Date of Issuance</p>
            </div>
            <div>
              <p className="font-mono text-[11px] font-semibold text-slate-700">{certificate.certificate_id}</p>
              <p className="text-[10px] text-slate-400">Digital Registry Identifier</p>
            </div>
            <div>
              <div className="font-serif italic font-semibold text-slate-800 text-sm">Secretary (DoPT)</div>
              <p className="text-[10px] text-slate-400">Karmayogi Accreditation Authority</p>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-end gap-2.5 sm:gap-3 px-4 sm:px-8 py-3.5 sm:py-4 bg-white border-t border-slate-200">
          <Button variant="outline" size="sm" onClick={handlePrint} className="gap-2 justify-center">
            <Printer className="h-4 w-4" /> Print Certificate
          </Button>
          <Button variant="default" size="sm" onClick={handlePrint} className="gap-2 bg-slate-900 justify-center">
            <Download className="h-4 w-4" /> Save / Download PDF
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
