from fastapi import FastAPI
from routes import router as main_router

app = FastAPI()

# Include all routes
app.include_router(main_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
