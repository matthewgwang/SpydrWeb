import { useState, useCallback } from "react";
import { Outlet, NavLink } from "react-router-dom";
import { Activity, ChevronDown, Play, LayoutDashboard, BarChart3, GitBranch, Settings } from "lucide-react";
import DemoControls from "../DemoControls/DemoControls";
import { useTransactionFeed } from "../../hooks/useTransactionFeed";
import type { CaseReport } from "../../types";
import { startDemo, pauseDemo, injectFraud, setMode } from "../../services/api";

export default function AppShell() {
  const { transactions, alerts, alertFlash, recentAlertTxIds } = useTransactionFeed();
  const [mode, setModeState] = useState<"pipeline" | "agentic">("pipeline");
  const [showDemo, setShowDemo] = useState(false);

  const handleModeChange = useCallback(async (m: "pipeline" | "agentic") => {
    setModeState(m);
    try { await setMode(m); } catch {}
  }, []);

  const handleDemoStart = useCallback(async () => {
    try { await startDemo(); } catch {}
  }, []);

  const handleDemoPause = useCallback(async () => {
    try { await pauseDemo(); } catch {}
  }, []);

  const handleInjectFraud = useCallback(
    async (scenario: string): Promise<CaseReport | null> => {
      try { return await injectFraud(scenario); } catch { return null; }
    },
    [],
  );

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium transition ${
      isActive
        ? "bg-s-accent text-white"
        : "text-s-muted hover:bg-s-surface"
    }`;

  return (
    <div className="flex flex-col h-screen bg-s-bg">
      {/* Top Bar */}
      <div className="shrink-0">
        <div className="flex items-center h-9 px-3 bg-s-panel border-b border-s-border">
          {/* Logo */}
          <div className="flex items-center gap-2.5 mr-3">
            <Activity size={14} className="text-s-accent" />
            <span className="text-[13px] font-semibold tracking-wide text-s-text">
              SPYDRWEB
            </span>
            <button className="flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] text-s-muted border border-s-border hover:bg-s-surface transition">
              Workspace
              <ChevronDown size={10} />
            </button>
          </div>

          <div className="h-4 w-px bg-s-border mx-1.5" />

          {/* Page Nav */}
          <nav className="flex items-center gap-1 mr-4">
            <NavLink to="/" className={navLinkClass} end>
              <LayoutDashboard size={10} />
              Monitor
            </NavLink>
            <NavLink to="/analytics" className={navLinkClass}>
              <BarChart3 size={10} />
              Analytics
            </NavLink>
            <NavLink to="/graph" className={navLinkClass}>
              <GitBranch size={10} />
              Graph
            </NavLink>
            <NavLink to="/config" className={navLinkClass}>
              <Settings size={10} />
              Config
            </NavLink>
          </nav>

          <div className="h-4 w-px bg-s-border mx-1.5" />

          {/* Stats */}
          <div className="flex items-center gap-5 flex-1 text-[11px]">
            <div>
              <span className="text-s-text-tertiary mr-1">Events</span>
              <span className="font-mono font-medium text-s-text-secondary">
                {transactions.length}
              </span>
            </div>
            <div>
              <span className="text-s-text-tertiary mr-1">Alerts</span>
              <span className="font-mono font-medium text-s-text-secondary">
                {alerts.length}
              </span>
            </div>
          </div>

          {/* Mode Toggle */}
          <div className="flex items-center gap-1.5 mr-3">
            <span className="text-[10px] text-s-text-tertiary">Mode</span>
            <div className="flex rounded border border-s-border overflow-hidden">
              <button
                onClick={() => handleModeChange("pipeline")}
                className={`px-2 py-0.5 text-[10px] font-medium transition ${
                  mode === "pipeline"
                    ? "bg-s-accent text-white"
                    : "bg-s-panel text-s-muted hover:bg-s-surface"
                }`}
              >
                Pipeline
              </button>
              <button
                onClick={() => handleModeChange("agentic")}
                className={`px-2 py-0.5 text-[10px] font-medium transition ${
                  mode === "agentic"
                    ? "bg-s-purple text-white"
                    : "bg-s-panel text-s-muted hover:bg-s-surface"
                }`}
              >
                Agent
              </button>
            </div>
          </div>

          <div className="h-4 w-px bg-s-border mx-1" />

          <button
            onClick={() => setShowDemo(!showDemo)}
            className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium transition ${
              showDemo
                ? "bg-s-accent text-white"
                : "text-s-muted border border-s-border hover:bg-s-surface"
            }`}
          >
            <Play size={9} />
            Demo
          </button>
        </div>

        {showDemo && (
          <DemoControls
            onStart={handleDemoStart}
            onPause={handleDemoPause}
            onInject={handleInjectFraud}
            onClose={() => setShowDemo(false)}
          />
        )}
      </div>

      {/* Page Content */}
      <div className="flex-1 overflow-hidden">
        <Outlet context={{ transactions, alerts, mode, recentAlertTxIds }} />
      </div>

      {alertFlash && (
        <div className="fixed inset-0 pointer-events-none z-50 animate-alert-vignette" />
      )}
    </div>
  );
}
