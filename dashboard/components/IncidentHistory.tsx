"use client";

import { useState, useEffect } from 'react';
import { Search, Filter, Eye } from 'lucide-react';
import { getIncidents } from '@/lib/api';

interface Incident {
  id: number;
  title: string;
  description: string;
  event_type: string;
  location: string;
  risk_level: string;
  status: string;
  created_at: string;
  resolved_at: string | null;
}

function getRiskColor(risk: string) {
  switch (risk) {
    case 'high':
      return 'bg-red-950/50 text-red-400 border-red-900/50';
    case 'medium':
      return 'bg-yellow-950/50 text-yellow-400 border-yellow-900/50';
    case 'low':
      return 'bg-zinc-800 text-zinc-400 border-zinc-700';
    default:
      return 'bg-zinc-800 text-zinc-400 border-zinc-700';
  }
}

function getStatusColor(status: string) {
  switch (status) {
    case 'Resolved':
      return 'bg-green-950/30 text-green-500 border-green-900/50';
    case 'Under Review':
      return 'bg-blue-950/30 text-blue-400 border-blue-900/50';
    case 'Escalated':
      return 'bg-red-950/50 text-red-400 border-red-900/50';
    case 'False Alarm':
      return 'bg-zinc-800 text-zinc-500 border-zinc-700';
    default:
      return 'bg-zinc-800 text-zinc-400 border-zinc-700';
  }
}

export default function IncidentHistory() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all-status');

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const data = await getIncidents();
        setIncidents(Array.isArray(data) ? data : []);
      } catch {
        console.error('Failed to fetch incidents');
      } finally {
        setLoading(false);
      }
    };
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 10000);
    return () => clearInterval(interval);
  }, []);

  const filtered = incidents.filter((inc) => {
    const matchSearch =
      !searchQuery ||
      inc.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.event_type?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchRisk = riskFilter === 'all' || inc.risk_level === riskFilter;
    const matchStatus =
      statusFilter === 'all-status' ||
      inc.status?.toLowerCase().replace(' ', '-') === statusFilter;
    return matchSearch && matchRisk && matchStatus;
  });

  return (
    <div className="flex-1 bg-black overflow-auto">
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-medium text-white mb-1">Incidents</h1>
          <p className="text-zinc-500 text-sm">Review and analyze detection events</p>
        </div>

        <div className="bg-zinc-950 border border-zinc-800">
          <div className="border-b border-zinc-800 p-4">
            <h2 className="text-white text-sm font-medium">Incident Log</h2>
          </div>
          <div className="p-4">
            <div className="flex items-center gap-3 mb-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-zinc-600" />
                <input
                  placeholder="Search incidents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 bg-black border border-zinc-800 text-white placeholder:text-zinc-600 text-sm h-9 w-full rounded-md focus:outline-none focus:border-zinc-500 transition-colors"
                />
              </div>
              <div className="relative">
                <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-3.5 h-3.5 text-zinc-400" />
                <select
                  value={riskFilter}
                  onChange={(e) => setRiskFilter(e.target.value)}
                  className="w-40 pl-9 bg-black border border-zinc-800 text-white text-xs h-9 rounded-md focus:outline-none focus:border-zinc-500 appearance-none cursor-pointer"
                >
                  <option value="all">All Risk Levels</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-40 bg-black border border-zinc-800 text-white text-xs h-9 px-3 rounded-md focus:outline-none focus:border-zinc-500 appearance-none cursor-pointer"
              >
                <option value="all-status">All Status</option>
                <option value="resolved">Resolved</option>
                <option value="under-review">Under Review</option>
                <option value="escalated">Escalated</option>
              </select>
            </div>

            {loading ? (
              <p className="text-zinc-500 text-xs font-mono text-center py-8">Loading incidents...</p>
            ) : (
              <div className="border border-zinc-800 rounded-md overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[800px]">
                  <thead>
                    <tr className="border-b border-zinc-800 bg-zinc-900/30">
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">TIMESTAMP</th>
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">EVENT TYPE</th>
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">LOCATION</th>
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">RISK LEVEL</th>
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">STATUS</th>
                      <th className="p-3 text-zinc-500 text-xs font-mono font-medium">ACTION</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((incident) => (
                      <tr
                        key={incident.id}
                        className="border-b border-zinc-800 hover:bg-zinc-900/50 transition-colors last:border-0"
                      >
                        <td className="p-3 text-zinc-400 text-xs font-mono">
                          {incident.created_at}
                        </td>
                        <td className="p-3 text-white text-xs">
                          {incident.event_type || incident.title}
                        </td>
                        <td className="p-3 text-zinc-400 text-xs">
                          {incident.location}
                        </td>
                        <td className="p-3">
                          <div className={`inline-block px-2 py-0.5 border rounded text-xs font-mono ${getRiskColor(incident.risk_level)}`}>
                            {incident.risk_level?.toUpperCase()}
                          </div>
                        </td>
                        <td className="p-3">
                          <div className={`inline-block px-2 py-0.5 border rounded text-xs font-mono ${getStatusColor(incident.status)}`}>
                            {incident.status}
                          </div>
                        </td>
                        <td className="p-3">
                          <button className="flex items-center gap-1.5 text-zinc-500 hover:text-white hover:bg-zinc-800 text-xs h-7 px-2 rounded transition-colors">
                            <Eye className="w-3.5 h-3.5" />
                            Review
                          </button>
                        </td>
                      </tr>
                    ))}
                    {filtered.length === 0 && (
                      <tr>
                        <td colSpan={6} className="p-6 text-center text-zinc-600 text-xs font-mono">
                          No incidents found
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
