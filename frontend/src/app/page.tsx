"use client";

import { useState, useEffect, useRef } from "react";
import { streamAgentQuery, uploadDocument } from "@/lib/api";
import {
  Send,
  Bot,
  User,
  Sparkles,
  Cpu,
  Search,
  Calculator,
  Database,
  Upload,
  CheckCircle2,
  Loader2,
} from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  executedAction?: string;
  sourcesCount?: number;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setSessionId(`session_${Date.now()}`);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus(null);
    try {
      const res = await uploadDocument(file);
      setUploadStatus(`Ingested "${res.filename}" (${res.chunks_ingested ?? "OK"} chunks)`);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Upload failed";
      setUploadStatus(`Error: ${message}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const currentSessionId = sessionId || `session_${Date.now()}`;
    const userPrompt = input;
    const userMsgId = `user_${Date.now()}`;
    const botMsgId = `bot_${Date.now() + 1}`;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, role: "user", content: userPrompt },
      { id: botMsgId, role: "assistant", content: "" },
    ]);
    setInput("");
    setIsLoading(true);

    try {
      await streamAgentQuery(
        { query: userPrompt, session_id: currentSessionId },
        {
          onMetadata: (meta) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === botMsgId
                  ? {
                      ...m,
                      intent: meta.intent,
                      executedAction: meta.executed_action,
                      sourcesCount: meta.sources.length,
                    }
                  : m
              )
            );
          },
          onToken: (delta) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === botMsgId ? { ...m, content: m.content + delta } : m
              )
            );
          },
          onError: (errMsg) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === botMsgId ? { ...m, content: `Error: ${errMsg}` } : m
              )
            );
          },
          onDone: () => {
            setIsLoading(false);
          },
        }
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to reach agent engine";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === botMsgId ? { ...m, content: `Error: ${message}` } : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const getIntentBadge = (intent?: string) => {
    switch (intent) {
      case "KNOWLEDGE_BASE_QUERY":
        return (
          <span className="flex items-center gap-1 text-xs bg-blue-900/60 text-blue-300 px-2.5 py-1 rounded-md border border-blue-700/50">
            <Database className="w-3 h-3" /> Knowledge Base RAG
          </span>
        );
      case "WEB_SEARCH":
        return (
          <span className="flex items-center gap-1 text-xs bg-emerald-900/60 text-emerald-300 px-2.5 py-1 rounded-md border border-emerald-700/50">
            <Search className="w-3 h-3" /> Web Search
          </span>
        );
      case "CALCULATOR":
        return (
          <span className="flex items-center gap-1 text-xs bg-purple-900/60 text-purple-300 px-2.5 py-1 rounded-md border border-purple-700/50">
            <Calculator className="w-3 h-3" /> Math Calculator
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded-md border border-slate-700">
            <Sparkles className="w-3 h-3" /> Direct Chat
          </span>
        );
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 font-sans">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900/80 px-6 py-4 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-600/20 text-indigo-400 rounded-lg border border-indigo-500/30">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-semibold text-lg">Enterprise RAG & Multi-Agent Platform</h1>
            <p className="text-xs text-slate-400">Session ID: {sessionId || "Initializing..."}</p>
          </div>
        </div>

        {/* Document Ingestion Control */}
        <div className="flex items-center gap-3">
          {uploadStatus && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-950/60 border border-emerald-800/60 px-3 py-1.5 rounded-lg">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {uploadStatus}
            </span>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md"
            onChange={handleFileUpload}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center gap-2 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-3.5 py-2 rounded-lg transition-colors disabled:opacity-50"
          >
            {isUploading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Upload className="w-3.5 h-3.5" />
            )}
            {isUploading ? "Ingesting..." : "Upload Doc (PDF/TXT/MD)"}
          </button>
        </div>
      </header>

      {/* Chat Messages */}
      <main className="flex-1 overflow-y-auto p-6 space-y-4 max-w-4xl w-full mx-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-3">
            <Bot className="w-12 h-12 text-slate-600" />
            <p className="text-sm">Upload a document or ask a question to stream live multi-agent responses.</p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="w-8 h-8 rounded-full bg-indigo-600/20 text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-500/30">
                  <Bot className="w-4 h-4" />
                </div>
              )}
              <div
                className={`max-w-2xl rounded-xl px-4 py-3 text-sm leading-relaxed space-y-2 ${
                  msg.role === "user"
                    ? "bg-indigo-600 text-white rounded-br-none"
                    : "bg-slate-900 text-slate-200 border border-slate-800 rounded-bl-none shadow-sm"
                }`}
              >
                {msg.intent && (
                  <div className="flex items-center gap-2 mb-1">
                    {getIntentBadge(msg.intent)}
                    {typeof msg.sourcesCount === "number" && msg.sourcesCount > 0 && (
                      <span className="text-[11px] text-slate-400">
                        • {msg.sourcesCount} sources retrieved
                      </span>
                    )}
                  </div>
                )}
                <div className="whitespace-pre-wrap">
                  {msg.content || (isLoading ? "Thinking..." : "")}
                </div>
                {msg.executedAction && (
                  <p className="text-[10px] text-slate-400 border-t border-slate-800 pt-1 mt-2">
                    Action: {msg.executedAction}
                  </p>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-full bg-slate-800 text-slate-300 flex items-center justify-center shrink-0 border border-slate-700">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Input Form */}
      <footer className="p-4 border-t border-slate-800 bg-slate-900/50 backdrop-blur">
        <div className="max-w-4xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about uploaded docs, run math (e.g. '45 * 12'), or 'search web latest AI news'..."
            className="flex-1 bg-slate-950 text-slate-100 border border-slate-800 rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-500 transition-colors"
          />
          <button
            onClick={handleSend}
            disabled={isLoading}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-5 py-3 rounded-xl flex items-center justify-center transition-colors disabled:opacity-50"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </footer>
    </div>
  );
}