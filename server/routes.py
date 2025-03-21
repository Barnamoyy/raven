from fastapi import APIRouter, Depends, UploadFile, File,HTTPException
from sqlalchemy.orm import Session
from pcapkit import extract
# from pcapkit.foundation.engines.scapy import ScapySniffer
from scapy.all import rdpcap
import shutil
from pathlib import Path
from database import get_db
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
    
    try:
        avg_latency = calculate_average_latency(file_path)    
        print(avg_latency)    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    

    
    return stored_file

@router.get("/", response_model=list[schema.PcapngFileResponse])
async def list_pcapng_files(db: Session = Depends(get_db)):
    return crud.get_pcapng_files(db)


def calculate_average_latency(file_path: Path) -> float:
    """Extracts packets from a PCAPNG file and calculates average latency."""
      # Extract file without saving output
    
    # Extract timestamps from packets
    timestamps = []
    
    packets = rdpcap(str(file_path))  # Run scapy to extract packets

    timestamps = [pkt.time for pkt in packets if hasattr(pkt, 'time')]

    if len(timestamps) < 2:
        raise ValueError("Not enough packets to calculate latency.")
    
    # Compute latency between consecutive packets
    latency_values = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    
    return sum(latency_values) / len(latency_values)  # Average latency