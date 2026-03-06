"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  AlertTriangle,
  BellOff,
  Check,
  Clock,
  Eye,
  Gauge,
  Play,
  Video,
  Waves,
  X,
} from "lucide-react";
import { acknowledgeAlert, dismissAlert, getAlerts, getStats, resolveAlert, bulkDismissAlerts } from "@/lib/api";

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
  active_tracks: number;
  pipeline_fps: number | null;
  pipeline_running: boolean;
  pipeline_frames: number;
  last_frame_age_s: number | null;
}

// Inlined siren tone to avoid third-party requests blocked by tracking prevention.
const SIREN_URL = "data:audio/ogg;base64,T2dnUwACAAAAAAAAAABY1s4bAAAAACFzEykBHgF2b3JiaXMAAAAAAkSsAAAAAAAAgDgAAAAAAAC4AU9nZ1MAAAAAAAAAAAAAWNfOGwEAAAAhcxMpBToBX29yYmlzAAAAAAJEbAAAAAAAAGAOAAAAAAAAuAFPZ2dTAAAAAAAAAAAAAFjXzhsCAAAAIHMTKQE2AVZvcmJpcwAAAAACRGwAAAAAAABgDgAAAAAAALgBT2dnUwAAAAAAAAAAAAAAYtfOGwMAAACRc5MpATYBX29yYmlzAAAAAAJEbAAAAAAAAGAOAAAAAAAAuAFPZ2dTAAAAAAAAAAAAAFjYzhsEAAAAJ3MTKQEyAVZvcmJpcwAAAAACRGwAAAAAAABgDgAAAAAAALgBT2dnUwAAAAAAAAAAAAAAYuTOGwUAAACecxMpAR4BX29yYmlzAAAAAAJEbAAAAAAAAGAOAAAAAAAAuAFPZ2dTAAAAAAAAAAAAAFjZzhsGAAAAnXMTKQEeAV9vcmJpcwAAAAACRGwAAAAAAABgDgAAAAAAALgBT2dnUwAAAAAAAAAAAAAAYtnOGwcAAACkc5MpAR4BX29yYmlzAAAAAAJEbAAAAAAAAGAOAAAAAAAAuAFPZ2dTAAAAAAAAAAAAAFjczhsIAAAArXMTKQEeAV9vcmJpcwAAAAACRGwAAAAAAABgDgAAAAAAALgBAAAAAQAAAP//AA==";

function MetricBar({
  label,
  value,
  color,
  compact = false,
}: {
  label: string;
  value: string;
  color: string;
  compact?: boolean;
}) {
  return (
    <div className="bg-[#0b0f18] border border-[#00e5ff]/10 rounded px-3 py-2 flex items-center justify-between">
      <span className="text-[11px] uppercase tracking-widest text-zinc-400">{label}</span>
      <span className="text-sm font-semibold" style={{ color }}>
        {value}
      </span>
      {!compact && (
        <div className="ml-3 flex-1 h-1.5 bg-[#050a12] rounded overflow-hidden">
          <div
            className="h-full"
            style={{ width: "70%", background: `linear-gradient(90deg, ${color}, rgba(0,229,255,0.2))` }}
          ></div>
        </div>
      )}
    </div>
  );
}

