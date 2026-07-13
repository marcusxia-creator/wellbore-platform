/**
 * Client-side auth helpers.
 *
 * Tokens are kept in cookies (not localStorage) so `proxy.ts` can do an
 * optimistic redirect check on the edge before a page renders.
 *
 * Mock mode (NEXT_PUBLIC_USE_MOCK=true) accepts any non-empty credentials
 * so the dashboard remains usable without a running Django backend —
 * mirroring the mock/real split in lib/api.ts.
 */
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
const IS_MOCK = process.env.NEXT_PUBLIC_USE_MOCK === "true";

export const ACCESS_COOKIE = "ws_access";
export const REFRESH_COOKIE = "ws_refresh";
export const USER_COOKIE = "ws_user";

export interface AuthUser {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

// ─── Cookie helpers ──────────────────────────────────────────────────────────

export function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(name + "="));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : null;
}

function setCookie(name: string, value: string, maxAgeSeconds: number) {
  if (typeof document === "undefined") return;
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${name}=${encodeURIComponent(
    value
  )}; Path=/; Max-Age=${maxAgeSeconds}; SameSite=Lax${secure}`;
}

function deleteCookie(name: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; Path=/; Max-Age=0; SameSite=Lax`;
}

// ─── Auth API ────────────────────────────────────────────────────────────────

const ACCESS_MAX_AGE = 60 * 60; // 1 h — matches SIMPLE_JWT access lifetime
const REFRESH_MAX_AGE = 7 * 24 * 60 * 60; // 7 d — matches refresh lifetime

export async function login(username: string, password: string): Promise<void> {
  if (IS_MOCK) {
    if (!username.trim() || !password.trim()) {
      throw new Error("Please enter a username and password.");
    }
    setCookie(ACCESS_COOKIE, "mock-access-token", ACCESS_MAX_AGE);
    setCookie(REFRESH_COOKIE, "mock-refresh-token", REFRESH_MAX_AGE);
    setCookie(USER_COOKIE, username.trim(), REFRESH_MAX_AGE);
    return;
  }

  try {
    const { data } = await axios.post<{ access: string; refresh: string }>(
      `${API_URL}/auth/login/`,
      { username, password },
      { headers: { "Content-Type": "application/json" } }
    );
    setCookie(ACCESS_COOKIE, data.access, ACCESS_MAX_AGE);
    setCookie(REFRESH_COOKIE, data.refresh, REFRESH_MAX_AGE);
    setCookie(USER_COOKIE, username.trim(), REFRESH_MAX_AGE);
  } catch (err) {
    if (axios.isAxiosError(err)) {
      if (err.response?.status === 401) {
        throw new Error("Invalid username or password.");
      }
      if (!err.response) {
        throw new Error("Cannot reach the server. Is the backend running?");
      }
    }
    throw new Error("Sign-in failed. Please try again.");
  }
}

export function logout(): void {
  deleteCookie(ACCESS_COOKIE);
  deleteCookie(REFRESH_COOKIE);
  deleteCookie(USER_COOKIE);
}

export function getAccessToken(): string | null {
  return getCookie(ACCESS_COOKIE);
}

export function getStoredUsername(): string | null {
  return getCookie(USER_COOKIE);
}

export function isAuthenticated(): boolean {
  return getAccessToken() !== null;
}

/**
 * Exchange the refresh token for a new access token.
 * Returns the new access token, or null if refresh failed (session expired).
 */
export async function refreshAccessToken(): Promise<string | null> {
  if (IS_MOCK) return getAccessToken();

  const refresh = getCookie(REFRESH_COOKIE);
  if (!refresh) return null;

  try {
    const { data } = await axios.post<{ access: string }>(
      `${API_URL}/auth/refresh/`,
      { refresh },
      { headers: { "Content-Type": "application/json" } }
    );
    setCookie(ACCESS_COOKIE, data.access, ACCESS_MAX_AGE);
    return data.access;
  } catch {
    logout();
    return null;
  }
}

export async function fetchCurrentUser(): Promise<AuthUser | null> {
  if (IS_MOCK) {
    const username = getStoredUsername();
    return username
      ? { id: 0, username, email: "", first_name: "", last_name: "" }
      : null;
  }

  const token = getAccessToken();
  if (!token) return null;

  try {
    const { data } = await axios.get<AuthUser>(`${API_URL}/auth/me/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return data;
  } catch {
    return null;
  }
}
