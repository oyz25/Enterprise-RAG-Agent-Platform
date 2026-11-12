"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  streamAgentQuery,
  uploadDocument,
  fetchSessions,
  fetchSessionMessages,
  deleteSession,
  CitationItem,
  SessionSummary,
} from "@/lib/api";
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
  BookOpen,
  Plus,
  MessageSquare,
  Trash2,
} from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  executedAction?: string;
  synthesisMode?: string;
  citations?: CitationItem[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const loadSidebarSessions = useCallback(async () => {
    const list = await fetchSessions();
    setSessions(list);
  }, []);

  useEffect(() => {
    setSessionId(`session_${Date.now()}`);
    loadSidebarSessions();
  }, [loadSidebarSessions]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleNewChat = () => {
    setSessionId(`session_${Date.now()}`);
    setMessages([]);
  };

  const handleSelectSession = async (targetSessionId: string) => {
    if (targetSessionId === sessionId) return;
    setSessionId(targetSessionId);
    const history = await fetchSessionMessages(targetSessionId);
    setMessages(
      history.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        intent: m.intent,
      }))
    );
  };

  const handleDeleteSession = async (e: React.MouseEvent, targetSessionId: string) => {
    e.stopPropagation();
    const ok = await deleteSession(targetSessionId);
    if (ok) {
      if (targetSessionId === sessionId) {
        handleNewChat();
      }
      await loadSidebarSessions();
    }
  };

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
    if (!sessionId) setSessionId(currentSessionId);

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
                      synthesisMode: meta.synthesis_mode,
                      citations: meta.citations,
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
            loadSidebarSessions();
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
      loadSidebarSessions();
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
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Left Sidebar: PostgreSQL Session History */}
      <aside className="w-72 border-r border-slate-800 bg-slate-900/60 flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-800">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium py-2.5 px-3 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Conversation
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1">
          <p className="px-2 py-1 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
            Saved Sessions ({sessions.length})
          </p>
          {sessions.length === 0 ? (
            <p className="px-2 py-4 text-xs text-slate-500">No saved conversations yet.</p>
          ) : (
            sessions.map((s) => {
              const isActive = s.id === sessionId;
              return (
                <div
                  key={s.id}
                  onClick={() => handleSelectSession(s.id)}
                  className={`group flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg text-xs cursor-pointer transition-colors ${
                    isActive
                      ? "bg-indigo-600/20 text-indigo-200 border border-indigo-500/40"
                      : "text-slate-400 hover:bg-slate-800/70 hover:text-slate-200"
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <MessageSquare className="w-3.5 h-3.5 shrink-0 text-slate-500" />
                    <div className="truncate">
                      <p className="truncate font-medium">{s.title}</p>
                      <p className="text-[10px] text-slate-500">{s.message_count} msgs</p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => handleDeleteSession(e, s.id)}
                    title="Delete session"
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 transition-opacity"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </aside>

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col min-w-0">
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

        <main className="flex-1 overflow-y-auto p-6 space-y-4 max-w-4xl w-full mx-auto">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-3">
              <Bot className="w-12 h-12 text-slate-600" />
              <p className="text-sm">Start a new prompt or select a saved session from the left sidebar.</p>
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
                  className={`max-w-2xl rounded-xl px-4 py-3 text-sm leading-relaxed space-y-2.5 ${
                    msg.role === "user"
                      ? "bg-indigo-600 text-white rounded-br-none"
                      : "bg-slate-900 text-slate-200 border border-slate-800 rounded-bl-none shadow-sm"
                  }`}
                >
                  {msg.intent && (
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      {getIntentBadge(msg.intent)}
                      {msg.synthesisMode && (
                        <span className="text-[11px] bg-slate-800/90 text-slate-400 px-2 py-0.5 rounded border border-slate-700/70">
                          {msg.synthesisMode}
                        </span>
                      )}
                    </div>
                  )}

                  <div className="whitespace-pre-wrap">
                    {msg.content || (isLoading ? "Synthesizing grounded answer..." : "")}
                  </div>

                  {msg.citations && msg.citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
                      <div className="flex items-center gap-1.5 text-[11px] font-medium text-slate-400">
                        <BookOpen className="w-3 h-3 text-indigo-400" />
                        <span>Grounded Citations ({msg.citations.length})</span>
                      </div>
                      <div className="grid gap-1.5">
                        {msg.citations.map((cite) => (
                          <div
                            key={cite.source_number}
                            className="text-xs bg-slate-950/80 border border-slate-800 rounded-lg p-2.5 text-slate-300"
                          >
                            <div className="flex items-center justify-between text-[11px] text-indigo-400 font-medium mb-1">
                              <span>[Source {cite.source_number}]</span>
                              {typeof cite.relevance_score === "number" && (
                                <span className="text-slate-500">Score: {cite.relevance_score}</span>
                              )}
                            </div>
                            <p className="text-slate-400 line-clamp-2">{cite.snippet}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {msg.executedAction && (
                    <p className="text-[10px] text-slate-500 pt-1">
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
    </div>
  );
}