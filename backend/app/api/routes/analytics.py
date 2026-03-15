from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/summary")
async def get_analytics_summary(request: Request):
    """Aggregate analytics from live pipeline data."""
    orchestrator = request.app.state.orchestrator
    event_stream = request.app.state.event_stream
    brain_graph = request.app.state.brain_graph

    reports = orchestrator.case_reports
    total = len(reports)
    fast_pathed = sum(1 for r in reports if r.fast_pathed)
    full_pipeline = total - fast_pathed

    # Layer trigger counts
    layer_triggers = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reports:
        for s in r.layer_signals:
            if s.triggered and s.layer_id in layer_triggers:
                layer_triggers[s.layer_id] += 1

    # Action distribution
    action_counts = {"allow": 0, "delay": 0, "hold": 0, "refer": 0}
    for r in reports:
        action = r.recommended_action.value if hasattr(r.recommended_action, "value") else str(r.recommended_action)
        if action in action_counts:
            action_counts[action] += 1

    # Score distribution (buckets of 10)
    score_buckets = [0] * 10
    for r in reports:
        bucket = min(int(r.confidence_score * 10), 9)
        score_buckets[bucket] += 1

    # Graph stats
    graph_data = brain_graph.serialize_for_frontend()
    node_count = len(graph_data.get("nodes", []))
    edge_count = len(graph_data.get("edges", []))
    flagged_nodes = sum(1 for n in graph_data.get("nodes", []) if n.get("flagged"))

    # Recent scores for time series
    recent_scores = []
    for r in reports[-50:]:
        recent_scores.append({
            "id": r.transaction_id[:8],
            "score": round(r.confidence_score, 3),
            "fast_pathed": r.fast_pathed,
            "action": r.recommended_action.value if hasattr(r.recommended_action, "value") else str(r.recommended_action),
        })

    # Fast-path batches (group reports into batches of 20)
    batch_size = 20
    fast_path_batches = []
    for i in range(0, total, batch_size):
        batch = reports[i : i + batch_size]
        fp = sum(1 for r in batch if r.fast_pathed)
        fast_path_batches.append({
            "batch": f"B{i // batch_size + 1}",
            "fastPathed": fp,
            "fullPipeline": len(batch) - fp,
        })

    return {
        "totals": {
            "reports": total,
            "fast_pathed": fast_pathed,
            "full_pipeline": full_pipeline,
            "fast_path_rate": round(fast_pathed / total * 100, 1) if total > 0 else 0,
        },
        "layer_triggers": layer_triggers,
        "action_counts": action_counts,
        "score_distribution": score_buckets,
        "graph": {
            "nodes": node_count,
            "edges": edge_count,
            "flagged": flagged_nodes,
        },
        "recent_scores": recent_scores,
        "fast_path_batches": fast_path_batches,
    }
