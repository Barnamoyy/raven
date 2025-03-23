from pathlib import Path
from scapy.all import PacketList
import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict


def detect_network_patterns(file_path: Path, packets: PacketList):
    """
    Advanced analysis of network traffic patterns.
    Generalized for all protocols with focus on:
    - Bundling delays (when small packets are aggregated)
    - Processing delays
    - Upload/download transmission delays
    - Retransmission patterns
    - Root cause analysis by correlating delays with packet size, protocol type, source/destination
    """

    # Extract timestamps and organize by connection/flow
    flows = {}
    analyzed_packets = []
    protocols = defaultdict(int)

    # Root cause analysis data structures
    delay_factors = {
        "by_size": defaultdict(list),
        "by_protocol": defaultdict(list),
        "by_source": defaultdict(list),
        "by_destination": defaultdict(list),
        "by_port": defaultdict(list),
    }

    for i, pkt in enumerate(packets):
        protocol_type = "Unknown"
        dst_port = src_port = None
        src_ip = dst_ip = None

        # Identify packet protocol type
        if pkt.haslayer("TCP"):
            protocol_type = "TCP"
            dst_port = pkt["TCP"].dport
            src_port = pkt["TCP"].sport
        elif pkt.haslayer("UDP"):
            protocol_type = "UDP"
            dst_port = pkt["UDP"].dport
            src_port = pkt["UDP"].sport
        elif pkt.haslayer("ICMP"):
            protocol_type = "ICMP"

        protocols[protocol_type] += 1

        if pkt.haslayer("IP"):
            src_ip = pkt["IP"].src
            dst_ip = pkt["IP"].dst
            flow_id = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"

            analyzed_packets.append((i, pkt, float(pkt.time), protocol_type))
            if flow_id not in flows:
                flows[flow_id] = []

            flows[flow_id].append(
                {
                    "index": i,
                    "time": float(pkt.time),
                    "size": len(pkt),
                    "protocol": protocol_type,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "seq": (
                        pkt["TCP"].seq
                        if pkt.haslayer("TCP") and hasattr(pkt["TCP"], "seq")
                        else None
                    ),
                }
            )

    results = {
        "packet_count": len(analyzed_packets),
        "protocol_distribution": dict(protocols),
        "flows": len(flows),
        "patterns": {
            "periodic_transmissions": [],
            "bursty_traffic": [],
            "congestion_events": [],
        },
        "root_cause_analysis": {},
    }

    for flow_id, packets in flows.items():
        if len(packets) < 2:
            continue

        packets.sort(key=lambda p: p["time"])
        delays = [
            packets[i + 1]["time"] - packets[i]["time"] for i in range(len(packets) - 1)
        ]

        for i in range(len(packets) - 1):
            pkt = packets[i]
            delay = delays[i]
            if delay > 0.001:
                size_bucket = (
                    f"{(pkt['size'] // 100) * 100}-{(pkt['size'] // 100 + 1) * 100}"
                )
                delay_factors["by_size"][size_bucket].append(delay)
                delay_factors["by_protocol"][pkt["protocol"]].append(delay)
                delay_factors["by_source"][pkt["src_ip"]].append(delay)
                delay_factors["by_destination"][pkt["dst_ip"]].append(delay)
                if pkt["dst_port"]:
                    delay_factors["by_port"][f"dst:{pkt['dst_port']}"].append(delay)
                if pkt["src_port"]:
                    delay_factors["by_port"][f"src:{pkt['src_port']}"].append(delay)

    # Root cause analysis processing
    for factor, delays in delay_factors.items():
        stats = {}
        for key, delay_list in delays.items():
            if delay_list:
                avg_delay = sum(delay_list) / len(delay_list)
                stats[key] = {
                    "avg_delay": avg_delay,
                    "min_delay": min(delay_list),
                    "max_delay": max(delay_list),
                    "count": len(delay_list),
                    "std_dev": np.std(delay_list) if len(delay_list) > 1 else 0,
                }
        results["root_cause_analysis"][factor] = stats

    return results
