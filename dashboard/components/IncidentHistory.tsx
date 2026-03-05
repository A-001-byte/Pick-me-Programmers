"use client";

import { useState, useEffect, useCallback } from 'react';
import { Search, Filter, Eye, Check, AlertTriangle, X, ArrowUp } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { getIncidents, resolveIncident, escalateIncident } from '@/lib/api';

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
  const normalizedRisk = (risk || '').toLowerCase();
  switch (normalizedRisk) {
    case 'high':
    case 'critical':
      return 'border-red-500 text-red-500 bg-red-500/10 shadow-[0_0_8px_rgba(239,68,68,0.4)]';
    case 'medium':
    case 'suspicious':
      return 'border-yellow-500 text-yellow-500 bg-yellow-500/10 shadow-[0_0_8px_rgba(234,179,8,0.3)]';
    case 'low':
      return 'border-[#22c55e] text-[#22c55e] bg-[#22c55e]/10 shadow-[0_0_8px_rgba(34,197,94,0.3)]';
    default:
      return 'border-[#00e5ff] text-[#00e5ff] bg-[#00e5ff]/10 shadow-[0_0_8px_rgba(0,229,255,0.3)]';
  }
}

function getStatusColor(status: string) {
  const normalizedStatus = (status || '').toLowerCase();
  switch (normalizedStatus) {
    case 'resolved':
      return 'border-[#22c55e] text-[#22c55e] bg-[#22c55e]/10 shadow-[0_0_8px_rgba(34,197,94,0.3)]';
    case 'under review':
      return 'border-[#00e5ff] text-[#00e5ff] bg-[#00e5ff]/10 shadow-[0_0_8px_rgba(0,229,255,0.3)]';
    case 'escalated':
      return 'border-red-500 text-red-500 bg-red-500/10 shadow-[0_0_8px_rgba(239,68,68,0.4)]';
    case 'false alarm':
      return 'border-zinc-500 text-zinc-500 bg-zinc-500/10';
    case 'open':
      return 'border-yellow-500 text-yellow-500 bg-yellow-500/10 shadow-[0_0_8px_rgba(234,179,8,0.3)]';
    default:
      return 'border-zinc-500 text-zinc-500 bg-zinc-500/10';
  }
}

