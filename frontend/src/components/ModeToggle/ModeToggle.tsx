import { setMode } from "../../services/api";

interface Props {
  current: "pipeline" | "agentic";
  onChange: (mode: "pipeline" | "agentic") => void;
}

export default function ModeToggle({ current, onChange }: Props) {
  const toggle = async () => {
    const next = current === "pipeline" ? "agentic" : "pipeline";
    try {
      await setMode(next);
    } catch {
      // backend not ready
    }
    onChange(next);
  };

  return (
    <button
      onClick={toggle}
      className="px-3 py-1 rounded text-xs font-medium bg-s-panel border border-s-border hover:border-s-accent transition text-s-text-secondary"
    >
      Mode: {current === "pipeline" ? "Pipeline" : "Agent"}
    </button>
  );
}
