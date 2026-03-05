"use client";

import { useState, useEffect } from 'react';
import { AlertTriangle, Clock } from 'lucide-react';
import { getAlerts, getStats } from '@/lib/api';

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
  switch (risk) {
    case 'high':
      return 'bg-red-900/30 text-red-400 border-red-800/50';
    case 'medium':
      return 'bg-yellow-900/30 text-yellow-400 border-yellow-800/50';
    case 'low':
      return 'bg-zinc-800 text-zinc-400 border-zinc-700';
    default:
      return 'bg-zinc-800 text-zinc-400 border-zinc-700';
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
  const [alertBanner, setAlertBanner] = useState(true);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [alertsData, statsData] = await Promise.all([
        getAlerts(10),
        getStats(),
      ]);
      setAlerts(Array.isArray(alertsData) ? alertsData : []);
      setStats(statsData);
    } catch {
      console.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    // Poll every 5 seconds for real-time updates
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const activeAlerts = alerts.filter(
    (a) => a.status === 'Active' || a.status === 'Under Review'
  );

  return (
    <div className="flex-1 bg-black overflow-auto">
      <div className="p-6">
        {alertBanner && activeAlerts.length > 0 && (
          <div className="mb-4 bg-red-950/40 border border-red-900/50 p-3">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="text-red-400 font-medium text-sm">
                  Alert: {activeAlerts[0]?.event_type}
                </h3>
                <p className="text-xs text-red-400/70 mt-0.5">
                  Detection at {activeAlerts[0]?.location} - Review recommended
                </p>
              </div>
              <button
                onClick={() => setAlertBanner(false)}
                className="text-red-500 hover:text-red-400 text-xs px-2 py-1 border border-red-900/50 hover:border-red-800"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-3">
            <div className="bg-zinc-950 border border-zinc-800">
              <div className="relative aspect-video bg-black">
                <img
                  src="https://images.unsplash.com/photo-1760866613530-e3e09e013c42?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxidWlsZGluZyUyMGVudHJhbmNlJTIwc2VjdXJpdHl8ZW58MXx8fHwxNzcyNjE4OTIxfDA&ixlib=rb-4.1.0&q=80&w=1080"
                  alt="Live Camera Feed"
                  className="w-full h-full object-cover"
                />

                <div className="absolute inset-0 pointer-events-none">
                  <svg className="w-full h-full">
                    <rect x="28%" y="30%" width="18%" height="40%" fill="none" stroke="#dc2626" strokeWidth="1.5" />
                    <rect x="28%" y="28%" width="100" height="16" fill="#000000" fillOpacity="0.8" />
                    <text x="28.5%" y="29.5%" fill="#dc2626" fontSize="11" fontFamily="monospace">
                      ID: {alerts[0]?.person_id || 'P-001'}
                    </text>
                    <rect x="28%" y="71%" width="100" height="16" fill="#000000" fillOpacity="0.8" />
                    <text x="28.5%" y="72.5%" fill="#dc2626" fontSize="11" fontFamily="monospace">
                      RISK: {alerts[0]?.risk_score ? Math.round(alerts[0].risk_score * 100) + '%' : '—'}
                    </text>
                  </svg>
                </div>

                <div className="absolute top-3 left-3">
                  <div className="flex items-center gap-2 bg-red-900/80 px-2 py-1 text-xs font-mono text-white border border-red-800">
                    <div className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
                    LIVE
                  </div>
                </div>

                <div className="absolute top-3 right-3 bg-black/80 px-2 py-1 text-xs text-zinc-300 font-mono border border-zinc-800">
                  {new Date().toLocaleTimeString()}
                </div>

                <div className="absolute bottom-3 left-3 right-3">
                  <div className="bg-black/80 border border-zinc-800 p-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-white text-sm font-mono">CAM-01 Main Entrance</div>
                        <div className="text-zinc-400 text-xs font-mono">1920x1080 • 30fps</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="text-xs font-mono text-green-500 border border-green-900/50 bg-green-950/30 px-2 py-0.5">
                          DETECTING
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="border-t border-zinc-800 p-4">
                <h3 className="text-white text-sm font-medium mb-3">Recent Detection Events</h3>
                {loading ? (
                  <p className="text-zinc-500 text-xs font-mono">Loading...</p>
                ) : (
                  <div className="space-y-2">
                    {alerts.map((event) => (
                      <div
                        key={event.id}
                        className="flex items-center justify-between p-2 bg-zinc-950 border border-zinc-800 text-xs"
                      >
                        <div className="flex items-center gap-3 flex-1">
                          <span className="text-white font-mono">{formatTime(event.timestamp)}</span>
                          <span className="text-zinc-400">{event.event_type}</span>
                        </div>
                        <div className={`px-2 py-0.5 border font-mono ${getRiskColor(event.risk_level)}`}>
                          {event.risk_level?.toUpperCase() || 'LOW'}
                        </div>
                      </div>
                    ))}
                    {alerts.length === 0 && (
                      <p className="text-zinc-600 text-xs font-mono text-center py-2">No recent events</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div className="bg-zinc-950 border border-zinc-800 p-4">
              <h3 className="text-white text-sm font-medium mb-3">Active Alerts</h3>
              <div className="space-y-2">
                {activeAlerts.length === 0 && (
                  <p className="text-zinc-600 text-xs font-mono text-center py-2">No active alerts</p>
                )}
                {activeAlerts.map((alert) => (
                  <div key={alert.id} className="p-3 bg-black border border-zinc-800">
                    <div className="flex items-start justify-between mb-2">
                      <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0" />
                      <div className={`text-xs px-1.5 py-0.5 border font-mono ${getRiskColor(alert.risk_level)}`}>
                        {alert.risk_level?.toUpperCase()}
                      </div>
                    </div>
                    <div className="text-white text-xs font-medium mb-1">{alert.event_type}</div>
                    <div className="flex items-center gap-2 text-xs text-zinc-500 font-mono">
                      <Clock className="w-3 h-3" />
                      {formatTime(alert.timestamp)}
                    </div>
                    <div className="mt-2 pt-2 border-t border-zinc-800">
                      <button className="text-xs text-red-400 hover:text-red-300 font-mono">
                        REVIEW →
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-zinc-950 border border-zinc-800 p-4">
              <h3 className="text-white text-sm font-medium mb-3">System Stats</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-zinc-400 font-mono">Total Alerts</span>
                  <span className="text-white font-mono border border-zinc-700 bg-zinc-800 px-2 py-0.5">
                    {stats?.total_alerts ?? '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-zinc-400 font-mono">Active Incidents</span>
                  <span className="text-white font-mono border border-zinc-700 bg-zinc-800 px-2 py-0.5">
                    {stats?.active_incidents ?? '—'}
                  </span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-zinc-400 font-mono">High Risk</span>
                  <span className="text-red-400 font-mono border border-red-900/50 bg-red-950/30 px-2 py-0.5">
                    {stats?.high_risk_alerts ?? '—'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
