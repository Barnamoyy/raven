from uuid import UUID
from pathlib import Path
from sqlalchemy.orm import Session
from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP, UDP
from . import model, schema
import time
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


def extract_and_store_packets(file_path: Path, pcapng_id: UUID, db: Session, batch_size: int = 1000):
    """
    Extracts packets from a PCAPNG file and stores them in the database using batch processing.
    
    Args:
        file_path: Path to the PCAPNG file
        pcapng_id: UUID of the PCAPNG file in the database
        db: Database session
        batch_size: Number of packets to process in a single batch
    """
    start_time = time.time()
    print(f"Starting packet extraction from {file_path}")
    
    # Read packets using Scapy - this loads them all into memory
    packets = rdpcap(str(file_path))
    total_packets = len(packets)
    print(f"Loaded {total_packets} packets from file")
    
    # Process packets in batches
    batch_count = 0
    processed_count = 0
    current_batch = []
    
    for idx, packet in enumerate(packets, start=1):
        if not hasattr(packet, "time"):
            continue  # Skip packets without timestamps
        
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
        packet_data = {
            "pcapng_id": pcapng_id,
            "packet_number": idx,
            "timestamp": packet_timestamp,  # Now using datetime object
            "protocol": protocol,
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "packet_size": packet_size
        }
        
        current_batch.append(packet_data)
        processed_count += 1
        
        # When batch is full or we've reached the end, commit to database
        if len(current_batch) >= batch_size or idx == total_packets:
            batch_count += 1
            create_packet_batch(db, current_batch)
            print(f"Batch {batch_count} completed: {len(current_batch)} packets")
            current_batch = []
    
    elapsed_time = time.time() - start_time
    print(f"Extracted and stored {processed_count} packets in {elapsed_time:.2f} seconds")
    print(f"Processing rate: {processed_count / elapsed_time:.2f} packets/second")


def create_packet_batch(db: Session, packet_data_list: List[Dict[str, Any]]):
    """
    Creates multiple packet entries in the database in a single transaction.
    
    Args:
        db: Database session
        packet_data_list: List of packet data dictionaries
    """
    # Create all packet objects
    new_packets = [model.Packet(**packet_data) for packet_data in packet_data_list]
    
    # Add all at once
    db.bulk_save_objects(new_packets)
    db.commit()


def parallel_extract_and_store(file_path: Path, pcapng_id: UUID, db: Session, 
                              batch_size: int = 1000, num_workers: int = 4):
    """
    Extract and store packets using parallel processing for very large files.
    
    Args:
        file_path: Path to the PCAPNG file
        pcapng_id: UUID of the PCAPNG file in the database
        db: Database session
        batch_size: Number of packets per batch
        num_workers: Number of parallel workers
    """
    start_time = time.time()
    print(f"Starting parallel packet extraction from {file_path}")
    
    # Read packets using Scapy
    packets = rdpcap(str(file_path))
    total_packets = len(packets)
    print(f"Loaded {total_packets} packets from file")
    
    # Split packets into chunks for parallel processing
    packet_chunks = []
    chunk_size = max(1, total_packets // num_workers)
    for i in range(0, total_packets, chunk_size):
        end_idx = min(i + chunk_size, total_packets)
        packet_chunks.append((i, packets[i:end_idx]))
    
    # Process chunks in parallel
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for chunk_idx, chunk in packet_chunks:
            futures.append(
                executor.submit(
                    process_packet_chunk, 
                    chunk, 
                    chunk_idx + 1,  # Starting packet number 
                    pcapng_id, 
                    batch_size
                )
            )
        
        # Wait for all tasks to complete
        processed_packets = 0
        for future in as_completed(futures):
            try:
                batch_packets = future.result()
                # Create a new database session for each batch to avoid concurrency issues
                with Session(bind=db.get_bind()) as session:
                    create_packet_batch(session, batch_packets)
                processed_packets += len(batch_packets)
                print(f"Processed batch: {len(batch_packets)} packets")
            except Exception as e:
                print(f"Chunk processing error: {str(e)}")
    
    elapsed_time = time.time() - start_time
    print(f"Parallel processing complete: {processed_packets} packets in {elapsed_time:.2f} seconds")
    print(f"Processing rate: {processed_packets / elapsed_time:.2f} packets/second")


def process_packet_chunk(packets, start_idx, pcapng_id, batch_size):
    """Process a chunk of packets and return batch data for database insertion."""
    processed_packets = []
    
    for idx, packet in enumerate(packets, start=start_idx):
        if not hasattr(packet, "time"):
            continue
        
        # Determine protocol and IPs
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
        
        # Convert Unix timestamp to datetime
        packet_timestamp = datetime.fromtimestamp(float(packet.time))
        
        packet_data = {
            "pcapng_id": pcapng_id,
            "packet_number": idx,
            "timestamp": packet_timestamp,  # Now using datetime object
            "protocol": protocol,
            "source_ip": source_ip,
            "destination_ip": destination_ip,
            "packet_size": len(packet)
        }
        
        processed_packets.append(packet_data)
    
    return processed_packets