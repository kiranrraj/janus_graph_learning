from typing import Optional, List, Dict, Any
from gremlin_python.process.graph_traversal import GraphTraversalSource
from gremlin_python.process.traversal import T

# When you use Gremlin's valueMap(True), it returns a dictionary which contains 
# special keys like the element's ID and label, represented by T.id and T.label 
# objects (not strings). Secondly single-valued properties are returned as a 
# list with an element. This function cleans up the raw Gremlin output. If the 
# key is instance of the T class it extracts its string representation using 
# k.name (T.id becomes the string 'id'), else it converts them to a string. If 
# a value v is a list and contains only one element, it unwraps that element 
# (v[0]). This converts {'name': ['Alice']} into {'name': 'Alice'}. If the 
# value is not a list, or if it's a list with multiple elements it keeps the 
# value as is.
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

    # get_all_vertices function provides a flexible way to fetch vertex data 
    # from your graph, optionally filtering by label, and then processes the 
    # raw Gremlin output into a clean, Python-friendly dictionary format.
    def get_all_vertices(self, label: Optional[str] = None) -> List[Dict[str, Any]]:
        # self.g.V(): This is the starting point of your Gremlin traversal.
        # self.g: This is your GraphTraversalSource object, which is connected 
        # to your remote JanusGraph database. V(): This is a Gremlin step that 
        # selects all vertices in the graph. At this point, query represents a 
        # traversal that will get every vertex.
        query = self.g.V()

        if label:
            # .hasLabel(label): This Gremlin step filters the current set of 
            # vertices (all vertices from .V()) to include only those that 
            # have the specified label.
            query = query.hasLabel(label)
        vertices = []
        try:
            # Gremlin query is actually executed and the results are fetched.
            # It instructs the graph to retrieve all properties of the selected 
            # vertices. The True argument tells Gremlin to include the special 
            # id and label of each vertex in the returned map.
            results = query.valueMap(True).toList()
            for v in results:
                vertices.append(normalize_result(v))
        except Exception as e:
            raise RuntimeError(f"Failed to get vertices: {e}")
        return vertices

    # get_vertex_by_id function, which is designed to retrieve a single vertex 
    # from your graph database based on its unique ID.
    def get_vertex_by_id(self, vertex_id: str) -> Dict[str, Any]:
        try:
            # self.g.V(vertex_id): This directly starts a Gremlin traversal 
            # that attempts to select a vertex whose ID matches the vertex_id 
            # you provided. valueMap(True): step instructs Gremlin to retrieve 
            # all properties of the selected vertex, including its id and label 
            # (due to True). next(): This is a terminal step that executes the 
            # Gremlin query and attempts to retrieve the first result.If the 
            # query (self.g.V(vertex_id)) does not find a vertex with the given 
            # vertex_id, calling .next() will raise an error (a StopIteration 
            # in Gremlin-Python, which the driver might wrap or which the 
            # Gremlin Server might send as a NoSuchElementException).
            v = self.g.V(vertex_id).valueMap(True).next()
            return normalize_result(v)
        except Exception as e:
            raise RuntimeError(f"Vertex {vertex_id} not found or query failed: {e}")
