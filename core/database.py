"""
Database handler for storing test results and logs
"""

import sqlite3
import json
import time
import logging
from typing import List, Dict, Optional, Any
from dataclasses import asdict
from contextlib import contextmanager
from core.test_engine import TestMetrics, TestMode

class DatabaseHandler:
    """SQLite database handler for test results"""
    
    def __init__(self, db_path: str = "serial_tester.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Test sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS test_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL NOT NULL,
                        mode TEXT NOT NULL,
                        duration REAL NOT NULL,
                        packet_size INTEGER NOT NULL,
                        transmission_rate INTEGER NOT NULL,
                        packets_sent INTEGER NOT NULL,
                        packets_received INTEGER NOT NULL,
                        packets_lost INTEGER NOT NULL,
                        packet_loss_rate REAL NOT NULL,
                        bytes_transmitted INTEGER NOT NULL,
                        average_latency REAL NOT NULL,
                        average_bandwidth REAL NOT NULL,
                        config_json TEXT,
                        notes TEXT
                    )
                ''')
                
                # Detailed metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS metric_samples (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER NOT NULL,
                        timestamp REAL NOT NULL,
                        metric_type TEXT NOT NULL,
                        value REAL NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES test_sessions (id)
                    )
                ''')
                
                # Error logs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS error_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER NOT NULL,
                        timestamp REAL NOT NULL,
                        error_message TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES test_sessions (id)
                    )
                ''')
                
                # Configuration presets table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config_presets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        created_timestamp REAL NOT NULL,
                        config_json TEXT NOT NULL,
                        description TEXT
                    )
                ''')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with context manager"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_test_session(self, metrics: TestMetrics, mode: TestMode, 
                         config: Dict[str, Any], notes: str = "") -> int:
        """Save test session results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Insert main session record
                cursor.execute('''
                    INSERT INTO test_sessions (
                        timestamp, mode, duration, packet_size, transmission_rate,
                        packets_sent, packets_received, packets_lost, packet_loss_rate,
                        bytes_transmitted, average_latency, average_bandwidth,
                        config_json, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.start_time,
                    mode.value,
                    metrics.test_duration,
                    config.get('packet_size', 0),
                    config.get('transmission_rate', 0),
                    metrics.packets_sent,
                    metrics.packets_received,
                    metrics.packets_lost,
                    metrics.packet_loss_rate,
                    metrics.bytes_transmitted,
                    metrics.average_latency,
                    metrics.average_bandwidth,
                    json.dumps(config),
                    notes
                ))
                
                session_id = cursor.lastrowid
                
                # Save latency samples
                for i, latency in enumerate(metrics.latency_samples):
                    cursor.execute('''
                        INSERT INTO metric_samples (session_id, timestamp, metric_type, value)
                        VALUES (?, ?, ?, ?)
                    ''', (session_id, metrics.start_time + i, 'latency', latency))
                
                # Save bandwidth samples
                for i, bandwidth in enumerate(metrics.bandwidth_samples):
                    cursor.execute('''
                        INSERT INTO metric_samples (session_id, timestamp, metric_type, value)
                        VALUES (?, ?, ?, ?)
                    ''', (session_id, metrics.start_time + i, 'bandwidth', bandwidth))
                
                # Save error logs
                for i, error in enumerate(metrics.errors):
                    cursor.execute('''
                        INSERT INTO error_logs (session_id, timestamp, error_message)
                        VALUES (?, ?, ?)
                    ''', (session_id, metrics.start_time + i, error))
                
                conn.commit()
                self.logger.info(f"Test session saved with ID: {session_id}")
                return session_id
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to save test session: {e}")
            return -1
    
    def get_test_sessions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of test sessions"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM test_sessions 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                sessions = []
                for row in cursor.fetchall():
                    session = dict(row)
                    # Parse JSON config
                    try:
                        session['config'] = json.loads(session['config_json'])
                    except (json.JSONDecodeError, TypeError):
                        session['config'] = {}
                    
                    sessions.append(session)
                
                return sessions
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get test sessions: {e}")
            return []
    
    def get_session_details(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific session"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get session info
                cursor.execute('SELECT * FROM test_sessions WHERE id = ?', (session_id,))
                session_row = cursor.fetchone()
                
                if not session_row:
                    return None
                
                session = dict(session_row)
                
                # Parse JSON config
                try:
                    session['config'] = json.loads(session['config_json'])
                except (json.JSONDecodeError, TypeError):
                    session['config'] = {}
                
                # Get metric samples
                cursor.execute('''
                    SELECT timestamp, metric_type, value 
                    FROM metric_samples 
                    WHERE session_id = ? 
                    ORDER BY timestamp
                ''', (session_id,))
                
                latency_samples = []
                bandwidth_samples = []
                
                for row in cursor.fetchall():
                    if row[1] == 'latency':
                        latency_samples.append((row[0], row[2]))
                    elif row[1] == 'bandwidth':
                        bandwidth_samples.append((row[0], row[2]))
                
                session['latency_samples'] = latency_samples
                session['bandwidth_samples'] = bandwidth_samples
                
                # Get error logs
                cursor.execute('''
                    SELECT timestamp, error_message 
                    FROM error_logs 
                    WHERE session_id = ? 
                    ORDER BY timestamp
                ''', (session_id,))
                
                session['error_logs'] = [(row[0], row[1]) for row in cursor.fetchall()]
                
                return session
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get session details: {e}")
            return None
    
    def delete_session(self, session_id: int) -> bool:
        """Delete a test session and all related data"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Delete related records first (foreign key constraints)
                cursor.execute('DELETE FROM metric_samples WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM error_logs WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM test_sessions WHERE id = ?', (session_id,))
                
                conn.commit()
                self.logger.info(f"Deleted session {session_id}")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete session: {e}")
            return False
    
    def save_config_preset(self, name: str, config: Dict[str, Any], description: str = "") -> bool:
        """Save a configuration preset"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO config_presets (name, created_timestamp, config_json, description)
                    VALUES (?, ?, ?, ?)
                ''', (name, time.time(), json.dumps(config), description))
                
                conn.commit()
                self.logger.info(f"Config preset '{name}' saved")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to save config preset: {e}")
            return False
    
    def get_config_presets(self) -> List[Dict[str, Any]]:
        """Get all configuration presets"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM config_presets 
                    ORDER BY created_timestamp DESC
                ''')
                
                presets = []
                for row in cursor.fetchall():
                    preset = dict(row)
                    try:
                        preset['config'] = json.loads(preset['config_json'])
                    except (json.JSONDecodeError, TypeError):
                        preset['config'] = {}
                    
                    presets.append(preset)
                
                return presets
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to get config presets: {e}")
            return []
    
    def delete_config_preset(self, name: str) -> bool:
        """Delete a configuration preset"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM config_presets WHERE name = ?', (name,))
                conn.commit()
                
                self.logger.info(f"Config preset '{name}' deleted")
                return True
                
        except sqlite3.Error as e:
            self.logger.error(f"Failed to delete config preset: {e}")
            return False
    
    def export_session_data(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Export session data for CSV/JSON export"""
        session = self.get_session_details(session_id)
        if not session:
            return None
        
        # Prepare data for export
        export_data = {
            'session_info': {
                'id': session['id'],
                'timestamp': session['timestamp'],
                'mode': session['mode'],
                'duration': session['duration'],
                'packet_size': session['packet_size'],
                'transmission_rate': session['transmission_rate'],
                'packets_sent': session['packets_sent'],
                'packets_received': session['packets_received'],
                'packets_lost': session['packets_lost'],
                'packet_loss_rate': session['packet_loss_rate'],
                'bytes_transmitted': session['bytes_transmitted'],
                'average_latency': session['average_latency'],
                'average_bandwidth': session['average_bandwidth'],
                'notes': session['notes']
            },
            'latency_data': session['latency_samples'],
            'bandwidth_data': session['bandwidth_samples'],
            'error_logs': session['error_logs'],
            'config': session['config']
        }
        
        return export_data
