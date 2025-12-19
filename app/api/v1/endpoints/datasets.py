from app.models.schemas import (
    DatasetUploadRequest, DatasetUploadResponse, DatasetListResponse, DatasetInfo
)
from app.models.graph_types import GraphTypes
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.core.context.user_context import UserContext
from app.core.services.analysis_manager import AnalysisManager
from app.core.services.user_manager import UserManager
from app.core.storage import active_datasets
from app.database.postgres import postgres_manager

from fastapi import APIRouter, HTTPException, Depends
from uuid import UUID
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
    """Загружает новый датасет маршрутов для города.

    Строит граф в Neo4j/GDS на основе выбранного типа
    транспорта и возвращает идентификатор полученного датасета.
    """
    # Проверяем дубликаты через active_datasets
    for dataset in active_datasets.values():
        # Для пользователей проверяем по user_id
        if user_ctx.type == "user" and dataset.get("user_id") == user_ctx.user_id:
            if dataset.get("city_name") == data.city and dataset.get("transport_type") == data.transport_type:
                raise HTTPException(status_code=409, detail="Dataset with this city and transport type already exists")
        # Для гостей проверяем по guest_token
        elif user_ctx.type == "guest" and dataset.get("guest_token") == user_ctx.guest_token:
            if dataset.get("city_name") == data.city and dataset.get("transport_type") == data.transport_type:
                raise HTTPException(status_code=409, detail="Dataset with this city and transport type already exists")
    
    graph_type = TRANSPORT_TO_GRAPH[data.transport_type]

    dataset_id = uuid.uuid4()
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
            "city_name": data.city,
            "transport_type": data.transport_type,
            "analysis_context": analysis_context,
            "user_id": user_ctx.user_id if user_ctx.type == "user" else None,
            "guest_token": user_ctx.guest_token if user_ctx.type == "guest" else None,
        }

        # Только пользователи → сохраняются в PostgreSQL
        if user_ctx.type == "user":
            await db.execute(
                "INSERT INTO datasets (id, user_id, city, transport_type, name) VALUES ($1, $2, $3, $4, $5)",
                dataset_id, user_ctx.user_id, data.city, data.transport_type, dataset_name
            )
        return DatasetUploadResponse(dataset_id=dataset_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dataset: {str(e)}")


@router.get("/", response_model=DatasetListResponse)
async def list_datasets(user_ctx: UserContext = Depends(user_manager.get_context)):
    datasets = []
    for dataset_id, ds in active_datasets.items():
        if user_ctx.type == "user" and ds.get("user_id") != user_ctx.user_id:
            continue
        if user_ctx.type == "guest" and ds.get("guest_token") != user_ctx.guest_token:
            continue

        datasets.append(DatasetInfo(
            dataset_id=dataset_id,
            city=ds["city_name"],
            transport_type=ds["transport_type"]
        ))
    return DatasetListResponse(datasets=datasets)

@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: UUID,
    user_ctx: UserContext = Depends(user_manager.get_context),
    db = Depends(postgres_manager.get_db)
):
    # Гости
    if user_ctx.type == "guest":
        dataset = active_datasets.get(dataset_id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        if dataset.get("guest_token") != user_ctx.guest_token:
            raise HTTPException(status_code=403, detail="Access denied")
        active_datasets.pop(dataset_id, None)
        return {"message": f"Dataset {dataset_id} deleted"}

    # Пользователи
    if user_ctx.type == "user":
        row = await db.fetchrow(
            "SELECT id, user_id FROM datasets WHERE id = $1",
            dataset_id
        )
        if not row or not active_datasets.get(dataset_id):
            raise HTTPException(status_code=404, detail="Dataset not found")
        if row["user_id"] != user_ctx.user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        active_datasets.pop(dataset_id, None)

        await db.execute("DELETE FROM datasets WHERE id = $1", dataset_id)
        return {"message": f"Dataset {dataset_id} deleted"}

    # Анонимные — нет прав на удаление
    raise HTTPException(status_code=401, detail="Unauthorized")
