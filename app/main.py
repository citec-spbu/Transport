from app.models.graph_types import GraphTypes
from app.api.v1.router import api_router
from app.core.storage import active_datasets
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.database.postgres import postgres_manager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

TRANSPORT_TO_GRAPH = {
    "bus": GraphTypes.BUS_GRAPH,
    "tram": GraphTypes.TRAM_GRAPH,
    "trolleybus": GraphTypes.TROLLEY_GRAPH,
    "minibus": GraphTypes.MINIBUS_GRAPH,
}

app = FastAPI(
    title="Graph Analysis API",
    description="API для загрузки, анализа и визуализации графов маршрутов. "
                "Поддерживает гостевой вход, вход по email-коду, загрузку наборов данных, "
                "кластеризацию и вычисление метрик (PageRank, Betweenness).",
    version="1.0.0",
)

# CORS — оставляем только origin и credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
)

app.include_router(api_router, prefix="/v1")


# --- восстановление active_datasets при старте ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from app.models.graph_types import GraphTypes
from app.api.v1.router import api_router
from app.core.storage import active_datasets
from app.core.context.analysis_context import AnalysisContext
from app.core.context.metric_calculation_context import MetricCalculationContext
from app.database.postgres import postgres_manager

TRANSPORT_TO_GRAPH = {
    "bus": GraphTypes.BUS_GRAPH,
    "tram": GraphTypes.TRAM_GRAPH,
    "trolleybus": GraphTypes.TROLLEY_GRAPH,
    "minibus": GraphTypes.MINIBUS_GRAPH,
}

app = FastAPI(
    title="Graph Analysis API",
    description="API для загрузки, анализа и визуализации графов маршрутов. "
                "Поддерживает гостевой вход, вход по email-коду, загрузку наборов данных, "
                "кластеризацию и вычисление метрик (PageRank, Betweenness).",
    version="1.0.0",
)

# CORS — оставляем только origin и credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
)

app.include_router(api_router, prefix="/v1")


# --- восстановление active_datasets при старте ---
@app.on_event("startup")
async def restore_active_datasets():
    await postgres_manager.init()

    async for db in postgres_manager.get_db():
        try:
            rows = await db.fetch("SELECT * FROM datasets")
            for row in rows:
                analysis_context = AnalysisContext(
                    city_name=row["city"],
                    graph_name=row["id"],
                    graph_type=TRANSPORT_TO_GRAPH[row["transport_type"]],
                    metric_calculation_context=MetricCalculationContext(),
                    need_create_graph=False
                )
                active_datasets[row["id"]] = {
                    "name": row["name"],
                    "city_name": row["city"],
                    "transport_type": row["transport_type"],
                    "analysis_context": analysis_context,
                    "user_id": row["user_id"],
                    "guest_token": None,
                }
        finally:
            break  # закрываем генератор после первого соединения

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
