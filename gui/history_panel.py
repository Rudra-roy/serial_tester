"""
History panel for viewing past test results
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QMenu, QLabel,
                            QLineEdit, QComboBox, QGroupBox, QFormLayout)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QAction

from core.database import DatabaseHandler

class HistoryPanel(QWidget):
    """History panel for viewing and managing test results"""
    
    # Signals
    export_session = pyqtSignal(int)  # session_id
    delete_session = pyqtSignal(int)  # session_id
    
    def __init__(self, database: DatabaseHandler):
        super().__init__()
        self.database = database
        self.logger = logging.getLogger(__name__)
        self.sessions_data: List[Dict[str, Any]] = []
        
        self.init_ui()
        self.refresh_history()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_history)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        """Initialize user interface"""
        layout = QVBoxLayout(self)
        
        # Create filter/search group
        self.create_filter_group(layout)
        
        # Create sessions table
        self.create_sessions_table(layout)
        
        # Create control buttons
        self.create_control_buttons(layout)
    
    def create_filter_group(self, parent_layout):
        """Create filter and search controls"""
        filter_group = QGroupBox("Filter & Search")
        filter_layout = QFormLayout(filter_group)
        
        # Search by notes/description
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search in notes...")
        self.search_edit.textChanged.connect(self.apply_filters)
        filter_layout.addRow("Search:", self.search_edit)
        
        # Filter by mode
        self.mode_filter = QComboBox()
        self.mode_filter.addItem("All Modes", "")
        self.mode_filter.addItem("Transmitter", "transmitter")
        self.mode_filter.addItem("Receiver", "receiver")
        self.mode_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addRow("Mode:", self.mode_filter)
        
        # Results info
        self.results_label = QLabel("0 sessions")
        filter_layout.addRow("Results:", self.results_label)
        
        parent_layout.addWidget(filter_group)
    
    def create_sessions_table(self, parent_layout):
        """Create sessions table"""
        self.sessions_table = QTableWidget()
        self.sessions_table.setAlternatingRowColors(True)
        self.sessions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sessions_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.sessions_table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Set up columns
        columns = [
            "ID", "Date", "Mode", "Duration", "Packet Size", "Rate", 
            "Sent", "Received", "Lost", "Loss %", "Avg Latency", "Avg Bandwidth", "Notes"
        ]
        self.sessions_table.setColumnCount(len(columns))
        self.sessions_table.setHorizontalHeaderLabels(columns)
        
        # Configure column widths
        header = self.sessions_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Mode
        header.setSectionResizeMode(12, QHeaderView.ResizeMode.Stretch)  # Notes
        
        parent_layout.addWidget(self.sessions_table)
    
    def create_control_buttons(self, parent_layout):
        """Create control buttons"""
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_history)
        
        self.export_button = QPushButton("Export Selected")
        self.export_button.clicked.connect(self.export_selected_session)
        self.export_button.setEnabled(False)
        
        self.delete_button = QPushButton("Delete Selected")
        self.delete_button.clicked.connect(self.delete_selected_session)
        self.delete_button.setEnabled(False)
        
        self.clear_all_button = QPushButton("Clear All")
        self.clear_all_button.clicked.connect(self.clear_all_sessions)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.clear_all_button)
        
        parent_layout.addLayout(button_layout)
        
        # Connect selection change
        self.sessions_table.selectionModel().selectionChanged.connect(self.on_selection_changed)
    
    def refresh_history(self):
        """Refresh history from database"""
        try:
            self.sessions_data = self.database.get_test_sessions(limit=500)
            self.apply_filters()
            self.logger.debug(f"Loaded {len(self.sessions_data)} sessions from database")
            
        except Exception as e:
            self.logger.error(f"Failed to refresh history: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load history: {e}")
    
    def apply_filters(self):
        """Apply current filters to the session list"""
        search_text = self.search_edit.text().lower()
        mode_filter = self.mode_filter.currentData()
        
        # Filter sessions
        filtered_sessions = []
        for session in self.sessions_data:
            # Mode filter
            if mode_filter and session['mode'] != mode_filter:
                continue
            
            # Search filter
            if search_text:
                notes = session.get('notes', '').lower()
                if search_text not in notes:
                    continue
            
            filtered_sessions.append(session)
        
        # Update table
        self.populate_table(filtered_sessions)
        self.results_label.setText(f"{len(filtered_sessions)} sessions")
    
    def populate_table(self, sessions: List[Dict[str, Any]]):
        """Populate table with session data"""
        self.sessions_table.setRowCount(len(sessions))
        
        for row, session in enumerate(sessions):
            # ID
            self.sessions_table.setItem(row, 0, QTableWidgetItem(str(session['id'])))
            
            # Date
            timestamp = datetime.fromtimestamp(session['timestamp'])
            date_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            self.sessions_table.setItem(row, 1, QTableWidgetItem(date_str))
            
            # Mode
            self.sessions_table.setItem(row, 2, QTableWidgetItem(session['mode'].title()))
            
            # Duration
            self.sessions_table.setItem(row, 3, QTableWidgetItem(f"{session['duration']:.1f}s"))
            
            # Packet Size
            self.sessions_table.setItem(row, 4, QTableWidgetItem(f"{session['packet_size']} B"))
            
            # Rate
            self.sessions_table.setItem(row, 5, QTableWidgetItem(f"{session['transmission_rate']} pkt/s"))
            
            # Sent
            self.sessions_table.setItem(row, 6, QTableWidgetItem(str(session['packets_sent'])))
            
            # Received
            self.sessions_table.setItem(row, 7, QTableWidgetItem(str(session['packets_received'])))
            
            # Lost
            self.sessions_table.setItem(row, 8, QTableWidgetItem(str(session['packets_lost'])))
            
            # Loss %
            self.sessions_table.setItem(row, 9, QTableWidgetItem(f"{session['packet_loss_rate']:.2f}%"))
            
            # Avg Latency
            latency_ms = session['average_latency'] * 1000
            self.sessions_table.setItem(row, 10, QTableWidgetItem(f"{latency_ms:.2f} ms"))
            
            # Avg Bandwidth
            bandwidth_str = self.format_bytes(session['average_bandwidth'])
            self.sessions_table.setItem(row, 11, QTableWidgetItem(f"{bandwidth_str}/s"))
            
            # Notes
            notes = session.get('notes', '')[:50]  # Truncate long notes
            if len(session.get('notes', '')) > 50:
                notes += "..."
            self.sessions_table.setItem(row, 12, QTableWidgetItem(notes))
    
    def on_selection_changed(self):
        """Handle table selection change"""
        has_selection = len(self.sessions_table.selectionModel().selectedRows()) > 0
        self.export_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
    
    def get_selected_session_id(self) -> Optional[int]:
        """Get selected session ID"""
        selected_rows = self.sessions_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        session_id_item = self.sessions_table.item(row, 0)  # ID column
        if session_id_item:
            return int(session_id_item.text())
        
        return None
    
    def export_selected_session(self):
        """Export selected session"""
        session_id = self.get_selected_session_id()
        if session_id is not None:
            self.export_session.emit(session_id)
    
    def delete_selected_session(self):
        """Delete selected session"""
        session_id = self.get_selected_session_id()
        if session_id is not None:
            self.delete_session.emit(session_id)
    
    def clear_all_sessions(self):
        """Clear all sessions after confirmation"""
        reply = QMessageBox.question(
            self, "Clear All Sessions",
            "Are you sure you want to delete ALL test sessions?\n"
            "This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete all sessions
                for session in self.sessions_data:
                    self.database.delete_session(session['id'])
                
                self.refresh_history()
                QMessageBox.information(self, "Cleared", "All sessions have been deleted.")
                
            except Exception as e:
                self.logger.error(f"Failed to clear sessions: {e}")
                QMessageBox.critical(self, "Clear Failed", f"Failed to clear sessions: {e}")
    
    def show_context_menu(self, position):
        """Show context menu for table"""
        if not self.sessions_table.itemAt(position):
            return
        
        menu = QMenu(self)
        
        export_action = QAction("Export Session", self)
        export_action.triggered.connect(self.export_selected_session)
        menu.addAction(export_action)
        
        delete_action = QAction("Delete Session", self)
        delete_action.triggered.connect(self.delete_selected_session)
        menu.addAction(delete_action)
        
        menu.addSeparator()
        
        view_details_action = QAction("View Details", self)
        view_details_action.triggered.connect(self.view_session_details)
        menu.addAction(view_details_action)
        
        menu.exec(self.sessions_table.mapToGlobal(position))
    
    def view_session_details(self):
        """View detailed information for selected session"""
        session_id = self.get_selected_session_id()
        if session_id is None:
            return
        
        try:
            details = self.database.get_session_details(session_id)
            if not details:
                QMessageBox.warning(self, "Not Found", "Session details not found.")
                return
            
            # Create details dialog
            self.show_session_details_dialog(details)
            
        except Exception as e:
            self.logger.error(f"Failed to get session details: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load session details: {e}")
    
    def show_session_details_dialog(self, details: Dict[str, Any]):
        """Show session details in a dialog"""
        dialog = QMessageBox(self)
        dialog.setWindowTitle(f"Session {details['id']} Details")
        dialog.setIcon(QMessageBox.Icon.Information)
        
        # Format details text
        timestamp = datetime.fromtimestamp(details['timestamp'])
        
        text = f"""
Session ID: {details['id']}
Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Mode: {details['mode'].title()}
Duration: {details['duration']:.1f} seconds
Packet Size: {details['packet_size']} bytes
Transmission Rate: {details['transmission_rate']} pkt/s

Results:
- Packets Sent: {details['packets_sent']}
- Packets Received: {details['packets_received']}
- Packets Lost: {details['packets_lost']}
- Packet Loss Rate: {details['packet_loss_rate']:.2f}%
- Bytes Transmitted: {self.format_bytes(details['bytes_transmitted'])}

Performance:
- Average Latency: {details['average_latency']*1000:.2f} ms
- Average Bandwidth: {self.format_bytes(details['average_bandwidth'])}/s

Samples:
- Latency Samples: {len(details.get('latency_samples', []))}
- Bandwidth Samples: {len(details.get('bandwidth_samples', []))}
- Error Logs: {len(details.get('error_logs', []))}

Notes:
{details.get('notes', 'No notes')}
        """.strip()
        
        dialog.setText(text)
        dialog.exec()
    
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
