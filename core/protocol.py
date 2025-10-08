"""
Binary protocol implementation for serial communication
"""

import struct
import time
import zlib
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional

class PacketType(IntEnum):
    """Packet type definitions"""
    DATA = 0x01
    ACK = 0x02
    HEARTBEAT = 0x03

@dataclass
class Packet:
    """Packet structure"""
    packet_type: PacketType
    sequence_id: int
    timestamp: float
    payload: bytes = b''
    
    @property
    def payload_size(self) -> int:
        return len(self.payload)

class ProtocolHandler:
    """Binary protocol handler for serial communication"""
    
    HEADER_FORMAT = '!BBHI'  # Magic, Type, Sequence, Timestamp
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT) + 4  # +4 for payload size
    FOOTER_SIZE = 4  # CRC32 checksum
    MAGIC_BYTE = 0xAA
    
    def __init__(self):
        self.sequence_counter = 0
    
    def create_packet(self, packet_type: PacketType, payload: bytes = b'') -> Packet:
        """Create a new packet with auto-incrementing sequence ID"""
        packet = Packet(
            packet_type=packet_type,
            sequence_id=self.sequence_counter,
            timestamp=time.time(),
            payload=payload
        )
        self.sequence_counter += 1
        return packet
    
    def serialize_packet(self, packet: Packet) -> bytes:
        """Serialize packet to bytes"""
        # Pack header
        header = struct.pack(
            self.HEADER_FORMAT,
            self.MAGIC_BYTE,
            packet.packet_type.value,
            packet.sequence_id,
            int(packet.timestamp * 1000)  # Convert to milliseconds
        )
        
        # Add payload size
        payload_size = struct.pack('!I', packet.payload_size)
        
        # Combine header, payload size, and payload
        data = header + payload_size + packet.payload
        
        # Calculate and append checksum
        checksum = zlib.crc32(data) & 0xffffffff
        data += struct.pack('!I', checksum)
        
        return data
    
    def deserialize_packet(self, data: bytes) -> Optional[Packet]:
        """Deserialize bytes to packet"""
        if len(data) < self.HEADER_SIZE + self.FOOTER_SIZE:
            return None
        
        try:
            # Unpack header
            magic, ptype, seq_id, timestamp_ms = struct.unpack(
                self.HEADER_FORMAT, 
                data[:struct.calcsize(self.HEADER_FORMAT)]
            )
            
            if magic != self.MAGIC_BYTE:
                return None
            
            # Unpack payload size
            payload_size = struct.unpack('!I', data[struct.calcsize(self.HEADER_FORMAT):self.HEADER_SIZE])[0]
            
            # Extract payload
            payload_start = self.HEADER_SIZE
            payload_end = payload_start + payload_size
            
            if len(data) < payload_end + self.FOOTER_SIZE:
                return None
            
            payload = data[payload_start:payload_end]
            
            # Verify checksum
            checksum_data = data[:payload_end]
            expected_checksum = struct.unpack('!I', data[payload_end:payload_end + self.FOOTER_SIZE])[0]
            actual_checksum = zlib.crc32(checksum_data) & 0xffffffff
            
            if expected_checksum != actual_checksum:
                return None
            
            # Create packet
            packet = Packet(
                packet_type=PacketType(ptype),
                sequence_id=seq_id,
                timestamp=timestamp_ms / 1000.0,  # Convert back to seconds
                payload=payload
            )
            
            return packet
            
        except (struct.error, ValueError):
            return None
    
    def create_data_packet(self, data: bytes) -> Packet:
        """Create a DATA packet"""
        return self.create_packet(PacketType.DATA, data)
    
    def create_ack_packet(self, sequence_id: int) -> Packet:
        """Create an ACK packet for given sequence ID"""
        ack_payload = struct.pack('!I', sequence_id)
        return self.create_packet(PacketType.ACK, ack_payload)
    
    def create_heartbeat_packet(self) -> Packet:
        """Create a HEARTBEAT packet"""
        return self.create_packet(PacketType.HEARTBEAT)
    
    def get_acked_sequence(self, ack_packet: Packet) -> Optional[int]:
        """Extract sequence ID from ACK packet payload"""
        if ack_packet.packet_type != PacketType.ACK or len(ack_packet.payload) < 4:
            return None
        
        try:
            return struct.unpack('!I', ack_packet.payload[:4])[0]
        except struct.error:
            return None
