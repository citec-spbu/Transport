from typing import List, Tuple

from app.core.services.parsers import BusGraphParser, TrolleyGraphParser, TramGraphParser, MiniBusGraphParser
from app.database.graph_db_manager import OneTypeNodeDBManager
from abc import abstractmethod

class TransportNetworkGraphDBManager(OneTypeNodeDBManager):

    def create_node_query(self) -> str:
        return f"""
        UNWIND $rows AS row
        WITH row WHERE row.name IS NOT NULL
        MERGE (s:{self.db_graph_parameters.main_node_name} {{name: row.name}})
            SET s.location = point({{latitude: row.yCoordinate, longitude: row.xCoordinate}}),
                s.roteList = row.roteList,
                s.isCoordinateApproximate = row.isCoordinateApproximate
        RETURN COUNT(*) AS total
        """

    def create_relationships_query(self) -> str:
        return f"""
        UNWIND $rows AS path
        MATCH (u:{self.db_graph_parameters.main_node_name} {{name: path.startStop}})
        MATCH (v:{self.db_graph_parameters.main_node_name} {{name: path.endStop}})
        MERGE (u)-[r:{self.db_graph_parameters.main_rels_name} {{name: path.name}}]->(v)
            SET r.duration = path.duration,
                r.route = path.route
        RETURN COUNT(*) AS total
        """
    
    def get_bd_all_node_query_graph(self):
        return f'''
        MATCH (s:{self.db_graph_parameters.main_node_name})
        RETURN 
            ID(s) AS id,
            s.roteList AS roteList, 
            s.location.longitude AS x, 
            s.location.latitude AS y, 
            s.name AS name, 
            s.isCoordinateApproximate AS isCoordinateApproximate
        '''

    def get_bd_all_rels_query_graph(self):
        return f'''
        MATCH (u:{self.db_graph_parameters.main_node_name})
        -[r:{self.db_graph_parameters.main_rels_name}]->
        (v:{self.db_graph_parameters.main_node_name})
        RETURN
            u.name AS first_stop_name, 
            v.name AS second_stop_name, 
            r.duration AS duration
        '''

    def get_constraint_list(self):
        return [
            f"CREATE CONSTRAINT IF NOT EXISTS FOR (s:{self.db_graph_parameters.main_node_name}) REQUIRE s.name IS UNIQUE",
            f"CREATE INDEX IF NOT EXISTS FOR ()-[r:{self.db_graph_parameters.main_rels_name}]-() ON r.name"
        ]
    
    @abstractmethod
    def get_graph(self):
        pass

    @abstractmethod
    def get_node_name(self):
        pass

    @abstractmethod
    def get_rels_name(self):
        pass

    @abstractmethod
    def get_weight(self):
        pass


class BusGraphDBManager(TransportNetworkGraphDBManager):

    def get_graph(self) -> Tuple[List[dict], List[dict]]:
        parser = BusGraphParser(self.city_name)
        nodes, relationships = parser.parse()
        return list(nodes.values()), relationships

    def get_node_name(self) -> str:
        return f"{self.city_name}BusStop"

    def get_rels_name(self) -> str:
        return f"{self.city_name}BusRouteSegment"

    def get_weight(self) -> str:
        return "duration"

    def node_geometry_identity(self) -> str:
        return "location"


class TrolleyGraphDBManager(BusGraphDBManager):
    def get_graph(self) -> Tuple[List[dict], List[dict]]:
        parser = TrolleyGraphParser(self.city_name)
        nodes, relationships = parser.parse()
        return list(nodes.values()), relationships

    def get_node_name(self) -> str:
        return f"{self.city_name}TrolleyStop"

    def get_rels_name(self) -> str:
        return f"{self.city_name}TrolleyRouteSegment"


class TramGraphDBManager(BusGraphDBManager):
    def get_graph(self) -> Tuple[List[dict], List[dict]]:
        parser = TramGraphParser(self.city_name)
        nodes, relationships = parser.parse()
        return list(nodes.values()), relationships

    def get_node_name(self) -> str:
        return f"{self.city_name}TramStop"

    def get_rels_name(self) -> str:
        return f"{self.city_name}TramRouteSegment"


class MiniBusGraphDBManager(BusGraphDBManager):
    def get_graph(self) -> Tuple[List[dict], List[dict]]:
        parser = MiniBusGraphParser(self.city_name)
        nodes, relationships = parser.parse()
        return list(nodes.values()), relationships

    def get_node_name(self) -> str:
        return f"{self.city_name}MiniBusStop"

    def get_rels_name(self) -> str:
        return f"{self.city_name}MiniBusRouteSegment"

