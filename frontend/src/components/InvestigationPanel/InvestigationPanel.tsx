import { Fragment, useEffect, useState } from "react";
import {
  Shield,
  User,
  GitBranch,
  MessageSquare,
  Brain,
  ChevronRight,
  Zap,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
} from "lucide-react";
import type { CaseReport, GraphData, LayerSignal } from "../../types";
import { getGraphNeighbors } from "../../services/api";
import Md from "../Md";
import GraphViewer from "../GraphViewer/GraphViewer";
import ThreatRadar from "../CaseBrief/ThreatRadar";

type TabId = "overview" | "rules" | "profiling" | "graph" | "comms" | "synthesis";

interface Props {
  report: CaseReport;
  onClose: () => void;
}

const TABS: { id: TabId; label: string; icon: typeof Shield; layerId?: number }[] = [
  { id: "overview", label: "Overview", icon: Zap },
  { id: "rules", label: "Rules Engine", icon: Shield, layerId: 1 },
  { id: "profiling", label: "Profiling", icon: User, layerId: 2 },
  { id: "graph", label: "Graph", icon: GitBranch, layerId: 3 },
  { id: "comms", label: "Comms", icon: MessageSquare, layerId: 4 },
  { id: "synthesis", label: "Synthesis", icon: Brain, layerId: 5 },
];

const RULE_LABELS: Record<string, string> = {
  velocity: "Velocity Anomaly",
  amount_threshold: "Amount Threshold",
  geo_impossibility: "Geographic Impossibility",
  new_payee_large: "New Payee Large Amount",
  blacklist: "Blacklist Check",
  device_sensitive: "Device + Sensitive Action",
  balance_drain: "Balance Drain",
  layering: "Layering Pattern",
  rules: "Rules Engine",
};

const TACTIC_DISPLAY: Record<string, string> = {
  family_coercion: "Family Coercion",
  romance_scam: "Romance Scam",
  authority_impersonation: "Authority Impersonation",
  phone_coaching: "Phone Coaching",
  elder_exploitation: "Elder Exploitation",
  account_takeover: "Account Takeover",
  mule_network: "Mule Network",
  card_testing: "Card Testing",
};

const PIPELINE_LAYERS = [
  { id: 1, name: "Rules", icon: Shield },
  { id: 2, name: "Profile", icon: User },
  { id: 3, name: "Graph", icon: GitBranch },
  { id: 4, name: "Comms", icon: MessageSquare },
  { id: 5, name: "Synthesis", icon: Brain },
] as const;

function getLayerSignals(report: CaseReport, layerId: number): LayerSignal[] {
  return report.layer_signals.filter((s) => s.layer_id === layerId);
}

function hasLayerRun(report: CaseReport, layerId: number): boolean {
  if (layerId === 1) return true;
  return report.layer_signals.some((s) => s.layer_id === layerId);
}

function StatusBadge({ triggered }: { triggered: boolean }) {
  return triggered ? (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[8px] font-bold bg-red-100 text-red-700 border border-red-200">
      <AlertTriangle size={10} /> TRIGGERED
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[8px] font-bold bg-emerald-100 text-emerald-700 border border-emerald-200">
      <CheckCircle2 size={10} /> CLEAR
    </span>
  );
}

function RiskGauge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const circumference = 2 * Math.PI * 28;
  const filled = (pct / 100) * circumference;
  const color = pct >= 80 ? "#9b2c2c" : pct >= 50 ? "#92400e" : "#276749";

  return (
    <div className="relative w-[56px] h-[56px]">
      <svg viewBox="0 0 64 64" className="w-full h-full -rotate-90">
        <circle cx="32" cy="32" r="28" fill="none" stroke="#e5e7eb" strokeWidth="4" />
        <circle
          cx="32" cy="32" r="28" fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={`${filled} ${circumference}`} strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-sm font-bold" style={{ color }}>{pct}</span>
        <span className="text-[6px] text-s-text-tertiary">/100</span>
      </div>
    </div>
  );
}

function ActionBadge({ action }: { action: string }) {
  const styles: Record<string, string> = {
    allow: "bg-emerald-600 text-white",
    delay: "bg-amber-500 text-white",
    hold: "bg-red-600 text-white",
    refer: "bg-red-800 text-white",
  };
  return (
    <span className={`px-3 py-1.5 rounded-md text-[11px] font-bold uppercase tracking-wider shrink-0 ${styles[action] || styles.allow}`}>
      {action}
    </span>
  );
}

