from pathlib import Path
from scapy.all import PacketList


def analyze_network_congestion(file_path: Path, packets: PacketList):
    """
    Analyzes network congestion, jitter, and inefficient packet aggregation
    without dependencies on other functions.

    Args:
        file_path: Path to the packet capture file
        packets: Scapy PacketList object containing network packets

    Returns:
        Dictionary with congestion analysis results
    """
    # Initialize statistics
    packet_count = len(packets)
    retransmission_count = 0
    jitter_values = []
    jitter_spikes = []
    bundling_delays = []
    congestion_events = []
    protocol_distribution = {}

    # Extract IP address information for aggregate stats
    ip_communication = {}

    # Create packet_flow list for individual packet flow information
    packet_flow = []

    # Track previous timestamp to calculate delays
    prev_timestamp = None
    flow_timestamps = {}  # Track timestamps by flow
    last_seq_nums = {}  # Track TCP sequence numbers for retransmission detection
    bulk_upload_flows = set()  # Track flows with bulk uploads
    known_brokers = set()  # Set of IPs identified as brokers
    packet_counts_by_flow = {}  # Track packet counts for bulk upload detection

    # Set thresholds
    JITTER_SPIKE_THRESHOLD_MS = 50  # ms
    BUNDLING_DELAY_THRESHOLD_MS = 25  # ms
    CONGESTION_WINDOW_SIZE = 10  # packets
    BULK_UPLOAD_THRESHOLD = (
        15  # Number of packets in short time to consider bulk upload
    )
    BULK_UPLOAD_TIME_WINDOW = 1.0  # seconds

    # Common broker ports (for broker detection)
    BROKER_PORTS = {
        1883,
        8883,
        8884,
        8885,
        8886,
        5671,
        5672,
    }  # MQTT, AMQP typical ports

    # Sliding window for congestion detection
    delay_window = []

    # First pass to identify broker IPs based on port usage
    for pkt in packets:
        if pkt.haslayer("TCP") or pkt.haslayer("UDP"):
            layer = "TCP" if pkt.haslayer("TCP") else "UDP"
            if pkt[layer].sport in BROKER_PORTS:
                known_brokers.add(pkt["IP"].src)
            if pkt[layer].dport in BROKER_PORTS:
                known_brokers.add(pkt["IP"].dst)

    # Main packet analysis
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

            # Track protocol distribution
            ip_proto = pkt["IP"].proto
            proto_name = "Other"

            # Add port information if available
            if pkt.haslayer("TCP"):
                flow_info["protocol"] = "TCP"
                flow_info["src_port"] = pkt["TCP"].sport
                flow_info["dst_port"] = pkt["TCP"].dport
                flow_info["flow"] = (
                    f"{pkt['IP'].src}:{pkt['TCP'].sport}-{pkt['IP'].dst}:{pkt['TCP'].dport}"
                )
                proto_name = "TCP"

                # Check for TCP retransmission
                flow_key = flow_info["flow"]
                seq_num = pkt["TCP"].seq

                if flow_key in last_seq_nums and seq_num == last_seq_nums[flow_key]:
                    retransmission_count += 1
                    flow_info["retransmission"] = True

                last_seq_nums[flow_key] = seq_num

            elif pkt.haslayer("UDP"):
                flow_info["protocol"] = "UDP"
                flow_info["src_port"] = pkt["UDP"].sport
                flow_info["dst_port"] = pkt["UDP"].dport
                flow_info["flow"] = (
                    f"{pkt['IP'].src}:{pkt['UDP'].sport}-{pkt['IP'].dst}:{pkt['UDP'].dport}"
                )
                proto_name = "UDP"
            else:
                flow_info["protocol"] = "IP"
                flow_info["flow"] = f"{pkt['IP'].src}-{pkt['IP'].dst}"

            # Update protocol distribution
            protocol_distribution[proto_name] = (
                protocol_distribution.get(proto_name, 0) + 1
            )

        elif pkt.haslayer("ARP"):
            flow_info["protocol"] = "ARP"
            if hasattr(pkt["ARP"], "psrc") and hasattr(pkt["ARP"], "pdst"):
                flow_info["src_ip"] = pkt["ARP"].psrc
                flow_info["dst_ip"] = pkt["ARP"].pdst
                flow_info["flow"] = f"ARP: {pkt['ARP'].psrc}-{pkt['ARP'].pdst}"

            # Update protocol distribution
            protocol_distribution["ARP"] = protocol_distribution.get("ARP", 0) + 1

        else:
            flow_info["protocol"] = "Other"
            flow_info["flow"] = f"Unknown flow (packet {i})"

            # Update protocol distribution
            protocol_distribution["Other"] = protocol_distribution.get("Other", 0) + 1

        # Calculate delay information
        if current_timestamp is not None:
            # Global delay (from first packet)
            if prev_timestamp is not None:
                packet_delay_ms = (current_timestamp - prev_timestamp) * 1000
                flow_info["delay_from_previous_ms"] = packet_delay_ms

                # Track jitter (variation in delay)
                jitter_values.append(packet_delay_ms)

                # Check for jitter spikes
                if (
                    len(jitter_values) > 1
                    and packet_delay_ms > JITTER_SPIKE_THRESHOLD_MS
                ):
                    jitter_spikes.append(
                        {
                            "packet_id": i,
                            "delay_ms": packet_delay_ms,
                            "timestamp": current_timestamp,
                        }
                    )

                # Update delay window for congestion detection
                delay_window.append(packet_delay_ms)
                if len(delay_window) > CONGESTION_WINDOW_SIZE:
                    delay_window.pop(0)

                # Detect congestion events (sustained high delays)
                if (
                    len(delay_window) == CONGESTION_WINDOW_SIZE
                    and sum(delay_window) / len(delay_window)
                    > JITTER_SPIKE_THRESHOLD_MS
                ):
                    congestion_events.append(
                        {
                            "start_packet": i - CONGESTION_WINDOW_SIZE,
                            "end_packet": i,
                            "avg_delay_ms": sum(delay_window) / len(delay_window),
                            "timestamp": current_timestamp,
                        }
                    )

            # Flow-specific delay
            if "flow" in flow_info:
                flow_key = flow_info["flow"]

                # Track packet counts by flow for bulk upload detection
                if flow_key not in packet_counts_by_flow:
                    packet_counts_by_flow[flow_key] = {
                        "count": 0,
                        "first_timestamp": current_timestamp,
                    }

                packet_counts_by_flow[flow_key]["count"] += 1
                packet_counts_by_flow[flow_key]["last_timestamp"] = current_timestamp

                # Detect bulk uploads (many packets in a short time)
                if (
                    packet_counts_by_flow[flow_key]["count"] >= BULK_UPLOAD_THRESHOLD
                    and (
                        current_timestamp
                        - packet_counts_by_flow[flow_key]["first_timestamp"]
                    )
                    <= BULK_UPLOAD_TIME_WINDOW
                ):
                    bulk_upload_flows.add(flow_key)

                if flow_key in flow_timestamps:
                    flow_delay_ms = (
                        current_timestamp - flow_timestamps[flow_key]
                    ) * 1000
                    flow_info["flow_delay_ms"] = flow_delay_ms

                    # Check for bundling delays (potentially inefficient packet aggregation)
                    if flow_delay_ms > BUNDLING_DELAY_THRESHOLD_MS:
                        bundling_delays.append(
                            {
                                "flow": flow_key,
                                "packet_id": i,
                                "delay_ms": flow_delay_ms,
                                "timestamp": current_timestamp,
                            }
                        )

                flow_timestamps[flow_key] = current_timestamp

            # Update previous timestamp for next iteration
            prev_timestamp = current_timestamp

        # Add packet classification fields
        # Add retransmission classification (already detected earlier)
        flow_info["packet_type"] = {
            "transmission": not flow_info.get("retransmission", False),
            "retransmission": flow_info.get("retransmission", False),
            "bulk_upload": "flow" in flow_info
            and flow_info["flow"] in bulk_upload_flows,
            "broker": False,  # Will be updated below
            "device_to_broker": False,  # Will be updated below
        }

        # Determine if broker-related
        if "src_ip" in flow_info and "dst_ip" in flow_info:
            # If either source or destination is a known broker
            if flow_info["src_ip"] in known_brokers:
                flow_info["packet_type"]["broker"] = True
                if flow_info["dst_ip"] not in known_brokers:
                    flow_info["packet_type"]["device_to_broker"] = True
            elif flow_info["dst_ip"] in known_brokers:
                flow_info["packet_type"]["broker"] = True
                flow_info["packet_type"]["device_to_broker"] = True

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

    # Calculate jitter (average of absolute differences between consecutive delays)
    jitter = 0
    if len(jitter_values) > 1:
        jitter_diffs = [
            abs(jitter_values[i] - jitter_values[i - 1])
            for i in range(1, len(jitter_values))
        ]
        jitter = sum(jitter_diffs) / len(jitter_diffs) if jitter_diffs else 0

    # Calculate average bundling delay
    avg_bundling_delay = (
        sum([d["delay_ms"] for d in bundling_delays]) / len(bundling_delays)
        if bundling_delays
        else 0
    )

    # Extract congestion-specific metrics
    congestion_metrics = {
        "retransmission_rate": (
            retransmission_count / packet_count if packet_count > 0 else 0
        ),
        "jitter_ms": jitter,
        "jitter_spikes": len(jitter_spikes),
        "packet_aggregation_inefficiency": len(bundling_delays),
        "congestion_events": len(congestion_events),
    }

    # Calculate congestion score (0-100 scale)
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

    return {
        "congestion_metrics": congestion_metrics,
        "congestion_score": congestion_score,
        "congestion_level": congestion_level,
        "ip_communication": ip_communication,  # Aggregate stats by flow
        "packet_flow": packet_flow,  # Individual packet flow information
        "detailed_metrics": {
            "jitter_analysis": {
                "mean_jitter_ms": jitter,
                "jitter_spikes": jitter_spikes,
            },
            "tcp_analysis": {
                "retransmissions": [
                    p for p in packet_flow if p.get("retransmission", False)
                ],
            },
        },
    }
