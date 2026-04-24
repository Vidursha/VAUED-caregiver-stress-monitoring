import type { AuthSession, StoredUser } from "./types";
import { DEFAULT_MOCK_USERS } from "./mockUsers";

const USERS_KEY = "care_sync_users_v1";
const SESSION_KEY = "care_sync_session_v1";

function safeParse<T>(raw: string | null): T | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

export function ensureMockUsersSeeded() {
  const existing = safeParse<StoredUser[]>(localStorage.getItem(USERS_KEY));
  if (existing && Array.isArray(existing) && existing.length) return;
  localStorage.setItem(USERS_KEY, JSON.stringify(DEFAULT_MOCK_USERS));
}

export function readUsers(): StoredUser[] {
  ensureMockUsersSeeded();
  const users = safeParse<StoredUser[]>(localStorage.getItem(USERS_KEY));
  return Array.isArray(users) ? users : [...DEFAULT_MOCK_USERS];
}

export function writeUsers(users: StoredUser[]) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

export function readSession(): AuthSession | null {
  const s = safeParse<AuthSession>(sessionStorage.getItem(SESSION_KEY));
  return s?.user ? s : null;
}

export function writeSession(session: AuthSession, remember: boolean) {
  // Session is stored in sessionStorage by default; if "remember me" we also persist in localStorage.
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
  if (remember) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } else {
    localStorage.removeItem(SESSION_KEY);
  }
}

export function hydrateRememberedSession(): AuthSession | null {
  const local = safeParse<AuthSession>(localStorage.getItem(SESSION_KEY));
  if (local?.user) {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(local));
    return local;
  }
  return null;
}

export function clearSession() {
  sessionStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(SESSION_KEY);
}

