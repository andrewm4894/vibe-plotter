export type DatasetResponse = {
  session_id: string;
  dataset_id?: string;
  columns: string[];
  dtypes: Record<string, string>;
  rows: Record<string, unknown>[];
  row_count: number;
  sample_count: number;
};

export type ChatResponse = {
  session_id: string;
  assistant_message: string;
  plot_json?: { data: unknown[]; layout?: Record<string, unknown>; frames?: unknown[] };
  title?: string;
  summary?: string;
  code?: string;
};

export class ApiError extends Error {
  code: string;

  constructor(code: string, message: string) {
    super(message);
    this.code = code;
  }
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>;
  }

  try {
    const payload = await response.json();
    if (payload?.error?.code) {
      throw new ApiError(payload.error.code, payload.error.message);
    }
  } catch (error) {
    if (error instanceof ApiError) throw error;
  }

  throw new ApiError("request_failed", "Request failed. Please try again.");
}

export async function loadUciDataset(
  datasetId: string,
  sessionId: string
): Promise<DatasetResponse> {
  const response = await fetch(`${API_BASE}/api/datasets/uci`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dataset_id: datasetId, session_id: sessionId }),
  });

  return handleResponse<DatasetResponse>(response);
}

export async function loadUrlDataset(
  url: string,
  sessionId: string
): Promise<DatasetResponse> {
  const response = await fetch(`${API_BASE}/api/datasets/url`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, session_id: sessionId }),
  });

  return handleResponse<DatasetResponse>(response);
}

export async function sendChatMessage(
  message: string,
  sessionId: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  return handleResponse<ChatResponse>(response);
}
