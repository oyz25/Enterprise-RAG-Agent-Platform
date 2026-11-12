"use client";

import { useState, useEffect } from "react";
import { sendAgentQuery } from "@/lib/api";
import { Send, Bot, User, Sparkles, Cpu, Search, Calculator, Database } from "lucide-react";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  executedAction?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");

  useEffect(() => {
    setSessionId(`session_${Date.now()}`);
  }, []);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const currentSessionId = sessionId || `session_${Date.now()}`;
    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await sendAgentQuery({
        query: userMsg.content,
        session_id: currentSessionId,
      });

      let responseContent = "";
      if (typeof res.result === "string") {
        responseContent = res.result;
      } else if (res.result.response) {
        responseContent = res.result.response;
      } else if (res.result.results) {
        responseContent = JSON.stringify(res.result.results, null, 2);
      } else {
        responseContent = JSON.stringify(res.result, null, 2);
      }

      const botMsg: ChatMessage = {
        id: `bot_${Date.now()}`,
        role: "assistant",
        content: responseContent,
        intent: res.intent,
        executedAction: res.executed_action,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `error_${Date.now()}`,
        role: "assistant",
        content: `Error: ${err.message || "Failed to reach agent engine"}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const getIntentBadge = (intent?: string) => {
    switch (intent) {
      case "KNOWLEDGE_BASE_QUERY":
        return <span className="flex items-center gap-1 text-xs bg-blue-900/60 text-blue-300 px-2.5 py-1 rounded-md border border-blue-700/50"><Database className="w-3 h-3" /> Knowledge Base RAG</span>;
      case "WEB_SEARCH":
        return <span className="flex items-center gap-1 text-xs bg-emerald-900/60 text-emerald-300 px-2.5 py-1 rounded-md border border-emerald-700/50"><Search className="w-3 h-3" /> Web Search</span>;
      case "CALCULATOR":
        return <span className="flex items-center gap-1 text-xs bg-purple-900/60 text-purple-300 px-2.5 py-1 rounded-md border border-purple-700/50"><Calculator className="w-3 h-3" /> Math Calculator</span>;
      default:
        return <span className="flex items-center gap-1 text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded-md border border-slate-700"><Sparkles className="w-3 h-3" /> Direct Chat</span>;
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
      </header>

      {/* Chat Messages */}
      <main className="flex-1 overflow-y-auto p-6 space-y-4 max-w-4xl w-full mx-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-3">
            <Bot className="w-12 h-12 text-slate-600" />
            <p className="text-sm">Ask a question, request a web search, or evaluate a math equation.</p>
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
                  </div>
                )}
                <div className="whitespace-pre-wrap">{msg.content}</div>
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
      </main>

      {/* Input Form */}
      <footer className="p-4 border-t border-slate-800 bg-slate-900/50 backdrop-blur">
        <div className="max-w-4xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type your prompt (e.g. 'FastAPI experience', 'Calculate 45 * 12', 'search web latest AI news')..."
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