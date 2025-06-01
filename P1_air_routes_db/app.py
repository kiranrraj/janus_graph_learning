import uvicorn
from fastapi import FastAPI, HTTPException, status, Depends
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from janusgraph_manager import janus_graph_manager
from janusgraph_crud import GraphCRUDOperations
from gremlin_python.process.graph_traversal import GraphTraversalSource

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting app, connecting to JanusGraph...")
    await janus_graph_manager.connect()
    yield
    print("Shutting down, closing JanusGraph connection...")
    janus_graph_manager.close()

app = FastAPI(lifespan=lifespan, title="JanusGraph Air Routes API v1.0")

async def get_graph_traversal_source() -> GraphTraversalSource:
    try:
        return janus_graph_manager.get_g()
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))

async def get_graph_crud_ops(
    g: GraphTraversalSource = Depends(get_graph_traversal_source)
) -> GraphCRUDOperations:
    return GraphCRUDOperations(g)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/vertices", response_model=List[Dict[str, Any]])
def read_vertices(label: Optional[str] = None, crud: GraphCRUDOperations = Depends(get_graph_crud_ops)):
    try:
        return crud.get_all_vertices(label)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/vertices/{vertex_id}", response_model=Dict[str, Any])
def read_vertex(vertex_id: str, crud: GraphCRUDOperations = Depends(get_graph_crud_ops)):
    try:
        return crud.get_vertex_by_id(vertex_id)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
