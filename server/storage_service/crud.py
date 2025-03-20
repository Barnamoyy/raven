from sqlalchemy.orm import Session
from . import model, schema
from datetime import datetime

def create_pcapng_file(db: Session, file_data: schema.PcapngFileCreate):
    new_file = model.PcapngFile(
        filename=file_data.filename,
        total_packets=file_data.total_packets,
        upload_timestamp=datetime.utcnow()
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)
    
    return {
        "id": str(new_file.id),  # ✅ Convert UUID to string
        "filename": new_file.filename,
        "upload_timestamp": new_file.upload_timestamp,
        "total_packets": new_file.total_packets,
        "processed": new_file.processed,
    }

def get_pcapng_files(db: Session):
    return db.query(model.PcapngFile).all()
