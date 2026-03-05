const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api";

export async function apiFetch(
    endpoint: string,
    options: RequestInit = {}
): Promise<Response> {
    // TODO: Migrate from localStorage JWT to HttpOnly cookies for better security
    const token =
        typeof window !== "undefined" ? localStorage.getItem("token") : null;

    const headers = new Headers(options.headers);
    headers.set("Content-Type", "application/json");

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
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
    const params = new URLSearchParams({ limit: limit.toString() });
    const res = await apiFetch(`/alerts?${params.toString()}`);
    return res.json();
}

export async function getIncidents(status?: string) {
    const params = new URLSearchParams();
    if (status) {
        params.set("status", status);
    }
    const queryString = params.toString() ? `?${params.toString()}` : "";
    const res = await apiFetch(`/incidents${queryString}`);
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
