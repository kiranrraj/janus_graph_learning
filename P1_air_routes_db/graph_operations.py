from gremlin_python.process.graph_traversal import GraphTraversalSource
from gremlin_python.process.traversal import T, __
from typing import Dict, Any, List, Optional


class GraphCRUDOperations:
    def __init__(self, g: GraphTraversalSource):
        self.g = g

    # --- READ Operations (GET) ---
    async def get_vertex_by_id(self, vertex_id: str) -> Optional[Dict[str, Any]]:
        try:
            vertex_data = await self.g.V(vertex_id)
                .project('id', 'label', 'properties')
                .by(T.id)
                .by(T.label)
                .by(__.valueMap(True))
                .next()
            vertex_data['id'] = str(vertex_data['id'])
            return vertex_data
        except StopIteration:
            return None
        except Exception as e:
            print(f"Error getting vertex by ID {vertex_id}")
            print(f"{e}")
            raise

    async def get_edge_by_id(self, edge_id: str) -> Optional[Dict[str, Any]]:
        try:
            edge_data = await self.g.E(edge_id)
                .project("id", "label", "properties")
                .by(T.id)
                .by(T.label)
                .by(__.valueMap(True))
                .by(__.outV().id())
                .by(__.inV().id())
                .next()
            edge_data["id"] = str(edge_data["id"])
            edge_data['outV'] = str(edge_data['outV'])
            edge_data['inV'] = str(edge_data['inV'])
            return edge_data
        except StopIteration:
            return None
        except Exception as e:
            print(f"Error getting edge by id {edge_id}")
            print(f"{e}")
            raise
    
    async def find_vertices(
        self, 
        label: Optional[str] = None, 
        property_filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        traversal_chain = self.g.V()
        if label:
            traversal_chain = traversal_chain.hasLabel(label)
        if property_filters:
            for prop_name, prop_value in property_filters.items():
                traversal_chain = traversal_chain.has(prop_name, prop_value)
        
        results = await traversal_chain.limit(limit).project("id", "label", "properties")
            .by(T.id)
            .by(T.label)
            .by(__.valueMap(True))
            .toList()
        return [{**r, 'id': str(r["id"])} for r in results]

    
    async def find_edges(
        self,
        label: Optional[str] = None,
        property_filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        traversal_chain = self.g.E()
        if label:
            traversal_chain = traversal_chain.hasLabel(label)
        if property_filters:
            for prop_name, prop_value in property_filters.items():
                traversal_chain = traversal_chain.has(prop_name, prop_value)

        results = await traversal_chain.limit(limit)
            .project('id', 'label', 'properties')
            .by(T.id)
            .by(T.label)
            .by(__.valueMap(True))
            .by(__.outV().id())
            .by(__.inV().id())
            .toList()
        return [{**r, 
            "id": str(r["id"]), 
            "outV": str(r["outV"]),
            "inV": str(r["inV"]) }
        for r in results ]
    
    async def create_vertex(
        self,
        label: str, 
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        t = self.g.addV(label)
        for prop_name, prop_value in properties.items():
            t= t.property(prop_name, prop_value)
        
        new_vertex = await t.project("id", "label", "properties")
        .by(T.id)
        .by(T.label)
        .by(__.valueMap(True))
        .next()

        new_vertex["id"] = str(new_vertex["id"])
        return new_vertex

    async def create_edge(
        self,
        label: str,
        source_id: str,
        target_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        source_vertex = await self.g.V(source_id).next()
        target_vertex = await self.g.V(target_id).next()

        if not source_vertex:
            raise ValueError(f"Source vertex with ID {source_id} not found.")

        if not target_vertex:
            raise ValueError(f"Target vertex with ID {target_id} not found.")

        t = self.g.V(source_vertex).addE(label).to(target_vertex)
        for prop_name, prop_value in properties.items():
            t = t.property(prop_name, prop_value)

        new_edge = await t.project("id", "label", "properties", "outV", "inV")
            .by(T.id)
            .by(T.label)
            .by(__.valueMap(True))
            .by(__.outV().id())
            .by(__.inV().id())
            .next()
        new_edge['id'] = str(new_edge['id'])
        new_edge['outV'] = str(new_edge['outV'])
        new_edge['inV'] = str(new_edge['inV'])
        return new_edge

    async def update_vertex_properties(
        self,
        vertex_id: str,
        properties: Dict[str, Any],
        replace_all: bool =False
    ) -> Optional[Dict[str, Any]]:
        vertex_exists = await self.g.V(vertex_id).hasNext()

        if not vertex_exists:
            return None
        
        t = self.g.V(vertex_id)

        if replace_all:
            current_props = await t.properties().key().toList()
            for prop_key in current_props:
                t = t.properties(prop_key).drop()

        for prop_name, prop_value in properties.items():
            t = t.property(prop_name, prop_value)

        updated_vertex = await t.project("id", "label", "properties")
            .by(T.id)
            .by(T.label)
            .by(__.valueMap(True))
            .next()
        updated_vertex['id'] = str(updated_vertex['id'])
        return updated_vertex

    async def update_edge_properties(
        self,
        edge_id: str,
        properties: Dict[str, Any],
        replace_all: bool = False
    ) -> Optional[Dict[str, Any]]:
        edge_exists = await self.g.E(edge_id).hasNext()

        if not edge_exists:
            return None

        t = self.g.E(edge_id)

        if replace_all:
            current_props = await t.properties().key().toList()
            for prop_key in current_props:
                t = t.properties(prop_key).drop()

        for prop_name, prop_value in properties.items():
            t = t.property(prop_name, prop_value)

        updated_edge = await t.project("id", "label", "properties", "outV", "inV")
            .by(T.id)
            .by(T.label)
            .by(__.valueMap(True))
            .by(__.outV().id())
            .by(__.inV().id())
            .next()
        updated_edge['id'] = str(updated_edge['id'])
        updated_edge['outV'] = str(updated_edge['outV'])
        updated_edge['inV'] = str(updated_edge['inV'])
        return updated_edge
    
    async def delete_vertex( self, vertex_id: str) -> bool:
        vertex_exists = await self.g.V(vertex_id).hasNext()
        if not vertex_exists:
            return False
        await self.g.V(vertex_id).drop().iterate()
        return True

    async def delete_edge(self, edge_id: str) -> bool:
        edge_exists = await self.g.E(edge_id).hasNext()
        if not edge_exists:
            return False
        await self.g.E(edge_id).drop().iterate()
        return True


