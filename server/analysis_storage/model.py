from sqlalchemy import Column, Integer, Float, JSON, ForeignKey, String
import uuid 
from database import Base 



class AnalysisResultsDB(Base):
    __tablename__ = "analysis_results"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    pcapng_id = Column(String, ForeignKey("pcapng_storage.id"), nullable=False)  # Links to uploaded file
 # Linking to PCAPNG file
    average_latency = Column(Float, nullable=True)
    pattern_analysis = Column(JSON, nullable=True)
    mqtt_analysis = Column(JSON, nullable=True)
    congestion_analysis = Column(JSON, nullable=True)
    tcp_window_analysis = Column(JSON, nullable=True)
    delay_analysis = Column(JSON, nullable=True)

