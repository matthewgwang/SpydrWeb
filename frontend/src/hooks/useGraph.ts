import { useCallback, useEffect, useState } from "react";
import type { GraphData } from "../types";
import { getGraphData, getGraphNeighbors } from "../services/api";

export function useGraph() {
  const [graph, setGraph] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(false);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getGraphData();
      setGraph(data);
    } catch {
      /* backend not ready yet */
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchNeighbors = useCallback(async (nodeId: string, depth = 1) => {
    setLoading(true);
    try {
      const data = await getGraphNeighbors(nodeId, depth);
      setGraph(data);
    } catch {
      /* backend not ready yet */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return { graph, loading, fetchAll, fetchNeighbors };
}
