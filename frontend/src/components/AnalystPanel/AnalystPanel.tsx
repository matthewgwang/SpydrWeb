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
    return <p className="text-s-safe text-sm">Feedback recorded.</p>;
  }

  return (
    <div className="space-y-2">
      <h3 className="font-semibold text-sm text-s-text">Analyst Action</h3>
      <div className="flex gap-2">
        <button
          onClick={() => handle("confirm_fraud")}
          className="px-3 py-1 rounded text-xs bg-s-danger text-white hover:bg-s-danger/90 transition"
        >
          Confirm Fraud
        </button>
        <button
          onClick={() => handle("mark_legitimate")}
          className="px-3 py-1 rounded text-xs bg-s-safe text-white hover:bg-s-safe/90 transition"
        >
          Legitimate
        </button>
        <button
          onClick={() => handle("escalate")}
          className="px-3 py-1 rounded text-xs bg-s-warn text-white hover:bg-s-warn/90 transition"
        >
          Escalate
        </button>
      </div>
    </div>
  );
}
