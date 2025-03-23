from pathlib import Path
from ..pattern_anomalies.crud import detect_network_patterns_anomalies
from ..pattern_detection.crud import advanced_pattern_detection
from scapy.all import PacketList


def analyze_network_congestion(file_path: Path, packets: PacketList):
    """Analyzes network congestion, jitter, and inefficient packet aggregation."""

    # Get base statistics from existing functions
    base_stats = advanced_pattern_detection(file_path, packets)
    mqtt_analysis = detect_network_patterns_anomalies(file_path, packets)

    # Extract congestion-specific metrics
    congestion_metrics = {
        "retransmission_rate": (
            mqtt_analysis["summary"]["retransmission_count"]
            / base_stats["statistics"]["packet_count"]
            if base_stats["statistics"]["packet_count"] > 0
            else 0
        ),
        "jitter_ms": base_stats["statistics"]["jitter"]
        * 1000,  # Convert to milliseconds
        "jitter_spikes": len(mqtt_analysis["anomalies"]["jitter_spikes"]),
        "packet_aggregation_inefficiency": len(
            mqtt_analysis["delay_categories"]["bundling_delays"]
        ),
        "congestion_events": len(mqtt_analysis["patterns"]["congestion_events"]),
    }

    # Calculate congestion score (0-100 scale)
    # This is a simplified example - you could weight these factors differently
    congestion_score = min(
        100,
        (
            (congestion_metrics["retransmission_rate"] * 50)
            + (min(1, congestion_metrics["jitter_ms"] / 100) * 25)
            + (min(1, congestion_metrics["jitter_spikes"] / 10) * 15)
            + (min(1, congestion_metrics["packet_aggregation_inefficiency"] / 20) * 10)
        ),
    )

    # Classify congestion level
    congestion_level = "Low"
    if congestion_score > 30:
        congestion_level = "Moderate"
    if congestion_score > 60:
        congestion_level = "High"
    if congestion_score > 80:
        congestion_level = "Severe"

    # Extract IP address information for aggregate stats
    ip_communication = {}

    # Create packet_flow list for individual packet flow information
    packet_flow = []

    # Track previous timestamp to calculate delays
    prev_timestamp = None
    flow_timestamps = {}  # Track timestamps by flow

    for i, pkt in enumerate(packets):
        flow_info = {"packet_id": i, "size": len(pkt)}

        # Add timestamp if available
        current_timestamp = None
        if hasattr(pkt, "time"):
            current_timestamp = float(pkt.time)
            flow_info["timestamp"] = current_timestamp

        # Check for IP layer
        if pkt.haslayer("IP"):
            flow_info["src_ip"] = pkt["IP"].src
            flow_info["dst_ip"] = pkt["IP"].dst

            # Add port information if available
            if pkt.haslayer("TCP"):
                flow_info["protocol"] = "TCP"
                flow_info["src_port"] = pkt["TCP"].sport
                flow_info["dst_port"] = pkt["TCP"].dport
                flow_info["flow"] = (
                    f"{pkt['IP'].src}:{pkt['TCP'].sport}-{pkt['IP'].dst}:{pkt['TCP'].dport}"
                )
            elif pkt.haslayer("UDP"):
                flow_info["protocol"] = "UDP"
                flow_info["src_port"] = pkt["UDP"].sport
                flow_info["dst_port"] = pkt["UDP"].dport
                flow_info["flow"] = (
                    f"{pkt['IP'].src}:{pkt['UDP'].sport}-{pkt['IP'].dst}:{pkt['UDP'].dport}"
                )
            else:
                flow_info["protocol"] = "IP"
                flow_info["flow"] = f"{pkt['IP'].src}-{pkt['IP'].dst}"
        elif pkt.haslayer("ARP"):
            flow_info["protocol"] = "ARP"
            if hasattr(pkt["ARP"], "psrc") and hasattr(pkt["ARP"], "pdst"):
                flow_info["src_ip"] = pkt["ARP"].psrc
                flow_info["dst_ip"] = pkt["ARP"].pdst
                flow_info["flow"] = f"ARP: {pkt['ARP'].psrc}-{pkt['ARP'].pdst}"
        else:
            flow_info["protocol"] = "Other"
            flow_info["flow"] = f"Unknown flow (packet {i})"

        # Calculate delay information
        if current_timestamp is not None:
            # Global delay (from first packet)
            if prev_timestamp is not None:
                flow_info["delay_from_previous_ms"] = (
                    current_timestamp - prev_timestamp
                ) * 1000

            # Flow-specific delay
            if "flow" in flow_info:
                flow_key = flow_info["flow"]
                if flow_key in flow_timestamps:
                    flow_info["flow_delay_ms"] = (
                        current_timestamp - flow_timestamps[flow_key]
                    ) * 1000
                flow_timestamps[flow_key] = current_timestamp

            # Update previous timestamp for next iteration
            prev_timestamp = current_timestamp

        # Add to packet_flow list
        packet_flow.append(flow_info)

        # Also update aggregate statistics
        if "flow" in flow_info:
            key = flow_info["flow"]

            if key not in ip_communication:
                ip_communication[key] = {
                    "src_ip": flow_info.get("src_ip", "Unknown"),
                    "dst_ip": flow_info.get("dst_ip", "Unknown"),
                    "src_port": flow_info.get("src_port", None),
                    "dst_port": flow_info.get("dst_port", None),
                    "protocol": flow_info.get("protocol", "Unknown"),
                    "packet_count": 0,
                    "bytes": 0,
                    "avg_delay_ms": 0,
                    "total_delay_ms": 0,
                }

            ip_communication[key]["packet_count"] += 1
            ip_communication[key]["bytes"] += len(pkt)

            # Update delay statistics for the flow
            if "flow_delay_ms" in flow_info:
                current_delay = flow_info["flow_delay_ms"]
                current_count = ip_communication[key]["packet_count"]

                # Update running average of delay
                ip_communication[key]["total_delay_ms"] += current_delay
                ip_communication[key]["avg_delay_ms"] = (
                    ip_communication[key]["total_delay_ms"] / (current_count - 1)
                    if current_count > 1
                    else 0
                )

    return {
        "congestion_metrics": congestion_metrics,
        "congestion_score": congestion_score,
        "congestion_level": congestion_level,
        "ip_communication": ip_communication,  # Aggregate stats by flow
        "packet_flow": packet_flow,  # Individual packet flow information
        "detailed_metrics": {
            "jitter_analysis": {
                "mean_jitter_ms": base_stats["statistics"]["jitter"] * 1000,
                "jitter_spikes": mqtt_analysis["anomalies"]["jitter_spikes"],
            },
            "packet_aggregation_analysis": {
                "bundling_events": mqtt_analysis["delay_categories"]["bundling_delays"],
                "avg_bundling_delay_ms": (
                    mqtt_analysis["summary"]["avg_bundling_delay"] * 1000
                    if "avg_bundling_delay" in mqtt_analysis["summary"]
                    else 0
                ),
            },
            "tcp_analysis": {
                "retransmissions": mqtt_analysis["delay_categories"]["retransmissions"],
                "protocol_distribution": base_stats["protocol_distribution"],
            },
        },
    }
