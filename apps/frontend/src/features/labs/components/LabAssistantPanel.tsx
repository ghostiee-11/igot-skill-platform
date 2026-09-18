"use client";

import { useEffect, useRef, useState } from "react";
import { Bot, Lightbulb, Loader2, Send, Sparkles, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Markdown } from "@/components/shared/Markdown";
import { fetchApi } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface AssistantResponse {
  response: string;
  source: string;
  suggestions: string[];
}

const INITIAL_MESSAGE: Message = {
  role: "assistant",
  content:
    "Tell me where you’re stuck. I can explain errors, ask guiding questions, and suggest a small next experiment—but I won’t write the solution for you.",
};

const INITIAL_SUGGESTIONS = ["Help me understand the task", "What should I test first?", "Explain my latest error"];

export function LabAssistantPanel({
  labId,
  labTitle,
  currentCode,
  activeOutput,
  onClose,
}: {
  labId: number;
  labTitle: string;
  currentCode: string;
  activeOutput?: string | null;
  onClose: () => void;
}) {
  const [messages, setMessages] = useState<Message[]>([INITIAL_MESSAGE]);
  const [suggestions, setSuggestions] = useState(INITIAL_SUGGESTIONS);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const thread = threadRef.current;
    if (thread) thread.scrollTop = thread.scrollHeight;
  }, [messages, sending]);

  const send = async (text = input) => {
    const message = text.trim();
    if (!message || sending) return;
    const history = messages.slice(-8);
    setMessages((current) => [...current, { role: "user", content: message }]);
    setInput("");
    setSuggestions([]);
    setError(null);
    setSending(true);
    try {
      const result = await fetchApi<AssistantResponse>(`/technical-courses/labs/${labId}/assistant`, {
        method: "POST",
        body: JSON.stringify({
          message,
          current_code: currentCode,
          active_output: activeOutput || null,
          history,
        }),
      });
      setMessages((current) => [...current, { role: "assistant", content: result.response }]);
      setSuggestions(result.suggestions);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The lab guide could not respond. Try again.");
    } finally {
      setSending(false);
    }
  };

  return (
    <aside
      id="lab-assistant-panel"
      aria-label="Lab assistant"
      className="fixed inset-x-0 bottom-0 top-20 z-50 flex min-h-0 flex-col border-l border-slate-200 bg-white shadow-2xl lg:static lg:z-auto lg:w-[23rem] lg:shrink-0 lg:shadow-none xl:w-[26rem]"
    >
      <header className="flex shrink-0 items-start gap-3 border-b border-slate-200 px-4 py-3">
        <span className="mt-0.5 inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#1E3A8A] to-[#0D9488] text-white">
          <Sparkles className="size-4" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold text-slate-900">Lab guide</h2>
          <p className="truncate text-xs text-slate-500" title={labTitle}>
            Guided hints · no direct answers
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close lab guide"
          className="inline-flex size-8 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-900"
        >
          <X className="size-4" aria-hidden="true" />
        </button>
      </header>

      <div ref={threadRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto px-4 py-4" aria-live="polite">
        {messages.map((message, index) => (
          <div key={`${message.role}-${index}`} className={`flex gap-2.5 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
            {message.role === "assistant" && (
              <span className="mt-0.5 inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-blue-50 text-[#1E3A8A]">
                <Bot className="size-3.5" aria-hidden="true" />
              </span>
            )}
            <div
              className={`max-w-[86%] rounded-2xl px-3 py-2 text-sm leading-relaxed ${
                message.role === "user" ? "rounded-br-md bg-[#1E3A8A] text-white" : "rounded-bl-md bg-slate-100 text-slate-700"
              }`}
            >
              {message.role === "assistant" ? (
                <Markdown content={message.content} className="prose prose-sm max-w-none prose-p:my-1 prose-code:break-words" />
              ) : (
                <p className="whitespace-pre-wrap text-pretty">{message.content}</p>
              )}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex items-center gap-2.5 text-xs text-slate-500" role="status">
            <span className="inline-flex size-7 items-center justify-center rounded-full bg-blue-50 text-[#1E3A8A]">
              <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
            </span>
            Thinking about your next step…
          </div>
        )}
        {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">{error}</p>}
      </div>

      <div className="shrink-0 border-t border-slate-200 p-3">
        {suggestions.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-1.5">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => void send(suggestion)}
                disabled={sending}
                className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-left text-[11px] font-medium text-slate-600 transition-colors hover:border-[#1E3A8A]/40 hover:bg-blue-50 hover:text-[#1E3A8A] disabled:opacity-50"
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}
        <div className="rounded-xl border border-slate-300 bg-white p-2 focus-within:border-[#1E3A8A] focus-within:ring-2 focus-within:ring-[#1E3A8A]/15">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void send();
              }
            }}
            rows={3}
            disabled={sending}
            aria-label="Ask the lab guide"
            placeholder="Ask for a hint or explain an error…"
            className="block w-full resize-none bg-transparent px-1 text-sm text-slate-900 outline-none placeholder:text-slate-400 disabled:opacity-60"
          />
          <div className="mt-1 flex items-center justify-between gap-2 pr-12">
            <span className="inline-flex items-center gap-1 text-[10px] text-slate-400">
              <Lightbulb className="size-3" aria-hidden="true" />
              Coaches your reasoning
            </span>
            <Button size="sm" onClick={() => void send()} disabled={sending || !input.trim()} aria-label="Send to lab guide">
              {sending ? <Loader2 className="size-3.5 animate-spin" aria-hidden="true" /> : <Send className="size-3.5" aria-hidden="true" />}
            </Button>
          </div>
        </div>
      </div>
    </aside>
  );
}
