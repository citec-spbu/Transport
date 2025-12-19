from app.models.schemas import (
    ClusterRequest, ClusterResponse, MetricAnalysisRequest, MetricAnalysisResponse,
    ClusterNode, MetricNode, ClusteringMethod, MetricType
)
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.core.services.analysis_manager import AnalysisManager
from app.core.storage import active_datasets

from fastapi import APIRouter, HTTPException
from typing import Optional
import copy

router = APIRouter()

@router.post("/cluster", response_model=ClusterResponse)
async def cluster_analysis(
    req: ClusterRequest
):

    # Проверка идентификатора датасета
    if req.dataset_id not in active_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset = active_datasets[req.dataset_id]

    analysis_context = copy.deepcopy(dataset["analysis_context"])
    analysis_context.metric_calculation_context = MetricCalculationContext(
        need_leiden_clusterization=(req.method == ClusteringMethod.LEIDEN),
        need_louvain_clusterization=(req.method == ClusteringMethod.LOUVAIN)
    )
    analysis_context.need_prepare_data = True
    analysis_context.need_create_graph = False

    manager = AnalysisManager()
    try:
        nodes = manager.process(analysis_context)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"External service error"
        )

    cluster_nodes = [ClusterNode(**n) for n in nodes]

    return ClusterResponse(dataset_id=req.dataset_id, type=req.method, nodes=cluster_nodes)


@router.post("/metric", response_model=MetricAnalysisResponse)
async def metric_analysis(
    req: MetricAnalysisRequest
):
    
    # Проверка индентификатора датасета
    if req.dataset_id not in active_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")

    dataset = active_datasets[req.dataset_id]

    analysis_context = copy.deepcopy(dataset["analysis_context"])
    analysis_context.metric_calculation_context = MetricCalculationContext(
        need_pagerank=(req.metric == MetricType.PAGERANK),
        need_betweenness=(req.metric == MetricType.BETWEENNESS)
    )
    analysis_context.need_prepare_data = True
    analysis_context.need_create_graph = False

    manager = AnalysisManager()
    try:
        nodes = manager.process(analysis_context)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"External service error"
        )

    metric_nodes = [MetricNode(**n) for n in nodes]

    return MetricAnalysisResponse(dataset_id=req.dataset_id, metric=req.metric, nodes=metric_nodes)
