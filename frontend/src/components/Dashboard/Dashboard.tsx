import { useState, useCallback } from "react";
import TransactionFeed from "../TransactionFeed/TransactionFeed";
import AlertQueue from "../AlertQueue/AlertQueue";
import GraphViewer from "../GraphViewer/GraphViewer";
import CaseBrief from "../CaseBrief/CaseBrief";
import { useTransactionFeed } from "../../hooks/useTransactionFeed";
import { useGraph } from "../../hooks/useGraph";
import type { CaseReport } from "../../types";
import { getReport, submitFeedback } from "../../services/api";

export default function Dashboard() {
  const { transactions, alerts } = useTransactionFeed();
  const { graph, loading: graphLoading, fetchNeighbors } = useGraph();
  const [selectedReport, setSelectedReport] = useState<CaseReport | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [alertRefresh, setAlertRefresh] = useState(0);

  const handleAlertSelect = useCallback(async (reportId: string) => {
    try {
      const report = await getReport(reportId);
      setSelectedReport(report);
      setAlertRefresh((n) => n + 1);
    } catch {}
  }, []);

  const handleBundleReportSelect = useCallback((report: CaseReport) => {
    setSelectedReport(report);
  }, []);

  const handleNodeSelect = useCallback(
    (nodeId: string) => {
      setSelectedNodeId(nodeId);
      fetchNeighbors(nodeId, 2);
    },
    [fetchNeighbors],
  );

  const handleAnalystAction = useCallback(
    async (action: string) => {
      if (!selectedReport) return;
      try {
        await submitFeedback({ report_id: selectedReport.id, action });
        setSelectedReport((prev) =>
          prev ? { ...prev, analyst_feedback: { action, submitted: true } } : null,
        );
      } catch {}
    },
    [selectedReport],
  );

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left — Feed + Alerts */}
      <div className="w-[280px] shrink-0 border-r border-s-border flex flex-col bg-s-panel">
        <div className="flex-1 overflow-y-auto min-h-0">
          <TransactionFeed
            transactions={transactions}
            alerts={alerts}
            onAlertSelect={handleAlertSelect}
          />
        </div>
        <AlertQueue
          onSelectReport={handleBundleReportSelect}
          refreshTrigger={alertRefresh}
        />
      </div>

      {/* Center — Graph */}
      <div className="flex-1 flex flex-col min-w-0">
        <GraphViewer
          graph={graph}
          loading={graphLoading}
          onNodeSelect={handleNodeSelect}
          selectedNodeId={selectedNodeId}
        />
      </div>

      {/* Right — Case Brief */}
      <div className="w-[340px] shrink-0 border-l border-s-border flex flex-col bg-s-panel">
        <CaseBrief report={selectedReport} onAction={handleAnalystAction} />
      </div>
    </div>
  );
}
