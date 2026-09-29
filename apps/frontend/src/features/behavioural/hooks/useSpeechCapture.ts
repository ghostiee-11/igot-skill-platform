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
    return "Microphone access was blocked. Please allow microphone permissions in your browser, then try again.";
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

/** Captures PCM audio and connects to the multi-provider speech transcription pipeline. */
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
  const liveTranscriptRef = useRef("");
  const dictatedWordsRef = useRef(0);
  const onTextRef = useRef(onText);
  const completionRef = useRef<Promise<string> | null>(null);
  const resolveCompletionRef = useRef<((text: string) => void) | null>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    onTextRef.current = onText;
  });

  useEffect(() => {
    // Client capability detection must happen after hydration.
    setSupported(
      typeof navigator !== "undefined" &&
        Boolean(navigator.mediaDevices?.getUserMedia) &&
        (typeof window !== "undefined" && Boolean(window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext))
    );
  }, []);

  const releaseCapture = useCallback(() => {
    try {
      if (recognitionRef.current) {
        recognitionRef.current.onresult = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.stop();
        recognitionRef.current = null;
      }
    } catch {
      // Ignored
    }

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
    const liveText = liveTranscriptRef.current.trim();
    liveTranscriptRef.current = "";

    releaseCapture();
    setListening(false);
    setBusy(true);

    let completedText = currentTextRef.current;
    try {
      const wav = encodeWav(chunks, sourceRate);
      const form = new FormData();
      form.append("audio", wav, "dictation.wav");
      if (liveText) {
        form.append("client_transcript", liveText);
      }

      const result = await uploadApi<{ text: string; provider?: string }>("/behavioural/interview/transcribe", form);
      const transcribedText = result.text.trim() || liveText;

      if (!transcribedText) {
        throw new Error("No audible speech detected. Speak clearly and try again.");
      }

      dictatedWordsRef.current += wordCount(transcribedText);
      completedText = join(baseTextRef.current, transcribedText);
      currentTextRef.current = completedText;
      onTextRef.current(completedText);
      setError(null);
    } catch (reason) {
      // If backend API failed but live speech recognition captured words, use that seamlessly
      if (liveText) {
        dictatedWordsRef.current += wordCount(liveText);
        completedText = join(baseTextRef.current, liveText);
        currentTextRef.current = completedText;
        onTextRef.current(completedText);
        setError(null);
      } else {
        const message = reason instanceof Error ? reason.message : "Transcription failed. Please try speaking again.";
        setError(message);
      }
    } finally {
      setBusy(false);
      resolveCompletionRef.current?.(completedText);
      resolveCompletionRef.current = null;
      completionRef.current = null;
    }
  }, [releaseCapture]);

  const start = useCallback(
    async (currentText: string) => {
      if (activeRef.current || starting || busy) return;
      setError(null);
      setStarting(true);
      baseTextRef.current = currentText.trim();
      currentTextRef.current = currentText.trim();
      liveTranscriptRef.current = "";
      sampleChunksRef.current = [];

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true, channelCount: 1 },
        });
        streamRef.current = stream;

        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        const context = new AudioCtx();
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
          if (activeRef.current) {
            sampleChunksRef.current.push(new Float32Array(event.inputBuffer.getChannelData(0)));
          }
        };

        // Initialize SpeechRecognition if supported in browser for live transcription
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const SpeechRec = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (SpeechRec) {
          try {
            const recognition = new SpeechRec();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = "en-IN";
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            recognition.onresult = (event: any) => {
              let live = "";
              for (let i = 0; i < event.results.length; i++) {
                live += event.results[i][0].transcript + " ";
              }
              const cleanLive = live.trim();
              if (cleanLive && activeRef.current) {
                liveTranscriptRef.current = cleanLive;
                const updated = join(baseTextRef.current, cleanLive);
                currentTextRef.current = updated;
                onTextRef.current(updated);
              }
            };
            recognition.onerror = () => {
              // Ignore recognition error; fallback to audio WAV backend transcription
            };
            recognition.start();
            recognitionRef.current = recognition;
          } catch {
            // SpeechRecognition start error ignored
          }
        }

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
    },
    [busy, releaseCapture, starting]
  );

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
    [releaseCapture]
  );

  return { supported, starting, listening, busy, error, start, stop, finish, takeDictatedWords };
}
