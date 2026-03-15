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
      <h3 className="font-semibold text-s-text">Investigation Trace</h3>
      {trace.map((step, i) => (
        <div key={i} className="bg-s-surface rounded p-2">
          <span className="text-s-accent font-mono text-xs">
            {step.tool}
          </span>
          <p className="text-s-muted text-xs mt-1">{step.reasoning}</p>
        </div>
      ))}
    </div>
  );
}
