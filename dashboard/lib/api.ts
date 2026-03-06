const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api";

function handleAuthError() {
    if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        localStorage.removeItem("role");
        window.location.href = "/login";
    }
}

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

    try {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
        });

        // Handle auth errors globally - treat any 401 as auth failure
        if (res.status === 401) {
            res
                .clone()
                .json()
                .catch(() => ({}))
                .then((data) => {
                    console.warn("[api] 401 Unauthorized:", data?.error || "Unknown auth error");
                });
            handleAuthError();
        }

        return res;
    } catch (err) {
        console.error("[api] network error", err);
        // Normalize to a rejected Response-like object so callers can handle gracefully
        return new Response(
            JSON.stringify({ error: "Network error. Is the backend running at " + API_BASE + "?" }),
            { status: 503, headers: { "Content-Type": "application/json" } }
        );
    }
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

export async function getMe() {
    const res = await apiFetch("/me");
    if (!res.ok) return null;
    return res.json();
}

export async function bulkDismissAlerts() {
    const res = await apiFetch("/alerts/bulk-dismiss", { method: "POST" });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || "Failed to bulk dismiss alerts");
    }
    return res.json();
}

// ==================== ALERT ACTIONS ====================

export async function dismissAlert(alertId: number) {
    const res = await apiFetch(`/alerts/${alertId}/dismiss`, {
        method: "POST",
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || "Failed to dismiss alert");
    }
    return res.json();
}

export async function acknowledgeAlert(alertId: number) {
    const res = await apiFetch(`/alerts/${alertId}/acknowledge`, {
        method: "POST",
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || "Failed to acknowledge alert");
    }
    return res.json();
}

export async function resolveAlert(alertId: number) {
    const res = await apiFetch(`/alerts/${alertId}/resolve`, {
        method: "POST",
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || "Failed to resolve alert");
    }
    return res.json();
}

// ==================== INCIDENT ACTIONS ====================

export async function getIncident(incidentId: number) {
    const res = await apiFetch(`/incidents/${incidentId}`);
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || "Failed to get incident");
    }
    return res.json();
}

export async function resolveIncident(incidentId: number) {
    const res = await apiFetch(`/incidents/${incidentId}/resolve`, {
        method: "POST",
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || "Failed to resolve incident");
    }
    return res.json();
}

export async function escalateIncident(incidentId: number) {
    const res = await apiFetch(`/incidents/${incidentId}/escalate`, {
        method: "POST",
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || "Failed to escalate incident");
    }
    return res.json();
}

// ==================== USER MANAGEMENT ====================

export interface CreateUserData {
    username: string;
    password: string;
    role: "admin" | "operator" | "viewer" | "security";
}

export interface UpdateUserData {
    username?: string;
    password?: string;
    role?: "admin" | "operator" | "viewer" | "security";
    status?: "Active" | "Inactive";
}

export async function createUser(data: CreateUserData) {
    const res = await apiFetch("/users", {
        method: "POST",
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || "Failed to create user");
    }
    return res.json();
}

export async function updateUser(userId: number, data: UpdateUserData) {
    const res = await apiFetch(`/users/${userId}`, {
        method: "PUT",
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || "Failed to update user");
    }
    return res.json();
}

export async function deleteUser(userId: number) {
    const res = await apiFetch(`/users/${userId}`, {
        method: "DELETE",
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({}));
        throw new Error(error.error || "Failed to delete user");
    }
    return res.json();
}
