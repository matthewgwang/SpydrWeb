import { useState } from "react";
import type { TimelineEntry } from "../../types";

interface Props {
  entries: TimelineEntry[];
}

type DotColor = "blue" | "amber" | "red" | "gray";

function classifyEvent(entry: TimelineEntry): DotColor {
  const type = entry.event_type.toLowerCase();
  if (
    type === "transaction" || type === "transfer" || type === "payment" ||
    entry.significance === "critical"
  ) return "red";
  if (
    type === "support_chat" || type === "phone_call" ||
    type === "branch_visit" || type === "email_change"
  ) return "amber";
  if (type.includes("missing") || type.includes("absence")) return "gray";
  return "blue";
}

const DOT_STYLES: Record<DotColor, { fill: string; label: string }> = {
  blue: { fill: "#2c5282", label: "Account/Device" },
  amber: { fill: "#92400e", label: "Communication" },
  red: { fill: "#9b2c2c", label: "Flagged Txn" },
  gray: { fill: "#9ca3af", label: "Missing" },
};

function formatTime(ts: string): string {
  try {
    return new Date(ts).toLocaleTimeString("en-US", {
      hour12: false, hour: "2-digit", minute: "2-digit",
    });
  } catch { return ts; }
}

export default function EventTimeline({ entries }: Props) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (entries.length === 0) return null;

  return (
    <div>
      <h3 className="text-[10px] font-semibold text-s-muted uppercase tracking-wide mb-2">
        Event Timeline
      </h3>

      <div className="relative overflow-x-auto pb-1">
        <div className="flex items-center min-w-max px-1">
          <div className="absolute left-1 right-1 top-[9px] h-px bg-s-border" />

          {entries.map((entry, i) => {
            const color = classifyEvent(entry);
            const style = DOT_STYLES[color];

            return (
              <div
                key={i}
                className="relative flex flex-col items-center"
                style={{ minWidth: entries.length > 8 ? 26 : 34 }}
                onMouseEnter={() => setHoveredIdx(i)}
                onMouseLeave={() => setHoveredIdx(null)}
              >
                <div
                  className="w-[7px] h-[7px] rounded-full relative z-10 cursor-pointer"
                  style={{
                    backgroundColor: style.fill,
                    transform: hoveredIdx === i ? "scale(1.5)" : "scale(1)",
                    transition: "transform 0.15s",
                  }}
                />
                <span className="font-mono text-[7px] text-s-text-tertiary mt-1">
                  {formatTime(entry.timestamp)}
                </span>

                {hoveredIdx === i && (
                  <div className="absolute bottom-full mb-1.5 left-1/2 -translate-x-1/2 bg-s-panel border border-s-border rounded px-2 py-1 text-[10px] z-20 whitespace-nowrap shadow-sm">
                    <div className="font-medium text-s-text">
                      {entry.event_type.replace(/_/g, " ")}
                    </div>
                    <div className="text-s-muted">{entry.description}</div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-3 mt-1 text-[8px] text-s-text-tertiary">
        {Object.entries(DOT_STYLES).map(([key, style]) => (
          <span key={key} className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: style.fill }} />
            {style.label}
          </span>
        ))}
      </div>
    </div>
  );
}
