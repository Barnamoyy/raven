from sqlalchemy.orm import Session
from crud import AnalysisResultsDB
from crud import AnalysisResults


def create_analysis_result(db: Session, analysis_data: AnalysisResults):
    db_analysis = AnalysisResultsDB(
        pcapng_id=analysis_data.pcapng_id,  # Link to specific PCAPNG file
        average_latency=analysis_data.average_latency,
        pattern_analysis=analysis_data.pattern_analysis,
        mqtt_analysis=analysis_data.mqtt_analysis,
        congestion_analysis=analysis_data.congestion_analysis,
        tcp_window_analysis=analysis_data.tcp_window_analysis,
        delay_analysis=analysis_data.delay_analysis,
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_analysis_results(db: Session, result_id: int):
    return db.query(AnalysisResultsDB).filter(AnalysisResultsDB.id == result_id).first()


def get_analysis_by_pcapng(db: Session, pcapng_id: int):
    return (
        db.query(AnalysisResultsDB)
        .filter(AnalysisResultsDB.pcapng_id == pcapng_id)
        .all()
    )
