from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ClusterRequest, ClusterResponse, MetricAnalysisRequest, MetricAnalysisResponse,
    ClusterNode, MetricNode, ClusteringMethod, MetricType, ClusterStatistics
)
from app.api.v1.endpoints.datasets import active_datasets
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.core.services.analysis_manager import AnalysisManager
import copy

router = APIRouter()


@router.post("/cluster", response_model=ClusterResponse)
async def cluster_analysis(req: ClusterRequest):
    """
    Perform clustering analysis for the specified dataset and return cluster nodes and summary statistics.
    
    Parameters:
        req (ClusterRequest): Request containing `dataset_id` (identifier of the dataset to analyze) and `method` (clustering method to apply).
    
    Returns:
        ClusterResponse: Contains the requested `dataset_id`, the `method` used, a list of `ClusterNode` objects for each node in the result, and a `ClusterStatistics` object summarizing the clustering.
    
    Raises:
        HTTPException: 404 if the specified dataset_id is not found.
        HTTPException: 502 if the external analysis processing fails.
    """
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
        result = manager.process(analysis_context)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"External service error"
        )

    cluster_nodes = [ClusterNode(**n) for n in result["nodes"]]
    statistics = ClusterStatistics(**result["statistics"])
    
    return ClusterResponse(
        dataset_id=req.dataset_id,
        method=req.method,
        nodes=cluster_nodes,
        statistics=statistics
    )


@router.post("/metric", response_model=MetricAnalysisResponse)
async def metric_analysis(req: MetricAnalysisRequest):
    """
    Run graph metric analysis for the specified dataset.
    
    Configures the analysis context to compute the requested metric and returns per-node metric results.
    
    Parameters:
        req (MetricAnalysisRequest): Request payload containing the dataset identifier and the metric to compute.
    
    Returns:
        MetricAnalysisResponse: Response containing the original dataset_id, the requested metric_type, and a list of nodes with their computed metric values.
    
    Raises:
        HTTPException: 404 if the dataset_id is not found.
        HTTPException: 502 if an error occurs while processing the analysis (external service error).
    """
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
        result = manager.process(analysis_context)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"External service error"
        )

    metric_nodes = [MetricNode(**n) for n in result["nodes"]]
    return MetricAnalysisResponse(dataset_id=req.dataset_id, metric_type=req.metric, nodes=metric_nodes)