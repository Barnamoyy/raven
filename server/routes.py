# dependencies 
from fastapi import APIRouter, Depends, UploadFile, File,HTTPException
from sqlalchemy.orm import Session
from scapy.all import rdpcap
import shutil
from pathlib import Path
from database import get_db
from storage_service import crud, schema



# importing analysis functions 
from analysis_service.tcp_analysis.crud import analyze_tcp_window_size
from analysis_service.network_analysis.crud import analyze_network_congestion
from analysis_service.pattern_detection.crud import advanced_pattern_detection
from analysis_service.pattern_anomalies.crud import detect_mqtt_patterns_anomalies
from latency_analysis_service.crud import calculate_average_latency
from packet_extract_service.crud import extract_and_store_packets, parallel_extract_and_store
import numpy as np
from sklearn.cluster import KMeans  # ✅ Correct
from fastapi import BackgroundTasks




router = APIRouter(prefix="/storage", tags=["Storage"])

UPLOAD_DIR = Path("uploaded_pcapng_files")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload/")
async def upload_pcapng(file: UploadFile = File(...), db: Session = Depends(get_db),background_tasks: BackgroundTasks = BackgroundTasks()):
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    file_data = schema.PcapngFileCreate(filename=file.filename)
    stored_file = crud.create_pcapng_file(db, file_data)
    
    packets = rdpcap(str(file_path)) # Run scapy to extract packets
    
    
    try:
        avg_latency = calculate_average_latency(file_path,packets)    
        print(f"Average latency: {avg_latency}")    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        # Extract and store packets
      background_tasks.add_task(parallel_extract_and_store, file_path, stored_file["id"], db, 3000, 8)


      print(f"Packets extracted and stored for {file.filename}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        pattern_analysis = advanced_pattern_detection(file_path,packets)
        print("Pattern analysis completed")        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))   
    
    try:
        mqtt_analysis = detect_mqtt_patterns_anomalies(file_path,packets)
        print("MQTT analysis completed")        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    try:
        congestion_analysis = analyze_network_congestion(file_path,packets)
        print(f"Network congestion level: {congestion_analysis['congestion_level']}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    try:
        tcp_window_analysis = analyze_tcp_window_size(file_path,packets)
        print(f"Zero window events: {tcp_window_analysis['congestion_indicators']['zero_window_count']}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Combine all analyses into a comprehensive result
    analysis_results = {
        "average_latency": avg_latency,
        "pattern_analysis": pattern_analysis,
        "mqtt_analysis": mqtt_analysis,
        "congestion_analysis": congestion_analysis,
        "tcp_window_analysis": tcp_window_analysis
    }
    
    return analysis_results

@router.get("/", response_model=list[schema.PcapngFileResponse])
async def list_pcapng_files(db: Session = Depends(get_db)):
    return crud.get_pcapng_files(db)




    



