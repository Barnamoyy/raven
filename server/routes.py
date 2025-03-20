from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
import shutil
from pathlib import Path
from storage_service.database import get_db
from storage_service import crud, schema

router = APIRouter(prefix="/storage", tags=["Storage"])

UPLOAD_DIR = Path("uploaded_pcapng_files")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload/", response_model=schema.PcapngFileResponse)
async def upload_pcapng(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_data = schema.PcapngFileCreate(filename=file.filename)
    stored_file = crud.create_pcapng_file(db, file_data)
    
    return stored_file

@router.get("/", response_model=list[schema.PcapngFileResponse])
async def list_pcapng_files(db: Session = Depends(get_db)):
    return crud.get_pcapng_files(db)
