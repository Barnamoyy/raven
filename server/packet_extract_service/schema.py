from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class PacketBase(BaseModel):
    pcapng_id: UUID
    packet_number: int
    timestamp: datetime
    protocol: str
    source_ip: str
    destination_ip: str
    packet_size: int

class PacketCreate(PacketBase):
    pass

class PacketResponse(PacketBase):
    id: str
    class Config:
        from_attributes = True
