from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import GraphTraversalSource
from gremlin_python.process.anonymous_traversal import traversal
import sys
import asyncio

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class JanusGraphConnector:
    """
    A class to manage the connection to a JanusGraph Gremlin Server.
    """

    def __init__(self, gremlin_server_url: str = "ws://localhost:8182/gremlin"):
        """
        Initialize with the Gremlin server URL.
        """
        self.gremlin_server_url = gremlin_server_url
        self.conn = None
        self.g: GraphTraversalSource | None = None

    def connect(self):
        """
        Establishes the connection and sets up the traversal source.
        """
        print(f"Connecting to Gremlin server at {self.gremlin_server_url}")
        try:
            self.conn = DriverRemoteConnection(self.gremlin_server_url, 'g')
            self.g = traversal().with_remote(self.conn)
            print("Connected to JanusGraph Gremlin Server.")
        except ConnectionRefusedError:
            print(f"ERROR: Connection refused. Is JanusGraph running at {self.gremlin_server_url}?")
            raise
        except Exception as e:
            print(f"Unexpected error during connection: {e}")
            raise

    def test_query(self):
        """
        Performs a sample query to count vertices.
        """
        if not self.g:
            print("Not connected to the graph. Run connect() first.")
            return

        try:
            vertex_count = self.g.V().count().next()
            print(f"Current number of vertices in the graph: {vertex_count}")
        except Exception as e:
            print(f"Failed to run test query: {e}")

    def close(self):
        """
        Closes the Gremlin server connection.
        """
        if self.conn:
            try:
                self.conn.close()
                print("Gremlin server connection closed.")
            except Exception as e:
                print(f"Error closing connection: {e}")


def main():
    connector = JanusGraphConnector("ws://localhost:8182/gremlin")

    try:
        connector.connect()
        connector.test_query()
    except Exception as e:
        print(f"Operation failed: {e}")
    finally:
        connector.close()


if __name__ == "__main__":
    main()
