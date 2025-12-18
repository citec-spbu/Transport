import os
import asyncpg
from contextlib import asynccontextmanager
import asyncio
import os
from typing import Optional

# Читаем URL из переменных окружения (поддерживается в Docker)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/appdb")

_pool = None


async def init_db():
    """Инициализация пула соединений и создание таблиц при старте приложения с повторными попытками подключения."""
    global _pool

    retries = 5
    while retries > 0:
        try:
            _pool = await asyncpg.create_pool(DATABASE_URL)
            print("Успешно подключились к PostgreSQL")

            # Создаём таблицы, если они ещё не существуют
            async with _pool.acquire() as conn:
                # Таблица пользователей
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        email TEXT PRIMARY KEY,
                        verified BOOLEAN NOT NULL DEFAULT FALSE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                # Таблица для датасетов
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS datasets (
                        id TEXT PRIMARY KEY,
                        email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
                        city TEXT NOT NULL,
                        transport_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                # Временные коды подтверждения
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS verification_codes (
                        email TEXT PRIMARY KEY,
                        code TEXT NOT NULL,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL
                    )
                """)

                # Токены аутентификации
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS tokens (
                        token TEXT PRIMARY KEY,
                        email TEXT REFERENCES users(email) ON DELETE CASCADE,
                        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)

                # Ensure email column in tokens allows NULL (for guest tokens)
                try:
                    await conn.execute("""
                        ALTER TABLE tokens ALTER COLUMN email DROP NOT NULL;
                    """)
                except Exception:
                    # If alter fails (e.g., column doesn't exist yet), ignore
                    pass

                # История аналитических запросов
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS analysis_requests (
                        id SERIAL PRIMARY KEY,
                        email TEXT NOT NULL REFERENCES users(email) ON DELETE CASCADE,
                        type TEXT NOT NULL CHECK (type IN ('cluster', 'metric', 'upload')),
                        dataset_id TEXT NOT NULL,
                        method TEXT,
                        metric TEXT,
                        transport_type TEXT,
                        city TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)

            print("Таблицы в PostgreSQL проверены/созданы")
            return

        except Exception as e:
            retries -= 1
            if retries == 0:
                print(f"Не удалось подключиться к PostgreSQL после нескольких попыток: {e}")
                raise Exception("Не удалось инициализировать подключение к базе данных") from e

            print(f"Ошибка подключения к PostgreSQL, осталось попыток: {retries}. Ошибка: {e}")
            await asyncio.sleep(2)  # Ждём 2 секунды перед повтором


async def close_db():
    """Закрытие пула соединений при завершении работы."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_db():
    """Контекстный менеджер для получения соединения из пула."""
    if _pool is None:
        await init_db()
    conn = await _pool.acquire()
    try:
        yield conn
    finally:
        await _pool.release(conn)