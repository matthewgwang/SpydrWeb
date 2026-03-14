import { useState } from "react";
import { submitFeedback } from "../../services/api";

interface Props {
  reportId: string;
}

export default function AnalystPanel({ reportId }: Props) {
  const [submitted, setSubmitted] = useState(false);

  const handle = async (action: string) => {
    await submitFeedback({ report_id: reportId, action });
    setSubmitted(true);
  };

  if (submitted) {
    return <p className="text-sentinel-safe text-sm">Feedback recorded.</p>;
  }

  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-sm">Analyst Action</h3>
      <div className="flex gap-2">
        <button
          onClick={() => handle("confirm_fraud")}
          className="px-3 py-1 rounded text-xs bg-sentinel-danger/20 text-sentinel-danger border border-sentinel-danger/40 hover:bg-sentinel-danger/30"
        >
          Confirm Fraud
        </button>
        <button
          onClick={() => handle("mark_legitimate")}
          className="px-3 py-1 rounded text-xs bg-sentinel-safe/20 text-sentinel-safe border border-sentinel-safe/40 hover:bg-sentinel-safe/30"
        >
          Legitimate
        </button>
        <button
          onClick={() => handle("escalate")}
          className="px-3 py-1 rounded text-xs bg-sentinel-warn/20 text-sentinel-warn border border-sentinel-warn/40 hover:bg-sentinel-warn/30"
        >
          Escalate
        </button>
      </div>
    </div>
  );
}
