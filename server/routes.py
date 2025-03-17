from fastapi import APIRouter
from upload import router as upload_router

router = APIRouter()

# Register the upload route
router.include_router(upload_router, prefix="/files")
