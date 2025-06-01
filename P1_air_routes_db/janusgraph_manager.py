import asyncio
from typing import Optional
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection

# The JanusGraphManager Class
class JanusGraphManager:
    #  Hold the single instance of the JanusGraphManager class once it's created.
    _instance = None
    # Hold the Gremlin Graph Traversal Source
    _g = None
    # Hold the DriverRemoteConnection object.
    _connection = None
    # A boolean flag to prevent multiple concurrent attempts to connect.
    _is_connecting = False

    # It implements the singleton pattern. This pattern ensures that only one 
    # instance of the JanusGraphManager class can exist throughout your 
    # application's lifecycle.
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # Establishing the Connection
    async def connect(self, url: str = 'ws://localhost:8182/gremlin'):
        # 1. Check if already connected
        if self._g and self._connection:
            return
        # 2. Handle concurrent connection attempts
        # if self._is_connecting:: This checks if another part of the 
        # application is already in the process of connecting. while 
        # self._is_connecting: await asyncio.sleep(0.1): If a connection 
        # is in progress, the function pauses for a short time and then 
        # re-checks. This prevents multiple callers from trying to establish 
        # the connection simultaneously, potentially causing issues. The 
        # second if self._g and self._connection: after the while loop 
        # ensures that if the connection was established by the other 
        # concurrent attempt, this one just returns.
        if self._is_connecting:
            while self._is_connecting:
                await asyncio.sleep(0.1)
            if self._g and self._connection:
                return

        # 3. Start connecting
        # The flag is set to indicate that a connection attempt is now active.
        self._is_connecting = True
        try:
            # Create the remote connection object
            self._connection = DriverRemoteConnection(url, 'g')
            # Create a local graph instance
            graph = Graph()
            # Create the GraphTraversalSource and bind it to the remote connection
            # It creates the Graph Traversal Source (g) that you'll use for all your 
            # Gremlin queries. It binds this traversal source to the remote connection 
            # established earlier. Now, any traversals built with self._g will be sent 
            # over the network to your JanusGraph instance.
            self._g = graph.traversal().withRemote(self._connection)
        except Exception as e:
            self._g = None
            self._connection = None
            raise RuntimeError(f"Failed to connect to JanusGraph: {e}")
        finally:
            self._is_connecting = False

    # Provides access to the _g (Graph Traversal Source) object.
    def get_g(self):
        if not self._g:
            raise RuntimeError("Not connected to JanusGraph.")
        return self._g

    # Gracefully shutting down the connection.
    def close(self):
        if self._connection:
            self._connection.close()
            self._g = None
            self._connection = None


janus_graph_manager = JanusGraphManager()
