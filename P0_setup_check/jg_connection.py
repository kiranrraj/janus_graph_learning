from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import GraphTraversalSource
from gremlin_python.process.anonymous_traversal import traversal
import sys, asyncio

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

GREMLIN_SERVER_URL = "ws://localhost:8182/gremlin"
print(f"Trying to connect to Gremlin server at {GREMLIN_SERVER_URL}")

g = None
conn = None

try:
    # Establish remote connection
    conn = DriverRemoteConnection(GREMLIN_SERVER_URL, 'g')
    g: GraphTraversalSource = traversal().with_remote(conn)
    print("Successfully connected to JanusGraph Gremlin Server.")

    # Perform a sample query
    vertex_count = g.V().count().next()
    print(f" Current number of vertices in the graph: {vertex_count}")

except ConnectionRefusedError:
    print(f"ERROR: Connection refused. Is JanusGraph running and listening on {GREMLIN_SERVER_URL}?")

except Exception as e:
    print(f"Unexpected error: {e}")

finally:
    try:
        if conn:
            conn.close()
            print("Gremlin server connection closed")
    except Exception as close_e:
        print(f"Error while closing connection: {close_e}")
