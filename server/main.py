from fastapi import FastAPI
from routes import router as main_router
import redis.asyncio as redis
import os

app = FastAPI()

# Redis Connection
REDIS_URL = "redis://localhost:6379"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Include all routes
app.include_router(main_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
