# Serial Communication Performance Testing Tool

A comprehensive PyQt6-based desktop application for testing serial communication performance between devices. This professional-grade tool addresses the limitations of existing serial testing solutions by providing advanced features for bandwidth analysis, packet loss detection, latency measurement, and comprehensive data logging.

## Features

### Core Functionality
- **Dual Mode Operation**: Transmitter and Receiver modes in a single application
- **Advanced Protocol**: Binary protocol with packet headers, sequence numbering, and CRC32 checksums
- **Real-time Metrics**: Live bandwidth, latency, and packet loss monitoring
- **Data Logging**: SQLite database for storing all test results and metrics

### Performance Metrics
- **Bandwidth Analysis**: Measure actual vs theoretical throughput limits
- **Packet Loss Detection**: Track missing/corrupted packets with sequence numbering
- **Latency Measurement**: Round-trip time and response delay analysis
- **Quality Metrics**: Jitter, efficiency, and error rate calculations

### User Interface
- **Professional GUI**: Clean, modern interface built with PyQt6
- **Real-time Charts**: Matplotlib integration for live performance visualization
- **Configuration Management**: Save/load test configurations and presets
- **Comprehensive History**: View, filter, and analyze past test results

### Data Management
- **SQLite Database**: Robust storage for test results and configurations
- **Export Capabilities**: CSV and JSON export formats for analysis
- **Statistical Analysis**: Built-in calculations for averages, percentiles, and distributions

## Installation

### Prerequisites
- Python 3.8 or later
- Linux/Windows/macOS

### Quick Setup
```bash
# Clone or download the project
cd serial_tester

# Run installation script (Linux/macOS)
chmod +x install.sh
./install.sh

# Or install manually
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Starting the Application
```bash
# Using the run script (Linux/macOS)
./run.sh

# Or manually
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

### Basic Workflow
1. **Configure Serial Port**: Select port, baud rate, and communication parameters
2. **Connect**: Establish connection to your serial device
3. **Configure Test**: Set packet size, transmission rate, and test duration
4. **Select Mode**: Choose Transmitter or Receiver mode based on your setup
5. **Run Test**: Start the performance test and monitor real-time metrics
6. **Analyze Results**: View statistics, charts, and export data for further analysis

### Test Modes

#### Transmitter Mode
- Sends test packets at configured rate
- Waits for ACK responses
- Measures round-trip latency
- Tracks packet loss and timeouts

#### Receiver Mode
- Receives and validates test packets
- Sends ACK responses
- Detects missing packets in sequence
- Measures reception bandwidth

## Architecture

### Modular Design
- **Core Components**: Protocol handler, serial communication, test engine
- **GUI Layer**: Separate panels for configuration, control, metrics, and history
- **Data Layer**: Database management and export utilities
- **Configuration**: Persistent settings and preset management

### Key Components
- `core/protocol.py`: Binary protocol implementation
- `core/serial_handler.py`: Thread-safe serial communication
- `core/test_engine.py`: Performance testing logic
- `core/database.py`: SQLite database operations
- `gui/main_window.py`: Main application window
- `utils/config.py`: Configuration management
- `utils/export.py`: Data export utilities

## Protocol Specification

### Packet Structure
```
[Magic][Type][Sequence][Timestamp][PayloadSize][Payload][CRC32]
```

- **Magic Byte**: 0xAA (packet delimiter)
- **Type**: DATA (0x01), ACK (0x02), HEARTBEAT (0x03)
- **Sequence**: 16-bit sequence number for ordering
- **Timestamp**: 32-bit millisecond timestamp
- **PayloadSize**: 32-bit payload length
- **Payload**: Variable length data
- **CRC32**: 32-bit checksum for integrity

### Communication Flow
1. Transmitter sends DATA packets with incrementing sequence numbers
2. Receiver validates packets and sends ACK responses
3. Both modes exchange periodic HEARTBEAT packets
4. Metrics are calculated based on timing and sequence analysis

## Configuration

### Serial Settings
- Port selection with auto-detection
- Baud rates from 300 to 921600
- Data bits, parity, stop bits configuration
- Timeout settings

### Test Parameters
- Packet size: 1-4096 bytes
- Transmission rate: 1-1000 packets/second
- Test duration: 1-3600 seconds
- Custom test notes and descriptions

## Data Export

### Supported Formats
- **CSV**: Separate files for summary, latency, bandwidth, and errors
- **JSON**: Complete session data in structured format
- **Summary Reports**: Multi-session comparison tables

### Export Contents
- Test configuration and parameters
- Performance metrics and statistics
- Time-series data for charts
- Error logs and diagnostic information

## Advanced Features

### Statistical Analysis
- Mean, median, standard deviation calculations
- Percentile analysis for latency distribution
- Bandwidth efficiency calculations
- Quality metrics and error rates

### Data Visualization
- Real-time latency and bandwidth charts
- Historical trend analysis
- Comparative performance graphs
- Statistical distribution plots

### Error Handling
- Comprehensive error logging
- Connection failure recovery
- Packet corruption detection
- Timeout and retry mechanisms

## Troubleshooting

### Common Issues
- **Permission Denied**: Ensure user has access to serial ports (Linux: add to dialout group)
- **Port Not Found**: Check device connections and driver installation
- **Import Errors**: Verify all dependencies are installed in virtual environment

### Logging
- Application logs are saved to `serial_tester.log`
- Enable verbose logging for detailed diagnostics
- Error messages include timestamps and context

## Technical Specifications

### Performance
- Supports baud rates up to 921600
- Real-time processing with minimal latency
- Efficient memory usage for long-term tests
- Thread-safe multi-component architecture

### Compatibility
- Cross-platform: Linux, Windows, macOS
- PyQt6 for modern GUI capabilities
- Standard serial communication protocols
- Matplotlib for professional charts

## Development

### Project Structure
```
serial_tester/
├── main.py              # Application entry point
├── requirements.txt     # Dependencies
├── core/               # Core functionality
│   ├── protocol.py     # Binary protocol
│   ├── serial_handler.py # Serial communication
│   ├── test_engine.py  # Testing logic
│   └── database.py     # Data storage
├── gui/                # User interface
│   ├── main_window.py  # Main window
│   ├── config_panel.py # Configuration
│   ├── test_control_panel.py # Test controls
│   ├── metrics_display.py # Real-time metrics
│   └── history_panel.py # Test history
└── utils/              # Utilities
    ├── config.py       # Settings management
    └── export.py       # Data export
```

### Contributing
- Follow PEP 8 style guidelines
- Add unit tests for new features
- Update documentation for API changes
- Test across multiple platforms

## License

This project is designed for professional use in testing serial communication systems. It provides a comprehensive solution for engineers and technicians who need reliable, accurate performance measurement tools.

## Support

For technical support, feature requests, or bug reports, please refer to the application logs and error messages for detailed diagnostic information.
