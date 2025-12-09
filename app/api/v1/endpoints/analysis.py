from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import (
    ClusterRequest, ClusterResponse, MetricAnalysisRequest, MetricAnalysisResponse,
    ClusterNode, MetricNode
)
from app.api.v1.endpoints.datasets import active_datasets
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.core.services.analysis_manager import AnalysisManager
from app.api.v1.endpoints.deps import get_current_user_email
from app.api.v1.endpoints.postgres import get_db
import copy

router = APIRouter()


@router.post("/cluster", response_model=ClusterResponse)
async def cluster_analysis(
    req: ClusterRequest,
    email: str | None = Depends(get_current_user_email),  # ← получаем email (или None)
    db = Depends(get_db)  # ← подключение к PostgreSQL
):

    # Проверка идентификатора датасета
    if req.dataset_id not in active_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset = active_datasets[req.dataset_id]

    # Копируем старый контекст и меняем только параметры для кластеризации
    analysis_context = copy.deepcopy(dataset["analysis_context"])
    analysis_context.metric_calculation_context = MetricCalculationContext(
        need_leiden_clusterization=(req.method == "leiden"),
        need_louvain_clusterization=(req.method == "louvain")
    )
    analysis_context.need_prepare_data = True
    analysis_context.need_create_graph = False

    # Проведение кластеризации и обработка результатов
    manager = AnalysisManager()
    nodes = manager.process(analysis_context)

    cluster_nodes = [ClusterNode(**n) for n in nodes]

    if email is not None:
        await db.execute(
            """
            INSERT INTO analysis_requests (email, type, dataset_id, method)
            VALUES ($1, $2, $3, $4)
            """,
            email, "cluster", req.dataset_id, req.method
        )

    return ClusterResponse(dataset_id=req.dataset_id, type=req.method, nodes=cluster_nodes)


@router.post("/metric", response_model=MetricAnalysisResponse)
async def metric_analysis(
    req: MetricAnalysisRequest,
    email: str | None = Depends(get_current_user_email),  # ← получаем email (или None)
    db = Depends(get_db)
):
    
    # Проверка индентификатора датасета
    if req.dataset_id not in active_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset = active_datasets[req.dataset_id]

    # Копируем старый контекст и меняем только параметры для анализа метрик
    analysis_context = copy.deepcopy(dataset["analysis_context"])
    analysis_context.metric_calculation_context = MetricCalculationContext(
        need_pagerank=(req.metric == "pagerank"),
        need_betweenness=(req.metric == "betweenness")
    )
    analysis_context.need_prepare_data = True
    analysis_context.need_create_graph = False

    manager = AnalysisManager()
    nodes = manager.process(analysis_context)

    metric_nodes = [MetricNode(**n) for n in nodes]

    if email is not None:
        await db.execute(
            """
            INSERT INTO analysis_requests (email, type, dataset_id, method)
            VALUES ($1, $2, $3, $4)
            """,
            email, "metric", req.dataset_id, req.metric
        )

    return MetricAnalysisResponse(dataset_id=req.dataset_id, metric=req.metric, nodes=metric_nodes)
