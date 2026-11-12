export interface CitationItem {
  source_number: number;
  type: "knowledge_base" | "web_search";
  chunk_id?: string;
  relevance_score?: number;
  title?: string;
  url?: string;
  snippet: string;
}

export interface AgentMessagePayload {
  query: string;
  session_id: string;
}

export interface StreamCallbacks {
  onMetadata: (meta: {
    intent: string;
    executed_action: string;
    synthesis_mode?: string;
    citations: CitationItem[];
  }) => void;
  onToken: (delta: string) => void;
  onDone: () => void;
  onError: (err: string) => void;
}

export interface SessionSummary {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface PersistedMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  created_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

function buildAuthHeaders(extra: Record<string, string> = {}): Record<string, string> {
  const headers: Record<string, string> = { ...extra };
  if (API_KEY) {
    headers["X-API-Key"] = API_KEY;
  }
  return headers;
}

export async function streamAgentQuery(
  payload: AgentMessagePayload,
  callbacks: StreamCallbacks
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/stream`, {
    method: "POST",
    headers: buildAuthHeaders({
      "Content-Type": "application/json",
    }),
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API Error: ${response.statusText || "Stream unavailable"}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() || "";

    for (const frame of frames) {
      const line = frame.trim();
      if (!line.startsWith("data: ")) continue;

      const jsonStr = line.slice(6);
      try {
        const parsed = JSON.parse(jsonStr);
        if (parsed.event === "metadata") {
          callbacks.onMetadata({
            intent: parsed.intent,
            executed_action: parsed.executed_action,
            synthesis_mode: parsed.synthesis_mode,
            citations: parsed.citations || parsed.sources || [],
          });
        } else if (parsed.event === "text") {
          callbacks.onToken(parsed.delta || "");
        } else if (parsed.event === "error") {
          callbacks.onError(parsed.message || "Agent execution error");
        } else if (parsed.event === "done") {
          callbacks.onDone();
        }
      } catch {
        // Ignore partial frames
      }
    }
  }
}

export async function uploadDocument(
  file: File
): Promise<{ status: string; filename: string; chunks_ingested?: number }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/v1/ingest/document`, {
    method: "POST",
    headers: buildAuthHeaders(),
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
  }

  return response.json();
}

export async function fetchSessions(): Promise<SessionSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/sessions`, {
    headers: buildAuthHeaders(),
  });
  if (!response.ok) return [];
  const data = await response.json();
  return data.sessions || [];
}

export async function fetchSessionMessages(sessionId: string): Promise<PersistedMessage[]> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/sessions/${encodeURIComponent(sessionId)}/messages`,
    {
      headers: buildAuthHeaders(),
    }
  );
  if (!response.ok) return [];
  const data = await response.json();
  return data.messages || [];
}

export async function deleteSession(sessionId: string): Promise<boolean> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/sessions/${encodeURIComponent(sessionId)}`,
    {
      method: "DELETE",
      headers: buildAuthHeaders(),
    }
  );
  return response.ok;
}