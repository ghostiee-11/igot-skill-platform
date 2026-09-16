"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { FaceLandmarker } from "@mediapipe/tasks-vision";

const MEDIAPIPE_VERSION = "1.0.1";
const WASM_BASE = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}/wasm`;
const FACE_MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

const SAMPLE_MS = 200;
const PUBLISH_MS = 1000;
// Head rotation beyond these angles counts as not facing the camera.
const MAX_YAW_DEG = 20;
const MAX_PITCH_DEG = 18;
// A head turn is counted each time yaw moves this far from where it last settled.
const HEAD_TURN_DEG = 15;
// Microphone RMS level (0-100) at or above which the officer is treated as speaking.
const VOICE_LEVEL = 8;
const PAUSE_MS = 2000;
const NOSE_TIP = 1;
const XNNPACK_INFO = "Created TensorFlow Lite XNNPACK delegate for CPU";

export type MediaStatus = "idle" | "requesting" | "live" | "denied" | "unavailable" | "stopped";
export type AnalyserStatus = "off" | "loading" | "ready" | "unavailable";

export interface DeliveryMetrics {
  face_presence_percent: number | null;
  eye_contact_percent: number | null;
  posture_stability_score: number | null;
  head_movement_rate: number | null;
  speaking_seconds: number | null;
  pauses_count: number | null;
}

interface Tally {
  startedAt: number;
  videoSamples: number;
  faceSamples: number;
  poseSamples: number;
  facingSamples: number;
  noseX: number[];
  noseY: number[];
  headTurns: number;
  yawAnchor: number | null;
  audioSamples: number;
  voicedMs: number;
  silenceMs: number;
  hasSpoken: boolean;
  pauses: number;
}

const EMPTY_METRICS: DeliveryMetrics = {
  face_presence_percent: null,
  eye_contact_percent: null,
  posture_stability_score: null,
  head_movement_rate: null,
  speaking_seconds: null,
  pauses_count: null,
};

function newTally(): Tally {
  return {
    startedAt: performance.now(),
    videoSamples: 0,
    faceSamples: 0,
    poseSamples: 0,
    facingSamples: 0,
    noseX: [],
    noseY: [],
    headTurns: 0,
    yawAnchor: null,
    audioSamples: 0,
    voicedMs: 0,
    silenceMs: 0,
    hasSpoken: false,
    pauses: 0,
  };
}

function std(values: number[]) {
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  return Math.sqrt(values.reduce((a, b) => a + (b - mean) ** 2, 0) / values.length);
}

function summarize(t: Tally): DeliveryMetrics {
  const minutes = (performance.now() - t.startedAt) / 60000;
  return {
    face_presence_percent: t.videoSamples ? Math.round((t.faceSamples / t.videoSamples) * 100) : null,
    eye_contact_percent: t.poseSamples ? Math.round((t.facingSamples / t.poseSamples) * 100) : null,
    // Nose-tip jitter in normalised frame units is about 0.003 when still and 0.03+ when moving a lot.
    posture_stability_score:
      t.noseX.length >= 10
        ? Math.round(Math.max(0, Math.min(100, 100 - Math.hypot(std(t.noseX), std(t.noseY)) * 2000)))
        : null,
    head_movement_rate:
      t.faceSamples >= 10 && minutes > 0.1 ? Math.round((t.headTurns / minutes) * 10) / 10 : null,
    speaking_seconds: t.audioSamples ? Math.round(t.voicedMs / 100) / 10 : null,
    pauses_count: t.audioSamples ? t.pauses : null,
  };
}

// The facial transformation matrix is a column-major 4x4; its rotation gives yaw and pitch.
function headAngles(m: number[]) {
  const yaw = (Math.asin(Math.max(-1, Math.min(1, -m[2]))) * 180) / Math.PI;
  const pitch = (Math.atan2(m[6], m[10]) * 180) / Math.PI;
  return { yaw, pitch };
}

function installMediaPipeLogFilter() {
  // MediaPipe captures console.error during initialization, so install the filter before importing the WASM module.
  const originalError = console.error;
  const filteredError = (...args: unknown[]) => {
    const message = args.map((value) => String(value)).join(" ");
    if (message.includes(XNNPACK_INFO)) return;
    originalError(...args);
  };
  console.error = filteredError;
  return () => {
    if (console.error === filteredError) console.error = originalError;
  };
}

/**
 * Owns the camera and microphone for the interview: requests them only when asked, measures
 * observable delivery signals locally, and guarantees the devices are released when the interview
 * stops, the component unmounts or the page is hidden for navigation.
 */
export function useInterviewMedia() {
  const [status, setStatus] = useState<MediaStatus>("idle");
  const [analyser, setAnalyser] = useState<AnalyserStatus>("off");
  const [cameraOn, setCameraOn] = useState(true);
  const [micOn, setMicOn] = useState(true);
  const [faceVisible, setFaceVisible] = useState<boolean | null>(null);
  const [facingCamera, setFacingCamera] = useState<boolean | null>(null);
  const [audioLevel, setAudioLevel] = useState(0);
  const [session, setSession] = useState<DeliveryMetrics>(EMPTY_METRICS);

  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserNodeRef = useRef<AnalyserNode | null>(null);
  const landmarkerRef = useRef<FaceLandmarker | null>(null);
  const restoreConsoleErrorRef = useRef<(() => void) | null>(null);
  const loopRef = useRef<number | null>(null);
  // Bumped on every start and stop so a permission prompt or model load that resolves late knows it is stale.
  const generationRef = useRef(0);
  const sessionTally = useRef<Tally>(newTally());
  const turnTally = useRef<Tally>(newTally());
  const cameraOnRef = useRef(true);
  const micOnRef = useRef(true);
  const lastPublishRef = useRef(0);
  const lastVideoTimeRef = useRef(-1);

  const stop = useCallback(() => {
    generationRef.current += 1;
    if (loopRef.current !== null) {
      window.clearInterval(loopRef.current);
      loopRef.current = null;
    }
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
    analyserNodeRef.current = null;
    if (audioCtxRef.current && audioCtxRef.current.state !== "closed") void audioCtxRef.current.close();
    audioCtxRef.current = null;
    landmarkerRef.current?.close();
    landmarkerRef.current = null;
    restoreConsoleErrorRef.current?.();
    restoreConsoleErrorRef.current = null;
    setStatus((current) => (current === "idle" ? current : "stopped"));
    setAnalyser("off");
    setFaceVisible(null);
    setFacingCamera(null);
    setAudioLevel(0);
  }, []);

  const sample = useCallback(() => {
    const now = performance.now();
    const tallies = [sessionTally.current, turnTally.current];

    const node = analyserNodeRef.current;
    if (node && micOnRef.current) {
      const buffer = new Uint8Array(node.fftSize);
      node.getByteTimeDomainData(buffer);
      let sum = 0;
      for (const v of buffer) {
        const x = (v - 128) / 128;
        sum += x * x;
      }
      const level = Math.min(100, Math.round(Math.sqrt(sum / buffer.length) * 300));
      setAudioLevel(level);
      for (const t of tallies) {
        t.audioSamples += 1;
        if (level >= VOICE_LEVEL) {
          if (t.hasSpoken && t.silenceMs >= PAUSE_MS) t.pauses += 1;
          t.voicedMs += SAMPLE_MS;
          t.silenceMs = 0;
          t.hasSpoken = true;
        } else {
          t.silenceMs += SAMPLE_MS;
        }
      }
    }

    const video = videoRef.current;
    const landmarker = landmarkerRef.current;
    if (
      video &&
      landmarker &&
      cameraOnRef.current &&
      video.readyState >= 2 &&
      video.currentTime !== lastVideoTimeRef.current
    ) {
      lastVideoTimeRef.current = video.currentTime;
      try {
        const result = landmarker.detectForVideo(video, now);
        const face = result.faceLandmarks[0];
        let facing: boolean | null = null;
        for (const t of tallies) t.videoSamples += 1;
        if (face) {
          const matrix = result.facialTransformationMatrixes?.[0]?.data;
          if (matrix) {
            const { yaw, pitch } = headAngles(matrix);
            facing = Math.abs(yaw) <= MAX_YAW_DEG && Math.abs(pitch) <= MAX_PITCH_DEG;
            for (const t of tallies) {
              t.poseSamples += 1;
              if (facing) t.facingSamples += 1;
              if (t.yawAnchor === null) t.yawAnchor = yaw;
              else if (Math.abs(yaw - t.yawAnchor) >= HEAD_TURN_DEG) {
                t.headTurns += 1;
                t.yawAnchor = yaw;
              }
            }
          }
          for (const t of tallies) {
            t.faceSamples += 1;
            t.noseX.push(face[NOSE_TIP].x);
            t.noseY.push(face[NOSE_TIP].y);
          }
        }
        setFaceVisible(Boolean(face));
        setFacingCamera(facing);
      } catch (err) {
        landmarkerRef.current?.close();
        landmarkerRef.current = null;
        restoreConsoleErrorRef.current?.();
        restoreConsoleErrorRef.current = null;
        setAnalyser("unavailable");
        setFaceVisible(null);
        setFacingCamera(null);
        console.warn("Face analysis disabled after an inference failure:", err instanceof Error ? err.message : String(err));
      }
    }

    if (now - lastPublishRef.current >= PUBLISH_MS) {
      lastPublishRef.current = now;
      setSession(summarize(sessionTally.current));
    }
  }, []);

  const loadLandmarker = useCallback(async (generation: number) => {
    setAnalyser("loading");
    restoreConsoleErrorRef.current?.();
    restoreConsoleErrorRef.current = installMediaPipeLogFilter();
    try {
      const { FaceLandmarker, FilesetResolver } = await import("@mediapipe/tasks-vision");
      const fileset = await FilesetResolver.forVisionTasks(WASM_BASE);
      const create = (delegate: "GPU" | "CPU") =>
        FaceLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: FACE_MODEL_URL, delegate },
          runningMode: "VIDEO",
          numFaces: 1,
          outputFacialTransformationMatrixes: true,
        });
      const landmarker = await create("GPU").catch(() => create("CPU"));
      if (generation !== generationRef.current) {
        landmarker.close();
        return;
      }
      landmarkerRef.current = landmarker;
      setAnalyser("ready");
    } catch (err) {
      restoreConsoleErrorRef.current?.();
      restoreConsoleErrorRef.current = null;
      console.warn("Face analysis could not load:", err);
      if (generation === generationRef.current) setAnalyser("unavailable");
    }
  }, []);

  const start = useCallback(async (): Promise<boolean> => {
    if (streamRef.current) return true;
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setStatus("unavailable");
      return false;
    }
    const generation = ++generationRef.current;
    setStatus("requesting");
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" },
        audio: { echoCancellation: true, noiseSuppression: true },
      });
    } catch (err) {
      if (generation === generationRef.current) {
        setStatus(err instanceof DOMException && err.name === "NotAllowedError" ? "denied" : "unavailable");
      }
      return false;
    }
    // Stopped or unmounted while the permission prompt was open: release the devices at once.
    if (generation !== generationRef.current) {
      stream.getTracks().forEach((track) => track.stop());
      return false;
    }

    streamRef.current = stream;
    cameraOnRef.current = true;
    micOnRef.current = true;
    setCameraOn(true);
    setMicOn(true);
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      void videoRef.current.play().catch(() => {});
    }
    try {
      const AudioCtx =
        window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx();
      const node = ctx.createAnalyser();
      node.fftSize = 1024;
      ctx.createMediaStreamSource(stream).connect(node);
      audioCtxRef.current = ctx;
      analyserNodeRef.current = node;
    } catch (err) {
      console.warn("Microphone level meter unavailable:", err);
    }

    sessionTally.current = newTally();
    turnTally.current = newTally();
    setSession(EMPTY_METRICS);
    loopRef.current = window.setInterval(sample, SAMPLE_MS);
    setStatus("live");
    void loadLandmarker(generation);
    return true;
  }, [loadLandmarker, sample]);

  const attachVideo = useCallback((el: HTMLVideoElement | null) => {
    videoRef.current = el;
    if (el && streamRef.current && el.srcObject !== streamRef.current) {
      el.srcObject = streamRef.current;
      void el.play().catch(() => {});
    }
  }, []);

  const toggleCamera = useCallback(() => {
    const track = streamRef.current?.getVideoTracks()[0];
    if (!track) return;
    track.enabled = !track.enabled;
    cameraOnRef.current = track.enabled;
    setCameraOn(track.enabled);
    if (!track.enabled) {
      setFaceVisible(null);
      setFacingCamera(null);
    }
  }, []);

  const toggleMic = useCallback((): boolean => {
    const track = streamRef.current?.getAudioTracks()[0];
    if (!track) return micOnRef.current;
    track.enabled = !track.enabled;
    micOnRef.current = track.enabled;
    setMicOn(track.enabled);
    if (!track.enabled) setAudioLevel(0);
    return track.enabled;
  }, []);

  const takeTurnMetrics = useCallback((): DeliveryMetrics => {
    const metrics = summarize(turnTally.current);
    turnTally.current = newTally();
    return metrics;
  }, []);

  const resetTurn = useCallback(() => {
    turnTally.current = newTally();
  }, []);

  const getStream = useCallback(() => streamRef.current, []);

  useEffect(() => {
    window.addEventListener("pagehide", stop);
    return () => {
      window.removeEventListener("pagehide", stop);
      stop();
    };
  }, [stop]);

  return {
    status,
    analyser,
    cameraOn,
    micOn,
    faceVisible,
    facingCamera,
    audioLevel,
    session,
    start,
    stop,
    attachVideo,
    toggleCamera,
    toggleMic,
    takeTurnMetrics,
    resetTurn,
    getStream,
  };
}
