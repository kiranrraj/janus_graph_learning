from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.graph_traversal import GraphTraversalSource
from gremlin_python.process.anonymous_traversal import traversal
import sys, asyncio, os

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class JanusGraphConnector:
    def __init__(self, gremlin_url: str = "ws://localhost:8182/gremlin"):
        self.gremlin_url = gremlin_url
        self.conn = None
        self.g : GraphTraversalSource | None = None

    def connect(self):
        print(f"Connecting to Gremlin server at {self.gremlin_url}")
        try:
            self.conn = DriverRemoteConnection(self.gremlin_url, 'g')
            self.g = traversal().with_remote(self.conn)
            print("Connected to JanusGraph Gremlin Server.")
        except ConnectionRefusedError:
            print(f"ERROR: Connection refused. Is JanusGraph running at {self.gremlin_url}?")
            raise
        except Exception as e:
            print(f"Unexpected error during connection: {e}")
            raise

    def test_query(self):
        if not self.g:
            print("Not connect to graph")
            return
        
        try:
            vertex_count = self.g.V().count().next()
            print(f"Current number of vertices in the graph: {vertex_count}")
        except Exception as e:
            print(f"Failed to run test query. {e}")
        
    def load_graphml_data(self, file_path: str): 
        """
        Loads graph data from a local GraphML file into the remote JanusGraph instance.

        Args:
            file_path (str): The absolute path to the GraphML file on the local system

        Important Note:
            For Dockerized JanusGraph, the local 'file_path' must correspond to a path
            that is mounted into the Docker container. This method automatically
            converts the local path to the container's internal path.
            Ensure your 'docker-compose.yaml' (or 'docker run' command) includes
            a volume mount like:
            - ./your_local_data_folder:/opt/janusgraph/data
            where 'your_local_data_folder' contains 'os.path.basename(file_path)'.
        """
        if not self.g:
            print("Not connected to the graph")
        if not os.path.exists(file_path):
            print(f"Error: File not found at {file_path}")
            return
        print(f"Attempting to load graph data from {file_path} into remote JanusGraph...")

        try:
            container_file_path = "/opt/janusgraph/data/" + os.path.basename(file_path)
            print(f"Attempting to load from container path: {container_file_path}")
            self.g.io(container_file_path).read().iterate()
            print("GraphML data loaded successfully.")
        except Exception as e:
            print(f"Failed to load graph data: {e}")
            raise

    def close(self):
        if self.conn:
            try:
                self.conn.close()
                print("Gremlin server connection closed.")
            except Exception as e:
                print(f"Error closing connection: {e}")

def main():
    connector = JanusGraphConnector("ws://localhost:8182/gremlin")
    air_routes_file_path = "D:/gremlin_console/data/air-routes-latest.graphml"

    try:
        connector.connect()
        connector.load_graphml_data(air_routes_file_path)
        connector.test_query()

    except Exception as e:
        print(f"Operation failed: {e}")
    finally:
        connector.close()

if __name__ == "__main__":
    main()