const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export async function fetchWithAuth(endpoint: string, token: string) {
  if (!token) return null;
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function loginUser(email: string, password: string): Promise<string | null> {
  try {
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", password);
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      body: params,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    if (!response.ok) return null;
    const data = await response.json();
    return data.access_token;
  } catch {
    return null;
  }
}

export async function postWithAuth(endpoint: string, data: unknown, token: string) {
  if (!token) return null;
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}
