"""
Configuration management for Serial Communication Performance Tester
"""

import json
import os
from typing import Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class SerialConfig:
    """Serial port configuration"""
    port: str = ""
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = 'N'  # N, E, O
    stopbits: int = 1
    timeout: float = 1.0
    
@dataclass 
class TestConfig:
    """Test parameters configuration"""
    packet_size: int = 64
    transmission_rate: int = 10  # packets per second
    test_duration: int = 60  # seconds
    max_retries: int = 3
    heartbeat_interval: int = 5  # seconds
    
@dataclass
class AppConfig:
    """Main application configuration"""
    def __init__(self):
        self.config_file = "config.json"
        self.serial = SerialConfig()
        self.test = TestConfig()
        self.window_geometry = ""
        self.last_export_path = ""
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    
                # Update serial config
                if 'serial' in data:
                    for key, value in data['serial'].items():
                        if hasattr(self.serial, key):
                            setattr(self.serial, key, value)
                
                # Update test config
                if 'test' in data:
                    for key, value in data['test'].items():
                        if hasattr(self.test, key):
                            setattr(self.test, key, value)
                
                # Update app settings
                self.window_geometry = data.get('window_geometry', '')
                self.last_export_path = data.get('last_export_path', '')
                            
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            data = {
                'serial': asdict(self.serial),
                'test': asdict(self.test),
                'window_geometry': self.window_geometry,
                'last_export_path': self.last_export_path
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_available_ports(self) -> list:
        """Get list of available serial ports"""
        import serial.tools.list_ports
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(port.device)
        return ports
