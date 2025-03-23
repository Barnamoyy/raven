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

    # Calculate packet loss
    # Assuming sequential packets should have consistent timing
    # Detect gaps that are significantly larger than the median delay
    median_delay = np.median(delays)
    threshold = median_delay * 3  # Threshold for considering a gap as packet loss
    large_gaps = delays[delays > threshold]
    estimated_lost_packets = sum(gap // median_delay for gap in large_gaps)

    stats["packet_loss_count"] = int(estimated_lost_packets)
    if len(timestamps) > 0:
        stats["packet_loss_percentage"] = float(
            estimated_lost_packets / len(timestamps) * 100
        )
    else:
        stats["packet_loss_percentage"] = 0.0

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

    # Group by protocols - detailed per packet
    protocol_stats = {}
    packet_protocols = []

    # Structure to track protocol-based latency
    protocol_latency = {}

    # Track packets by conversation (src IP, dst IP, src port, dst port)
    conversations = {}

    # Process each packet
    for i, pkt in enumerate(packets):
        # Get detailed protocol information for each packet
        packet_proto_info = {"packet_id": i}

        # Identify the highest layer protocol
        highest_layer = "Other"

        # Check common protocols
        if pkt.haslayer("TCP"):
            highest_layer = "TCP"
            if pkt.haslayer("HTTP"):
                highest_layer = "HTTP"
            elif pkt.haslayer("TLS") or pkt.haslayer("SSL"):
                highest_layer = "TLS/SSL"
        elif pkt.haslayer("UDP"):
            highest_layer = "UDP"
            if pkt.haslayer("DNS"):
                highest_layer = "DNS"
        elif pkt.haslayer("ICMP"):
            highest_layer = "ICMP"
        elif pkt.haslayer("ARP"):
            highest_layer = "ARP"

        packet_proto_info["protocol"] = highest_layer
        packet_proto_info["size"] = len(pkt)

        # Extract IP information
        src_ip = "N/A"
        dst_ip = "N/A"
        if pkt.haslayer("IP"):
            src_ip = pkt["IP"].src
            dst_ip = pkt["IP"].dst
        elif pkt.haslayer("IPv6"):
            src_ip = pkt["IPv6"].src
            dst_ip = pkt["IPv6"].dst

        packet_proto_info["src_ip"] = src_ip
        packet_proto_info["dst_ip"] = dst_ip

        # Extract port information
        src_port = "N/A"
        dst_port = "N/A"
        if pkt.haslayer("TCP"):
            src_port = pkt["TCP"].sport
            dst_port = pkt["TCP"].dport
        elif pkt.haslayer("UDP"):
            src_port = pkt["UDP"].sport
            dst_port = pkt["UDP"].dport

        packet_proto_info["src_port"] = src_port
        packet_proto_info["dst_port"] = dst_port

        # Add current timestamp
        if hasattr(pkt, "time"):
            packet_proto_info["timestamp"] = float(pkt.time)

            # Track conversation for delay calculation
            if highest_layer in ["TCP", "UDP", "HTTP", "TLS/SSL", "DNS"]:
                # Create a conversation key (a tuple of src/dst IPs and ports)
                forward_key = (src_ip, dst_ip, src_port, dst_port)
                reverse_key = (dst_ip, src_ip, dst_port, src_port)

                # For protocols with request/response pattern, we calculate delay
                # Check if this packet could be a response to a previous packet
                if reverse_key in conversations:
                    # This might be a response, calculate delay from the last packet in reverse direction
                    request_time = conversations[reverse_key]["last_time"]
                    packet_proto_info["delay"] = float(pkt.time) - request_time
                else:
                    # This is a new conversation or a continuing conversation in the same direction
                    packet_proto_info["delay"] = 0.0

                # Update conversation tracking
                if forward_key not in conversations:
                    conversations[forward_key] = {
                        "packets": 0,
                        "last_time": float(pkt.time),
                    }
                else:
                    conversations[forward_key]["last_time"] = float(pkt.time)
                conversations[forward_key]["packets"] += 1
            else:
                # For other protocols without clear request/response pattern
                packet_proto_info["delay"] = 0.0

        packet_protocols.append(packet_proto_info)

        # Also maintain the protocol distribution summary
        if highest_layer not in protocol_stats:
            protocol_stats[highest_layer] = {"count": 0, "bytes": 0}

        protocol_stats[highest_layer]["count"] += 1
        protocol_stats[highest_layer]["bytes"] += len(pkt)

        # Initialize protocol latency tracking
        if highest_layer not in protocol_latency:
            protocol_latency[highest_layer] = {
                "timestamps": [],
                "delays": [],
                "total_delay": 0,
                "count": 0,
                "avg_latency": 0,
            }

        # Add timestamp to the protocol's list
        if hasattr(pkt, "time"):
            protocol_latency[highest_layer]["timestamps"].append(float(pkt.time))

    # Calculate per-protocol latency statistics
    for protocol in protocol_latency:
        timestamps = protocol_latency[protocol]["timestamps"]
        if len(timestamps) > 1:
            # Calculate delays between packets of the same protocol
            delays = np.diff(timestamps)
            protocol_latency[protocol]["delays"] = delays.tolist()
            protocol_latency[protocol]["total_delay"] = float(np.sum(delays))
            protocol_latency[protocol]["count"] = len(delays)
            protocol_latency[protocol]["avg_latency"] = float(np.mean(delays))

            # Add additional latency statistics
            protocol_latency[protocol]["min_latency"] = float(np.min(delays))
            protocol_latency[protocol]["max_latency"] = float(np.max(delays))
            protocol_latency[protocol]["median_latency"] = float(np.median(delays))
            protocol_latency[protocol]["std_latency"] = float(np.std(delays))

            # Remove the raw timestamps and delays lists to keep output clean
            del protocol_latency[protocol]["timestamps"]
            del protocol_latency[protocol]["delays"]

    # Add protocol latency statistics to protocol_stats
    for protocol in protocol_latency:
        if protocol in protocol_stats:
            for key, value in protocol_latency[protocol].items():
                if key != "timestamps" and key != "delays":
                    protocol_stats[protocol][key] = value

    return {
        "statistics": stats,
        "protocol_distribution": protocol_stats,
        "packet_protocols": packet_protocols,
    }
