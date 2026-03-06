"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginCard() {
  const router = useRouter();
  const [operatorId, setOperatorId] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const AUTH_BASE = process.env.NEXT_PUBLIC_AUTH_URL || "http://localhost:5000/api";

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${AUTH_BASE}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: operatorId, password }),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("token", data.token);
        localStorage.setItem("role", data.role);
        localStorage.setItem("username", operatorId);
        router.push("/dashboard");
      } else {
        alert("Invalid credentials");
      }
    } catch (error) {
      alert("Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{`
        .bg-dark { background-color: #0a0a0c; }
        .text-cyan { color: #00e5ff; }
        .border-cyan { border-color: #00e5ff; }
        .bg-cyan-dim { background-color: rgba(0, 229, 255, 0.1); }
        .shadow-cyan { box-shadow: 0 0 30px rgba(0, 229, 255, 0.05); }
        
        .scanlines {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
                        linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            background-size: 100% 4px, 3px 100%; z-index: 2; pointer-events: none;
        }

        .weapon-scanner {
            position: absolute; top: -100%; left: 0; width: 100%; height: 200%;
            background: linear-gradient(to bottom, transparent 45%, rgba(0, 229, 255, 0.1) 50%, #00e5ff 50%, rgba(0, 229, 255, 0.1) 50.5%, transparent 55%);
            animation: scan 4s linear infinite; pointer-events: none; opacity: 0.6;
        }

        @keyframes scan { 0% { transform: translateY(0); } 100% { transform: translateY(100%); } }
        
        @keyframes glitch {
            0% { transform: translate(0) }
            20% { transform: translate(-2px, 2px) }
            40% { transform: translate(-2px, -2px) }
            60% { transform: translate(2px, 2px) }
            80% { transform: translate(2px, -2px) }
            100% { transform: translate(0) }
        }
        .glitch-anim { animation: glitch 0.2s ease-in-out; }
        .pulse-anim { animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
      `}</style>

      <div className="min-h-screen bg-dark flex items-center justify-center relative overflow-hidden font-sans">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover opacity-50 z-0 pointer-events-none"
        >
          <source src="/surveillance-bg.mp4" type="video/mp4" />
        </video>

        <div className="absolute inset-0 bg-[#0a0a0c]/40 z-1 pointer-events-none"></div>

        <div className="scanlines"></div>

        <div className="relative z-10 bg-[#0a0a0c]/80 backdrop-blur-md border border-cyan/30 p-10 w-[380px] rounded shadow-cyan overflow-hidden pointer-events-auto">
          <div className="weapon-scanner"></div>

          <div className="text-center mb-8 relative z-20">
            <svg className="w-10 h-10 mx-auto fill-none stroke-[#00e5ff] stroke-2 mb-3 drop-shadow-[0_0_8px_rgba(0,229,255,0.8)]" viewBox="0 0 24 24">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              <circle cx="12" cy="11" r="3"></circle>
            </svg>
            <h1 className="text-xl tracking-[3px] font-semibold text-white mb-1">THREATSENSE</h1>
            <p className="font-mono text-[10px] text-zinc-400 tracking-[1px]">{'// SECURE UPLINK //'}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5 relative z-20">
            <div className="space-y-1.5 flex flex-col">
              <label htmlFor="operatorId" className="font-mono text-[11px] text-cyan uppercase">Operator ID 👤</label>
              <input
                id="operatorId"
                type="text"
                placeholder="SYS_ADMIN_01"
                value={operatorId}
                onChange={(event) => setOperatorId(event.target.value)}
                className="w-full p-2.5 bg-black/60 border border-zinc-800 text-white font-mono text-sm focus:outline-none focus:border-cyan transition-colors"
                required
              />
            </div>

            <div className="space-y-1.5 flex flex-col">
              <label htmlFor="password" className="font-mono text-[11px] text-cyan uppercase">Passkey 🔑</label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full p-2.5 bg-black/60 border border-zinc-800 text-white font-mono text-sm focus:outline-none focus:border-cyan transition-colors"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full p-3 bg-black/40 border border-cyan text-cyan font-mono uppercase cursor-pointer transition-all hover:bg-cyan-dim hover:shadow-[0_0_15px_rgba(0,229,255,0.4)] disabled:border-zinc-600 disabled:text-zinc-600 flex items-center justify-center mt-2"
            >
              {loading ? <span className="pulse-anim">Authenticating...</span> : <span className="tracking-[1px] font-bold">INITIALIZE CONNECTION</span>}
            </button>
          </form>

          <div className="mt-4 text-center text-xs text-zinc-400 font-mono relative z-20">
            New Operator? <button type="button" onClick={() => router.push("/signup")} className="text-cyan underline decoration-dotted hover:text-white transition-colors">Register</button>
          </div>
        </div>
      </div>
    </>
  );
}
