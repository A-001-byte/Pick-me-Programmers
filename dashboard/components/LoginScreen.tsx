"use client";

import { useState } from 'react';
import { Shield } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api';

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
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
        router.push('/monitor');
      } else {
        setError(result.error || 'Login failed');
      }
    } catch {
      setError('Cannot connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-red-950/50 p-3 border border-red-900/50">
              <Shield className="w-10 h-10 text-red-500" />
            </div>
          </div>
          <h1 className="text-2xl font-medium text-white mb-1">ThreatSense</h1>
          <p className="text-zinc-500 text-sm font-mono">Security Monitoring System</p>
        </div>

        <div className="bg-zinc-950 border border-zinc-800 p-6">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* TODO: Migrate from localStorage JWT to HttpOnly cookies for better security */}
            {error && (
              <div className="bg-red-950/40 border border-red-900/50 text-red-400 text-xs p-2 font-mono">
                {error}
              </div>
            )}
            <div className="space-y-2 flex flex-col">
              <label htmlFor="username" className="text-zinc-400 text-xs font-mono">USERNAME</label>
              <input
                id="username"
                type="text"
                placeholder="admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="bg-black border border-zinc-800 text-white placeholder:text-zinc-700 text-sm h-9 px-3 focus:outline-none focus:border-zinc-500 transition-colors"
                required
              />
            </div>

            <div className="space-y-2 flex flex-col">
              <label htmlFor="password" className="text-zinc-400 text-xs font-mono">PASSWORD</label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="bg-black border border-zinc-800 text-white placeholder:text-zinc-700 text-sm h-9 px-3 focus:outline-none focus:border-zinc-500 transition-colors"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-red-900/50 hover:bg-red-900/70 text-red-400 border border-red-900/50 text-sm h-9 transition-colors font-medium flex items-center justify-center disabled:opacity-50"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {process.env.NODE_ENV === 'development' && (
            <div className="mt-5 text-center">
              <p className="text-xs text-zinc-600 font-mono">
                Default: admin / admin
              </p>
            </div>
          )}
        </div>

        <div className="mt-6 text-center text-xs text-zinc-700 font-mono">
          © 2026 ThreatSense Security Systems
        </div>
      </div>
    </div>
  );
}
