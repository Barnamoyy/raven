from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PcapngFileCreate(BaseModel):
    user_id: str
    filename: str

class PcapngFileResponse(BaseModel):
    id: str
    user_id: str
    filename: str
    upload_timestamp: datetime

    class Config:
        from_attributes = True
