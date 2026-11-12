export interface AgentMessagePayload {
  query: string;
  session_id: string;
}

export interface StreamCallbacks {
  onMetadata: (meta: { intent: string; executed_action: string; sources: Record<string, unknown>[] }) => void;
  onToken: (delta: string) => void;
  onDone: () => void;
  onError: (err: string) => void;
}

const API_BASE_URL = "http://127.0.0.1:8000";

export async function streamAgentQuery(
  payload: AgentMessagePayload,
  callbacks: StreamCallbacks
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok || !response.body) {
    throw new Error(`API Error: ${response.statusText || "Stream unavailable"}`);
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
            sources: parsed.sources || [],
          });
        } else if (parsed.event === "text") {
          callbacks.onToken(parsed.delta || "");
        } else if (parsed.event === "error") {
          callbacks.onError(parsed.message || "Agent execution error");
        } else if (parsed.event === "done") {
          callbacks.onDone();
        }
      } catch {
        // Ignore malformed partial frames
      }
    }
  }
}

export async function uploadDocument(file: File): Promise<{ status: string; filename: string; chunks_ingested?: number }> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/v1/ingest/document`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed: ${response.statusText}`);
  }

  return response.json();
}