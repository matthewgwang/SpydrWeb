import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";
import type { LayerSignal } from "../../types";

interface Props {
  signals: LayerSignal[];
  recipientRiskScore?: number;
}

const AXES = [
  { key: "rules", label: "Rules", layerId: 1 },
  { key: "behavioral", label: "Behavioral", layerId: 2 },
  { key: "relationship", label: "Relationship", layerId: 3 },
  { key: "communication", label: "Communication", layerId: 4 },
  { key: "recipient", label: "Recipient", layerId: -1 },
];

export default function ThreatRadar({ signals, recipientRiskScore = 0 }: Props) {
  const signalMap = new Map(signals.map((s) => [s.layer_id, s]));

  const data = AXES.map((axis) => {
    if (axis.layerId === -1) {
      return { axis: axis.label, value: Math.round(recipientRiskScore * 100) };
    }
    const signal = signalMap.get(axis.layerId);
    return { axis: axis.label, value: signal ? Math.round(signal.confidence * 100) : 0 };
  });

  return (
    <div>
      <h3 className="text-[10px] font-semibold text-s-muted uppercase tracking-wide mb-1">
        Threat Vectors
      </h3>
      <ResponsiveContainer width="100%" height={160}>
        <RadarChart data={data} cx="50%" cy="50%" outerRadius="68%">
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fill: "#6b7280", fontSize: 9 }}
            tickLine={false}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={false}
            axisLine={false}
          />
          <Radar
            name="Threat"
            dataKey="value"
            stroke="#2c5282"
            fill="#2c5282"
            fillOpacity={0.15}
            strokeWidth={1.5}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
