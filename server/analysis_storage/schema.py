from pydantic import BaseModel
from typing import Dict, Any


class AnalysisResults(BaseModel):
    pcapng_id: str  # Foreign Key linking to the pcapng file
    average_latency: float
    pattern_analysis: Dict[str, Any]
    mqtt_analysis: Dict[str, Any]
    congestion_analysis: Dict[str, Any]
    tcp_window_analysis: Dict[str, Any]
    delay_analysis: Dict[str, Any]

    class Config:
        from_attributes = True # Enable ORM compatibility
