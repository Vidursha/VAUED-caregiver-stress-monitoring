import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { AppUser, AuthSession, Role, StoredUser } from "./types";
import { clearSession, hydrateRememberedSession, readSession, readUsers, writeSession, writeUsers } from "./storage";
import { hasPermission } from "./rbac";

type AuthState =
  | { status: "loading"; user: null }
  | { status: "unauthenticated"; user: null }
  | { status: "authenticated"; user: AppUser };

type LoginInput = { email: string; password: string; remember: boolean };

type AuthContextValue = {
  state: AuthState;
  login: (input: LoginInput) => Promise<void>;
  logout: () => void;
  users: StoredUser[];
  upsertUser: (user: StoredUser) => void;
  setUserActive: (id: string, active: boolean) => void;
  can: (perm: Parameters<typeof hasPermission>[1]) => boolean;
  hasRole: (role: Role) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function normalizeEmail(v: string) {
  return (v || "").trim().toLowerCase();
}

function safeUser(u: StoredUser): AppUser {
  // Strip password for session state.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { password, ...rest } = u;
  return rest;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({ status: "loading", user: null });
  const [users, setUsers] = useState<StoredUser[]>(() => readUsers());

  useEffect(() => {
    // Keep users in sync with localStorage seed.
    setUsers(readUsers());
  }, []);

  useEffect(() => {
    const session = readSession() ?? hydrateRememberedSession();
    if (session?.user) {
      setState({ status: "authenticated", user: session.user });
    } else {
      setState({ status: "unauthenticated", user: null });
    }
  }, []);

  async function login(input: LoginInput) {
    const email = normalizeEmail(input.email);
    const password = input.password;

    // Simulate network latency for UX.
    await new Promise((r) => setTimeout(r, 520));

    const match = users.find((u) => normalizeEmail(u.email) === email);
    if (!match || match.password !== password) {
      throw new Error("Invalid email/username or password.");
    }
    if (!match.active) {
      throw new Error("Your account is deactivated. Please contact an admin.");
    }

    const session: AuthSession = { user: safeUser(match), createdAt: Date.now() };
    writeSession(session, input.remember);
    setState({ status: "authenticated", user: session.user });
  }

  function logout() {
    clearSession();
    setState({ status: "unauthenticated", user: null });
  }

  function upsertUser(user: StoredUser) {
    setUsers((prev) => {
      const next = [...prev];
      const idx = next.findIndex((u) => u.id === user.id);
      if (idx >= 0) next[idx] = user;
      else next.unshift(user);
      writeUsers(next);
      return next;
    });
  }

  function setUserActive(id: string, active: boolean) {
    setUsers((prev) => {
      const next = prev.map((u) => (u.id === id ? { ...u, active } : u));
      writeUsers(next);
      return next;
    });
  }

  const value = useMemo<AuthContextValue>(() => {
    return {
      state,
      login,
      logout,
      users,
      upsertUser,
      setUserActive,
      can: (perm) => (state.status === "authenticated" ? hasPermission(state.user.role, perm) : false),
      hasRole: (role) => (state.status === "authenticated" ? state.user.role === role : false),
    };
  }, [state, users]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}

