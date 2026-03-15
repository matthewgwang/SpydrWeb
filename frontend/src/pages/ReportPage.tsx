import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import type { CaseReport } from "../types";
import { getReport } from "../services/api";
import EvidenceBrief from "../components/EvidenceBrief/EvidenceBrief";
import ConfidenceScore from "../components/ConfidenceScore/ConfidenceScore";
import AnalystPanel from "../components/AnalystPanel/AnalystPanel";

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<CaseReport | null>(null);

  useEffect(() => {
    if (id) {
      getReport(id).then(setReport).catch(() => {});
    }
  }, [id]);

  if (!report) {
    return (
      <div className="flex items-center justify-center h-screen text-s-text-tertiary">
        Loading report...
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <h1 className="text-xl font-bold text-s-text">Case Report</h1>

      <ConfidenceScore
        score={report.confidence_score}
        signals={report.evidence_brief?.signals}
      />

      {report.evidence_brief && <EvidenceBrief brief={report.evidence_brief} />}

      <AnalystPanel reportId={report.id} />
    </div>
  );
}
