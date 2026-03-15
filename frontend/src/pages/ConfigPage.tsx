import { useState, useEffect } from "react";
import {
  Settings,
  Brain,
  Shield,
  Zap,
  Layers,
  Gauge,
  Database,
  Activity,
} from "lucide-react";

interface LayerConfig {
  id: number;
  name: string;
  type: string;
  description: string;
}

interface SystemConfig {
  llm: { model: string; base_url: string; cache_responses: boolean };
  pipeline: { mode: string; max_agent_rounds: number; layers: LayerConfig[] };
  scoring: {
    thresholds: { allow: number; delay: number; hold: number; refer: number };
    velocity_multiplier_weight: number;
    corroboration_bonus: number;
  };
  fast_path: { max_amount_std: number; min_profile_age_days: number };
  vulnerability: { high_threshold: number; medium_threshold: number };
  data: { mode: string; demo_speed: number; baseline_decay_factor: number };
}

function SectionCard({
  title,
  subtitle,
  icon: Icon,
  children,
}: {
  title: string;
  subtitle: string;
  icon: typeof Settings;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-s-panel rounded border border-s-border flex flex-col">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-s-border">
        <Icon size={12} className="text-s-accent" />
        <div>
          <h3 className="text-[11px] font-semibold text-s-text">{title}</h3>
          <p className="text-[9px] text-s-text-tertiary">{subtitle}</p>
        </div>
      </div>
      <div className="p-3">{children}</div>
    </div>
  );
}

function ConfigRow({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-center justify-between py-1 border-b border-s-border last:border-0">
      <span className="text-[10px] text-s-text-tertiary">{label}</span>
      <span className={`text-[10px] text-s-text font-medium ${mono ? "font-mono" : ""}`}>
        {value}
      </span>
    </div>
  );
}