export default function IncidentHistory() {
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get('search') || '';
  
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState(initialSearch);
  const [riskFilter, setRiskFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all-status');
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [showModal, setShowModal] = useState(false);

  const fetchIncidents = useCallback(async () => {
    try {
      const data = await getIncidents();
      setIncidents(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch incidents', err);
      setError('Failed to connect to backend');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 10000);
    return () => clearInterval(interval);
  }, [fetchIncidents]);

  // Update search when URL param changes
  useEffect(() => {
    const urlSearch = searchParams.get('search');
    if (urlSearch) {
      setSearchQuery(urlSearch);
    }
  }, [searchParams]);

  const handleResolve = async (incidentId: number) => {
    setActionLoading(incidentId);
    try {
      await resolveIncident(incidentId);
      await fetchIncidents();
      setError(null);
      if (selectedIncident?.id === incidentId) {
        setSelectedIncident(prev => prev ? { ...prev, status: 'Resolved' } : null);
      }
    } catch (err) {
      console.error('Failed to resolve incident:', err);
      setError(err instanceof Error ? err.message : 'Failed to resolve incident');
    } finally {
      setActionLoading(null);
    }
  };

  const handleEscalate = async (incidentId: number) => {
    setActionLoading(incidentId);
    try {
      await escalateIncident(incidentId);
      await fetchIncidents();
      setError(null);
      if (selectedIncident?.id === incidentId) {
        setSelectedIncident(prev => prev ? { ...prev, status: 'Escalated' } : null);
      }
    } catch (err) {
      console.error('Failed to escalate incident:', err);
      setError(err instanceof Error ? err.message : 'Failed to escalate incident');
    } finally {
      setActionLoading(null);
    }
  };

  const handleView = (incident: Incident) => {
    setSelectedIncident(incident);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedIncident(null);
  };

  const filtered = incidents.filter((inc) => {
    const matchSearch =
      !searchQuery ||
      inc.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.event_type?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      inc.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchRisk = riskFilter === 'all' || inc.risk_level?.toLowerCase() === riskFilter;
    const matchStatus =
      statusFilter === 'all-status' ||
      inc.status?.toLowerCase().replace(/\s+/g, '-') === statusFilter;
    return matchSearch && matchRisk && matchStatus;
  });

  return (
    <div className="flex-1 bg-[#0a0a0c] overflow-auto">
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-[#00e5ff] text-xl font-mono font-bold tracking-widest uppercase flex items-center gap-2">📋 INCIDENT LOG</h1>
          <p className="text-zinc-500 text-sm font-mono mt-1">{'// Review and analyze detection events'}</p>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0" />
              <p className="text-yellow-400 text-sm font-mono">⚠️ {error}</p>
            </div>
          </div>
        )}

        <div className="bg-black/40 backdrop-blur-md border border-[#00e5ff]/20 rounded-lg overflow-hidden">
          <div className="border-b border-[#00e5ff]/20 p-4">
            <h2 className="text-[#00e5ff] font-mono text-xs uppercase tracking-widest">📊 EVENT DATABASE</h2>
          </div>
          <div className="p-4">
            <div className="flex flex-wrap items-center gap-3 mb-4">
              <div className="relative flex-1 min-w-[200px]">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#00e5ff]/50" />
                <input
                  aria-label="Search incidents"
                  placeholder="🔍 SEARCH DATABANKS..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2.5 bg-black/60 border border-[#00e5ff]/30 text-zinc-300 placeholder:text-zinc-600 text-sm w-full rounded-md focus:outline-none focus:border-[#00e5ff] focus:shadow-[0_0_15px_rgba(0,229,255,0.15)] font-mono transition-all"
                />
              </div>
              <div className="relative">
                <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#00e5ff]/50" />
                <select
                  aria-label="Filter by risk level"
                  value={riskFilter}
                  onChange={(e) => setRiskFilter(e.target.value)}
                  className="w-44 pl-10 pr-4 py-2.5 bg-black/60 border border-[#00e5ff]/30 text-zinc-300 text-xs rounded-md focus:outline-none focus:border-[#00e5ff] font-mono transition-all appearance-none cursor-pointer"
                >
                  <option value="all">ALL RISK LEVELS</option>
                  <option value="high">⚠️ HIGH</option>
                  <option value="medium">🔶 MEDIUM</option>
                  <option value="low">🟢 LOW</option>
                </select>
              </div>
              <select
                aria-label="Filter by status"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-44 px-4 py-2.5 bg-black/60 border border-[#00e5ff]/30 text-zinc-300 text-xs rounded-md focus:outline-none focus:border-[#00e5ff] font-mono transition-all appearance-none cursor-pointer"
              >
                <option value="all-status">ALL STATUS</option>
                <option value="open">● OPEN</option>
                <option value="resolved">✓ RESOLVED</option>
                <option value="under-review">👁️ UNDER REVIEW</option>
                <option value="escalated">🚨 ESCALATED</option>
                <option value="false-alarm">❌ FALSE ALARM</option>
              </select>
            </div>

            {loading ? (
              <div className="space-y-2">
                {[1,2,3,4,5].map(i => (
                  <div key={i} className="animate-pulse flex items-center gap-4 p-3 bg-black/40 border border-[#00e5ff]/10 rounded">
                    <div className="h-4 bg-zinc-800 rounded w-24"></div>
                    <div className="h-4 bg-zinc-800 rounded w-32"></div>
                    <div className="h-4 bg-zinc-800 rounded w-20"></div>
                    <div className="h-4 bg-zinc-800 rounded w-16"></div>
                    <div className="h-4 bg-zinc-800 rounded w-16"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="border border-[#00e5ff]/20 rounded-md overflow-x-auto">
                <table className="w-full text-left border-collapse min-w-[900px]">
                  <thead>
                    <tr className="border-b border-[#00e5ff]/20">
                      <th className="p-4 text-[#00e5ff]/70 text-[10px] font-mono font-medium uppercase tracking-widest">TIMESTAMP</th>
                      <th className="p-4 text-[#00e5ff]/70 text-[10px] font-mono font-medium uppercase tracking-widest">EVENT TYPE</th>
                      <th className="p-4 text-[#00e5ff]/70 text-[10px] font-mono font-medium uppercase tracking-widest">LOCATION</th>
                      <th className="p-4 text-[#00e5ff]/70 text-[10px] font-mono font-medium uppercase tracking-widest">RISK LEVEL</th>
                      <th className="p-4 text-[#00e5ff]/70 text-[10px] font-mono font-medium uppercase tracking-widest">STATUS</th>
                      <th className="p-4 text-[#00e5ff]/70 text-[10px] font-mono font-medium uppercase tracking-widest">ACTIONS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.map((incident) => {
                      const isResolved = incident.status?.toLowerCase() === 'resolved';
                      const isEscalated = incident.status?.toLowerCase() === 'escalated';
                      
                      return (
                        <tr
                          key={incident.id}
                          className="border-b border-[#00e5ff]/10 hover:bg-[#00e5ff]/5 transition-colors last:border-0"
                        >
                          <td className="p-4 text-zinc-400 text-xs font-mono">
                            {incident.created_at}
                          </td>
                          <td className="p-4 text-zinc-300 text-xs font-mono">
                            {incident.event_type || incident.title}
                          </td>
                          <td className="p-4 text-zinc-400 text-xs font-mono">
                            {incident.location}
                          </td>
                          <td className="p-4">
                            <div className={`inline-block px-2 py-0.5 border rounded text-[10px] font-mono uppercase ${getRiskColor(incident.risk_level)}`}>
                              {incident.risk_level?.toUpperCase()}
                            </div>
                          </td>
                          <td className="p-4">
                            <div className={`inline-block px-2 py-0.5 border rounded text-[10px] font-mono uppercase ${getStatusColor(incident.status)}`}>
                              {incident.status}
                            </div>
                          </td>
                          <td className="p-4">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleView(incident)}
                                className="px-2 py-1 bg-transparent border border-[#00e5ff]/50 text-[#00e5ff] hover:bg-[#00e5ff]/20 hover:shadow-[0_0_10px_rgba(0,229,255,0.2)] rounded font-mono text-[10px] uppercase tracking-wider transition-all flex items-center gap-1"
                                title="View details"
                              >
                                <Eye className="w-3 h-3" />
                                👁️ VIEW
                              </button>
                              {!isResolved && (
                                <button
                                  onClick={() => handleResolve(incident.id)}
                                  disabled={actionLoading === incident.id}
                                  className="px-2 py-1 bg-transparent border border-[#22c55e]/50 text-[#22c55e] hover:bg-[#22c55e]/20 hover:shadow-[0_0_10px_rgba(34,197,94,0.2)] rounded font-mono text-[10px] uppercase tracking-wider transition-all flex items-center gap-1 disabled:opacity-50"
                                  title="Resolve incident"
                                >
                                  <Check className="w-3 h-3" />
                                  {actionLoading === incident.id ? '...' : '✅ RESOLVE'}
                                </button>
                              )}
                              {!isResolved && !isEscalated && (
                                <button
                                  onClick={() => handleEscalate(incident.id)}
                                  disabled={actionLoading === incident.id}
                                  className="px-2 py-1 bg-transparent border border-red-500/50 text-red-500 hover:bg-red-500/20 hover:shadow-[0_0_10px_rgba(239,68,68,0.2)] rounded font-mono text-[10px] uppercase tracking-wider transition-all flex items-center gap-1 disabled:opacity-50"
                                  title="Escalate incident"
                                >
                                  <ArrowUp className="w-3 h-3" />
                                  {actionLoading === incident.id ? '...' : '🚨 ESCALATE'}
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {filtered.length === 0 && (
                      <tr>
                        <td colSpan={6} className="p-8 text-center text-zinc-600 text-xs font-mono">
                          {'// NO INCIDENTS MATCHING CRITERIA'}
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

      {/* Incident Detail Modal */}
      {showModal && selectedIncident && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#0a0a0c] border border-[#00e5ff]/30 rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto shadow-[0_0_30px_rgba(0,229,255,0.2)]">
            <div className="flex items-center justify-between p-4 border-b border-[#00e5ff]/20">
              <h2 className="text-[#00e5ff] font-mono text-sm uppercase tracking-widest">📋 INCIDENT DETAILS</h2>
              <button
                onClick={closeModal}
                className="text-zinc-500 hover:text-[#00e5ff] transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="text-[#00e5ff]/60 text-[10px] font-mono uppercase tracking-wider block mb-1">EVENT TYPE</label>
                <p className="text-zinc-300 font-mono">{selectedIncident.event_type || selectedIncident.title}</p>
              </div>
              <div>
                <label className="text-[#00e5ff]/60 text-[10px] font-mono uppercase tracking-wider block mb-1">DESCRIPTION</label>
                <p className="text-zinc-400 text-sm">{selectedIncident.description || 'No description available'}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-zinc-500 text-xs font-mono block mb-1">Location</label>
                  <p className="text-white text-sm">{selectedIncident.location}</p>
                </div>
                <div>
                  <label className="text-zinc-500 text-xs font-mono block mb-1">Created At</label>
                  <p className="text-white text-sm">{selectedIncident.created_at}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-zinc-500 text-xs font-mono block mb-1">Risk Level</label>
                  <div className={`inline-block px-2 py-0.5 border rounded text-xs font-mono ${getRiskColor(selectedIncident.risk_level)}`}>
                    {selectedIncident.risk_level?.toUpperCase()}
                  </div>
                </div>
                <div>
                  <label className="text-zinc-500 text-xs font-mono block mb-1">Status</label>
                  <div className={`inline-block px-2 py-0.5 border rounded text-xs font-mono ${getStatusColor(selectedIncident.status)}`}>
                    {selectedIncident.status}
                  </div>
                </div>
              </div>
              {selectedIncident.resolved_at && (
                <div>
                  <label className="text-[#00e5ff]/60 text-[10px] font-mono uppercase tracking-wider block mb-1">RESOLVED AT</label>
                  <p className="text-green-400 text-sm font-mono">{selectedIncident.resolved_at}</p>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2 p-4 border-t border-[#00e5ff]/20">
              {selectedIncident.status?.toLowerCase() !== 'resolved' && (
                <>
                  <button
                    onClick={() => handleResolve(selectedIncident.id)}
                    disabled={actionLoading === selectedIncident.id}
                    className="flex items-center gap-1.5 bg-transparent border border-green-500/50 text-green-400 hover:bg-green-500/20 hover:shadow-[0_0_10px_rgba(34,197,94,0.2)] font-mono text-[10px] uppercase tracking-wider px-3 h-8 rounded transition-all disabled:opacity-50"
                  >
                    <Check className="w-3 h-3" />
                    {actionLoading === selectedIncident.id ? '...' : '✅ RESOLVE'}
                  </button>
                  {selectedIncident.status?.toLowerCase() !== 'escalated' && (
                    <button
                      onClick={() => handleEscalate(selectedIncident.id)}
                      disabled={actionLoading === selectedIncident.id}
                      className="flex items-center gap-1.5 bg-transparent border border-red-500/50 text-red-400 hover:bg-red-500/20 hover:shadow-[0_0_10px_rgba(239,68,68,0.2)] font-mono text-[10px] uppercase tracking-wider px-3 h-8 rounded transition-all disabled:opacity-50"
                    >
                      <ArrowUp className="w-3 h-3" />
                      {actionLoading === selectedIncident.id ? '...' : '🚨 ESCALATE'}
                    </button>
                  )}
                </>
              )}
              <button
                onClick={closeModal}
                className="flex items-center gap-1.5 bg-transparent border border-[#00e5ff]/30 text-[#00e5ff]/70 hover:bg-[#00e5ff]/10 hover:text-[#00e5ff] font-mono text-[10px] uppercase tracking-wider px-3 h-8 rounded transition-all ml-auto"
              >
                ✕ CLOSE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
