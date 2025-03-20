from sqlalchemy import Column, Integer, String, Float
from storage_service.database import Base

class Latency_analysis(Base):
    __tablename__ = "latency_analysis"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, unique=True)
    average_latency = Column(Float, nullable=False)
