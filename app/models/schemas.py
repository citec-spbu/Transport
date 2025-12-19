from pydantic import BaseModel, Field, conlist, EmailStr
from typing import List, Optional
from uuid import UUID
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
    email: EmailStr = Field(..., json_schema_extra={"example": "user@example.com"})


class RequestCodeResponse(BaseModel):
    message: str = Field(..., json_schema_extra={"example": "Verification code sent"})
    token: Optional[str] = None


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
    dataset_id: UUID = Field(..., json_schema_extra={"example": "b361e37f-a5bc-436d-ac58-dfe573c29aac"})


class DatasetInfo(BaseModel):
    dataset_id: UUID
    city: str = Field(..., json_schema_extra={"example": "Saint Petersburg"})
    transport_type: TransportType

class DatasetListResponse(BaseModel):
    datasets: List[DatasetInfo]

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
    dataset_id: UUID = Field(..., json_schema_extra={"example": "b361e37f-a5bc-436d-ac58-dfe573c29aac"})
    method: ClusteringMethod = Field(..., description="Метод кластеризации")


class ClusterResponse(BaseModel):
    dataset_id: UUID
    type: ClusteringMethod = Field("cluster", json_schema_extra={"example": "cluster"})
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
    dataset_id: UUID = Field(..., json_schema_extra={"example": "b361e37f-a5bc-436d-ac58-dfe573c29aac"})
    metric_type: MetricType = Field(...)


class MetricAnalysisResponse(BaseModel):
    dataset_id: UUID
    metric_type: MetricType = Field("metric", json_schema_extra={"example": "metric"})
    nodes: List[MetricNode]
