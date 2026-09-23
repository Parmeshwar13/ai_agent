import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api, clearSession, hasSession, setSession } from "../services/api";
import type { Organization, SessionResponse, User } from "../types";

type RegisterInput = {
  email: string;
  password: string;
  first_name: string;
  last_name?: string;
  organization_name?: string;
};

type AuthContextValue = {
  user: User | null;
  organizations: Organization[];
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (input: RegisterInput) => Promise<void>;
  logout: () => Promise<void>;
  refreshOrganizations: () => Promise<Organization[]>;
  setUser: (user: User) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function applySession(payload: SessionResponse) {
  setSession(payload.access, payload.refresh);
  return payload;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [ready, setReady] = useState(false);

  const refreshOrganizations = useCallback(async () => {
    const me = await api<{ user: User; organizations: Organization[] }>("/auth/me/");
    setUser(me.user);
    setOrganizations(me.organizations);
    return me.organizations;
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      if (!hasSession()) {
        setReady(true);
        return;
      }
      try {
        const me = await api<{ user: User; organizations: Organization[] }>("/auth/me/");
        if (!cancelled) {
          setUser(me.user);
          setOrganizations(me.organizations);
        }
      } catch {
        clearSession();
        if (!cancelled) {
          setUser(null);
          setOrganizations([]);
        }
      } finally {
        if (!cancelled) setReady(true);
      }
    }
    void boot();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    function onUnauthorized() {
      clearSession();
      setUser(null);
      setOrganizations([]);
    }
    window.addEventListener("orbit:unauthorized", onUnauthorized);
    return () => window.removeEventListener("orbit:unauthorized", onUnauthorized);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const payload = await api<SessionResponse>("/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    applySession(payload);
    setUser(payload.user);
    setOrganizations(payload.organizations);
  }, []);

  const register = useCallback(async (input: RegisterInput) => {
    const payload = await api<SessionResponse>("/auth/register/", {
      method: "POST",
      body: JSON.stringify(input),
    });
    applySession(payload);
    setUser(payload.user);
    setOrganizations(payload.organizations);
  }, []);

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem("orbit.refresh");
    try {
      if (refresh) {
        await api("/auth/logout/", { method: "POST", body: JSON.stringify({ refresh }) });
      }
    } catch {
      // Local sign-out still proceeds if the refresh token is already dead.
    }
    clearSession();
    setUser(null);
    setOrganizations([]);
  }, []);

  const value = useMemo(
    () => ({
      user,
      organizations,
      ready,
      login,
      register,
      logout,
      refreshOrganizations,
      setUser,
    }),
    [user, organizations, ready, login, register, logout, refreshOrganizations],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
