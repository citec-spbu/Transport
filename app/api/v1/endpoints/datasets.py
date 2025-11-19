from fastapi import APIRouter, HTTPException
from app.models.schemas import DatasetUploadRequest, DatasetUploadResponse
import uuid

from app.core.services.analysis_manager import AnalysisManager
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.models.graph_types import GraphTypes
from app.database.neo4j_connection import Neo4jConnection

router = APIRouter()

# Поддерживаемые типы транспорта
TRANSPORT_TO_GRAPH = {
    "bus": GraphTypes.BUS_GRAPH,
    "tram": GraphTypes.TRAM_GRAPH,
    "trolleybus": GraphTypes.TROLLEY_GRAPH,
    "minibus": GraphTypes.MINIBUS_GRAPH,
}


active_datasets = {}


@router.post("/", response_model=DatasetUploadResponse)
async def upload_dataset(data: DatasetUploadRequest):

    # Проверяем только тип транспорта
    if data.transport_type not in TRANSPORT_TO_GRAPH:
        raise HTTPException(
            status_code=400,
            detail={"error": "Unknown transport type"}
        )

    graph_type = TRANSPORT_TO_GRAPH[data.transport_type]

    dataset_id = str(uuid.uuid4())
    dataset_name = f"{data.transport_type.capitalize()} routes — {data.city}"

    try:
        analysis_context = AnalysisContext(
            city_name=data.city,                      
            graph_type=graph_type,
            metric_calculation_context=MetricCalculationContext(),
            need_create_graph=True
        )

        manager = AnalysisManager()
        manager.process(analysis_context)

        # сохраняем датасет
        active_datasets[dataset_id] = {
            "id": dataset_id,
            "name": dataset_name,
            "analysis_context": analysis_context,
        }

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
    if dataset_id not in active_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset = active_datasets[dataset_id]

    try:
        ctx = dataset["analysis_context"]
        db_params = ctx.db_graph_parameters

        connection = Neo4jConnection()

        # 1. Удаляем GDS граф
        try:
            query = f"CALL gds.graph.drop('{db_params.graph_name}', false)"
            connection.run(query)
        except Exception:
            pass

        # 2. Удаляем основные отношения
        try:
            query = f"""
                MATCH ()-[r:{db_params.main_rels_name}]->()
                DELETE r
            """
            connection.run(query)
        except Exception:
            pass

        # 3. Удаляем основные узлы
        try:
            query = f"""
                MATCH (n:{db_params.main_node_name})
                DELETE n
            """
            connection.run(query)
        except Exception:
            pass

        # 4. При наличии — удаляем вторичные узлы/связи
        if getattr(db_params, "secondary_node_name", None):
            try:
                q = f"MATCH ()-[r:{db_params.secondary_rels_name}]->() DELETE r"
                connection.run(q)
            except Exception:
                pass

            try:
                q = f"MATCH (n:{db_params.secondary_node_name}) DELETE n"
                connection.run(q)
            except Exception:
                pass

        connection.close()
        active_datasets.pop(dataset_id)

        return {"message": f"Dataset {dataset_id} deleted"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete dataset: {str(e)}"
        )