function VerdictHero({ report }: { report: CaseReport }) {
  const brief = report.evidence_brief;
  const tactic = brief?.exploitation_tactic;
  const hasTactic = tactic && tactic !== "unknown";
  const triggered = report.layer_signals.filter((s) => s.triggered);

  if (report.fast_pathed) {
    const sender = report.sender_profile;
    const reasons: string[] = [];
    if (sender?.baseline && sender.baseline.days_of_history >= 30)
      reasons.push(`${sender.baseline.days_of_history}d history`);
    if (sender?.vulnerability && sender.vulnerability.score <= 0.4)
      reasons.push("Low vulnerability");
    const rulesTriggered = report.layer_signals.filter((s) => s.layer_id === 1 && s.triggered).length;
    if (rulesTriggered === 0) reasons.push("0/8 rules triggered");

    return (
      <div className="rounded-lg border-2 border-emerald-300 bg-gradient-to-r from-emerald-50 via-emerald-50 to-emerald-100/60 p-4">
        <div className="flex items-center gap-4">
          <RiskGauge score={report.confidence_score} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Zap size={16} className="text-emerald-600 shrink-0" />
              <h3 className="text-[14px] font-bold text-emerald-800 tracking-tight">
                Routine Transaction
              </h3>
            </div>
            <p className="text-[10px] text-emerald-700 leading-relaxed">
              Fast-pathed at Layer 1. All criteria met — deeper analysis skipped.
            </p>
            {reasons.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-2">
                {reasons.map((r, i) => (
                  <span key={i} className="inline-flex items-center gap-0.5 text-[8px] px-1.5 py-0.5 rounded-full bg-emerald-200/60 text-emerald-700 font-medium">
                    <CheckCircle2 size={8} /> {r}
                  </span>
                ))}
              </div>
            )}
          </div>
          <ActionBadge action={report.recommended_action} />
        </div>
      </div>
    );
  }

  if (hasTactic) {
    const tacticLabel = TACTIC_DISPLAY[tactic] || tactic.replace(/_/g, " ");
    const firstSentence = brief?.narrative
      ? brief.narrative.split(/[.!?]\s/)[0]?.replace(/[*#_`]/g, "").trim()
      : "";

    return (
      <div className="rounded-lg border-2 border-red-300 bg-gradient-to-r from-red-50 via-red-50 to-red-100/60 p-4">
        <div className="flex items-center gap-4">
          <RiskGauge score={report.confidence_score} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <AlertTriangle size={16} className="text-red-600 shrink-0" />
              <h3 className="text-[14px] font-bold text-red-800 tracking-tight capitalize">
                {tacticLabel}
              </h3>
            </div>
            {firstSentence && (
              <p className="text-[10px] text-red-700 leading-relaxed line-clamp-2">
                {firstSentence}{firstSentence.match(/[.!?]$/) ? "" : "."}
              </p>
            )}
          </div>
          <ActionBadge action={report.recommended_action} />
        </div>
      </div>
    );
  }

  const topSignals = triggered
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 3);
  const signalNames = topSignals
    .map((s) => RULE_LABELS[s.layer_name] || s.layer_name.replace(/_/g, " "))
    .join(" + ");

  return (
    <div className="rounded-lg border-2 border-amber-300 bg-gradient-to-r from-amber-50 via-amber-50 to-amber-100/60 p-4">
      <div className="flex items-center gap-4">
        <RiskGauge score={report.confidence_score} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Shield size={16} className="text-amber-600 shrink-0" />
            <h3 className="text-[14px] font-bold text-amber-800 tracking-tight">
              {triggered.length > 0 ? "Suspicious Activity Detected" : "Under Review"}
            </h3>
          </div>
          {signalNames && (
            <p className="text-[10px] text-amber-700 leading-relaxed">
              Triggered: {signalNames}
            </p>
          )}
        </div>
        <ActionBadge action={report.recommended_action} />
      </div>
    </div>
  );
}

