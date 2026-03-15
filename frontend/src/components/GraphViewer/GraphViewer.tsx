import { useEffect, useRef, useCallback } from "react";
import * as d3 from "d3";
import type { GraphData, GraphNode } from "../../types";

interface SimNode extends GraphNode {
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  vx?: number;
  vy?: number;
  index?: number;
}

interface SimLink {
  source: SimNode | string;
  target: SimNode | string;
  type: string;
  amount?: number;
  flagged?: boolean;
  new?: boolean;
}

interface Props {
  graph: GraphData;
  loading: boolean;
  onNodeSelect?: (nodeId: string) => void;
  selectedNodeId?: string | null;
  compact?: boolean;
}

const NODE_COLORS: Record<string, string> = {
  account: "#2c5282",
  device: "#553c9a",
  merchant: "#276749",
};

const NODE_COLORS_FLAGGED = "#9b2c2c";
const NODE_COLORS_VULNERABLE = "#92400e";

function nodeShape(
  el: d3.Selection<SVGGElement, SimNode, null, undefined>,
  d: SimNode,
) {
  const baseColor = d.flagged
    ? NODE_COLORS_FLAGGED
    : d.vulnerable
      ? NODE_COLORS_VULNERABLE
      : NODE_COLORS[d.type] || "#6b7280";

  if (d.type === "device") {
    el.append("rect")
      .attr("width", 16)
      .attr("height", 16)
      .attr("x", -8)
      .attr("y", -8)
      .attr("rx", 2)
      .attr("fill", baseColor)
      .attr("opacity", 0.9)
      .attr("stroke", d.flagged ? NODE_COLORS_FLAGGED : "none")
      .attr("stroke-width", d.flagged ? 1.5 : 0);
  } else if (d.type === "merchant") {
    el.append("polygon")
      .attr("points", "0,-10 9,0 0,10 -9,0")
      .attr("fill", baseColor)
      .attr("opacity", 0.9)
      .attr("stroke", d.flagged ? NODE_COLORS_FLAGGED : "none")
      .attr("stroke-width", d.flagged ? 1.5 : 0);
  } else {
    el.append("circle")
      .attr("r", d.flagged ? 12 : 9)
      .attr("fill", baseColor)
      .attr("opacity", 0.9)
      .attr("stroke", d.flagged ? NODE_COLORS_FLAGGED : "none")
      .attr("stroke-width", d.flagged ? 1.5 : 0);

    if (d.flagged) {
      el.append("circle")
        .attr("r", 16)
        .attr("fill", "none")
        .attr("stroke", NODE_COLORS_FLAGGED)
        .attr("stroke-width", 0.75)
        .attr("opacity", 0.4)
        .attr("stroke-dasharray", "2,2");
    }
  }

  el.append("text")
    .text(d.label || d.id)
    .attr("dy", d.type === "device" ? 20 : d.type === "merchant" ? 18 : 20)
    .attr("text-anchor", "middle")
    .attr("fill", "#6b7280")
    .attr("font-size", "8px")
    .attr("pointer-events", "none");
}

