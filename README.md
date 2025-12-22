# Transit Analysis — веб‑приложение для анализа городских транспортных сетей

Краткое описание
---
Веб‑приложение, состоящее из backend (HTTP API на FastAPI) и frontend (веб‑интерфейс на React/Vite) частей. Оно собирает и анализирует данные городских транспортных сетей, сохраняет графы в Neo4j и выполняет алгоритмы Graph Data Science (GDS) — кластеризацию (Leiden/Louvain)
и вычисление метрик центральности (PageRank, Betweenness). Результаты доступны через API и визуализируются в клиенте. Приложение поддерживает **двухуровневую авторизацию** (гость, зарегистрированный пользователь) и может работать как по HTTP, так и по **защищённому HTTPS протоколу**.

**Быстрые ссылки:**
- 🚀 [Быстрый старт](#быстрый-старт)
- 🔐 [Авторизация](#система-авторизации)
- 🔒 [HTTPS](#https-и-сертификаты)
- 📚 [API](#api--основные-эндпоинты)

Содержимое репозитория — основные директории
---
- `app/` — серверная часть с FastAPI + uvicorn (эндпоинты в `app/api`, логика в `app/core`, доступ к БД в `app/database`). Содержит логику авторизации и управления токенами.
- `cache/` — кешированные JSON файлы с маршрутами по городам.
- `frontend/` — клиентская часть на React + TypeScript (Vite). Работает как с HTTP, так и с HTTPS.
- `tests/` — модульные (unit) тесты для backend (pytest).
- `certs/` — директория для хранения SSL/TLS сертификатов (если используется HTTPS).

Стек используемых технологий
---
- Backend: Python 3.12, FastAPI + uvicorn, neo4j Python driver.
- Авторизация: Email-код верификация, SMTP (отправка кодов верификации).
- Визуализация и frontend: React, TypeScript, Vite, Leaflet + Chart.js.
- База данных: Neo4j с Graph Data Science (GDS), PostgreSQL для хранения пользователей и токенов.
- Безопасность: SSL/TLS сертификаты для HTTPS, токены с истечением срока действия.
- Контейнеризация: Docker + Docker Compose.
- Тестирование: pytest (unit тесты).

Система авторизации
---

Приложение использует **двухуровневую авторизацию** на основе токенов (PostgreSQL):

- **Гость** (`guest`) — вход без регистрации, токен на 1 день
- **Пользователь** (`user`) — вход через email-код, токен на 30 дней

**Как использовать:**

Запросить код:
```bash
curl -X POST "http://localhost:8050/v1/auth/request_code" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'
```

Подтвердить код и получить токен:
```bash
curl -X POST "http://localhost:8050/v1/auth/verify_code" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","code":"123456"}'
```

Использовать токен:
```bash
curl -X POST "http://localhost:8050/v1/datasets/" \
  -H "Authorization: <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"city":"Санкт-Петербург","transport_type":"bus"}'
```

HTTPS и сертификаты
---

**По умолчанию:** HTTP на `http://localhost:3000`

**Для HTTPS:**

1. **Генерируем самоподписанный сертификат:**

**Linux/macOS:**
```bash
openssl req -x509 -newkey rsa:4096 -keyout certs/localhost.key -out certs/localhost.crt -days 365 -nodes \
  -subj "/C=RU/ST=Saint Petersburg/L=Saint Petersburg/O=Transit Analysis/CN=localhost"
```

**Windows (PowerShell, требует установки OpenSSL):**

Сначала установите OpenSSL с сайта https://slproweb.com/products/Win32OpenSSL.html.

Затем сгенерируйте сертификат:
```powershell
openssl req -x509 -newkey rsa:4096 -keyout certs/localhost.key -out certs/localhost.crt -days 365 -nodes `
  -subj "/C=RU/ST=Saint Petersburg/L=Saint Petersburg/O=Transit Analysis/CN=localhost"
```

2. **Запускаем приложение:**
```bash
docker compose up --build
```
Frontend автоматически обнаружит сертификаты → `https://localhost:3000`

4. **В браузере:**
Если сертификат не добавлен в доверенные — нажмите "Продолжить" при предупреждении (это нормально для self-signed).

> **Важно:** Приватные ключи (`*.key`, `*.pem`) исключены из Git (см. `.gitignore`). Никогда не коммитьте их!


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

- **Frontend (HTTP, если нет сертификатов):** http://localhost:3000
- **Frontend (HTTPS, если добавлены сертификаты):** https://localhost:3000
- **Backend API (HTTP):** http://localhost:8050
- **Neo4j Browser:** http://localhost:7474 (логин: `neo4j`, пароль: `hello123`)

> **Примечание:** Если вы добавили сертификаты в папку `certs/`, фронтенд автоматически запустится на HTTPS. Браузер может показать предупреждение о безопасности для самоподписанных сертификатов — это нормально. Нажмите "Продолжить" или "Я понимаю риск".

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
- Контекст анализа и управление (`test_analysis_context.py`, `test_analysis_manager.py`, `test_analysis_preparer.py`)
- Обнаружение сообществ и кластеризация (`test_community_detection.py`, `test_metric_cluster_preparer.py`)
- Работу с БД (`test_database_*.py`, `test_neo4j_connection.py`)
- Вычисление метрик и запросы (`test_metrics_*.py`, `test_metrics_queries.py`)
- Парсинг данных (`test_parsers_unit.py`)

Переменные окружения
---

### Необходимые переменные для работы:

**Neo4j (граф-база):**
```bash
GRAPH_DATABASE_URL="neo4j://localhost:7687"
GRAPH_DATABASE_USER="neo4j"
GRAPH_DATABASE_PASSWORD="hello123"
```

**PostgreSQL (для авторизации):**
```bash
DATABASE_URL="postgresql://user:password@localhost:5432/appdb"
```

**Email (отправка кодов верификации):**
```bash
SMTP_HOST="smtp.yandex.ru"    
SMTP_PORT=587
SMTP_USER="your-email@yandex.ru"
SMTP_PASSWORD="your-app-password"   
SMTP_FROM="Transit Analysis <noreply@example.com>"
```

Все переменные уже настроены в `docker-compose.yaml` для локальной разработки.

API — основные эндпоинты
---

### Авторизация:
- `POST /v1/auth/request_code` — отправить код на email
- `POST /v1/auth/verify_code` — подтвердить код и получить токен
- `POST /v1/auth/guest` — получить гостевой токен

### Датасеты (требует токена в `Authorization`):
- `GET /v1/datasets/` — список датасетов
- `POST /v1/datasets/` — создать датасет (`{city, transport_type}`)
- `DELETE /v1/datasets/{id}` — удалить датасет

### Анализ:
- `POST /v1/analysis/cluster` — кластеризация (`{dataset_id, method: leiden|louvain}`)
- `POST /v1/analysis/metric` — метрика (`{dataset_id, metric_type: pagerank|betweenness}`)

Примеры использования (curl)
---

**Авторизация:**
```bash
# Запросить код
curl -X POST "http://localhost:8050/v1/auth/request_code" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# Подтвердить код
curl -X POST "http://localhost:8050/v1/auth/verify_code" \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","code":"123456"}' | jq .token

# Гостевой вход
curl -X POST "http://localhost:8050/v1/auth/guest" | jq .token
```

**Работа с данными (замените `<TOKEN>` на полученный токен):**
```bash
export TOKEN="<TOKEN>"

# Получить список датасетов
curl -X GET "http://localhost:8050/v1/datasets/" \
  -H "Authorization: $TOKEN" | jq

# Создать датасет
curl -X POST "http://localhost:8050/v1/datasets/" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"city":"Бирск","transport_type":"bus"}' | jq .dataset_id

# Удалить датасет
curl -X DELETE "http://localhost:8050/v1/datasets/<DATASET_ID>" \
  -H "Authorization: $TOKEN" | jq

# Кластеризация (Leiden)
curl -X POST "http://localhost:8050/v1/analysis/cluster" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"<ID>","method":"leiden"}' | jq

# PageRank метрика
curl -X POST "http://localhost:8050/v1/analysis/metric" \
  -H "Authorization: $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id":"<ID>","metric_type":"pagerank"}' | jq
```


