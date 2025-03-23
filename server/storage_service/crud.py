from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import model, schema
from datetime import datetime
from .model import PcapngFile
from analysis_storage.model import AnalysisResultsDB

def create_pcapng_file(db: Session, file_data: schema.PcapngFileCreate):
    new_file = model.PcapngFile(
        filename=file_data.filename,
        upload_timestamp=datetime.utcnow(),
        user_id=file_data.user_id,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    
    return {
        "id": str(new_file.id),  # ✅ Convert UUID to string
        "user_id": new_file.user_id,
        "filename": new_file.filename,
        "upload_timestamp": new_file.upload_timestamp, 
    }

def get_pcapng_files(db: Session):
    return db.query(PcapngFile).all()

def get_latest_pcapng_files(user_id: str, db: Session): 
    latest_pcapng = (
        db.query(PcapngFile)
        .filter(PcapngFile.user_id == user_id)
        .order_by(PcapngFile.upload_timestamp.desc())
        .first()
    )

    if not latest_pcapng:
        raise HTTPException(status_code=404, detail="No PCAPNG files found for this user.")

    latest_analysis = db.query(AnalysisResultsDB).filter(AnalysisResultsDB.pcapng_id == latest_pcapng.id).first()
    if not latest_analysis:
        raise HTTPException(status_code=404, detail="No analysis results found for this PCAPNG file.")
    return latest_analysis