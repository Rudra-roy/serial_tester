"""
Configuration panel for serial settings
"""

import logging
from typing import Dict, Any
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QComboBox, QSpinBox, QPushButton, QGroupBox,
                            QLabel, QMessageBox)
from PyQt6.QtCore import pyqtSignal, QTimer
from utils.config import AppConfig, SerialConfig

class ConfigPanel(QWidget):
    """Configuration panel for serial port and test settings"""
    
    # Signals
    connect_requested = pyqtSignal()
    disconnect_requested = pyqtSignal()
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        self.init_ui()
        self.load_current_config()
        
        # Refresh ports periodically
        self.port_refresh_timer = QTimer()
        self.port_refresh_timer.timeout.connect(self.refresh_ports)
        self.port_refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Serial configuration group
        serial_group = QGroupBox("Serial Port Configuration")
        serial_layout = QFormLayout(serial_group)
        
        # Increase spacing between form rows
        serial_layout.setVerticalSpacing(15)
        serial_layout.setHorizontalSpacing(10)
        serial_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Port selection
        port_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        self.port_combo.setMinimumHeight(30)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setMinimumHeight(30)
        self.refresh_button.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.port_combo)
        port_layout.addWidget(self.refresh_button)
        serial_layout.addRow("Port:", port_layout)
        
        # Baud rate
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.setMinimumHeight(30)
        self.baudrate_combo.setMinimumWidth(120)
        common_bauds = [300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        for baud in common_bauds:
            self.baudrate_combo.addItem(str(baud), baud)
        self.baudrate_combo.setCurrentText("9600")
        self.baudrate_combo.setEditable(True)
        serial_layout.addRow("Baud Rate:", self.baudrate_combo)
        
        # Data bits
        self.bytesize_combo = QComboBox()
        self.bytesize_combo.setMinimumHeight(30)
        self.bytesize_combo.setMinimumWidth(80)
        for size in [5, 6, 7, 8]:
            self.bytesize_combo.addItem(str(size), size)
        self.bytesize_combo.setCurrentText("8")
        serial_layout.addRow("Data Bits:", self.bytesize_combo)
        
        # Parity
        self.parity_combo = QComboBox()
        self.parity_combo.setMinimumHeight(30)
        self.parity_combo.setMinimumWidth(100)
        parity_options = [('None', 'N'), ('Even', 'E'), ('Odd', 'O'), ('Mark', 'M'), ('Space', 'S')]
        for name, value in parity_options:
            self.parity_combo.addItem(name, value)
        serial_layout.addRow("Parity:", self.parity_combo)
        
        # Stop bits
        self.stopbits_combo = QComboBox()
        self.stopbits_combo.setMinimumHeight(30)
        self.stopbits_combo.setMinimumWidth(80)
        for bits in [1, 1.5, 2]:
            self.stopbits_combo.addItem(str(bits), bits)
        serial_layout.addRow("Stop Bits:", self.stopbits_combo)
        
        # Timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setMinimumHeight(30)
        self.timeout_spin.setMinimumWidth(100)
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(1)
        self.timeout_spin.setSuffix(" sec")
        serial_layout.addRow("Timeout:", self.timeout_spin)
        
        layout.addWidget(serial_group)
        
        # Connection controls
        connection_group = QGroupBox("Connection Control")
        connection_layout = QVBoxLayout(connection_group)
        connection_layout.setSpacing(10)  # Add spacing between elements
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Add spacing between buttons
        self.connect_button = QPushButton("Connect")
        self.connect_button.setMinimumHeight(35)
        self.connect_button.clicked.connect(self.connect_requested.emit)
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.setMinimumHeight(35)
        self.disconnect_button.clicked.connect(self.disconnect_requested.emit)
        self.disconnect_button.setEnabled(False)
        
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.disconnect_button)
        connection_layout.addLayout(button_layout)
        
        # Connection status
        self.status_label = QLabel("Status: Disconnected")
        connection_layout.addWidget(self.status_label)
        
        layout.addWidget(connection_group)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        # Connect value change signals to save config
        self.port_combo.currentTextChanged.connect(self.save_current_config)
        self.baudrate_combo.currentTextChanged.connect(self.save_current_config)
        self.bytesize_combo.currentTextChanged.connect(self.save_current_config)
        self.parity_combo.currentTextChanged.connect(self.save_current_config)
        self.stopbits_combo.currentTextChanged.connect(self.save_current_config)
        self.timeout_spin.valueChanged.connect(self.save_current_config)
    
    def refresh_ports(self):
        """Refresh available serial ports"""
        try:
            current_port = self.port_combo.currentText()
            
            self.port_combo.clear()
            ports = self.config.get_available_ports()
            
            if not ports:
                self.port_combo.addItem("No ports available")
                self.connect_button.setEnabled(False)
            else:
                for port in ports:
                    self.port_combo.addItem(port)
                self.connect_button.setEnabled(True)
                
                # Restore previously selected port if still available
                if current_port in ports:
                    self.port_combo.setCurrentText(current_port)
            
        except Exception as e:
            self.logger.error(f"Error refreshing ports: {e}")
            QMessageBox.warning(self, "Port Refresh Error", 
                              f"Failed to refresh ports: {e}")
    
    def get_serial_config(self) -> SerialConfig:
        """Get current serial configuration"""
        config = SerialConfig()
        
        config.port = self.port_combo.currentText()
        
        try:
            config.baudrate = int(self.baudrate_combo.currentText())
        except ValueError:
            config.baudrate = 9600
        
        config.bytesize = self.bytesize_combo.currentData()
        config.parity = self.parity_combo.currentData()
        config.stopbits = self.stopbits_combo.currentData()
        config.timeout = float(self.timeout_spin.value())
        
        return config
    
    def set_connection_status(self, connected: bool):
        """Update connection status display"""
        if connected:
            self.status_label.setText("Status: Connected")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            
            # Disable port selection when connected
            self.port_combo.setEnabled(False)
            self.refresh_button.setEnabled(False)
        else:
            self.status_label.setText("Status: Disconnected")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            
            # Enable port selection when disconnected
            self.port_combo.setEnabled(True)
            self.refresh_button.setEnabled(True)
    
    def load_current_config(self):
        """Load configuration from config object"""
        # Refresh ports first
        self.refresh_ports()
        
        # Set serial configuration
        if self.config.serial.port:
            index = self.port_combo.findText(self.config.serial.port)
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        
        self.baudrate_combo.setCurrentText(str(self.config.serial.baudrate))
        
        index = self.bytesize_combo.findData(self.config.serial.bytesize)
        if index >= 0:
            self.bytesize_combo.setCurrentIndex(index)
        
        index = self.parity_combo.findData(self.config.serial.parity)
        if index >= 0:
            self.parity_combo.setCurrentIndex(index)
        
        index = self.stopbits_combo.findData(self.config.serial.stopbits)
        if index >= 0:
            self.stopbits_combo.setCurrentIndex(index)
        
        self.timeout_spin.setValue(int(self.config.serial.timeout))
    
    def save_current_config(self):
        """Save current settings to config object"""
        serial_config = self.get_serial_config()
        
        self.config.serial.port = serial_config.port
        self.config.serial.baudrate = serial_config.baudrate
        self.config.serial.bytesize = serial_config.bytesize
        self.config.serial.parity = serial_config.parity
        self.config.serial.stopbits = serial_config.stopbits
        self.config.serial.timeout = serial_config.timeout
        
        self.config.save_config()
    
    def load_config(self, config_dict: Dict[str, Any]):
        """Load configuration from dictionary"""
        if 'serial_port' in config_dict:
            index = self.port_combo.findText(config_dict['serial_port'])
            if index >= 0:
                self.port_combo.setCurrentIndex(index)
        
        if 'baudrate' in config_dict:
            self.baudrate_combo.setCurrentText(str(config_dict['baudrate']))
        
        if 'bytesize' in config_dict:
            index = self.bytesize_combo.findData(config_dict['bytesize'])
            if index >= 0:
                self.bytesize_combo.setCurrentIndex(index)
        
        if 'parity' in config_dict:
            index = self.parity_combo.findData(config_dict['parity'])
            if index >= 0:
                self.parity_combo.setCurrentIndex(index)
        
        if 'stopbits' in config_dict:
            index = self.stopbits_combo.findData(config_dict['stopbits'])
            if index >= 0:
                self.stopbits_combo.setCurrentIndex(index)
