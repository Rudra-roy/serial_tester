"""
Metrics display panel with real-time charts and statistics
"""

import logging
import statistics
from typing import List, Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QGroupBox, QTabWidget, QTextEdit)
from PyQt6.QtCore import pyqtSlot, QTimer
from PyQt6.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from core.test_engine import TestMetrics

class MetricsDisplay(QWidget):
    """Real-time metrics display with charts and statistics"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Data storage for charts
        self.latency_data: List[float] = []
        self.bandwidth_data: List[float] = []
        self.time_data: List[float] = []
        
        # Chart update timer
        self.chart_update_timer = QTimer()
        self.chart_update_timer.timeout.connect(self.update_charts)
        self.chart_update_timer.start(1000)  # Update every second
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Statistics tab
        self.create_statistics_tab()
        
        # Charts tab
        self.create_charts_tab()
        
        # Raw data tab
        self.create_raw_data_tab()
    
    def create_statistics_tab(self):
        """Create statistics display tab"""
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        
        # Create statistics groups
        self.create_connection_stats_group(stats_layout)
        self.create_performance_stats_group(stats_layout)
        self.create_quality_stats_group(stats_layout)
        
        stats_layout.addStretch()
        self.tab_widget.addTab(stats_widget, "Statistics")
    
    def create_connection_stats_group(self, parent_layout):
        """Create connection statistics group"""
        group = QGroupBox("Connection Statistics")
        layout = QGridLayout(group)
        
        # Create labels with bold font for headers
        header_font = QFont()
        header_font.setBold(True)
        
        # Packets
        layout.addWidget(QLabel("Packets Sent:"), 0, 0)
        self.packets_sent_label = QLabel("0")
        layout.addWidget(self.packets_sent_label, 0, 1)
        
        layout.addWidget(QLabel("Packets Received:"), 1, 0)
        self.packets_received_label = QLabel("0")
        layout.addWidget(self.packets_received_label, 1, 1)
        
        layout.addWidget(QLabel("Packets Lost:"), 2, 0)
        self.packets_lost_label = QLabel("0")
        layout.addWidget(self.packets_lost_label, 2, 1)
        
        # Bytes
        layout.addWidget(QLabel("Bytes Transmitted:"), 0, 2)
        self.bytes_transmitted_label = QLabel("0")
        layout.addWidget(self.bytes_transmitted_label, 0, 3)
        
        layout.addWidget(QLabel("Test Duration:"), 1, 2)
        self.test_duration_label = QLabel("0.0 s")
        layout.addWidget(self.test_duration_label, 1, 3)
        
        parent_layout.addWidget(group)
    
    def create_performance_stats_group(self, parent_layout):
        """Create performance statistics group"""
        group = QGroupBox("Performance Metrics")
        layout = QGridLayout(group)
        
        # Latency
        layout.addWidget(QLabel("Average Latency:"), 0, 0)
        self.avg_latency_label = QLabel("0.0 ms")
        layout.addWidget(self.avg_latency_label, 0, 1)
        
        layout.addWidget(QLabel("Min Latency:"), 1, 0)
        self.min_latency_label = QLabel("0.0 ms")
        layout.addWidget(self.min_latency_label, 1, 1)
        
        layout.addWidget(QLabel("Max Latency:"), 2, 0)
        self.max_latency_label = QLabel("0.0 ms")
        layout.addWidget(self.max_latency_label, 2, 1)
        
        # Bandwidth
        layout.addWidget(QLabel("Average Bandwidth:"), 0, 2)
        self.avg_bandwidth_label = QLabel("0 B/s")
        layout.addWidget(self.avg_bandwidth_label, 0, 3)
        
        layout.addWidget(QLabel("Peak Bandwidth:"), 1, 2)
        self.peak_bandwidth_label = QLabel("0 B/s")
        layout.addWidget(self.peak_bandwidth_label, 1, 3)
        
        layout.addWidget(QLabel("Current Bandwidth:"), 2, 2)
        self.current_bandwidth_label = QLabel("0 B/s")
        layout.addWidget(self.current_bandwidth_label, 2, 3)
        
        parent_layout.addWidget(group)
    
    def create_quality_stats_group(self, parent_layout):
        """Create quality statistics group"""
        group = QGroupBox("Quality Metrics")
        layout = QGridLayout(group)
        
        # Packet loss
        layout.addWidget(QLabel("Packet Loss Rate:"), 0, 0)
        self.packet_loss_label = QLabel("0.0%")
        layout.addWidget(self.packet_loss_label, 0, 1)
        
        # Jitter (latency standard deviation)
        layout.addWidget(QLabel("Latency Jitter:"), 1, 0)
        self.jitter_label = QLabel("0.0 ms")
        layout.addWidget(self.jitter_label, 1, 1)
        
        # Throughput efficiency
        layout.addWidget(QLabel("Throughput Efficiency:"), 0, 2)
        self.efficiency_label = QLabel("0.0%")
        layout.addWidget(self.efficiency_label, 0, 3)
        
        # Error count
        layout.addWidget(QLabel("Error Count:"), 1, 2)
        self.error_count_label = QLabel("0")
        layout.addWidget(self.error_count_label, 1, 3)
        
        parent_layout.addWidget(group)
    
    def create_charts_tab(self):
        """Create charts display tab"""
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        
        # Create matplotlib figures
        self.latency_figure = Figure(figsize=(10, 4))
        self.latency_canvas = FigureCanvas(self.latency_figure)
        self.latency_ax = self.latency_figure.add_subplot(111)
        self.latency_ax.set_title('Latency Over Time')
        self.latency_ax.set_xlabel('Time (s)')
        self.latency_ax.set_ylabel('Latency (ms)')
        self.latency_ax.grid(True)
        
        self.bandwidth_figure = Figure(figsize=(10, 4))
        self.bandwidth_canvas = FigureCanvas(self.bandwidth_figure)
        self.bandwidth_ax = self.bandwidth_figure.add_subplot(111)
        self.bandwidth_ax.set_title('Bandwidth Over Time')
        self.bandwidth_ax.set_xlabel('Time (s)')
        self.bandwidth_ax.set_ylabel('Bandwidth (B/s)')
        self.bandwidth_ax.grid(True)
        
        charts_layout.addWidget(self.latency_canvas)
        charts_layout.addWidget(self.bandwidth_canvas)
        
        self.tab_widget.addTab(charts_widget, "Charts")
    
    def create_raw_data_tab(self):
        """Create raw data display tab"""
        raw_widget = QWidget()
        raw_layout = QVBoxLayout(raw_widget)
        
        self.raw_data_text = QTextEdit()
        self.raw_data_text.setReadOnly(True)
        self.raw_data_text.setFont(QFont("Courier", 9))
        raw_layout.addWidget(self.raw_data_text)
        
        self.tab_widget.addTab(raw_widget, "Raw Data")
    
    @pyqtSlot(object)
    def update_metrics(self, metrics: TestMetrics):
        """Update display with new metrics"""
        self.update_statistics_display(metrics)
        self.update_raw_data_display(metrics)
        
        # Store data for charts
        if metrics.latency_samples:
            self.latency_data = metrics.latency_samples.copy()
        if metrics.bandwidth_samples:
            self.bandwidth_data = metrics.bandwidth_samples.copy()
    
    def update_statistics_display(self, metrics: TestMetrics):
        """Update statistics labels"""
        # Connection stats
        self.packets_sent_label.setText(str(metrics.packets_sent))
        self.packets_received_label.setText(str(metrics.packets_received))
        self.packets_lost_label.setText(str(metrics.packets_lost))
        self.bytes_transmitted_label.setText(self.format_bytes(metrics.bytes_transmitted))
        self.test_duration_label.setText(f"{metrics.test_duration:.1f} s")
        
        # Performance stats
        if metrics.latency_samples:
            avg_latency = statistics.mean(metrics.latency_samples) * 1000  # Convert to ms
            min_latency = min(metrics.latency_samples) * 1000
            max_latency = max(metrics.latency_samples) * 1000
            
            self.avg_latency_label.setText(f"{avg_latency:.2f} ms")
            self.min_latency_label.setText(f"{min_latency:.2f} ms")
            self.max_latency_label.setText(f"{max_latency:.2f} ms")
            
            # Calculate jitter (standard deviation)
            if len(metrics.latency_samples) > 1:
                jitter = statistics.stdev(metrics.latency_samples) * 1000
                self.jitter_label.setText(f"{jitter:.2f} ms")
        
        if metrics.bandwidth_samples:
            avg_bandwidth = statistics.mean(metrics.bandwidth_samples)
            peak_bandwidth = max(metrics.bandwidth_samples)
            current_bandwidth = metrics.bandwidth_samples[-1] if metrics.bandwidth_samples else 0
            
            self.avg_bandwidth_label.setText(f"{self.format_bytes(avg_bandwidth)}/s")
            self.peak_bandwidth_label.setText(f"{self.format_bytes(peak_bandwidth)}/s")
            self.current_bandwidth_label.setText(f"{self.format_bytes(current_bandwidth)}/s")
        
        # Quality stats
        self.packet_loss_label.setText(f"{metrics.packet_loss_rate:.2f}%")
        self.error_count_label.setText(str(len(metrics.errors)))
        
        # Calculate efficiency (actual vs theoretical)
        if metrics.test_duration > 0 and metrics.bytes_transmitted > 0:
            actual_rate = metrics.bytes_transmitted / metrics.test_duration
            # This would need theoretical rate from configuration
            # For now, just show actual rate as efficiency placeholder
            self.efficiency_label.setText("N/A")
    
    def update_raw_data_display(self, metrics: TestMetrics):
        """Update raw data text display"""
        text = f"=== Test Metrics ===\n"
        text += f"Start Time: {metrics.start_time}\n"
        text += f"Test Duration: {metrics.test_duration:.2f} s\n"
        text += f"Packets Sent: {metrics.packets_sent}\n"
        text += f"Packets Received: {metrics.packets_received}\n"
        text += f"Packets Lost: {metrics.packets_lost}\n"
        text += f"Bytes Transmitted: {metrics.bytes_transmitted}\n"
        text += f"Packet Loss Rate: {metrics.packet_loss_rate:.2f}%\n"
        
        if metrics.latency_samples:
            text += f"\nLatency Statistics:\n"
            text += f"  Average: {statistics.mean(metrics.latency_samples)*1000:.2f} ms\n"
            text += f"  Min: {min(metrics.latency_samples)*1000:.2f} ms\n"
            text += f"  Max: {max(metrics.latency_samples)*1000:.2f} ms\n"
            if len(metrics.latency_samples) > 1:
                text += f"  Std Dev: {statistics.stdev(metrics.latency_samples)*1000:.2f} ms\n"
        
        if metrics.bandwidth_samples:
            text += f"\nBandwidth Statistics:\n"
            text += f"  Average: {self.format_bytes(statistics.mean(metrics.bandwidth_samples))}/s\n"
            text += f"  Peak: {self.format_bytes(max(metrics.bandwidth_samples))}/s\n"
        
        if metrics.errors:
            text += f"\nErrors ({len(metrics.errors)}):\n"
            for error in metrics.errors[-10:]:  # Show last 10 errors
                text += f"  {error}\n"
            if len(metrics.errors) > 10:
                text += f"  ... and {len(metrics.errors) - 10} more\n"
        
        self.raw_data_text.setPlainText(text)
    
    def update_charts(self):
        """Update matplotlib charts"""
        if not self.latency_data and not self.bandwidth_data:
            return
        
        # Update latency chart
        if self.latency_data:
            self.latency_ax.clear()
            self.latency_ax.set_title('Latency Over Time')
            self.latency_ax.set_xlabel('Sample')
            self.latency_ax.set_ylabel('Latency (ms)')
            self.latency_ax.grid(True)
            
            latency_ms = [lat * 1000 for lat in self.latency_data]  # Convert to ms
            self.latency_ax.plot(latency_ms, 'b-', linewidth=1)
            self.latency_figure.tight_layout()
            self.latency_canvas.draw()
        
        # Update bandwidth chart
        if self.bandwidth_data:
            self.bandwidth_ax.clear()
            self.bandwidth_ax.set_title('Bandwidth Over Time')
            self.bandwidth_ax.set_xlabel('Sample')
            self.bandwidth_ax.set_ylabel('Bandwidth (B/s)')
            self.bandwidth_ax.grid(True)
            
            self.bandwidth_ax.plot(self.bandwidth_data, 'g-', linewidth=1)
            self.bandwidth_figure.tight_layout()
            self.bandwidth_canvas.draw()
    
    def reset_display(self):
        """Reset all displays for new test"""
        # Clear data
        self.latency_data.clear()
        self.bandwidth_data.clear()
        self.time_data.clear()
        
        # Reset labels
        self.packets_sent_label.setText("0")
        self.packets_received_label.setText("0")
        self.packets_lost_label.setText("0")
        self.bytes_transmitted_label.setText("0 B")
        self.test_duration_label.setText("0.0 s")
        
        self.avg_latency_label.setText("0.0 ms")
        self.min_latency_label.setText("0.0 ms")
        self.max_latency_label.setText("0.0 ms")
        self.jitter_label.setText("0.0 ms")
        
        self.avg_bandwidth_label.setText("0 B/s")
        self.peak_bandwidth_label.setText("0 B/s")
        self.current_bandwidth_label.setText("0 B/s")
        
        self.packet_loss_label.setText("0.0%")
        self.error_count_label.setText("0")
        self.efficiency_label.setText("0.0%")
        
        # Clear charts
        self.latency_ax.clear()
        self.latency_ax.set_title('Latency Over Time')
        self.latency_ax.set_xlabel('Sample')
        self.latency_ax.set_ylabel('Latency (ms)')
        self.latency_ax.grid(True)
        self.latency_canvas.draw()
        
        self.bandwidth_ax.clear()
        self.bandwidth_ax.set_title('Bandwidth Over Time')
        self.bandwidth_ax.set_xlabel('Sample')
        self.bandwidth_ax.set_ylabel('Bandwidth (B/s)')
        self.bandwidth_ax.grid(True)
        self.bandwidth_canvas.draw()
        
        # Clear raw data
        self.raw_data_text.clear()
    
    @staticmethod
    def format_bytes(bytes_value: float) -> str:
        """Format bytes with appropriate units"""
        if bytes_value < 1024:
            return f"{bytes_value:.0f} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
