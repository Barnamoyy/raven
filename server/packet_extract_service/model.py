import uuid 
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.sql import func
from database import Base 

class Packet(Base):
    __tablename__ = "packet_metadata"
    
    id = Column(Integer, primary_key=True, default=lambda: str(uuid.uuid4()))
    pcapng_id = Column(String, ForeignKey("pcapng_storage.id"), nullable=False)  # Links to uploaded file
    packet_number = Column(Integer, nullable=False)
    timestamp = Column(String, nullable=False)
    protocol = Column(String, nullable=False)  # Protocol type (e.g., TCP, UDP)
    source_ip = Column(String, nullable=False)  # Source IP address
    destination_ip = Column(String, nullable=False)  # Destination IP address
    packet_size = Column(Integer, nullable=False)