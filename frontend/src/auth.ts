// Token storage plus reading the role claim back out of the JWT for display.
// Never trust this client-side decode for access control — the backend is the
// only real enforcement point; this is purely "what should the UI show."

const TOKEN_KEY = "finsolve_token";

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

interface TokenPayload {
  sub: string;
  role: string;
  exp: number;
}

export function decodeToken(token: string): TokenPayload | null {
  try {
    const payload = token.split(".")[1];
    const json = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    return JSON.parse(json) as TokenPayload;
  } catch {
    return null;
  }
}

export function isTokenExpired(payload: TokenPayload): boolean {
  return payload.exp * 1000 < Date.now();
}
