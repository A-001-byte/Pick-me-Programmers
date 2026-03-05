"use client";

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api';

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [waitingForFlash, setWaitingForFlash] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(username, password);

      if ('token' in result) {
        localStorage.setItem('token', result.token);
        localStorage.setItem('role', result.role);
        // Wait for video to reach the flash at the end
        setWaitingForFlash(true);
        const video = videoRef.current;
        if (video) {
          const checkFlash = () => {
            // Redirect when video is near the end (last 0.3 seconds where flash occurs)
            if (video.duration - video.currentTime <= 0.3) {
              router.push('/monitor');
            } else {
              requestAnimationFrame(checkFlash);
            }
          };
          checkFlash();
        } else {
          // Fallback if no video
          router.push('/monitor');
        }
      } else {
        setError(result.error || 'UNRECOGNIZED BIOMETRIC/KEY');
      }
    } catch {
      setError('CONNECTION FAILED: HOST UNREACHABLE');
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
        
        {/* Background Video Element */}
        <video 
          ref={videoRef}
          autoPlay 
          loop 
          muted 
          playsInline 
          className="absolute inset-0 w-full h-full object-cover opacity-50 z-0"
        >
          {/* Place your video in the /public folder of your Next.js app */}
          <source src="/surveillance-bg.mp4" type="video/mp4" />
        </video>

        {/* Video Overlay (darkens the video so the UI remains readable) */}
        <div className="absolute inset-0 bg-[#0a0a0c]/40 z-1 pointer-events-none"></div>

        <div className="scanlines"></div>

        {/* Main Login Card */}
        <div className="relative z-10 bg-[#0a0a0c]/80 backdrop-blur-md border border-cyan/30 p-10 w-[380px] rounded shadow-cyan overflow-hidden">
          <div className="weapon-scanner"></div>

          <div className="text-center mb-8 relative z-20">
            <svg className="w-10 h-10 mx-auto fill-none stroke-[#00e5ff] stroke-2 mb-3 drop-shadow-[0_0_8px_rgba(0,229,255,0.8)]" viewBox="0 0 24 24">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              <circle cx="12" cy="11" r="3"></circle>
            </svg>
            <h1 className="text-xl tracking-[3px] font-semibold text-white mb-1">THREATSENSE</h1>
            <p className="font-mono text-[10px] text-zinc-400 tracking-[1px]">// SECURE UPLINK //</p>
          </div>

          {error && (
            <div className="glitch-anim border-l-2 border-red-500 bg-red-500/10 p-2.5 font-mono text-xs text-red-500 mb-5 relative z-20">
              ⚠️ ERR 401: {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5 relative z-20">
            <div className="space-y-1.5 flex flex-col">
              <label htmlFor="username" className="font-mono text-[11px] text-cyan uppercase">Operator ID 👤</label>
              <input
                id="username"
                type="text"
                placeholder="SYS_ADMIN_01"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
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
                onChange={(e) => setPassword(e.target.value)}
                className="w-full p-2.5 bg-black/60 border border-zinc-800 text-white font-mono text-sm focus:outline-none focus:border-cyan transition-colors"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading || waitingForFlash}
              className="w-full p-3 bg-black/40 border border-cyan text-cyan font-mono uppercase cursor-pointer transition-all hover:bg-cyan-dim hover:shadow-[0_0_15px_rgba(0,229,255,0.4)] disabled:border-zinc-600 disabled:text-zinc-600 flex items-center justify-center mt-2"
            >
              {waitingForFlash ? (
                <span className="pulse-anim">Syncing...</span>
              ) : loading ? (
                <span className="pulse-anim">Authenticating...</span>
              ) : (
                <span className="tracking-[1px] font-bold">Initialize Connection</span>
              )}
            </button>
          </form>

          {process.env.NODE_ENV === 'development' && (
            <div className="mt-6 text-center relative z-20">
              <p className="text-[10px] text-zinc-600 font-mono">
                DEV OVERRIDE: admin / admin
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
}