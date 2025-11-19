from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class TransportType(str, Enum):
    BUS = "bus"
    TRAM = "tram"
    TROLLEY = "trolleybus"
    MINIBUS = "minibus"

class ClusteringMethod(str, Enum):
    LEIDEN = "leiden"
    LOUVAIN = "louvain"


class MetricType(str, Enum):
    PAGERANK = "pagerank"
    BETWEENNESS = "betweenness"


# Auth Schemas
class RequestCodeRequest(BaseModel):
    email: str = Field(..., example="user@example.com")


class RequestCodeResponse(BaseModel):
    message: str = Field(..., example="Verification code sent")


class VerifyCodeRequest(BaseModel):
    email: str = Field(..., example="user@example.com")
    code: str = Field(..., example="123456")


class VerifyCodeResponse(BaseModel):
    token: str
    email: str


class GuestTokenResponse(BaseModel):
    token: str = Field(..., example="guest-token")


# Dataset Schemas
class DatasetUploadRequest(BaseModel):
    transport_type: str = Field(..., example="bus", description="Тип транспорта")
    city: str = Field(..., example="Saint Petersburg", description="Город для набора данных")


class DatasetUploadResponse(BaseModel):
    dataset_id: str = Field(..., example="abc123")
    name: str = Field(..., example="Bus routes — Saint Petersburg")


# Analysis Schemas
class ClusterNode(BaseModel):
    id: str
    name: str
    cluster_id: int = Field(..., description="Значение кластера (например, 0, 1, 2…)")
    coordinates: List[float] = Field(..., example=[30.33, 59.93], description="[longitude, latitude]")


class ClusterRequest(BaseModel):
    dataset_id: str = Field(..., example="abc123")
    method: ClusteringMethod = Field(..., description="Метод кластеризации")


class ClusterResponse(BaseModel):
    dataset_id: str
    type: str = Field("cluster", example="cluster")
    nodes: List[ClusterNode]


class MetricNode(BaseModel):
    id: str
    name: str
    metric: float = Field(..., description="Значение выбранной метрики")
    coordinates: List[float] = Field(..., example=[30.33, 59.93], description="[longitude, latitude]")


class MetricAnalysisRequest(BaseModel):
    dataset_id: str = Field(..., example="abc123")
    metric: MetricType = Field(...)


class MetricAnalysisResponse(BaseModel):
    dataset_id: str
    type: str = Field("metric", example="metric")
    nodes: List[MetricNode]
