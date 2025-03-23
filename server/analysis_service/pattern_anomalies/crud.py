from pathlib import Path
from scapy.all import PacketList
import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict


def detect_network_patterns_anomalies(file_path: Path, packets: PacketList):
    """
    # Advanced analysis of network traffic patterns and anomalies.
    # Generalized for all protocols with focus on:
    # - Bundling delays (when small packets are aggregated)
    # - Processing delays
    # - Upload/download transmission delays
    # - Retransmission patterns
    # - Root cause analysis by correlating delays with packet size, protocol type, source/destination
    """

    # Extract timestamps and organize by connection/flow
    flows = {}
    analyzed_packets = []
    protocols = defaultdict(int)

    # Root cause analysis data structures
    delay_factors = {
        "by_size": defaultdict(list),  # Delays by packet size ranges
        "by_protocol": defaultdict(list),  # Delays by protocol
        "by_source": defaultdict(list),  # Delays by source IP
        "by_destination": defaultdict(list),  # Delays by destination IP
        "by_port": defaultdict(list),  # Delays by port
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

        # Count protocols for statistics
        protocols[protocol_type] += 1

        # Get IP information if available
        if pkt.haslayer("IP"):
            src_ip = pkt["IP"].src
            dst_ip = pkt["IP"].dst

            # Create flow identifier
            flow_id = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"

            analyzed_packets.append((i, pkt, float(pkt.time), protocol_type))

            if flow_id not in flows:
                flows[flow_id] = []

            # Store packet info
            packet_info = {
                "index": i,
                "time": float(pkt.time),
                "size": len(pkt),
                "protocol": protocol_type,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port,
                "is_ack": (
                    pkt.haslayer("TCP") and pkt["TCP"].flags.A
                    if pkt.haslayer("TCP")
                    else False
                ),
                "is_retransmission": False,  # Will be updated later
                "seq": (
                    pkt["TCP"].seq
                    if pkt.haslayer("TCP") and hasattr(pkt["TCP"], "seq")
                    else None
                ),
            }

            flows[flow_id].append(packet_info)

    # Calculate statistics and identify patterns
    results = {
        "packet_count": len(analyzed_packets),
        "protocol_distribution": dict(protocols),
        "flows": len(flows),
        "patterns": {
            "periodic_transmissions": [],
            "bursty_traffic": [],
            "congestion_events": [],
        },
        "anomalies": {
            "irregular_delays": [],
            "packet_loss_indicators": [],
            "jitter_spikes": [],
        },
        "root_cause_analysis": {
            "size_correlation": {},
            "protocol_correlation": {},
            "source_correlation": {},
            "destination_correlation": {},
            "port_correlation": {},
        },
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
                    retransmission_delay = (
                        pkt["time"] - packets[seq_seen[pkt["seq"]]]["time"]
                    )

                    # Record for root cause analysis
                    size_bucket = (
                        f"{(pkt['size'] // 100) * 100}-{(pkt['size'] // 100 + 1) * 100}"
                    )
                    delay_factors["by_size"][size_bucket].append(retransmission_delay)
                    delay_factors["by_protocol"][pkt["protocol"]].append(
                        retransmission_delay
                    )
                    delay_factors["by_source"][pkt["src_ip"]].append(
                        retransmission_delay
                    )
                    delay_factors["by_destination"][pkt["dst_ip"]].append(
                        retransmission_delay
                    )
                    if pkt["dst_port"]:
                        delay_factors["by_port"][f"dst:{pkt['dst_port']}"].append(
                            retransmission_delay
                        )
                    if pkt["src_port"]:
                        delay_factors["by_port"][f"src:{pkt['src_port']}"].append(
                            retransmission_delay
                        )
                else:
                    seq_seen[pkt["seq"]] = i

        # Calculate inter-packet delays and identify patterns
        delays = [
            packets[i + 1]["time"] - packets[i]["time"] for i in range(len(packets) - 1)
        ]

        # Store inter-packet delays for root cause analysis
        for i in range(len(packets) - 1):
            pkt = packets[i]
            next_pkt = packets[i + 1]
            delay = delays[i]

            # Only record significant delays (adjust threshold as needed)
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

        # Identify periodic transmissions (consistent delays)
        if len(delays) > 5:
            mean_delay = sum(delays) / len(delays)
            std_delay = np.std(delays)

            # If standard deviation is low relative to mean, likely periodic
            if (
                std_delay < 0.2 * mean_delay and mean_delay > 0.001
            ):  # Avoid false positives on too small delays
                results["patterns"]["periodic_transmissions"].append(
                    {
                        "flow": flow_id,
                        "period": mean_delay,
                        "confidence": 1.0 - (std_delay / mean_delay),
                        "protocol": packets[0]["protocol"],
                        "src_ip": packets[0]["src_ip"],
                        "dst_ip": packets[0]["dst_ip"],
                    }
                )

        # Identify bursty traffic (clusters of packets followed by longer gaps)
        if len(delays) > 10:
            # Use k-means clustering to identify natural groupings in the delays
            delay_array = np.array(delays).reshape(-1, 1)
            kmeans = KMeans(n_clusters=2, random_state=0).fit(delay_array)

            # The larger cluster center indicates the gap between bursts
            cluster_centers = sorted(kmeans.cluster_centers_.flatten())
            if len(cluster_centers) > 1 and cluster_centers[1] > 3 * cluster_centers[0]:
                burst_indices = [
                    i
                    for i, label in enumerate(kmeans.labels_)
                    if label == np.argmin(kmeans.cluster_centers_)
                ]

                # If we have substantial bursts
                if len(burst_indices) > 5 and len(burst_indices) < len(delays) - 5:
                    results["patterns"]["bursty_traffic"].append(
                        {
                            "flow": flow_id,
                            "avg_burst_size": len(burst_indices)
                            / (
                                np.sum(
                                    kmeans.labels_ == np.argmax(kmeans.cluster_centers_)
                                )
                                + 1
                            ),
                            "avg_gap": float(cluster_centers[1]),
                            "protocol": packets[0]["protocol"],
                            "src_ip": packets[0]["src_ip"],
                            "dst_ip": packets[0]["dst_ip"],
                        }
                    )

        # Identify anomalies - irregular delays
        if len(delays) > 5:
            mean_delay = sum(delays) / len(delays)
            std_delay = np.std(delays)
            threshold = mean_delay + 3 * std_delay

            for i, delay in enumerate(delays):
                if delay > threshold:
                    results["anomalies"]["irregular_delays"].append(
                        {
                            "flow": flow_id,
                            "packet_index": packets[i + 1]["index"],
                            "delay": delay,
                            "z_score": (delay - mean_delay) / std_delay,
                            "protocol": packets[i + 1]["protocol"],
                            "size": packets[i + 1]["size"],
                            "src_ip": packets[i + 1]["src_ip"],
                            "dst_ip": packets[i + 1]["dst_ip"],
                        }
                    )

        # Calculate jitter (variation in delay)
        if len(delays) > 3:
            jitter_values = [
                abs(delays[i] - delays[i - 1]) for i in range(1, len(delays))
            ]
            mean_jitter = sum(jitter_values) / len(jitter_values)

            # Identify jitter spikes
            for i, jitter in enumerate(jitter_values):
                if (
                    jitter > 5 * mean_jitter and jitter > 0.01
                ):  # Significant jitter spike
                    results["anomalies"]["jitter_spikes"].append(
                        {
                            "flow": flow_id,
                            "packet_index": packets[i + 1]["index"],
                            "jitter": jitter,
                            "ratio_to_mean": jitter / mean_jitter,
                            "protocol": packets[i + 1]["protocol"],
                            "size": packets[i + 1]["size"],
                            "src_ip": packets[i + 1]["src_ip"],
                            "dst_ip": packets[i + 1]["dst_ip"],
                        }
                    )

    # Perform root cause analysis

    # Analyze correlation with packet size
    if delay_factors["by_size"]:
        size_stats = {}
        for size_range, delays in delay_factors["by_size"].items():
            if delays:
                avg_delay = sum(delays) / len(delays)
                size_stats[size_range] = {
                    "avg_delay": avg_delay,
                    "min_delay": min(delays),
                    "max_delay": max(delays),
                    "count": len(delays),
                    "std_dev": np.std(delays) if len(delays) > 1 else 0,
                }

        # Sort by average delay to identify most problematic size ranges
        sorted_sizes = sorted(
            size_stats.items(), key=lambda x: x[1]["avg_delay"], reverse=True
        )
        results["root_cause_analysis"]["size_correlation"] = {
            k: v for k, v in sorted_sizes
        }

    # Analyze correlation with protocol
    if delay_factors["by_protocol"]:
        protocol_stats = {}
        for protocol, delays in delay_factors["by_protocol"].items():
            if delays:
                avg_delay = sum(delays) / len(delays)
                protocol_stats[protocol] = {
                    "avg_delay": avg_delay,
                    "min_delay": min(delays),
                    "max_delay": max(delays),
                    "count": len(delays),
                    "std_dev": np.std(delays) if len(delays) > 1 else 0,
                }

        # Sort by average delay to identify most problematic protocols
        sorted_protocols = sorted(
            protocol_stats.items(), key=lambda x: x[1]["avg_delay"], reverse=True
        )
        results["root_cause_analysis"]["protocol_correlation"] = {
            k: v for k, v in sorted_protocols
        }

    # Analyze correlation with source IP
    if delay_factors["by_source"]:
        source_stats = {}
        for src_ip, delays in delay_factors["by_source"].items():
            if delays:
                avg_delay = sum(delays) / len(delays)
                if len(delays) > 5:  # Only include sources with enough data points
                    source_stats[src_ip] = {
                        "avg_delay": avg_delay,
                        "min_delay": min(delays),
                        "max_delay": max(delays),
                        "count": len(delays),
                        "std_dev": np.std(delays) if len(delays) > 1 else 0,
                    }

        # Sort by average delay to identify most problematic source IPs
        sorted_sources = sorted(
            source_stats.items(), key=lambda x: x[1]["avg_delay"], reverse=True
        )
        results["root_cause_analysis"]["source_correlation"] = {
            k: v for k, v in sorted_sources[:10]  # Limit to top 10 for clarity
        }

    # Analyze correlation with destination IP
    if delay_factors["by_destination"]:
        dest_stats = {}
        for dst_ip, delays in delay_factors["by_destination"].items():
            if delays:
                avg_delay = sum(delays) / len(delays)
                if len(delays) > 5:  # Only include destinations with enough data points
                    dest_stats[dst_ip] = {
                        "avg_delay": avg_delay,
                        "min_delay": min(delays),
                        "max_delay": max(delays),
                        "count": len(delays),
                        "std_dev": np.std(delays) if len(delays) > 1 else 0,
                    }

        # Sort by average delay to identify most problematic destination IPs
        sorted_dests = sorted(
            dest_stats.items(), key=lambda x: x[1]["avg_delay"], reverse=True
        )
        results["root_cause_analysis"]["destination_correlation"] = {
            k: v for k, v in sorted_dests[:10]  # Limit to top 10 for clarity
        }

    # Analyze correlation with ports
    if delay_factors["by_port"]:
        port_stats = {}
        for port_info, delays in delay_factors["by_port"].items():
            if delays:
                avg_delay = sum(delays) / len(delays)
                if len(delays) > 5:  # Only include ports with enough data points
                    port_stats[port_info] = {
                        "avg_delay": avg_delay,
                        "min_delay": min(delays),
                        "max_delay": max(delays),
                        "count": len(delays),
                        "std_dev": np.std(delays) if len(delays) > 1 else 0,
                    }

        # Sort by average delay to identify most problematic ports
        sorted_ports = sorted(
            port_stats.items(), key=lambda x: x[1]["avg_delay"], reverse=True
        )
        results["root_cause_analysis"]["port_correlation"] = {
            k: v for k, v in sorted_ports[:10]  # Limit to top 10 for clarity
        }

    # Compute statistics for different types of events for the summary
    retransmission_count = 0
    bundling_count = 0
    processing_count = 0
    transmission_count = 0

    # We'll need to count these differently since we removed packet_delays
    for flow_id, packets in flows.items():
        for packet in packets:
            if packet["is_retransmission"]:
                retransmission_count += 1

    # Add summary statistics
    results["summary"] = {
        "total_packets": len(analyzed_packets),
        "total_flows": len(flows),
        "protocol_distribution": protocols,
        "retransmission_count": retransmission_count,
        "periodic_flow_count": len(results["patterns"]["periodic_transmissions"]),
        "bursty_flow_count": len(results["patterns"]["bursty_traffic"]),
        "anomaly_count": len(results["anomalies"]["irregular_delays"])
        + len(results["anomalies"]["jitter_spikes"]),
    }

    # Provide root cause summary based on analysis
    likely_causes = []

    # Check for problematic sizes
    if results["root_cause_analysis"]["size_correlation"]:
        top_size = next(iter(results["root_cause_analysis"]["size_correlation"]))
        top_size_stats = results["root_cause_analysis"]["size_correlation"][top_size]
        likely_causes.append(
            {
                "factor": f"Packet size ({top_size} bytes)",
                "avg_delay": top_size_stats["avg_delay"],
                "evidence": f"Packets in this size range experienced {top_size_stats['avg_delay']:.3f}s average delay across {top_size_stats['count']} instances",
            }
        )

    # Check for problematic protocols
    if results["root_cause_analysis"]["protocol_correlation"]:
        top_protocol = next(
            iter(results["root_cause_analysis"]["protocol_correlation"])
        )
        top_protocol_stats = results["root_cause_analysis"]["protocol_correlation"][
            top_protocol
        ]
        likely_causes.append(
            {
                "factor": f"Protocol ({top_protocol})",
                "avg_delay": top_protocol_stats["avg_delay"],
                "evidence": f"{top_protocol} traffic experienced {top_protocol_stats['avg_delay']:.3f}s average delay across {top_protocol_stats['count']} packets",
            }
        )

    # Check for problematic source/destination pairs
    if (
        results["root_cause_analysis"]["source_correlation"]
        and results["root_cause_analysis"]["destination_correlation"]
    ):
        top_source = next(iter(results["root_cause_analysis"]["source_correlation"]))
        top_source_stats = results["root_cause_analysis"]["source_correlation"][
            top_source
        ]

        top_dest = next(iter(results["root_cause_analysis"]["destination_correlation"]))
        top_dest_stats = results["root_cause_analysis"]["destination_correlation"][
            top_dest
        ]

        likely_causes.append(
            {
                "factor": "Source/Destination",
                "top_source": {
                    "ip": top_source,
                    "avg_delay": top_source_stats["avg_delay"],
                },
                "top_destination": {
                    "ip": top_dest,
                    "avg_delay": top_dest_stats["avg_delay"],
                },
                "evidence": f"Traffic from {top_source} ({top_source_stats['avg_delay']:.3f}s avg delay) and to {top_dest} ({top_dest_stats['avg_delay']:.3f}s avg delay) experienced the highest delays",
            }
        )

    # Add most likely root causes to results
    likely_causes.sort(
        key=lambda x: (
            x.get("avg_delay", 0) if isinstance(x.get("avg_delay"), (int, float)) else 0
        ),
        reverse=True,
    )
    results["root_cause_summary"] = likely_causes

    return results
