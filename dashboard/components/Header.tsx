"use client";

import { useState, useEffect } from 'react';
import { LogOut, User } from 'lucide-react';
import { useAuth } from '@/components/AuthProvider';

export function Header() {
  const { role, username, logout } = useAuth();
  const [currentTime, setCurrentTime] = useState<Date | null>(null);

  useEffect(() => {
    // Set initial time on client only to avoid hydration mismatch
    setCurrentTime(new Date());
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatDate = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="bg-black/40 backdrop-blur-md border-b border-[#00e5ff]/20 px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 bg-[#00e5ff] rounded-full shadow-[0_0_8px_#00e5ff] animate-pulse" />
            <span className="text-[#00e5ff]/70 font-mono text-[10px] uppercase tracking-widest">SYSTEM ONLINE</span>
          </div>
          <div className="h-4 w-px bg-[#00e5ff]/20" />
          <div className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 bg-[#22c55e] rounded-full shadow-[0_0_8px_#22c55e]" />
            <span className="text-[#22c55e]/70 font-mono text-[10px] uppercase tracking-widest">📹 CAMERA ACTIVE</span>
          </div>
          <div className="h-4 w-px bg-[#00e5ff]/20" />
          <div className="flex items-center gap-2 text-xs">
            <div className="w-2 h-2 bg-[#22c55e] rounded-full shadow-[0_0_8px_#22c55e] animate-pulse" />
            <span className="text-[#22c55e]/70 font-mono text-[10px] uppercase tracking-widest">🧠 AI DETECTING</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Date & Time */}
          <div className="flex items-center gap-2 font-mono">
            <span className="text-[#00e5ff]/50 text-xs">{'//'}</span>
            <span className="text-[#00e5ff] text-xs tracking-wider">{currentTime ? formatDate(currentTime) : '--'}</span>
            <span className="text-[#00e5ff]/50 text-xs">::</span>
            <span className="text-[#00e5ff] text-xs tracking-wider">{currentTime ? formatTime(currentTime) : '--:--:--'}</span>
          </div>

          {/* Divider */}
          <div className="h-4 w-px bg-[#00e5ff]/20" />

          {/* User badge */}
          <div className="flex items-center gap-2 bg-[#00e5ff]/10 border border-[#00e5ff]/30 rounded px-2.5 py-1">
            <User className="w-3 h-3 text-[#00e5ff]" />
            <span className="text-[#00e5ff] text-[10px] font-mono uppercase tracking-wider">
              {username || 'operator'} · {role || 'viewer'}
            </span>
          </div>

          {/* Sign Out */}
          <button
            onClick={logout}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 hover:border-red-400/50 hover:shadow-[0_0_12px_rgba(239,68,68,0.2)] rounded font-mono text-[10px] uppercase tracking-wider transition-all duration-200"
            title="Sign out"
          >
            <LogOut className="w-3 h-3" />
            <span>SIGN OUT</span>
          </button>
        </div>
      </div>
    </div>
  );
}
