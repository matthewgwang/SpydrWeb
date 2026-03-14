import { setMode } from "../../services/api";

interface Props {
  current: "pipeline" | "agentic";
  onChange: (mode: "pipeline" | "agentic") => void;
}

export default function ModeToggle({ current, onChange }: Props) {
  const toggle = async () => {
    const next = current === "pipeline" ? "agentic" : "pipeline";
    await setMode(next);
    onChange(next);
  };

  return (
    <button
      onClick={toggle}
      className="px-3 py-1 rounded text-xs font-medium bg-sentinel-panel border border-sentinel-border hover:border-sentinel-accent transition"
    >
      Mode: {current === "pipeline" ? "Pipeline" : "Agent"}
    </button>
  );
}
