from enum import Enum
import app.database.graph_db_manager as GraphDbManager

"""
    Список типов сетей с соответсвующими конструкторами для классов работающими с бд
"""


class GraphTypes(Enum):
    BUS_GRAPH = GraphDbManager.BusGraphDBManager
    TRAM_GRAPH = GraphDbManager.TramGraphDBManager
    TROLLEY_GRAPH = GraphDbManager.TrolleyGraphDBManager
    MINIBUS_GRAPH = GraphDbManager.MiniBusGraphDBManager
