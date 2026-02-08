import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, setAuthToken } from "./api";

type Me = { id: number; email: string; full_name: string; role: string };

type AuthState = {
  me: Me | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthState | null>(null);

const TOKEN_KEY = "token";

function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
  setAuthToken(token);
}
function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  setAuthToken(null);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadMe() {
    try {
      const r = await api.get("/auth/me");
      setMe(r.data);
    } catch {
      clearToken();
      setMe(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const t = getToken();
    if (t) {
      setAuthToken(t);
      loadMe();
    } else {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function login(email: string, password: string) {
    const r = await api.post("/auth/login", { email, password });
    saveToken(r.data.access_token);
    await loadMe();
  }

  function logout() {
    clearToken();
    setMe(null);
  }

  const value = useMemo(() => ({ me, loading, login, logout }), [me, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
