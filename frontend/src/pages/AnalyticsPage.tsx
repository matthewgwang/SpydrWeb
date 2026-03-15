import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
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
import { useTransactionFeed } from "../hooks/useTransactionFeed";
import { useGraph } from "../hooks/useGraph";

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

const EVENT_STREAM_DATA = Array.from({ length: 30 }, (_, i) => ({
  t: `${i}s`,
  transactions: Math.floor(Math.random() * 40 + 10),
  logins: Math.floor(Math.random() * 15 + 2),
  chats: Math.floor(Math.random() * 8),
  device_changes: Math.floor(Math.random() * 3),
}));

const VELOCITY_DATA = Array.from({ length: 24 }, (_, i) => ({
  hour: `${String(i).padStart(2, "0")}:00`,
  current: Math.floor(Math.random() * 30 + 5),
  baseline: 18,
}));

const ANOMALY_DATA = Array.from({ length: 20 }, (_, i) => ({
  tick: i,
  rules: Math.floor(Math.random() * 5),
  behavioral: Math.floor(Math.random() * 4),
  graph: Math.floor(Math.random() * 3),
  communication: Math.floor(Math.random() * 2),
}));

const LAYER_PERF_DATA = [
  { layer: "L1 Rules", latency: 2, triggers: 45 },
  { layer: "L2 Profile", latency: 8, triggers: 28 },
  { layer: "L3 Graph", latency: 15, triggers: 19 },
  { layer: "L4 Comms", latency: 120, triggers: 12 },
  { layer: "L5 Synth", latency: 340, triggers: 8 },
];

const RADAR_DATA = [
  { axis: "Rules", value: 85 },
  { axis: "Behavioral", value: 62 },
  { axis: "Relationship", value: 48 },
  { axis: "Communication", value: 71 },
  { axis: "Recipient", value: 39 },
];

const FRAUD_TYPE_DATA = [
  { name: "Elder Exploit.", value: 34, color: "#9b2c2c" },
  { name: "Account Takeover", value: 22, color: "#92400e" },
  { name: "Mule Network", value: 18, color: "#2c5282" },
  { name: "Card Testing", value: 11, color: "#553c9a" },
  { name: "Clean", value: 215, color: "#276749" },
];

const FAST_PATH_DATA = Array.from({ length: 15 }, (_, i) => ({
  batch: `B${i + 1}`,
  fastPathed: Math.floor(Math.random() * 80 + 60),
  fullPipeline: Math.floor(Math.random() * 30 + 5),
}));

const GRAPH_METRICS_DATA = Array.from({ length: 20 }, (_, i) => ({
  t: i,
  nodes: 40 + i * 3 + Math.floor(Math.random() * 5),
  edges: 80 + i * 5 + Math.floor(Math.random() * 10),
  entropy: +(Math.random() * 0.4 + 0.3).toFixed(2),
}));

