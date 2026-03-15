import { useState } from "react";
import { Play, ChevronDown, Activity } from "lucide-react";
import DemoControls from "../DemoControls/DemoControls";
import type { CaseReport } from "../../types";

interface Props {
  eventCount: number;
  alertCount: number;
  alertQueueSize: number;
  mode: "pipeline" | "agentic";
  onModeChange: (mode: "pipeline" | "agentic") => void;
  onDemoStart: () => void;
  onInjectFraud: (scenario: string) => Promise<CaseReport | null>;
}

export default function TopBar({
  eventCount,
  alertCount,
  alertQueueSize,
  mode,
  onModeChange,
  onDemoStart,
  onInjectFraud,
}: Props) {
  const [showDemoPanel, setShowDemoPanel] = useState(false);

  return (
    <div className="shrink-0">
      <div className="flex items-center h-9 px-3 bg-s-panel border-b border-s-border">
        {/* Logo */}
        <div className="flex items-center gap-2.5 mr-4">
          <Activity size={14} className="text-s-accent" />
          <span className="text-[13px] font-semibold tracking-wide text-s-text">
            SPYDRWEB
          </span>
          <button className="flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] text-s-muted border border-s-border hover:bg-s-surface transition">
            Workspace
            <ChevronDown size={10} />
          </button>
        </div>

        <div className="h-4 w-px bg-s-border mx-2" />

        {/* Stats */}
        <div className="flex items-center gap-5 flex-1 text-[11px]">
          <div>
            <span className="text-s-text-tertiary mr-1">Events</span>
            <span className="font-mono font-medium text-s-text-secondary">
              {eventCount}
            </span>
          </div>
          <div>
            <span className="text-s-text-tertiary mr-1">Alerts</span>
            <span className="font-mono font-medium text-s-text-secondary">
              {alertCount}
            </span>
          </div>
          <div>
            <span className="text-s-text-tertiary mr-1">Queue</span>
            <span className="font-mono font-medium text-s-text-secondary">
              {alertQueueSize}
            </span>
          </div>
        </div>

        {/* Mode Toggle */}
        <div className="flex items-center gap-1.5 mr-3">
          <span className="text-[10px] text-s-text-tertiary">Mode</span>
          <div className="flex rounded border border-s-border overflow-hidden">
            <button
              onClick={() => onModeChange("pipeline")}
              className={`px-2 py-0.5 text-[10px] font-medium transition ${
                mode === "pipeline"
                  ? "bg-s-accent text-white"
                  : "bg-s-panel text-s-muted hover:bg-s-surface"
              }`}
            >
              Pipeline
            </button>
            <button
              onClick={() => onModeChange("agentic")}
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

        {/* Demo Toggle */}
        <button
          onClick={() => setShowDemoPanel(!showDemoPanel)}
          className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-medium transition ${
            showDemoPanel
              ? "bg-s-accent text-white"
              : "text-s-muted border border-s-border hover:bg-s-surface"
          }`}
        >
          <Play size={9} />
          Demo
        </button>
      </div>

      {showDemoPanel && (
        <DemoControls
          onStart={onDemoStart}
          onInject={onInjectFraud}
          onClose={() => setShowDemoPanel(false)}
        />
      )}
    </div>
  );
}
