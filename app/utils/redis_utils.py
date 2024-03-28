import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL")

async def fetch_cache(key):
    async with redis.from_url(REDIS_URL) as r:
        return await r.get(key)

async def set_cache(key, value, ttl=3600):
    async with redis.from_url(REDIS_URL) as r:
        return await r.setex(key, ttl, value)
