from pathlib import Path
from scapy.all import PacketList
import numpy as np


def advanced_pattern_detection(file_path: Path, packets: PacketList):
    """Performs advanced pattern detection on network traffic."""
    timestamps = [float(pkt.time) for pkt in packets if hasattr(pkt, "time")]

    if len(timestamps) < 10:  # Need more packets for meaningful analysis
        return {"error": "Insufficient packets for advanced analysis"}

    # Calculate inter-packet delays
    delays = np.diff(timestamps)

    # Basic statistics
    stats = {
        "mean_delay": float(np.mean(delays)),
        "median_delay": float(np.median(delays)),
        "std_delay": float(np.std(delays)),
        "min_delay": float(np.min(delays)),
        "max_delay": float(np.max(delays)),
        "jitter": float(np.std(delays)),
        "packet_count": len(timestamps),
    }

    # Detect periodic patterns using autocorrelation
    if len(delays) > 20:
        from scipy import signal

        autocorr = signal.correlate(delays, delays, mode="full")
        autocorr = autocorr[len(autocorr) // 2 :]
        peaks, _ = signal.find_peaks(autocorr, height=0)
        if len(peaks) > 1:
            stats["periodic_pattern_detected"] = True
            stats["periodicity_seconds"] = float(peaks[1] * np.mean(delays))
        else:
            stats["periodic_pattern_detected"] = False

    # Group by protocols
    protocol_stats = {}
    for pkt in packets:
        proto = "Other"
        if pkt.haslayer("TCP"):
            proto = "TCP"
        elif pkt.haslayer("UDP"):
            proto = "UDP"
        elif pkt.haslayer("ICMP"):
            proto = "ICMP"

        if proto not in protocol_stats:
            protocol_stats[proto] = {"count": 0, "bytes": 0}

        protocol_stats[proto]["count"] += 1
        protocol_stats[proto]["bytes"] += len(pkt)

    return {
        "statistics": stats,
        "protocol_distribution": protocol_stats,
        # Add more analysis results here
    }
