from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os

router = APIRouter()

# Directory to store uploaded files
UPLOAD_DIR = "uploaded_pcaps"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload/")
async def upload_pcap(file: UploadFile = File(...)):
    """Upload a .pcapng file and store it."""
    
    if not file.filename.endswith(".pcapng"):
        raise HTTPException(status_code=400, detail="Only .pcapng files are allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"filename": file.filename, "message": "File uploaded successfully", "path": file_path}