export default function AnalyticsPage() {
  const { transactions, alerts } = useTransactionFeed();
  const { graph } = useGraph();

  return (
    <div className="h-full overflow-y-auto p-3 space-y-3">
      {/* Top Stats Row */}
      <div className="grid grid-cols-6 gap-2">
        <StatCard label="Total Events" value={String(transactions.length || "—")} />
        <StatCard label="Active Alerts" value={String(alerts.length || "—")} change="+3 last hr" trend="up" />
        <StatCard label="Graph Nodes" value={String(graph.nodes.length || "—")} />
        <StatCard label="Graph Edges" value={String(graph.edges.length || "—")} />
        <StatCard label="Fast-Path Rate" value="78%" change="-2% vs avg" trend="flat" />
        <StatCard label="Avg Latency" value="4.2ms" change="L1 only" trend="flat" />
      </div>

      {/* Row 1 — Event Stream + Velocity */}
      <div className="grid grid-cols-2 gap-3" style={{ minHeight: 240 }}>
        <ChartCard
          title="Event Stream"
          subtitle="L0/L1 multi-vector event feed by type"
          icon={Activity}
        >
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={EVENT_STREAM_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="t" tick={{ fontSize: 9, fill: "#9ca3af" }} />
              <YAxis tick={{ fontSize: 9, fill: "#9ca3af" }} width={30} />
              <Tooltip contentStyle={{ fontSize: 10 }} />
              <Area type="monotone" dataKey="transactions" stackId="1" stroke="#2c5282" fill="#2c5282" fillOpacity={0.3} />
              <Area type="monotone" dataKey="logins" stackId="1" stroke="#553c9a" fill="#553c9a" fillOpacity={0.2} />
              <Area type="monotone" dataKey="chats" stackId="1" stroke="#92400e" fill="#92400e" fillOpacity={0.15} />
              <Area type="monotone" dataKey="device_changes" stackId="1" stroke="#9b2c2c" fill="#9b2c2c" fillOpacity={0.15} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Data Stream Velocity"
          subtitle="Transactions/sec vs baseline"
          icon={Zap}
        >
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={VELOCITY_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="hour" tick={{ fontSize: 9, fill: "#9ca3af" }} interval={3} />
              <YAxis tick={{ fontSize: 9, fill: "#9ca3af" }} width={30} />
              <Tooltip contentStyle={{ fontSize: 10 }} />
              <Area type="monotone" dataKey="baseline" stroke="#9ca3af" fill="none" strokeDasharray="4 3" />
              <Area type="monotone" dataKey="current" stroke="#2c5282" fill="#2c5282" fillOpacity={0.15} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Row 2 — Anomaly Frequency + Layer Performance */}
      <div className="grid grid-cols-2 gap-3" style={{ minHeight: 240 }}>
        <ChartCard
          title="Anomaly Frequency"
          subtitle="Layer triggers over time"
          icon={AlertTriangle}
        >
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={ANOMALY_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="tick" tick={{ fontSize: 9, fill: "#9ca3af" }} />
              <YAxis tick={{ fontSize: 9, fill: "#9ca3af" }} width={25} />
              <Tooltip contentStyle={{ fontSize: 10 }} />
              <Bar dataKey="rules" stackId="a" fill="#2c5282" radius={[0, 0, 0, 0]} />
              <Bar dataKey="behavioral" stackId="a" fill="#553c9a" />
              <Bar dataKey="graph" stackId="a" fill="#92400e" />
              <Bar dataKey="communication" stackId="a" fill="#9b2c2c" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Layer Performance"
          subtitle="Latency (ms) and trigger count by layer"
          icon={Layers}
        >
          <div className="space-y-1.5 mt-1">
            {LAYER_PERF_DATA.map((l) => (
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

      {/* Row 3 — Threat Vectors + Fraud Distribution + Fast Path */}
      <div className="grid grid-cols-3 gap-3" style={{ minHeight: 240 }}>
        <ChartCard
          title="Threat Vectors"
          subtitle="Aggregate signal strength"
          icon={Shield}
        >
          <ResponsiveContainer width="100%" height={180}>
            <RadarChart data={RADAR_DATA} cx="50%" cy="50%" outerRadius="68%">
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="axis" tick={{ fill: "#6b7280", fontSize: 9 }} tickLine={false} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
              <Radar dataKey="value" stroke="#2c5282" fill="#2c5282" fillOpacity={0.15} strokeWidth={1.5} />
            </RadarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Fraud Type Distribution"
          subtitle="Classification breakdown"
          icon={Database}
        >
          <div className="flex items-center gap-3">
            <ResponsiveContainer width={120} height={120}>
              <PieChart>
                <Pie
                  data={FRAUD_TYPE_DATA}
                  cx="50%"
                  cy="50%"
                  innerRadius={30}
                  outerRadius={55}
                  dataKey="value"
                  stroke="none"
                >
                  {FRAUD_TYPE_DATA.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="space-y-1">
              {FRAUD_TYPE_DATA.map((d) => (
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
            <BarChart data={FAST_PATH_DATA}>
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
          title="Graph Growth"
          subtitle="Nodes, edges, and cluster entropy over time"
          icon={GitBranch}
        >
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={GRAPH_METRICS_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="t" tick={{ fontSize: 9, fill: "#9ca3af" }} />
              <YAxis tick={{ fontSize: 9, fill: "#9ca3af" }} width={30} />
              <Tooltip contentStyle={{ fontSize: 10 }} />
              <Line type="monotone" dataKey="nodes" stroke="#2c5282" strokeWidth={1.5} dot={false} />
              <Line type="monotone" dataKey="edges" stroke="#553c9a" strokeWidth={1.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
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
                  {tx.sender_id.slice(-4)} → {tx.receiver_id.slice(-4)}
                </span>
                <span className="font-mono text-s-text-secondary w-16 text-right">
                  ${tx.amount.toLocaleString()}
                </span>
                <span className={`w-12 text-right font-mono text-[9px] ${
                  tx.status === "flagged" ? "text-s-danger" : "text-s-safe"
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
