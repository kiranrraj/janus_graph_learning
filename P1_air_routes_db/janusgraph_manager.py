import asyncio
from typing import Optional
from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection


class JanusGraphManager:
    _instance = None
    _g = None
    _connection = None
    _is_connecting = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self, url: str = 'ws://localhost:8182/gremlin'):
        if self._g and self._connection:
            return

        if self._is_connecting:
            while self._is_connecting:
                await asyncio.sleep(0.1)
            if self._g and self._connection:
                return

        self._is_connecting = True
        try:
            self._connection = DriverRemoteConnection(url, 'g')
            graph = Graph()
            self._g = graph.traversal().withRemote(self._connection)
        except Exception as e:
            self._g = None
            self._connection = None
            raise RuntimeError(f"Failed to connect to JanusGraph: {e}")
        finally:
            self._is_connecting = False

    def get_g(self):
        if not self._g:
            raise RuntimeError("Not connected to JanusGraph.")
        return self._g

    def close(self):
        if self._connection:
            self._connection.close()
            self._g = None
            self._connection = None


janus_graph_manager = JanusGraphManager()
