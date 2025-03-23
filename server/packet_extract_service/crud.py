from uuid import UUID
from pathlib import Path
from sqlalchemy.orm import Session
from scapy.all import PcapReader
from scapy.layers.inet import IP, TCP, UDP
from . import model
import time
from typing import List, Dict, Any, Generator
from datetime import datetime


def extract_and_store_packets_optimized(
    file_path: Path, pcapng_id: UUID, db: Session, batch_size: int = 10000
):
    """
    Extracts packets from a PCAPNG file and stores them in the database using optimized
    streaming processing without loading the entire file into memory.

    Args:
        file_path: Path to the PCAPNG file
        pcapng_id: UUID of the PCAPNG file in the database
        db: Database session
        batch_size: Number of packets to process in a single batch
    """
    start_time = time.time()
    total_processed = 0
    batch_count = 0

    # Process packets in batches using a generator
    for batch in stream_packets(file_path, pcapng_id, batch_size):
        batch_count += 1
        if batch:  # Only process non-empty batches
            create_packet_batch_optimized(db, batch)
            batch_size = len(batch)
            total_processed += batch_size
            print(
                f"Batch {batch_count} completed: {batch_size} packets, "
                f"Total: {total_processed}"
            )

    elapsed_time = time.time() - start_time
    print(
        f"Extracted and stored {total_processed} packets in {elapsed_time:.2f} seconds"
    )
    print(f"Processing rate: {total_processed / elapsed_time:.2f} packets/second")


def stream_packets(
    file_path: Path, pcapng_id: UUID, batch_size: int
) -> Generator[List[Dict[str, Any]], None, None]:
    """
    Stream packets from a PCAPNG file without loading everything into memory.

    Args:
        file_path: Path to the PCAPNG file
        pcapng_id: UUID of the PCAPNG file in the database
        batch_size: Number of packets per batch

    Yields:
        Batches of packet data dictionaries
    """
    current_batch = []
    packet_number = 1

    # Use PcapReader instead of rdpcap to avoid loading entire file
    with PcapReader(str(file_path)) as pcap_reader:
        for packet in pcap_reader:
            if not hasattr(packet, "time"):
                continue  # Skip packets without timestamps

            packet_data = extract_packet_data(packet, pcapng_id, packet_number)
            current_batch.append(packet_data)
            packet_number += 1

            # When batch is full, yield it
            if len(current_batch) >= batch_size:
                yield current_batch
                current_batch = []

        # Yield any remaining packets
        if current_batch:
            yield current_batch


def extract_packet_data(packet, pcapng_id: UUID, packet_number: int) -> Dict[str, Any]:
    """
    Extract relevant data from a packet.

    Args:
        packet: Scapy packet object
        pcapng_id: UUID of the PCAPNG file
        packet_number: Sequential number of the packet

    Returns:
        Dictionary containing packet data
    """
    # Determine protocol layer
    protocol = "Unknown"
    source_ip = "Unknown"
    destination_ip = "Unknown"

    if packet.haslayer(IP):
        protocol = "IP"
        source_ip = packet[IP].src
        destination_ip = packet[IP].dst

    if packet.haslayer(TCP):
        protocol = "TCP"
    elif packet.haslayer(UDP):
        protocol = "UDP"

    # Extract packet size safely
    packet_size = len(packet)

    # Convert Unix timestamp to datetime
    packet_timestamp = datetime.fromtimestamp(float(packet.time))

    # Create packet data dictionary
    return {
        "pcapng_id": pcapng_id,
        "packet_number": packet_number,
        "timestamp": packet_timestamp,
        "protocol": protocol,
        "source_ip": source_ip,
        "destination_ip": destination_ip,
        "packet_size": packet_size,
    }


def create_packet_batch_optimized(db: Session, packet_data_list: List[Dict[str, Any]]):
    """
    Creates multiple packet entries in the database in a single optimized transaction.

    Args:
        db: Database session
        packet_data_list: List of packet data dictionaries
    """
    # Use multi_params for faster insertion
    db.execute(
        model.Packet.__table__.insert(),
        [packet_data for packet_data in packet_data_list],
    )
    db.commit()
