import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { getToken, decodeToken, isTokenExpired, clearToken } from "../auth";

export default function RequireAuth({ children }: { children: ReactNode }) {
  const token = getToken();
  const payload = token ? decodeToken(token) : null;

  if (!token || !payload || isTokenExpired(payload)) {
    clearToken();
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
