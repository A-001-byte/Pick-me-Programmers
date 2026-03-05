"use client";

import {
  MonitorPlay,
  AlertCircle,
  Users,
  Shield,
  LogOut,
  Activity
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Sidebar({ className = "" }: { className?: string }) {
  const pathname = usePathname();

  const navItems = [
    { id: 'monitor', path: '/monitor', label: 'LIVE SURVEILLANCE', icon: MonitorPlay, emoji: '📡' },
    { id: 'incidents', path: '/incidents', label: 'INCIDENT LOG', icon: AlertCircle, emoji: '📋' },
    { id: 'users', path: '/users', label: 'OPERATORS', icon: Users, emoji: '👥' },
  ];

  return (
    <div className={`bg-black/40 backdrop-blur-md border-r border-[#00e5ff]/20 flex flex-col h-screen ${className}`}>
      {/* Logo Section */}
      <div className="p-5 border-b border-[#00e5ff]/20">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded border border-[#00e5ff]/40 bg-[#00e5ff]/10 flex items-center justify-center">
            <Shield className="w-4 h-4 text-[#00e5ff]" />
          </div>
          <div>
            <h2 className="text-[#00e5ff] text-sm font-mono font-bold tracking-widest">THREATSENSE</h2>
            <p className="text-[#00e5ff]/40 text-[10px] font-mono tracking-wider">{'v2.0.4 // ACTIVE'}</p>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="px-4 py-3 border-b border-[#00e5ff]/20">
        <div className="flex items-center gap-2 mb-2">
          <Activity className="w-3 h-3 text-[#00e5ff]" />
          <span className="text-[#00e5ff]/70 text-[10px] font-mono uppercase tracking-widest">SYSTEM STATUS</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1 bg-[#00e5ff]/20 rounded-full overflow-hidden">
            <div className="h-full w-3/4 bg-gradient-to-r from-[#00e5ff] to-[#22c55e] rounded-full shadow-[0_0_8px_#00e5ff]"></div>
          </div>
          <span className="text-[#22c55e] text-[10px] font-mono">OPTIMAL</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        <p className="px-3 mb-2 text-[#00e5ff]/40 text-[10px] font-mono uppercase tracking-widest">{'// NAVIGATION'}</p>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname?.startsWith(item.path);

          return (
            <Link
              key={item.id}
              href={item.path}
              className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-r transition-all duration-300 text-xs ${isActive
                ? 'border-l-2 border-[#00e5ff] bg-[#00e5ff]/10 text-[#00e5ff] shadow-[inset_0_0_20px_rgba(0,229,255,0.1)]'
                : 'border-l-2 border-transparent text-zinc-400 hover:text-[#00e5ff] hover:bg-[#00e5ff]/5 hover:border-[#00e5ff]/50'
                }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-[#00e5ff] drop-shadow-[0_0_4px_#00e5ff]' : ''}`} />
              <span className="font-mono tracking-wider">{item.emoji} {item.label}</span>
              {isActive && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-[#00e5ff] shadow-[0_0_6px_#00e5ff] animate-pulse"></div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* AI Status */}
      <div className="p-4 border-t border-[#00e5ff]/20">
        <div className="bg-black/60 border border-[#00e5ff]/20 rounded p-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-2 h-2 rounded-full bg-[#22c55e] shadow-[0_0_6px_#22c55e] animate-pulse"></div>
            <span className="text-[#22c55e] text-[10px] font-mono uppercase tracking-widest">🧠 AI ENGINE ACTIVE</span>
          </div>
          <p className="text-zinc-500 text-[10px] font-mono">Neural threat detection online...</p>
        </div>
      </div>

      {/* Logout */}
      <div className="p-3 border-t border-[#00e5ff]/20">
        <button
          onClick={() => {
            if (typeof window !== 'undefined') {
              localStorage.removeItem('token');
              localStorage.removeItem('role');
              window.location.href = '/login';
            }
          }}
          className="w-full flex items-center justify-start text-red-500/70 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/30 rounded-md text-xs px-3 py-2 transition-all font-mono uppercase tracking-wider"
        >
          <LogOut className="w-4 h-4 mr-2.5" />
          <span>🔌 DISCONNECT</span>
        </button>
      </div>
    </div>
  );
}