export default function LiveMonitor() {
  const router = useRouter();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [bannerVisible, setBannerVisible] = useState(true);
  const [alarmMuted, setAlarmMuted] = useState(() => {
    if (typeof window !== "undefined") return localStorage.getItem("alarmMuted") === "true";
    return false;
  });
  const [showAllTimeline, setShowAllTimeline] = useState(false);
  const [bulkDismissing, setBulkDismissing] = useState(false);
  const [replayAlert, setReplayAlert] = useState<Alert | null>(null);
  const [replayFrames, setReplayFrames] = useState<{ id: number; timestamp: string }[]>([]);
  const [streamUrl, setStreamUrl] = useState<string | null>(null);
  const [snapshotUrl, setSnapshotUrl] = useState<string | null>(null);
  const [currentFeed, setCurrentFeed] = useState<string | null>(null);
  const fallbackInterval = useRef<NodeJS.Timeout | null>(null);
  const hasTriedStream = useRef<boolean>(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const activeAlerts = useMemo(
    () => alerts.filter((a) => (a.status || "").toLowerCase() !== "resolved" && (a.status || "").toLowerCase() !== "dismissed"),
    [alerts]
  );

  const highRiskAlert = useMemo(
    () =>
      activeAlerts.find((a) => {
        const lvl = (a.risk_level || "").toLowerCase();
        return lvl === "high" || lvl === "critical";
      }),
    [activeAlerts]
  );

  const riskPercent = useMemo(() => {
    if (!activeAlerts.length) return 12;
    const maxScore = Math.max(...activeAlerts.map((a) => a.risk_score ?? 0));
    return Math.min(100, Math.max(8, Math.round(maxScore * 10)));
  }, [activeAlerts]);

  const riskLabel = riskPercent > 70 ? "Critical" : riskPercent > 45 ? "Elevated" : riskPercent > 20 ? "Guarded" : "Stable";

  const radarBlips = useMemo(() => {
    const palette = ["#ff2d55", "#ffc400", "#1de9b6", "#00e5ff"];
    return activeAlerts.slice(0, 12).map((alert, idx) => ({
      id: alert.id,
      cx: 20 + ((alert.risk_score ?? idx) % 60),
      cy: 15 + ((alert.risk_score ?? idx * 3) % 70),
      color: palette[idx % palette.length],
    }));
  }, [activeAlerts]);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [alertRes, statsRes] = await Promise.all([getAlerts(50), getStats()]);
      const incomingAlerts = Array.isArray(alertRes?.alerts) ? alertRes.alerts : Array.isArray(alertRes) ? alertRes : [];
      setAlerts(incomingAlerts as Alert[]);
      setStats(statsRes as Stats);
    } catch (error) {
      console.error("Failed to load dashboard data", error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 15000);
    return () => clearInterval(interval);
  }, [fetchData]);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const streamBase = process.env.NEXT_PUBLIC_VIDEO_FEED_URL || "http://localhost:5000/api/video_feed";
    const snapBase = process.env.NEXT_PUBLIC_VIDEO_FRAME_URL || "http://localhost:5000/api/frame";
    const stream = token ? `${streamBase}?token=${encodeURIComponent(token)}` : streamBase;
    const snap = token ? `${snapBase}?token=${encodeURIComponent(token)}` : snapBase;
    setStreamUrl(stream);
    setSnapshotUrl(snap);
    setCurrentFeed(stream);
  }, []);

  const startSnapshotFallback = useCallback(() => {
    if (!snapshotUrl) return;
    if (fallbackInterval.current) return;
    const tick = () => setCurrentFeed(`${snapshotUrl}${snapshotUrl.includes("?") ? "&" : "?"}ts=${Date.now()}`);
    tick();
    fallbackInterval.current = setInterval(tick, 1500);
  }, [snapshotUrl]);

  const stopSnapshotFallback = useCallback(() => {
    if (fallbackInterval.current) {
      clearInterval(fallbackInterval.current);
      fallbackInterval.current = null;
    }
  }, []);

  useEffect(() => {
    if (!highRiskAlert || alarmMuted) return;
    if (!audioRef.current) {
      audioRef.current = new Audio(SIREN_URL);
      audioRef.current.loop = true;
    }
    audioRef.current.play().catch(() => undefined);
    return () => {
      audioRef.current?.pause();
    };
  }, [highRiskAlert, alarmMuted]);

  const formatTime = (timestamp: string) => {
    const dt = new Date(timestamp);
    return dt.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
      timeZone: "Asia/Kolkata",
    });
  };

  const getRiskColor = (risk?: string) => {
    const level = (risk || "").toLowerCase();
    if (level === "high" || level === "critical") return "border-red-500/50 text-red-400";
    if (level === "medium") return "border-yellow-400/50 text-yellow-300";
    return "border-[#1de9b6]/40 text-[#1de9b6]";
  };

  const handleReviewAlert = (alert: Alert) => {
    setReplayAlert(alert);
    const now = Date.now();
    const frames = Array.from({ length: 6 }, (_, idx) => ({
      id: idx,
      timestamp: new Date(now - (5 - idx) * 1500).toLocaleTimeString(),
    }));
    setReplayFrames(frames);
  };

  const handleEventClick = (alert: Alert) => handleReviewAlert(alert);

  const updateAlertStatus = (id: number, status: string) => {
    setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, status } : a)));
  };

  const handleAcknowledgeAlert = async (id: number) => {
    setActionLoading(id);
    try {
      await acknowledgeAlert(id);
      updateAlertStatus(id, "acknowledged");
    } catch (error) {
      console.error("Ack failed", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResolveAlert = async (id: number) => {
    setActionLoading(id);
    try {
      await resolveAlert(id);
      updateAlertStatus(id, "resolved");
    } catch (error) {
      console.error("Resolve failed", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDismissAlert = async (id: number) => {
    setActionLoading(id);
    try {
      await dismissAlert(id);
      updateAlertStatus(id, "dismissed");
    } catch (error) {
      console.error("Dismiss failed", error);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDismissBannerAlert = async () => {
    if (!highRiskAlert) return;
    await handleDismissAlert(highRiskAlert.id);
    setBannerVisible(false);
  };

  const handleBannerDismiss = () => setBannerVisible(false);

  const toggleAlarmMuted = () => {
    setAlarmMuted((prev) => {
      const next = !prev;
      if (typeof window !== "undefined") localStorage.setItem("alarmMuted", String(next));
      return next;
    });
  };

  const handleBulkDismiss = async () => {
    setBulkDismissing(true);
    try {
      await bulkDismissAlerts();
      await fetchData();
    } catch (err) {
      console.error("Bulk dismiss failed", err);
    } finally {
      setBulkDismissing(false);
    }
  };

  const TIMELINE_LIMIT = 10;
  const visibleTimelineAlerts = showAllTimeline ? alerts : alerts.slice(0, TIMELINE_LIMIT);
  const hasMoreAlerts = alerts.length > TIMELINE_LIMIT;

  return (
    <div className="space-y-6 text-zinc-200">
      {highRiskAlert && bannerVisible && (
        <div className="relative overflow-hidden rounded-lg border border-red-500/40 bg-[#12060c] shadow-[0_0_24px_rgba(255,45,85,0.18)]">
          <div className="absolute inset-0 opacity-30" style={{ background: "repeating-linear-gradient(90deg, transparent, transparent 12px, rgba(255,45,85,0.15) 12px, rgba(255,45,85,0.15) 18px)" }}></div>
          <div className="p-4 flex flex-wrap items-center gap-3 relative z-10">
            <div className="flex items-center gap-2 text-red-400">
              <AlertTriangle className="w-4 h-4" />
              <span className="font-mono text-xs uppercase tracking-widest">Critical Alert</span>
            </div>
            <div className="text-sm text-zinc-200 flex-1">
              {highRiskAlert.event_type} @ {highRiskAlert.location || "Unknown"} • {formatTime(highRiskAlert.timestamp)}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={toggleAlarmMuted}
                className="px-3 py-1.5 bg-red-500/10 border border-red-400/40 text-red-200 hover:bg-red-500/20 rounded font-mono text-[11px] uppercase tracking-wider transition-all"
              >
                <BellOff className="w-3 h-3" /> {alarmMuted ? "Unmute" : "Mute Alarm"}
              </button>
              <button
                onClick={handleDismissBannerAlert}
                disabled={actionLoading === highRiskAlert.id}
                className="px-3 py-1.5 bg-transparent border border-red-500/50 text-red-400 hover:bg-red-500/20 hover:shadow-[0_0_15px_rgba(239,68,68,0.3)] rounded font-mono text-[11px] uppercase tracking-wider transition-all disabled:opacity-50"
              >
                {actionLoading === highRiskAlert.id ? "..." : "Dismiss"}
              </button>
              <button
                onClick={handleBannerDismiss}
                className="px-2 py-1.5 text-zinc-500 hover:text-zinc-300 font-mono text-xs transition-all"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-4">
          <div className="bg-[#071018]/90 border border-[#00e5ff]/25 rounded-lg overflow-hidden shadow-[0_0_28px_rgba(0,229,255,0.12)]">
            <div className="p-4 border-b border-[#00e5ff]/20 flex items-center justify-between bg-gradient-to-r from-[#071018] via-[#0a1623] to-[#071018]">
              <div className="flex items-center gap-3">
                <Video className="w-4 h-4 text-[#00e5ff]" />
                <span className="text-[#00e5ff] text-sm uppercase tracking-[0.25em]">[ Camera Feed ]</span>
              </div>
              <div className="flex items-center gap-2 text-[11px] text-red-400">
                <div className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_#ff2d55] animate-pulse"></div>
                <span className="border border-red-400/50 px-2 py-0.5 rounded uppercase tracking-widest">Live</span>
              </div>
            </div>

            <div className="relative aspect-video bg-[#050a12]">
              <div
                className="absolute inset-0 pointer-events-none z-10 opacity-25"
                style={{ background: "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,229,255,0.04) 3px, rgba(0,229,255,0.04) 6px)" }}
              ></div>

              {currentFeed ? (
                <img
                  src={currentFeed}
                  alt="Live Camera Feed"
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    if (!hasTriedStream.current && streamUrl) {
                      hasTriedStream.current = true;
                      setCurrentFeed(streamUrl);
                      return;
                    }
                    startSnapshotFallback();
                  }}
                  onLoad={() => {
                    if (currentFeed === streamUrl) {
                      stopSnapshotFallback();
                    }
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-[#00e5ff] text-sm">Loading video feed...</div>
              )}

              <div className="absolute top-3 left-3 bg-[#071018]/85 border border-[#00e5ff]/40 px-3 py-1 rounded text-[11px] text-[#1de9b6] tracking-widest uppercase">
                CAM-01 • Main Entrance
              </div>
              <div className="absolute top-3 right-3 bg-[#071018]/85 border border-red-400/40 px-2 py-1 rounded text-[11px] text-red-400 tracking-widest flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_#ff2d55] animate-pulse"></span>
                Live
              </div>
              <div className="absolute bottom-3 left-3 right-3">
                <div className="bg-[#071018]/85 border border-[#00e5ff]/30 p-3 rounded">
                  <div className="flex items-center justify-between">
                    <div className="text-[#00e5ff] text-sm uppercase tracking-widest">Resolution 1920x1080 • 30fps</div>
                    <div className="flex items-center gap-2 text-[11px] text-[#1de9b6]">
                      <span className="w-2 h-2 rounded-full bg-[#1de9b6] shadow-[0_0_8px_#1de9b6] animate-pulse"></span>
                      Detecting
                    </div>
                  </div>
                </div>
              </div>

              <div
                className="absolute inset-0 pointer-events-none"
                style={{ background: "radial-gradient(circle at 20% 20%, rgba(0,229,255,0.08), transparent 35%), radial-gradient(circle at 80% 30%, rgba(29,233,182,0.06), transparent 40%)" }}
              ></div>
            </div>

            <div className="border-t border-[#00e5ff]/20 p-4 bg-[#050a12]">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="w-4 h-4 text-[#00e5ff]" />
                <h3 className="text-[#00e5ff] text-xs uppercase tracking-[0.25em]">[ Threat Timeline ]</h3>
              </div>
              {loading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="animate-pulse flex items-center justify-between p-3 bg-[#071018] border border-[#00e5ff]/10 rounded">
                      <div className="h-4 bg-zinc-800 rounded w-1/3"></div>
                      <div className="h-4 bg-zinc-800 rounded w-16"></div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-2">
                  {visibleTimelineAlerts.map((event) => (
                    <div
                      key={event.id}
                      onClick={() => handleEventClick(event)}
                      className="flex items-center justify-between p-3 bg-[#071018] border border-[#00e5ff]/10 rounded text-xs cursor-pointer hover:border-[#00e5ff]/30 hover:bg-[#00e5ff]/5 transition-all"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <div
                          className={`w-2 h-2 rounded-full ${event.risk_level?.toLowerCase() === "high"
                            ? "bg-[#ff2d55] shadow-[0_0_6px_#ff2d55]"
                            : event.risk_level?.toLowerCase() === "medium"
                              ? "bg-[#ffc400] shadow-[0_0_6px_#ffc400]"
                              : "bg-[#1de9b6] shadow-[0_0_6px_#1de9b6]"
                            }`}
                        ></div>
                        <span className="text-[#00e5ff]">{formatTime(event.timestamp)}</span>
                        <span className="text-zinc-400">{event.event_type}</span>
                      </div>
                      <div className={`px-2 py-0.5 border rounded text-[10px] uppercase ${getRiskColor(event.risk_level)}`}>
                        {event.risk_level?.toUpperCase() || "LOW"}
                      </div>
                    </div>
                  ))}
                  {alerts.length === 0 && <p className="text-zinc-600 text-xs text-center py-4">// No recent events</p>}
                  {hasMoreAlerts && (
                    <button
                      onClick={() => setShowAllTimeline((s) => !s)}
                      className="w-full py-2 text-center text-[11px] font-mono text-[#00e5ff]/70 hover:text-[#00e5ff] border border-[#00e5ff]/15 hover:border-[#00e5ff]/30 rounded bg-[#071018] hover:bg-[#00e5ff]/5 transition-all uppercase tracking-wider"
                    >
                      {showAllTimeline ? `▲ Show Less` : `▼ Show All (${alerts.length})`}
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-[#071018]/90 border border-[#ff2d55]/30 rounded-lg overflow-hidden shadow-[0_0_24px_rgba(255,45,85,0.18)]">
            <div className="p-4 border-b border-[#ff2d55]/30 flex items-center justify-between bg-[#12060c]">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-[#ff2d55]" />
                <h3 className="text-[#ff2d55] text-xs uppercase tracking-[0.25em]">[ Alert Stack ]</h3>
              </div>
              <span className="text-[#ff2d55] text-sm font-bold">{activeAlerts.length}</span>
            </div>
            {/* Clear Resolved button */}
            <div className="px-4 pt-3 pb-1 border-b border-[#ff2d55]/15">
              <button
                onClick={handleBulkDismiss}
                disabled={bulkDismissing || activeAlerts.length === 0}
                className="w-full py-1.5 text-center text-[10px] font-mono uppercase tracking-wider border border-zinc-700 text-zinc-400 hover:text-red-400 hover:border-red-500/40 hover:bg-red-500/10 rounded transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {bulkDismissing ? "Clearing..." : "⊘ Clear All Alerts"}
              </button>
            </div>
            <div className="p-4 space-y-3 max-h-[420px] overflow-y-auto">
              {activeAlerts.length === 0 && <p className="text-zinc-600 text-xs text-center py-4">// No active alerts</p>}
              {activeAlerts.map((alert) => {
                const risk = (alert.risk_level || "").toLowerCase();
                const pulse = risk === "high" || risk === "critical" ? "animate-pulse" : "";
                return (
                  <div
                    key={alert.id}
                    className={`p-3 bg-[#0b0f18] border ${risk === "high" || risk === "critical"
                      ? "border-[#ff2d55]/50 shadow-[0_0_14px_rgba(255,45,85,0.22)]"
                      : "border-[#00e5ff]/20"
                      } rounded transition-all`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-2 h-2 rounded-full ${pulse} ${risk === "high" || risk === "critical"
                            ? "bg-[#ff2d55]"
                            : risk === "medium"
                              ? "bg-[#ffc400]"
                              : "bg-[#1de9b6]"
                            }`}
                        ></div>
                        <div className="text-[10px] text-zinc-400 uppercase tracking-widest">{alert.camera_id || "CAM-01"}</div>
                      </div>
                      <div className={`text-[10px] px-2 py-0.5 border rounded uppercase ${getRiskColor(alert.risk_level)}`}>
                        {alert.risk_level?.toUpperCase()}
                      </div>
                    </div>
                    <div className="text-[#00e5ff] text-sm font-semibold mb-1">{alert.event_type}</div>
                    <div className="text-[11px] text-zinc-400 mb-2">
                      Confidence: {(alert.risk_score ?? 0).toFixed(2)} • Camera: {alert.camera_id || "CAM-01"} • {formatTime(alert.timestamp)}
                    </div>
                    <div className="pt-2 border-t border-[#00e5ff]/10 flex flex-wrap gap-2">
                      <button
                        onClick={() => handleReviewAlert(alert)}
                        className="px-2 py-1 bg-[#00e5ff]/10 border border-[#00e5ff]/40 text-[#00e5ff] hover:bg-[#00e5ff]/20 rounded text-[10px] uppercase tracking-wider transition-all"
                      >
                        Review
                      </button>
                      {alert.status?.toLowerCase() === "active" && (
                        <button
                          onClick={() => handleAcknowledgeAlert(alert.id)}
                          disabled={actionLoading === alert.id}
                          className="px-2 py-1 bg-[#ffc400]/10 border border-[#ffc400]/40 text-[#ffc400] hover:bg-[#ffc400]/20 rounded text-[10px] uppercase tracking-wider transition-all disabled:opacity-50"
                        >
                          {actionLoading === alert.id ? "..." : "Ack"}
                        </button>
                      )}
                      <button
                        onClick={() => handleResolveAlert(alert.id)}
                        disabled={actionLoading === alert.id}
                        className="px-2 py-1 bg-[#1de9b6]/10 border border-[#1de9b6]/40 text-[#1de9b6] hover:bg-[#1de9b6]/20 rounded text-[10px] uppercase tracking-wider transition-all disabled:opacity-50"
                      >
                        {actionLoading === alert.id ? "..." : "Resolve"}
                      </button>
                      <button
                        onClick={() => handleDismissAlert(alert.id)}
                        disabled={actionLoading === alert.id}
                        className="px-2 py-1 bg-zinc-800 border border-zinc-600 text-zinc-300 hover:border-zinc-400 rounded text-[10px] uppercase tracking-wider transition-all disabled:opacity-50"
                      >
                        {actionLoading === alert.id ? "..." : "Dismiss"}
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="bg-[#071018]/90 border border-[#00e5ff]/25 rounded-lg p-4 space-y-4 shadow-[0_0_18px_rgba(0,229,255,0.12)]">
            <div className="flex items-center justify-between">
              <h3 className="text-[#00e5ff] text-xs uppercase tracking-[0.25em]">[ Threat Radar ]</h3>
              <span className="text-[11px] text-zinc-500">blips = detections</span>
            </div>
            <div className="relative w-full aspect-square bg-gradient-to-br from-[#050a12] to-[#0a1623] border border-[#00e5ff]/20 rounded-full overflow-hidden">
              <svg viewBox="0 0 100 100" className="absolute inset-0">
                <circle cx="50" cy="50" r="48" stroke="#00e5ff22" strokeWidth="0.6" fill="none" />
                <circle cx="50" cy="50" r="32" stroke="#00e5ff18" strokeWidth="0.6" fill="none" />
                <circle cx="50" cy="50" r="16" stroke="#00e5ff12" strokeWidth="0.6" fill="none" />
                <line x1="50" y1="0" x2="50" y2="100" stroke="#00e5ff15" strokeWidth="0.4" />
                <line x1="0" y1="50" x2="100" y2="50" stroke="#00e5ff15" strokeWidth="0.4" />
                {radarBlips.map((b) => (
                  <circle key={b.id} cx={b.cx} cy={b.cy} r="2" fill={b.color} opacity="0.9" />
                ))}
              </svg>
              <div className="absolute inset-0 animate-spin-slow" style={{ background: "conic-gradient(from 90deg, transparent 60%, rgba(0,229,255,0.25) 100%)" }}></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-3 h-3 rounded-full bg-[#00e5ff] shadow-[0_0_12px_rgba(0,229,255,0.6)]"></div>
              </div>
            </div>
          </div>

          <div className="bg-[#071018]/90 border border-[#00e5ff]/25 rounded-lg p-4 shadow-[0_0_18px_rgba(0,229,255,0.12)]">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-[#00e5ff] text-xs uppercase tracking-[0.25em]">[ Threat Risk ]</h3>
              <span className="text-[11px] text-zinc-400">{riskLabel}</span>
            </div>
            <div className="flex items-center gap-4">
              <div className="h-36 w-10 bg-[#050a12] border border-[#00e5ff]/25 rounded relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-t from-[#ff2d55]/70 via-[#ffc400]/60 to-[#1de9b6]/50 opacity-70"></div>
                <div className="absolute bottom-0 left-0 right-0" style={{ height: `${riskPercent}%`, background: "linear-gradient(180deg, #ff2d55, #ffc400)" }}></div>
              </div>
              <div>
                <div className="text-3xl font-bold text-[#00e5ff]">{riskPercent}%</div>
                <div className="text-[11px] text-zinc-400">Threat Level</div>
              </div>
            </div>
          </div>

          <div className="bg-[#071018]/90 border border-[#00e5ff]/25 rounded-lg p-4 space-y-3 shadow-[0_0_18px_rgba(0,229,255,0.12)]">
            <div className="flex items-center gap-2">
              <Gauge className="w-4 h-4 text-[#00e5ff]" />
              <h3 className="text-[#00e5ff] text-xs uppercase tracking-[0.25em]">[ System Telemetry ]</h3>
            </div>
            <div className="space-y-2 text-sm text-zinc-300">
              <MetricBar label="Pipeline FPS" value={stats?.pipeline_fps != null ? `${stats.pipeline_fps} fps` : "—"} color="#1de9b6" />
              <MetricBar label="Frame Latency" value={stats?.last_frame_age_s != null ? `${stats.last_frame_age_s}s ago` : "—"} color="#ffc400" />
              <MetricBar label="Active Tracks" value={`${stats?.active_tracks ?? activeAlerts.length}`} color="#00e5ff" />
              <MetricBar label="Pipeline" value={stats?.pipeline_running ? "Running" : "Offline"} color={stats?.pipeline_running ? "#1de9b6" : "#ff2d55"} compact />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <div className="bg-[#0b0f18]/90 border border-[#00e5ff]/20 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Waves className="w-4 h-4 text-[#00e5ff]" />
              <h3 className="text-[#00e5ff] text-xs uppercase tracking-[0.25em]">[ Operations Board ]</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="bg-[#050a12] border border-[#00e5ff]/15 rounded p-3 flex items-center justify-between">
                <span className="text-[11px] uppercase tracking-widest text-zinc-400">Total Alerts</span>
                <span className="text-[#00e5ff] text-lg font-semibold">{stats?.total_alerts ?? "—"}</span>
              </div>
              <div className="bg-[#050a12] border border-[#ffc400]/25 rounded p-3 flex items-center justify-between">
                <span className="text-[11px] uppercase tracking-widest text-zinc-400">Active Incidents</span>
                <span className="text-[#ffc400] text-lg font-semibold">{stats?.active_incidents ?? "—"}</span>
              </div>
              <div className="bg-[#050a12] border border-[#ff2d55]/25 rounded p-3 flex items-center justify-between">
                <span className="text-[11px] uppercase tracking-widest text-zinc-400">High Risk</span>
                <span className="text-[#ff2d55] text-lg font-semibold">{stats?.high_risk_alerts ?? "—"}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-[#0b0f18]/90 border border-[#00e5ff]/20 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[#00e5ff] text-xs uppercase tracking-[0.25em]">[ Quick Actions ]</h3>
            <button
              onClick={() => router.refresh()}
              className="text-[11px] text-[#1de9b6] border border-[#1de9b6]/40 px-2 py-1 rounded uppercase tracking-wider hover:bg-[#1de9b6]/10"
            >
              Refresh
            </button>
          </div>
          <div className="space-y-2 text-sm text-zinc-300">
            <div className="flex items-center justify-between bg-[#050a12] border border-[#00e5ff]/15 rounded px-3 py-2">
              <span className="text-[11px] uppercase tracking-widest text-zinc-400">Pipeline</span>
              <span className={`text-xs ${stats?.pipeline_running ? 'text-[#1de9b6]' : 'text-[#ff2d55]'}`}>{stats?.pipeline_running ? 'Active' : 'Offline'}</span>
            </div>
            <div className="flex items-center justify-between bg-[#050a12] border border-[#ffc400]/15 rounded px-3 py-2">
              <span className="text-[11px] uppercase tracking-widest text-zinc-400">Total Frames</span>
              <span className="text-[#ffc400] text-xs">{stats?.pipeline_frames?.toLocaleString() ?? '—'}</span>
            </div>
            <div className="flex items-center justify-between bg-[#050a12] border border-[#1de9b6]/15 rounded px-3 py-2">
              <span className="text-[11px] uppercase tracking-widest text-zinc-400">High Risk</span>
              <span className="text-[#ff2d55] text-xs">{stats?.high_risk_alerts ?? '—'}</span>
            </div>
          </div>
        </div>
      </div>

      {replayAlert && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-[#0a0a0c] border border-[#00e5ff]/30 rounded-xl w-full max-w-5xl shadow-[0_0_30px_rgba(0,229,255,0.15)] relative">
            <div className="flex items-center justify-between px-6 py-4 border-b border-[#00e5ff]/20">
              <div>
                <p className="text-[#00e5ff] font-mono text-xs uppercase tracking-widest">Incident Replay</p>
                <p className="text-zinc-400 text-sm font-mono">
                  {replayAlert.event_type} @ {replayAlert.location || "Unknown"}
                </p>
              </div>
              <button onClick={() => setReplayAlert(null)} className="text-zinc-400 hover:text-white font-mono text-sm">
                Close ✕
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-6">
              <div className="lg:col-span-2 bg-black/60 border border-[#00e5ff]/20 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Play className="w-4 h-4 text-[#00e5ff]" />
                  <p className="text-[#00e5ff] font-mono text-xs uppercase tracking-widest">Replay Sequence (last 10s)</p>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {replayFrames.map((frame) => (
                    <div key={frame.id} className="border border-[#00e5ff]/20 rounded bg-black/50 p-2">
                      <div className="relative aspect-video bg-[#0f172a] overflow-hidden">
                        {streamUrl ? (
                          <img src={streamUrl} alt="Replay frame" className="w-full h-full object-contain" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-zinc-600 font-mono text-xs">Frame</div>
                        )}
                        <div className="absolute bottom-1 left-1 px-2 py-0.5 bg-black/70 border border-[#00e5ff]/30 rounded text-[10px] font-mono text-[#00e5ff]">{frame.timestamp}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-black/60 border border-[#00e5ff]/20 rounded-lg p-4 space-y-3">
                <p className="text-[#00e5ff] font-mono text-xs uppercase tracking-widest">Details</p>
                <div className="text-zinc-300 text-sm font-mono space-y-1">
                  <p>Person ID: {replayAlert.person_id || "N/A"}</p>
                  <p>Camera: {replayAlert.camera_id || "CAM-01"}</p>
                  <p>Risk: {replayAlert.risk_level?.toUpperCase()}</p>
                  <p>Timestamp: {formatTime(replayAlert.timestamp)}</p>
                </div>
                <div className="space-y-2 text-zinc-400 text-xs font-mono">
                  <p>// Playback uses recent frame buffer. Full forensic export available in archives.</p>
                  <p>// Bounding boxes overlay pending data feed.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
