import type { LayerSignal } from "../../types";

interface Props {
  score: number;
  signals?: LayerSignal[];
}

export default function ConfidenceScore({ score, signals = [] }: Props) {
  const pct = Math.round(score * 100);
  const color =
    score >= 0.85
      ? "text-sentinel-danger"
      : score >= 0.5
        ? "text-sentinel-warn"
        : "text-sentinel-safe";

  return (
    <div className="space-y-1">
      <div className={`text-2xl font-bold ${color}`}>{pct}%</div>
      <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-current rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
      {signals.filter((s) => s.triggered).length > 0 && (
        <div className="text-xs text-gray-500 space-y-0.5">
          {signals
            .filter((s) => s.triggered)
            .map((s) => (
              <div key={s.layer_id}>
                L{s.layer_id}: {s.explanation.slice(0, 80)}
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
