import { FileText, X } from "lucide-react";
import type { CaseReport } from "../../types";
import Md from "../Md";

interface Props {
  report: CaseReport;
  onClose: () => void;
}

export default function ReportModal({ report, onClose }: Props) {
  return (
    <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-s-panel rounded-lg shadow-2xl w-full max-w-3xl border border-s-border flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex justify-between items-center px-4 py-3 border-b border-s-border bg-s-panel-alt rounded-t-lg">
          <div className="flex items-center gap-2 text-s-text font-bold text-[12px]">
            <FileText size={14} className="text-s-accent" />
            SYSTEM GENERATED SAR REPORT (PREVIEW)
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded text-s-muted hover:text-s-danger hover:bg-s-danger-light transition"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-[10px] text-s-text-secondary">
          {/* Document metadata */}
          <div className="bg-s-surface p-3 rounded border border-s-border">
            <strong className="text-s-text">DOCUMENT ID:</strong> SAR-{report.id.slice(0, 12)}<br />
            <strong className="text-s-text">DATE:</strong> {new Date(report.timestamp).toUTCString()}<br />
            <strong className="text-s-text">FILING INSTITUTION:</strong> SENTINEL CORE SEC-OPS<br />
            <strong className="text-s-text">RISK SCORE:</strong>{" "}
            <span className={report.confidence_score >= 0.7 ? "text-s-danger font-bold" : ""}>
              {Math.round(report.confidence_score * 100)} / 100
            </span>
            <br />
            <strong className="text-s-text">ACTION:</strong>{" "}
            <span className={`font-bold ${
              report.recommended_action === "hold" || report.recommended_action === "refer"
                ? "text-s-danger"
                : report.recommended_action === "delay"
                  ? "text-s-warn"
                  : "text-s-safe"
            }`}>
              {report.recommended_action.toUpperCase()}
            </span>
          </div>

          {/* Part I: Subject */}
          <div>
            <h3 className="font-bold text-s-text border-b border-s-border pb-1 mb-2">
              PART I: SUBJECT INFORMATION
            </h3>
            {report.sender_profile && (
              <>
                Name: {report.sender_profile.name} (ID: {report.sender_profile.account_id})<br />
                Age: {report.sender_profile.age || "N/A"}<br />
                Location: {report.sender_profile.location || "N/A"}<br />
                Account Type: {report.sender_profile.account_type || "N/A"}<br />
                Vulnerability:{" "}
                {report.sender_profile.vulnerability
                  ? `${Math.round(report.sender_profile.vulnerability.score * 100)}% — ${
                      report.sender_profile.vulnerability.factors
                        .map((f) => f.factor)
                        .join(", ") || "none"
                    }`
                  : "N/A"}
              </>
            )}
          </div>

          {/* Part II: Suspicious Activity */}
          <div>
            <h3 className="font-bold text-s-text border-b border-s-border pb-1 mb-2">
              PART II: SUSPICIOUS ACTIVITY
            </h3>
            {report.transaction && (
              <>
                Amount: ${report.transaction.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}<br />
                Type: {report.transaction.type}<br />
                Channel: {report.transaction.channel}<br />
                Sender: {report.transaction.sender_id} → Receiver: {report.transaction.receiver_id}<br />
                Description: {report.transaction.description || "N/A"}
              </>
            )}
          </div>

          {/* Part III: Layer signals summary */}
          <div>
            <h3 className="font-bold text-s-text border-b border-s-border pb-1 mb-2">
              PART III: DETECTION SIGNALS
            </h3>
            {report.layer_signals.filter((s) => s.triggered).length === 0 ? (
              <p className="text-s-safe">No detection signals triggered. Transaction cleared.</p>
            ) : (
              <div className="space-y-1.5">
                {report.layer_signals
                  .filter((s) => s.triggered)
                  .map((s, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <span className="text-s-danger font-bold">▸</span>
                      <div>
                        <span className="font-bold text-s-text">
                          L{s.layer_id} {s.layer_name}
                        </span>
                        {" — "}
                        <span className="text-s-text-secondary"><Md>{s.explanation}</Md></span>
                        <span className="text-s-muted ml-1">
                          (conf: {Math.round(s.confidence * 100)}%, severity: {s.severity})
                        </span>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>

          {/* Part IV: AI Narrative */}
          {report.evidence_brief?.narrative && (
            <div>
              <h3 className="font-bold text-s-text border-b border-s-border pb-1 mb-2">
                PART IV: AI NARRATIVE & SYNTHESIS
              </h3>
              <Md className="leading-relaxed font-sans text-[11px]">
                {report.evidence_brief.narrative}
              </Md>
            </div>
          )}

          {/* Part V: What traditional systems missed */}
          {report.evidence_brief?.what_traditional_systems_missed && (
            <div>
              <h3 className="font-bold text-s-text border-b border-s-border pb-1 mb-2">
                PART V: WHAT TRADITIONAL SYSTEMS MISSED
              </h3>
              <Md className="font-sans text-[11px] leading-relaxed">
                {report.evidence_brief.what_traditional_systems_missed}
              </Md>
            </div>
          )}

          {/* Part VI: Interventions */}
          {report.evidence_brief && report.evidence_brief.interventions.length > 0 && (
            <div>
              <h3 className="font-bold text-s-text border-b border-s-border pb-1 mb-2">
                PART VI: RECOMMENDED INTERVENTIONS
              </h3>
              <div className="space-y-1.5 font-sans text-[10px]">
                {report.evidence_brief.interventions.map((inv, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <span className={`font-bold text-[9px] px-1 py-0.5 rounded ${
                      inv.urgency === "HIGH"
                        ? "bg-red-100 text-red-700"
                        : inv.urgency === "MEDIUM"
                          ? "bg-amber-100 text-amber-700"
                          : "bg-emerald-100 text-emerald-700"
                    }`}>
                      {inv.urgency}
                    </span>
                    <div>
                      <span className="text-s-text font-medium"><Md>{inv.action}</Md></span>
                      {" — "}
                      <span className="text-s-text-secondary"><Md>{inv.reason}</Md></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-s-border bg-s-panel-alt flex justify-end gap-2 rounded-b-lg">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded text-[10px] font-medium border border-s-border text-s-text-secondary hover:bg-s-surface transition"
          >
            Close Preview
          </button>
          <button className="px-3 py-1.5 rounded text-[10px] font-medium bg-s-accent text-white hover:bg-s-accent/90 transition flex items-center gap-1.5">
            <FileText size={11} />
            Submit to Compliance
          </button>
        </div>
      </div>
    </div>
  );
}
