from pydantic import BaseModel, Field, EmailStr
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
    BETWEENNESS = "betweenness"


# Auth Schemas
class RequestCodeRequest(BaseModel):
    email: EmailStr = Field(..., json_schema_extra={"example": "user@example.com"})


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
    cluster_id: int = Field(..., description="Значение кластера (например, 0, 1, 2…)")
    coordinates: List[float] = Field(..., json_schema_extra={"example": [30.33, 59.93]}, description="[longitude, latitude]")


class ClusterRequest(BaseModel):
    dataset_id: str = Field(..., json_schema_extra={"example": "abc123"})
    method: ClusteringMethod = Field(..., description="Метод кластеризации")


class ClusterResponse(BaseModel):
    dataset_id: str
    type: ClusteringMethod = Field("cluster", json_schema_extra={"example": "cluster"})
    nodes: List[ClusterNode]


class MetricNode(BaseModel):
    id: str
    name: str
    metric: float = Field(..., description="Значение выбранной метрики")
    coordinates: List[float] = Field(..., json_schema_extra={"example": [30.33, 59.93]}, description="[longitude, latitude]")


class MetricAnalysisRequest(BaseModel):
    dataset_id: str = Field(..., json_schema_extra={"example": "abc123"})
    metric: MetricType = Field(...)


class MetricAnalysisResponse(BaseModel):
    dataset_id: str
    type: MetricType = Field("metric", json_schema_extra={"example": "metric"})
    nodes: List[MetricNode]
