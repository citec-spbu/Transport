from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ClusterRequest, ClusterResponse, MetricAnalysisRequest, MetricAnalysisResponse,
    ClusterNode, MetricNode
)
from datasets import active_datasets
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.core.services.analysis_manager import AnalysisManager

router = APIRouter()


@router.post("/cluster", response_model=ClusterResponse)
async def cluster_analysis(req: ClusterRequest):

    # Проверка идентификатора датасета
    if req.dataset_id not in active_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    dataset = active_datasets[req.dataset_id]

    # Контекст для кластеризации
    metric_context = MetricCalculationContext(
        need_leiden_clusterization=(req.method == "leiden"),
        need_louvain_clusterization=(req.method == "louvain")
    )
    
    analysis_context = AnalysisContext(
        city_name=dataset["ru_city_name"],
        graph_type=dataset["graph_context"].graph_type,
        metric_calculation_context=metric_context,
        need_prepare_data=True
    )

    # Проведение кластеризации и обработка результатов
    manager = AnalysisManager()
    nodes = manager.process(analysis_context)

    cluster_nodes = [ClusterNode(**n) for n in nodes]

    return ClusterResponse(dataset_id=req.dataset_id, type=req.method, nodes=cluster_nodes)


@router.post("/metric", response_model=MetricAnalysisResponse)
async def metric_analysis(req: MetricAnalysisRequest):
    
    # Проверка индентификатора датасета
    if req.dataset_id not in active_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset = active_datasets[req.dataset_id]

    # Контекст для анализа метрик
    metric_context = MetricCalculationContext(
        need_page_rank=(req.metric == "pagerank"),
        need_betweenness=(req.metric == "betweenness")
    )

    analysis_context = AnalysisContext(
        city_name=dataset["ru_city_name"],
        graph_type=dataset["graph_context"].graph_type,
        metric_calculation_context=metric_context,
        need_prepare_data=True
    )

    manager = AnalysisManager()
    nodes = manager.process(analysis_context)

    metric_nodes = [MetricNode(**n) for n in nodes]

    return MetricAnalysisResponse(dataset_id=req.dataset_id, metric=req.metric, nodes=metric_nodes)