export default function ConfigPage() {
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/config")
      .then((r) => r.json())
      .then((data) => {
        setConfig(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-6 h-6 border-2 border-s-accent border-t-transparent rounded-full animate-spin mx-auto mb-2" />
          <p className="text-[10px] text-s-text-tertiary">Loading configuration...</p>
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-[11px] text-s-text-tertiary">Failed to load system configuration.</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-3 space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2 mb-1">
        <Settings size={14} className="text-s-accent" />
        <div>
          <h1 className="text-[13px] font-semibold text-s-text">System Configuration</h1>
          <p className="text-[9px] text-s-text-tertiary">
            Read-only view of detection pipeline settings and thresholds
          </p>
        </div>
      </div>

      {/* Row 1: LLM + Pipeline Mode */}
      <div className="grid grid-cols-2 gap-3">
        <SectionCard title="LLM Provider" subtitle="Language model configuration" icon={Brain}>
          <div className="space-y-0">
            <ConfigRow label="Model" value={config.llm.model} mono />
            <ConfigRow label="Endpoint" value={config.llm.base_url.replace(/^https?:\/\//, "").slice(0, 40) + "..."} mono />
            <ConfigRow label="Response Caching" value={config.llm.cache_responses ? "Enabled" : "Disabled"} />
          </div>
        </SectionCard>

        <SectionCard title="Pipeline Mode" subtitle="Processing strategy" icon={Activity}>
          <div className="space-y-0">
            <ConfigRow label="Default Mode" value={config.pipeline.mode.toUpperCase()} />
            <ConfigRow label="Max Agent Rounds" value={String(config.pipeline.max_agent_rounds)} mono />
            <ConfigRow label="Data Source" value={config.data.mode.toUpperCase()} />
            <ConfigRow label="Demo Speed" value={`${config.data.demo_speed}x`} mono />
            <ConfigRow label="Baseline Decay" value={String(config.data.baseline_decay_factor)} mono />
          </div>
        </SectionCard>
      </div>

      {/* Row 2: Detection Layers */}
      <SectionCard title="Detection Layers" subtitle="5-layer fraud detection pipeline" icon={Layers}>
        <div className="space-y-2">
          {config.pipeline.layers.map((layer) => (
            <div
              key={layer.id}
              className="rounded border border-s-border p-2.5 bg-s-surface flex items-start gap-3"
            >
              <div className="w-7 h-7 rounded flex items-center justify-center bg-s-panel border border-s-border shrink-0">
                <span className="text-[10px] font-bold font-mono text-s-accent">L{layer.id}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-semibold text-s-text">{layer.name}</span>
                  <span className={`text-[8px] font-medium px-1.5 py-0.5 rounded ${
                    layer.type === "llm"
                      ? "bg-purple-100 text-purple-700 border border-purple-200"
                      : "bg-emerald-100 text-emerald-700 border border-emerald-200"
                  }`}>
                    {layer.type === "llm" ? "AI/LLM" : "DETERMINISTIC"}
                  </span>
                </div>
                <p className="text-[9px] text-s-text-secondary mt-0.5 leading-relaxed">
                  {layer.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      {/* Row 3: Scoring + Fast-Path + Vulnerability */}
      <div className="grid grid-cols-3 gap-3">
        <SectionCard title="Score Thresholds" subtitle="Action classification bands" icon={Gauge}>
          <div className="space-y-1.5">
            {Object.entries(config.scoring.thresholds).map(([action, threshold]) => {
              const colors: Record<string, string> = {
                allow: "bg-emerald-100 text-emerald-700 border-emerald-200",
                delay: "bg-amber-100 text-amber-700 border-amber-200",
                hold: "bg-red-100 text-red-700 border-red-200",
                refer: "bg-red-200 text-red-800 border-red-300",
              };
              return (
                <div key={action} className="flex items-center justify-between">
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${colors[action] || ""}`}>
                    {action.toUpperCase()}
                  </span>
                  <span className="text-[10px] font-mono text-s-text">
                    {"≥"} {threshold}
                  </span>
                </div>
              );
            })}
            <div className="border-t border-s-border pt-1.5 mt-1.5 space-y-0">
              <ConfigRow label="Velocity Weight" value={String(config.scoring.velocity_multiplier_weight)} mono />
              <ConfigRow label="Corroboration Bonus" value={String(config.scoring.corroboration_bonus)} mono />
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Fast-Path Filter" subtitle="Skip criteria for low-risk txns" icon={Zap}>
          <div className="space-y-0">
            <ConfigRow label="Max Amount Std Dev" value={`${config.fast_path.max_amount_std}σ`} mono />
            <ConfigRow label="Min Profile Age" value={`${config.fast_path.min_profile_age_days} days`} mono />
          </div>
          <div className="mt-3 rounded border border-s-border p-2 bg-emerald-50">
            <p className="text-[9px] text-emerald-700 leading-relaxed">
              Transactions within {config.fast_path.max_amount_std}σ of baseline, from accounts
              with {config.fast_path.min_profile_age_days}+ days history and low vulnerability,
              skip Layers 2–5 entirely.
            </p>
          </div>
        </SectionCard>

        <SectionCard title="Vulnerability Scoring" subtitle="Exploitation risk classification" icon={Shield}>
          <div className="space-y-0">
            <ConfigRow label="High Threshold" value={`≥ ${config.vulnerability.high_threshold}`} mono />
            <ConfigRow label="Medium Threshold" value={`≥ ${config.vulnerability.medium_threshold}`} mono />
          </div>
          <div className="mt-3 space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="flex-1 h-4 rounded-full bg-s-surface overflow-hidden flex">
                <div className="h-full bg-emerald-400" style={{ width: `${config.vulnerability.medium_threshold * 100}%` }} />
                <div
                  className="h-full bg-amber-400"
                  style={{ width: `${(config.vulnerability.high_threshold - config.vulnerability.medium_threshold) * 100}%` }}
                />
                <div
                  className="h-full bg-red-400"
                  style={{ width: `${(1 - config.vulnerability.high_threshold) * 100}%` }}
                />
              </div>
            </div>
            <div className="flex justify-between text-[8px] text-s-muted">
              <span>Low</span>
              <span>Medium</span>
              <span>High</span>
            </div>
          </div>
        </SectionCard>
      </div>

      {/* Row 4: Rules engine details */}
      <SectionCard title="Rules Engine (Layer 1)" subtitle="Deterministic rule descriptions" icon={Database}>
        <div className="grid grid-cols-2 gap-2">
          {[
            { name: "Velocity Check", desc: "≥5 transfers in 1 hour window" },
            { name: "Amount Threshold", desc: "Single transaction exceeds $10,000" },
            { name: "Geographic Impossibility", desc: "Cross-country transaction within impossible timeframe" },
            { name: "New Payee Large Amount", desc: "First-time recipient receives large transfer" },
            { name: "Blacklist Check", desc: "Receiver ID matches known fraud blacklist" },
            { name: "Device + Sensitive Action", desc: "Unusual device paired with password/email change" },
            { name: "Balance Drain", desc: "Transaction drains ≥80% of account balance" },
            { name: "Layering Pattern", desc: "Money-in immediately followed by money-out (mule behavior)" },
          ].map((rule) => (
            <div key={rule.name} className="rounded border border-s-border p-2 bg-s-surface">
              <div className="text-[10px] font-semibold text-s-text">{rule.name}</div>
              <p className="text-[8px] text-s-text-tertiary mt-0.5">{rule.desc}</p>
            </div>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
