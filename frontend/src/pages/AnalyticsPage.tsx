import { useState, useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  Activity,
  Zap,
  AlertTriangle,
  Layers,
  GitBranch,
  Shield,
  Clock,
  Database,
} from "lucide-react";
import { useGraph } from "../hooks/useGraph";
import type { TransactionFeedItem, AlertFeedItem } from "../types";

interface AnalyticsSummary {
  totals: {
    reports: number;
    fast_pathed: number;
    full_pipeline: number;
    fast_path_rate: number;
  };
  layer_triggers: Record<string, number>;
  action_counts: Record<string, number>;
  score_distribution: number[];
  graph: { nodes: number; edges: number; flagged: number };
  recent_scores: { id: string; score: number; fast_pathed: boolean; action: string }[];
  fast_path_batches: { batch: string; fastPathed: number; fullPipeline: number }[];
}

function ChartCard({
  title,
  subtitle,
  icon: Icon,
  children,
  className = "",
}: {
  title: string;
  subtitle: string;
  icon: typeof Activity;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-s-panel rounded border border-s-border flex flex-col ${className}`}>
      <div className="flex items-center gap-2 px-3 py-2 border-b border-s-border">
        <Icon size={12} className="text-s-accent" />
        <div>
          <h3 className="text-[11px] font-semibold text-s-text">{title}</h3>
          <p className="text-[9px] text-s-text-tertiary">{subtitle}</p>
        </div>
      </div>
      <div className="flex-1 p-3">{children}</div>
    </div>
  );
}

function StatCard({
  label,
  value,
  change,
  trend,
}: {
  label: string;
  value: string;
  change?: string;
  trend?: "up" | "down" | "flat";
}) {
  const trendColor =
    trend === "up" ? "text-s-danger" : trend === "down" ? "text-s-safe" : "text-s-muted";
  return (
    <div className="bg-s-panel rounded border border-s-border px-3 py-2">
      <div className="text-[9px] text-s-text-tertiary uppercase tracking-wide">{label}</div>
      <div className="text-lg font-bold font-mono text-s-text mt-0.5">{value}</div>
      {change && (
        <div className={`text-[9px] font-medium mt-0.5 ${trendColor}`}>{change}</div>
      )}
    </div>
  );
}

const LAYER_NAMES: Record<number, string> = {
  1: "L1 Rules",
  2: "L2 Profile",
  3: "L3 Graph",
  4: "L4 Comms",
  5: "L5 Synth",
};

const LAYER_LATENCY_ESTIMATE: Record<number, number> = {
  1: 2,
  2: 8,
  3: 15,
  4: 120,
  5: 340,
};

interface OutletCtx {
  transactions: TransactionFeedItem[];
  alerts: AlertFeedItem[];
  mode: "pipeline" | "agentic";
  recentAlertTxIds: Set<string>;
}

export default function AnalyticsPage() {
  const { transactions, alerts } = useOutletContext<OutletCtx>();
  const { graph } = useGraph();
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);

  useEffect(() => {
    const fetchAnalytics = () => {
      fetch("/api/analytics/summary")
        .then((r) => r.json())
        .then(setAnalytics)
        .catch(() => {});
    };
    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 10000);
    return () => clearInterval(interval);
  }, []);

  const layerPerfData = analytics
    ? Object.entries(analytics.layer_triggers).map(([id, triggers]) => ({
        layer: LAYER_NAMES[Number(id)] || `L${id}`,
        latency: LAYER_LATENCY_ESTIMATE[Number(id)] || 10,
        triggers,
      }))
    : [];

  const radarData = analytics
    ? [
        { axis: "Rules", value: Math.min(analytics.layer_triggers[1] || 0, 100) },
        { axis: "Behavioral", value: Math.min(analytics.layer_triggers[2] || 0, 100) },
        { axis: "Graph", value: Math.min(analytics.layer_triggers[3] || 0, 100) },
        { axis: "Communication", value: Math.min(analytics.layer_triggers[4] || 0, 100) },
        { axis: "Synthesis", value: Math.min(analytics.layer_triggers[5] || 0, 100) },
      ]
    : [];

  const fraudTypeData = analytics
    ? [
        { name: "Hold", value: analytics.action_counts.hold || 0, color: "#9b2c2c" },
        { name: "Refer", value: analytics.action_counts.refer || 0, color: "#92400e" },
        { name: "Delay", value: analytics.action_counts.delay || 0, color: "#553c9a" },
        { name: "Allow", value: analytics.action_counts.allow || 0, color: "#276749" },
      ]
    : [];

  const scoreChartData = analytics
    ? analytics.recent_scores.map((s, i) => ({
        t: i,
        score: Math.round(s.score * 100),
        fastPathed: s.fast_pathed ? 1 : 0,
      }))
    : [];

  const scoreDistData = analytics
    ? analytics.score_distribution.map((count, i) => ({
        range: `${i * 10}-${i * 10 + 9}`,
        count,
      }))
    : [];

  return (
    <div className="h-full overflow-y-auto p-3 space-y-3">
      {/* Top Stats Row */}
      <div className="grid grid-cols-6 gap-2">
        <StatCard label="Total Events" value={String(transactions.length || "—")} />
        <StatCard
          label="Active Alerts"
          value={String(alerts.length || "—")}
          change={alerts.length > 0 ? `${alerts.length} flagged` : undefined}
          trend={alerts.length > 0 ? "up" : "flat"}
        />
        <StatCard label="Graph Nodes" value={String(graph.nodes.length || "—")} />
        <StatCard label="Graph Edges" value={String(graph.edges.length || "—")} />
        <StatCard
          label="Fast-Path Rate"
          value={analytics ? `${analytics.totals.fast_path_rate}%` : "—"}
          change={analytics ? `${analytics.totals.fast_pathed} of ${analytics.totals.reports}` : undefined}
          trend="flat"
        />
        <StatCard
          label="Total Reports"
          value={analytics ? String(analytics.totals.reports) : "—"}
          change={analytics ? `${analytics.totals.full_pipeline} full pipeline` : undefined}
          trend="flat"
        />
      </div>

      {/* Row 1 — Score Trend + Score Distribution */}
      <div className="grid grid-cols-2 gap-3" style={{ minHeight: 240 }}>
        <ChartCard
          title="Risk Score Trend"
          subtitle="Recent transaction confidence scores"
          icon={Activity}
        >
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={scoreChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="t" tick={{ fontSize: 9, fill: "#9ca3af" }} />
              <YAxis tick={{ fontSize: 9, fill: "#9ca3af" }} width={30} domain={[0, 100]} />
              <Tooltip contentStyle={{ fontSize: 10 }} />
              <Area type="monotone" dataKey="score" stroke="#2c5282" fill="#2c5282" fillOpacity={0.15} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Score Distribution"
          subtitle="Risk score frequency buckets"
          icon={Zap}
        >
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={scoreDistData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="range" tick={{ fontSize: 8, fill: "#9ca3af" }} />
              <YAxis tick={{ fontSize: 9, fill: "#9ca3af" }} width={30} />
              <Tooltip contentStyle={{ fontSize: 10 }} />
              <Bar dataKey="count" fill="#2c5282" opacity={0.7} radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 2 — Layer Triggers + Layer Performance */}
      <div className="grid grid-cols-2 gap-3" style={{ minHeight: 240 }}>
        <ChartCard
          title="Layer Trigger Counts"
          subtitle="Signals triggered per detection layer"
          icon={AlertTriangle}
        >
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={layerPerfData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="layer" tick={{ fontSize: 9, fill: "#9ca3af" }} />
              <YAxis tick={{ fontSize: 9, fill: "#9ca3af" }} width={30} />
              <Tooltip contentStyle={{ fontSize: 10 }} />
              <Bar dataKey="triggers" fill="#553c9a" opacity={0.7} radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Layer Performance"
          subtitle="Latency (ms) and trigger count by layer"
          icon={Layers}
        >
          <div className="space-y-1.5 mt-1">
            {layerPerfData.map((l) => (
              <div key={l.layer} className="flex items-center gap-2 text-[10px]">
                <span className="w-16 text-s-text-secondary font-medium">{l.layer}</span>
                <div className="flex-1 h-3 bg-s-surface rounded overflow-hidden flex">
                  <div
                    className="h-full bg-s-accent/60 rounded"
                    style={{ width: `${Math.min((l.latency / 400) * 100, 100)}%` }}
                  />
                </div>
                <span className="w-12 text-right font-mono text-s-text-tertiary">
                  {l.latency}ms
                </span>
                <span className="w-10 text-right font-mono text-s-muted">
                  {l.triggers}
                </span>
              </div>
            ))}
            <div className="flex items-center gap-2 text-[8px] text-s-text-tertiary mt-2 pt-1 border-t border-s-border">
              <span className="w-16" />
              <span className="flex-1">Latency</span>
              <span className="w-12 text-right">ms</span>
              <span className="w-10 text-right">triggers</span>
            </div>
          </div>
        </ChartCard>
      </div>

      {/* Row 3 — Threat Vectors + Action Distribution + Fast Path */}
      <div className="grid grid-cols-3 gap-3" style={{ minHeight: 240 }}>
        <ChartCard
          title="Threat Vectors"
          subtitle="Layer trigger intensity"
          icon={Shield}
        >
          <ResponsiveContainer width="100%" height={180}>
            <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="68%">
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="axis" tick={{ fill: "#6b7280", fontSize: 9 }} tickLine={false} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
              <Radar dataKey="value" stroke="#2c5282" fill="#2c5282" fillOpacity={0.15} strokeWidth={1.5} />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Action Distribution"
          subtitle="Pipeline recommended actions"
          icon={Database}
        >
          <div className="flex items-center gap-3">
            <ResponsiveContainer width={120} height={120}>
              <PieChart>
                <Pie
                  data={fraudTypeData}
                  cx="50%"
                  cy="50%"
                  innerRadius={30}
                  outerRadius={55}
                  dataKey="value"
                  stroke="none"
                >
                  {fraudTypeData.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-1">
              {fraudTypeData.map((d) => (
                <div key={d.name} className="flex items-center gap-1.5 text-[9px]">
                  <span className="w-2 h-2 rounded-sm shrink-0" style={{ backgroundColor: d.color }} />
                  <span className="text-s-text-secondary">{d.name}</span>
                  <span className="font-mono text-s-muted ml-auto">{d.value}</span>
                </div>
              ))}
            </div>
          </div>
        </ChartCard>

        <ChartCard
          title="Fast-Path Filter"
          subtitle="Transactions skipping full pipeline"
          icon={Clock}
        >
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={analytics?.fast_path_batches || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="batch" tick={{ fontSize: 8, fill: "#9ca3af" }} />
              <YAxis tick={{ fontSize: 9, fill: "#9ca3af" }} width={25} />
              <Tooltip contentStyle={{ fontSize: 10 }} />
              <Bar dataKey="fastPathed" fill="#276749" opacity={0.6} name="Fast-pathed" />
              <Bar dataKey="fullPipeline" fill="#9b2c2c" opacity={0.6} name="Full pipeline" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 4 — Graph Metrics + Event Log */}
      <div className="grid grid-cols-2 gap-3" style={{ minHeight: 240 }}>
        <ChartCard
          title="Graph Summary"
          subtitle="Entity relationship network stats"
          icon={GitBranch}
        >
          <div className="grid grid-cols-3 gap-3 mt-2">
            <div className="bg-s-surface rounded p-3 border border-s-border text-center">
              <div className="text-lg font-bold font-mono text-s-accent">
                {analytics?.graph.nodes || graph.nodes.length}
              </div>
              <div className="text-[8px] text-s-text-tertiary uppercase mt-0.5">Nodes</div>
            </div>
            <div className="bg-s-surface rounded p-3 border border-s-border text-center">
              <div className="text-lg font-bold font-mono text-s-accent">
                {analytics?.graph.edges || graph.edges.length}
              </div>
              <div className="text-[8px] text-s-text-tertiary uppercase mt-0.5">Edges</div>
            </div>
            <div className="bg-s-surface rounded p-3 border border-s-border text-center">
              <div className="text-lg font-bold font-mono text-s-danger">
                {analytics?.graph.flagged || 0}
              </div>
              <div className="text-[8px] text-s-text-tertiary uppercase mt-0.5">Flagged</div>
            </div>
          </div>
          <div className="mt-4 rounded border border-s-border p-2.5 bg-s-surface">
            <div className="text-[9px] font-semibold text-s-text-tertiary uppercase mb-1">Pipeline Summary</div>
            <div className="grid grid-cols-2 gap-2 text-[9px]">
              <div>
                <span className="text-s-text-tertiary">Fast-pathed:</span>{" "}
                <span className="font-mono text-s-text font-medium">{analytics?.totals.fast_pathed || 0}</span>
              </div>
              <div>
                <span className="text-s-text-tertiary">Full pipeline:</span>{" "}
                <span className="font-mono text-s-text font-medium">{analytics?.totals.full_pipeline || 0}</span>
              </div>
              <div>
                <span className="text-s-text-tertiary">Hold:</span>{" "}
                <span className="font-mono text-s-danger font-medium">{analytics?.action_counts.hold || 0}</span>
              </div>
              <div>
                <span className="text-s-text-tertiary">Refer:</span>{" "}
                <span className="font-mono text-s-danger font-medium">{analytics?.action_counts.refer || 0}</span>
              </div>
            </div>
          </div>
        </ChartCard>

        <ChartCard
          title="Recent Event Log"
          subtitle="L0 append-only event stream"
          icon={Activity}
        >
          <div className="space-y-px overflow-y-auto max-h-[180px]">
            {transactions.length === 0 && (
              <p className="text-[10px] text-s-text-tertiary text-center py-6">
                No events yet — start the demo to see the stream
              </p>
            )}
            {transactions.slice(0, 30).map((tx) => (
              <div
                key={tx.id}
                className="flex items-center justify-between px-2 py-1 rounded hover:bg-s-surface text-[10px] transition"
              >
                <span className="font-mono text-s-text-tertiary w-16 shrink-0">
                  {new Date(tx.timestamp).toLocaleTimeString("en-US", {
                    hour12: false,
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  })}
                </span>
                <span className="text-s-text-secondary flex-1 px-2">
                  {tx.sender_name || tx.sender_id.slice(-4)} → {tx.receiver_name || tx.receiver_id.slice(-4)}
                </span>
                <span className="font-mono text-s-text-secondary w-16 text-right">
                  ${tx.amount.toLocaleString()}
                </span>
                <span className={`w-12 text-right font-mono text-[9px] ${
                  tx.status === "flagged" || tx.status === "hold" || tx.status === "refer"
                    ? "text-s-danger"
                    : tx.status === "delay"
                      ? "text-s-warn"
                      : "text-s-safe"
                }`}>
                  {tx.status}
                </span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>
    </div>
  );
}
