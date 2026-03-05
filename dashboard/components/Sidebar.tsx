"use client";

import {
  MonitorPlay,
  AlertCircle,
  Users,
  Settings,
  Shield,
  LogOut
} from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Sidebar({ className = "" }: { className?: string }) {
  const pathname = usePathname();

  const navItems = [
    { id: 'monitor', path: '/monitor', label: 'Live Monitor', icon: MonitorPlay },
    { id: 'incidents', path: '/incidents', label: 'Incidents', icon: AlertCircle },
    { id: 'users', path: '/users', label: 'Users', icon: Users },
  ];

  return (
    <div className={`bg-zinc-950 border-zinc-800 flex flex-col h-screen ${className}`}>
      <div className="p-5 border-b border-zinc-800">
        <div className="flex items-center gap-2.5">
          <div className="bg-red-950/50 p-1.5 border border-red-900/50">
            <Shield className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <h2 className="font-medium text-white text-sm">ThreatSense</h2>
            <p className="text-xs text-zinc-600 font-mono">SECURITY</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname?.startsWith(item.path);

          return (
            <Link
              key={item.id}
              href={item.path}
              className={`w-full flex items-center gap-2.5 px-3 py-2 transition-colors text-xs ${isActive
                ? 'bg-red-950/50 text-red-400 border border-red-900/50'
                : 'text-zinc-500 hover:bg-zinc-900 hover:text-zinc-300 border border-transparent'
                }`}
            >
              <Icon className="w-4 h-4" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-zinc-800">
        <button
          onClick={() => {
            if (typeof window !== 'undefined') {
              localStorage.removeItem('token');
              localStorage.removeItem('role');
              // Option: trigger a router.push('/login') but window.location works simply
              window.location.href = '/login';
            }
          }}
          className="w-full flex items-center justify-start text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900 rounded-md text-xs px-3 py-2 transition font-medium"
        >
          <LogOut className="w-4 h-4 mr-2.5" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}
