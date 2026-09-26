"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { uploadApi } from "@/lib/api";

const FILLER_PATTERN = /\b(um+|uh+|erm+|hmm+|you know|i mean|sort of|kind of|basically)\b/gi;
const TARGET_SAMPLE_RATE = 16_000;

export function countFillers(text: string) {
  return text.match(FILLER_PATTERN)?.length ?? 0;
}

function wordCount(text: string) {
  return text.trim().split(/\s+/).filter(Boolean).length;
}

function join(a: string, b: string) {
  return [a.trim(), b.trim()].filter(Boolean).join(" ");
}

function microphoneError(reason: unknown) {
  if (reason instanceof DOMException && (reason.name === "NotAllowedError" || reason.name === "SecurityError")) {
    return "Microphone access was blocked. Allow microphone access for localhost, then try again.";
  }
  if (reason instanceof DOMException && reason.name === "NotFoundError") {
    return "No microphone was found. Connect a microphone and try again.";
  }
  return "The microphone could not start. Check browser permissions and try again.";
}

function mergeSamples(chunks: Float32Array[]) {
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const merged = new Float32Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    merged.set(chunk, offset);
    offset += chunk.length;
  }
  return merged;
}

function resample(samples: Float32Array, sourceRate: number, targetRate: number) {
  if (sourceRate === targetRate) return samples;
  const ratio = sourceRate / targetRate;
  const output = new Float32Array(Math.max(1, Math.floor(samples.length / ratio)));
  for (let i = 0; i < output.length; i++) {
    const start = Math.floor(i * ratio);
    const end = Math.max(start + 1, Math.min(samples.length, Math.floor((i + 1) * ratio)));
    let sum = 0;
    for (let j = start; j < end; j++) sum += samples[j];
    output[i] = sum / (end - start);
  }
  return output;
}

function writeAscii(view: DataView, offset: number, text: string) {
  for (let i = 0; i < text.length; i++) view.setUint8(offset + i, text.charCodeAt(i));
}

function encodeWav(chunks: Float32Array[], sourceRate: number) {
  const samples = resample(mergeSamples(chunks), sourceRate, TARGET_SAMPLE_RATE);
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  writeAscii(view, 0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeAscii(view, 8, "WAVE");
  writeAscii(view, 12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, TARGET_SAMPLE_RATE, true);
  view.setUint32(28, TARGET_SAMPLE_RATE * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeAscii(view, 36, "data");
  view.setUint32(40, samples.length * 2, true);
  for (let i = 0; i < samples.length; i++) {
    const value = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(44 + i * 2, value < 0 ? value * 0x8000 : value * 0x7fff, true);
  }
  return new Blob([buffer], { type: "audio/wav" });
}

/** Captures PCM immediately after permission, encodes 16 kHz mono WAV, and sends it to Sarvam STT. */
export function useSpeechCapture(onText: (text: string) => void) {
  const [supported, setSupported] = useState(false);
  const [starting, setStarting] = useState(false);
  const [listening, setListening] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeRef = useRef(false);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const silentGainRef = useRef<GainNode | null>(null);
  const sampleChunksRef = useRef<Float32Array[]>([]);
  const sampleRateRef = useRef(48_000);
  const baseTextRef = useRef("");
  const currentTextRef = useRef("");
  const dictatedWordsRef = useRef(0);
  const onTextRef = useRef(onText);
  const completionRef = useRef<Promise<string> | null>(null);
  const resolveCompletionRef = useRef<((text: string) => void) | null>(null);

  useEffect(() => {
    onTextRef.current = onText;
  });

  useEffect(() => {
    // Client capability detection must happen after hydration.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSupported(typeof navigator.mediaDevices?.getUserMedia === "function" && typeof window.AudioContext === "function");
  }, []);

  const releaseCapture = useCallback(() => {
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    silentGainRef.current?.disconnect();
    if (processorRef.current) processorRef.current.onaudioprocess = null;
    processorRef.current = null;
    sourceRef.current = null;
    silentGainRef.current = null;
    const context = audioContextRef.current;
    audioContextRef.current = null;
    if (context && context.state !== "closed") void context.close();
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  const transcribe = useCallback(async () => {
    const chunks = sampleChunksRef.current;
    sampleChunksRef.current = [];
    const sourceRate = sampleRateRef.current;
    releaseCapture();
    setListening(false);
    setBusy(true);

    let completedText = currentTextRef.current;
    try {
      const wav = encodeWav(chunks, sourceRate);
      if (wav.size < 1_644) throw new Error("No speech was recorded. Speak after the mic turns red, then stop dictation.");
      const form = new FormData();
      form.append("audio", wav, "dictation.wav");
      const result = await uploadApi<{ text: string; provider: "sarvam" }>("/behavioural/interview/transcribe", form);
      dictatedWordsRef.current += wordCount(result.text);
      completedText = join(baseTextRef.current, result.text);
      currentTextRef.current = completedText;
      onTextRef.current(completedText);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sarvam could not transcribe the recording. Try again.");
    } finally {
      setBusy(false);
      resolveCompletionRef.current?.(completedText);
      resolveCompletionRef.current = null;
      completionRef.current = null;
    }
  }, [releaseCapture]);

  const start = useCallback(async (currentText: string) => {
    if (activeRef.current || starting || busy) return;
    setError(null);
    setStarting(true);
    baseTextRef.current = currentText.trim();
    currentTextRef.current = currentText.trim();
    sampleChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 },
      });
      streamRef.current = stream;
      const context = new AudioContext();
      audioContextRef.current = context;
      await context.resume();
      sampleRateRef.current = context.sampleRate;
      const source = context.createMediaStreamSource(stream);
      const processor = context.createScriptProcessor(2048, 1, 1);
      const silentGain = context.createGain();
      silentGain.gain.value = 0;
      sourceRef.current = source;
      processorRef.current = processor;
      silentGainRef.current = silentGain;
      processor.onaudioprocess = (event) => {
        if (activeRef.current) sampleChunksRef.current.push(new Float32Array(event.inputBuffer.getChannelData(0)));
      };
      completionRef.current = new Promise<string>((resolve) => {
        resolveCompletionRef.current = resolve;
      });
      activeRef.current = true;
      source.connect(processor);
      processor.connect(silentGain);
      silentGain.connect(context.destination);
      setListening(true);
    } catch (reason) {
      activeRef.current = false;
      releaseCapture();
      setError(microphoneError(reason));
    } finally {
      setStarting(false);
    }
  }, [busy, releaseCapture, starting]);

  const stop = useCallback(() => {
    if (!activeRef.current) return;
    activeRef.current = false;
    setListening(false);
    void transcribe();
  }, [transcribe]);

  const finish = useCallback(async () => {
    const completion = completionRef.current;
    stop();
    return completion ? await completion : currentTextRef.current;
  }, [stop]);

  const takeDictatedWords = useCallback(() => {
    const words = dictatedWordsRef.current;
    dictatedWordsRef.current = 0;
    return words;
  }, []);

  useEffect(
    () => () => {
      activeRef.current = false;
      sampleChunksRef.current = [];
      releaseCapture();
    },
    [releaseCapture],
  );

  return { supported, starting, listening, busy, error, start, stop, finish, takeDictatedWords };
}
