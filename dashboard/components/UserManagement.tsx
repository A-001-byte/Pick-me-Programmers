"use client";

import { useState, useEffect } from 'react';
import { Search, UserPlus, Edit, Trash2 } from 'lucide-react';
import { getUsers } from '@/lib/api';

interface User {
  id: number;
  username: string;
  role: string;
  status: string;
  last_active: string;
}

function getInitials(name: string) {
  return name
    .split(/[\s._-]/)
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

function getRoleBadgeColor(role: string) {
  switch (role) {
    case 'admin':
      return 'bg-red-950/50 text-red-400 border-red-900/50';
    case 'security':
      return 'bg-zinc-800 text-zinc-300 border-zinc-700';
    case 'viewer':
      return 'bg-zinc-800 text-zinc-400 border-zinc-700';
    default:
      return 'bg-zinc-800 text-zinc-400 border-zinc-700';
  }
}

export default function UserManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const data = await getUsers();
        setUsers(Array.isArray(data) ? data : []);
      } catch {
        console.error('Failed to fetch users');
      } finally {
        setLoading(false);
      }
    };
    fetchUsers();
  }, []);

  const filtered = users.filter(
    (u) =>
      !searchQuery ||
      u.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.role.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 bg-black overflow-auto">
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-medium text-white mb-1">Users</h1>
          <p className="text-zinc-500 text-sm">Manage system users and permissions</p>
        </div>

        <div className="bg-zinc-950 border border-zinc-800">
          <div className="border-b border-zinc-800 p-4">
            <div className="flex items-center justify-between">
              <h2 className="text-white text-sm font-medium">User Accounts</h2>
              <button
                type="button"
                disabled
                aria-disabled="true"
                title="Coming soon"
                className="flex items-center bg-red-900/50 text-red-400/50 border border-red-900/50 text-xs px-3 h-8 rounded-md transition-colors font-medium opacity-50 cursor-not-allowed"
              >
                <UserPlus className="w-3 h-3 mr-1.5" />
                Add User
              </button>
            </div>
          </div>
          <div className="p-4">
            <div className="mb-4">
              <div className="relative flex items-center gap-2">
                <label htmlFor="user-search" className="sr-only">Search users</label>
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-zinc-600" />
                <input
                  id="user-search"
                  placeholder="Search users..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 bg-black border border-zinc-800 text-white placeholder:text-zinc-600 text-sm h-9 w-full md:w-80 rounded-md focus:outline-none focus:border-zinc-500 transition-colors"
                />
              </div>
            </div>

            {loading ? (
              <p className="text-zinc-500 text-xs font-mono text-center py-8">Loading users...</p>
            ) : (
              <div className="border border-zinc-800 rounded-md overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[800px]">
                  <thead>
                    <tr className="border-b border-zinc-800 bg-zinc-900/30">
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">USER</th>
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">ROLE</th>
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">STATUS</th>
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">LAST ACTIVE</th>
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((user) => (
                      <tr
                        key={user.id}
                        className="border-b border-zinc-800 hover:bg-zinc-900/50 transition-colors last:border-0"
                      >
                        <td className="p-3">
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 bg-zinc-800 border border-zinc-700 rounded-full flex items-center justify-center shrink-0">
                              <span className="text-white text-xs font-medium">
                                {getInitials(user.username)}
                              </span>
                            </div>
                            <div>
                              <div className="text-white text-sm font-medium">{user.username}</div>
                              <div className="text-zinc-500 text-xs font-mono">{user.username}@threatsense.io</div>
                            </div>
                          </div>
                        </td>
                        <td className="p-3">
                          <div className={`inline-block px-2 py-0.5 border rounded text-xs font-mono capitalize ${getRoleBadgeColor(user.role)}`}>
                            {user.role}
                          </div>
                        </td>
                        <td className="p-3">
                          <div
                            className={`inline-block px-2 py-0.5 border rounded text-xs font-mono ${(user.status || '').toString().trim().toLowerCase() === 'active'
                                ? 'bg-green-950/30 text-green-500 border-green-900/50'
                                : 'bg-zinc-800 text-zinc-500 border-zinc-700'
                              }`}
                          >
                            {user.status}
                          </div>
                        </td>
                        <td className="p-3 text-zinc-400 text-xs font-mono">
                          {user.last_active}
                        </td>
                        <td className="p-3">
                          <div className="flex items-center gap-1">
                            <button
                              type="button"
                              disabled
                              aria-disabled="true"
                              title="Coming soon"
                              className="flex items-center justify-center text-zinc-500 h-7 w-7 rounded transition-colors opacity-50 cursor-not-allowed"
                              aria-label={`Edit ${user.username}`}
                            >
                              <Edit className="w-3.5 h-3.5" />
                            </button>
                            <button
                              type="button"
                              disabled
                              aria-disabled="true"
                              title="Coming soon"
                              className="flex items-center justify-center text-zinc-500 h-7 w-7 rounded transition-colors opacity-50 cursor-not-allowed"
                              aria-label={`Delete ${user.username}`}
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {filtered.length === 0 && (
                      <tr>
                        <td colSpan={5} className="p-6 text-center text-zinc-600 text-xs font-mono">
                          No users found
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
