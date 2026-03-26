// Use the environment variable that matches your .env.local
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

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
  } catch (error) {
    console.error("fetchWithAuth error:", error);
    return null;
  }
}

export async function loginUser(email: string, password: string): Promise<string | null> {
  try {
    // Backend expects form‑encoded data with "username" and "password"
    const params = new URLSearchParams();
    params.append("username", email);
    params.append("password", password);

    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      body: params,
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    // Log the response for debugging (remove in production)
    console.log("Login response status:", response.status);
    const responseText = await response.text();
    console.log("Login response body:", responseText);

    if (!response.ok) {
      console.error("Login failed with status", response.status);
      return null;
    }

    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      console.error("Failed to parse JSON:", e);
      return null;
    }

    // Adjust if your backend returns a different field name
    const token = data.access_token || data.token;
    if (!token) {
      console.error("No token in response", data);
      return null;
    }
    return token;
  } catch (error) {
    console.error("Login error:", error);
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
  } catch (error) {
    console.error("postWithAuth error:", error);
    return null;
  }
}
