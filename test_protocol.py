#!/usr/bin/env python3
"""
Test script to verify protocol packet creation and serialization
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.protocol import ProtocolHandler, PacketType

def test_protocol():
    """Test protocol packet creation and serialization"""
    print("Testing Protocol Handler...")
    
    handler = ProtocolHandler()
    
    # Test 1: Create data packet
    print("\n1. Creating DATA packet...")
    test_data = b'X' * 64  # 64 bytes of test data
    packet = handler.create_data_packet(test_data)
    
    print(f"   Packet type: {packet.packet_type}")
    print(f"   Sequence ID: {packet.sequence_id}")
    print(f"   Timestamp: {packet.timestamp}")
    print(f"   Payload size: {packet.payload_size}")
    print(f"   Payload: {packet.payload[:10]}... (showing first 10 bytes)")
    
    # Test 2: Serialize packet
    print("\n2. Serializing packet...")
    serialized = handler.serialize_packet(packet)
    print(f"   Serialized size: {len(serialized)} bytes")
    print(f"   Serialized data (hex): {serialized[:20].hex()}... (showing first 20 bytes)")
    
    # Test 3: Deserialize packet
    print("\n3. Deserializing packet...")
    deserialized = handler.deserialize_packet(serialized)
    
    if deserialized:
        print(f"   SUCCESS - Packet deserialized correctly")
        print(f"   Type: {deserialized.packet_type}")
        print(f"   Sequence: {deserialized.sequence_id}")
        print(f"   Payload size: {deserialized.payload_size}")
        print(f"   Payload matches: {deserialized.payload == packet.payload}")
    else:
        print(f"   FAILED - Could not deserialize packet")
        return False
    
    # Test 4: Create ACK packet
    print("\n4. Creating ACK packet...")
    ack_packet = handler.create_ack_packet(packet.sequence_id)
    ack_serialized = handler.serialize_packet(ack_packet)
    print(f"   ACK packet size: {len(ack_serialized)} bytes")
    
    # Test 5: Create HEARTBEAT packet
    print("\n5. Creating HEARTBEAT packet...")
    heartbeat = handler.create_heartbeat_packet()
    hb_serialized = handler.serialize_packet(heartbeat)
    print(f"   Heartbeat packet size: {len(hb_serialized)} bytes")
    
    print("\nProtocol test completed successfully!")
    return True

def test_serial_simulation():
    """Simulate serial transmission without actual hardware"""
    print("\n" + "="*50)
    print("Testing Serial Transmission Simulation...")
    
    try:
        import serial
        print("PySerial is available")
        
        # Try to list available ports
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        print(f"Available ports: {[port.device for port in ports]}")
        
        if not ports:
            print("No serial ports found - this is normal on some systems")
        
    except ImportError:
        print("PySerial not installed - install with: pip install pyserial")
        return False
    
    return True

if __name__ == "__main__":
    print("Serial Communication Performance Tester - Protocol Test")
    print("="*60)
    
    # Test protocol functionality
    protocol_ok = test_protocol()
    
    # Test serial availability
    serial_ok = test_serial_simulation()
    
    print("\n" + "="*60)
    if protocol_ok and serial_ok:
        print("✅ All tests passed! The protocol implementation is working.")
        print("\nIf the main application isn't sending data, the issue is likely:")
        print("1. Serial port connection problems")
        print("2. Test engine configuration issues")
        print("3. Threading/timing issues")
        print("\nRun the debug_serial.py script to investigate further.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("\nTo debug the main application:")
    print("python debug_serial.py")
