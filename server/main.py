from fastapi import FastAPI
from routes import router as main_router
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
import database
from storage_service import model
from routes import router as storage_router
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ✅ Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # ✅ Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # ✅ Allow all headers
)

# Redis Connection
REDIS_URL = "redis://localhost:6379"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Initialize the database
model.Base.metadata.create_all(bind=database.engine)

# Include all routes
app.include_router(storage_router)


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Backend!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
