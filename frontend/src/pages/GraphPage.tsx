import { useState, useCallback } from "react";
import { GitBranch, Search, Users, AlertTriangle, RefreshCw } from "lucide-react";
import GraphViewer from "../components/GraphViewer/GraphViewer";
import { useGraph } from "../hooks/useGraph";
import { getAccountProfile } from "../services/api";
import type { AccountProfile } from "../types";
import Md from "../components/Md";

export default function GraphPage() {
  const { graph, loading, fetchAll, fetchNeighbors } = useGraph();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [nodeProfile, setNodeProfile] = useState<AccountProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const handleNodeSelect = useCallback(
    async (nodeId: string) => {
      setSelectedNodeId(nodeId);
      setProfileLoading(true);
      try {
        const profile = await getAccountProfile(nodeId);
        setNodeProfile(profile);
      } catch {
        setNodeProfile(null);
      } finally {
        setProfileLoading(false);
      }
    },
    [],
  );

  const handleFocusNode = useCallback(
    (nodeId: string) => {
      fetchNeighbors(nodeId, 2);
      setSelectedNodeId(nodeId);
    },
    [fetchNeighbors],
  );

  const handleSearch = useCallback(() => {
    if (searchQuery.trim()) {
      const node = graph.nodes.find(
        (n) =>
          n.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
          n.label.toLowerCase().includes(searchQuery.toLowerCase()),
      );
      if (node) handleNodeSelect(node.id);
    }
  }, [searchQuery, graph.nodes, handleNodeSelect]);

  const flaggedNodes = graph.nodes.filter((n) => n.flagged);
  const vulnerableNodes = graph.nodes.filter((n) => n.vulnerable);
  const accountNodes = graph.nodes.filter((n) => n.type === "account");

  return (
    <div className="flex h-full overflow-hidden">
      {/* Main graph area */}
      <div className="flex-1 flex flex-col min-w-0">
        <GraphViewer
          graph={graph}
          loading={loading}
          onNodeSelect={handleNodeSelect}
          selectedNodeId={selectedNodeId}
        />
      </div>

      {/* Sidebar */}
      <div className="w-72 shrink-0 bg-s-panel border-l border-s-border flex flex-col overflow-hidden">
        {/* Search */}
        <div className="px-3 py-2 border-b border-s-border">
          <div className="flex gap-1.5">
            <div className="flex-1 relative">
              <Search size={10} className="absolute left-2 top-1/2 -translate-y-1/2 text-s-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                placeholder="Search nodes..."
                className="w-full pl-6 pr-2 py-1 rounded text-[10px] bg-s-surface border border-s-border text-s-text placeholder:text-s-muted focus:outline-none focus:border-s-accent"
              />
            </div>
            <button
              onClick={() => fetchAll()}
              title="Reset to full graph"
              className="p-1 rounded border border-s-border text-s-muted hover:text-s-accent hover:bg-s-surface transition"
            >
              <RefreshCw size={12} />
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-2 px-3 py-2 border-b border-s-border">
          <div className="bg-s-surface rounded px-2 py-1.5 border border-s-border">
            <div className="text-[8px] text-s-text-tertiary uppercase">Nodes</div>
            <div className="text-sm font-bold font-mono text-s-text">{graph.nodes.length}</div>
          </div>
          <div className="bg-s-surface rounded px-2 py-1.5 border border-s-border">
            <div className="text-[8px] text-s-text-tertiary uppercase">Edges</div>
            <div className="text-sm font-bold font-mono text-s-text">{graph.edges.length}</div>
          </div>
          <div className="bg-s-surface rounded px-2 py-1.5 border border-s-border">
            <div className="text-[8px] text-s-text-tertiary uppercase">Flagged</div>
            <div className="text-sm font-bold font-mono text-s-danger">{flaggedNodes.length}</div>
          </div>
          <div className="bg-s-surface rounded px-2 py-1.5 border border-s-border">
            <div className="text-[8px] text-s-text-tertiary uppercase">Vulnerable</div>
            <div className="text-sm font-bold font-mono text-s-warn">{vulnerableNodes.length}</div>
          </div>
        </div>

        {/* Node detail or entity list */}
        <div className="flex-1 overflow-y-auto">
          {profileLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-5 h-5 border-2 border-s-accent border-t-transparent rounded-full animate-spin" />
            </div>
          ) : nodeProfile ? (
            <div className="p-3 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-[11px] font-semibold text-s-text">
                  {nodeProfile.name || nodeProfile.account_id}
                </h3>
                <button
                  onClick={() => handleFocusNode(nodeProfile.account_id)}
                  className="px-1.5 py-0.5 rounded text-[9px] font-medium border border-s-border text-s-text-secondary hover:bg-s-accent-light hover:text-s-accent transition"
                >
                  Focus
                </button>
              </div>

              <div className="space-y-1.5 text-[9px]">
                <div className="flex justify-between">
                  <span className="text-s-text-tertiary">ID</span>
                  <span className="font-mono text-s-text-secondary truncate ml-2 max-w-[140px]">
                    {nodeProfile.account_id}
                  </span>
                </div>
                {nodeProfile.age && (
                  <div className="flex justify-between">
                    <span className="text-s-text-tertiary">Age</span>
                    <span className="text-s-text-secondary">{nodeProfile.age}</span>
                  </div>
                )}
                {nodeProfile.location && (
                  <div className="flex justify-between">
                    <span className="text-s-text-tertiary">Location</span>
                    <span className="text-s-text-secondary">{nodeProfile.location}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-s-text-tertiary">Type</span>
                  <span className="text-s-text-secondary">{nodeProfile.account_type}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-s-text-tertiary">Known Payees</span>
                  <span className="font-mono text-s-text-secondary">
                    {nodeProfile.known_payees.length}
                  </span>
                </div>
              </div>

              {nodeProfile.vulnerability && (
                <div className={`rounded p-2 border text-[9px] ${
                  nodeProfile.vulnerability.score >= 0.4
                    ? "bg-amber-50 border-amber-200"
                    : "bg-emerald-50 border-emerald-200"
                }`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-s-text">Vulnerability</span>
                    <span className={`font-bold font-mono ${
                      nodeProfile.vulnerability.score >= 0.4 ? "text-amber-700" : "text-emerald-700"
                    }`}>
                      {Math.round(nodeProfile.vulnerability.score * 100)}%
                    </span>
                  </div>
                  {nodeProfile.vulnerability.factors.length > 0 && (
                    <div className="space-y-0.5 mt-1">
                      {nodeProfile.vulnerability.factors.map((f, i) => (
                        <div key={i} className="text-[8px] text-s-text-tertiary flex items-start gap-1">
                          <span className="w-1 h-1 rounded-full bg-amber-400 mt-1 shrink-0" />
                          <Md>{f.description}</Md>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {nodeProfile.summary_text && (
                <div className="rounded border border-s-border p-2 bg-s-surface">
                  <div className="text-[8px] font-semibold text-s-text-tertiary uppercase mb-1">Summary</div>
                  <Md className="text-[9px] text-s-text-secondary leading-relaxed">
                    {nodeProfile.summary_text}
                  </Md>
                </div>
              )}

              <button
                onClick={() => {
                  setSelectedNodeId(null);
                  setNodeProfile(null);
                }}
                className="w-full px-2 py-1 rounded text-[9px] font-medium border border-s-border text-s-text-secondary hover:bg-s-surface transition"
              >
                Clear Selection
              </button>
            </div>
          ) : (
            <div className="p-3 space-y-2">
              <div className="flex items-center gap-1.5 text-[10px] font-semibold text-s-text mb-2">
                <Users size={11} className="text-s-accent" />
                Entities ({accountNodes.length})
              </div>

              {flaggedNodes.length > 0 && (
                <div className="mb-2">
                  <div className="text-[9px] font-semibold text-s-danger uppercase mb-1 flex items-center gap-1">
                    <AlertTriangle size={9} /> Flagged
                  </div>
                  {flaggedNodes.map((n) => (
                    <button
                      key={n.id}
                      onClick={() => handleNodeSelect(n.id)}
                      className="w-full text-left px-2 py-1 rounded text-[9px] hover:bg-red-50 transition flex items-center justify-between"
                    >
                      <span className="text-s-text truncate">{n.label || n.id.slice(0, 16)}</span>
                      <span className="text-[8px] text-s-danger font-mono">{n.type}</span>
                    </button>
                  ))}
                </div>
              )}

              {accountNodes.slice(0, 20).map((n) => (
                <button
                  key={n.id}
                  onClick={() => handleNodeSelect(n.id)}
                  className="w-full text-left px-2 py-1 rounded text-[9px] hover:bg-s-surface transition flex items-center justify-between"
                >
                  <span className="text-s-text-secondary truncate">
                    {n.label || n.id.slice(0, 16)}
                  </span>
                  <span className="flex items-center gap-1">
                    {n.vulnerable && (
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    )}
                    <span className="text-[8px] text-s-muted font-mono">{n.type}</span>
                  </span>
                </button>
              ))}

              {accountNodes.length === 0 && (
                <p className="text-[10px] text-s-text-tertiary text-center py-4">
                  Click a node in the graph to see details
                </p>
              )}
            </div>
          )}
        </div>

        {/* Legend */}
        <div className="px-3 py-2 border-t border-s-border">
          <div className="flex items-center gap-1.5 mb-1.5">
            <GitBranch size={10} className="text-s-accent" />
            <span className="text-[9px] font-semibold text-s-text">Legend</span>
          </div>
          <div className="grid grid-cols-2 gap-1 text-[8px] text-s-muted">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#2c5282]" /> Account
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-[#553c9a]" /> Device
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rotate-45 bg-[#276749]" /> Merchant
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#9b2c2c]" /> Flagged
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
