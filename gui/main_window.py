"""
Main window for Serial Communication Performance Tester
"""

import os
import logging
from typing import Optional
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QStatusBar, QMenuBar, QMessageBox,
                            QFileDialog, QInputDialog)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QAction, QIcon

from core.serial_handler import SerialHandler
from core.test_engine import TestEngine, TestMode
from core.database import DatabaseHandler
from gui.config_panel import ConfigPanel
from gui.test_control_panel import TestControlPanel
from gui.metrics_display import MetricsDisplay
from gui.history_panel import HistoryPanel
from utils.config import AppConfig
from utils.export import DataExporter

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, config: AppConfig):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.serial_handler = SerialHandler()
        self.test_engine = TestEngine(self.serial_handler)
        self.database = DatabaseHandler()
        self.exporter = DataExporter()
        
        # UI state
        self.current_test_session_id: Optional[int] = None
        
        self.init_ui()
        self.connect_signals()
        self.restore_window_state()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Update every second
    
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Serial Communication Performance Tester")
        self.setMinimumSize(1200, 800)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Configuration tab
        self.config_panel = ConfigPanel(self.config)
        self.tab_widget.addTab(self.config_panel, "Configuration")
        
        # Test control tab
        test_tab = QWidget()
        test_layout = QVBoxLayout(test_tab)
        
        self.test_control_panel = TestControlPanel()
        test_layout.addWidget(self.test_control_panel)
        
        self.metrics_display = MetricsDisplay()
        test_layout.addWidget(self.metrics_display)
        
        self.tab_widget.addTab(test_tab, "Test & Metrics")
        
        # History tab
        self.history_panel = HistoryPanel(self.database)
        self.tab_widget.addTab(self.history_panel, "History")
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        export_action = QAction('Export Current Session...', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_current_session)
        file_menu.addAction(export_action)
        
        export_all_action = QAction('Export All Sessions...', self)
        export_all_action.triggered.connect(self.export_all_sessions)
        file_menu.addAction(export_all_action)
        
        file_menu.addSeparator()
        
        save_config_action = QAction('Save Configuration...', self)
        save_config_action.setShortcut('Ctrl+S')
        save_config_action.triggered.connect(self.save_configuration_preset)
        file_menu.addAction(save_config_action)
        
        load_config_action = QAction('Load Configuration...', self)
        load_config_action.setShortcut('Ctrl+O')
        load_config_action.triggered.connect(self.load_configuration_preset)
        file_menu.addAction(load_config_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Connection menu
        connection_menu = menubar.addMenu('Connection')
        
        connect_action = QAction('Connect', self)
        connect_action.setShortcut('Ctrl+C')
        connect_action.triggered.connect(self.connect_serial)
        connection_menu.addAction(connect_action)
        
        disconnect_action = QAction('Disconnect', self)
        disconnect_action.setShortcut('Ctrl+D')
        disconnect_action.triggered.connect(self.disconnect_serial)
        connection_menu.addAction(disconnect_action)
        
        # Test menu
        test_menu = menubar.addMenu('Test')
        
        start_test_action = QAction('Start Test', self)
        start_test_action.setShortcut('F5')
        start_test_action.triggered.connect(self.start_test)
        test_menu.addAction(start_test_action)
        
        stop_test_action = QAction('Stop Test', self)
        stop_test_action.setShortcut('F6')
        stop_test_action.triggered.connect(self.stop_test)
        test_menu.addAction(stop_test_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def connect_signals(self):
        """Connect signals between components"""
        # Serial handler signals
        self.serial_handler.connection_status_changed.connect(self.on_connection_status_changed)
        self.serial_handler.error_occurred.connect(self.on_serial_error)
        
        # Test engine signals
        self.test_engine.test_started.connect(self.on_test_started)
        self.test_engine.test_stopped.connect(self.on_test_stopped)
        self.test_engine.metrics_updated.connect(self.metrics_display.update_metrics)
        self.test_engine.status_message.connect(self.status_bar.showMessage)
        
        # Config panel signals
        self.config_panel.connect_requested.connect(self.connect_serial)
        self.config_panel.disconnect_requested.connect(self.disconnect_serial)
        
        # Test control panel signals
        self.test_control_panel.start_test.connect(self.start_test)
        self.test_control_panel.stop_test.connect(self.stop_test)
        self.test_control_panel.pause_test.connect(self.pause_test)
        self.test_control_panel.resume_test.connect(self.resume_test)
        
        # History panel signals
        self.history_panel.export_session.connect(self.export_session)
        self.history_panel.delete_session.connect(self.delete_session)
    
    @pyqtSlot()
    def connect_serial(self):
        """Connect to serial port"""
        if self.serial_handler.is_connected:
            QMessageBox.information(self, "Already Connected", 
                                  "Serial port is already connected.")
            return
        
        # Get configuration from config panel
        serial_config = self.config_panel.get_serial_config()
        
        if not serial_config.port:
            QMessageBox.warning(self, "No Port Selected", 
                              "Please select a serial port first.")
            return
        
        # Attempt connection
        success = self.serial_handler.connect(
            port=serial_config.port,
            baudrate=serial_config.baudrate,
            timeout=serial_config.timeout,
            bytesize=serial_config.bytesize,
            parity=serial_config.parity,
            stopbits=serial_config.stopbits
        )
        
        if success:
            self.status_bar.showMessage(f"Connected to {serial_config.port}")
        else:
            QMessageBox.critical(self, "Connection Failed", 
                               f"Failed to connect to {serial_config.port}")
    
    @pyqtSlot()
    def disconnect_serial(self):
        """Disconnect from serial port"""
        if self.test_engine.is_running:
            reply = QMessageBox.question(self, "Test Running", 
                                       "A test is currently running. Stop the test and disconnect?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_test()
            else:
                return
        
        self.serial_handler.disconnect()
        self.status_bar.showMessage("Disconnected")
    
    @pyqtSlot()
    def start_test(self):
        """Start performance test"""
        if not self.serial_handler.is_connected:
            QMessageBox.warning(self, "Not Connected", 
                              "Please connect to a serial port first.")
            return
        
        if self.test_engine.is_running:
            QMessageBox.information(self, "Test Running", 
                                  "A test is already running.")
            return
        
        # Get test configuration
        test_config = self.test_control_panel.get_test_config()
        
        # Configure test engine
        success = self.test_engine.configure_test(
            mode=TestMode(test_config['mode']),
            packet_size=test_config['packet_size'],
            transmission_rate=test_config['transmission_rate'],
            test_duration=test_config['test_duration']
        )
        
        if not success:
            QMessageBox.warning(self, "Configuration Error", 
                              "Failed to configure test parameters.")
            return
        
        # Start test
        if self.test_engine.start_test():
            self.test_control_panel.set_test_running(True)
            self.metrics_display.reset_display()
        else:
            QMessageBox.critical(self, "Test Failed", "Failed to start test.")
    
    @pyqtSlot()
    def stop_test(self):
        """Stop performance test"""
        if not self.test_engine.is_running:
            return
        
        self.test_engine.stop_test()
    
    @pyqtSlot()
    def pause_test(self):
        """Pause performance test"""
        self.test_engine.pause_test()
    
    @pyqtSlot()
    def resume_test(self):
        """Resume performance test"""
        self.test_engine.resume_test()
    
    @pyqtSlot(bool)
    def on_connection_status_changed(self, connected: bool):
        """Handle connection status change"""
        self.config_panel.set_connection_status(connected)
        self.test_control_panel.set_connection_status(connected)
        
        if connected:
            self.status_bar.showMessage("Serial port connected")
        else:
            self.status_bar.showMessage("Serial port disconnected")
    
    @pyqtSlot(str)
    def on_serial_error(self, error_message: str):
        """Handle serial communication error"""
        QMessageBox.critical(self, "Serial Error", error_message)
        self.logger.error(f"Serial error: {error_message}")
    
    @pyqtSlot()
    def on_test_started(self):
        """Handle test started"""
        self.test_control_panel.set_test_running(True)
        self.status_bar.showMessage("Test started")
    
    @pyqtSlot()
    def on_test_stopped(self):
        """Handle test stopped"""
        self.test_control_panel.set_test_running(False)
        self.status_bar.showMessage("Test stopped")
        
        # Save test results to database
        self.save_test_results()
        
        # Refresh history panel
        self.history_panel.refresh_history()
    
    def save_test_results(self):
        """Save current test results to database"""
        metrics = self.test_engine.get_current_metrics()
        test_config = self.test_control_panel.get_test_config()
        serial_config = self.config_panel.get_serial_config()
        
        # Combine configurations
        full_config = {
            **test_config,
            'serial_port': serial_config.port,
            'baudrate': serial_config.baudrate,
            'bytesize': serial_config.bytesize,
            'parity': serial_config.parity,
            'stopbits': serial_config.stopbits
        }
        
        # Save to database
        session_id = self.database.save_test_session(
            metrics=metrics,
            mode=TestMode(test_config['mode']),
            config=full_config,
            notes=""  # Could add a dialog for notes
        )
        
        if session_id > 0:
            self.current_test_session_id = session_id
            self.logger.info(f"Test results saved with session ID: {session_id}")
        else:
            QMessageBox.warning(self, "Save Failed", "Failed to save test results to database.")
    
    def update_status(self):
        """Update status bar with current information"""
        if self.serial_handler.is_connected:
            stats = self.serial_handler.get_statistics()
            status = f"Connected | Sent: {stats['packets_sent']} pkts | Received: {stats['packets_received']} pkts"
            if self.test_engine.is_running:
                status += " | Test: RUNNING"
            elif self.test_engine.is_paused:
                status += " | Test: PAUSED"
            self.status_bar.showMessage(status)
    
    def export_current_session(self):
        """Export current test session"""
        if self.current_test_session_id is None:
            QMessageBox.information(self, "No Session", "No test session to export.")
            return
        
        self.export_session(self.current_test_session_id)
    
    def export_session(self, session_id: int):
        """Export specific session"""
        export_data = self.database.export_session_data(session_id)
        if not export_data:
            QMessageBox.warning(self, "Export Failed", "Failed to retrieve session data.")
            return
        
        # Get export file path
        file_path, file_type = QFileDialog.getSaveFileName(
            self, "Export Session Data", 
            f"session_{session_id}",
            "CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        # Export based on file type
        success = False
        if file_type.startswith("CSV"):
            success = self.exporter.export_to_csv(export_data, file_path)
        elif file_type.startswith("JSON"):
            success = self.exporter.export_to_json(export_data, file_path)
        
        if success:
            QMessageBox.information(self, "Export Complete", f"Data exported to {file_path}")
        else:
            QMessageBox.critical(self, "Export Failed", "Failed to export data.")
    
    def export_all_sessions(self):
        """Export summary of all sessions"""
        sessions = self.database.get_test_sessions(limit=1000)
        if not sessions:
            QMessageBox.information(self, "No Data", "No test sessions to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export All Sessions", 
            "all_sessions_summary.csv",
            "CSV Files (*.csv)"
        )
        
        if not file_path:
            return
        
        if self.exporter.create_export_summary(sessions, file_path):
            QMessageBox.information(self, "Export Complete", f"Summary exported to {file_path}")
        else:
            QMessageBox.critical(self, "Export Failed", "Failed to export summary.")
    
    def delete_session(self, session_id: int):
        """Delete a test session"""
        reply = QMessageBox.question(self, "Delete Session", 
                                   f"Are you sure you want to delete session {session_id}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.database.delete_session(session_id):
                self.history_panel.refresh_history()
                QMessageBox.information(self, "Deleted", "Session deleted successfully.")
            else:
                QMessageBox.critical(self, "Delete Failed", "Failed to delete session.")
    
    def save_configuration_preset(self):
        """Save current configuration as preset"""
        name, ok = QInputDialog.getText(self, "Save Configuration", "Preset name:")
        if not ok or not name.strip():
            return
        
        # Get current configuration
        test_config = self.test_control_panel.get_test_config()
        serial_config = self.config_panel.get_serial_config()
        
        full_config = {
            **test_config,
            'serial_port': serial_config.port,
            'baudrate': serial_config.baudrate,
            'bytesize': serial_config.bytesize,
            'parity': serial_config.parity,
            'stopbits': serial_config.stopbits
        }
        
        if self.database.save_config_preset(name.strip(), full_config):
            QMessageBox.information(self, "Saved", f"Configuration preset '{name}' saved.")
        else:
            QMessageBox.critical(self, "Save Failed", "Failed to save configuration preset.")
    
    def load_configuration_preset(self):
        """Load a configuration preset"""
        presets = self.database.get_config_presets()
        if not presets:
            QMessageBox.information(self, "No Presets", "No configuration presets found.")
            return
        
        # Create selection dialog
        preset_names = [preset['name'] for preset in presets]
        name, ok = QInputDialog.getItem(self, "Load Configuration", 
                                       "Select preset:", preset_names, 0, False)
        
        if not ok:
            return
        
        # Find and load preset
        for preset in presets:
            if preset['name'] == name:
                config = preset['config']
                self.config_panel.load_config(config)
                self.test_control_panel.load_config(config)
                QMessageBox.information(self, "Loaded", f"Configuration preset '{name}' loaded.")
                break
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About", 
                         "Serial Communication Performance Tester v1.0.0\n\n"
                         "A professional tool for testing serial communication performance.\n"
                         "Features comprehensive metrics, data logging, and export capabilities.")
    
    def restore_window_state(self):
        """Restore window geometry from configuration"""
        if self.config.window_geometry:
            try:
                # Parse geometry string (format: "x,y,width,height")
                parts = self.config.window_geometry.split(',')
                if len(parts) == 4:
                    x, y, w, h = map(int, parts)
                    self.setGeometry(x, y, w, h)
            except (ValueError, IndexError):
                pass  # Use default geometry
    
    def save_window_state(self):
        """Save window geometry to configuration"""
        geometry = self.geometry()
        self.config.window_geometry = f"{geometry.x()},{geometry.y()},{geometry.width()},{geometry.height()}"
        self.config.save_config()
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Stop any running test
        if self.test_engine.is_running:
            reply = QMessageBox.question(self, "Test Running", 
                                       "A test is currently running. Stop the test and exit?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            self.stop_test()
        
        # Disconnect serial port
        if self.serial_handler.is_connected:
            self.serial_handler.disconnect()
        
        # Save window state
        self.save_window_state()
        
        # Save configuration
        self.config.save_config()
        
        event.accept()
