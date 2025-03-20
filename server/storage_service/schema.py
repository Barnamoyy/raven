from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PcapngFileCreate(BaseModel):
    filename: str
    total_packets: Optional[int] = None

class PcapngFileResponse(BaseModel):
    id: str
    filename: str
    upload_timestamp: datetime
    total_packets: Optional[int]
    processed: bool

    class Config:
        from_attributes = True
