from packet_extract_service import schema as packet_schema, crud as packet_crud
from uuid import UUID
from pathlib import Path
from sqlalchemy.orm import Session
from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP, UDP
from . import model, schema

def extract_and_store_packets(file_path: Path, pcapng_id: UUID, db: Session):

    """Extracts packets from a PCAPNG file and stores them in the database."""
    packets = rdpcap(str(file_path))  # Read packets using Scapy

    for idx, packet in enumerate(packets, start=1):
        if not hasattr(packet, "time"):
            continue  # Skip packets without timestamps

        # Determine protocol layer
        if packet.haslayer(IP):
            protocol = "IP"
        elif packet.haslayer(TCP):
            protocol = "TCP"
        elif packet.haslayer(UDP):
            protocol = "UDP"
        else:
            protocol = "Unknown"

        # Extract source & destination IPs (only for IP packets)
        source_ip = packet[IP].src if packet.haslayer(IP) else "Unknown"
        destination_ip = packet[IP].dst if packet.haslayer(IP) else "Unknown"

        # Extract packet size safely
        packet_size = len(packet)

        packet_data = packet_schema.PacketCreate(
            pcapng_id=pcapng_id,
            packet_number=idx,
            timestamp=packet.time,
            protocol=protocol,
            source_ip=source_ip,
            destination_ip=destination_ip,
            packet_size=packet_size
        )
        
        packet_crud.create_packet(db, packet_data)  # Store in DB

    print(f"Extracted and stored {len(packets)} packets.")

def create_packet(db: Session, packet_data: schema.PacketCreate):
    """Creates a packet entry in the database."""
    new_packet = model.Packet(
        pcapng_id=packet_data.pcapng_id,
        packet_number=packet_data.packet_number,
        timestamp=packet_data.timestamp,
        protocol=packet_data.protocol,
        source_ip=packet_data.source_ip,
        destination_ip=packet_data.destination_ip,
        packet_size=packet_data.packet_size
    )
    db.add(new_packet)
    db.commit()
    db.refresh(new_packet)
    return new_packet