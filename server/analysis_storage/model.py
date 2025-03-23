from sqlalchemy import Column, Integer, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class AnalysisResultsDB(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    pcapng_id = Column(
        Integer, ForeignKey("pcapng_files.id"), nullable=False
    )  # Linking to PCAPNG file
    average_latency = Column(Float, nullable=True)
    pattern_analysis = Column(JSON, nullable=True)
    mqtt_analysis = Column(JSON, nullable=True)
    congestion_analysis = Column(JSON, nullable=True)
    tcp_window_analysis = Column(JSON, nullable=True)
    delay_analysis = Column(JSON, nullable=True)

    # Relationship (Assuming a PCAPNGFile model exists)
    pcapng_file = relationship("PCAPNGFile", back_populates="analysis_results")
