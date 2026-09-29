"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Maximize2,
  CheckCircle2,
  ExternalLink,
  Check,
  Film,
  Clock,
  AlertCircle,
} from "lucide-react";
import { extractYouTubeId, getYouTubeEmbedUrl } from "@/lib/video";
import { LessonVideoMapping } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export interface LessonVideoProps {
  title: string;
  videoMapping?: LessonVideoMapping | null;
  videoUrl?: string | null;
  startTime?: number | null;
  endTime?: number | null;
  sourceVideoTitle?: string | null;
  topic?: string | null;
  learningObjective?: string | null;
  durationMinutes?: number;
  isCompleted?: boolean;
  onProgress?: (percent: number) => void;
  onComplete?: () => void;
}

export function LessonVideo({
  title,
  videoMapping,
  videoUrl,
  startTime,
  endTime,
  sourceVideoTitle,
  topic,
  learningObjective,
  durationMinutes,
  isCompleted: initialCompleted = false,
  onProgress,
  onComplete,
}: LessonVideoProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isCompleted, setIsCompleted] = useState(initialCompleted);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    setIsCompleted(initialCompleted);
  }, [initialCompleted]);

  // Consolidate single reliable mapping data object
  const activeUrl = videoMapping?.source_url ?? videoUrl ?? null;
  const activeStart = videoMapping?.start_time ?? startTime ?? null;
  const activeEnd = videoMapping?.end_time ?? endTime ?? null;
  const activeSourceTitle = videoMapping?.source_video_title ?? sourceVideoTitle ?? null;
  const activeTopic = videoMapping?.topic ?? topic ?? null;
  const activeVideoId = videoMapping?.source_video_id ?? extractYouTubeId(activeUrl);

  const calculatedDuration =
    typeof activeEnd === "number" && typeof activeStart === "number" && activeEnd > activeStart
      ? Math.max(1, Math.round((activeEnd - activeStart) / 60))
      : videoMapping?.duration_minutes ?? durationMinutes ?? null;

  const embedUrl = getYouTubeEmbedUrl(activeUrl || activeVideoId, activeStart, activeEnd);

  const formatTimestamp = (totalSeconds: number) => {
    if (isNaN(totalSeconds) || totalSeconds < 0) return "00:00";
    const hrs = Math.floor(totalSeconds / 3600);
    const mins = Math.floor((totalSeconds % 3600) / 60);
    const secs = Math.floor(totalSeconds % 60);
    if (hrs > 0) {
      return `${hrs}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    }
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const handleToggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen?.().catch((err) => {
        console.error("Error attempting to enable fullscreen:", err);
      });
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.().catch((err) => {
        console.error("Error attempting to exit fullscreen:", err);
      });
      setIsFullscreen(false);
    }
  };

  const handleMarkWatched = () => {
    const nextState = !isCompleted;
    setIsCompleted(nextState);
    if (nextState && onComplete) {
      onComplete();
    }
  };

  // --------------------------------------------------------------------------
  // 1. YOUTUBE VIDEO SEGMENT EMBED
  // --------------------------------------------------------------------------
  if (embedUrl && activeVideoId) {
    const hasSegmentTimestamps =
      typeof activeStart === "number" && typeof activeEnd === "number" && activeEnd > activeStart;

    const iframeKey = `${activeVideoId}_${activeStart ?? 0}_${activeEnd ?? 0}`;

    return (
      <div ref={containerRef} className="space-y-3 w-full">
        {/* Top Video Header Ribbon with Segment & Source Details */}
        <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="font-bold text-slate-800 flex items-center gap-1.5">
              <Film className="h-3.5 w-3.5 text-[#1E3A8A]" />
              Curated Video Segment
            </span>

            {calculatedDuration && (
              <Badge
                variant="outline"
                className="text-[10px] text-slate-600 font-semibold border-slate-300 bg-slate-50 flex items-center gap-1"
              >
                <Clock className="h-3 w-3 text-slate-400" />
                Duration: {calculatedDuration} min
              </Badge>
            )}

            {hasSegmentTimestamps && (
              <Badge
                variant="secondary"
                className="text-[10px] text-teal-700 bg-teal-50 border border-teal-200/80 font-mono font-medium"
              >
                Segment: {formatTimestamp(activeStart!)} – {formatTimestamp(activeEnd!)}
              </Badge>
            )}

            {activeTopic && (
              <Badge variant="outline" className="text-[10px] text-blue-700 bg-blue-50 border-blue-200">
                {activeTopic}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            {activeUrl && (
              <a
                href={activeUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#1E3A8A] hover:text-[#0D9488] transition-colors"
                title="Open original video source on YouTube"
              >
                <span>Source Video</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            )}
          </div>
        </div>

        {/* 16:9 Video Player Frame (Remounted on lesson/segment change via iframeKey) */}
        <div className="aspect-video w-full overflow-hidden rounded-2xl bg-slate-950 shadow-lg border border-slate-800 relative group">
          <iframe
            key={iframeKey}
            src={`${embedUrl}${embedUrl.includes("?") ? "&" : "?"}enablejsapi=1&origin=${typeof window !== "undefined" ? window.location.origin : ""}`}
            title={title}
            className="size-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
            referrerPolicy="strict-origin-when-cross-origin"
            loading="lazy"
          />
        </div>

        {/* Video Player Action & Completion Bar */}
        <div className="bg-white border border-slate-200/90 rounded-xl px-4 py-3 flex flex-wrap items-center justify-between gap-3 shadow-2xs">
          <div className="space-y-0.5 max-w-lg">
            <div className="flex items-center gap-2 text-xs text-slate-600">
              <span className="font-bold text-slate-900 line-clamp-1">
                {title}
              </span>
            </div>
            {activeSourceTitle && (
              <p className="text-[11px] text-slate-500 line-clamp-1">
                <span className="font-medium text-slate-600">Relevant source video:</span>{" "}
                {activeSourceTitle}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <Button
              type="button"
              size="sm"
              variant="default"
              onClick={handleMarkWatched}
              className={`h-8 px-3.5 text-xs font-bold rounded-xl transition-all cursor-pointer ${
                isCompleted
                  ? "bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                  : "navy-teal-gradient hover:opacity-95 text-white shadow-sm"
              }`}
            >
              {isCompleted ? (
                <>
                  <Check className="h-3.5 w-3.5 mr-1.5" />
                  Segment Completed
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />
                  Mark Segment as Watched
                </>
              )}
            </Button>

            <button
              type="button"
              onClick={handleToggleFullscreen}
              title="Fullscreen"
              className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // 2. FALLBACK (When no sufficiently relevant video exists)
  // --------------------------------------------------------------------------
  return (
    <div className="flex aspect-video w-full flex-col items-center justify-center gap-3 rounded-2xl border border-slate-200 bg-gradient-to-br from-slate-900 to-slate-950 p-6 text-center text-white shadow-sm">
      <div className="h-12 w-12 rounded-2xl bg-slate-800/80 border border-slate-700 flex items-center justify-center shadow-lg">
        <AlertCircle className="size-6 text-amber-400" aria-hidden="true" />
      </div>
      <h4 className="text-base font-bold text-slate-100">
        Learning material unavailable for this lesson
      </h4>
      <p className="text-xs text-slate-400 max-w-md">
        This lesson is queued for verified domain content mapping. Please review the structured lecture notes below and proceed with the practical concept check.
      </p>
    </div>
  );
}
