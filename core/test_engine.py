"""
Test engine for performance testing
"""

import time
import threading
import logging
import statistics
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from core.serial_handler import SerialHandler
from core.protocol import PacketType, Packet

class TestMode(Enum):
    """Test modes"""
    TRANSMITTER = "transmitter"
    RECEIVER = "receiver"

@dataclass
class TestMetrics:
    """Performance metrics data"""
    start_time: float
    end_time: float
    packets_sent: int
    packets_received: int
    packets_lost: int
    bytes_transmitted: int
    latency_samples: List[float]
    bandwidth_samples: List[float]
    errors: List[str]
    
    @property
    def test_duration(self) -> float:
        return self.end_time - self.start_time if self.end_time > 0 else time.time() - self.start_time
    
    @property
    def packet_loss_rate(self) -> float:
        if self.packets_sent == 0:
            return 0.0
        return (self.packets_lost / self.packets_sent) * 100
    
    @property
    def average_latency(self) -> float:
        return statistics.mean(self.latency_samples) if self.latency_samples else 0.0
    
    @property
    def average_bandwidth(self) -> float:
        return statistics.mean(self.bandwidth_samples) if self.bandwidth_samples else 0.0

class TestEngine(QObject):
    """Performance test engine"""
    
    # Signals
    test_started = pyqtSignal()
    test_stopped = pyqtSignal()
    test_paused = pyqtSignal()
    test_resumed = pyqtSignal()
    metrics_updated = pyqtSignal(object)  # TestMetrics
    progress_updated = pyqtSignal(float)  # elapsed_time in seconds
    status_message = pyqtSignal(str)
    
    def __init__(self, serial_handler: SerialHandler):
        super().__init__()
        self.serial_handler = serial_handler
        self.logger = logging.getLogger(__name__)
        
        # Test configuration
        self.mode = TestMode.TRANSMITTER
        self.packet_size = 64
        self.transmission_rate = 10  # packets per second
        self.test_duration = 60  # seconds
        self.heartbeat_interval = 5  # seconds
        
        # Test state
        self.is_running = False
        self.is_paused = False
        self.test_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        
        # Metrics tracking
        self.metrics = TestMetrics(
            start_time=0,
            end_time=0,
            packets_sent=0,
            packets_received=0,
            packets_lost=0,
            bytes_transmitted=0,
            latency_samples=[],
            bandwidth_samples=[],
            errors=[]
        )
        
        # Transmitter state
        self.pending_acks: Dict[int, float] = {}  # seq_id -> timestamp
        self.expected_sequences: List[int] = []
        
        # Receiver state
        self.received_sequences: set = set()
        self.last_sequence = -1
        
        # Connect to serial handler signals
        self.serial_handler.packet_received.connect(self._handle_received_packet)
        
        # Periodic update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._emit_metrics_update)
        self.update_timer.start(1000)  # Update every second
    
    def configure_test(self, mode: TestMode, packet_size: int, 
                      transmission_rate: int, test_duration: int):
        """Configure test parameters"""
        if self.is_running:
            return False
        
        self.mode = mode
        self.packet_size = packet_size
        self.transmission_rate = transmission_rate
        self.test_duration = test_duration
        
        self.logger.info(f"Test configured: mode={mode.value}, size={packet_size}, "
                        f"rate={transmission_rate}, duration={test_duration}")
        return True
    
    def start_test(self) -> bool:
        """Start performance test"""
        if self.is_running or not self.serial_handler.is_connected:
            return False
        
        # Reset metrics
        self._reset_metrics()
        
        self.is_running = True
        self.is_paused = False
        self.stop_event.clear()
        self.pause_event.clear()
        
        # Start test thread
        self.test_thread = threading.Thread(target=self._test_loop, daemon=True)
        self.test_thread.start()
        
        self.test_started.emit()
        self.status_message.emit(f"Test started in {self.mode.value} mode")
        self.logger.info(f"Test started in {self.mode.value} mode")
        
        return True
    
    def stop_test(self):
        """Stop performance test"""
        if not self.is_running:
            return
        
        self.stop_event.set()
        self.is_running = False
        
        if self.test_thread and self.test_thread.is_alive():
            self.test_thread.join(timeout=2.0)
        
        self.metrics.end_time = time.time()
        self.test_stopped.emit()
        self.status_message.emit("Test stopped")
        self.logger.info("Test stopped")
    
    def pause_test(self):
        """Pause performance test"""
        if not self.is_running or self.is_paused:
            return
        
        self.is_paused = True
        self.pause_event.set()
        self.test_paused.emit()
        self.status_message.emit("Test paused")
    
    def resume_test(self):
        """Resume performance test"""
        if not self.is_running or not self.is_paused:
            return
        
        self.is_paused = False
        self.pause_event.clear()
        self.test_resumed.emit()
        self.status_message.emit("Test resumed")
    
    def _test_loop(self):
        """Main test loop"""
        self.metrics.start_time = time.time()
        last_heartbeat = time.time()
        last_bandwidth_calc = time.time()
        bytes_at_last_calc = 0
        
        if self.mode == TestMode.TRANSMITTER:
            self._transmitter_loop(last_heartbeat, last_bandwidth_calc, bytes_at_last_calc)
        else:
            self._receiver_loop(last_heartbeat, last_bandwidth_calc, bytes_at_last_calc)
        
        # Finalize test when loop ends (either by break or stop_event)
        self.metrics.end_time = time.time()
        self.is_running = False
        self.test_stopped.emit()
        self.status_message.emit("Test completed")
        self.logger.info(f"Test completed. Duration: {self.metrics.test_duration:.2f}s")
        
        # Send final metrics update
        self.metrics_updated.emit(self.metrics)
    
    def _transmitter_loop(self, last_heartbeat: float, last_bandwidth_calc: float, bytes_at_last_calc: int):
        """Transmitter test loop"""
        packet_interval = 1.0 / self.transmission_rate
        next_packet_time = time.time()
        
        while not self.stop_event.is_set():
            current_time = time.time()
            elapsed_time = current_time - self.metrics.start_time
            
            # Check if test duration exceeded
            if elapsed_time >= self.test_duration:
                self.logger.info(f"Test duration exceeded: {elapsed_time:.1f}s >= {self.test_duration}s")
                break
            
            # Handle pause
            while self.pause_event.is_set() and not self.stop_event.is_set():
                time.sleep(0.1)
            
            # Send heartbeat if needed
            if current_time - last_heartbeat >= self.heartbeat_interval:
                heartbeat = self.serial_handler.protocol.create_heartbeat_packet()
                self.serial_handler.send_packet(heartbeat)
                last_heartbeat = current_time
            
            # Send data packet if it's time
            if current_time >= next_packet_time:
                # Create test data
                test_data = b'X' * self.packet_size
                packet = self.serial_handler.protocol.create_data_packet(test_data)
                
                if self.serial_handler.send_packet(packet):
                    self.metrics.packets_sent += 1
                    self.metrics.bytes_transmitted += len(test_data)
                    self.pending_acks[packet.sequence_id] = current_time
                    self.expected_sequences.append(packet.sequence_id)
                
                next_packet_time += packet_interval
            
            # Calculate bandwidth periodically
            if current_time - last_bandwidth_calc >= 1.0:
                bytes_diff = self.metrics.bytes_transmitted - bytes_at_last_calc
                bandwidth = bytes_diff / (current_time - last_bandwidth_calc)
                self.metrics.bandwidth_samples.append(bandwidth)
                
                last_bandwidth_calc = current_time
                bytes_at_last_calc = self.metrics.bytes_transmitted
            
            # Check for timeouts
            self._check_ack_timeouts(current_time)
            
            time.sleep(0.001)  # Small delay
    
    def _receiver_loop(self, last_heartbeat: float, last_bandwidth_calc: float, bytes_at_last_calc: int):
        """Receiver test loop"""
        while not self.stop_event.is_set():
            current_time = time.time()
            elapsed_time = current_time - self.metrics.start_time
            
            # Check if test duration exceeded
            if elapsed_time >= self.test_duration:
                self.logger.info(f"Test duration exceeded: {elapsed_time:.1f}s >= {self.test_duration}s")
                break
            
            # Handle pause
            while self.pause_event.is_set() and not self.stop_event.is_set():
                time.sleep(0.1)
            
            # Send heartbeat if needed
            if current_time - last_heartbeat >= self.heartbeat_interval:
                heartbeat = self.serial_handler.protocol.create_heartbeat_packet()
                self.serial_handler.send_packet(heartbeat)
                last_heartbeat = current_time
            
            # Calculate bandwidth periodically
            if current_time - last_bandwidth_calc >= 1.0:
                bytes_diff = self.metrics.bytes_transmitted - bytes_at_last_calc
                bandwidth = bytes_diff / (current_time - last_bandwidth_calc)
                if bandwidth > 0:
                    self.metrics.bandwidth_samples.append(bandwidth)
                
                last_bandwidth_calc = current_time
                bytes_at_last_calc = self.metrics.bytes_transmitted
            
            time.sleep(0.1)  # Receiver mostly waits for packets
    
    def _handle_received_packet(self, packet: Packet):
        """Handle received packet based on current mode"""
        if not self.is_running:
            return
        
        current_time = time.time()
        
        if packet.packet_type == PacketType.DATA:
            if self.mode == TestMode.TRANSMITTER:
                # Unexpected DATA packet in transmitter mode
                self.metrics.errors.append(f"Unexpected DATA packet: seq={packet.sequence_id}")
            else:
                # Receiver mode - handle data packet
                self._handle_data_packet_receiver(packet, current_time)
        
        elif packet.packet_type == PacketType.ACK:
            if self.mode == TestMode.TRANSMITTER:
                # Transmitter mode - handle ACK
                self._handle_ack_packet_transmitter(packet, current_time)
            else:
                # Unexpected ACK in receiver mode
                self.metrics.errors.append(f"Unexpected ACK packet: seq={packet.sequence_id}")
        
        elif packet.packet_type == PacketType.HEARTBEAT:
            # Heartbeat received - update connection status
            pass
    
    def _handle_data_packet_receiver(self, packet: Packet, current_time: float):
        """Handle DATA packet in receiver mode"""
        self.metrics.packets_received += 1
        self.metrics.bytes_transmitted += len(packet.payload)
        self.received_sequences.add(packet.sequence_id)
        
        # Check for packet loss (gaps in sequence)
        if packet.sequence_id > self.last_sequence + 1:
            lost_count = packet.sequence_id - self.last_sequence - 1
            self.metrics.packets_lost += lost_count
            for seq in range(self.last_sequence + 1, packet.sequence_id):
                self.metrics.errors.append(f"Missing packet: seq={seq}")
        
        self.last_sequence = max(self.last_sequence, packet.sequence_id)
        
        # Send ACK
        ack_packet = self.serial_handler.protocol.create_ack_packet(packet.sequence_id)
        self.serial_handler.send_packet(ack_packet)
        
        # Calculate latency (round-trip from packet timestamp to now)
        latency = current_time - packet.timestamp
        if latency > 0:  # Sanity check
            self.metrics.latency_samples.append(latency)
    
    def _handle_ack_packet_transmitter(self, packet: Packet, current_time: float):
        """Handle ACK packet in transmitter mode"""
        acked_seq = self.serial_handler.protocol.get_acked_sequence(packet)
        
        if acked_seq is not None and acked_seq in self.pending_acks:
            # Calculate round-trip latency
            send_time = self.pending_acks[acked_seq]
            latency = current_time - send_time
            self.metrics.latency_samples.append(latency)
            
            # Remove from pending
            del self.pending_acks[acked_seq]
            self.metrics.packets_received += 1
    
    def _check_ack_timeouts(self, current_time: float, timeout: float = 5.0):
        """Check for ACK timeouts and mark packets as lost"""
        timed_out = []
        for seq_id, send_time in self.pending_acks.items():
            if current_time - send_time > timeout:
                timed_out.append(seq_id)
        
        for seq_id in timed_out:
            del self.pending_acks[seq_id]
            self.metrics.packets_lost += 1
            self.metrics.errors.append(f"ACK timeout: seq={seq_id}")
    
    def _reset_metrics(self):
        """Reset all metrics for new test"""
        self.metrics = TestMetrics(
            start_time=0,
            end_time=0,
            packets_sent=0,
            packets_received=0,
            packets_lost=0,
            bytes_transmitted=0,
            latency_samples=[],
            bandwidth_samples=[],
            errors=[]
        )
        
        self.pending_acks.clear()
        self.expected_sequences.clear()
        self.received_sequences.clear()
        self.last_sequence = -1
    
    def _emit_metrics_update(self):
        """Emit metrics update signal"""
        if self.is_running:
            elapsed_time = time.time() - self.metrics.start_time
            self.metrics_updated.emit(self.metrics)
            self.progress_updated.emit(elapsed_time)
    
    def get_current_metrics(self) -> TestMetrics:
        """Get current test metrics"""
        return self.metrics
