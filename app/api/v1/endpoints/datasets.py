from fastapi import APIRouter, HTTPException
from app.models.schemas import DatasetUploadRequest, DatasetUploadResponse
import uuid
from datetime import datetime
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from app.core.services.analysis_manager import AnalysisManager
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.models.graph_types import GraphTypes
from app.database.neo4j_connection import Neo4jConnection

router = APIRouter()

# Поддерживаемые города и типы транспорта с маппингом на GraphTypes
SUPPORTED_CONFIGS = {
    "Saint Petersburg": {
        "ru_name": "Санкт-Петербург",
        "bus": GraphTypes.BUS_GRAPH,
        "metro": GraphTypes.ROAD_GRAPH,  # TODO: Добавить метро если будет
        "tram": GraphTypes.ROAD_GRAPH,
        "trolleybus": GraphTypes.ROAD_GRAPH,
    },
    "Moscow": {
        "ru_name": "Москва",
        "bus": GraphTypes.BUS_GRAPH,
    }
}

# Хранилище активных датасетов и их контекстов
active_datasets = {}


@router.post("/", response_model=DatasetUploadResponse)
async def upload_dataset(data: DatasetUploadRequest):
    """Загрузить новый набор данных"""
    # Проверяем поддерживаемые города
    if data.city not in SUPPORTED_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail={"error": "Unknown city or transport type"}
        )
    
    city_config = SUPPORTED_CONFIGS[data.city]
    ru_city_name = city_config["ru_name"]
    
    # Проверяем поддерживаемые типы транспорта
    if data.transport_type not in city_config or data.transport_type == "ru_name":
        raise HTTPException(
            status_code=400,
            detail={"error": "Unknown city or transport type"}
        )
    
    dataset_id = str(uuid.uuid4())
    dataset_name = f"{data.transport_type.capitalize()} routes — {data.city}"
    
    try:
        # Получаем тип графика для этого города и типа транспорта
        graph_type = city_config[data.transport_type]
        
        # Создаём контекст анализа для загрузки данных в BD
        analysis_context = AnalysisContext(
            city_name=ru_city_name,
            graph_type=graph_type,
            metric_calculation_context=MetricCalculationContext(),
            need_prepare_data=False
        )
        
        # Загружаем данные в Neo4j через AnalysisManager
        manager = AnalysisManager()
        manager.process(analysis_context)
        
        # Сохраняем информацию о датасете
        dataset_info = {
            "id": dataset_id,
            "name": dataset_name,
            "transport_type": data.transport_type,
            "city": data.city,
            "created_at": datetime.now().isoformat(),
            "analysis_context": analysis_context
        }
        
        active_datasets[dataset_id] = dataset_info
        
        return DatasetUploadResponse(
            dataset_id=dataset_id,
            name=dataset_name
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create dataset: {str(e)}"
        )


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Удалить набор данных"""
    if dataset_id not in active_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset = active_datasets[dataset_id]
    
    try:
        # Получаем параметры графа для очистки
        graph_context = dataset["graph_context"]
        db_params = graph_context.neo4j_DB_graph_parameters
        
        # Очищаем граф в Neo4j
        connection = Neo4jConnection()
        
        # 1. Удаляем GDS проекцию графа если она существует
        try:
            drop_graph_query = f"CALL gds.graph.drop('{graph_context.graph_name}', false)"
            connection.run(drop_graph_query)
            print(f"[INFO] Dropped GDS graph projection: {graph_context.graph_name}")
        except Exception as e:
            print(f"[WARNING] Could not drop GDS graph projection: {e}")
        
        # 2. Удаляем все связи главного типа
        delete_rels_query = f"""
            MATCH ()-[r:{db_params.main_rels_name}]->()
            DELETE r
            RETURN count(r) AS deleted_relationships
        """
        try:
            result = connection.run(delete_rels_query)
            print(f"[INFO] Deleted relationships: {result}")
        except Exception as e:
            print(f"[WARNING] Could not delete relationships: {e}")
        
        # 3. Удаляем все узлы главного типа
        delete_nodes_query = f"""
            MATCH (n:{db_params.main_node_name})
            DELETE n
            RETURN count(n) AS deleted_nodes
        """
        try:
            result = connection.run(delete_nodes_query)
            print(f"[INFO] Deleted nodes: {result}")
        except Exception as e:
            print(f"[WARNING] Could not delete nodes: {e}")
        
        # 4. Если есть вторичные узлы и связи, удаляем их
        if hasattr(db_params, 'secondary_node_name') and db_params.secondary_node_name:
            # Удаляем вторичные связи
            delete_secondary_rels_query = f"""
                MATCH ()-[r:{db_params.secondary_rels_name}]->()
                DELETE r
                RETURN count(r) AS deleted_secondary_relationships
            """
            try:
                result = connection.run(delete_secondary_rels_query)
                print(f"[INFO] Deleted secondary relationships: {result}")
            except Exception as e:
                print(f"[WARNING] Could not delete secondary relationships: {e}")
            
            # Удаляем вторичные узлы
            delete_secondary_nodes_query = f"""
                MATCH (n:{db_params.secondary_node_name})
                DELETE n
                RETURN count(n) AS deleted_secondary_nodes
            """
            try:
                result = connection.run(delete_secondary_nodes_query)
                print(f"[INFO] Deleted secondary nodes: {result}")
            except Exception as e:
                print(f"[WARNING] Could not delete secondary nodes: {e}")
        
        connection.close()
        
        # Удаляем из активных датасетов
        active_datasets.pop(dataset_id)
        
        return {"message": f"Dataset {dataset_id} deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete dataset: {str(e)}"
        )
