import { useState } from "react";
import {
  MessageSquare, Smartphone, Clock, Building2, Link2,
  Phone, Zap, CheckCircle2,
} from "lucide-react";
import type { CaseReport, InterventionRecommendation } from "../../types";
import ThreatRadar from "./ThreatRadar";
import EventTimeline from "./EventTimeline";
import AccountProfile from "../AccountProfile/AccountProfile";

interface Props {
  report: CaseReport | null;
  onAction: (action: string) => void;
}

const TACTIC_LABELS: Record<string, string> = {
  family_coercion: "Family Coercion",
  romance_scam: "Romance Scam",
  authority_impersonation: "Authority Impersonation",
  phone_coaching: "Phone Coaching",
  unknown: "Unknown Tactic",
};

const TACTIC_TAG: Record<string, string> = {
  family_coercion: "tag-warn",
  romance_scam: "tag-danger",
  authority_impersonation: "tag-accent",
  phone_coaching: "tag-warn",
  unknown: "tag-neutral",
};

const INDICATOR_ICONS: Record<string, typeof MessageSquare> = {
  coached: MessageSquare,
  language: MessageSquare,
  vocabulary: MessageSquare,
  chat: MessageSquare,
  device: Smartphone,
  routine: Clock,
  balance: Clock,
  branch: Building2,
  companion: Building2,
  recipient: Link2,
  phone: Phone,
};

function getIndicatorIcon(text: string) {
  const lower = text.toLowerCase();
  for (const [key, Icon] of Object.entries(INDICATOR_ICONS)) {
    if (lower.includes(key)) return Icon;
  }
  return Zap;
}

function RiskGauge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const circumference = 2 * Math.PI * 32;
  const filled = (pct / 100) * circumference;
  const color = pct >= 80 ? "#9b2c2c" : pct >= 50 ? "#92400e" : "#276749";

  return (
    <div className="flex items-center gap-2">
      <div className="relative w-[64px] h-[64px]">
        <svg viewBox="0 0 72 72" className="w-full h-full -rotate-90">
          <circle cx="36" cy="36" r="32" fill="none" stroke="#e5e7eb" strokeWidth="4" />
          <circle
            cx="36" cy="36" r="32" fill="none" stroke={color} strokeWidth="4"
            strokeDasharray={`${filled} ${circumference}`} strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-base font-bold" style={{ color }}>{pct}</span>
          <span className="text-[7px] text-s-text-tertiary">/100</span>
        </div>
      </div>
      <div>
        <div className="text-[9px] text-s-text-tertiary uppercase tracking-wide">Risk</div>
        <div className="text-[10px] font-medium" style={{ color }}>
          {pct >= 80 ? "Critical" : pct >= 50 ? "Elevated" : "Low"}
        </div>
      </div>
    </div>
  );
}

function InterventionCard({ intervention }: { intervention: InterventionRecommendation }) {
  const isHigh = intervention.urgency.toLowerCase() === "high";
  const isMed = intervention.urgency.toLowerCase() === "medium";

  const borderColor = isHigh
    ? "border-s-danger/20"
    : isMed
      ? "border-s-warn/20"
      : "border-s-border";
  const tagClass = isHigh ? "tag-danger" : isMed ? "tag-warn" : "tag-safe";

  return (
    <div className={`rounded border ${borderColor} p-2 bg-s-panel`}>
      <div className="flex items-start justify-between gap-2">
        <p className="text-[11px] text-s-text font-medium leading-tight">
          {intervention.action}
        </p>
        <span className={`tag ${tagClass} text-[8px] shrink-0`}>
          {intervention.urgency.toUpperCase()}
        </span>
      </div>
      {intervention.sensitivity_notes && (
        <p className="text-[9px] text-s-muted mt-1 leading-relaxed">
          {intervention.sensitivity_notes}
        </p>
      )}
    </div>
  );
}

