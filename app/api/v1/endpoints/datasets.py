from app.models.schemas import DatasetUploadRequest, DatasetUploadResponse
from app.models.graph_types import GraphTypes
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.core.context.user_context import UserContext
from app.core.services.analysis_manager import AnalysisManager
from app.core.services.user_manager import UserManager
from app.core.storage import active_datasets
from app.database.neo4j_connection import Neo4jConnection
from app.database.postgres import postgres_manager

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid

router = APIRouter()
user_manager = UserManager()

TRANSPORT_TO_GRAPH = {
    "bus": GraphTypes.BUS_GRAPH,
    "tram": GraphTypes.TRAM_GRAPH,
    "trolleybus": GraphTypes.TROLLEY_GRAPH,
    "minibus": GraphTypes.MINIBUS_GRAPH,
}

@router.post("/", response_model=DatasetUploadResponse)
async def upload_dataset(
    data: DatasetUploadRequest,
    user_ctx: UserContext = Depends(user_manager.get_context),
    db = Depends(postgres_manager.get_db)
):
    graph_type = TRANSPORT_TO_GRAPH[data.transport_type]

    dataset_id = str(uuid.uuid4())
    dataset_name = f"{data.transport_type.capitalize()} routes — {data.city}"

    try:
        # Создаём граф в Neo4j — для всех (и гостей, и пользователей)
        analysis_context = AnalysisContext(
            city_name=data.city,
            graph_name=dataset_id,
            graph_type=graph_type,
            metric_calculation_context=MetricCalculationContext(),
            need_create_graph=True
        )

        manager = AnalysisManager()
        manager.process(analysis_context)

        # Сохраняем в active_datasets с контекстом
        active_datasets[dataset_id] = {
            "name": dataset_name,
            "analysis_context": analysis_context,
            "user_email": user_ctx.email if user_ctx.type == "user" else None,
            "guest_token": user_ctx.guest_token if user_ctx.type == "guest" else None,
        }

        # Только пользователи → сохраняются в PostgreSQL
        if user_ctx.type == "user":
            await db.execute(
                "INSERT INTO datasets (id, email, city, transport_type, name) VALUES ($1, $2, $3, $4, $5)",
                dataset_id, user_ctx.email, data.city, data.transport_type, dataset_name
            )
        return DatasetUploadResponse(dataset_id=dataset_id, name=dataset_name)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dataset: {str(e)}")
    

@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: str,
    user_ctx: UserContext = Depends(user_manager.get_context),
    db = Depends(postgres_manager.get_db)
):
    if user_ctx.type != "user":
        raise HTTPException(status_code=401, detail="Only verified users can delete datasets")

    # Проверка владения через PostgreSQL
    row = await db.fetchrow(
        "SELECT id FROM datasets WHERE id = $1 AND email = $2",
        dataset_id, user_ctx.email
    )
    if not row:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied")

    # Проверка наличия в active_datasets
    dataset = active_datasets.get(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not loaded in memory")

    ctx = dataset["analysis_context"]
    db_params = ctx.db_graph_parameters

    connection = Neo4jConnection()
    try:
        # --- Удаление графа GDS ---
        try:
            connection.run(f"CALL gds.graph.drop('{ctx.graph_name}')")
        except Exception as e:
            print(f"GDS graph drop failed (ignored): {e}")

        # --- Удаление основных узлов и отношений ---
        for rels_name, node_name in [(db_params.main_rels_name, db_params.main_node_name),
                                     (getattr(db_params, 'secondary_rels_name', None), 
                                      getattr(db_params, 'secondary_node_name', None))]:
            if node_name:
                try:
                    if rels_name:
                        connection.run(f"MATCH ()-[r:{rels_name}]->() DELETE r")
                    connection.run(f"MATCH (n:{node_name}) DELETE n")
                except Exception as e:
                    print(f"Failed to delete {node_name} or {rels_name}: {e}")
    finally:
        connection.close()

    # --- Удаление из in-memory кэша ---
    active_datasets.pop(dataset_id, None)

    # --- Удаление из базы ---
    await db.execute("DELETE FROM analysis_requests WHERE dataset_id = $1", dataset_id)
    await db.execute("DELETE FROM datasets WHERE id = $1", dataset_id)

    return {"message": f"Dataset {dataset_id} deleted"}
