import { useEffect, useState } from "react";
import { ChevronRight } from "lucide-react";
import type { AlertBundle, CaseReport } from "../../types";
import { getAlertBundles } from "../../services/api";

const FRAUD_LABELS: Record<string, string> = {
  ELDER_EXPLOITATION: "Elder Exploitation",
  ACCOUNT_TAKEOVER: "Account Takeover",
  MULE_NETWORK: "Mule Network",
  CARD_TESTING: "Card Testing",
  UNKNOWN: "Unknown",
};

const FRAUD_TAG: Record<string, string> = {
  ELDER_EXPLOITATION: "tag-danger",
  ACCOUNT_TAKEOVER: "tag-warn",
  MULE_NETWORK: "tag-accent",
  CARD_TESTING: "tag-warn",
  UNKNOWN: "tag-neutral",
};

interface Props {
  onSelectReport: (report: CaseReport) => void;
  refreshTrigger?: number;
}

export default function AlertQueue({ onSelectReport, refreshTrigger }: Props) {
  const [bundles, setBundles] = useState<AlertBundle[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    getAlertBundles().then(setBundles).catch(() => {});
  }, [refreshTrigger]);

  return (
    <div className="border-t border-s-border">
      <div className="px-3 py-1.5 flex items-center justify-between">
        <h3 className="text-[10px] font-semibold text-s-danger uppercase tracking-wide">
          Alert Queue
        </h3>
        {bundles.length > 0 && (
          <span className="tag tag-danger text-[8px]">{bundles.length}</span>
        )}
      </div>

      <div className="px-1.5 pb-1.5 space-y-0.5 max-h-48 overflow-y-auto">
        {bundles.length === 0 && (
          <p className="text-[10px] text-s-text-tertiary text-center py-2">
            No bundled alerts
          </p>
        )}

        {bundles.map((b) => {
          const isOpen = expandedId === b.bundle_id;
          const label = FRAUD_LABELS[b.primary_fraud_type] || b.primary_fraud_type;
          const tagClass = FRAUD_TAG[b.primary_fraud_type] || "tag-neutral";

          return (
            <div key={b.bundle_id} className="rounded border border-s-border bg-s-panel">
              <button
                onClick={() => setExpandedId(isOpen ? null : b.bundle_id)}
                className="w-full text-left px-2 py-1.5 hover:bg-s-surface transition flex items-center gap-1.5"
              >
                <ChevronRight
                  size={10}
                  className={`text-s-muted transition-transform ${isOpen ? "rotate-90" : ""}`}
                />
                <span className={`tag ${tagClass} text-[8px]`}>{label}</span>
                <span className="flex-1" />
                <span className="text-[9px] font-mono text-s-text-tertiary">
                  {b.case_reports.length}
                </span>
              </button>

              {isOpen && (
                <div className="border-t border-s-border px-2 py-1 space-y-0.5">
                  {b.case_reports.map((r) => (
                    <button
                      key={r.id}
                      onClick={() => onSelectReport(r)}
                      className="w-full text-left px-1.5 py-1 rounded hover:bg-s-surface transition text-[10px] flex items-center justify-between"
                    >
                      <span className="font-mono text-s-text-secondary">
                        #{r.id.slice(-6)}
                      </span>
                      <span
                        className={`font-mono font-medium ${
                          r.confidence_score >= 0.8 ? "text-s-danger" : "text-s-warn"
                        }`}
                      >
                        {Math.round(r.confidence_score * 100)}%
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
