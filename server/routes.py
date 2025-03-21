from fastapi import APIRouter, Depends, UploadFile, File,HTTPException
from sqlalchemy.orm import Session
from pcapkit import extract
# from pcapkit.foundation.engines.scapy import ScapySniffer
from scapy.all import rdpcap,PacketList
import shutil
from pathlib import Path
from database import get_db
from storage_service import crud, schema
from packet_extract_service.crud import extract_and_store_packets
import numpy as np
from sklearn.cluster import KMeans  # ✅ Correct



router = APIRouter(prefix="/storage", tags=["Storage"])

UPLOAD_DIR = Path("uploaded_pcapng_files")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload/")
async def upload_pcapng(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_path = UPLOAD_DIR / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # file_data = schema.PcapngFileCreate(filename=file.filename)
    # stored_file = crud.create_pcapng_file(db, file_data)
    
    packets = rdpcap(str(file_path)) # Run scapy to extract packets

    
    
    try:
        avg_latency = calculate_average_latency(file_path,packets)    
        print(f"Average latency: {avg_latency}")    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        # Extract and store packets
        extract_and_store_packets(file_path, stored_file["id"], db)  # ✅ Now it works!

        print(f"Packets extracted and stored for {file.filename}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        pattern_analysis = advanced_pattern_detection(file_path,packets)
        print("Pattern analysis completed")        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))   
    
    try:
        mqtt_analysis = detect_mqtt_patterns_anomalies(file_path,packets)
        print("MQTT analysis completed")        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    try:
        congestion_analysis = analyze_network_congestion(file_path,packets)
        print(f"Network congestion level: {congestion_analysis['congestion_level']}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    try:
        tcp_window_analysis = analyze_tcp_window_size(file_path,packets)
        print(f"Zero window events: {tcp_window_analysis['congestion_indicators']['zero_window_count']}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Combine all analyses into a comprehensive result
    analysis_results = {
        "average_latency": avg_latency,
        "pattern_analysis": pattern_analysis,
        "mqtt_analysis": mqtt_analysis,
        "congestion_analysis": congestion_analysis,
        "tcp_window_analysis": tcp_window_analysis
    }
    
    return analysis_results

@router.get("/", response_model=list[schema.PcapngFileResponse])
async def list_pcapng_files(db: Session = Depends(get_db)):
    return crud.get_pcapng_files(db)


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


def advanced_pattern_detection(file_path: Path,packets: PacketList):
    """Performs advanced pattern detection on network traffic."""
    timestamps = [float(pkt.time) for pkt in packets if hasattr(pkt, 'time')]
    
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
        "packet_count": len(timestamps)
    }
    
    # Detect periodic patterns using autocorrelation
    if len(delays) > 20:
        from scipy import signal
        autocorr = signal.correlate(delays, delays, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
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
        if pkt.haslayer("TCP"): proto = "TCP"
        elif pkt.haslayer("UDP"): proto = "UDP"
        elif pkt.haslayer("ICMP"): proto = "ICMP"
        
        if proto not in protocol_stats:
            protocol_stats[proto] = {"count": 0, "bytes": 0}
        
        protocol_stats[proto]["count"] += 1
        protocol_stats[proto]["bytes"] += len(pkt)
    
    return {
        "statistics": stats,
        "protocol_distribution": protocol_stats,
        # Add more analysis results here
    }
    
    
def detect_mqtt_patterns_anomalies(file_path: Path,packets: PacketList):
    """
    # Advanced analysis of MQTT traffic patterns and anomalies.
    # Specifically designed for IoT applications with focus on:
    # - Bundling delays (when small packets are aggregated)
    # - Broker processing delays
    # - Upload/download transmission delays
    # - Retransmission patterns
    # """
    
    # Extract timestamps and organize by connection/flow
    flows = {}
    mqtt_packets = []
    
    for i, pkt in enumerate(packets):
        # Identify MQTT packets (typically on port 1883 or 8883)
        is_mqtt = False
        dst_port = src_port = None
        
        if pkt.haslayer("TCP"):
            dst_port = pkt["TCP"].dport
            src_port = pkt["TCP"].sport
            if dst_port == 1883 or dst_port == 8883 or src_port == 1883 or src_port == 8883:
                is_mqtt = True
        
        if not is_mqtt and pkt.haslayer("UDP"):
            dst_port = pkt["UDP"].dport
            src_port = pkt["UDP"].sport
            # Some MQTT implementations use UDP
            if dst_port == 1883 or dst_port == 8883 or src_port == 1883 or src_port == 8883:
                is_mqtt = True
        
        if is_mqtt:
            mqtt_packets.append((i, pkt, float(pkt.time)))
            
            # Create flow identifier
            if pkt.haslayer("IP"):
                src_ip = pkt["IP"].src
                dst_ip = pkt["IP"].dst
                flow_id = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
                
                if flow_id not in flows:
                    flows[flow_id] = []
                
                flows[flow_id].append({
                    "index": i,
                    "time": float(pkt.time),
                    "size": len(pkt),
                    "is_ack": pkt.haslayer("TCP") and pkt["TCP"].flags.A,
                    "is_retransmission": False,  # Will be updated later
                    "seq": pkt["TCP"].seq if pkt.haslayer("TCP") and hasattr(pkt["TCP"], "seq") else None
                })
    
    # Calculate statistics and identify patterns
    results = {
        "mqtt_packet_count": len(mqtt_packets),
        "mqtt_flows": len(flows),
        "delay_categories": {
            "bundling_delays": [],
            "broker_processing_delays": [],
            "transmission_delays": [],
            "retransmissions": []
        },
        "patterns": {
            "periodic_transmissions": [],
            "bursty_traffic": [],
            "congestion_events": []
        },
        "anomalies": {
            "irregular_delays": [],
            "packet_loss_indicators": [],
            "jitter_spikes": []
        }
    }
    
    # Process each flow to identify delays and patterns
    for flow_id, packets in flows.items():
        if len(packets) < 2:
            continue
            
        # Sort by time
        packets.sort(key=lambda p: p["time"])
        
        # Identify retransmissions (duplicate sequence numbers)
        seq_seen = {}
        for i, pkt in enumerate(packets):
            if pkt["seq"] is not None:
                if pkt["seq"] in seq_seen:
                    packets[i]["is_retransmission"] = True
                    results["delay_categories"]["retransmissions"].append({
                        "flow": flow_id,
                        "packet_index": pkt["index"],
                        "original_index": seq_seen[pkt["seq"]],
                        "delay": pkt["time"] - packets[seq_seen[pkt["seq"]]]["time"]
                    })
                else:
                    seq_seen[pkt["seq"]] = i
        
        # Calculate inter-packet delays and identify patterns
        delays = [packets[i+1]["time"] - packets[i]["time"] for i in range(len(packets)-1)]
        
        # Identify periodic transmissions (consistent delays)
        if len(delays) > 5:
            mean_delay = sum(delays) / len(delays)
            std_delay = np.std(delays)
            
            # If standard deviation is low relative to mean, likely periodic
            if std_delay < 0.2 * mean_delay and mean_delay > 0.001:  # Avoid false positives on too small delays
                results["patterns"]["periodic_transmissions"].append({
                    "flow": flow_id, 
                    "period": mean_delay,
                    "confidence": 1.0 - (std_delay / mean_delay)
                })
        
        # Identify bursty traffic (clusters of packets followed by longer gaps)
        if len(delays) > 10:
            # Use k-means clustering to identify natural groupings in the delays
            delay_array = np.array(delays).reshape(-1, 1)
            kmeans = KMeans(n_clusters=2, random_state=0).fit(delay_array)
            
            # The larger cluster center indicates the gap between bursts
            cluster_centers = sorted(kmeans.cluster_centers_.flatten())
            if len(cluster_centers) > 1 and cluster_centers[1] > 3 * cluster_centers[0]:
                burst_indices = [i for i, label in enumerate(kmeans.labels_) if label == np.argmin(kmeans.cluster_centers_)]
                
                # If we have substantial bursts
                if len(burst_indices) > 5 and len(burst_indices) < len(delays) - 5:
                    results["patterns"]["bursty_traffic"].append({
                        "flow": flow_id,
                        "avg_burst_size": len(burst_indices) / (np.sum(kmeans.labels_ == np.argmax(kmeans.cluster_centers_)) + 1),
                        "avg_gap": float(cluster_centers[1])
                    })
        
        # Identify bundling delays (small packets followed by larger ones)
        for i in range(len(packets) - 1):
            # Look for small packet followed by larger one after a delay
            if packets[i]["size"] < 100 and packets[i+1]["size"] > 300 and delays[i] > 0.05:
                results["delay_categories"]["bundling_delays"].append({
                    "flow": flow_id,
                    "start_packet": packets[i]["index"],
                    "end_packet": packets[i+1]["index"],
                    "delay": delays[i],
                    "size_ratio": packets[i+1]["size"] / packets[i]["size"]
                })
        
        # Identify broker processing delays (request-response patterns)
        for i in range(len(packets) - 1):
            # For simplicity, look for alternating patterns of non-ACK packets
            if i < len(packets) - 2 and not packets[i]["is_ack"] and packets[i+1]["is_ack"] and not packets[i+2]["is_ack"]:
                processing_delay = packets[i+2]["time"] - packets[i]["time"]
                if 0.001 < processing_delay < 1.0:  # Reasonable processing delay range
                    results["delay_categories"]["broker_processing_delays"].append({
                        "flow": flow_id,
                        "request_packet": packets[i]["index"],
                        "response_packet": packets[i+2]["index"],
                        "delay": processing_delay
                    })
        
        # Identify anomalies - irregular delays
        if len(delays) > 5:
            mean_delay = sum(delays) / len(delays)
            std_delay = np.std(delays)
            threshold = mean_delay + 3 * std_delay
            
            for i, delay in enumerate(delays):
                if delay > threshold:
                    results["anomalies"]["irregular_delays"].append({
                        "flow": flow_id,
                        "packet_index": packets[i+1]["index"],
                        "delay": delay,
                        "z_score": (delay - mean_delay) / std_delay
                    })
        
        # Calculate jitter (variation in delay)
        if len(delays) > 3:
            jitter_values = [abs(delays[i] - delays[i-1]) for i in range(1, len(delays))]
            mean_jitter = sum(jitter_values) / len(jitter_values)
            
            # Identify jitter spikes
            for i, jitter in enumerate(jitter_values):
                if jitter > 5 * mean_jitter and jitter > 0.01:  # Significant jitter spike
                    results["anomalies"]["jitter_spikes"].append({
                        "flow": flow_id,
                        "packet_index": packets[i+1]["index"],
                        "jitter": jitter,
                        "ratio_to_mean": jitter / mean_jitter
                    })
    
    # Add summary statistics
    results["summary"] = {
        "avg_bundling_delay": np.mean([d["delay"] for d in results["delay_categories"]["bundling_delays"]]) if results["delay_categories"]["bundling_delays"] else 0,
        "avg_processing_delay": np.mean([d["delay"] for d in results["delay_categories"]["broker_processing_delays"]]) if results["delay_categories"]["broker_processing_delays"] else 0,
        "retransmission_count": len(results["delay_categories"]["retransmissions"]),
        "periodic_flow_count": len(results["patterns"]["periodic_transmissions"]),
        "bursty_flow_count": len(results["patterns"]["bursty_traffic"]),
        "anomaly_count": len(results["anomalies"]["irregular_delays"]) + len(results["anomalies"]["jitter_spikes"])
    }
    
    return results


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