export default function GraphViewer({
  graph,
  loading,
  onNodeSelect,
  selectedNodeId,
  compact = false,
}: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<d3.Simulation<SimNode, SimLink> | null>(null);

  const buildGraph = useCallback(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const rect = svgRef.current.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;

    svg.selectAll("*").remove();

    if (graph.nodes.length === 0) return;

    const defs = svg.append("defs");
    defs
      .append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 20)
      .attr("refY", 0)
      .attr("markerWidth", 5)
      .attr("markerHeight", 5)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-4L8,0L0,4")
      .attr("fill", "#9ca3af");

    const g = svg.append("g");

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 5])
      .on("zoom", (event) => g.attr("transform", event.transform));
    svg.call(zoom);

    const nodes: SimNode[] = graph.nodes.map((d) => ({ ...d }));
    const links: SimLink[] = graph.edges.map((d) => ({
      source: d.source,
      target: d.target,
      type: d.type,
      amount: d.amount,
      flagged: d.flagged,
      new: d.new,
    }));

    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimLink>(links)
          .id((d) => d.id)
          .distance(120),
      )
      .force("charge", d3.forceManyBody().strength(-400))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30))
      .force("x", d3.forceX(width / 2).strength(0.05))
      .force("y", d3.forceY(height / 2).strength(0.05));

    simulationRef.current = simulation;

    const link = g
      .selectAll<SVGLineElement, SimLink>(".link")
      .data(links)
      .enter()
      .append("line")
      .attr("class", "link")
      .attr("stroke", (d) => (d.flagged ? "#9b2c2c" : "#d1d5db"))
      .attr("stroke-width", (d) => (d.flagged ? 2 : 1))
      .attr("stroke-dasharray", (d) =>
        d.type === "coercion" || d.type === "semantic_dissonance"
          ? "5,3"
          : "none",
      )
      .attr("opacity", (d) => (d.flagged ? 0.8 : 0.5))
      .attr("marker-end", "url(#arrowhead)");

    const edgeLabels = g
      .selectAll<SVGTextElement, SimLink>(".edge-label")
      .data(links.filter((l) => l.type && l.type !== "transfer"))
      .enter()
      .append("text")
      .attr("class", "edge-label")
      .attr("text-anchor", "middle")
      .attr("fill", "#9ca3af")
      .attr("font-size", "7px")
      .text((d) => d.type.replace(/_/g, " "));

    const node = g
      .selectAll<SVGGElement, SimNode>(".node")
      .data(nodes)
      .enter()
      .append("g")
      .attr("class", "node")
      .attr("cursor", "pointer")
      .call(
        d3
          .drag<SVGGElement, SimNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }),
      );

    node.each(function (d) {
      nodeShape(d3.select(this) as any, d);
    });

    node.on("click", (_, d) => {
      onNodeSelect?.(d.id);
    });

    if (selectedNodeId) {
      node
        .filter((d) => d.id === selectedNodeId)
        .select("circle, rect, polygon")
        .attr("stroke", "#2c5282")
        .attr("stroke-width", 2.5);
    }

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SimNode).x ?? 0)
        .attr("y1", (d) => (d.source as SimNode).y ?? 0)
        .attr("x2", (d) => (d.target as SimNode).x ?? 0)
        .attr("y2", (d) => (d.target as SimNode).y ?? 0);

      edgeLabels
        .attr(
          "x",
          (d) =>
            (((d.source as SimNode).x ?? 0) + ((d.target as SimNode).x ?? 0)) /
            2,
        )
        .attr(
          "y",
          (d) =>
            (((d.source as SimNode).y ?? 0) + ((d.target as SimNode).y ?? 0)) /
              2 -
            4,
        );

      node.attr("transform", (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
    });

    return () => {
      simulation.stop();
    };
  }, [graph, onNodeSelect, selectedNodeId]);

  useEffect(() => {
    const cleanup = buildGraph();
    return () => cleanup?.();
  }, [buildGraph]);

  useEffect(() => {
    const handleResize = () => buildGraph();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [buildGraph]);

  return (
    <div className="flex flex-col h-full bg-s-bg">
      {!compact && (
        <div className="panel-header bg-s-panel">
          <h2 className="panel-title">Network Graph</h2>
          <p className="panel-subtitle">Cross-silo relationship topology</p>
        </div>
      )}

      <div className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-s-bg/60 z-10">
            <div className="text-[11px] text-s-text-tertiary">Loading...</div>
          </div>
        )}

        {graph.nodes.length === 0 && !loading && (
          <div className="absolute inset-0 flex items-center justify-center text-s-text-tertiary text-[11px]">
            Awaiting graph data
          </div>
        )}

        <svg
          ref={svgRef}
          className="w-full h-full"
          style={{ display: graph.nodes.length === 0 ? "none" : "block" }}
        />
      </div>

      {/* Legend */}
      <div className="px-3 py-1.5 border-t border-s-border bg-s-panel flex items-center gap-4 text-[9px] text-s-muted">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-s-accent" />
          Account
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-sm bg-s-purple" />
          Device
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rotate-45 bg-s-safe" />
          Merchant
        </span>
        <span className="h-3 w-px bg-s-border" />
        <span className="flex items-center gap-1">
          <span className="w-3 h-px bg-s-muted" />
          Normal
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 border-t border-dashed border-s-muted" />
          Coercion
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-px bg-s-danger" style={{ height: 2 }} />
          Flagged
        </span>
      </div>
    </div>
  );
}
