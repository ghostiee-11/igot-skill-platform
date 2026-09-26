const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("karmayogi_token") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function buildUrl(endpoint: string): string {
  return `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
}

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = "An unexpected server error occurred";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    throw new ApiError(typeof errorDetail === "string" ? errorDetail : JSON.stringify(errorDetail), response.status);
  }
  return response.json();
}

export async function fetchApi<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(buildUrl(endpoint), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
      ...authHeaders(),
    },
  });
  return parseResponse<T>(response);
}

export async function fetchBlob(endpoint: string, options: RequestInit = {}): Promise<Blob> {
  const response = await fetch(buildUrl(endpoint), {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
      ...authHeaders(),
    },
  });
  if (!response.ok) await parseResponse(response);
  return response.blob();
}

export async function uploadApi<T = any>(endpoint: string, formData: FormData): Promise<T> {
  const response = await fetch(buildUrl(endpoint), { method: "POST", body: formData, headers: authHeaders() });
  return parseResponse<T>(response);
}
