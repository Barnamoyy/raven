import numpy as np
import pandas as pd
from collections import defaultdict
from sklearn.cluster import DBSCAN
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Union


class DelayAnalyzer:
    def __init__(self):
        self.df = None
        self.delay_categories = {
            "bundling_delay": [],
            "broker_processing_delay": [],
            "retransmission_delay": [],
            "network_congestion": [],
            "jitter": [],
        }
        self.mqtt_ports = set([1883, 8883])  # Using set for faster lookups

    def process_packets(self, packets: List[Any]) -> bool:
        """Process packet capture and extract relevant information"""
        # Pre-allocate list with estimated size for better memory usage
        packet_data = []
        packet_data_append = packet_data.append  # Local reference for faster access

        for i, packet in enumerate(packets):
            pkt_info = self._extract_packet_info(packet, i)
            if pkt_info:
                packet_data_append(pkt_info)

        # Create DataFrame from packet data
        if not packet_data:
            return False

        self.df = pd.DataFrame(packet_data)

        # Optimize data types to reduce memory usage
        self._optimize_dtypes()

        # Sort by timestamp and calculate delays in one pass
        self.df.sort_values("timestamp", inplace=True)
        self.df["delay"] = self.df["timestamp"].diff().fillna(0)

        return True

    def _optimize_dtypes(self):
        """Optimize DataFrame data types to reduce memory usage"""
        # Numeric columns that can be downcasted
        int_cols = [
            "packet_id",
            "src_port",
            "dst_port",
            "protocol",
            "seq_num",
            "ack_num",
            "ip_length",
            "total_length",
        ]
        for col in int_cols:
            if col in self.df and self.df[col].notna().all():
                # Use smallest possible integer type
                self.df[col] = pd.to_numeric(self.df[col], downcast="integer")

        # Boolean columns
        if "is_mqtt" in self.df:
            self.df["is_mqtt"] = self.df["is_mqtt"].astype("bool")

    def _extract_packet_info(
        self, packet: Any, packet_id: int
    ) -> Optional[Dict[str, Any]]:
        """Extract relevant information from a packet"""
        if packet.haslayer("IP"):
            timestamp = float(packet.time)

            # Get IP layer information
            src_ip = packet["IP"].src
            dst_ip = packet["IP"].dst
            protocol = packet["IP"].proto

            # Get transport layer info (TCP/UDP)
            src_port = None
            dst_port = None
            tcp_flags = None
            seq_num = None
            ack_num = None

            if packet.haslayer("TCP"):
                src_port = packet["TCP"].sport
                dst_port = packet["TCP"].dport
                tcp_flags = packet["TCP"].flags
                seq_num = packet["TCP"].seq
                ack_num = packet["TCP"].ack

            elif packet.haslayer("UDP"):
                src_port = packet["UDP"].sport
                dst_port = packet["UDP"].dport

            # Determine if this is likely MQTT traffic - use set membership test for speed
            is_mqtt = src_port in self.mqtt_ports or dst_port in self.mqtt_ports

            # Packet size information
            ip_len = packet["IP"].len
            total_len = len(packet)

            return {
                "packet_id": packet_id,
                "timestamp": timestamp,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "src_port": src_port,
                "dst_port": dst_port,
                "protocol": protocol,
                "tcp_flags": tcp_flags,
                "seq_num": seq_num,
                "ack_num": ack_num,
                "ip_length": ip_len,
                "total_length": total_len,
                "is_mqtt": is_mqtt,
            }
        return None

    def analyze_delays(self) -> bool:
        """Analyze and categorize different types of delays"""
        if self.df is None or self.df.empty:
            return False

        # Create flow column using vectorized operation instead of apply
        self.df["flow"] = (
            self.df["src_ip"].astype(str)
            + ":"
            + self.df["src_port"].astype(str)
            + "->"
            + self.df["dst_ip"].astype(str)
            + ":"
            + self.df["dst_port"].astype(str)
        )

        # Analyze for each major delay type - run in optimal order
        self._identify_retransmissions()  # Quick operation first
        self._identify_jitter()  # Also relatively fast
        self._identify_bundling_delays()  # More complex operations later
        self._identify_network_congestion()
        self._identify_broker_processing_delays()  # Most complex operation last

        return True

    def _identify_bundling_delays(self):
        """Identify bundling delays - small packets from same src in close succession"""
        # Skip if we don't have enough data
        if len(self.df) < 5:
            return

        # Group by source IP
        src_ip_groups = self.df.groupby("src_ip")

        # Calculate median packet size per source once
        src_medians = src_ip_groups["ip_length"].median()

        for src_ip, group in src_ip_groups:
            if len(group) < 3:  # Need at least a few packets to identify bundling
                continue

            # Sort by timestamp - use local indices for better performance
            group = group.sort_values("timestamp")

            # Calculate inter-packet time once
            group_timestamps = group["timestamp"].values
            inter_packet_times = np.diff(group_timestamps, prepend=group_timestamps[0])
            group = group.assign(inter_packet_time=inter_packet_times)

            # Identify small packets using vectorized comparison instead of iteration
            median_size = src_medians[src_ip]
            small_packet_mask = group["ip_length"] < (median_size * 0.7)
            small_packets = group[small_packet_mask]

            if len(small_packets) < 3:
                continue

            # Use clustering to identify bundling patterns
            X = small_packets[["timestamp", "inter_packet_time"]].values

            # Normalize only if necessary to save computation
            if np.std(X[:, 1]) > 0:
                X_scaled = np.column_stack([X[:, 0], X[:, 1] / np.std(X[:, 1]) * 10])
            else:
                X_scaled = X

            # Use DBSCAN with optimized parameters - higher eps for fewer clusters
            clustering = DBSCAN(eps=0.5, min_samples=2, algorithm="ball_tree").fit(
                X_scaled
            )
            small_packets["cluster"] = clustering.labels_

            # Process only non-noise clusters (more efficient)
            valid_clusters = small_packets[small_packets["cluster"] >= 0]
            if valid_clusters.empty:
                continue

            # Group by cluster and process each cluster
            for cluster_id, cluster_packets in valid_clusters.groupby("cluster"):
                if len(cluster_packets) >= 3:
                    # Use numpy for faster min/max calculation
                    timestamps = cluster_packets["timestamp"].values
                    start_time = timestamps.min()
                    end_time = timestamps.max()
                    bundle_time = end_time - start_time

                    # Record bundling delay event if significant
                    if bundle_time > 0.01:  # Minimum threshold to consider it bundling
                        self.delay_categories["bundling_delay"].append(
                            {
                                "src_ip": src_ip,
                                "start_time": start_time,
                                "end_time": end_time,
                                "duration": bundle_time,
                                "packet_count": len(cluster_packets),
                                "avg_size": cluster_packets["ip_length"].mean(),
                            }
                        )

    def _identify_broker_processing_delays(self):
        """Identify broker processing delays in MQTT flows"""
        # Fast return if no MQTT data
        if "is_mqtt" not in self.df.columns or not self.df["is_mqtt"].any():
            return

        # First, identify potential MQTT brokers more efficiently
        mqtt_ports_set = self.mqtt_ports  # Local reference for speed

        # Create masks for MQTT packets and potential brokers
        mqtt_mask = self.df["is_mqtt"]
        mqtt_packets = self.df[mqtt_mask]

        if len(mqtt_packets) < 2:
            return

        # Find potential brokers - use vectorized operations
        dst_brokers = set(
            mqtt_packets[mqtt_packets["dst_port"].isin(mqtt_ports_set)]["dst_ip"]
        )
        src_brokers = set(
            mqtt_packets[mqtt_packets["src_port"].isin(mqtt_ports_set)]["src_ip"]
        )
        potential_brokers = dst_brokers.union(src_brokers)

        for broker_ip in potential_brokers:
            # Create masks instead of filtering repeatedly
            to_broker_mask = self.df["dst_ip"] == broker_ip
            from_broker_mask = self.df["src_ip"] == broker_ip

            to_broker = self.df[to_broker_mask]
            from_broker = self.df[from_broker_mask]

            if len(to_broker) == 0 or len(from_broker) == 0:
                continue

            # Sort for faster processing
            to_broker_sorted = to_broker.sort_values("timestamp")
            from_broker_sorted = from_broker.sort_values("timestamp")

            # Process only a sample of packets for large datasets
            sample_size = min(100, len(to_broker_sorted))
            if len(to_broker_sorted) > sample_size:
                # Take samples distributed throughout time range
                indices = np.linspace(
                    0, len(to_broker_sorted) - 1, sample_size, dtype=int
                )
                to_broker_sample = to_broker_sorted.iloc[indices]
            else:
                to_broker_sample = to_broker_sorted

            # For each packet to broker, look for subsequent packets from broker
            for _, in_pkt in to_broker_sample.iterrows():
                in_time = in_pkt["timestamp"]

                # Find packets from broker after this time - use boolean indexing
                subsequent_mask = from_broker_sorted["timestamp"] > in_time
                subsequent = from_broker_sorted[subsequent_mask]

                if len(subsequent) == 0:
                    continue

                # Find first response and calculate delay
                first_response = subsequent.iloc[0]
                first_response_time = first_response["timestamp"]
                processing_delay = first_response_time - in_time

                # Skip if delay is too small
                if processing_delay <= 0.05:  # Less than 50ms delay
                    continue

                # Find window of responses more efficiently
                window_end = first_response_time + 0.5  # 500ms window
                responses_window_mask = (
                    subsequent["timestamp"] >= first_response_time
                ) & (subsequent["timestamp"] <= window_end)
                responses_window = subsequent[responses_window_mask]

                if len(responses_window) >= 2:
                    # Count unique destinations more efficiently
                    unique_destinations = len(set(responses_window["dst_ip"]))

                    if (
                        unique_destinations >= 2
                    ):  # Multiple destinations = distribution pattern
                        self.delay_categories["broker_processing_delay"].append(
                            {
                                "broker_ip": broker_ip,
                                "in_time": in_time,
                                "out_time": first_response_time,
                                "delay": processing_delay,
                                "response_count": len(responses_window),
                                "destinations": unique_destinations,
                            }
                        )

    def _identify_retransmissions(self):
        """Identify TCP retransmissions"""
        # Fast early return if no TCP data
        if "seq_num" not in self.df.columns or self.df["seq_num"].isna().all():
            return

        # Drop NA rows once
        tcp_data = self.df.dropna(subset=["seq_num"])
        if len(tcp_data) < 2:
            return

        # Group by flow and find duplicates more efficiently
        for flow, group in tcp_data.groupby("flow"):
            if len(group) < 2:
                continue

            # Sort by timestamp
            group = group.sort_values("timestamp")

            # Find duplicate sequence numbers efficiently
            # Create a Series indicating if a seq_num is the same as the next one
            seq_nums = group["seq_num"].values
            timestamps = group["timestamp"].values

            # Find where sequence numbers repeat
            # This is faster than shift and compare
            seq_dups = np.where(seq_nums[:-1] == seq_nums[1:])[0]

            for idx in seq_dups:
                retrans_delay = timestamps[idx + 1] - timestamps[idx]

                self.delay_categories["retransmission_delay"].append(
                    {
                        "flow": flow,
                        "orig_time": timestamps[idx],
                        "retrans_time": timestamps[idx + 1],
                        "delay": retrans_delay,
                        "seq_num": seq_nums[idx],
                    }
                )

    def _identify_network_congestion(self):
        """Identify patterns indicative of network congestion"""
        if len(self.df) < 10:
            return

        # Calculate moving average and standard deviation of delays more efficiently
        window_size = min(15, len(self.df) // 5 + 1)  # Adaptive window size

        # Use numpy for rolling calculations instead of pandas for speed
        delays = self.df["delay"].values

        # Calculate rolling stats using numpy - much faster than pandas rolling
        ma_values = np.zeros_like(delays)
        std_values = np.zeros_like(delays)

        for i in range(len(delays)):
            start_idx = max(0, i - window_size + 1)
            window = delays[start_idx : i + 1]
            ma_values[i] = np.mean(window) if len(window) > 0 else 0
            std_values[i] = np.std(window) if len(window) > 1 else 0

        # Add calculated values to DataFrame
        self.df["delay_ma"] = ma_values
        self.df["delay_std"] = std_values

        # Find intervals with high delay variance
        std_mean = np.mean(std_values[std_values > 0])
        high_variance_mask = (self.df["delay_std"] > std_mean * 2) & (
            self.df["delay_std"] > 0
        )
        high_variance = self.df[high_variance_mask]

        if len(high_variance) < 2:
            return

        # Cluster these points in time to find congestion events
        X = high_variance[["timestamp"]].values

        # Use DBSCAN with optimized parameters for temporal clustering
        clustering = DBSCAN(eps=0.5, min_samples=2, algorithm="ball_tree").fit(X)
        high_variance["cluster"] = clustering.labels_

        # Process only valid clusters
        valid_clusters = high_variance[high_variance["cluster"] >= 0]
        if valid_clusters.empty:
            return

        # Process each cluster efficiently
        for cluster_id, cluster_data in valid_clusters.groupby("cluster"):
            # Use numpy for faster min/max calculation
            cluster_times = cluster_data["timestamp"].values
            start_time = np.min(cluster_times) - 0.1
            end_time = np.max(cluster_times) + 0.1

            # Get all packets in this time range using boolean indexing
            event_mask = (self.df["timestamp"] >= start_time) & (
                self.df["timestamp"] <= end_time
            )
            event_packets = self.df[event_mask]

            # Check if multiple flows affected - use set for unique count
            flows_affected = len(set(event_packets["flow"]))

            if flows_affected >= 2:
                # Calculate metrics efficiently using numpy
                event_delays = event_packets["delay"].values
                avg_delay = np.mean(event_delays)
                max_delay = np.max(event_delays)
                overall_mean = np.mean(delays)
                delay_increase = avg_delay / overall_mean if overall_mean > 0 else 0

                if delay_increase > 1.5:  # At least 50% increase in delays
                    self.delay_categories["network_congestion"].append(
                        {
                            "start_time": start_time,
                            "end_time": end_time,
                            "duration": end_time - start_time,
                            "flows_affected": flows_affected,
                            "avg_delay": avg_delay,
                            "max_delay": max_delay,
                            "delay_increase_factor": delay_increase,
                        }
                    )

    def _identify_jitter(self):
        """Identify jitter (variation in delay) in each flow"""
        # Skip small datasets
        if len(self.df) < 5:
            return

        # For each flow, calculate jitter statistics
        for flow, indices in self.df.groupby("flow").indices.items():
            if len(indices) < 5:  # Need enough packets to calculate meaningful jitter
                continue

            # Get delays for this flow using optimized indexing
            flow_data = self.df.iloc[indices]

            # Sort by timestamp and extract delays as numpy array - much faster
            sorted_indices = np.argsort(flow_data["timestamp"].values)
            delays = flow_data["delay"].values[sorted_indices]
            timestamps = flow_data["timestamp"].values[sorted_indices]

            # Calculate delay differences using numpy - faster than pandas diff
            delay_diffs = np.abs(np.diff(delays))

            if len(delay_diffs) < 3:
                continue

            # Calculate statistics using numpy
            mean_jitter = np.mean(delay_diffs)
            max_jitter = np.max(delay_diffs)

            # Record significant jitter events
            if mean_jitter > 0.01:  # At least 10ms average jitter
                self.delay_categories["jitter"].append(
                    {
                        "flow": flow,
                        "mean_jitter": mean_jitter,
                        "max_jitter": max_jitter,
                        "start_time": np.min(timestamps),
                        "end_time": np.max(timestamps),
                        "packet_count": len(indices),
                    }
                )

    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of delay analysis"""
        if self.df is None or self.df.empty:
            return {}

        # Use numpy for faster statistical calculations
        timestamps = self.df["timestamp"].values
        delays = self.df["delay"].values

        # Count MQTT traffic efficiently
        mqtt_count = (
            int(self.df["is_mqtt"].sum()) if "is_mqtt" in self.df.columns else 0
        )

        summary = {
            "packet_count": len(self.df),
            "unique_flows": (
                len(set(self.df["flow"])) if "flow" in self.df.columns else 0
            ),
            "time_span": {
                "start": np.min(timestamps),
                "end": np.max(timestamps),
                "duration": np.max(timestamps) - np.min(timestamps),
            },
            "delays": {
                "average": np.mean(delays),
                "median": np.median(delays),
                "max": np.max(delays),
                "std_dev": np.std(delays),
            },
            "delay_categories": {
                "bundling_delays": len(self.delay_categories["bundling_delay"]),
                "broker_processing_delays": len(
                    self.delay_categories["broker_processing_delay"]
                ),
                "retransmission_delays": len(
                    self.delay_categories["retransmission_delay"]
                ),
                "network_congestion_events": len(
                    self.delay_categories["network_congestion"]
                ),
                "jitter_flows": len(self.delay_categories["jitter"]),
            },
            "mqtt_traffic": {
                "packets": mqtt_count,
                "percentage": (
                    (mqtt_count / len(self.df) * 100) if len(self.df) > 0 else 0
                ),
            },
            "protocols": (
                self.df["protocol"].value_counts().to_dict()
                if "protocol" in self.df.columns
                else {}
            ),
        }

        return summary


def analyze_packet_delays(file_path, packets):
    """Main function to analyze packet delays in MQTT-based IoT workflows"""
    try:
        # Initialize analyzer
        analyzer = DelayAnalyzer()

        # Process packets
        start_time = None  # You could add timing code here if needed
        if not analyzer.process_packets(packets):
            return {"error": "Failed to process packets or no valid packets found"}

        # Analyze delays
        analyzer.analyze_delays()

        # Generate summary
        summary = analyzer.generate_summary()

        # Extract individual packet delays and categorize them
        packet_delays = []
        if analyzer.df is not None and not analyzer.df.empty:
            # Create lookup dictionaries for each delay category
            bundling_packets = set()
            retransmission_packets = set()
            congestion_packets = set()
            jitter_packets = set()
            broker_packets = set()

            # Map packets to categories
            # 1. Bundling delays
            for event in analyzer.delay_categories["bundling_delay"]:
                start_time = event["start_time"]
                end_time = event["end_time"]
                src_ip = event["src_ip"]
                # Find packets in this bundling event
                bundled_packets = analyzer.df[
                    (analyzer.df["timestamp"] >= start_time)
                    & (analyzer.df["timestamp"] <= end_time)
                    & (analyzer.df["src_ip"] == src_ip)
                ]["packet_id"].tolist()
                bundling_packets.update(bundled_packets)

            # 2. Retransmission delays
            for event in analyzer.delay_categories["retransmission_delay"]:
                orig_time = event["orig_time"]
                retrans_time = event["retrans_time"]
                flow = event["flow"]
                seq_num = event["seq_num"]
                # Find packets in this retransmission
                retrans_packets = analyzer.df[
                    (analyzer.df["timestamp"].between(orig_time, retrans_time))
                    & (analyzer.df["flow"] == flow)
                    & (analyzer.df["seq_num"] == seq_num)
                ]["packet_id"].tolist()
                retransmission_packets.update(retrans_packets)

            # 3. Network congestion
            for event in analyzer.delay_categories["network_congestion"]:
                start_time = event["start_time"]
                end_time = event["end_time"]
                # Find packets affected by congestion
                congestion_affected = analyzer.df[
                    (analyzer.df["timestamp"] >= start_time)
                    & (analyzer.df["timestamp"] <= end_time)
                ]["packet_id"].tolist()
                congestion_packets.update(congestion_affected)

            # 4. Jitter
            for event in analyzer.delay_categories["jitter"]:
                flow = event["flow"]
                start_time = event["start_time"]
                end_time = event["end_time"]
                # Find packets in this flow with jitter
                jitter_affected = analyzer.df[
                    (analyzer.df["flow"] == flow)
                    & (analyzer.df["timestamp"] >= start_time)
                    & (analyzer.df["timestamp"] <= end_time)
                ]["packet_id"].tolist()
                jitter_packets.update(jitter_affected)

            # 5. Broker processing
            for event in analyzer.delay_categories["broker_processing_delay"]:
                broker_ip = event["broker_ip"]
                in_time = event["in_time"]
                out_time = event["out_time"]
                # Find packets in this broker processing event
                broker_affected = analyzer.df[
                    (
                        (analyzer.df["src_ip"] == broker_ip)
                        | (analyzer.df["dst_ip"] == broker_ip)
                    )
                    & (analyzer.df["timestamp"] >= in_time)
                    & (analyzer.df["timestamp"] <= out_time)
                ]["packet_id"].tolist()
                broker_packets.update(broker_affected)

        # Combine results
        results = {
            "summary": summary,
        }

        return results

    except Exception as e:
        return {"error": f"Error analyzing packet delays: {str(e)}"}
