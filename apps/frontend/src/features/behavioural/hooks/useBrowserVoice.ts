"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** Browser-native board voice with a completion signal for microphone handoff. */
export function useBrowserVoice() {
  const [speaking, setSpeaking] = useState(false);
  const finishRef = useRef<(() => void) | null>(null);

  const stop = useCallback(() => {
    window.speechSynthesis?.cancel();
    finishRef.current?.();
    finishRef.current = null;
    setSpeaking(false);
  }, []);

  const speak = useCallback(async (text: string): Promise<void> => {
    stop();
    if (!("speechSynthesis" in window)) return;
    setSpeaking(true);
    await new Promise<void>((resolve) => {
      let done = false;
      const finish = () => {
        if (done) return;
        done = true;
        if (finishRef.current === finish) finishRef.current = null;
        setSpeaking(false);
        resolve();
      };
      finishRef.current = finish;
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "en-IN";
      utterance.onend = finish;
      utterance.onerror = finish;
      window.speechSynthesis.speak(utterance);
    });
  }, [stop]);

  useEffect(() => stop, [stop]);
  return { speaking, speak, stop };
}
