"use client";

import { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, Clock, Check, X, Eye, Video, Activity } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { getAlerts, getStats, dismissAlert, acknowledgeAlert, resolveAlert } from '@/lib/api';

interface Alert {
  id: number;
  person_id: string;
  event_type: string;
  risk_score: number;
  risk_level: string;
  timestamp: string;
  camera_id: string;
  location: string;
  status: string;
}

interface Stats {
  total_alerts: number;
  total_incidents: number;
  active_incidents: number;
  high_risk_alerts: number;
}

function getRiskColor(risk: string) {
  const normalizedRisk = (risk || '').toLowerCase();
  switch (normalizedRisk) {
    case 'high':
    case 'critical':
    case 'high_risk':
      return 'border-red-500 text-red-500 bg-red-500/10 shadow-[0_0_8px_rgba(239,68,68,0.4)]';
    case 'medium':
    case 'suspicious':
      return 'border-yellow-500 text-yellow-500 bg-yellow-500/10 shadow-[0_0_8px_rgba(234,179,8,0.3)]';
    case 'low':
      return 'border-[#00e5ff] text-[#00e5ff] bg-[#00e5ff]/10 shadow-[0_0_8px_rgba(0,229,255,0.3)]';
    default:
      return 'border-[#00e5ff] text-[#00e5ff] bg-[#00e5ff]/10 shadow-[0_0_8px_rgba(0,229,255,0.3)]';
  }
}

function formatTime(timestamp: string) {
  try {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { hour12: false });
  } catch {
    return timestamp;
  }
}

