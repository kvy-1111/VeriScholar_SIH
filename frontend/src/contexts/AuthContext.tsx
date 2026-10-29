import { createContext, useContext, useMemo, useState } from "react";
import { api, setToken } from "../api";

type User = { id: number; email: string; role: string } | null;

const AuthCtx = createContext<{
  user: User;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}>({ user: null, login: async () => undefined, logout: () => undefined });

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User>(null);

  const login = async (email: string, password: string) => {
    const tokenResp = await api.post("/auth/login", { email, password });
    setToken(tokenResp.data.access_token);
    const meResp = await api.get("/auth/me");
    setUser(meResp.data);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const value = useMemo(() => ({ user, login, logout }), [user]);
  return <AuthCtx.Provider value={value}>{children}</AuthCtx.Provider>;
}

export const useAuth = () => useContext(AuthCtx);
