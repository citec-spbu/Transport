# Transit Analysis — анализ городских транспортных сетей

Краткое описание
---
Этот проект собирает и анализирует данные городских транспортных сетей (остановки и маршруты), сохраняет графы в Neo4j
и выполняет алгоритмы Graph Data Science (GDS) — кластеризацию (Leiden/Louvain) и метрики центральности
(PageRank, Betweenness). Результаты доступны через HTTP API (FastAPI) и используются для визуализации.

Основные возможности
---
- Создание графа остановок общественного транспорта из парсера (kudikina.ru)
- Кластеризация узлов (Leiden / Louvain) через GDS
- Вычисление метрик центральности (pagerank, betweenness) через GDS
- API для загрузки датасетов и запуска анализа

Требования
---
- Docker и Docker Compose
- Neo4j с плагином Graph Data Science (GDS) — в docker-compose настроено требование `NEO4J_PLUGINS=["graph-data-science"]` и согласие лицензии
- Python зависимости указаны в `requirements.txt` (установлены в контейнере)

Запуск (Docker)
---
1. Собрать и запустить сервисы:

```bash
docker compose up --build
```

2. Приложение доступно по адресу: `http://localhost:8050`
3. Neo4j Bolt доступен на `neo4j://localhost:7687` (логин/пароль — из `docker-compose.yaml`)

Переменные окружения
---
- `GRAPH_DATABASE_URL` — URL Neo4j (`neo4j://neo4j:7687` в compose)
- `GRAPH_DATABASE_USER` — имя пользователя (например, `neo4j`)
- `GRAPH_DATABASE_PASSWORD` — пароль

API — основные эндпоинты
---
- `POST /v1/datasets` — загрузка/создание датасета (тело: `{ "transport_type": "bus|tram|trolleybus|minibus", "city": "Город" }`). Возвращает `dataset_id`.
- `DELETE /v1/datasets/{dataset_id}` — удалить датасет (включая очистку графа в Neo4j).
- `POST /v1/analysis/cluster` — запустить кластеризацию. Тело: `{ "dataset_id": "...", "method": "leiden|louvain" }`.
- `POST /v1/analysis/metric` — рассчитать метрики. Тело: `{ "dataset_id": "...", "metric": "pagerank|betweenness" }`.
- `POST /v1/auth/*` — эндпоинты аутентификации (если используются).

Примеры запросов (curl)
---
Создать датасет (использует кеш, если данные уже скачаны):

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