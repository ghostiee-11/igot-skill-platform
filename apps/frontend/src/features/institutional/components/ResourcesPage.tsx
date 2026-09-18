"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Building2,
  BookOpen,
  FileText,
  Download,
  Search,
  CheckCircle2,
  ExternalLink,
  ShieldCheck,
  Compass,
  ArrowRight,
  Filter,
  Layers,
  FileCheck,
  Check,
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { useI18n } from "@/lib/i18n";
import { useAuth } from "@/lib/auth/AuthContext";

interface ResourceDoc {
  id: string;
  docCode: string;
  category: string;
  tag: string;
  title: string;
  desc: string;
  org: string;
  fileSize: string;
  pages: number;
  published: string;
  version: string;
  relatedCourseId: number;
  relatedCourseTitle: string;
}

export default function ResourcesPage() {
  const { t } = useI18n();
  const { user } = useAuth();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [activeDocModal, setActiveDocModal] = useState<ResourceDoc | null>(null);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const categories = [
    "All",
    "Sample Surveys",
    "Price Statistics",
    "Quality Standards",
    "Survey Tech",
    "Fiscal Governance",
  ];

  const documents: ResourceDoc[] = [
    {
      id: "res-1",
      docCode: "NSSO-FOD-MAN-2026",
      category: "Sample Surveys",
      tag: t("resources.doc1Tag"),
      title: t("resources.doc1Title"),
      desc: t("resources.doc1Desc"),
      org: "National Sample Survey Office (NSSO)",
      fileSize: "4.2 MB",
      pages: 148,
      published: "January 2026",
      version: "v4.2",
      relatedCourseId: 1,
      relatedCourseTitle: "Fundamentals of National Sample Surveys (NSS)",
    },
    {
      id: "res-2",
      docCode: "CSO-CPI-TECH-2026",
      category: "Price Statistics",
      tag: t("resources.doc2Tag"),
      title: t("resources.doc2Title"),
      desc: t("resources.doc2Desc"),
      org: "Central Statistics Office (CSO)",
      fileSize: "3.8 MB",
      pages: 112,
      published: "February 2026",
      version: "v3.1",
      relatedCourseId: 2,
      relatedCourseTitle: "Compilation of Consumer Price Index (CPI) & Inflation Metrics",
    },
    {
      id: "res-3",
      docCode: "MOSPI-QA-RUBRICS-2026",
      category: "Quality Standards",
      tag: t("resources.doc3Tag"),
      title: t("resources.doc3Title"),
      desc: t("resources.doc3Desc"),
      org: "MoSPI Data Governance Lab",
      fileSize: "2.6 MB",
      pages: 86,
      published: "December 2025",
      version: "v2.0",
      relatedCourseId: 3,
      relatedCourseTitle: "Data Quality Frameworks & Official Statistics in India",
    },
    {
      id: "res-4",
      docCode: "NSSTA-CAPI-OPS-2026",
      category: "Survey Tech",
      tag: t("resources.doc4Tag"),
      title: t("resources.doc4Title"),
      desc: t("resources.doc4Desc"),
      org: "National Statistical Systems Training Academy (NSSTA)",
      fileSize: "5.1 MB",
      pages: 164,
      published: "March 2026",
      version: "v5.0",
      relatedCourseId: 1,
      relatedCourseTitle: "Fundamentals of National Sample Surveys (NSS)",
    },
    {
      id: "res-5",
      docCode: "CSO-NAS-SYS-2026",
      category: "Quality Standards",
      tag: "National Accounts",
      title: "National Accounts Statistics Compilation Handbook",
      desc: "Gross Domestic Product (GDP), Gross Value Added (GVA), sectoral output allocations, and international System of National Accounts (SNA 2008) guidelines.",
      org: "Central Statistics Office (CSO)",
      fileSize: "6.4 MB",
      pages: 220,
      published: "January 2026",
      version: "v4.0",
      relatedCourseId: 3,
      relatedCourseTitle: "Data Quality Frameworks & Official Statistics in India",
    },
    {
      id: "res-6",
      docCode: "ISTM-PFMS-GOV-2026",
      category: "Fiscal Governance",
      tag: "Fiscal Procedure",
      title: "Public Financial Management System (PFMS) Cadre Guide",
      desc: "Treasury Single Account (TSA) protocols, electronic sanction procedures, Single Nodal Agency (SNA) operations, and central expenditure audits.",
      org: "Institute of Secretariat Training & Management (ISTM)",
      fileSize: "3.1 MB",
      pages: 94,
      published: "November 2025",
      version: "v3.5",
      relatedCourseId: 4,
      relatedCourseTitle: "Digital Governance & Public Financial Management System (PFMS)",
    },
  ];

  const filteredDocs = documents.filter((doc) => {
    const matchesCategory =
      selectedCategory === "All" || doc.category === selectedCategory;
    const matchesSearch =
      doc.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.desc.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.docCode.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.org.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleTriggerDownload = (doc: ResourceDoc) => {
    setActiveDocModal(doc);
    setDownloadSuccess(false);
  };

  const handleConfirmDownload = () => {
    setDownloadSuccess(true);
    setTimeout(() => {
      setDownloadSuccess(false);
      setActiveDocModal(null);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* 1. Institutional White Header Banner */}
      <section className="bg-white border-b border-slate-200 py-8 sm:py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="max-w-3xl">
              <div className="flex items-center gap-2 mb-2">
                <Building2 className="h-4 w-4 text-[#1E3A8A]" />
                <span className="text-[11px] font-bold text-[#1E3A8A] uppercase tracking-wider">
                  Official Statistical Library • Ministry of Statistics & Programme Implementation
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-slate-900 tracking-tight">
                {t("resources.title")}
              </h1>
              <p className="mt-2 text-xs sm:text-sm text-slate-600 leading-relaxed">
                {t("resources.subtitle")}
              </p>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <Link href="/discover">
                <Button
                  size="sm"
                  className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold px-4 shadow-xs cursor-pointer"
                >
                  <Compass className="h-4 w-4 mr-1.5" /> {t("resources.browseCatalog")}
                </Button>
              </Link>
              {user && (
                <Link href="/home">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-slate-300 text-slate-700 hover:bg-slate-50 text-xs font-semibold px-4 cursor-pointer"
                  >
                    Dashboard <ArrowRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </Link>
              )}
            </div>
          </div>

          {/* Search & Category Filter Bar */}
          <div className="mt-8 pt-6 border-t border-slate-100 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="relative w-full md:w-96">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <Input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by title, document ID, or ministry..."
                className="pl-9 text-xs border-slate-300 bg-[#F8FAFC] focus:bg-white"
              />
            </div>

            {/* Category Filter Chips */}
            <div className="flex flex-wrap items-center gap-1.5 w-full md:w-auto">
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                    selectedCategory === cat
                      ? "bg-[#1E3A8A] text-white border-[#1E3A8A] shadow-2xs"
                      : "bg-white text-slate-700 border-slate-200 hover:bg-slate-50"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* 2. Main Content Canvas */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-10">
        {/* Results Count Strip */}
        <div className="flex items-center justify-between text-xs text-slate-500">
          <p>
            Showing <span className="font-semibold text-slate-900">{filteredDocs.length}</span> official manuals & standards
          </p>
          {(searchQuery || selectedCategory !== "All") && (
            <button
              onClick={() => {
                setSearchQuery("");
                setSelectedCategory("All");
              }}
              className="text-[#1E3A8A] hover:underline font-semibold cursor-pointer"
            >
              Reset Filters
            </button>
          )}
        </div>

        {/* Document Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDocs.map((doc) => (
            <Card
              key={doc.id}
              className="border-slate-200 bg-white shadow-2xs rounded-xl overflow-hidden flex flex-col justify-between"
            >
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#1E3A8A] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                    {doc.tag}
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">{doc.docCode}</span>
                </div>
                <CardTitle className="text-sm font-bold text-slate-900 leading-snug">
                  {doc.title}
                </CardTitle>
                <CardDescription className="text-xs text-slate-600 mt-1 line-clamp-3 leading-relaxed">
                  {doc.desc}
                </CardDescription>
              </CardHeader>

              <CardContent className="py-0 space-y-3">
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-[11px] text-slate-600 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Issuing Body:</span>
                    <span className="font-medium text-slate-800 truncate max-w-[170px]">{doc.org}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Format & Pages:</span>
                    <span className="font-medium text-slate-800">PDF • {doc.pages} pages</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Version:</span>
                    <span className="font-medium text-slate-800">{doc.version} ({doc.published})</span>
                  </div>
                </div>

                <div className="pt-1">
                  <Link
                    href={`/courses/${doc.relatedCourseId}`}
                    className="text-[11px] text-[#1E3A8A] hover:underline inline-flex items-center gap-1 font-medium"
                  >
                    <BookOpen className="h-3 w-3" /> Related: {doc.relatedCourseTitle}
                  </Link>
                </div>
              </CardContent>

              <CardFooter className="pt-4 pb-4 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="font-mono text-slate-400 text-[11px]">{doc.fileSize}</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleTriggerDownload(doc)}
                  className="border-slate-300 text-[#1E3A8A] hover:bg-blue-50 text-xs font-semibold gap-1.5 h-8 cursor-pointer"
                >
                  <Download className="h-3.5 w-3.5" /> {t("resources.access")}
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>

        {filteredDocs.length === 0 && (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-200 p-8">
            <FileText className="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <h3 className="text-sm font-bold text-slate-900">No resources match your filter</h3>
            <p className="text-xs text-slate-500 mt-1">
              Try adjusting your search keywords or select "All" categories.
            </p>
          </div>
        )}

        {/* Document Detail & Download Modal */}
        <Dialog open={!!activeDocModal} onOpenChange={(open) => !open && setActiveDocModal(null)}>
          <DialogContent className="max-w-md p-6 bg-white">
            {activeDocModal && (
              <>
                <DialogHeader>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#1E3A8A] bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      {activeDocModal.docCode}
                    </span>
                    <span className="text-xs text-slate-400 font-mono">{activeDocModal.version}</span>
                  </div>
                  <DialogTitle className="text-base font-bold text-slate-900">
                    {activeDocModal.title}
                  </DialogTitle>
                  <DialogDescription className="text-xs text-slate-500">
                    Official technical release authenticated by {activeDocModal.org}
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 pt-2 text-xs">
                  <p className="text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg border border-slate-200">
                    {activeDocModal.desc}
                  </p>

                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block">File Size</span>
                      <span className="font-bold text-slate-800">{activeDocModal.fileSize}</span>
                    </div>
                    <div className="p-2.5 bg-slate-50 rounded-lg border border-slate-100">
                      <span className="text-slate-400 block">Publication Date</span>
                      <span className="font-bold text-slate-800">{activeDocModal.published}</span>
                    </div>
                  </div>

                  <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-slate-700 text-[11px] flex items-start gap-2">
                    <ShieldCheck className="h-4 w-4 text-[#1E3A8A] shrink-0 mt-0.5" />
                    <span>Official civil service document authorized for official training, field survey implementation, and departmental exams.</span>
                  </div>

                  {downloadSuccess ? (
                    <div className="py-4 text-center text-xs font-semibold text-emerald-800 space-y-1 bg-emerald-50 rounded-xl border border-emerald-200">
                      <CheckCircle2 className="h-6 w-6 text-emerald-600 mx-auto" />
                      <p>Document Access Granted</p>
                      <p className="text-[11px] text-slate-500">Official technical manual downloaded successfully.</p>
                    </div>
                  ) : (
                    <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setActiveDocModal(null)}
                        className="text-xs"
                      >
                        Close
                      </Button>
                      <Button
                        size="sm"
                        onClick={handleConfirmDownload}
                        className="bg-[#1E3A8A] hover:bg-[#172554] text-white text-xs font-semibold gap-1.5 shadow-xs cursor-pointer"
                      >
                        <Download className="h-3.5 w-3.5" /> Download Document
                      </Button>
                    </div>
                  )}
                </div>
              </>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
