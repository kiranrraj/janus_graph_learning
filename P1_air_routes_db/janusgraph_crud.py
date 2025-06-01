from typing import Optional, List, Dict, Any
from gremlin_python.process.graph_traversal import GraphTraversalSource
from gremlin_python.process.traversal import T


def normalize_result(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Gremlin result map to a clean Python dict."""
    normalized = {}
    for k, v in raw.items():
        if isinstance(k, T):
            key = k.name
        else:
            key = str(k)

        if isinstance(v, list) and len(v) == 1:
            normalized[key] = v[0]
        else:
            normalized[key] = v
    return normalized


class GraphCRUDOperations:
    def __init__(self, g: GraphTraversalSource):
        self.g = g

    def get_all_vertices(self, label: Optional[str] = None) -> List[Dict[str, Any]]:
        query = self.g.V()
        if label:
            query = query.hasLabel(label)
        vertices = []
        try:
            results = query.valueMap(True).toList()
            for v in results:
                vertices.append(normalize_result(v))
        except Exception as e:
            raise RuntimeError(f"Failed to get vertices: {e}")
        return vertices

    def get_vertex_by_id(self, vertex_id: str) -> Dict[str, Any]:
        try:
            v = self.g.V(vertex_id).valueMap(True).next()
            return normalize_result(v)
        except Exception as e:
            raise RuntimeError(f"Vertex {vertex_id} not found or query failed: {e}")
