from enum import Enum
from app.database.transport_db_manager import BusGraphDBManager, TramGraphDBManager, TrolleyGraphDBManager, MiniBusGraphDBManager

"""
    Список типов сетей с соответствующими конструкторами для классов работающими с бд
"""


class GraphTypes(Enum):
    BUS_GRAPH = BusGraphDBManager
    TRAM_GRAPH = TramGraphDBManager
    TROLLEY_GRAPH = TrolleyGraphDBManager
    MINIBUS_GRAPH = MiniBusGraphDBManager