function PipelineJourney({ report }: { report: CaseReport }) {
  type LayerState = "skipped" | "clear" | "triggered";

  const getState = (layerId: number): LayerState => {
    if (report.fast_pathed && layerId > 1) return "skipped";
    const signals = getLayerSignals(report, layerId);
    if (signals.length === 0 && layerId > 1) return "skipped";
    if (signals.some((s) => s.triggered)) return "triggered";
    return "clear";
  };

  const stateStyles: Record<LayerState, { node: string; label: string; text: string }> = {
    triggered: {
      node: "bg-red-100 border-red-400 text-red-700",
      label: "text-red-600",
      text: "TRIGGERED",
    },
    clear: {
      node: "bg-emerald-100 border-emerald-400 text-emerald-700",
      label: "text-emerald-600",
      text: "CLEAR",
    },
    skipped: {
      node: "bg-slate-50 border-slate-300 text-slate-400 border-dashed",
      label: "text-slate-400",
      text: "SKIPPED",
    },
  };

  return (
    <div className="rounded border border-s-border p-3 bg-white">
      <div className="text-[8px] font-semibold text-s-text-tertiary uppercase mb-3">Pipeline Journey</div>
      <div className="flex items-center mb-1.5">
        {PIPELINE_LAYERS.map((layer, i) => {
          const state = getState(layer.id);
          const style = stateStyles[state];
          const Icon = layer.icon;
          const nextState = i < PIPELINE_LAYERS.length - 1 ? getState(PIPELINE_LAYERS[i + 1].id) : null;

          return (
            <Fragment key={layer.id}>
              <div className={`w-9 h-9 rounded-full flex items-center justify-center border-2 shrink-0 ${style.node}`}>
                <Icon size={14} />
              </div>
              {i < PIPELINE_LAYERS.length - 1 && (
                <div className="flex-1 relative">
                  <div className={`h-[2px] ${
                    nextState === "skipped"
                      ? "border-t-[2px] border-dashed border-slate-200"
                      : "bg-slate-200"
                  }`} />
                  {report.fast_pathed && i === 0 && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 text-[7px] text-emerald-600 font-bold whitespace-nowrap">
                      FAST PATH
                    </div>
                  )}
                </div>
              )}
            </Fragment>
          );
        })}
      </div>
      <div className="flex">
        {PIPELINE_LAYERS.map((layer, i) => {
          const state = getState(layer.id);
          const style = stateStyles[state];
          return (
            <Fragment key={layer.id}>
              <div className="flex flex-col items-center w-9 shrink-0">
                <span className="text-[8px] font-semibold text-s-text-secondary">{layer.name}</span>
                <span className={`text-[7px] font-bold uppercase tracking-wide ${style.label}`}>
                  {style.text}
                </span>
              </div>
              {i < PIPELINE_LAYERS.length - 1 && <div className="flex-1" />}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}

function KeyEvidence({ report }: { report: CaseReport }) {
  if (report.fast_pathed) return null;

  const triggered = report.layer_signals
    .filter((s) => s.triggered)
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 4);

  if (triggered.length === 0) return null;

  const layerColors: Record<number, string> = {
    1: "bg-red-50 text-red-700 border-red-200",
    2: "bg-amber-50 text-amber-700 border-amber-200",
    3: "bg-blue-50 text-blue-700 border-blue-200",
    4: "bg-purple-50 text-purple-700 border-purple-200",
  };

  const layerNames: Record<number, string> = {
    1: "Rules",
    2: "Profile",
    3: "Graph",
    4: "Comms",
  };

  return (
    <div className="rounded border border-s-border p-3 bg-white">
      <div className="text-[8px] font-semibold text-s-text-tertiary uppercase mb-2">Key Evidence</div>
      <div className="flex flex-wrap gap-1.5">
        {triggered.map((signal, i) => {
          const colors = layerColors[signal.layer_id] || "bg-slate-50 text-slate-700 border-slate-200";
          const name = layerNames[signal.layer_id] || `L${signal.layer_id}`;
          const label = RULE_LABELS[signal.layer_name] || signal.layer_name.replace(/_/g, " ");
          return (
            <span
              key={i}
              className={`inline-flex items-center gap-1 px-2 py-1 rounded-full border text-[9px] font-medium ${colors}`}
            >
              <span className="font-bold">{name}:</span>
              <span>{label}</span>
              <span className="text-[8px] opacity-60">{Math.round(signal.confidence * 100)}%</span>
            </span>
          );
        })}
      </div>
    </div>
  );
}

function SkippedLayerNotice({ layerName, report }: { layerName: string; report: CaseReport }) {
  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[200px] text-center px-6">
      <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mb-3">
        <ChevronRight size={20} className="text-slate-400" />
      </div>
      <p className="text-[11px] font-medium text-slate-500">
        {report.fast_pathed
          ? `${layerName} was skipped — transaction was fast-pathed at Layer 1`
          : `${layerName} did not run for this transaction`}
      </p>
      <p className="text-[9px] text-slate-400 mt-1 max-w-xs">
        {report.fast_pathed
          ? "The Rules Engine found no anomalies and fast-path criteria were met, so deeper analysis layers were not invoked."
          : "The AI test plan did not prioritize this layer for this transaction."}
      </p>
    </div>
  );
}

function OverviewTab({ report }: { report: CaseReport }) {
  const sender = report.sender_profile;
  const receiver = report.receiver_profile;

  return (
    <div className="space-y-3">
      <VerdictHero report={report} />
      <PipelineJourney report={report} />
      <KeyEvidence report={report} />

      {report.layer_signals.length > 0 && !report.fast_pathed && (
        <div className="rounded border border-s-border p-3 bg-white">
          <ThreatRadar
            signals={report.layer_signals}
            recipientRiskScore={receiver?.recipient_risk?.receive_to_send_ratio ? 0.5 : 0}
          />
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        {sender && (
          <div className="rounded border border-s-border p-3 bg-white">
            <div className="text-[9px] text-s-text-tertiary uppercase font-semibold mb-2 flex items-center gap-1">
              <User size={10} /> Sender Profile
            </div>
            <div className="text-[11px] font-medium text-s-text">{sender.name || sender.account_id}</div>
            <div className="text-[9px] text-s-text-secondary mt-0.5">
              {sender.age ? `Age ${sender.age}` : ""} {sender.location ? `• ${sender.location}` : ""}
            </div>
            {sender.vulnerability && (
              <div className="mt-2 flex items-center gap-2">
                <div className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                  sender.vulnerability.score >= 0.4
                    ? "bg-amber-100 text-amber-700 border border-amber-200"
                    : "bg-emerald-100 text-emerald-700 border border-emerald-200"
                }`}>
                  Vulnerability: {Math.round(sender.vulnerability.score * 100)}%
                </div>
              </div>
            )}
            {sender.vulnerability && sender.vulnerability.factors.length > 0 && (
              <div className="mt-1.5 space-y-0.5">
                {sender.vulnerability.factors.map((f, i) => (
                  <div key={i} className="text-[8px] text-s-text-tertiary flex items-start gap-1">
                    <span className="w-1 h-1 rounded-full bg-amber-400 mt-1 shrink-0" />
                    <Md>{f.description}</Md>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {receiver && (
          <div className="rounded border border-s-border p-3 bg-white">
            <div className="text-[9px] text-s-text-tertiary uppercase font-semibold mb-2 flex items-center gap-1">
              <ArrowRight size={10} /> Receiver Profile
            </div>
            <div className="text-[11px] font-medium text-s-text">{receiver.name || receiver.account_id}</div>
            <div className="text-[9px] text-s-text-secondary mt-0.5">
              {receiver.age ? `Age ${receiver.age}` : ""} {receiver.location ? `• ${receiver.location}` : ""}
            </div>
            {receiver.recipient_risk && (
              <div className="mt-2 space-y-0.5 text-[8px] text-s-text-tertiary">
                <div>First-time senders (7d): {receiver.recipient_risk.first_time_sender_count_7d}</div>
                <div>Inbound velocity (24h): {receiver.recipient_risk.inbound_velocity_24h}</div>
                <div>Receive-only: {receiver.recipient_risk.is_receive_only ? "Yes" : "No"}</div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function RulesTab({ report }: { report: CaseReport }) {
  const rulesSignals = getLayerSignals(report, 1);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-[11px] font-semibold text-s-text">Layer 1 — Deterministic Rules Engine</h3>
          <p className="text-[9px] text-s-text-tertiary mt-0.5">
            Pure Python, no AI. 8 rules checked against every transaction.
          </p>
        </div>
        <div className="text-[9px] font-mono text-s-text-secondary">
          {rulesSignals.filter((s) => s.triggered).length}/{rulesSignals.length} triggered
        </div>
      </div>

      <div className="space-y-2">
        {rulesSignals.map((signal, i) => (
          <div
            key={i}
            className={`rounded border p-2.5 ${
              signal.triggered
                ? "bg-red-50 border-red-200"
                : "bg-white border-s-border"
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-s-text font-mono">
                  {RULE_LABELS[signal.layer_name] || signal.layer_name}
                </span>
              </div>
              <StatusBadge triggered={signal.triggered} />
            </div>

            <Md className={`text-[9px] leading-relaxed ${
              signal.triggered ? "text-red-700" : "text-s-text-secondary"
            }`}>
              {signal.explanation}
            </Md>

            {signal.evidence && Object.keys(signal.evidence).length > 0 && (
              <div className="mt-1.5 bg-slate-50 rounded p-1.5 border border-slate-100">
                <div className="text-[8px] text-slate-500 font-semibold uppercase mb-0.5">Evidence</div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-0.5">
                  {Object.entries(signal.evidence).map(([k, v]) => (
                    <div key={k} className="text-[8px] flex justify-between">
                      <span className="text-slate-400">{k}:</span>
                      <span className="text-slate-600 font-mono truncate ml-1 max-w-[120px]">
                        {typeof v === "object" ? JSON.stringify(v).slice(0, 40) : String(v)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {signal.triggered && (
              <div className="mt-1 text-[8px] font-mono text-red-500">
                Confidence: {Math.round(signal.confidence * 100)}% | Severity: {signal.severity}
              </div>
            )}
          </div>
        ))}

        {rulesSignals.length === 0 && (
          <div className="text-center text-[10px] text-s-text-tertiary py-6">
            No Layer 1 signals recorded for this transaction.
          </div>
        )}
      </div>
    </div>
  );
}

function ProfilingTab({ report }: { report: CaseReport }) {
  if (!hasLayerRun(report, 2)) {
    return <SkippedLayerNotice layerName="Behavioral Profiling (Layer 2)" report={report} />;
  }

  const signals = getLayerSignals(report, 2);

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-[11px] font-semibold text-s-text">Layer 2 — Behavioral Disruption Analysis</h3>
        <p className="text-[9px] text-s-text-tertiary mt-0.5">
          Compares transaction against sender's baseline for amount, frequency, timing, and social patterns.
        </p>
      </div>

      {/* Baseline summary */}
      {report.sender_profile?.baseline && (
        <div className="rounded border border-s-border p-2.5 bg-white">
          <div className="text-[9px] font-semibold text-s-text-tertiary uppercase mb-1.5">Sender Baseline</div>
          <div className="grid grid-cols-3 gap-3 text-[9px]">
            <div>
              <div className="text-s-text-tertiary">Avg Amount</div>
              <div className="font-mono font-medium text-s-text">
                ${report.sender_profile.baseline.avg_amount.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-s-text-tertiary">Std Dev</div>
              <div className="font-mono font-medium text-s-text">
                ${report.sender_profile.baseline.std_amount.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-s-text-tertiary">Daily Freq</div>
              <div className="font-mono font-medium text-s-text">
                {report.sender_profile.baseline.avg_daily_frequency.toFixed(1)}
              </div>
            </div>
            <div>
              <div className="text-s-text-tertiary">History</div>
              <div className="font-mono font-medium text-s-text">
                {report.sender_profile.baseline.days_of_history} days
              </div>
            </div>
            <div>
              <div className="text-s-text-tertiary">Typical Hours</div>
              <div className="font-mono font-medium text-s-text">
                {report.sender_profile.baseline.typical_hours?.slice(0, 5).join(", ") || "N/A"}
              </div>
            </div>
            <div>
              <div className="text-s-text-tertiary">Balance Checks/day</div>
              <div className="font-mono font-medium text-s-text">
                {report.sender_profile.baseline.balance_check_frequency_daily.toFixed(1)}
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-2">
        {signals.map((signal, i) => (
          <div
            key={i}
            className={`rounded border p-2.5 ${
              signal.triggered ? "bg-amber-50 border-amber-200" : "bg-white border-s-border"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <StatusBadge triggered={signal.triggered} />
              {signal.triggered && (
                <span className="text-[8px] font-mono text-amber-600">
                  Confidence: {Math.round(signal.confidence * 100)}%
                </span>
              )}
            </div>
            <Md className={`text-[10px] leading-relaxed ${
              signal.triggered ? "text-amber-800" : "text-s-text-secondary"
            }`}>
              {signal.explanation}
            </Md>
          </div>
        ))}
      </div>
    </div>
  );
}

function GraphTab({ report }: { report: CaseReport }) {
  const [egoGraph, setEgoGraph] = useState<GraphData>({ nodes: [], edges: [] });
  const [egoLoading, setEgoLoading] = useState(false);

  const senderId = report.transaction?.sender_id;

  useEffect(() => {
    if (!senderId) return;
    let cancelled = false;
    setEgoLoading(true);
    getGraphNeighbors(senderId, 2)
      .then((data) => {
        if (!cancelled) setEgoGraph(data);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setEgoLoading(false);
      });
    return () => { cancelled = true; };
  }, [senderId]);

  if (!hasLayerRun(report, 3)) {
    return (
      <div className="space-y-3">
        <SkippedLayerNotice layerName="Graph Topology Analysis (Layer 3)" report={report} />
        {egoGraph.nodes.length > 0 && (
          <div className="rounded border border-s-border overflow-hidden bg-white h-[300px]">
            <GraphViewer
              graph={egoGraph}
              loading={egoLoading}
              selectedNodeId={senderId}
              compact
            />
          </div>
        )}
      </div>
    );
  }

  const signals = getLayerSignals(report, 3);

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-[11px] font-semibold text-s-text">Layer 3 — Graph Topology & Velocity</h3>
        <p className="text-[9px] text-s-text-tertiary mt-0.5">
          Analyzes hub detection, fan-in/out patterns, shared identity, and velocity spikes.
        </p>
      </div>

      {/* Ego-network graph */}
      <div className="rounded border border-s-border overflow-hidden bg-white h-[300px]">
        <GraphViewer
          graph={egoGraph}
          loading={egoLoading}
          selectedNodeId={senderId}
          compact
        />
      </div>

      {/* Brain overlay context */}
      {report.brain_overlay && (
        <div className="rounded border border-s-border p-2.5 bg-white">
          <div className="text-[9px] font-semibold text-s-text-tertiary uppercase mb-1.5">Brain Overlay Context</div>
          <div className="grid grid-cols-2 gap-3 text-[9px]">
            <div>
              <div className="text-s-text-tertiary">Elevated</div>
              <div className={`font-medium ${
                report.brain_overlay.elevated ? "text-s-danger" : "text-s-safe"
              }`}>
                {report.brain_overlay.elevated ? "Yes" : "No"}
              </div>
            </div>
            <div>
              <div className="text-s-text-tertiary">Velocity Deviation</div>
              <div className="font-mono font-medium text-s-text">
                {(report.brain_overlay.velocity_deviation as number)?.toFixed(2) || "1.00"}x
              </div>
            </div>
          </div>
          {report.brain_overlay.context && (
            <Md className="text-[9px] text-s-text-secondary mt-1.5">
              {String(report.brain_overlay.context)}
            </Md>
          )}
        </div>
      )}

      <div className="space-y-2">
        {signals.map((signal, i) => (
          <div
            key={i}
            className={`rounded border p-2.5 ${
              signal.triggered ? "bg-red-50 border-red-200" : "bg-white border-s-border"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <StatusBadge triggered={signal.triggered} />
              {signal.triggered && (
                <span className="text-[8px] font-mono text-red-500">
                  Confidence: {Math.round(signal.confidence * 100)}%
                </span>
              )}
            </div>
            <Md className={`text-[10px] leading-relaxed ${
              signal.triggered ? "text-red-800" : "text-s-text-secondary"
            }`}>
              {signal.explanation}
            </Md>
            {signal.evidence && Object.keys(signal.evidence).length > 0 && (
              <details className="mt-1.5">
                <summary className="text-[8px] text-slate-400 cursor-pointer hover:text-slate-600">
                  Show evidence
                </summary>
                <pre className="text-[8px] text-slate-500 font-mono mt-1 bg-slate-50 p-1.5 rounded overflow-x-auto">
                  {JSON.stringify(signal.evidence, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function CommsTab({ report }: { report: CaseReport }) {
  if (!hasLayerRun(report, 4)) {
    return <SkippedLayerNotice layerName="Communication Comprehension (Layer 4)" report={report} />;
  }

  const signals = getLayerSignals(report, 4);

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-[11px] font-semibold text-s-text">Layer 4 — AI Communication Comprehension</h3>
        <p className="text-[9px] text-s-text-tertiary mt-0.5">
          LLM analyzes support chat for coaching markers, vocabulary shifts, and coercion indicators.
        </p>
      </div>

      {/* Communication fingerprint */}
      {report.sender_profile?.communication_fingerprint && (
        <div className="rounded border border-s-border p-2.5 bg-white">
          <div className="text-[9px] font-semibold text-s-text-tertiary uppercase mb-1.5">
            Established Communication Fingerprint
          </div>
          <div className="grid grid-cols-2 gap-2 text-[9px]">
            <div>
              <span className="text-s-text-tertiary">Vocabulary:</span>{" "}
              <span className="text-s-text font-medium">
                {report.sender_profile.communication_fingerprint.typical_vocabulary_level}
              </span>
            </div>
            <div>
              <span className="text-s-text-tertiary">Tone:</span>{" "}
              <span className="text-s-text font-medium">
                {report.sender_profile.communication_fingerprint.typical_tone}
              </span>
            </div>
            <div>
              <span className="text-s-text-tertiary">Tech terms:</span>{" "}
              <span className="text-s-text font-medium">
                {report.sender_profile.communication_fingerprint.uses_technical_banking_terms ? "Yes" : "No"}
              </span>
            </div>
            <div>
              <span className="text-s-text-tertiary">Sentiment:</span>{" "}
              <span className="text-s-text font-medium">
                {report.sender_profile.communication_fingerprint.baseline_sentiment}
              </span>
            </div>
          </div>
          {report.sender_profile.communication_fingerprint.sample_phrases.length > 0 && (
            <div className="mt-1.5">
              <div className="text-[8px] text-s-text-tertiary">Sample phrases:</div>
              <div className="text-[8px] text-s-text-secondary italic mt-0.5">
                {report.sender_profile.communication_fingerprint.sample_phrases.slice(0, 3).map((p, i) => (
                  <span key={i}>"{p}" {i < 2 ? "• " : ""}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="space-y-2">
        {signals.map((signal, i) => (
          <div
            key={i}
            className={`rounded border p-2.5 ${
              signal.triggered ? "bg-purple-50 border-purple-200" : "bg-white border-s-border"
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <StatusBadge triggered={signal.triggered} />
              {signal.triggered && (
                <span className="text-[8px] font-mono text-purple-600">
                  Confidence: {Math.round(signal.confidence * 100)}%
                </span>
              )}
            </div>
            <Md className={`text-[10px] leading-relaxed ${
              signal.triggered ? "text-purple-800" : "text-s-text-secondary"
            }`}>
              {signal.explanation}
            </Md>
            {signal.evidence && Object.keys(signal.evidence).length > 0 && (
              <div className="mt-2 space-y-1.5">
                {Object.entries(signal.evidence).map(([indicator, data]) => {
                  const d = data as Record<string, unknown>;
                  return (
                    <div key={indicator} className="bg-white rounded border border-purple-100 p-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[9px] font-medium text-purple-700">
                          {indicator.replace(/_/g, " ")}
                        </span>
                        <span className="text-[8px] font-mono text-purple-500">
                          {d.confidence ? `${Math.round(Number(d.confidence) * 100)}%` : ""}
                        </span>
                      </div>
                      {d.evidence && (
                        <Md className="text-[8px] text-slate-500 mt-0.5">{String(d.evidence)}</Md>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function SynthesisTab({ report }: { report: CaseReport }) {
  const brief = report.evidence_brief;

  if (!brief) {
    const hasTriggered = report.layer_signals.some((s) => s.triggered);
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[200px] text-center px-6">
        <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mb-3">
          <Brain size={20} className="text-slate-400" />
        </div>
        <p className="text-[11px] font-medium text-slate-500">
          {report.fast_pathed
            ? "Synthesis was not required — transaction was fast-pathed"
            : hasTriggered
              ? "No synthesis was produced for this transaction"
              : "No signals triggered — synthesis not invoked"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div>
        <h3 className="text-[11px] font-semibold text-s-text">Layer 5 — Cross-Signal Synthesis</h3>
        <p className="text-[9px] text-s-text-tertiary mt-0.5">
          LLM synthesizes all layer evidence into a narrative, exploitation pattern, and intervention plan.
        </p>
      </div>

      {/* Narrative */}
      {brief.narrative && (
        <div className="rounded border border-s-border p-3 bg-white">
          <div className="text-[9px] font-semibold text-s-text-tertiary uppercase mb-1.5">AI Narrative</div>
          <Md className="text-[10px] text-s-text-secondary leading-relaxed">
            {brief.narrative}
          </Md>
        </div>
      )}

      {/* Exploitation tactic */}
      {brief.exploitation_tactic && brief.exploitation_tactic !== "unknown" && (
        <div className="rounded border border-amber-200 bg-amber-50 p-2.5">
          <div className="text-[9px] font-semibold text-amber-700 uppercase mb-0.5">Exploitation Pattern</div>
          <div className="text-[11px] font-bold text-amber-800">
            {brief.exploitation_tactic.replace(/_/g, " ")}
          </div>
        </div>
      )}

      {/* Manipulation indicators */}
      {brief.manipulation_indicators.length > 0 && (
        <div className="rounded border border-s-border p-3 bg-white">
          <div className="text-[9px] font-semibold text-s-text-tertiary uppercase mb-1.5">
            Manipulation Indicators
          </div>
          <div className="space-y-1">
            {brief.manipulation_indicators.map((ind, i) => (
              <div key={i} className="flex items-start gap-1.5 text-[10px] text-s-text-secondary">
                <XCircle size={10} className="text-s-warn mt-0.5 shrink-0" />
                <Md>{ind}</Md>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* What traditional systems missed */}
      {brief.what_traditional_systems_missed && (
        <div className="rounded border border-blue-200 bg-blue-50 p-3">
          <div className="text-[9px] font-semibold text-blue-700 uppercase mb-1">
            What Traditional Systems Missed
          </div>
          <Md className="text-[10px] text-blue-800 leading-relaxed">
            {brief.what_traditional_systems_missed}
          </Md>
        </div>
      )}

      {/* Interventions */}
      {brief.interventions.length > 0 && (
        <div className="rounded border border-s-border p-3 bg-white">
          <div className="text-[9px] font-semibold text-s-text-tertiary uppercase mb-1.5">
            Recommended Interventions
          </div>
          <div className="space-y-1.5">
            {brief.interventions.map((inv, i) => (
              <div key={i} className="rounded border border-s-border p-2 bg-s-surface">
                <div className="flex items-start justify-between gap-2">
                  <Md className="text-[10px] text-s-text font-medium">{inv.reason}</Md>
                  <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded shrink-0 ${
                    inv.urgency === "HIGH"
                      ? "bg-red-100 text-red-700"
                      : inv.urgency === "MEDIUM"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-emerald-100 text-emerald-700"
                  }`}>
                    {inv.urgency}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function InvestigationPanel({ report, onClose }: Props) {
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  const tabContent: Record<TabId, JSX.Element> = {
    overview: <OverviewTab report={report} />,
    rules: <RulesTab report={report} />,
    profiling: <ProfilingTab report={report} />,
    graph: <GraphTab report={report} />,
    comms: <CommsTab report={report} />,
    synthesis: <SynthesisTab report={report} />,
  };

  return (
    <div className="flex flex-col h-full bg-s-panel border border-s-border rounded overflow-hidden">
      {/* Header */}
      <div className="px-3 py-2 border-b border-s-border flex items-center justify-between shrink-0 bg-s-panel-alt">
        <div>
          <h2 className="text-[11px] font-semibold text-s-text">
            Pipeline Trace: {report.transaction_id.slice(0, 10)}...
          </h2>
          <p className="text-[9px] text-s-text-tertiary">
            {report.sender_profile?.name || report.transaction?.sender_id} →{" "}
            {report.receiver_profile?.name || report.transaction?.receiver_id}
            {" • "}${report.transaction?.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </p>
        </div>
        <button
          onClick={onClose}
          className="px-2 py-1 rounded text-[10px] font-medium bg-s-surface border border-s-border text-s-text-secondary hover:bg-s-danger-light hover:text-s-danger transition"
        >
          Close
        </button>
      </div>

      {/* Tab bar */}
      <div className="flex border-b border-s-border shrink-0 bg-s-panel overflow-x-auto">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id;
          const layerRan = tab.layerId ? hasLayerRun(report, tab.layerId) : true;
          const Icon = tab.icon;

          let tabIndicator = "";
          if (tab.layerId) {
            const sigs = getLayerSignals(report, tab.layerId);
            const triggered = sigs.filter((s) => s.triggered).length;
            if (!layerRan) tabIndicator = "—";
            else if (triggered > 0) tabIndicator = `${triggered}`;
            else tabIndicator = "✓";
          }

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 text-[10px] font-medium border-b-2 transition whitespace-nowrap ${
                isActive
                  ? "border-s-accent text-s-accent bg-s-accent-light/30"
                  : "border-transparent text-s-text-secondary hover:text-s-text hover:bg-s-surface"
              }`}
            >
              <Icon size={12} />
              {tab.label}
              {tabIndicator && (
                <span className={`text-[8px] font-mono px-1 py-0.5 rounded ${
                  tabIndicator === "—"
                    ? "bg-slate-100 text-slate-400"
                    : tabIndicator === "✓"
                      ? "bg-emerald-100 text-emerald-600"
                      : "bg-red-100 text-red-600"
                }`}>
                  {tabIndicator}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-3">
        {tabContent[activeTab]}
      </div>
    </div>
  );
}
