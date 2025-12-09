from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.v1.router import api_router
from app.api.v1.endpoints.postgres import init_db, close_db
import asyncio
from datetime import datetime, timezone, timedelta
from app.api.v1.endpoints.storage import active_datasets
from app.database.neo4j_connection import Neo4jConnection

async def cleanup_old_datasets():
    while True:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=1)
        to_delete = []

        # Собираем ID для удаления
        for ds_id, ds in list(active_datasets.items()):
            if ds["created_at"] < cutoff:
                to_delete.append(ds_id)

        # Удаляем по одному
        for ds_id in to_delete:
            try:
                ds = active_datasets[ds_id]
                ctx = ds["analysis_context"]
                db_params = ctx.db_graph_parameters

                # Удаляем из Neo4j
                conn = Neo4jConnection()
                try:
                    conn.run(f"CALL gds.graph.drop('{db_params.graph_name}', false)")
                except:
                    pass
                try:
                    conn.run(f"MATCH ()-[r:{db_params.main_rels_name}]->() DELETE r")
                    conn.run(f"MATCH (n:{db_params.main_node_name}) DELETE n")
                except:
                    pass
                conn.close()

                # Удаляем из in-memory
                del active_datasets[ds_id]
                print(f"Cleaned up expired dataset: {ds_id}")

            except Exception as e:
                print(f"Error cleaning dataset {ds_id}: {e}")

        await asyncio.sleep(300)  # проверяем каждые 5 минут

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Запускаем фоновую задачу
    cleanup_task = asyncio.create_task(cleanup_old_datasets())
    try:
        yield
    finally:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        await close_db()

app = FastAPI(
    title="Graph Analysis API",
    description="API для загрузки, анализа и визуализации графов маршрутов. "
                "Поддерживает гостевой вход, вход по email-коду, загрузку наборов данных, "
                "кластеризацию и вычисление метрик (PageRank, Betweenness).",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
