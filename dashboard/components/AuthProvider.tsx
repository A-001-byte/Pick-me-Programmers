"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";

interface AuthState {
    token: string | null;
    role: string | null;
    username: string | null;
    logout: () => void;
}

const AuthContext = createContext<AuthState>({
    token: null,
    role: null,
    username: null,
    logout: () => { },
});

export function useAuth() {
    return useContext(AuthContext);
}

const PUBLIC_PATHS = ["/login", "/signup"];

export default function AuthProvider({ children }: { children: ReactNode }) {
    const router = useRouter();
    const pathname = usePathname();
    const [token, setToken] = useState<string | null>(null);
    const [role, setRole] = useState<string | null>(null);
    const [username, setUsername] = useState<string | null>(null);
    const [ready, setReady] = useState(false);

    // Read from localStorage on mount
    useEffect(() => {
        if (typeof window === "undefined") return;
        const t = localStorage.getItem("token");
        const r = localStorage.getItem("role");
        const u = localStorage.getItem("username");
        setToken(t);
        setRole(r);
        setUsername(u);
        setReady(true);
    }, []);

    // Redirect unauthenticated users away from protected pages
    useEffect(() => {
        if (!ready) return;
        const isPublic = PUBLIC_PATHS.some((p) => pathname?.startsWith(p));
        if (!token && !isPublic) {
            router.replace("/login");
        }
    }, [ready, token, pathname, router]);

    const logout = useCallback(() => {
        if (typeof window === "undefined") return;
        localStorage.removeItem("token");
        localStorage.removeItem("role");
        localStorage.removeItem("username");
        setToken(null);
        setRole(null);
        setUsername(null);
        router.replace("/login");
    }, [router]);

    // Show nothing until hydration is done to avoid flash
    if (!ready) return null;

    return (
        <AuthContext.Provider value={{ token, role, username, logout }}>
            {children}
        </AuthContext.Provider>
    );
}
