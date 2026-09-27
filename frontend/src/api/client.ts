// Thin fetch wrapper for the FastAPI backend (login, chat).
import { getToken } from "../auth";

// /api is proxied + rewritten to the backend in dev (see vite.config.ts) — the
// frontend's own page routes are also named /login and /chat, so this prefix
// is required to avoid colliding with them, not just cosmetic.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const res = await fetch(`${API_BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.detail ?? "Login failed");
  }

  return res.json();
}

export interface ChatResponse {
  answer: string;
  sources: string[];
}

export async function askQuestion(question: string): Promise<ChatResponse> {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.detail ?? "Request failed");
  }

  return res.json();
}
