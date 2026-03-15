import { useState } from "react";
import { Play, X, Loader2 } from "lucide-react";
import type { CaseReport } from "../../types";

interface Props {
  onStart: () => void;
  onInject: (scenario: string) => Promise<CaseReport | null>;
  onClose: () => void;
}

const SCENARIOS = [
  {
    id: "elder_exploitation",
    label: "Elder Exploitation",
    description: "Family coercion of elderly customer",
  },
  {
    id: "account_takeover",
    label: "Account Takeover",
    description: "Credential theft, unauthorized access",
  },
  {
    id: "mule_network",
    label: "Mule Network",
    description: "Laundering through mule accounts",
  },
  {
    id: "card_testing",
    label: "Card Testing",
    description: "Rapid small txns, stolen cards",
  },
];

export default function DemoControls({ onStart, onInject, onClose }: Props) {
  const [demoStarted, setDemoStarted] = useState(false);
  const [injecting, setInjecting] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<string | null>(null);

  const handleStart = () => {
    onStart();
    setDemoStarted(true);
    setLastResult("Stream started");
    setTimeout(() => setLastResult(null), 3000);
  };

  const handleInject = async (scenarioId: string) => {
    setInjecting(scenarioId);
    setLastResult(null);
    try {
      const result = await onInject(scenarioId);
      setLastResult(
        result ? `Case #${result.id.slice(-6)} created` : "Injected",
      );
    } catch {
      setLastResult("Failed — backend not ready");
    } finally {
      setInjecting(null);
    }
  };

  return (
    <div className="bg-s-panel-alt border-b border-s-border px-4 py-2">
      <div className="flex items-center gap-3">
        <button
          onClick={handleStart}
          disabled={demoStarted}
          className={`flex items-center gap-1 px-2.5 py-1 rounded text-[11px] font-medium transition ${
            demoStarted
              ? "bg-s-safe-light text-s-safe border border-s-safe/20"
              : "bg-s-accent text-white hover:bg-s-accent/90"
          }`}
        >
          {demoStarted ? (
            <>
              <span className="w-1.5 h-1.5 rounded-full bg-s-safe" />
              Active
            </>
          ) : (
            <>
              <Play size={10} />
              Start
            </>
          )}
        </button>

        <div className="h-5 w-px bg-s-border" />

        <span className="text-[10px] text-s-text-tertiary">Inject:</span>

        {SCENARIOS.map((sc) => (
          <button
            key={sc.id}
            onClick={() => handleInject(sc.id)}
            disabled={injecting !== null}
            title={sc.description}
            className="px-2 py-0.5 rounded text-[10px] font-medium text-s-text-secondary border border-s-border hover:bg-s-surface hover:border-s-accent/30 transition"
          >
            {injecting === sc.id ? (
              <Loader2 size={10} className="animate-spin inline mr-1" />
            ) : null}
            {sc.label}
          </button>
        ))}

        <div className="flex-1" />

        {lastResult && (
          <span className="text-[10px] text-s-safe font-medium">
            {lastResult}
          </span>
        )}

        <button
          onClick={onClose}
          className="p-0.5 rounded hover:bg-s-surface text-s-muted transition"
        >
          <X size={12} />
        </button>
      </div>
    </div>
  );
}
