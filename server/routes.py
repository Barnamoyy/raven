from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    HTTPException,
    BackgroundTasks,
    Form,
)
from sqlalchemy.orm import Session
from scapy.all import rdpcap
import shutil
from pathlib import Path
from database import get_db
from analysis_service.delay_categorization.crud import analyze_packet_delays
from storage_service import crud, schema
from scapy.all import PcapReader
from analysis_service.tcp_analysis.analysis import analyze_tcp_window_size
from analysis_service.network_analysis.crud import analyze_network_congestion
from analysis_service.pattern_detection.crud import advanced_pattern_detection
from analysis_service.pattern_anomalies.crud import detect_network_patterns_anomalies
from latency_analysis_service.crud import calculate_average_latency
from packet_extract_service.crud import extract_and_store_packets_optimized
from analysis_storage.schema import AnalysisResults
from analysis_storage.crud import create_analysis_result, get_analysis_by_pcapng
from storage_service.crud import get_latest_pcapng_files
import time

router = APIRouter(prefix="/storage", tags=["Storage"])

UPLOAD_DIR = Path("uploaded_pcapng_files")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload/")
async def upload_pcapng(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Uploads a PCAPNG file, extracts packets, runs analysis, and stores results."""
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Store file metadata in DB
    file_data = schema.PcapngFileCreate(user_id=user_id, filename=file.filename)
    stored_file = crud.create_pcapng_file(db, file_data)

    try:
        packets = rdpcap(str(file_path))  # Extract packets using Scapy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PCAPNG file: {e}")

    # Run analysis functions
    try:
        start = time.time()
        avg_latency = calculate_average_latency(file_path, packets)
        end = time.time()
        print("latency")
        print(end - start)
        start = time.time()
        pattern_analysis = advanced_pattern_detection(file_path, packets)
        end = time.time()
        print("pattern_analysis")
        print(end - start)
        start = time.time()
        mqtt_analysis = detect_network_patterns_anomalies(file_path, packets)
        end = time.time()
        print("mqtt")
        print(end - start)
        start = time.time()
        congestion_analysis = analyze_network_congestion(file_path, packets)
        end = time.time()
        print("conjestion")
        print(end - start)
        start = time.time()
        tcp_window_analysis = analyze_tcp_window_size(file_path, packets)
        end = time.time()
        print("tcp")
        print(end - start)
        start = time.time()
        delay_categorization = analyze_packet_delays(file_path, packets)
        end = time.time()
        print("delay_categorization")
        print(end - start)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Store analysis results in DB
    analysis_results = AnalysisResults(
        pcapng_id=stored_file["id"],
        average_latency=avg_latency,
        pattern_analysis=pattern_analysis,
        mqtt_analysis=mqtt_analysis,
        congestion_analysis=congestion_analysis,
        tcp_window_analysis=tcp_window_analysis,
        delay_analysis=delay_categorization,
    )

    background_tasks.add_task(create_analysis_result, db, analysis_results)

    # Background Task: Store extracted packets in DB
    background_tasks.add_task(
        extract_and_store_packets_optimized,
        file_path,
        stored_file["id"],
        db,
        3000,
    )

    return {
        "message": "PCAPNG file uploaded successfully",
        "pcapng_id": stored_file["id"],
        "analysis_results": {
            "avg_latency": avg_latency,
            "pattern_analysis": pattern_analysis,
            "mqtt_analysis": mqtt_analysis,
            "congestion_analysis": congestion_analysis,
            "tcp_window_analysis": tcp_window_analysis,
            "delay_categorization": delay_categorization,
        },
    }


@router.get("/analysis/{pcapng_id}")
def get_analysis_results(pcapng_id: str, db: Session = Depends(get_db)):
    """Fetches analysis results for a specific PCAPNG file."""
    results = get_analysis_by_pcapng(db, pcapng_id)
    if not results:
        raise HTTPException(status_code=404, detail="No analysis results found.")
    return results


@router.get("/", response_model=list[schema.PcapngFileResponse])
async def list_pcapng_files(db: Session = Depends(get_db)):
    """Lists all uploaded PCAPNG files."""
    return crud.get_pcapng_files(db)


@router.get("/latest/{user_id}")
def get_latest_pcapng(user_id: str, db: Session = Depends(get_db)):
    """Fetches the latest uploaded PCAPNG file for a specific user."""
    return get_latest_pcapng_files(user_id, db)