export default function LiveMonitor() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [bannerDismissed, setBannerDismissed] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [alertsData, statsData] = await Promise.all([
        getAlerts(10),
        getStats(),
      ]);
      setAlerts(Array.isArray(alertsData) ? alertsData : []);
      setStats(statsData);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch data', err);
      setError('Failed to connect to backend');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    // Poll every 3 seconds for real-time updates
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const activeAlerts = alerts.filter((a) => {
    const s = a.status?.toString().toLowerCase().trim();
    return s === 'active' || s === 'under review';
  });

  const handleDismissAlert = async (alertId: number) => {
    setActionLoading(alertId);
    try {
      await dismissAlert(alertId);
      await fetchData();
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleAcknowledgeAlert = async (alertId: number) => {
    setActionLoading(alertId);
    try {
      await acknowledgeAlert(alertId);
      await fetchData();
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResolveAlert = async (alertId: number) => {
    setActionLoading(alertId);
    try {
      await resolveAlert(alertId);
      await fetchData();
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReviewAlert = (alert: Alert) => {
    // Navigate to incidents page filtered by this event type
    router.push(`/incidents?search=${encodeURIComponent(alert.event_type)}`);
  };

  const handleEventClick = (alert: Alert) => {
    // Navigate to incidents page filtered for this event
    router.push(`/incidents?search=${encodeURIComponent(alert.event_type)}`);
  };

  const handleBannerDismiss = () => {
    // Only update local UI state - don't call backend dismiss
    // Backend alert dismissal should be done via a separate explicit action
    setBannerDismissed(true);
  };

  const handleDismissBannerAlert = async () => {
    // Explicit action to dismiss the alert in the backend
    if (activeAlerts.length > 0) {
      await handleDismissAlert(activeAlerts[0].id);
      setBannerDismissed(true);
    }
  };

  const showBanner = !bannerDismissed && activeAlerts.length > 0;

  return (
    <div className="flex-1 bg-[#0a0a0c] overflow-auto">
      <div className="p-6">
        {/* Error Banner */}
        {error && (
          <div className="mb-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 backdrop-blur-md">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0" />
              <p className="text-yellow-400 text-sm font-mono">⚠️ {error}</p>
            </div>
          </div>
        )}

        {/* Alert Banner */}
        {showBanner && (
          <div className="mb-4 bg-red-500/10 border border-red-500/50 rounded-lg p-4 backdrop-blur-md shadow-[0_0_20px_rgba(239,68,68,0.2)]">
            <div className="flex items-center gap-4">
              <div className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_10px_#ef4444] animate-pulse"></div>
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <div className="flex-1">
                <h3 className="text-red-400 font-mono text-sm uppercase tracking-wider">
                  ⚠️ ACTIVE THREAT: {activeAlerts[0]?.event_type}
                </h3>
                <p className="text-zinc-400 text-xs font-mono mt-0.5">
                  {`Detection at ${activeAlerts[0]?.location} - Review recommended`}
                </p>
              </div>
              <button
                onClick={handleDismissBannerAlert}
                disabled={actionLoading === activeAlerts[0]?.id}
                className="px-3 py-1.5 bg-transparent border border-red-500/50 text-red-400 hover:bg-red-500/20 hover:shadow-[0_0_15px_rgba(239,68,68,0.3)] rounded font-mono text-xs uppercase tracking-wider transition-all disabled:opacity-50"
              >
                {actionLoading === activeAlerts[0]?.id ? '...' : '🗑️ DISMISS ALERT'}
              </button>
              <button
                onClick={handleBannerDismiss}
                className="px-2 py-1.5 text-zinc-500 hover:text-zinc-300 font-mono text-xs transition-all"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-3">
            <div className="bg-black/40 backdrop-blur-md border border-[#00e5ff]/20 rounded-lg overflow-hidden hover:shadow-[0_0_20px_rgba(0,229,255,0.1)] transition-all">
              {/* Video Header */}
              <div className="p-4 border-b border-[#00e5ff]/20 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Video className="w-4 h-4 text-[#00e5ff]" />
                  <span className="text-[#00e5ff] font-mono text-sm uppercase tracking-widest">📡 PRIMARY FEED</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_#ef4444] animate-pulse"></div>
                  <span className="text-red-500 font-mono text-[10px] uppercase tracking-widest border border-red-500/50 px-2 py-0.5 bg-red-500/10">● LIVE</span>
                </div>
              </div>

              {/* Video Container with Scanlines */}
              <div className="relative aspect-video bg-black">
                {/* Scanline Overlay */}
                <div className="absolute inset-0 pointer-events-none z-10 opacity-20"
                  style={{
                    background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,229,255,0.03) 2px, rgba(0,229,255,0.03) 4px)'
                  }}
                ></div>
                
                <img
                  src={process.env.NEXT_PUBLIC_VIDEO_FEED_URL || "/api/video_feed"}
                  alt="Live Camera Feed"
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = "https://images.unsplash.com/photo-1760866613530-e3e09e013c42?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxidWlsZGluZyUyMGVudHJhbmNlJTIwc2VjdXJpdHl8ZW58MXx8fHwxNzcyNjE4OTIxfDA&ixlib=rb-4.1.0&q=80&w=1080";
                  }}
                />

                {/* Corner Brackets */}
                <div className="absolute top-4 left-4 w-8 h-8 border-l-2 border-t-2 border-[#00e5ff]/60"></div>
                <div className="absolute top-4 right-4 w-8 h-8 border-r-2 border-t-2 border-[#00e5ff]/60"></div>
                <div className="absolute bottom-4 left-4 w-8 h-8 border-l-2 border-b-2 border-[#00e5ff]/60"></div>
                <div className="absolute bottom-4 right-4 w-8 h-8 border-r-2 border-b-2 border-[#00e5ff]/60"></div>

                <div className="absolute top-3 right-3 bg-black/80 backdrop-blur-sm border border-[#00e5ff]/30 px-2 py-1 text-xs text-[#00e5ff] font-mono rounded">
                  {new Date().toLocaleTimeString()}
                </div>

                <div className="absolute bottom-3 left-3 right-3">
                  <div className="bg-black/80 backdrop-blur-sm border border-[#00e5ff]/30 p-3 rounded">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-[#00e5ff] text-sm font-mono uppercase tracking-wider">📹 CAM-01 Main Entrance</div>
                        <div className="text-zinc-500 text-[10px] font-mono">1920x1080 • 30fps</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-[#22c55e] shadow-[0_0_6px_#22c55e] animate-pulse"></div>
                        <span className="text-[#22c55e] font-mono text-[10px] uppercase tracking-widest border border-[#22c55e]/50 px-2 py-0.5 bg-[#22c55e]/10">🧠 DETECTING</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="border-t border-[#00e5ff]/20 p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="w-4 h-4 text-[#00e5ff]" />
                  <h3 className="text-[#00e5ff] font-mono text-xs uppercase tracking-widest">📋 RECENT EVENTS</h3>
                </div>
                {loading ? (
                  <div className="space-y-2">
                    {[1,2,3].map(i => (
                      <div key={i} className="animate-pulse flex items-center justify-between p-3 bg-black/40 border border-[#00e5ff]/10 rounded">
                        <div className="h-4 bg-zinc-800 rounded w-1/3"></div>
                        <div className="h-4 bg-zinc-800 rounded w-16"></div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {alerts.map((event) => (
                      <div
                        key={event.id}
                        onClick={() => handleEventClick(event)}
                        className="flex items-center justify-between p-3 bg-black/40 border border-[#00e5ff]/10 rounded text-xs cursor-pointer hover:border-[#00e5ff]/30 hover:bg-[#00e5ff]/5 transition-all"
                      >
                        <div className="flex items-center gap-3 flex-1">
                          <div className={`w-2 h-2 rounded-full ${event.risk_level?.toLowerCase() === 'high' ? 'bg-red-500 shadow-[0_0_6px_#ef4444]' : 'bg-[#00e5ff] shadow-[0_0_6px_#00e5ff]'}`}></div>
                          <span className="text-[#00e5ff] font-mono">{formatTime(event.timestamp)}</span>
                          <span className="text-zinc-400">{event.event_type}</span>
                        </div>
                        <div className={`px-2 py-0.5 border rounded font-mono text-[10px] uppercase ${getRiskColor(event.risk_level)}`}>
                          {event.risk_level?.toUpperCase() || 'LOW'}
                        </div>
                      </div>
                    ))}
                    {alerts.length === 0 && (
                      <p className="text-zinc-600 text-xs font-mono text-center py-4">// NO RECENT EVENTS</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-black/40 backdrop-blur-md border border-red-500/30 rounded-lg overflow-hidden">
              <div className="p-4 border-b border-red-500/20 flex items-center justify-between bg-red-500/5">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                  <h3 className="text-red-500 font-mono text-xs uppercase tracking-widest">🚨 ACTIVE ALERTS</h3>
                </div>
                <span className="text-red-500 font-mono text-sm font-bold">{activeAlerts.length}</span>
              </div>
              <div className="p-4 space-y-3 max-h-[400px] overflow-y-auto">
                {activeAlerts.length === 0 && (
                  <p className="text-zinc-600 text-xs font-mono text-center py-4">// NO ACTIVE ALERTS</p>
                )}
                {activeAlerts.map((alert) => (
                  <div key={alert.id} className="p-3 bg-black/60 border border-red-500/20 rounded hover:border-red-500/40 transition-all">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_6px_#ef4444] animate-pulse"></div>
                        <AlertTriangle className="w-4 h-4 text-red-500" />
                      </div>
                      <div className={`text-[9px] px-1.5 py-0.5 border rounded font-mono uppercase ${getRiskColor(alert.risk_level)}`}>
                        {alert.risk_level?.toUpperCase()}
                      </div>
                    </div>
                    <div className="text-zinc-300 text-xs font-mono mb-1">{alert.event_type}</div>
                    <div className="flex items-center gap-2 text-[10px] text-zinc-500 font-mono mb-2">
                      <Clock className="w-3 h-3" />
                      {formatTime(alert.timestamp)}
                    </div>
                    <div className="text-[10px] text-zinc-600 mb-3 font-mono">
                      STATUS: <span className="text-[#00e5ff]">{alert.status?.toUpperCase()}</span>
                    </div>
                    <div className="pt-2 border-t border-red-500/20 flex flex-wrap gap-2">
                      <button
                        onClick={() => handleReviewAlert(alert)}
                        className="px-2 py-1 bg-transparent border border-[#00e5ff]/50 text-[#00e5ff] hover:bg-[#00e5ff]/20 rounded font-mono text-[10px] uppercase tracking-wider transition-all flex items-center gap-1"
                      >
                        <Eye className="w-3 h-3" />
                        👁️ REVIEW
                      </button>
                      {alert.status?.toLowerCase() === 'active' && (
                        <button
                          onClick={() => handleAcknowledgeAlert(alert.id)}
                          disabled={actionLoading === alert.id}
                          className="px-2 py-1 bg-transparent border border-yellow-500/50 text-yellow-500 hover:bg-yellow-500/20 rounded font-mono text-[10px] uppercase tracking-wider transition-all flex items-center gap-1 disabled:opacity-50"
                        >
                          <Check className="w-3 h-3" />
                          {actionLoading === alert.id ? '...' : '📋 ACK'}
                        </button>
                      )}
                      <button
                        onClick={() => handleResolveAlert(alert.id)}
                        disabled={actionLoading === alert.id}
                        className="px-2 py-1 bg-transparent border border-[#22c55e]/50 text-[#22c55e] hover:bg-[#22c55e]/20 rounded font-mono text-[10px] uppercase tracking-wider transition-all flex items-center gap-1 disabled:opacity-50"
                      >
                        <Check className="w-3 h-3" />
                        {actionLoading === alert.id ? '...' : '✅ RESOLVE'}
                      </button>
                      <button
                        onClick={() => handleDismissAlert(alert.id)}
                        disabled={actionLoading === alert.id}
                        className="px-2 py-1 bg-transparent border border-zinc-600 text-zinc-400 hover:text-zinc-300 hover:border-zinc-500 rounded font-mono text-[10px] uppercase tracking-wider transition-all flex items-center gap-1 disabled:opacity-50"
                      >
                        <X className="w-3 h-3" />
                        {actionLoading === alert.id ? '...' : '❌'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-black/40 backdrop-blur-md border border-[#00e5ff]/20 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-[#00e5ff]" />
                <h3 className="text-[#00e5ff] font-mono text-xs uppercase tracking-widest">📊 SYSTEM METRICS</h3>
              </div>
              {loading ? (
                <div className="space-y-3">
                  {[1,2,3].map(i => (
                    <div key={i} className="animate-pulse flex justify-between items-center p-3 bg-black/40 border border-[#00e5ff]/10 rounded">
                      <div className="h-4 bg-zinc-800 rounded w-20"></div>
                      <div className="h-4 bg-zinc-800 rounded w-10"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-black/40 border border-[#00e5ff]/20 rounded">
                    <span className="text-[#00e5ff]/60 text-[10px] font-mono uppercase tracking-wider">TOTAL ALERTS</span>
                    <span className="text-[#00e5ff] font-mono text-lg">
                      {stats?.total_alerts ?? '—'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-black/40 border border-yellow-500/20 rounded">
                    <span className="text-yellow-500/60 text-[10px] font-mono uppercase tracking-wider">ACTIVE INCIDENTS</span>
                    <span className="text-yellow-500 font-mono text-lg">
                      {stats?.active_incidents ?? '—'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-black/40 border border-red-500/20 rounded">
                    <span className="text-red-500/60 text-[10px] font-mono uppercase tracking-wider">⚠️ HIGH RISK</span>
                    <span className="text-red-500 font-mono text-lg">
                      {stats?.high_risk_alerts ?? '—'}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