export default function CaseBrief({ report, onAction }: Props) {
  const [actionSubmitted, setActionSubmitted] = useState<string | null>(null);

  const brief = report?.evidence_brief;
  const feedbackDone = actionSubmitted !== null || report?.analyst_feedback != null;

  const handleAction = (action: string) => {
    setActionSubmitted(action);
    onAction(action);
  };

  if (!report) {
    return (
      <div className="flex flex-col h-full bg-s-panel">
        <div className="panel-header">
          <h2 className="panel-title">Case Brief</h2>
          <p className="panel-subtitle">Investigation details</p>
        </div>
        <div className="flex-1 flex items-center justify-center px-6 text-center">
          <p className="text-[11px] text-s-text-tertiary">
            Select an alert to view case details.
          </p>
        </div>
      </div>
    );
  }

  const tactic = brief?.exploitation_tactic || "unknown";
  const tacticLabel = TACTIC_LABELS[tactic] || tactic.replace(/_/g, " ");
  const tacticTagClass = TACTIC_TAG[tactic] || "tag-neutral";

  return (
    <div className="flex flex-col h-full bg-s-panel">
      <div className="panel-header">
        <h2 className="panel-title">Case Brief</h2>
        <p className="panel-subtitle">Investigation details</p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-3 space-y-3">
          {/* 1. Alert Header */}
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-[13px] font-semibold text-s-text">
                {brief
                  ? tactic === "unknown"
                    ? "Potential Exploitation"
                    : tacticLabel
                  : "Alert"}
              </h3>
              <span className={`tag ${tacticTagClass} mt-1`}>{tacticLabel}</span>
            </div>
            <RiskGauge score={report.confidence_score} />
          </div>

          <hr className="border-s-border" />

          {/* Account Profiles */}
          {(report.sender_profile || report.receiver_profile) && (
            <>
              <div>
                <h3 className="text-[10px] font-semibold text-s-muted uppercase tracking-wide mb-1.5">
                  Profiles
                </h3>
                <div className="space-y-2">
                  {report.sender_profile && (
                    <AccountProfile profile={report.sender_profile} role="sender" />
                  )}
                  {report.receiver_profile && (
                    <AccountProfile profile={report.receiver_profile} role="receiver" />
                  )}
                </div>
              </div>
              <hr className="border-s-border" />
            </>
          )}

          {/* 2. Threat Radar */}
          {brief && (
            <>
              <ThreatRadar
                signals={brief.signals}
                recipientRiskScore={report.receiver_profile?.recipient_risk ? 0.7 : 0}
              />
              <hr className="border-s-border" />
            </>
          )}

          {/* 3. Timeline */}
          {brief && brief.timeline.length > 0 && (
            <>
              <EventTimeline entries={brief.timeline} />
              <hr className="border-s-border" />
            </>
          )}

          {/* 4. Evidence Summary */}
          {brief?.narrative && (
            <>
              <div>
                <h3 className="text-[10px] font-semibold text-s-muted uppercase tracking-wide mb-1">
                  Evidence Summary
                </h3>
                <p className="text-[11px] text-s-text-secondary leading-relaxed">
                  {brief.narrative}
                </p>
              </div>
              <hr className="border-s-border" />
            </>
          )}

          {/* 5. Manipulation Indicators */}
          {brief && brief.manipulation_indicators.length > 0 && (
            <>
              <div>
                <h3 className="text-[10px] font-semibold text-s-muted uppercase tracking-wide mb-1">
                  Indicators
                </h3>
                <div className="space-y-1">
                  {brief.manipulation_indicators.map((indicator, i) => {
                    const Icon = getIndicatorIcon(indicator);
                    return (
                      <div key={i} className="flex items-start gap-2 text-[11px] text-s-text-secondary">
                        <Icon size={12} className="text-s-muted shrink-0 mt-px" />
                        <span className="leading-tight">{indicator}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
              <hr className="border-s-border" />
            </>
          )}

          {/* 6. Interventions */}
          {brief && brief.interventions.length > 0 && (
            <div>
              <h3 className="text-[10px] font-semibold text-s-muted uppercase tracking-wide mb-1">
                Recommended Actions
              </h3>
              <div className="space-y-1.5">
                {brief.interventions.map((intervention, i) => (
                  <InterventionCard key={i} intervention={intervention} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 7. Analyst Actions */}
      <div className="shrink-0 p-2.5 border-t border-s-border">
        {feedbackDone ? (
          <div className="flex items-center justify-center gap-1 text-[11px] text-s-safe font-medium">
            <CheckCircle2 size={12} />
            Action recorded: {actionSubmitted || "submitted"}
          </div>
        ) : (
          <div className="flex gap-2">
            <button
              onClick={() => handleAction("confirm_exploitation")}
              className="flex-1 py-1.5 rounded text-[11px] font-medium bg-s-danger text-white hover:bg-s-danger/90 transition"
            >
              Confirm Exploitation
            </button>
            <button
              onClick={() => handleAction("mark_legitimate")}
              className="flex-1 py-1.5 rounded text-[11px] font-medium bg-s-safe text-white hover:bg-s-safe/90 transition"
            >
              Mark Legitimate
            </button>
            <button
              onClick={() => handleAction("escalate")}
              className="flex-1 py-1.5 rounded text-[11px] font-medium bg-s-warn text-white hover:bg-s-warn/90 transition"
            >
              Escalate
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
