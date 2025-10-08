"""
Serial communication handler
"""

import serial
import threading
import time
import logging
from typing import Optional, Callable, List
from PyQt6.QtCore import QObject, pyqtSignal
from core.protocol import ProtocolHandler, Packet

class SerialHandler(QObject):
    """Serial communication handler with thread-safe operations"""
    
    # Signals for Qt integration
    connection_status_changed = pyqtSignal(bool)
    packet_received = pyqtSignal(object)  # Packet object
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.serial_connection: Optional[serial.Serial] = None
        self.protocol = ProtocolHandler()
        self.is_connected = False
        self.receive_thread: Optional[threading.Thread] = None
        self.stop_receiving = threading.Event()
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.bytes_sent = 0
        self.bytes_received = 0
        self.packets_sent = 0
        self.packets_received = 0
        
    def connect(self, port: str, baudrate: int, timeout: float = 1.0, 
                bytesize: int = 8, parity: str = 'N', stopbits: int = 1) -> bool:
        """Connect to serial port"""
        try:
            if self.is_connected:
                self.disconnect()
            
            self.serial_connection = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                bytesize=bytesize,
                parity=parity,
                stopbits=stopbits
            )
            
            self.is_connected = True
            self.connection_status_changed.emit(True)
            
            # Start receive thread
            self.stop_receiving.clear()
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            self.logger.info(f"Connected to {port} at {baudrate} baud")
            return True
            
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to {port}: {e}")
            self.error_occurred.emit(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from serial port"""
        if not self.is_connected:
            return
        
        # Stop receive thread
        self.stop_receiving.set()
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2.0)
        
        # Close serial connection
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except Exception as e:
                self.logger.error(f"Error closing serial connection: {e}")
        
        self.serial_connection = None
        self.is_connected = False
        self.connection_status_changed.emit(False)
        self.logger.info("Disconnected from serial port")
    
    def send_packet(self, packet: Packet) -> bool:
        """Send a packet over serial connection"""
        if not self.is_connected or not self.serial_connection:
            return False
        
        try:
            data = self.protocol.serialize_packet(packet)
            bytes_written = self.serial_connection.write(data)
            self.serial_connection.flush()
            
            self.bytes_sent += bytes_written
            self.packets_sent += 1
            
            self.logger.debug(f"Sent packet: type={packet.packet_type}, seq={packet.sequence_id}, size={len(data)}")
            return True
            
        except serial.SerialException as e:
            self.logger.error(f"Failed to send packet: {e}")
            self.error_occurred.emit(f"Send failed: {e}")
            return False
    
    def _receive_loop(self):
        """Receive loop running in separate thread"""
        buffer = bytearray()
        
        while not self.stop_receiving.is_set() and self.is_connected:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    # Read available data
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    buffer.extend(data)
                    self.bytes_received += len(data)
                    
                    # Try to parse packets from buffer
                    self._parse_buffer(buffer)
                
                time.sleep(0.001)  # Small delay to prevent busy waiting
                
            except serial.SerialException as e:
                self.logger.error(f"Receive error: {e}")
                self.error_occurred.emit(f"Receive error: {e}")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in receive loop: {e}")
                break
    
    def _parse_buffer(self, buffer: bytearray):
        """Parse packets from receive buffer"""
        while len(buffer) >= self.protocol.HEADER_SIZE + self.protocol.FOOTER_SIZE:
            # Look for magic byte
            magic_index = buffer.find(self.protocol.MAGIC_BYTE)
            if magic_index == -1:
                # No magic byte found, clear buffer
                buffer.clear()
                break
            
            # Remove data before magic byte
            if magic_index > 0:
                del buffer[:magic_index]
            
            # Check if we have enough data for header
            if len(buffer) < self.protocol.HEADER_SIZE:
                break
            
            # Try to determine packet size
            try:
                import struct
                payload_size = struct.unpack('!I', 
                    buffer[struct.calcsize(self.protocol.HEADER_FORMAT):self.protocol.HEADER_SIZE])[0]
                
                total_packet_size = self.protocol.HEADER_SIZE + payload_size + self.protocol.FOOTER_SIZE
                
                if len(buffer) < total_packet_size:
                    # Not enough data for complete packet
                    break
                
                # Try to parse packet
                packet_data = bytes(buffer[:total_packet_size])
                packet = self.protocol.deserialize_packet(packet_data)
                
                if packet:
                    # Valid packet received
                    self.packets_received += 1
                    self.packet_received.emit(packet)
                    self.logger.debug(f"Received packet: type={packet.packet_type}, seq={packet.sequence_id}")
                    
                    # Remove parsed packet from buffer
                    del buffer[:total_packet_size]
                else:
                    # Invalid packet, remove magic byte and continue
                    del buffer[0]
                    
            except (struct.error, IndexError):
                # Error parsing, remove first byte and continue
                del buffer[0]
    
    def get_statistics(self) -> dict:
        """Get communication statistics"""
        return {
            'bytes_sent': self.bytes_sent,
            'bytes_received': self.bytes_received,
            'packets_sent': self.packets_sent,
            'packets_received': self.packets_received,
            'is_connected': self.is_connected
        }
    
    def reset_statistics(self):
        """Reset communication statistics"""
        self.bytes_sent = 0
        self.bytes_received = 0
        self.packets_sent = 0
        self.packets_received = 0
