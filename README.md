# Transit Analysis — веб‑приложение для анализа городских транспортных сетей

Краткое описание
---
Веб‑приложение, состоящее из backend (HTTP API на FastAPI) и frontend (веб‑интерфейс на React/Vite) частей. Оно собирает и анализирует данные городских транспортных сетей, сохраняет графы в Neo4j и выполняет алгоритмы Graph Data Science (GDS) — кластеризацию (Leiden/Louvain)
и вычисление метрик центральности (PageRank, Betweenness). Результаты доступны через API и визуализируются в клиенте.

Содержимое репозитория — основные директории
---
- `app/` — серверная часть с FastAPI + uvicorn (эндпоинты в `app/api`, логика в `app/core`, доступ к БД в `app/database`).
- `cache/` — кешированные JSON файлы с маршрутами по городам.
- `frontend/` — клиентская часть на React + TypeScript (Vite).

Стек используемых технологий
---
- Backend: Python 3.12, FastAPI + uvicorn, neo4j Python driver.
- Визуализация и frontend: React, TypeScript, Vite, Leaflet + Chart.js.
- База данных: Neo4j с Graph Data Science (GDS).
- Контейнеризация: Docker + Docker Compose.

Быстрый старт
---
1) Запуск через Docker Compose (рекомендуется):

```bash
docker compose up --build
```

2) Локальный запуск (без Docker)

Backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8050
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Доступ по умолчанию
---
- Backend API: `http://localhost:8050`
- Neo4j Browser: `http://localhost:7474` (логин: `neo4j`, пароль: `hello123`)
- Frontend: `http://localhost:3000`

Переменные окружения
---

```bash
GRAPH_DATABASE_URL="neo4j://localhost:7687"
GRAPH_DATABASE_USER="neo4j"
GRAPH_DATABASE_PASSWORD="secret"
```

API — основные эндпоинты
---
- `POST /v1/datasets` — создание/загрузка датасета (`{ "transport_type": "bus|tram|...", "city": "Город" }`). Возвращает `dataset_id`.
- `DELETE /v1/datasets/{dataset_id}` — удалить датасет и связанный граф.
- `POST /v1/analysis/cluster` — запустить кластеризацию (`{ "dataset_id": "...", "method": "leiden|louvain" }`).
- `POST /v1/analysis/metric` — рассчитать метрику (`{ "dataset_id": "...", "metric": "pagerank|betweenness" }`).

Примеры использования (curl)
---

Создать датасет (используется кеш, если данные уже скачаны):

```bash
curl -s -X POST "http://127.0.0.1:8050/v1/datasets" \
  -H "Content-Type: application/json" \
  -d '{"transport_type":"bus","city":"Бирск"}' | jq
```

Запустить кластеризацию (Leiden):

```bash
curl -s -X POST "http://127.0.0.1:8050/v1/analysis/cluster" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"<DATASET_ID>","method":"leiden"}' | jq
```

Запустить вычисление PageRank:

```bash
curl -s -X POST "http://127.0.0.1:8050/v1/analysis/metric" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"<DATASET_ID>","metric":"pagerank"}' | jq
```