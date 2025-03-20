import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from .database import Base  # ✅ Using relative import

class PcapngFile(Base):
    __tablename__ = "pcapng_storage"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    total_packets = Column(Integer, default=0)
    processed = Column(Boolean, default=False)
