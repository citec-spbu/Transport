from typing import List, Tuple

from app.core.context.analysis_context import AnalysisContext
from app.core.services.parsers import BusGraphParser, TrolleyGraphParser, TramGraphParser, MiniBusGraphParser
from database.graph_db_manager import OneTypeNodeDBManager


class TransportNetworkGraphDBManager(OneTypeNodeDBManager):

    def __init__(self, graph_analis_context: AnalysisContext):
        super().__init__(graph_analis_context)

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

