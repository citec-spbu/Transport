from fastapi import FastAPI
from app.api.v1.router import api_router

app = FastAPI(
    title="Graph Analysis API",
    description="API для загрузки, анализа и визуализации графов маршрутов. "
                "Поддерживает гостевой вход, вход по email-коду, загрузку наборов данных, "
                "кластеризацию и вычисление метрик (PageRank, Betweenness).",
    version="1.0.0"
)

app.include_router(api_router, prefix="/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
