from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/data")
async def get_graph_data(request: Request):
    """Return full graph as nodes + edges for d3-force visualization."""
    graph = request.app.state.brain_graph
    return graph.serialize_for_frontend()


@router.get("/neighbors/{node_id}")
async def get_neighbors(node_id: str, request: Request, depth: int = 2):
    graph = request.app.state.brain_graph
    subgraph = graph.get_subgraph(node_id, depth=depth)
    return subgraph
