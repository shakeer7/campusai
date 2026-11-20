const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("campusai_access_token");
}

export function setAuthSession(token: string, role: string, user: any) {
  if (typeof window === "undefined") return;
  localStorage.setItem("campusai_access_token", token);
  localStorage.setItem("campusai_user_role", role);
  localStorage.setItem("campusai_user_data", JSON.stringify(user));
}

export function clearAuthSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("campusai_access_token");
  localStorage.removeItem("campusai_user_role");
  localStorage.removeItem("campusai_user_data");
}

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}) {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const url = `${API_BASE_URL}${endpoint}`;
  const res = await fetch(url, { ...options, headers });

  if (res.status === 401 && typeof window !== "undefined") {
    // If unauthorized, redirect to login
    clearAuthSession();
    window.location.href = "/login";
    throw new Error("Session expired. Please log in again.");
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${res.status}`);
  }

  return res.json();
}
