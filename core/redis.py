from redis import asyncio as aioredis
from fastapi import Depends
from typing import Annotated, AsyncGenerator

redis_pool = aioredis.ConnectionPool.from_url('redis://redis-db:6379', decode_responses=True)
client = aioredis.Redis(connection_pool=redis_pool)


async def get_client(cls):
    yield client


RedisDep = Annotated[aioredis.Redis, Depends(get_client)]
