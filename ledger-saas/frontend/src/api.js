// Configure backend URL via .env (Vite): VITE_API_URL=http://127.0.0.1:8000
export const API_BASE = import.meta?.env?.VITE_API_URL || "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem("token");
}
export function setToken(t) {
  localStorage.setItem("token", t);
}
export async function apiFetch(path, opts = {}) {
  const headers = opts.headers || {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || `HTTP ${res.status}`);
  }
  
  // Handle empty responses
  const text = await res.text();
  if (!text || text.trim() === "") {
    return {};
  }
  
  try {
    return JSON.parse(text);
  } catch (e) {
    console.error("JSON parse error:", e, "Response text:", text);
    throw new Error(`Invalid JSON response: ${text.slice(0, 100)}`);
  }
}

