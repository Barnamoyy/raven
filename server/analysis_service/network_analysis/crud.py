from pathlib import Path
from ..pattern_anomalies.crud import detect_mqtt_patterns_anomalies
from ..pattern_detection.crud import advanced_pattern_detection
from scapy.all import PacketList


def analyze_network_congestion(file_path: Path,packets:PacketList):
    """Analyzes network congestion, jitter, and inefficient packet aggregation."""
    
    # Get base statistics from existing functions
    base_stats = advanced_pattern_detection(file_path,packets)
    mqtt_analysis = detect_mqtt_patterns_anomalies(file_path,packets)
    
    # Extract congestion-specific metrics
    congestion_metrics = {
        "retransmission_rate": mqtt_analysis["summary"]["retransmission_count"] / base_stats["statistics"]["packet_count"] 
            if base_stats["statistics"]["packet_count"] > 0 else 0,
        "jitter_ms": base_stats["statistics"]["jitter"] * 1000,  # Convert to milliseconds
        "jitter_spikes": len(mqtt_analysis["anomalies"]["jitter_spikes"]),
        "packet_aggregation_inefficiency": len(mqtt_analysis["delay_categories"]["bundling_delays"]),
        "congestion_events": len(mqtt_analysis["patterns"]["congestion_events"]),
    }
    
    # Calculate congestion score (0-100 scale)
    # This is a simplified example - you could weight these factors differently
    congestion_score = min(100, (
        (congestion_metrics["retransmission_rate"] * 50) +
        (min(1, congestion_metrics["jitter_ms"] / 100) * 25) +
        (min(1, congestion_metrics["jitter_spikes"] / 10) * 15) +
        (min(1, congestion_metrics["packet_aggregation_inefficiency"] / 20) * 10)
    ))
    
    # Classify congestion level
    congestion_level = "Low"
    if congestion_score > 30: congestion_level = "Moderate"
    if congestion_score > 60: congestion_level = "High"
    if congestion_score > 80: congestion_level = "Severe"
    
    return {
        "congestion_metrics": congestion_metrics,
        "congestion_score": congestion_score,
        "congestion_level": congestion_level,
        "detailed_metrics": {
            "jitter_analysis": {
                "mean_jitter_ms": base_stats["statistics"]["jitter"] * 1000,
                "jitter_spikes": mqtt_analysis["anomalies"]["jitter_spikes"]
            },
            "packet_aggregation_analysis": {
                "bundling_events": mqtt_analysis["delay_categories"]["bundling_delays"],
                "avg_bundling_delay_ms": mqtt_analysis["summary"]["avg_bundling_delay"] * 1000 if "avg_bundling_delay" in mqtt_analysis["summary"] else 0
            },
            "tcp_analysis": {
                "retransmissions": mqtt_analysis["delay_categories"]["retransmissions"],
                "protocol_distribution": base_stats["protocol_distribution"]
            }
        }
    }