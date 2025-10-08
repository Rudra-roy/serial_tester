"""
Test control panel for managing performance tests
"""

import logging
from typing import Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QComboBox, QSpinBox, QPushButton, QGroupBox,
                            QLabel, QProgressBar, QTextEdit, QGridLayout)
from PyQt6.QtCore import pyqtSignal, Qt

class TestControlPanel(QWidget):
    """Test control panel for performance testing"""
    
    # Signals
    start_test = pyqtSignal()
    stop_test = pyqtSignal()
    pause_test = pyqtSignal()
    resume_test = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
        self.is_test_running = False
        self.is_test_paused = False
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Test configuration group
        config_group = QGroupBox("Test Configuration")
        config_layout = QGridLayout(config_group)
        config_layout.setVerticalSpacing(12)
        config_layout.setHorizontalSpacing(10)
        
        # Create labels and controls with proper sizing
        row = 0
        
        # Test mode
        mode_label = QLabel("Test Mode:")
        mode_label.setMinimumWidth(100)
        mode_label.setMaximumWidth(100)
        self.mode_combo = QComboBox()
        self.mode_combo.setMinimumHeight(32)
        self.mode_combo.setMinimumWidth(150)
        self.mode_combo.addItem("Transmitter", "transmitter")
        self.mode_combo.addItem("Receiver", "receiver")
        config_layout.addWidget(mode_label, row, 0, Qt.AlignmentFlag.AlignRight)
        config_layout.addWidget(self.mode_combo, row, 1)
        row += 1
        
        # Packet size
        packet_label = QLabel("Packet Size:")
        packet_label.setMinimumWidth(100)
        packet_label.setMaximumWidth(100)
        self.packet_size_spin = QSpinBox()
        self.packet_size_spin.setMinimumHeight(32)
        self.packet_size_spin.setMinimumWidth(150)
        self.packet_size_spin.setRange(1, 4096)
        self.packet_size_spin.setValue(64)
        self.packet_size_spin.setSuffix(" bytes")
        config_layout.addWidget(packet_label, row, 0, Qt.AlignmentFlag.AlignRight)
        config_layout.addWidget(self.packet_size_spin, row, 1)
        row += 1
        
        # Transmission rate
        rate_label = QLabel("Rate:")
        rate_label.setMinimumWidth(100)
        rate_label.setMaximumWidth(100)
        self.rate_spin = QSpinBox()
        self.rate_spin.setMinimumHeight(32)
        self.rate_spin.setMinimumWidth(150)
        self.rate_spin.setRange(1, 1000)
        self.rate_spin.setValue(10)
        self.rate_spin.setSuffix(" pkt/s")
        config_layout.addWidget(rate_label, row, 0, Qt.AlignmentFlag.AlignRight)
        config_layout.addWidget(self.rate_spin, row, 1)
        row += 1
        
        # Test duration
        duration_label = QLabel("Duration:")
        duration_label.setMinimumWidth(100)
        duration_label.setMaximumWidth(100)
        self.duration_spin = QSpinBox()
        self.duration_spin.setMinimumHeight(32)
        self.duration_spin.setMinimumWidth(150)
        self.duration_spin.setRange(1, 3600)
        self.duration_spin.setValue(60)
        self.duration_spin.setSuffix(" sec")
        config_layout.addWidget(duration_label, row, 0, Qt.AlignmentFlag.AlignRight)
        config_layout.addWidget(self.duration_spin, row, 1)
        
        # Set column stretch: labels don't expand, controls expand to fill available space
        config_layout.setColumnStretch(0, 0)  # Labels stay fixed width
        config_layout.setColumnStretch(1, 1)  # Controls expand
        
        layout.addWidget(config_group)
        
        # Test control group
        control_group = QGroupBox("Test Control")
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(12)  # Add spacing between elements
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Add spacing between buttons
        
        self.start_button = QPushButton("Start Test")
        self.start_button.setMinimumHeight(35)
        self.start_button.clicked.connect(self.start_test.emit)
        self.start_button.setEnabled(False)
        
        self.stop_button = QPushButton("Stop Test")
        self.stop_button.setMinimumHeight(35)
        self.stop_button.clicked.connect(self.stop_test.emit)
        self.stop_button.setEnabled(False)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.setMinimumHeight(35)
        self.pause_button.clicked.connect(self.on_pause_clicked)
        self.pause_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.pause_button)
        
        control_layout.addLayout(button_layout)
        
        # Test status
        self.status_label = QLabel("Status: Ready")
        control_layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        layout.addWidget(control_group)
        
        # Test notes group
        notes_group = QGroupBox("Test Notes")
        notes_layout = QVBoxLayout(notes_group)
        notes_layout.setSpacing(10)  # Add spacing
        
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(120)  # Slightly taller for better visibility
        self.notes_text.setMinimumHeight(80)
        self.notes_text.setPlaceholderText("Enter optional notes about this test...")
        notes_layout.addWidget(self.notes_text)
        
        layout.addWidget(notes_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
    
    def on_pause_clicked(self):
        """Handle pause/resume button click"""
        if self.is_test_paused:
            self.resume_test.emit()
        else:
            self.pause_test.emit()
    
    def get_test_config(self) -> Dict[str, Any]:
        """Get current test configuration"""
        return {
            'mode': self.mode_combo.currentData(),
            'packet_size': self.packet_size_spin.value(),
            'transmission_rate': self.rate_spin.value(),
            'test_duration': self.duration_spin.value(),
            'notes': self.notes_text.toPlainText().strip()
        }
    
    def set_connection_status(self, connected: bool):
        """Update controls based on connection status"""
        self.is_connected = connected
        self.update_button_states()
        
        if connected:
            self.status_label.setText("Status: Connected - Ready to test")
        else:
            self.status_label.setText("Status: Not connected")
    
    def set_test_running(self, running: bool):
        """Update controls based on test running status"""
        self.is_test_running = running
        self.is_test_paused = False
        self.update_button_states()
        
        if running:
            self.status_label.setText("Status: Test running...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, self.duration_spin.value())
            self.progress_bar.setValue(0)
        else:
            self.status_label.setText("Status: Test stopped")
            self.progress_bar.setVisible(False)
    
    def set_test_paused(self, paused: bool):
        """Update controls based on test paused status"""
        self.is_test_paused = paused
        self.update_button_states()
        
        if paused:
            self.status_label.setText("Status: Test paused")
            self.pause_button.setText("Resume")
        else:
            self.status_label.setText("Status: Test running...")
            self.pause_button.setText("Pause")
    
    def update_button_states(self):
        """Update button enabled states"""
        # Start button: enabled when connected and not running
        self.start_button.setEnabled(self.is_connected and not self.is_test_running)
        
        # Stop button: enabled when test is running
        self.stop_button.setEnabled(self.is_test_running)
        
        # Pause button: enabled when test is running
        self.pause_button.setEnabled(self.is_test_running)
        
        # Configuration controls: disabled when test is running
        config_enabled = not self.is_test_running
        self.mode_combo.setEnabled(config_enabled)
        self.packet_size_spin.setEnabled(config_enabled)
        self.rate_spin.setEnabled(config_enabled)
        self.duration_spin.setEnabled(config_enabled)
    
    def update_progress(self, elapsed_time: float):
        """Update progress bar"""
        if self.progress_bar.isVisible():
            self.progress_bar.setValue(int(elapsed_time))
    
    def load_config(self, config_dict: Dict[str, Any]):
        """Load configuration from dictionary"""
        if 'mode' in config_dict:
            index = self.mode_combo.findData(config_dict['mode'])
            if index >= 0:
                self.mode_combo.setCurrentIndex(index)
        
        if 'packet_size' in config_dict:
            self.packet_size_spin.setValue(config_dict['packet_size'])
        
        if 'transmission_rate' in config_dict:
            self.rate_spin.setValue(config_dict['transmission_rate'])
        
        if 'test_duration' in config_dict:
            self.duration_spin.setValue(config_dict['test_duration'])
        
        if 'notes' in config_dict:
            self.notes_text.setPlainText(config_dict['notes'])
