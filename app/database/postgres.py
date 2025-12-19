# app/database/postgres.py
import os
import asyncpg
import asyncio
from typing import Optional, AsyncGenerator

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/appdb")


class PostgresManager:
    def __init__(self, database_url: str = DATABASE_URL):
        self.database_url = database_url
        self._pool: Optional[asyncpg.pool.Pool] = None

    async def init(self, retries: int = 5):
        """Инициализация пула и создание таблиц при старте приложения"""
        while retries > 0:
            try:
                self._pool = await asyncpg.create_pool(self.database_url)
                print("Успешно подключились к PostgreSQL")
                await self._create_tables()
                return
            except Exception as e:
                retries -= 1
                if retries == 0:
                    raise Exception(f"Не удалось подключиться к PostgreSQL: {e}") from e
                print(f"Ошибка подключения к PostgreSQL. Осталось попыток: {retries}. Ошибка: {e}")
                await asyncio.sleep(2)

    async def _create_tables(self):
        async with self._pool.acquire() as conn:
            # UUID generator
            await conn.execute("""
                CREATE EXTENSION IF NOT EXISTS pgcrypto;
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email TEXT UNIQUE NOT NULL,
                    verified BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    city TEXT NOT NULL,
                    transport_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS verification_codes (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email TEXT UNIQUE NOT NULL,
                    code TEXT NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    token TEXT UNIQUE NOT NULL,
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    expires_at TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)


    async def get_connection(self) -> asyncpg.Connection:
        """Получение соединения из пула (для Depends)"""
        if self._pool is None:
            await self.init()
        return await self._pool.acquire()

    async def release_connection(self, conn: asyncpg.Connection):
        """Возврат соединения в пул"""
        if self._pool:
            await self._pool.release(conn)

    async def close(self):
        """Закрытие пула соединений"""
        if self._pool:
            await self._pool.close()
            self._pool = None

    async def get_db(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """Контекст для Depends"""
        conn = await self.get_connection()
        try:
            yield conn
        finally:
            await self.release_connection(conn)


# Создаём глобальный менеджер для использования в эндпоинтах
postgres_manager = PostgresManager()