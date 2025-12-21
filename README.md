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
- `tests/` — модульные (unit) тесты для backend (pytest).

Стек используемых технологий
---
- Backend: Python 3.12, FastAPI + uvicorn, neo4j Python driver.
- Визуализация и frontend: React, TypeScript, Vite, Leaflet + Chart.js.
- База данных: Neo4j с Graph Data Science (GDS).
- Контейнеризация: Docker + Docker Compose.
- Тестирование: pytest (unit тесты).

Перед началом работы
---

Для запуска проекта потребуется командная строка, Git и Docker.

### 1. Открыть командную строку

**Windows:** PowerShell или «Командная строка»

**macOS / Linux:** Terminal

### 2. Установить Git (если не установлен)

Проверьте, установлен ли Git:

```bash
git --version
```

Если команды нет:

**Windows:**
скачайте и установите Git с официального сайта
https://git-scm.com/download/win

**macOS:**

```bash
brew install git
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install git
```

### 3. Клонировать репозиторий

```bash
git clone https://github.com/citec-spbu/Transport.git
cd Transport
```

### 4. Установить Docker и Docker Compose (если не установлены)

Проверьте установку:

```bash
docker --version
docker compose version
```

Если Docker отсутствует:

**Windows / macOS:**
установите Docker Desktop
https://www.docker.com/products/docker-desktop/

**Linux:**
https://docs.docker.com/engine/install/

После установки убедитесь, что Docker запущен.

Быстрый старт
---

### 5. Запуск проекта одной командой

В корневой папке проекта выполните:

```bash
docker compose up --build
```

### 6. Альтернативный запуск (локально без Docker)

**Backend:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8050
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### 7. Открыть приложение в браузере

После успешного запуска доступны:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8050
- **Neo4j Browser:** http://localhost:7474 (логин: `neo4j`, пароль: `hello123`)

Запуск тестов
---

Для проверки корректности backend'а используются модульные (unit) тесты на pytest.

**Запустить все тесты (локально):**

```bash
pip install -r requirements-test.txt
pytest
```

**Запустить тесты в Docker:**

```bash
docker compose -f docker-compose.yaml exec app pytest
```

**Запустить конкретный тестовый файл:**

```bash
pytest tests/test_analysis_context.py -v
```

Тесты находятся в директории `tests/` и охватывают:
- API эндпоинты (`test_*_endpoints.py`)
- Логику анализа (`test_analysis_*.py`)
- Работу с БД (`test_database_*.py`)
- Алгоритмы кластеризации и метрик (`test_metrics_*.py`, `test_community_detection.py`)

Переменные окружения
---

```bash
GRAPH_DATABASE_URL="neo4j://localhost:7687"
GRAPH_DATABASE_USER="neo4j"
GRAPH_DATABASE_PASSWORD="hello123"
```

API — основные эндпоинты
---
- `POST /v1/datasets` — создание/загрузка датасета (`{ "transport_type": "bus|tram|...", "city": "Город" }`). Возвращает `dataset_id`.
- `DELETE /v1/datasets/{dataset_id}` — удалить датасет и связанный граф.
- `POST /v1/analysis/cluster` — запустить кластеризацию (`{ "dataset_id": "...", "method": "leiden|louvain" }`).
- `POST /v1/analysis/metric` — рассчитать метрику (`{ "dataset_id": "...", "metric_type": "pagerank|betweenness" }`).

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
  -d '{"dataset_id":"<DATASET_ID>","metric_type":"pagerank"}' | jq
```


