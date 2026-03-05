"use client";

import { useState, useEffect } from 'react';

export function Header() {
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
        <div className="flex items-center gap-2 font-mono">
          <span className="text-[#00e5ff]/50 text-xs">{'//'}</span>
          <span className="text-[#00e5ff] text-xs tracking-wider">{currentTime ? formatDate(currentTime) : '--'}</span>
          <span className="text-[#00e5ff]/50 text-xs">::</span>
          <span className="text-[#00e5ff] text-xs tracking-wider">{currentTime ? formatTime(currentTime) : '--:--:--'}</span>
        </div>
      </div>
    </div>
  );
}
