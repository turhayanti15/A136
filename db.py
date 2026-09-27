import asyncpg
import os
import re
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
USERNAMES_TABLE = os.getenv("POSTGRES_TABLE_USERNAMES", "usernames")
CHANNELS_TABLE = os.getenv("POSTGRES_TABLE_CHANNELS", "channels")


def _validate_table_name(name: str) -> str:
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        raise ValueError(f"Invalid table name: {name}")
    return name

USERNAMES_TABLE = _validate_table_name(USERNAMES_TABLE)
CHANNELS_TABLE = _validate_table_name(CHANNELS_TABLE)

async def get_pool():
    return await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

async def get_usernames(pool):
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"SELECT username FROM {USERNAMES_TABLE} LIMIT 50")
        return [row['username'] for row in rows]

async def add_username(pool, username):
    async with pool.acquire() as conn:
        await conn.execute(
            f"INSERT INTO {USERNAMES_TABLE} (username) VALUES ($1) ON CONFLICT DO NOTHING",
            username,
        )

async def delete_username(pool, username):
    async with pool.acquire() as conn:
        await conn.execute(
            f"DELETE FROM {USERNAMES_TABLE} WHERE username = $1",
            username,
        )

async def add_channel(pool, channel_id):
    async with pool.acquire() as conn:
        await conn.execute(
            f"INSERT INTO {CHANNELS_TABLE} (channel_id) VALUES ($1) ON CONFLICT DO NOTHING",
            channel_id,
        )

async def delete_channel(pool, channel_id):
    async with pool.acquire() as conn:
        await conn.execute(
            f"DELETE FROM {CHANNELS_TABLE} WHERE channel_id = $1",
            channel_id,
        )

async def get_channels(pool):
    async with pool.acquire() as conn:
        rows = await conn.fetch(f"SELECT channel_id FROM {CHANNELS_TABLE}")
        return [row['channel_id'] for row in rows]