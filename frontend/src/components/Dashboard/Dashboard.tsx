import { useState, useCallback } from "react";
import { useOutletContext } from "react-router-dom";
import StatsCards from "../StatsCards/StatsCards";
import TransactionTable from "../TransactionTable/TransactionTable";
import InvestigationPanel from "../InvestigationPanel/InvestigationPanel";
import ReportModal from "../ReportModal/ReportModal";
import type { TransactionFeedItem, AlertFeedItem, CaseReport } from "../../types";
import { getReport, getReportByTransactionId } from "../../services/api";

interface OutletCtx {
  transactions: TransactionFeedItem[];
  alerts: AlertFeedItem[];
  mode: "pipeline" | "agentic";
  recentAlertTxIds: Set<string>;
}

export default function Dashboard() {
  const { transactions, alerts, recentAlertTxIds } = useOutletContext<OutletCtx>();
  const [inspectingTx, setInspectingTx] = useState<TransactionFeedItem | null>(null);
  const [selectedReport, setSelectedReport] = useState<CaseReport | null>(null);
  const [reportModalData, setReportModalData] = useState<CaseReport | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchReport = useCallback(async (tx: TransactionFeedItem): Promise<CaseReport | null> => {
    try {
      if (tx.report_id) {
        return await getReport(tx.report_id);
      }
      return await getReportByTransactionId(tx.id);
    } catch {
      return null;
    }
  }, []);

  const handleReasoning = useCallback(async (tx: TransactionFeedItem) => {
    setInspectingTx(tx);
    setLoading(true);
    const report = await fetchReport(tx);
    setSelectedReport(report);
    setLoading(false);
  }, [fetchReport]);

  const handleReport = useCallback(async (tx: TransactionFeedItem) => {
    const report = await fetchReport(tx);
    if (report) setReportModalData(report);
  }, [fetchReport]);

  const handleClosePanel = useCallback(() => {
    setInspectingTx(null);
    setSelectedReport(null);
  }, []);

  const isPanelOpen = inspectingTx !== null;

  return (
    <div className="flex flex-col h-full p-3 gap-3 overflow-hidden">
      <StatsCards transactions={transactions} alerts={alerts} />

      <div className="flex-1 flex gap-3 min-h-0 overflow-hidden">
        <div
          className={`flex flex-col min-h-0 overflow-hidden transition-all duration-300 ${
            isPanelOpen ? "w-1/4 shrink-0" : "flex-1"
          }`}
        >
          <TransactionTable
            transactions={transactions}
            compact={isPanelOpen}
            pinnedId={inspectingTx?.id ?? null}
            recentAlertTxIds={recentAlertTxIds}
            onReasoning={handleReasoning}
            onReport={handleReport}
          />
        </div>

        {isPanelOpen && (
          <div className="w-3/4 min-h-0 overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center h-full bg-s-panel border border-s-border rounded">
                <div className="text-center">
                  <div className="w-8 h-8 border-2 border-s-accent border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                  <p className="text-[11px] text-s-text-tertiary">Loading pipeline trace...</p>
                </div>
              </div>
            ) : selectedReport ? (
              <InvestigationPanel report={selectedReport} onClose={handleClosePanel} />
            ) : (
              <div className="flex items-center justify-center h-full bg-s-panel border border-s-border rounded">
                <p className="text-[11px] text-s-text-tertiary">
                  No pipeline data available for this transaction.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {reportModalData && (
        <ReportModal
          report={reportModalData}
          onClose={() => setReportModalData(null)}
        />
      )}
    </div>
  );
}
