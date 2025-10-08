#!/usr/bin/env python3
"""
Debug version to identify why data is not being sent
"""

import sys
import logging
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QTimer

# Add project root to path
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.serial_handler import SerialHandler
from core.test_engine import TestEngine, TestMode
from utils.config import AppConfig

class DebugWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Serial Tester Debug")
        self.setGeometry(100, 100, 600, 400)
        
        # Setup logging with more detailed output
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('debug_serial.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Create components
        self.serial_handler = SerialHandler()
        self.test_engine = TestEngine(self.serial_handler)
        
        self.init_ui()
        self.connect_signals()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)
    
    def init_ui(self):
        widget = QWidget()
        self.setCentralWidget(widget)
        layout = QVBoxLayout(widget)
        
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)
        
        self.connect_btn = QPushButton("Connect to /dev/ttyUSB1")
        self.connect_btn.clicked.connect(self.connect_serial)
        layout.addWidget(self.connect_btn)
        
        self.test_btn = QPushButton("Start Transmitter Test")
        self.test_btn.clicked.connect(self.start_test)
        self.test_btn.setEnabled(False)
        layout.addWidget(self.test_btn)
        
        self.stop_btn = QPushButton("Stop Test")
        self.stop_btn.clicked.connect(self.stop_test)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        self.stats_label = QLabel("No stats yet")
        layout.addWidget(self.stats_label)
    
    def connect_signals(self):
        self.serial_handler.connection_status_changed.connect(self.on_connection_changed)
        self.serial_handler.error_occurred.connect(self.on_error)
        self.test_engine.test_started.connect(self.on_test_started)
        self.test_engine.test_stopped.connect(self.on_test_stopped)
        self.test_engine.metrics_updated.connect(self.on_metrics_updated)
        self.test_engine.status_message.connect(self.on_status_message)
    
    def connect_serial(self):
        self.logger.info("Attempting to connect to /dev/ttyUSB1")
        success = self.serial_handler.connect(
            port="/dev/ttyUSB1",
            baudrate=56700,
            timeout=1.0
        )
        self.logger.info(f"Connection result: {success}")
    
    def start_test(self):
        self.logger.info("Starting test...")
        
        # Configure test
        success = self.test_engine.configure_test(
            mode=TestMode.TRANSMITTER,
            packet_size=64,
            transmission_rate=1,  # Start with 1 packet per second for debugging
            test_duration=30
        )
        
        self.logger.info(f"Test configuration result: {success}")
        
        if success:
            start_result = self.test_engine.start_test()
            self.logger.info(f"Test start result: {start_result}")
    
    def stop_test(self):
        self.logger.info("Stopping test...")
        self.test_engine.stop_test()
    
    def on_connection_changed(self, connected):
        self.logger.info(f"Connection status changed: {connected}")
        self.test_btn.setEnabled(connected)
        self.connect_btn.setEnabled(not connected)
        if connected:
            self.status_label.setText("Status: Connected")
        else:
            self.status_label.setText("Status: Disconnected")
    
    def on_error(self, error):
        self.logger.error(f"Serial error: {error}")
        self.status_label.setText(f"Error: {error}")
    
    def on_test_started(self):
        self.logger.info("Test started signal received")
        self.test_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: Test Running")
    
    def on_test_stopped(self):
        self.logger.info("Test stopped signal received")
        self.test_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Test Stopped")
    
    def on_metrics_updated(self, metrics):
        stats_text = f"Sent: {metrics.packets_sent}, Received: {metrics.packets_received}, Duration: {metrics.test_duration:.1f}s"
        self.stats_label.setText(stats_text)
        self.logger.debug(f"Metrics update: {stats_text}")
    
    def on_status_message(self, message):
        self.logger.info(f"Status message: {message}")
    
    def update_status(self):
        if self.serial_handler.is_connected:
            stats = self.serial_handler.get_statistics()
            debug_text = f"Serial stats - Sent: {stats['packets_sent']}, Received: {stats['packets_received']}"
            self.logger.debug(debug_text)

def main():
    app = QApplication(sys.argv)
    window = DebugWindow()
    window.show()
    
    print("Debug window launched. Check the console and debug_serial.log for detailed logging.")
    print("Steps to test:")
    print("1. Click 'Connect to /dev/ttyS5'")
    print("2. Click 'Start Transmitter Test'")
    print("3. Watch the logs for packet transmission details")
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
