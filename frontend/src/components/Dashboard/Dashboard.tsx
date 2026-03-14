import TransactionFeed from "../TransactionFeed/TransactionFeed";
import GraphViewer from "../GraphViewer/GraphViewer";
import GovernanceBar from "../GovernanceBar/GovernanceBar";

export default function Dashboard() {
  return (
    <div className="flex flex-col h-screen">
      <GovernanceBar />
      <div className="flex flex-1 overflow-hidden">
        <div className="w-1/4 border-r border-sentinel-border overflow-y-auto">
          <TransactionFeed />
        </div>
        <div className="flex-1">
          <GraphViewer />
        </div>
        <div className="w-1/4 border-l border-sentinel-border overflow-y-auto p-4">
          <p className="text-gray-500 text-sm">
            Select a node or transaction to view details.
          </p>
        </div>
      </div>
    </div>
  );
}
