interface TraceStep {
  tool: string;
  reasoning: string;
  result_summary: string;
}

interface Props {
  trace: TraceStep[];
}

export default function InvestigationTrace({ trace }: Props) {
  return (
    <div className="space-y-2 text-sm">
      <h3 className="font-semibold">Investigation Trace</h3>
      {trace.map((step, i) => (
        <div key={i} className="bg-sentinel-panel rounded p-2">
          <span className="text-sentinel-accent font-mono text-xs">
            {step.tool}
          </span>
          <p className="text-gray-400 text-xs mt-1">{step.reasoning}</p>
        </div>
      ))}
    </div>
  );
}
