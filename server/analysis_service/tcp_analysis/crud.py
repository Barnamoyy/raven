from pathlib import Path
from scapy.all import PacketList
import numpy as np


def analyze_tcp_window_size(file_path: Path,packets: PacketList):
    """Analyzes TCP window size to identify congestion."""
    
    window_sizes = []
    zero_window_events = []
    window_scale_factors = {}
    
    for i, pkt in enumerate(packets):
        if pkt.haslayer("TCP"):
            tcp_layer = pkt["TCP"]
            
            # Get source and destination information safely
            src_info = "Unknown"
            dst_info = "Unknown"
            
            if pkt.haslayer("IP"):
                src_ip = pkt["IP"].src
                dst_ip = pkt["IP"].dst
                src_info = f"{src_ip}:{tcp_layer.sport}"
                dst_info = f"{dst_ip}:{tcp_layer.dport}"
                connection = f"{src_info}-{dst_info}"
            elif pkt.haslayer("IPv6"):
                src_ip = pkt["IPv6"].src
                dst_ip = pkt["IPv6"].dst
                src_info = f"{src_ip}:{tcp_layer.sport}"
                dst_info = f"{dst_ip}:{tcp_layer.dport}"
                connection = f"{src_info}-{dst_info}"
            else:
                # If neither IP nor IPv6, just use ports
                connection = f"unknown:{tcp_layer.sport}-unknown:{tcp_layer.dport}"
            
            # Get window size
            if hasattr(tcp_layer, "window"):
                window_sizes.append({
                    "packet_index": i,
                    "time": float(pkt.time),
                    "window_size": tcp_layer.window,
                    "src": src_info
                })
                
                # Check for zero window - congestion indicator
                if tcp_layer.window == 0:
                    zero_window_events.append({
                        "packet_index": i,
                        "time": float(pkt.time),
                        "src": src_info
                    })
            
            # Look for window scaling option
            if hasattr(tcp_layer, "options"):
                for option_name, option_value in tcp_layer.options:
                    if option_name == "WScale":
                        window_scale_factors[connection] = option_value
    
    # Analyze window size variations
    window_analysis = {}
    if window_sizes:
        hosts = set([item["src"] for item in window_sizes])
        for host in hosts:
            host_windows = [item["window_size"] for item in window_sizes if item["src"] == host]
            if host_windows:
                window_analysis[host] = {
                    "min": min(host_windows),
                    "max": max(host_windows),
                    "mean": sum(host_windows) / len(host_windows),
                    "variation": np.std(host_windows) / (sum(host_windows) / len(host_windows)) if sum(host_windows) > 0 else 0
                }
    
    return {
        "window_size_analysis": window_analysis,
        "zero_window_events": zero_window_events,
        "window_scale_factors": window_scale_factors,
        "congestion_indicators": {
            "zero_window_count": len(zero_window_events),
            "window_size_variation": np.mean([analysis["variation"] for analysis in window_analysis.values()]) if window_analysis else 0
        }
    }