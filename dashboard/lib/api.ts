const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api";

export async function apiFetch(
    endpoint: string,
    options: RequestInit = {}
): Promise<Response> {
    const token =
        typeof window !== "undefined" ? localStorage.getItem("token") : null;

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...(options.headers as Record<string, string>),
    };

    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    return res;
}

export async function login(
    username: string,
    password: string
): Promise<{ token: string; role: string } | { error: string }> {
    const res = await apiFetch("/login", {
        method: "POST",
        body: JSON.stringify({ username, password }),
    });
    return res.json();
}

export async function getAlerts(limit = 50) {
    const res = await apiFetch(`/alerts?limit=${limit}`);
    return res.json();
}

export async function getIncidents(status?: string) {
    const query = status ? `?status=${status}` : "";
    const res = await apiFetch(`/incidents${query}`);
    return res.json();
}

export async function getStats() {
    const res = await apiFetch("/stats");
    return res.json();
}

export async function getUsers() {
    const res = await apiFetch("/users");
    return res.json();
}
