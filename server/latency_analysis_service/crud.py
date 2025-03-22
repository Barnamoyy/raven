from pathlib import Path
from scapy.all import PacketList

def calculate_average_latency(file_path: Path,packets: PacketList) -> float:
    """Extracts packets from a PCAPNG file and calculates average latency."""
      # Extract file without saving output
    
    # Extract timestamps from packets
    timestamps = []
    

    timestamps = [pkt.time for pkt in packets if hasattr(pkt, 'time')]

    if len(timestamps) < 2:
        raise ValueError("Not enough packets to calculate latency.")
    
    # Compute latency between consecutive packets
    latency_values = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
    
    return sum(latency_values) / len(latency_values)  # Average latency