from pydantic import BaseModel, Field, conlist
from typing import List, Optional
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
    BETWEENNESS_CENTRALITY = "betweenness"


# Auth Schemas
class RequestCodeRequest(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "user@example.com"})


class RequestCodeResponse(BaseModel):
    message: str = Field(..., json_schema_extra={"example": "Verification code sent"})


class VerifyCodeRequest(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "user@example.com"})
    code: str = Field(..., json_schema_extra={"example": "123456"})


class VerifyCodeResponse(BaseModel):
    token: Optional[str] = None
    email: str


class GuestTokenResponse(BaseModel):
    token: str = Field(..., json_schema_extra={"example": "guest-token"})


# Dataset Schemas
class DatasetUploadRequest(BaseModel):
    transport_type: TransportType = Field(..., json_schema_extra={"example": "bus"}, description="Тип транспорта")
    city: str = Field(..., json_schema_extra={"example": "Бирск"}, description="Город для набора данных")


class DatasetUploadResponse(BaseModel):
    dataset_id: str = Field(..., json_schema_extra={"example": "abc123"})
    name: str = Field(..., json_schema_extra={"example": "Bus routes — Saint Petersburg"})


# Analysis Schemas
class ClusterNode(BaseModel):
    id: str
    name: str
    cluster_id: int = Field(..., description="Значение кластера")
    coordinates: conlist(float, min_length=2, max_length=2) = Field(
    ...,
    description="[longitude, latitude]",
    json_schema_extra={"example": [30.33, 59.93]}
)

class ClusterStatistics(BaseModel):
    modularity: float = Field(
        ..., 
        description="Модулярность (0-1, выше лучше)",
        json_schema_extra={"example": 0.45}
    )
    conductance: float = Field(
        ...,
        description="Проводимость (0-1, ниже лучше)",
        json_schema_extra={"example": 0.12}
    )
    coverage: float = Field(
        ...,
        description="Покрытие (0-1, выше лучше)",
        json_schema_extra={"example": 0.78}
    )

class ClusterRequest(BaseModel):
    dataset_id: str = Field(..., json_schema_extra={"example": "abc123"})
    method: ClusteringMethod = Field(..., description="Метод кластеризации")


class ClusterResponse(BaseModel):
    dataset_id: str
    method: ClusteringMethod
    nodes: List[ClusterNode]
    statistics: ClusterStatistics


class MetricNode(BaseModel):
    id: str
    name: str
    metric: float = Field(..., description="Значение выбранной метрики")
    coordinates: conlist(float, min_length=2, max_length=2) = Field(
    ...,
    description="[longitude, latitude]",
    json_schema_extra={"example": [30.33, 59.93]}
)

class MetricAnalysisRequest(BaseModel):
    dataset_id: str = Field(..., json_schema_extra={"example": "abc123"})
    metric_type: MetricType = Field(...)

class MetricAnalysisResponse(BaseModel):
    dataset_id: str
    metric_type: MetricType
    nodes: List[MetricNode]
