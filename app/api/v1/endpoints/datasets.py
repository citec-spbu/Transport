from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import DatasetUploadRequest, DatasetUploadResponse
import uuid

from app.core.services.analysis_manager import AnalysisManager
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.models.graph_types import GraphTypes
from app.database.neo4j_connection import Neo4jConnection
from app.api.v1.endpoints.deps import get_user_or_guest, UserContext
from app.api.v1.endpoints.postgres import get_db
from datetime import datetime, timezone
from app.api.v1.endpoints.storage import active_datasets

router = APIRouter()

# Поддерживаемые типы транспорта
TRANSPORT_TO_GRAPH = {
    "bus": GraphTypes.BUS_GRAPH,
    "tram": GraphTypes.TRAM_GRAPH,
    "trolleybus": GraphTypes.TROLLEY_GRAPH,
    "minibus": GraphTypes.MINIBUS_GRAPH,
}

@router.post("/", response_model=DatasetUploadResponse)
async def upload_dataset(
    data: DatasetUploadRequest,
    user_ctx: UserContext = Depends(get_user_or_guest),
    db = Depends(get_db)
):
    if user_ctx.type == "anonymous":
        raise HTTPException(status_code=401, detail="Please get a guest token or verify email")
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
            "id": dataset_id,
            "name": dataset_name,
            "analysis_context": analysis_context,
            "owner_email": user_ctx.email if user_ctx.type == "user" else None,
            "guest_token": user_ctx.guest_token if user_ctx.type == "guest" else None,
            "created_at": datetime.now(timezone.utc),
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
    user_ctx: UserContext = Depends(get_user_or_guest),
    db = Depends(get_db)
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

    # Удаляем из Neo4j
    if dataset_id not in active_datasets:
        raise HTTPException(status_code=404, detail="Dataset not loaded in memory")

    dataset = active_datasets[dataset_id]

    try:
        ctx = dataset["analysis_context"]
        db_params = ctx.db_graph_parameters

        connection = Neo4jConnection()

        # 1. Удаляем GDS граф
        try:
            query = f"CALL gds.graph.drop('{ctx.graph_name}')"
            connection.run(query)
            print(f"GDS graph '{db_params.graph_name}' deleted")
        except Exception as e:
            print(f"GDS graph drop failed (ignored): {e}")

        # 2. Удаляем основные отношения
        try:
            query = f"""
                MATCH ()-[r:{db_params.main_rels_name}]->()
                DELETE r
            """
            connection.run(query)
            print(f"Deleted {db_params.main_rels_name} relationships")
        except Exception as e:
            print(f"Failed to delete relationships: {e}")

        # 3. Удаляем основные узлы
        try:
            query = f"""
                MATCH (n:{db_params.main_node_name})
                DELETE n
            """
            connection.run(query)
            print(f"Deleted {db_params.main_node_name} nodes")
        except Exception as e:
            print(f"Failed to delete nodes: {e}")

        # 4. При наличии — удаляем вторичные узлы/связи
        if getattr(db_params, "secondary_node_name", None):
            try:
                connection.run(f"MATCH ()-[r:{db_params.secondary_rels_name}]->() DELETE r")
                connection.run(f"MATCH (n:{db_params.secondary_node_name}) DELETE n")
                print(f"Deleted secondary nodes/rels")
            except Exception as e:
                print(f"Failed to delete secondary nodes/rels: {e}")

        connection.close()

        # Удаляем из in-memory кэша
        active_datasets.pop(dataset_id)

        # удаляем из базы
        await db.execute("DELETE FROM analysis_requests WHERE dataset_id = $1", dataset_id)
        await db.execute("DELETE FROM datasets WHERE id = $1", dataset_id)

        return {"message": f"Dataset {dataset_id} deleted"}

    except Exception as e:
        print(f"Critical error in delete_dataset: {repr(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete dataset: {str(e)}"
        )
