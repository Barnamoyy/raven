from pathlib import Path
from scapy.all import PacketList
import numpy as np
from sklearn.cluster import KMeans

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