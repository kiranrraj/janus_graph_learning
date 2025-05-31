from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import GraphTraversalSource
from gremlin_python.process.anonymous_traversal import traversal

GREMLIN_SERVER_URL = "ws://localhost:8182/gremlin"
print(f"Trying to connect to Gremlin server at {GREMLIN_SERVER_URL}")

g = None

try:
    conn = DriverRemoteConnection(GREMLIN_SERVER_URL, 'g')
    g = traversal().with_remote(conn)
    print("Successfully connected to JanusGraph Gremlin Server.")

    vertex_count = g.V().count().next()
    print(f"Current number of vertices in the graph: {vertex_count}")

except ConnectionRefusedError:
    print(f"ERROR: Connection refused. Is JanusGraph Gremlin Server running and accessible at {GREMLIN_SERVER_URL}?")

except Exception as e:
    print(f"An unexpected error occurred: {e}")

finally:
    if g:
        try:
            g.close()
            print("Gremlin server connection closed")
        except Exception as close_e:
            print(f"Error closing Gremlin Server connection: {close_e}")
