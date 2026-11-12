export interface AgentMessagePayload {
  query: string;
  session_id: string;
}

export interface AgentResponse {
  status: string;
  intent: string;
  confidence_score: number;
  reasoning: string;
  executed_action: string;
  result: Record<string, any>;
}

const API_BASE_URL = "http://127.0.0.1:8000";

export async function sendAgentQuery(payload: AgentMessagePayload): Promise<AgentResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agent/process`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }

  return response.json();
}